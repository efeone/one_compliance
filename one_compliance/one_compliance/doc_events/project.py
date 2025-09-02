import frappe
from frappe import _
from frappe.email.doctype.notification.notification import get_context
from frappe.utils import add_days, getdate, today
from one_compliance.one_compliance.doc_events.task import (
	create_sales_order,
	get_rate_from_compliance_agreement,
	update_expected_dates_in_task,
)
from one_compliance.one_compliance.utils import (
	create_project_completion_todos,
	send_notification,
)


@frappe.whitelist()
def project_on_update(doc, method):
	is_not_rework = doc.sales_order and not frappe.db.get_value("Sales Order", doc.sales_order, "custom_is_rework")

	if doc.status == 'Completed':
		if is_not_rework:
			create_project_completion_todos(doc.sales_order, doc.project_name)

		send_project_completion_mail = frappe.db.get_value('Customer', doc.customer, 'send_project_completion_mail')
		if send_project_completion_mail:
			email_id = frappe.db.get_value('Customer', doc.customer, 'email_id')
			if email_id and frappe.db.get_single_value('Compliance Settings', 'enable_project_complete_notification_for_customer'):
				project_complete_notification_for_customer(doc, email_id)

	if is_not_rework:
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
	if status not in ("Open","Completed", "Cancelled", "Hold"):
		frappe.throw(_("Status must be or Open or Hold Cancelled or Completed"))

	project = frappe.get_doc("Project", project)
	frappe.has_permission(doc=project, throw=True)
	tasks = frappe.get_all("Task", filters={"project": project.name}, fields=["name", "status"])
	for task in tasks:
		if task.status == "Completed":
			continue
		frappe.db.set_value("Task", task.name, "status", status)
		if status == "Hold":
			frappe.db.set_value("Task", task.name, "hold", 1)
		else:
			frappe.db.set_value("Task", task.name, "hold", 0)
			task_doc = frappe.get_doc('Task', task.name)
			update_expected_dates_in_task(task_doc)
	frappe.db.set_value("Project", project.name, "status", status)
	if status == "Hold":
		frappe.db.set_value("Project", project.name, "hold", 1)
	elif status == "Open":
		frappe.db.set_value("Project", project.name, "hold", 0)
	if comment:
		project.add_comment('Comment', comment)

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
			if not sales_order:
				sales_order = frappe.db.exists("Sales Order", {"project":doc.name})
				if sales_order:
					doc.sales_order = sales_order
					doc.save(ignore_permissions=True)
			if sales_order:
				frappe.db.set_value("Sales Order", sales_order, "status", "Proforma Invoice")
				frappe.db.set_value("Sales Order", sales_order, "workflow_state", "Proforma Invoice")
				frappe.db.set_value("Sales Order", sales_order, "invoice_generation_date", today())
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


@frappe.whitelist()
def convert_project_to_premium(project):
    """
    Convert Project to Premium by adding its associated Premium Tasks.
    """
    try:
        project_doc = frappe.get_doc("Project", project)

        if not project_doc.compliance_sub_category:
            return "no_sub_category"

        sub_category_doc = frappe.get_doc("Compliance Sub Category", project_doc.compliance_sub_category)

        if not sub_category_doc.project_template:
            return "no_template"

        template_doc = frappe.get_doc("Project Template", sub_category_doc.project_template)

        for premium_task in template_doc.premium_tasks:
            task = frappe.new_doc("Task")
            task.subject = premium_task.subject
            task.project = project_doc.name
            task.expected_time = premium_task.task_duration or 0
            task.task_weightage = premium_task.task_weightage or 0
            task.save()

        project_doc.is_premium = 1
        project_doc.save()

        return "success"

    except Exception:
        frappe.log_error(frappe.get_traceback(), "Convert Project to Premium Error")
        return "failed"
