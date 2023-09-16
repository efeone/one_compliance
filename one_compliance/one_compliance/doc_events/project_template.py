import frappe
from frappe.model.document import Document
from frappe.model.mapper import *
from frappe import _


@frappe.whitelist()
def update_project_template(doc, method=None):
    ''' Method to set project template in Compliance Sub Category '''
    frappe.db.set_value('Compliance Sub Category', doc.compliance_sub_category, 'project_template', doc.name)
    frappe.db.commit()

@frappe.whitelist()
def calculate_project_duration(doc, method):
    if doc.tasks:
        total_duration = 0
        for task in doc.tasks:
            duration = frappe.db.get_value('Task', task.task, 'duration')
            total_duration += duration
        if doc.custom_project_duration < total_duration:
            frappe.throw(_('Project Duration should be greater than task total task duration'))
