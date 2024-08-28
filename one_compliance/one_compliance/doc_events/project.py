import frappe
from frappe.model.mapper import get_mapped_doc
from one_compliance.one_compliance.utils import create_project_completion_todos, send_notification
from frappe.email.doctype.notification.notification import get_context
from one_compliance.one_compliance.doc_events.task import update_expected_dates_in_task
from frappe.utils import *
from one_compliance.one_compliance.doc_events.task import (
	create_sales_order, get_rate_from_compliance_agreement,
	update_expected_dates_in_task)
from frappe.utils.user import get_users_with_role
from frappe.desk.form.assign_to import add as add_assign

@frappe.whitelist()
def project_on_update(doc, method):
	if doc.status == 'Completed':
		if doc.sales_order:
			create_project_completion_todos(doc.sales_order, doc.project_name)

		send_project_completion_mail = frappe.db.get_value('Customer', doc.customer, 'send_project_completion_mail')
		if send_project_completion_mail:
			email_id = frappe.db.get_value('Customer', doc.customer, 'email_id')
			if email_id:
				project_complete_notification_for_customer(doc, email_id)
	if doc.sales_order:
		update_sales_order_billing_instruction(doc.sales_order, doc.custom_billing_instruction)
		
def update_sales_order_billing_instruction(sales_order, custom_billing_instruction):
	"""
	Updates the 'Billing Instruction' field in the Sales Order.
	"""
	if frappe.db.exists('Sales Order', sales_order):
		sales_order_doc = frappe.get_doc('Sales Order', sales_order)
		sales_order_doc.custom_billing_instruction = custom_billing_instruction
		sales_order_doc.save()
	else:
		frappe.throw(_("Sales Order does not exist"))


@frappe.whitelist()
def project_complete_notification_for_customer(doc, email_id):
	context = get_context(doc)
	send_notification(doc, email_id, context, 'project_complete_notification_for_customer')

@frappe.whitelist()
def set_project_status(project, status, comment=None):
	"""
	set status for project and all related tasks
	"""
	if not status in ("Open","Completed", "Cancelled", "Hold"):
		frappe.throw(_("Status must be or Open or Hold Cancelled or Completed"))

	project = frappe.get_doc("Project", project)
	frappe.has_permission(doc=project, throw=True)

	for task in frappe.get_all("Task", dict(project=project.name)):
		frappe.db.set_value("Task", task.name, "status", status)
		if status == "Hold":
			frappe.db.set_value("Task", task.name, "hold", 1)
		else:
			frappe.db.set_value("Task", task.name, "hold", 0)
			task_doc = frappe.get_doc('Task', task.name)
			update_expected_dates_in_task(task_doc)
	project.status = status
	if status == "Hold":
		project.hold = 1
	elif status == "Open":
		project.hold = 0
	if comment:
		project.add_comment('Comment', comment)
	project.save()

@frappe.whitelist()
def project_after_insert(doc, method):
	if not doc.expected_end_date and doc.compliance_sub_category:
		project_template = frappe.db.get_value('Compliance Sub Category', doc.compliance_sub_category, 'project_template')
		if doc.expected_start_date and project_template:
			project_duration = frappe.db.get_value('Project Template', project_template, 'custom_project_duration')
			doc.expected_end_date = add_days(doc.expected_start_date, project_duration)
			doc.save()
		frappe.db.commit

	# Creating a Sales Order after a project is created
	if frappe.db.exists('Compliance Sub Category', doc.compliance_sub_category):
		sub_category_doc = frappe.get_doc('Compliance Sub Category', doc.compliance_sub_category)
		if sub_category_doc.is_billable:
			sales_order = frappe.db.exists('Sales Order', doc.sales_order)
			if sales_order:
				sales_order_status = frappe.db.get_value("Sales Order", sales_order, "workflow_state")
				if sales_order_status == "In Progress":
					frappe.db.set_value("Sales Order", sales_order, "status", "Proforma Invoice")
				elif sales_order_status == "Pre-Invoice":
					frappe.db.set_value("Sales Order", sales_order, "status", "Invoiced")
			else:
				payment_terms = None
				rate = 0
				if frappe.db.exists('Compliance Agreement', doc.compliance_agreement):
					payment_terms = frappe.db.get_value('Compliance Agreement', doc.compliance_agreement,'default_payment_terms_template')
					rate = get_rate_from_compliance_agreement(doc.compliance_agreement, doc.compliance_sub_category)
				create_sales_order(doc, rate, sub_category_doc, payment_terms, submit=True)

@frappe.whitelist()
def set_status_to_overdue():
	projects = frappe.db.get_all('Project', filters= {'status': ['not in',['Cancelled','Hold','Completed', 'Invoiced']]})
	if projects:
		for project in projects:
			doc = frappe.get_doc('Project', project.name)
			today = getdate(frappe.utils.today())
			if today > getdate(doc.expected_end_date):
				frappe.db.set_value('Project', project.name, 'status', 'Overdue')
			frappe.db.commit()

@frappe.whitelist()
def get_permission_query_conditions(user):
	"""
	Method used to set the permission to get the list of docs (Example: list view query)
	Called from the permission_query_conditions of hooks for the DocType Issue
	args:
		user: name of User object or current user
	return conditions query
	"""
	if not user:
		user = frappe.session.user

	user_roles = frappe.get_roles(user)
	if "Administrator" in user_roles:
		return None

	if "Manager" in user_roles or "Executive" in user_roles:
		conditions = """(tabProject._assign like '%{user}%')""" \
			.format(user=user)
		return conditions
	else:
		return None
