import frappe
from frappe.model.mapper import *
from frappe import _

@frappe.whitelist()
def make_engagement_letter(source_name,target_name=None):
    
    doclist = get_mapped_doc(
        "Opportunity",
        source_name,
        {
            "Opportunity": {
                "doctype": "Engagement Letter",
                "field_map": {"name": "engagement_letter","engagement_letter_type":"Preliminary analysis & report"},
                
            }
        },
        target_name
    )

    
    return doclist
