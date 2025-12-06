import frappe


def payment_entry_on_submit(doc, method):
	"""method sets workflow for Sales Order if the Payment Entry is referenced to an SI against it"""

	for payment_reference in doc.references:

		if payment_reference.reference_doctype == "Sales Invoice":

			sales_order = frappe.db.get_value(
				"Sales Invoice Item",
				{"parent": payment_reference.reference_name},
				"sales_order",
			)

			if payment_reference.outstanding_amount == 0:
				new_state = "Paid"
				project_status = "Paid"
			elif payment_reference.allocated_amount < payment_reference.outstanding_amount:
					new_state = "Partially Paid"
					project_status = "Partially Paid" 
			else:
				continue
			
			frappe.db.set_value("Sales Order", sales_order, "workflow_state", new_state)
			project = frappe.db.get_value("Sales Order", sales_order, "project")
			if project:
				frappe.db.set_value("Project", project, "status", project_status)
