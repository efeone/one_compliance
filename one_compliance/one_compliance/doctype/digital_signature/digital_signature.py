# Copyright (c) 2023, efeone and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import *
from frappe.model.document import Document
from frappe import _

class DigitalSignature(Document):
	def validate(self):
		self.validate_expiry_date()

	def validate_expiry_date(self):
		''' Method to validate Expiry Date '''
		if getdate(self.expiry_date) <= getdate(today()):
			frappe.throw(_('Please Enter Valid Expiry Date'))
