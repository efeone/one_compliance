import frappe

@frappe.whitelist()
def set_customer_type_value(doc, method):
    if doc.compliance_customer_type:
        if doc.compliance_customer_type == 'Individual':
            doc.customer_type = 'Individual'
        else:
            doc.customer_type = 'Company')
