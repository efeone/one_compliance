import frappe
import json
from frappe.utils import *
from frappe.model.document import Document
from frappe.email.doctype.notification.notification import get_context
from frappe.utils.user import get_users_with_role
from frappe import _
from dateutil.relativedelta import relativedelta
import datetime
from datetime import date

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
def task_daily_sheduler():
    """ Method to send task before due date and overdue notification to employee and task overdue and no action taken notification to director"""
    tasks = frappe.db.get_all('Task', filters= {'status': ['not in', ['Template', 'Completed', 'Cancelled']]})
    if tasks:
        for task in tasks:
            doc = frappe.get_doc('Task', task.name)
            assigns = frappe.db.get_value('Task', doc.name, '_assign')
            if assigns:
                assigns = json.loads(assigns)
                for assign in assigns:
                    context = get_context(doc)
                    if assign:
                        today = frappe.utils.today()
                        if doc.exp_end_date:
                            days_diff = date_diff(getdate(doc.exp_end_date), getdate(today))
                            if days_diff == 0:
                                send_notification(doc, assign, context, 'task_overdue_notification_for_employee')
                                send_notification_to_roles(doc, 'Director', context, 'task_overdue_notification_for_director')
                            if days_diff == 1:
                                send_notification(doc, assign, context, 'task_before_due_date__notification')
                        if doc.exp_start_date:
                            if doc.status == 'Open' and (getdate(doc.exp_start_date) < getdate(today)):
                                send_notification_to_roles(doc, 'Director', context, 'no_action_taken_notification_for_director')

@frappe.whitelist()
def send_notification(doc, for_user, context, notification_template_fieldname):
    ''' Method to send notification for daily task scheduling using Notification Template '''
    notification_template = frappe.db.get_value('Compliance Sub Category', doc.compliance_sub_category, notification_template_fieldname)
    if notification_template:
        subject_template, content_template = frappe.db.get_value('Notification Template', notification_template, ['subject', 'content'])
        subject = frappe.render_template(subject_template, context)
        content = frappe.render_template(content_template, context)
        create_notification_log(subject, 'Mention', for_user, content, doc.doctype, doc.name)

@frappe.whitelist()
def send_notification_to_roles(doc, role, context, notification_template_fieldname):
    """ Method to send notification to perticular role """
    users = get_users_with_role(role)
    for user in users:
        send_notification(doc, user, context, notification_template_fieldname)

@frappe.whitelist()
def view_credential_details(customer,purpose):
    """ Method to view customer Credential details """
    if frappe.db.exists('Customer Credentials',{'customer':customer}):
        customer_credential = frappe.db.get_value('Customer Credentials',{'customer':customer})
        if frappe.db.exists('Credential Details', {'parent':customer_credential,'purpose':purpose}):
            username, password, url = frappe.db.get_value('Credential Details', {'parent':customer_credential,'purpose':purpose}, ['username', 'password','url'])
            return [username, password, url]
        else:
            frappe.throw(_('Credential not configured for this Purpose'))

@frappe.whitelist()
def view_customer_documents(customer,compliance_sub_category):
    """ Method to view customer documents """
    if frappe.db.exists('Customer Document',{'customer':customer}):
        customer_document =frappe.db.get_value('Customer Document',{'customer':customer})
        if frappe.db.exists('Customer Document Record',{'parent':customer_document,'compliance_sub_category':compliance_sub_category}):
            document_attachment = frappe.db.get_value('Customer Document Record',{'parent':customer_document,'compliance_sub_category':compliance_sub_category}, ['document_attachment'])
            return [document_attachment]
        else:
            frappe.throw(_('Document not attached for this sub category'))



@frappe.whitelist()
def edit_customer_credentials(customer):
    """ Method to edit or add customer Credential """
    if frappe.db.exists('Customer Credentials',{'customer':customer}):
        customer_credential = frappe.db.get_value('Customer Credentials',{'customer':customer})
        return customer_credential

