# Copyright (c) 2024, efeone and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class ProjectNameYearType(Document):
	pass

@frappe.whitelist()
def get_reference_doctype(reference_doctype,reference_docname):
    """
    Fetch the complete document based on the provided reference doctype and docname.
    """
    doc = frappe.get_doc(reference_doctype, reference_docname)

    return {
        'from_date': doc.year_start_date,
        'to_date': doc.year_end_date,
    }
