
import frappe
import json
from frappe.model.document import Document
from frappe.utils import today
from frappe import _

class InternalProjectTool(Document):
    pass

@frappe.whitelist()
def create_project(doc_data):
    doc_data = json.loads(doc_data)
    new_project = frappe.new_doc("Project")
    new_project.project_name = f"{doc_data.get('project_name', '')} {doc_data.get('sub_category', '')} {today()}"
    new_project.department = doc_data.get('department', '')
    new_project.compliance_sub_category = doc_data.get('sub_category', '')
    new_project.expected_start_date = doc_data.get('date', today())
    new_project.category_type = doc_data.get('category_type', '')
    new_project.priority = 'Medium'
    new_project.status = 'Open'
    new_project.flags.ignore_mandatory = True
    new_project.save ()
    frappe.db.commit()
    frappe.msgprint(_('Project Created'))
    return new_project.name
