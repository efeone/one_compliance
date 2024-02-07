import frappe
from frappe import _
from one_compliance.one_compliance.utils import send_notification
from one_compliance.one_compliance.utils import send_notification_to_roles
from frappe.email.doctype.notification.notification import get_context
from frappe.utils import *

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
		if doc.project:
			if frappe.db.exists('Project', doc.project):
				project = frappe.get_doc ('Project', doc.project)
				if project.status == 'Completed':
					send_project_completion_mail = frappe.db.get_value('Customer', project.customer, 'send_project_completion_mail')
					if send_project_completion_mail:
						email_id = frappe.db.get_value('Customer', project.customer, 'email_id')
						if email_id:
							project_complete_notification_for_customer(project, email_id)

@frappe.whitelist()
def task_complete_notification_for_director(doc):
	context = get_context(doc)
	send_notification_to_roles(doc, 'Director', context, 'task_complete_notification_for_director')

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
						if frappe.db.exists('Compliance Agreement', project.compliance_agreement):
							invoice_based_on = frappe.db.get_value('Compliance Agreement', project.compliance_agreement, 'invoice_based_on')
							if invoice_based_on == 'Project' and not frappe.db.exists('Sales Invoice', {'project':project.name}):
								sales_invoice = frappe.new_doc('Sales Invoice')
								sales_invoice.customer = project.customer
								sales_invoice.posting_date = frappe.utils.today()
								sales_invoice.project = project.name
								sales_invoice.company = project.company
								sub_category_income_account = sub_category_doc.income_account
								income_account = sub_category_income_account if sub_category_income_account else frappe.db.get_value('Company',project.company, 'default_income_account')
								payment_terms = frappe.db.get_value('Compliance Agreement', project.compliance_agreement,'default_payment_terms_template')
								rate = get_rate_from_compliance_agreement(project.compliance_agreement, project.compliance_sub_category)
								rate = rate if rate else sub_category_doc.rate
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
								if project.custom_have_reimbursement:
									reimbursement_item = project.custom_reimbursement_item if project.custom_reimbursement_item else frappe.db.get_single_value("Compliance Settings", 'default_reimbursement_item')
									reimbursement_income_account =project.custom_reimbursement_income_account if project.custom_reimbursement_income_account else frappe.db.get_single_value("Compliance Settings", 'default__reimbursement_income_account')
									item_code, item_name, description = frappe.db.get_value('Item', reimbursement_item , ['name', 'item_name', 'description'])
									reimbursement_amount = project.custom_reimbursement_amount or 0
									sales_invoice.append('items', {
										'item_code' : item_code,
										'item_name' : item_name,
										'rate' : reimbursement_amount,
										'qty' : 1,
										'income_account' : reimbursement_income_account,
										'description' : description
									})
								sales_invoice.save(ignore_permissions=True)
								frappe.db.set_value('Project', project.name, 'is_invoiced', 1)

@frappe.whitelist()
def check_payable_task(task):
	task_template = frappe.get_all("Task", filters = {"subject":task, "status":"Template"}, fields = ['name','custom_is_payable'])
	if task_template:
		is_payable = task_template[0].get("custom_is_payable")
		if(is_payable):
			return True
		else:
			return False

@frappe.whitelist()
def check_reimbursement(project_id):
	project = frappe.get_doc("Project", project_id)
	have_reimbursement = project.get("custom_reimbursement_amount") if project else None
	if have_reimbursement != 0.00:
		return True
	else:
		return False

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
