import frappe


def payment_entry_on_submit(doc, method):
	"""Sets workflow for Sales Order based on Sales Invoice updated status"""

	for ref in doc.references:

		if ref.reference_doctype == "Sales Invoice":

			si = frappe.get_doc("Sales Invoice", ref.reference_name)

			sales_order = frappe.db.get_value(
				"Sales Invoice Item",
				{"parent": si.name},
				"sales_order",
			)

			outstanding = si.outstanding_amount
			grand_total = si.rounded_total or si.grand_total

			if outstanding == 0:
				new_state = "Paid"
				project_status = "Paid"

			elif outstanding < grand_total:
				new_state = "Partially Paid"
				project_status = "Partially Paid"

			else:
				continue
			frappe.db.set_value("Sales Order", sales_order, "workflow_state", new_state)
			project = frappe.db.get_value("Sales Order", sales_order, "project")
			if project:
				frappe.db.set_value("Project", project, "status", project_status)

def update_commission_status_from_payment(doc, method=None):
	"""
	Update referral commission status in Customer doctype when a Payment Entry linked to a Commission Invoice is submitted or cancelled.
	"""

	for ref in doc.references:
		if ref.reference_doctype != "Purchase Invoice":
			continue
		pi = frappe.get_doc("Purchase Invoice", ref.reference_name)

		if not pi.is_commission_invoice or not pi.customer:
			continue

		customer = frappe.get_doc("Customer", pi.customer)

		updated = False

		for row in customer.reference_details:
			if row.purchase_invoice == pi.name:
				row.status = pi.status
				updated = True
		if updated:
			customer.flags.ignore_version = True
			customer.save(ignore_permissions=True)