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
def get_existing_documents(template, task):
    project_template = frappe.get_doc("Project Template", template)
    existing_documents = []
    # Find documents corresponding to the task in custom_documents_required table
    for row in project_template.custom_documents_required:
        if row.task == task:
            existing_documents = row.documents.split(', ')
    return existing_documents

@frappe.whitelist()
def update_documents_required(template, documents, task):
    document = json.loads(documents)
    documents_string = ', '.join(document)

    project_template = frappe.get_doc("Project Template", template)
    project_template_task = (row for row in project_template.tasks if row.task == task)
    project_template_task = next((row for row in project_template.tasks if row.task == task), None)
    if project_template_task:
        project_template_task.custom_has_document = 1
    existing_row = next((row for row in project_template.custom_documents_required if row.task == task), None)
    if existing_row:
        # Update the existing row
        existing_row.documents = documents_string
    else:
        project_template.append("custom_documents_required",{
            "task": task,
            "documents": documents_string
        })

    project_template.save()
    return 'success'
