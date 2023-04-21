# Copyright (c) 2023, efeone and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.model.mapper import *
from frappe import _

class ComplianceSubCategory(Document):
	def validate(self):
		self.validate_rate()

	def validate_rate(self):
		""" Method to validate rate """
		if not self.rate :
			frappe.throw(_('Please Enter Valid Rate'))

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

@frappe.whitelist()
def get_notification_details():
	doc = frappe.get_doc('Compliance Settings')
	return doc

@frappe.whitelist()
def set_filter_for_employee(doctype, txt, searchfield, start, page_len, filters):
	# *Applied filter for employee in compliance_executive child table*
	if filters:
		query = '''
			SELECT
				ce.employee,ce.employee_name
			FROM
				`tabCompliance Executive` as ce,
				`tabCompliance Category` as cc
			WHERE
				cc.name = ce.parent AND
				cc.name = %(compliance_category)s
			'''
		values = frappe.db.sql(query.format(**{
			}), {
			'compliance_category': filters['compliance_category'],
		})
		return values