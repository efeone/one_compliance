# Copyright (c) 2023, efeone and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.model.mapper import *

class ComplianceSubCategory(Document):
	pass

@frappe.whitelist()
def create_project_template_custom_button(source_name, target_doc = None):
	''' Method to get project template for custom button using mapdoc '''
	def set_missing_values(source, target):
		target.compliance_category= source.compliance_category
		target.compliance_sub_category = source.name
	doc = get_mapped_doc(
		'Compliance Sub Category',
		source_name,
		{
		'Compliance Sub Category': {
		'doctype': 'Project Template',
        },
		}, target_doc, set_missing_values)
	return doc
