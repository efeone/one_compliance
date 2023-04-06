# Copyright (c) 2023, efeone and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import *
from frappe.model.document import Document
from frappe import _

class DigitalSignature(Document):
	def validate(self):
		self.validate_expiry_date()
		self.validate_duplicate_entry()

	def validate_expiry_date(self):
		''' Method to validate Expiry Date '''
		if getdate(self.expiry_date) <= getdate(today()):
			frappe.throw(_('Please Enter Valid Expiry Date'))

	def validate_duplicate_entry(self):
		''' Method to validate duplicate entry of Register '''
		if self.digital_signature_details:
			for digital_signature in self.digital_signature_details:
				if digital_signature.reference_id:
					reference_id = digital_signature.reference_id
					count = 0
					for ds in self.digital_signature_details:
						if ds.reference_id == reference_id:
							count = count + 1
					if count > 1:
						frappe.throw("Register Type :{0} is already linked with this Digital Signature".format(reference_id))

@frappe.whitelist()
def get_notification_details():
	doc = frappe.get_doc('Compliance Settings')
	return doc
