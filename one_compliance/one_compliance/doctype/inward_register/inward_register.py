# Copyright (c) 2023, efeone and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.model.mapper import *


class InwardRegister(Document):
	pass

@frappe.whitelist()
def create_outward_register(source_name, target_doc = None):
    def set_missing_values(source, target):
        target.register_type = source.register_type
    doc = get_mapped_doc(
        'Inward Register',
        source_name,
        {
        'Inward Register': {
        'doctype': 'Outward Register',
        },
        },target_doc,set_missing_values)
    return doc
