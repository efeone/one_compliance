import frappe
from frappe.model.mapper import *

@frappe.whitelist()
def set_customer_type_value(doc, method):
    if doc.compliance_customer_type:
        if doc.compliance_customer_type == 'Individual':
            doc.customer_type = 'Individual'
        else:
            doc.customer_type = 'Company'

@frappe.whitelist()
def create_agreement_custom_button(source_name, target_doc = None):
    def set_missing_values(source, target):
        target.customer_name= source.customer_name
        target.lead_name = source.lead_name
        target.opportunity_name= source.opportunity_name
    doc = get_mapped_doc(
        'Customer',
        source_name,
        {
        'Customer': {
        'doctype': 'Compliance Agreement',
        },
        },target_doc,set_missing_values)
    return doc
