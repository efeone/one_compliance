# Copyright (c) 2023, efeone and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import get_datetime
from erpnext.accounts.party import get_party_account

@frappe.whitelist()
def get_task(status=None, task=None, project=None, customer=None, department=None, sub_category=None, employee=None, employee_group=None, from_date=None, to_date=None, page=1, page_length=20):
	"""
		Retrieve a filtered, paginated list of tasks from the Task Management Tool.
	"""
	current_user = frappe.session.user
	roles = frappe.get_roles(current_user)

	conditions = []
	values = {}

	if status:
		if status in ["Completed", "Cancelled", "Template"]:
			return
		else:
			values["status"] = status
			conditions.append("t.status = %(status)s")
	else:
		conditions.append("t.status NOT IN ('Completed', 'Cancelled', 'Template')")

	if task:
		conditions.append("t.name = %(task)s")
		values["task"] = task

	if project:
		conditions.append("t.project = %(project)s")
		values["project"] = project

	if customer:
		conditions.append("t.customer = %(customer)s")
		values["customer"] = customer

	if department:
		conditions.append("c.department = %(department)s")
		values["department"] = department

	if sub_category:
		conditions.append("t.compliance_sub_category = %(sub_category)s")
		values["sub_category"] = sub_category

	if employee:
		conditions.append("t._assign LIKE %(employee)s")
		values["employee"] = f'%"{employee}"%'

	if employee_group:
		conditions.append("t.assigned_to = %(employee_group)s")
		values["employee_group"] = employee_group

	if from_date:
		conditions.append("t.exp_start_date >= %(from_date)s")
		values["from_date"] = from_date

	if to_date:
		conditions.append("t.exp_end_date < %(to_date)s")
		values["to_date"] = to_date

	if current_user != "Administrator" and "Executive" in roles:
		conditions.append("(t.readiness_status = 'Ready' OR t.readiness_status IS NULL OR t.readiness_status = '')")

	where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""

	count_query = f"""
		SELECT COUNT(t.name)
		FROM tabTask t
		LEFT JOIN `tabCompliance Sub Category` c ON t.compliance_sub_category = c.name
		{where_clause}
	"""
	total_tasks = frappe.db.sql(count_query, values.copy(), as_dict=False)[0][0]

	data_query = f"""
		SELECT
			t.name, t.project, t.subject, t.project_name, t.customer, c.department, t.compliance_sub_category,
			t.exp_start_date, t.exp_end_date, t._assign, t.status, t.assigned_to, t.completed_by, t.color,
			t.custom_is_payable, t.readiness_status
		FROM
			tabTask t LEFT JOIN `tabCompliance Sub Category` c ON t.compliance_sub_category = c.name
		{where_clause}
		ORDER BY
			t.modified DESC
		LIMIT %(page_length)s OFFSET %(offset)s
	"""
	values['page_length'] = int(page_length)
	values['offset'] = (int(page) - 1) * int(page_length)

	task_list = frappe.db.sql(data_query, values, as_dict=1)

	for task_item in task_list:
		task_item['employee_names'] = []
		if task_item['_assign']:
			user_ids = frappe.parse_json(task_item['_assign'])
			if user_ids:
				user_names_query = """
					SELECT name, employee_name, user_id FROM `tabEmployee`
					WHERE user_id IN ({})
				""".format(', '.join(['%s' for _ in user_ids]))
				user_names = frappe.db.sql(user_names_query, tuple(user_ids), as_dict=True)
				task_item['_assign'] = [{'employee_name': user['employee_name'], 'employee_id': user['name']} for user in user_names]
				task_item['employee_names'] = [user['employee_name'] for user in user_names]
			else:
				task_item['_assign'] = []
				task_item['employee_names'] = []
		else:
			task_item['_assign'] = []
			task_item['employee_names'] = []

		if task_item['completed_by']:
			if task_item['completed_by'] == 'Administrator':
				task_item['completed_by_name'] = 'Administrator'
			else:
				completed_by = frappe.get_value("Employee", {"user_id": task_item['completed_by']}, ["name", "employee_name"], as_dict=True)
				if completed_by:
					task_item['completed_by_name'] = completed_by.get("employee_name")
					task_item['completed_by_id'] = completed_by.get("name")
		else:
			task_item['completed_by_name'] = []
			task_item['completed_by_id'] = []

	return {
		"tasks": task_list,
		"total_tasks": total_tasks,
		"icons": get_icon_hidden_status()
	}

@frappe.whitelist()
def create_timesheet(project, task, employee, activity, from_time, to_time, lag_time=None, reason_for_lag_time=None, description=None):
	"""
		Create or update a Timesheet for an employee based on provided time logs.
	"""
	from_time = get_datetime(from_time)
	to_time = get_datetime(to_time)
	employee_id = frappe.get_value("Employee", {"employee_name": employee}, "name")

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
			"to_time": to_time,
			"lag_time": lag_time,
			"reason_for_lag_time": reason_for_lag_time,
			"description": description,
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
			"to_time": to_time,
			"lag_time": lag_time,
			"reason_for_lag_time": reason_for_lag_time,
			"description": description,
		})

		timesheet.insert(ignore_permissions=True)
		frappe.db.commit()

@frappe.whitelist()
def update_task_status(task, status):
	"""
		Create or update a Timesheet for an employee based on provided time logs.
	"""
	#Using get_doc and save to trigger doctype events
	task_doc = frappe.get_doc("Task", task)
	task_doc.status = status
	task_doc.save()
	return "success"

