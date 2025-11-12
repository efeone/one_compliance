# Copyright (c) 2025, efeone and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class Stakeholder(Document):
	def before_save(self):
		self.set_full_name()

	def set_full_name(self):
		'''
			Set full name by combining first, middle, and last names
		'''
		parts = [self.first_name or '', self.middle_name or '', self.last_name or '']
		self.full_name = ' '.join(part for part in parts if part).strip()
