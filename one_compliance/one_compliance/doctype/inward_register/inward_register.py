# Copyright (c) 2023, efeone and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.model.mapper import *


class InwardRegister(Document):
	def on_update_after_submit(self):
		self.change_inward_status()

	def change_inward_status(self):
		''' Method to change the status of Inward Doctype based on status of child table '''
		is_returned = True
		is_issued = True
		for register_types in self.register_type_detail:
			if register_types.status != 'Issued':
				is_issued = False
			if register_types.status != 'Returned':
				is_returned = False
		if is_issued == True:
			frappe.db.set_value('Inward Register', self.name, 'status', 'Open')
		else:
			if is_returned == True:
				frappe.db.set_value('Inward Register', self.name, 'status', 'Closed')
			else:
				frappe.db.set_value('Inward Register', self.name, 'status', 'Partially Returned')


@frappe.whitelist()
def create_outward_register(source_name, target_doc = None):
	''' Method to route to Outward Register from Inward Register '''
	def set_missing_values(source, target):
		target.register_type = source.register_type
		target.customer = source.customer
		target.document_register_type = []
		for register_types in source.register_type_detail:
			if register_types.status == 'Issued':
				target.append('document_register_type', {
				'document_register_type' : register_types.document_register_type
				})
	doc = get_mapped_doc(
		'Inward Register',
		source_name,
		{
		'Inward Register': {
		'doctype': 'Outward Register',
		},
		},target_doc, set_missing_values)
	return doc


@frappe.whitelist()
def disable_add_or_view_digital_signature_button(customer):
	''' Method to check is there any value existing in the table with same customer '''
	if frappe.db.exists('Digital Signature', {'customer' : customer}):
		digital_signature_doc = frappe.get_doc('Digital Signature', {'customer' : customer})
		if digital_signature_doc.digital_signature_details:
			return 1
