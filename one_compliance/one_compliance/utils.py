import frappe
import json
from frappe.utils import *
from frappe.email.doctype.notification.notification import get_context



@frappe.whitelist()
def create_todo(doctype, name, assign_to, owner, description):
    todo = frappe.new_doc('ToDo')
    todo.status = 'Open'
    todo.owner = owner
    todo.reference_doctype = doctype
    todo.reference_name = name
    todo.description = description
    todo.assigned_by = assign_to
    todo.date = frappe.utils.today()
    todo.save(ignore_permissions = True)

@frappe.whitelist()
def create_notification_log(subject, type, for_user, email_content, document_type, document_name):
    ''' Method to Create Notification Log '''
    notification_doc = frappe.new_doc('Notification Log')
    notification_doc.subject = subject
    notification_doc.type = type
    notification_doc.for_user = for_user
    notification_doc.email_content = email_content
    notification_doc.document_type = document_type
    notification_doc.document_name = document_name
    notification_doc.save()
    frappe.db.commit()

@frappe.whitelist()
def sent_ovderdue_notification_to_employee(doc, method):
    assigns = json.loads(frappe.db.get_value('Task', doc.name, '_assign'))
    if assigns:
        for assign in assigns:
            context = get_context(doc)
            if assign:
                if doc.status == 'Overdue':
                    if frappe.db.exists('Notification Template', {'doctype_name':'Task', 'notification_name':'Task Overdue'}):
                        subject_template, content_template = frappe.db.get_value('Notification Template', {'doctype_name':'Task', 'notification_name':'Task Overdue'}, ['subject', 'content'])
                        subject = frappe.render_template(subject_template, context)
                        content = frappe.render_template(content_template, context)
                        create_notification_log(subject, 'Mention', assign, content, doc.doctype, doc.name)