@frappe.whitelist()
def add_payment_info(task_id, payable_amount, mode_of_payment, reference_number=None, reference_date=None, user_remark=None, type=None):
	"""
		Add payment details to a task and create related Journal Entry and Reimbursement records.
	"""
	task_doc = frappe.get_doc("Task", task_id)
	payment_info = {
		"payable_amount": payable_amount,
		"mode_of_payment": mode_of_payment,
		"reference_number": reference_number,
		"reference_date": reference_date,
		"user_remark": user_remark,
		"type": type
	}
	journal_entry = create_journal_entry_pay_info(task_doc, payment_info)
	payment_info['journal_entry'] = journal_entry
	task_doc.append("custom_task_payment_informations", payment_info)
	task_doc.custom_is_payable = 1
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

def create_journal_entry_pay_info(task, payment_info):
	"""
		Create a Journal Entry for the provided payment information.
	"""
	if payment_info['payable_amount'] and payment_info['mode_of_payment']:
		account = get_party_account('Customer', task.customer, task.company)
		default_account = get_default_account_for_mode_of_payment(payment_info['mode_of_payment'], task.company)
		voucher_type = 'Bank Entry' if payment_info['type'] == 'Bank' else 'Journal Entry'
		journal_entry = frappe.new_doc('Journal Entry')
		journal_entry.voucher_type = voucher_type
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
	"""
		Get the default account for the specified mode of payment and company.
	"""
	mode_of_payment_doc = frappe.get_doc("Mode of Payment", mode_of_payment)
	for account in mode_of_payment_doc.accounts:
		if account.company == company:
			return account.default_account
	frappe.throw(_("Default account not found for mode of payment {0} and company {1}").format(mode_of_payment, company))

def get_total_reimbursement_amount(sales_order):
	"""
		Calculate the total reimbursement amount for a given Sales Order
	"""
	total_reimbursement_amount = 0
	amounts = frappe.db.get_all('Reimbursement Details', { 'parent':sales_order, 'parentfield':'custom_reimbursement_details', 'parenttype':'Sales Order'}, pluck='amount')
	for amount in amounts:
		total_reimbursement_amount += amount
	return total_reimbursement_amount

@frappe.whitelist()
def get_icon_hidden_status():
	"""
		Check if the task icons is set to be hidden in One Compliance Settings.
	"""
	data ={
		'hide_document_icon': frappe.db.get_single_value("Compliance Settings", "hide_document_icon"),
		'hide_credentials_icon': frappe.db.get_single_value("Compliance Settings", "hide_credentials_icon"),
		'hide_payment_icon': frappe.db.get_single_value("Compliance Settings", "hide_payment_icon")
	}
	return data

@frappe.whitelist()
def start_active_timer(task, project, subject, start_time):
	"""
		Start a timer for a specific task, ensuring no overlapping timers for the same user.
	"""
	user = frappe.session.user
	if not user or user == 'Guest':
		frappe.throw(_("User authentication required. Please login first."))
	if not frappe.db.exists("Task", task):
		frappe.throw(_("Task {0} not found").format(task))
	if not frappe.has_permission("Task", "read", task):
		frappe.throw(_("No permission to access this task"))
	if project and not frappe.db.exists("Project", project):
		frappe.throw(_("Project {0} not found").format(project))
	try:
		start_dt = frappe.utils.get_datetime(start_time)
		if start_dt > frappe.utils.now_datetime():
			frappe.throw(_("Start time cannot be in the future"))
	except Exception:
		frappe.throw(_("Invalid start_time format"))

	val1 = frappe.db.get_value("Projects Settings", "Projects Settings", "ignore_employee_time_overlap")
	val2 = frappe.db.get_value("Projects Settings", "Projects Settings", "ignore_user_time_overlap")
	ignore_overlap = (int(val1 or 0) == 1) or (int(val2 or 0) == 1)
	
	if not ignore_overlap:
		existing_timer = frappe.db.sql("""
			SELECT task, subject FROM `tabActive Task Timer` WHERE user = %s AND task != %s
		""", (user, task), as_dict=True)
		
		if existing_timer:
			existing_timer = existing_timer[0]
			frappe.throw(_("Another task is already running: {0}. Please stop it before starting a new one.").format(existing_timer.subject or existing_timer.task))

	timer_name = frappe.db.get_value("Active Task Timer", {"user": user, "task": task})

	if timer_name:
		doc = frappe.get_doc("Active Task Timer", timer_name)
	else:
		doc = frappe.new_doc("Active Task Timer")
		doc.user = user
		doc.task = task
	
	doc.flags.ignore_permissions = True
	
	doc.project = project
	doc.subject = subject
	doc.start_time = start_time
	doc.save(ignore_permissions=True)
	frappe.db.commit() 

	all_timers = get_active_timer()
	frappe.publish_realtime("one_compliance_timer_update", all_timers, user=user)

	return all_timers

@frappe.whitelist()
def stop_active_timer(task=None):
	"""
		Stop the active timer for the current user, optionally filtering by task.
	"""
	user = frappe.session.user
	filters = {"user": user}
	if task:
		filters["task"] = task
	
	timer_names = frappe.get_all("Active Task Timer", filters=filters, pluck="name", ignore_permissions=True)
	for name in timer_names:
		frappe.delete_doc("Active Task Timer", name, ignore_permissions=True)
	
	frappe.db.commit()
	
	all_timers = get_active_timer()
	frappe.publish_realtime("one_compliance_timer_update", all_timers, user=user)
	return all_timers

@frappe.whitelist()
def get_active_timer():
	"""
		Retrieve the active timer for the current user, ensuring proper permissions and handling guest users.
	"""
	user = frappe.session.user
	if not user or user == 'Guest':
		return []
	
	timers = frappe.db.sql("""
		SELECT task, project, subject, start_time FROM `tabActive Task Timer` WHERE user = %s
	""", (user,), as_dict=True)
	
	return timers