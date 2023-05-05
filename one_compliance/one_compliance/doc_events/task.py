import frappe
from frappe import _
from one_compliance.one_compliance.utils import send_notification
from one_compliance.one_compliance.utils import send_notification_to_roles
from frappe.email.doctype.notification.notification import get_context
from frappe.utils import *

@frappe.whitelist()
def task_on_update(doc, method):
    set_task_time_line(doc)
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

@frappe.whitelist()
def set_task_time_line(doc):
    if doc.duration and doc.exp_start_date:
        exp_end_date = add_days(doc.exp_start_date, doc.duration)
        doc.db_set('exp_end_date', exp_end_date, update_modified=False)
        frappe.db.commit()

@frappe.whitelist()
def make_sales_invoice(doc, method):
    # *The sales invoice will be automatic on the on update of the project*
    if doc.status == 'Completed':
        if frappe.db.exists('Project', doc.project):
            project = frappe.get_doc ('Project',doc.project)
            if project.status == 'Completed':
                if frappe.db.exists('Compliance Agreement', project.compliance_agreement):
                    compliance_agreement = frappe.get_doc ('Compliance Agreement', project.compliance_agreement)
                    if compliance_agreement.invoice_based_on == 'Project':
                        sales_invoice = frappe.new_doc('Sales Invoice')
                        sales_invoice.customer = project.customer
                        sales_invoice.posting_date = frappe.utils.today()
                        sales_invoice.project = project.name
                        income_account = frappe.db.get_value('Company',project.company, 'default_income_account')
                        payment_terms = frappe.db.get_value('Compliance Agreement', project.compliance_agreement,'default_payment_terms_template')
                        if payment_terms:
                            sales_invoice.default_payment_terms_template = payment_terms
                        if compliance_agreement.compliance_category_details:
                            for sub_category in compliance_agreement.compliance_category_details:
                                if frappe.db.exists('Compliance Sub Category', sub_category.compliance_sub_category):
                                    sub_category_doc = frappe.get_doc('Compliance Sub Category', sub_category.compliance_sub_category)
                                    if doc.compliance_sub_category == sub_category.compliance_sub_category:
                                        sales_invoice.append('items', {
                                        'item_name' : sub_category.compliance_sub_category,
                                        'rate' : sub_category_doc.rate,
                                        'qty' : 1,
                                        'income_account' : income_account,
                                        'description' : sub_category_doc.name
                                        })
                        sales_invoice.save(ignore_permissions=True)
