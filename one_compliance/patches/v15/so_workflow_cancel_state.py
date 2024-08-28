import frappe

def execute():
    frappe.db.sql("""UPDATE `tabSales Order` SET workflow_state = 'Cancelled' WHERE docstatus=2""")
