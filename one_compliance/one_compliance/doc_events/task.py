import frappe
from frappe import _
from one_compliance.one_compliance.utils import send_notification
from one_compliance.one_compliance.utils import send_notification_to_roles
from frappe.email.doctype.notification.notification import get_context

@frappe.whitelist()
def task_on_update(doc, method):
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
