import frappe
from frappe.model.mapper import get_mapped_doc
from one_compliance.one_compliance.utils import send_notification
from frappe.email.doctype.notification.notification import get_context

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
