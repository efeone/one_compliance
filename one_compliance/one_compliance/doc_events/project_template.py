import frappe
from frappe.model.document import Document
from frappe.model.mapper import *
from frappe import _


@frappe.whitelist()
def update_project_template(doc, method=None):
    ''' Method to set project template in Compliance Sub Category '''
    frappe.db.set_value('Compliance Sub Category', doc.compliance_sub_category, 'project_template', doc.name)
    frappe.db.commit()
