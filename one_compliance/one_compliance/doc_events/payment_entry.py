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
                frappe.db.set_value(
                    "Sales Order", sales_order, "workflow_state", "Paid"
                )
            elif (
                payment_reference.allocated_amount
                < payment_reference.outstanding_amount
            ):
                frappe.db.set_value(
                    "Sales Order", sales_order, "workflow_state", "Partially Paid"
                )


def payment_entry_on_cancel(doc, method):
    """method sets workflow for Sales Order if the Payment Entry is referenced to an SI against it"""
    for payment_reference in doc.references:
        if payment_reference.reference_doctype == "Sales Invoice":
            sales_order = frappe.db.get_value(
                "Sales Invoice Item",
                {"parent": payment_reference.reference_name},
                "sales_order",
            )
            sales_invoice_doc = frappe.get_doc(
                "Sales Invoice", payment_reference.reference_name
            )
            if sales_invoice_doc.outstanding_amount == 0:
                frappe.db.set_value(
                    "Sales Order", sales_order, "workflow_state", "Paid"
                )
            elif sales_invoice_doc.rounded_total > sales_invoice_doc.outstanding_amount:
                frappe.db.set_value(
                    "Sales Order", sales_order, "workflow_state", "Partially Paid"
                )
            else:
                frappe.db.set_value(
                    "Sales Order", sales_order, "workflow_state", "Invoiced"
                )
