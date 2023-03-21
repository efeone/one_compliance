import frappe
import json
from frappe.utils import *
from frappe.email.doctype.notification.notification import get_context

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
def create_todo(doctype, name, assign_to, owner, description):
    ''' Method used for create ToDo '''
    todo = frappe.new_doc('ToDo')
    todo.status = 'Open'
    todo.owner = owner
    todo.reference_type = doctype
    todo.reference_name = name
    todo.description = description
    todo.allocated_to = assign_to
    todo.date = frappe.utils.today()
    todo.save(ignore_permissions = True)

@frappe.whitelist()
def sent_email_notification():
    tasks = frappe.db.get_all('Task')
    if tasks:
        for task in tasks:
            doc = frappe.get_doc('Task',task.name)
            assigns = frappe.db.get_value('Task', doc.name, '_assign')
            if assigns:
                assigns = json.loads(assigns)
                for assign in assigns:
                    context = get_context(doc)
                    if assign:
                        today = frappe.utils.today()
                        days_diff = date_diff(getdate(doc.expected_time), today)
                        if days_diff == 1:
                            sub_doc = frappe.db.get_value('Compliance Sub Category', doc.compliance_sub_category, 'task_before_due_date__notification')
                            if sub_doc:
                                subject_template, content_template = frappe.db.get_value('Notification Template', sub_doc, ['subject', 'content'])
                                subject = frappe.render_template(subject_template, context)
                                content = frappe.render_template(content_template, context)
                                create_notification_log(subject, 'Mention', assign, content, doc.doctype, doc.name)
                        if days_diff == 0:
                            sub_doc = frappe.db.get_value('Compliance Sub Category', doc.compliance_sub_category, 'task_overdue_notification')
                            if sub_doc:
                                subject_template, content_template = frappe.db.get_value('Notification Template', sub_doc, ['subject', 'content'])
                                subject = frappe.render_template(subject_template, context)
                                content = frappe.render_template(content_template, context)
                                create_notification_log(subject, 'Mention', assign, content, doc.doctype, doc.name)
