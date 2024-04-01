import frappe
from frappe import _
from one_compliance.one_compliance.utils import send_notification
from one_compliance.one_compliance.utils import send_notification_to_roles
from frappe.email.doctype.notification.notification import get_context
from frappe.utils import *
from erpnext.accounts.party import get_party_account
from erpnext.accounts.doctype.sales_invoice.sales_invoice import get_mode_of_payment_info

@frappe.whitelist()
def append_users_to_project(doc, method):
	if doc.assigned_to and doc.project:
		if frappe.db.exists('Employee Group', doc.assigned_to):
			employee_group = frappe.get_doc('Employee Group', doc.assigned_to)
			for employee in employee_group.employee_list:
				if employee.user_id:
					add_project_user_if_not_exists(doc.project, employee.user_id)
@frappe.whitelist()
def set_task_status_to_hold(doc, method):
	if doc.hold == 1:
		frappe.db.set_value("Task", doc.name, "status", "Hold")

@frappe.whitelist()
def update_expected_dates_in_task(doc):
	if doc.doctype == "Task":
		doc.exp_start_date = frappe.utils.today()
		doc.exp_end_date = add_days(doc.exp_start_date, doc.duration)
		doc.save()
	frappe.db.commit()

def add_project_user_if_not_exists(project, user_id):
	project_doc = frappe.get_doc('Project', project)
	exists = False
	for project_user in project_doc.users:
		if project_user.user == user_id:
			exists = True
	if not exists:
		project_doc.append('users', {
			'user': user_id
		})
		project_doc.save()

@frappe.whitelist()
def task_on_update(doc, method):
	set_task_time_line(doc)
	if doc.status == 'Completed':
		task_complete_notification_for_director(doc)
		if doc.custom_is_payable:
			create_journal_entry(doc)
		if doc.project:
			if frappe.db.exists('Project', doc.project):
				project = frappe.get_doc ('Project', doc.project)
				if project.status == 'Completed':
					send_project_completion_mail = frappe.db.get_value('Customer', project.customer, 'send_project_completion_mail')
					if send_project_completion_mail:
						email_id = frappe.db.get_value('Customer', project.customer, 'email_id')
						if email_id:
							project_complete_notification_for_customer(project, email_id)
		# Check if this task is a dependency for other tasks
		dependent_tasks = frappe.get_all('Task Depends On', filters={'task': doc.name}, fields=['parent'])
		for dependent_task in dependent_tasks:
			task = frappe.get_doc('Task', dependent_task.parent)
			all_dependencies_completed = True
			# Check if all dependent tasks are completed
			for dependency in task.depends_on:
				dependency_doc = frappe.get_doc('Task', dependency.task)
				if dependency_doc.status != 'Completed':
					all_dependencies_completed = False
					break
			# If all dependencies are completed, mark the dependent task as completed
			if all_dependencies_completed and task.status != 'Completed':
				task.status = 'Completed'
				task.save()

@frappe.whitelist()
def task_complete_notification_for_director(doc):
	context = get_context(doc)
	send_notification_to_roles(doc, 'Director', context, 'task_complete_notification_for_director')

@frappe.whitelist()
def create_journal_entry(doc):
	if doc.custom_payable_amount and doc.custom_mode_of_payment:
		account = get_party_account('Customer', doc.customer, doc.company)
		payment_account = get_mode_of_payment_info(doc.custom_mode_of_payment, doc.company)
		default_account = payment_account[0]['default_account']
		journal_entry = frappe.new_doc('Journal Entry')
		journal_entry.voucher_type = 'Bank Entry'
		journal_entry.cheque_no = doc.custom_reference_number
		journal_entry.cheque_date = doc.custom_reference_date
		journal_entry.user_remark = doc.custom_user_remark
		journal_entry.posting_date = frappe.utils.today()
		journal_entry.append('accounts', {
            'account': account,
            'party_type': 'Customer',
            'party': doc.customer,
            'debit_in_account_currency': doc.custom_payable_amount
        })
		journal_entry.append('accounts', {
            'account': default_account,
            'credit_in_account_currency': doc.custom_payable_amount
        })
		journal_entry.insert(ignore_permissions = True)
		frappe.msgprint("Journal Entry is created Successfully", alert=True)

@frappe.whitelist()
def project_complete_notification_for_customer(doc, email_id):
	context = get_context(doc)
	send_notification(doc, email_id, context, 'project_complete_notification_for_customer')

@frappe.whitelist()
def set_task_time_line(doc):
	if doc.duration and doc.exp_start_date:
		exp_end_date = add_days(doc.exp_start_date, doc.duration)
		doc.db_set('exp_end_date', exp_end_date, update_modified=False)
		frappe.db.commit()

