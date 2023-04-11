import frappe
from frappe.model.mapper import get_mapped_doc
from one_compliance.one_compliance.utils import send_notification
from frappe.email.doctype.notification.notification import get_context

@frappe.whitelist()
def make_sales_invoice(doc, method):
	# *The sales invoice will be automatic on the on update of the project*
	if doc.status == 'Completed':
		sales_invoice = frappe.new_doc('Sales Invoice')
		sales_invoice.customer = doc.customer
		sales_invoice.posting_date = frappe.utils.today()
		income_account = frappe.db.get_value('Company',doc.company, 'default_income_account')
		payment_terms = frappe.db.get_value('Compliance Agreement', doc.compliance_agreement,'default_payment_terms_template')
		if payment_terms:
			sales_invoice.default_payment_terms_template = payment_terms
		if frappe.db.exists('Compliance Agreement', doc.compliance_agreement):
			compliance_agreement = frappe.get_doc ('Compliance Agreement', doc.compliance_agreement)
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
		sales_invoice.save()

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
