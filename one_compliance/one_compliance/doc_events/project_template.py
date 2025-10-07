import frappe
import json
from frappe.model.document import Document
from frappe import _

@frappe.whitelist()
def update_project_template(doc, method=None):
    """Set project template in Compliance Sub Category."""
    frappe.db.set_value('Compliance Sub Category', doc.compliance_sub_category, 'project_template', doc.name)

@frappe.whitelist()
def get_existing_documents(template, task):
    """Get documents for a task from custom_documents_required table."""
    project_template = frappe.get_doc("Project Template", template)
    for row in project_template.custom_documents_required:
        if row.task == task:
            return row.documents.split(', ')
    return []

@frappe.whitelist()
def update_documents_required(template, task, documents=None):
    """Update or remove documents required for a task in a project template."""
    project_template = frappe.get_doc("Project Template", template)
    task_row = next((row for row in project_template.tasks if row.task == task), None)
    doc_row = next((row for row in project_template.custom_documents_required if row.task == task), None)

    if documents:
        documents_list = json.loads(documents)
        documents_string = ', '.join(documents_list)
        if task_row:
            task_row.custom_has_document = 1
        if doc_row:
            doc_row.documents = documents_string
        else:
            project_template.append("custom_documents_required", {
                "task": task,
                "documents": documents_string
            })
    else:
        if task_row:
            task_row.custom_has_document = 0
        if doc_row:
            project_template.custom_documents_required.remove(doc_row)
    project_template.save()
    return 'success'

def on_trash(doc, method):
    """Clear project_template in Compliance Sub Category if the template is deleted."""
    sub_category = doc.compliance_sub_category
    if sub_category and frappe.db.exists("Compliance Sub Category", sub_category):
        compliance_sub_category = frappe.get_doc("Compliance Sub Category", sub_category)
        if compliance_sub_category.project_template == doc.name:
            compliance_sub_category.set('project_template', None)
            compliance_sub_category.save()

def validate(doc, method):
    """
    Ensure only one project template exists per compliance sub category.
    Throws error if duplicate found.
    """
    sub_category = doc.compliance_sub_category
    if not sub_category:
        return
    existing_template = frappe.db.exists({
        "doctype": "Project Template",
        "compliance_sub_category": sub_category,
        "name": ["!=", doc.name]
    })
    if existing_template:
        sub_category_name = frappe.get_value("Compliance Sub Category", sub_category, "name")
        frappe.throw(_("Project Template already exists for <b>{0}</b>").format(sub_category_name))