@frappe.whitelist()
def update_digital_signature(digital_signature, register_type, register_name):
    """ Method to append values to child table digital signature details from inward and outward register """
    if digital_signature and register_name and register_type:
        if not frappe.db.exists('Digital Signature', digital_signature):
            frappe.throw("Digital signature does not exists")
        if not frappe.db.exists(register_type, register_name):
            frappe.throw("Register does not exists")
        digital_signature_doc = frappe.get_doc('Digital Signature', digital_signature)
        register_doc = frappe.get_doc(register_type, register_name)
        digital_signature_detail = digital_signature_doc.append('digital_signature_details')
        digital_signature_detail.register_type = register_doc.doctype
        digital_signature_detail.reference_id = register_doc.name
        if register_type == 'Inward Register':
            digital_signature_detail.posting_date = register_doc.posting_date
            digital_signature_detail.posting_time = register_doc.posting_time
            digital_signature_detail.sender_receiver = register_doc.person_name
        else:
            if register_type == 'Outward Register':
                digital_signature_detail.posting_date = register_doc.returned_date
                digital_signature_detail.posting_time = register_doc.returned_time
                digital_signature_detail.sender_receiver = register_doc.receiver_name
        digital_signature_doc.save()
        frappe.db.commit()
        digital_signature_doc.reload()
        return True

@frappe.whitelist()
def daily_notification_for_digital_signature_expiry():
    ''' Method to send daily notification for notifying Digital Signature expiration to director email '''
    digital_signature = frappe.get_all('Digital Signature')
    if digital_signature:
        today = getdate(frappe.utils.today())
        for digital_signature_docs in digital_signature:
            doc = frappe.get_doc('Digital Signature', digital_signature_docs.name)
            context = get_context(doc)
            director_mail = doc.director_email
            due_date = getdate(doc.expiry_date)
            notification_date = ''
            if doc.notify_on_expiration == 1:
                if doc.notify_before_unit == 'Day':
                    if doc.notify_before:
                        notification_date = frappe.utils.add_to_date(due_date, days=-1*doc.notify_before)
        if getdate(notification_date) == today:
            send_notification_for_digital_signature(doc, director_mail, context, 'digital_signature_expiry_notification')

@frappe.whitelist()
def weekly_notification_for_digital_signature_expiry():
    ''' Method to send weekly notification for notifying Digital Signature expiration to director email '''
    digital_signature = frappe.get_all('Digital Signature')
    if digital_signature:
        today = getdate(frappe.utils.today())
        for digital_signature_docs in digital_signature:
            doc = frappe.get_doc('Digital Signature', digital_signature_docs.name)
            context = get_context(doc)
            director_mail = doc.director_email
            due_date = getdate(doc.expiry_date)
            notification_date = ''
            if doc.notify_on_expiration == 1:
                if doc.notify_before_unit == 'Week':
                    if doc.notify_before:
                        notification_date = frappe.utils.add_to_date(due_date, days=-7*doc.notify_before)
        if getdate(notification_date) == today:
            send_notification_for_digital_signature(doc, director_mail, context, 'digital_signature_expiry_notification')

@frappe.whitelist()
def monthly_notification_for_digital_signature_expiry():
    ''' Method to send Monthly notification for notifying Digital Signature expiration to director email '''
    digital_signature = frappe.get_all('Digital Signature')
    if digital_signature:
        today = getdate(frappe.utils.today())
        for digital_signature_docs in digital_signature:
            doc = frappe.get_doc('Digital Signature', digital_signature_docs.name)
            context = get_context(doc)
            director_mail = doc.director_email
            due_date = getdate(doc.expiry_date)
            notification_date = ''
            if doc.notify_on_expiration == 1:
                if doc.notify_before_unit == 'Month':
                    if doc.notify_before:
                        notification_date = due_date + relativedelta(months=-doc.notify_before)
        if getdate(notification_date) == today:
            send_notification_for_digital_signature(doc, director_mail, context, 'digital_signature_expiry_notification')

@frappe.whitelist()
def send_notification_for_digital_signature(doc, for_user, context, notification_template_fieldname):
    ''' Method to send email for digital signature expiration using Notification Template '''
    notification_template = frappe.db.get_value('Digital Signature', doc.name, notification_template_fieldname)
    if notification_template:
        subject_template, content_template = frappe.db.get_value('Notification Template', notification_template, ['subject', 'content'])
        subject = frappe.render_template(subject_template, context)
        content = frappe.render_template(content_template, context)
        frappe.sendmail(recipients=[for_user], subject=subject, message=content)
        frappe.db.commit()
