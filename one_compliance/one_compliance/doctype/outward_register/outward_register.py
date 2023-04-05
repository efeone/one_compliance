# Copyright (c) 2023, efeone and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class OutwardRegister(Document):
	pass

@frappe.whitelist()
def disable_add_or_view_digital_signature_button(customer):
	''' Method to check the register type is outward register in the for updated signature table with same customer '''
	if frappe.db.exists('Digital Signature', {'customer' : customer}):
		digital_signature_doc = frappe.get_doc('Digital Signature', {'customer' : customer})
		for digital_signature in digital_signature_doc.digital_signature_details:
			if digital_signature.register_type == 'Outward Register':
				return 1
