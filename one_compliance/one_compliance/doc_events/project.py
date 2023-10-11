import frappe
from frappe.model.mapper import get_mapped_doc
from one_compliance.one_compliance.utils import send_notification
from frappe.email.doctype.notification.notification import get_context
from one_compliance.one_compliance.doc_events.task import update_expected_dates_in_task
from frappe.utils import *

@frappe.whitelist()
def project_on_update(doc, method):
	if doc.status == 'Completed':
		send_project_completion_mail = frappe.db.get_value('Customer', doc.customer, 'send_project_completion_mail')
		if send_project_completion_mail:
			email_id = frappe.db.get_value('Customer', doc.customer, 'email_id')
			if email_id:
				project_complete_notification_for_customer(doc, email_id)

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
def update_expected_end_date_in_project(doc, method):
	if not doc.expected_end_date and doc.compliance_sub_category:
		project_template = frappe.db.get_value('Compliance Sub Category', doc.compliance_sub_category, 'project_template')
		if doc.expected_start_date and project_template:
			project_duration = frappe.db.get_value('Project Template', project_template, 'custom_project_duration')
			doc.expected_end_date = add_days(doc.expected_start_date, project_duration)
			doc.save()
		frappe.db.commit

@frappe.whitelist()
def set_status_to_overdue():
	projects = frappe.db.get_all('Project', filters= {'status': ['not in',['Cancelled','Hold','Completed']]})
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


