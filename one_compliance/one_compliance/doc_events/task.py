import frappe
from frappe import _

""" Method to add customer Credential details """

@frappe.whitelist()
def add_credential_details(project,purpose):
    if frappe.db.exists('Project',project):
        customer = frappe.db.get_value('Project',project,'customer')
        if frappe.db.exists('Customer Credentials',{'customer':customer}):
            customer_credential = frappe.db.get_value('Customer Credentials',{'customer':customer})
            if frappe.db.exists('Credential Details', {'parent':customer_credential,'purpose':purpose}):
                username, password, url = frappe.db.get_value('Credential Details', {'parent':customer_credential,'purpose':purpose}, ['username', 'password','url'])
            return [username, password, url]
        else:
            frappe.throw(_('Credential not configured for this Purpose'))
