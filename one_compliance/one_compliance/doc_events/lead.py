import frappe
import json

@frappe.whitelist()
def create_sales_invoice(doc_name, services: str):
    """
    Create a Customer from Lead and generate a Sales Invoice with given services.
    """

    try:
        service_items = json.loads(services) if services else []
    except Exception:
        frappe.throw("Invalid services data. Expected JSON list of item codes.")

    if not service_items:
        frappe.throw("No services provided to create Sales Invoice.")

    lead = frappe.get_doc("Lead", doc_name)

    customer_type = frappe.db.get_single_value("Compliance Settings", "customer_type")
    customer = frappe.get_doc({
        "doctype": "Customer",
        "customer_name": lead.lead_name,
        "compliance_customer_type": customer_type,
        "lead_name": lead.name
    })
    customer.insert(ignore_permissions=True)

    sales_invoice = frappe.get_doc({
        "doctype": "Sales Invoice",
        "customer": customer.name,
        "items": [{"item_code": item, "qty": 1} for item in service_items]
    })
    sales_invoice.insert(ignore_permissions=True)

    frappe.msgprint(f"Sales Invoice {sales_invoice.name} created successfully.", alert=1)
    return sales_invoice.name
