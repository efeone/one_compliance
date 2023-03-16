# Copyright (c) 2023, efeone and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc

class ComplianceCategory(Document):
	pass

@frappe.whitelist()
def custom_button_for_sub_category(source_name, target_doc = None):
	''' Method to get Compliance Sub category for custom button using mapdoc '''
	def set_missing_values(source, target):
		target.compliance_category = source.compliance_category
	doc = get_mapped_doc(
		'Compliance Category',
		source_name,
		{
		'Compliance Category':{
		'doctype' : 'Compliance Sub Category',
		},
		},target_doc, set_missing_values)
	return doc
