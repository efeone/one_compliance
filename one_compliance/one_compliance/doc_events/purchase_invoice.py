import frappe


def update_sales_order(doc, method):
	"""
	Update linked Sales Order's payment status and outstanding amount
	"""
	frappe.db.set_value(
		"Sales Order",
		doc.sales_order,
		{
			"payment_status": doc.status,
			"outstanding_amount": doc.outstanding_amount
		},
		update_modified=False
	)

def update_commission_status_in_customer(doc, method=None):
	"""
	Update referral commission status in Customer doctype when a Commission Invoice is paid.
	"""
	if not doc.is_commission_invoice:
		return
	if not doc.customer:
		return
	customer = frappe.get_doc("Customer", doc.customer)

	for row in customer.reference_details:
		if row.purchase_invoice == doc.name:
			row.status = doc.status

	customer.save(ignore_permissions=True)	