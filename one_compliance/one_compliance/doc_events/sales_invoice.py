import frappe
from frappe import _
from frappe.model.naming import make_autoname

def sales_invoice_on_submit(doc, method):
	for item in doc.items:
		if item.sales_order:
			sales_order_status = frappe.db.get_value(
				"Sales Order", item.sales_order, "workflow_state"
			)
			if sales_order_status == "In Progress":
				frappe.db.set_value(
					"Sales Order", item.sales_order, "workflow_state", "Pre-Invoice"
				)
				break
			else:
				frappe.db.set_value(
					"Sales Order", item.sales_order, "workflow_state", "Invoiced"
				)

def autoname(doc, method=None):
	if doc.company and doc.custom_invoice_type:
		compliance_settings = frappe.get_doc("Compliance Settings")
		invoice_series_name = ''
		for series in compliance_settings.invoice_series:
			if series.company  == doc.company and doc.custom_invoice_type == series.invoice_type and series.sales_invoice_series:
				invoice_series_name = series.sales_invoice_series
		if invoice_series_name:
			doc.name = frappe.model.naming.make_autoname(invoice_series_name)
		else:
			frappe.throw(_("Naming Series is not created"))

@frappe.whitelist()
def create_tds_journal_entry(sales_invoice, customer, tds_account, tds_amount):
	sales_invoice_doc = frappe.get_doc('Sales Invoice', sales_invoice)
	tds_amount = float(tds_amount)
	if tds_amount <= 0:
		frappe.throw("TDS Amount must be greater than zero.")
	je = frappe.new_doc('Journal Entry')
	je.voucher_type = 'Journal Entry'
	je.posting_date = sales_invoice_doc.posting_date
	je.company = sales_invoice_doc.company
	je.remark = f'TDS Booking for Sales Invoice {sales_invoice}'
	je.append('accounts', {
		'account': sales_invoice_doc.debit_to,
		'party_type': 'Customer',
		'party': customer,
		'debit_in_account_currency': 0.0,
		'credit_in_account_currency': tds_amount,
		'reference_type': 'Sales Invoice',
		'reference_name': sales_invoice
	})
	je.append('accounts', {
		'account': tds_account,
		'debit_in_account_currency': tds_amount,
		'credit_in_account_currency': 0.0
	})
	je.save()
	sales_invoice_doc.paid_amount = tds_amount
	sales_invoice_doc.outstanding_amount = sales_invoice_doc.rounded_total - tds_amount
	sales_invoice_doc.flags.ignore_validate_update_after_submit = True
	sales_invoice_doc.save(ignore_permissions=True)
	frappe.db.commit()
	return je.name