@frappe.whitelist()
def make_sales_invoice(doc, method):
	# The sales invoice will be automatic on the on update of the project
	if doc.status == 'Completed':
		if frappe.db.exists('Project', doc.project):
			project = frappe.get_doc ('Project',doc.project)
			if project.status == 'Completed':
				if frappe.db.exists('Compliance Sub Category', project.compliance_sub_category):
					sub_category_doc = frappe.get_doc('Compliance Sub Category', project.compliance_sub_category)
					if sub_category_doc.is_billable:
						if frappe.db.exists('Sales Order', project.sales_order):
							payment_terms = frappe.db.get_value('Sales Order', project.sales_order,'payment_terms_template')
							rate = get_rate_from_sales_order(project.sales_order, project.compliance_sub_category)
							rate = rate if rate else sub_category_doc.rate
							if not frappe.db.exists('Sales Invoice', {'project':project.name}):
								create_sales_invoice(project, payment_terms, rate, sub_category_doc)
						elif frappe.db.exists('Compliance Agreement', project.compliance_agreement):
							invoice_based_on = frappe.db.get_value('Compliance Agreement', project.compliance_agreement, 'invoice_based_on')
							payment_terms = frappe.db.get_value('Compliance Agreement', project.compliance_agreement,'default_payment_terms_template')
							rate = get_rate_from_compliance_agreement(project.compliance_agreement, project.compliance_sub_category)
							rate = rate if rate else sub_category_doc.rate
							if invoice_based_on == 'Project' and not frappe.db.exists('Sales Invoice', {'project':project.name}):
								create_sales_invoice(project, payment_terms, rate, sub_category_doc)
								frappe.db.set_value('Project', project.name, 'is_invoiced', 1)

@frappe.whitelist()
def create_sales_invoice(project, payment_terms, rate, sub_category_doc):
	sales_invoice = frappe.new_doc('Sales Invoice')
	sales_invoice.customer = project.customer
	sales_invoice.posting_date = frappe.utils.today()
	sales_invoice.project = project.name
	sales_invoice.company = project.company
	sub_category_income_account = sub_category_doc.income_account
	income_account = sub_category_income_account if sub_category_income_account else frappe.db.get_value('Company',project.company, 'default_income_account')

	if payment_terms:
		sales_invoice.default_payment_terms_template = payment_terms
	sales_invoice.append('items', {
		'item_code' : sub_category_doc.item_code,
		'item_name' : sub_category_doc.sub_category,
		'rate' : rate,
		'qty' : 1,
		'income_account' : income_account,
		'description' : project.custom_project_service,
		'cost_center' : project.cost_center
	})
	sales_invoice.save(ignore_permissions=True)

@frappe.whitelist()
def update_task_status(task_id, status, completed_by, completed_on):
	# Load the task document from the database
	task_doc = frappe.get_doc("Task", task_id)
	task_doc.completed_on = frappe.utils.getdate(completed_on)
	task_doc.status = status
	task_doc.completed_by = completed_by
	task_doc.save()
	frappe.db.commit()
	frappe.msgprint("Task Status has been set to {0}".format(status), alert=True)
	return True

@frappe.whitelist()
def get_permission_query_conditions(user):

	if not user:
		user = frappe.session.user

	user_roles = frappe.get_roles(user)
	if "Administrator" in user_roles:
		return None

	if "Manager" in user_roles or "Executive" in user_roles:
		conditions = """(tabTask._assign like '%{user}%')""" \
			.format(user=user)
		return conditions
	else:
		return None

@frappe.whitelist()
def get_rate_from_sales_order(sales_order, compliance_sub_category):
	rate_result = frappe.db.sql(
		"""
		select rate
		from `tabCompliance Category Details`
		where parent=%s and compliance_sub_category=%s""",
		(sales_order, compliance_sub_category),
		as_dict=1,
		)
	if rate_result:
		return rate_result[0].rate

@frappe.whitelist()
def get_rate_from_compliance_agreement(compliance_agreement, compliance_sub_category):
	rate_result = frappe.db.sql(
		"""
		select rate
		from `tabCompliance Category Details`
		where parent=%s and compliance_sub_category=%s""",
		(compliance_agreement, compliance_sub_category),
		as_dict=1,
		)
	if rate_result:
		return rate_result[0].rate

# Check for uncompleted documents on updation of task to completed
@frappe.whitelist()
def subtask_on_update(doc, event):
    if doc.status == "Completed":
        items = frappe.get_all("Task Document Item", filters={"parent": doc.name}, fields=["is_completed"])
        if any(item.get("is_completed") == 0 for item in items):
            frappe.throw(_("Please complete all documents before marking the task as complete"))