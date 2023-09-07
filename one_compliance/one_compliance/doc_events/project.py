import frappe
from frappe.model.mapper import get_mapped_doc
from one_compliance.one_compliance.utils import send_notification
from frappe.email.doctype.notification.notification import get_context
from one_compliance.one_compliance.doc_events.task import update_expected_dates_in_task

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
def set_project_status(project, status):
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
	project.save()
