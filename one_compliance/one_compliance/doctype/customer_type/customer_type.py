# Copyright (c) 2023, efeone and contributors
# For license information, please see license.txt
import frappe
from frappe.model.document import Document

class CustomerType(Document):
	def on_trash(self):
		self.validate_customer_type()

	def validate_customer_type(self):
		if self.customer_type == 'Individual' or self.customer_type == 'Company':
			frappe.throw('You have no Permission to Delete Standard Customer Types')
