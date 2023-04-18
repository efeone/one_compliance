# Copyright (c) 2023, efeone and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class OutwardRegister(Document):

	def on_submit(self):
		self.update_inward_child_table()

	def update_inward_child_table(self):
		''' Method to update status of Inward child table based on Outward child table '''
		inward_doc = frappe.get_doc('Inward Register', self.inward_register)
		for document_types in self.document_register_type:
			document_doc = document_types.document_register_type
			for register_types in inward_doc.register_type_detail:
				if register_types.document_register_type == document_doc:
					register_types.status = 'Returned'
					register_types.outward_register = self.name
		inward_doc.save()


@frappe.whitelist()
def disable_add_or_view_digital_signature_button(customer):
	''' Method to check the register type is outward register in the for updated signature table with same customer '''
	if frappe.db.exists('Digital Signature', {'customer' : customer}):
		digital_signature_doc = frappe.get_doc('Digital Signature', {'customer' : customer})
		for digital_signature in digital_signature_doc.digital_signature_details:
			if digital_signature.register_type == 'Outward Register':
				return 1
