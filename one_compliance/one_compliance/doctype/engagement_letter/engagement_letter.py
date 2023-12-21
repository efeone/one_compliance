

import frappe
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc

class EngagementLetter(Document):
    pass
@frappe.whitelist()
def get_terms_description(terms):
    description = frappe.db.get_value("Terms and Conditions", terms, "terms")
    return description

@frappe.whitelist()
def make_customer(customer, customer_group,territory,opportunity_name,customer_type):
    doc = frappe.new_doc('Customer')
    doc.customer_name = customer
    doc.customer_group = customer_group
    doc.territory = territory
    doc.opportunity_name = opportunity_name
    doc.compliance_customer_type = customer_type
    doc.save()

@frappe.whitelist()
def make_project(project_name):
    doc= frappe.new_doc('Project')
    doc.oganisation_name = project_name
    doc.save()

@frappe.whitelist()
def get_working_team(employee_group):
    
    child_table_data = frappe.get_all('Employee Group Table',filters={'parent': employee_group},
        fields=['employee','employee_name','user_id']
    )
    return child_table_data



@frappe.whitelist()
def make_project(source_name,target_name=None):
    
    doclist = get_mapped_doc(
        "Engagement Letter",
        source_name,
        {
            "Engagement Letter": {
                "doctype": "Project",
                "field_map": {"name": "project_name"},
            }
        },
        target_name
    )

    
    return doclist



