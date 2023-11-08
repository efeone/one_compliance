# Copyright (c) 2023, efeone and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

#Fields used to map Compliance Item to Item
compliance_item_fields = ['item_code', 'item_name', 'item_group', 'is_service_item']

class ComplianceItem(Document):
	def validate(self):
		''' Method to validate Item name and Item Code '''
		if self.is_new():
			self.validate_item_name()
			self.validate_item_code()

	def after_insert(self):
		''' Method to create Item from Compliance Item '''
		create_or_update_item(self)

	def on_update(self):
		''' Method to update created Item on changes of Compliance Item '''
		create_or_update_item(self, self.item)

	def validate_item_name(self):
		''' Method to validate AuMMS Item Name wrt to Item Name '''
		if self.item_name:
			if frappe.db.exists('Item', { 'item_name' : self.item_name }):
				frappe.throw('Item already exists with Item Name `{0}`.'.format(frappe.bold(self.item_name)))

	def validate_item_code(self):
		''' Method to validate AuMMS Item Code wrt to Item Code '''
		if self.item_code:
			if frappe.db.exists('Item', { 'item_code' : self.item_code }):
				frappe.throw('Item already exists with Item Code `{0}`.'.format(frappe.bold(self.item_code)))

def create_or_update_item(self, item=None):
	''' Method to create or update Item from Compliance Item '''
	if not item:
		#Case of new Item
		if not frappe.db.exists('Item', self.name):
			#Creating new Item object
			item_doc = frappe.new_doc('Item')
		else:
			#Case of exception
			return 0
	else:
		#Case of existing Item
		if frappe.db.exists("Item", item):
			#Creating existing Item object
			item_doc = frappe.get_doc('Item', item)
		else:
			#Case of exception
			return 0

	# Set values to Item from Compliance Item
	for compliance_item_field in compliance_item_fields:
		item_doc.set(compliance_item_field, self.get(compliance_item_field))

	item_doc.is_service_item = 1
	item_doc.is_stock_item = 0
	item_doc.include_item_in_manufacturing = 0

	if not item:
		# Case of new Item
		item_doc.insert(ignore_permissions = True)
		# Set Item Group link to Compliance Item Group
		frappe.db.set_value('Compliance Item', self.name, 'item', item_doc.name)
	elif frappe.db.exists("Item", item):
		# case of updating existing Item
		item_doc.save(ignore_permissions = True)
	frappe.db.commit()
