import frappe
import json

@frappe.whitelist()
def create_sales_invoice(doc_name, services):
    service = json.loads(services)
    lead = frappe.get_doc('Lead',doc_name)
    customer_type = frappe.db.get_single_value("Compliance Settings", 'customer_type')
    customer = frappe.new_doc('Customer')
    customer.customer_name = lead.lead_name
    customer.compliance_customer_type = customer_type
    customer.lead_name = lead.name
    customer.insert(ignore_permissions = True)
    sales_invoice = frappe.new_doc('Sales Invoice')
    sales_invoice.customer = customer.name
    for item in service:
        sales_invoice.append('items', {
            'item_code': item,
            'qty':1,
        })

    sales_invoice.insert(ignore_permissions = True)
    frappe.msgprint(f"Sales Invoice {sales_invoice.name} created successfully.")
    return sales_invoice.name
