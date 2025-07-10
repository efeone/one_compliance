import frappe
from frappe.utils import get_datetime
from erpnext.accounts.party import get_party_account

@frappe.whitelist()
def get_task(status = None, task = None, project = None, customer = None, department = None, sub_category = None, employee = None, employee_group = None, from_date = None, to_date = None):
    current_user = frappe.session.user
    roles = frappe.get_roles(current_user)
    user_id = f'"{employee}"' if id else None

    # Construct the SQL query to fetch list of tasks
    query = """
	SELECT
        t.name,t.project,t.subject, t.project_name, t.customer, c.department, t.compliance_sub_category, t.exp_start_date, t.exp_end_date, t._assign, t.status, t.assigned_to, t.completed_by, t.color, t.custom_is_payable, t.readiness_status
    FROM
        tabTask t LEFT JOIN `tabCompliance Sub Category` c ON t.compliance_sub_category = c.name
    """

    if status:
            query += f" WHERE t.status = '{status}'"
    else:
        query += " WHERE t.status IN ('open', 'working', 'overdue')"

    if task:
            query += f" AND t.name = '{task}'"

    if project:
            query += f" AND t.project = '{project}'"

    if customer:
            query += f" AND t.customer = '{customer}'"

    if department:
            query += f" AND c.department = '{department}'"

    if sub_category:
            query += f" AND t.compliance_sub_category = '{sub_category}'"

    if employee:
            query += f" AND t._assign LIKE '%{user_id}%'"

    if employee_group:
            query += f" AND t.assigned_to = '{employee_group}'"

    if from_date:
            query += f" AND t.exp_start_date >= '{from_date}'"

    if to_date:
            query += f" AND t.exp_end_date < '{to_date}'"


    # Only show tasks with readiness_status = "Ready" for Executive (excluding Administrator)
    if current_user != "Administrator" and "Executive" in roles:
        query +="AND (t.readiness_status = 'Ready' OR t.readiness_status IS NULL OR t.readiness_status = '')"

    query += """ ORDER BY
            t.modified DESC;"""

    task_list = frappe.db.sql(query, as_dict=1)
    for task in task_list:
        task['employee_names'] = []
        if task['_assign']:
            user_ids = frappe.parse_json(task['_assign'])

            if user_ids:
                user_names_query = """
                    SELECT name, employee_name, user_id FROM `tabEmployee`
                    WHERE user_id IN ({})
                """.format(', '.join(['%s' for _ in user_ids]))

                user_names = frappe.db.sql(user_names_query, tuple(user_ids), as_dict=True)
                task['_assign'] = [{'employee_name': user['employee_name'], 'employee_id': user['name']} for user in user_names]
                task['employee_names'] = [user['employee_name'] for user in user_names]
            else:
                task['_assign'] = []
                task['employee_names'] = []
        else:
            task['_assign'] = []
            task['employee_names'] = []

        if task['completed_by']:
            if task['completed_by'] == 'Administrator':
                task['completed_by_name'] = 'Administrator'
            else:
                completed_by = frappe.get_value("Employee", {"user_id": task['completed_by']}, ["name", "employee_name"], as_dict=True)
                task['completed_by_name'] = completed_by["employee_name"]
                task['completed_by_id'] = completed_by["name"]
        else:
            task['completed_by_name'] = []
            task['completed_by_id'] = []

    return task_list

@frappe.whitelist()
def create_timesheet(project, task, employee, activity, from_time, to_time):

    from_time = get_datetime(from_time)
    to_time = get_datetime(to_time)
    employee_id = frappe.get_value("Employee", {"employee_name": employee}, "name")

    # Check if a timesheet already exists for the employee within the given date range
    existing_timesheets = frappe.get_all("Timesheet", filters={
        "employee": employee_id,
        "start_date": from_time.date(),
        "end_date": to_time.date(),
    })

    if existing_timesheets:
        existing_timesheet = frappe.get_doc("Timesheet", existing_timesheets)
        existing_timesheet.append("time_logs",{
            "activity_type": activity,
            "project": project,
            "task": task,
            "from_time": from_time,
            "to_time": to_time
        })
        existing_timesheet.save()
        frappe.db.commit()
    else:
        timesheet = frappe.new_doc("Timesheet")
        timesheet.employee = employee_id
        timesheet.append("time_logs",{
            "activity_type": activity,
            "project": project,
            "task": task,
            "from_time": from_time,
            "to_time": to_time
        })

        timesheet.insert(ignore_permissions=True)
        frappe.db.commit()

