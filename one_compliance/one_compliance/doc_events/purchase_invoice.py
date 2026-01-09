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
