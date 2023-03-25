import frappe
from frappe import _
from one_compliance.one_compliance.utils import send_notification
from one_compliance.one_compliance.utils import send_notification_to_roles
from frappe.email.doctype.notification.notification import get_context

@frappe.whitelist()
def task_on_update(doc, method):
    if doc.status == 'Completed':
        task_complete_notification_for_director(doc)

@frappe.whitelist()
def task_complete_notification_for_director(doc):
    context = get_context(doc)
    send_notification_to_roles(doc, 'Director', context, 'task_complete_notification_for_director')