@frappe.whitelist()
def update_task_status(task, project, status):
    task_doc = frappe.get_doc("Task", {"name":task,"project":project})

    task_doc.status = status

    task_doc.save()
    return "success"


@frappe.whitelist()
def add_payment_info(task_id, payable_amount, mode_of_payment, reference_number=None, reference_date=None, user_remark=None):
    task_doc = frappe.get_doc("Task", task_id)
    payment_info = {
        "payable_amount": payable_amount,
        "mode_of_payment": mode_of_payment,
        "reference_number": reference_number,
        "reference_date": reference_date,
        "user_remark": user_remark
    }
    journal_entry = create_journal_entry_pay_info(task_doc, payment_info)
    payment_info['journal_entry'] = journal_entry
    task_doc.append("custom_task_payment_informations", payment_info)
    task_doc.custom_is_payable = 1
    # task_doc.custom_payable_amount = payable_amount
    # task_doc.custom_mode_of_payment = mode_of_payment
    # task_doc.custom_reference_number = reference_number
    # task_doc.custom_reference_date = reference_date
    # task_doc.custom_user_remark = user_remark
    task_doc.save()
    task_doc.reload()
    sales_order = frappe.db.get_value("Project", task_doc.project, 'sales_order') or None
    if sales_order:
        so_reimburse = frappe.new_doc('Reimbursement Details')
        so_reimburse.parent = sales_order
        so_reimburse.parentfield = 'custom_reimbursement_details'
        so_reimburse.parenttype = 'Sales Order'
        so_reimburse.journal_entry = journal_entry
        so_reimburse.date = reference_date
        so_reimburse.amount = payable_amount
        so_reimburse.user_remark = user_remark
        so_reimburse.save(ignore_permissions= True)
        total_reimbursement_amount = get_total_reimbursement_amount(sales_order)
        frappe.db.set_value('Sales Order', sales_order, 'custom_total_reimbursement_amount', total_reimbursement_amount)
    frappe.db.commit()

def create_journal_entry_pay_info(task, payment_info):
    if payment_info['payable_amount'] and payment_info['mode_of_payment']:
        account = get_party_account('Customer', task.customer, task.company)
        default_account = get_default_account_for_mode_of_payment(payment_info['mode_of_payment'], task.company)
        journal_entry = frappe.new_doc('Journal Entry')
        journal_entry.voucher_type = 'Bank Entry'
        journal_entry.company = task.company
        journal_entry.cheque_no = payment_info['reference_number']
        journal_entry.cheque_date = payment_info['reference_date']
        journal_entry.user_remark = payment_info['user_remark']
        journal_entry.posting_date = frappe.utils.today()
        journal_entry.append('accounts', {
            'account': account,
            'party_type': 'Customer',
            'party': task.customer,
            'project': task.project,
            'debit_in_account_currency': payment_info['payable_amount']
        })
        journal_entry.append('accounts', {
            'account': default_account,
            'project': task.project,
            'credit_in_account_currency': payment_info['payable_amount']
        })
        journal_entry.insert(ignore_permissions=True)
        return journal_entry.name

def get_default_account_for_mode_of_payment(mode_of_payment, company):
    mode_of_payment_doc = frappe.get_doc("Mode of Payment", mode_of_payment)
    for account in mode_of_payment_doc.accounts:
        if account.company == company:
            return account.default_account
    frappe.throw(_("Default account not found for mode of payment {0} and company {1}").format(mode_of_payment, company))

def get_total_reimbursement_amount(sales_order):
    total_reimbursement_amount = 0
    amounts = frappe.db.get_all('Reimbursement Details', { 'parent':sales_order, 'parentfield':'custom_reimbursement_details', 'parenttype':'Sales Order'}, pluck='amount')
    for amount in amounts:
        total_reimbursement_amount += amount
    return total_reimbursement_amount
