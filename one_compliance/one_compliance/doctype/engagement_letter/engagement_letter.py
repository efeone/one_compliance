# Copyright (c) 2023, efeone and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class EngagementLetter(Document):
    pass
@frappe.whitelist()
def get_terms_description(terms):
    description = frappe.db.get_value("Terms and Conditions", terms, "terms")
    return description
