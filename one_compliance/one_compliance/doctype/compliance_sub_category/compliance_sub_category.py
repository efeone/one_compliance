# Copyright (c) 2023, efeone and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.model.mapper import *
from frappe import _

class ComplianceSubCategory(Document):
	def validate(self):
		self.validate_rate()
		if self.is_billable and not self.item_code:
			sub_cat_item = create_compliance_item_from_sub_category(self.sub_category)
			self.item_code = sub_cat_item

	def validate_rate(self):
		""" Method to validate rate """
		if not self.rate and self.is_billable:
			frappe.throw(_('Please Enter Valid Rate'))

@frappe.whitelist()
def create_project_manually(customer, project_template, expected_start_date, expected_end_date):
	compliance_sub_category = frappe.db.get_value('Project Template', project_template, 'compliance_sub_category')
	today = frappe.utils.today()
	project_name = customer + '-' + compliance_sub_category + '-' + today
	if not frappe.db.exists('Project', { 'project_name':project_name }):
		project = frappe.new_doc('Project')
		project.project_name = project_name
		project.project_template = project_template
		project.customer = customer
		project.expected_start_date = expected_start_date
		project.expected_end_date = expected_end_date
		project.save()
		frappe.msgprint("Project Created",alert = 1)
	else:
		frappe.msgprint("Project already created!")

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
	# Applied filter for employee in compliance_executive child table
	searchfields = frappe.get_meta(doctype).get_search_fields()
	searchfields = " or ".join("ce." + field + " like %(txt)s" for field in searchfields)
	if filters['compliance_category']:
		return frappe.db.sql(
			"""SELECT
				ce.employee,ce.employee_name
			FROM
				`tabCompliance Executive` as ce,
				`tabCompliance Category` as cc
			WHERE
				({key})
				and cc.name = ce.parent
				and cc.name = %(compliance_category)s
			""".format(
				key=searchfields,
			),
			{
			"txt": "%" + txt + "%",
			'compliance_category': filters['compliance_category']
			}
		)

@frappe.whitelist()
def create_compliance_item_from_sub_category(sub_category):

	if not frappe.db.exists('Compliance Item', {'item_code':sub_category}):
		# Fetch the 'Services' Item Group
		item_group = frappe.get_value("Item Group", {"item_group_name": "Services"})


		# Create a new Compliance Item document
		compliance_item = frappe.get_doc({
			"doctype": "Compliance Item",
			"item_name": sub_category,
			"item_code": sub_category,
			"item_group": item_group
		})
		# Save the Compliance Item document
		compliance_item.insert()
		frappe.msgprint("Compliance Item Created: {}".format(compliance_item.name), indicator="green", alert=1)
		return compliance_item.name
	else:
		return  frappe.get_value("Compliance Item", {"item_code": sub_category})
	return compliance_item.name
