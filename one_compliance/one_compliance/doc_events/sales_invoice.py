import frappe

def sales_invoice_on_submit(doc, method):
    if doc.project:
        frappe.db.set_value('Project', doc.project, 'status', 'Invoiced')
        frappe.db.commit()
