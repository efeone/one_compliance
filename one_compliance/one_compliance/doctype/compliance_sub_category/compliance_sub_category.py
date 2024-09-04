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
			sub_cat_item = create_compliance_item_from_sub_category(self, self.sub_category, self.rate)
			self.item_code = sub_cat_item

		# Check if the subcategory name is changed
		if self.get_doc_before_save() and self.get_doc_before_save().sub_category != self.sub_category:
			self.item_code = self.sub_category
			update_related_item_name(self,self.get_doc_before_save().sub_category, self.sub_category, self.compliance_category)

	def validate_rate(self):
		""" Method to validate rate """
		if not self.rate and self.is_billable:
			frappe.throw(_('Please Enter Valid Rate'))

	def after_delete(self):
		# Delete related Compliance Items
		delete_related_items(self.sub_category)


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
def create_compliance_item_from_sub_category(doc, sub_category, rate):
	if not frappe.db.exists('Item', {'item_code':sub_category}):
		# Fetch the 'Services' Item Group
		item_group = frappe.db.get_single_value("Compliance Settings", 'compliance_service_item_group')

		# Create a new Compliance Item document
		compliance_item = frappe.get_doc({
			"doctype": "Item",
			"item_name": sub_category,
			"item_code": sub_category,
			"item_group": item_group,
			"is_service_item":True,
			"is_stock_item": False,
			"include_item_in_manufacturing": False,
			"item_defaults": []
		})
		for account in doc.default_account:
			compliance_item.append("item_defaults", {
				"company":account.company,
                "income_account": account.default_income_account,
				"default_warehouse": ''
            })
		compliance_item.flags.ignore_mandatory = True
		compliance_item.save(ignore_permissions=True)
		make_item_price(sub_category,rate)
		frappe.msgprint("Compliance Item Created: {}".format(compliance_item.name), indicator="green", alert=1)
		return compliance_item.name
	else:
		return  frappe.get_value("Item", {"item_code": sub_category})
	return compliance_item.name

@frappe.whitelist()
def make_item_price(sub_category, rate):
    price_list_name = frappe.db.get_value(
        "Selling Settings", None, "selling_price_list"
    ) or frappe.db.get_value("Price List", {"selling": 1})
    frappe.get_doc(
        {
            "doctype": "Item Price",
            "price_list": price_list_name,
            "item_code": sub_category,
            "price_list_rate": rate,
            "valid_from": frappe.utils.today(),
        }
    ).insert(ignore_permissions=True, ignore_mandatory=True)

@frappe.whitelist()
def disable_related_item(item_name):
	frappe.db.set_value('Item', item_name, 'disabled', 1)
	frappe.db.commit()

@frappe.whitelist()
def enable_related_item(item_name):
	frappe.db.set_value('Item', item_name, 'disabled', 0)
	frappe.db.commit()

@frappe.whitelist()
def delete_related_items(item_name):
	frappe.delete_doc('Item', item_name, ignore_permissions=True)
	frappe.db.commit()

	frappe.msgprint("Compliance Item Deleted: {}".format(item_name), indicator="green", alert=1)

@frappe.whitelist()
def update_related_item_name(doc, old_sub_category, new_sub_category, compliance_category):
	# Update Compliance Item name and code based on the new subcategory
	item = frappe.get_doc("Item", {"item_name": old_sub_category})
	if item:
		item.item_name = new_sub_category
		item.item_code = new_sub_category
		for default_acc in doc.default_account:
			frappe.db.set_value("Item Default", {"parent":item.name, "idx":1}, "company", default_acc.company)
			frappe.db.set_value("Item Default", {"parent":item.name, "idx":1}, "income_account", default_acc.default_income_account)
			# Rename the doctype in the Item
			frappe.rename_doc('Item', old_sub_category, new_sub_category, force=True)

			rename_compliance_subcategory(old_sub_category, new_sub_category, compliance_category)


	frappe.msgprint("Compliance Item Name Updated: {} -> {}".format(old_sub_category, new_sub_category), indicator="blue", alert=1)

@frappe.whitelist()
def rename_compliance_subcategory(old_sub_category, new_sub_category, compliance_category):
    # Formulate the old and new doctype names
    old_doctype_name = f"{compliance_category}-{old_sub_category}"
    new_doctype_name = f"{compliance_category}-{new_sub_category}"

    doc = frappe.get_all("Compliance Sub Category", filters={'name': old_doctype_name})

    if doc:
        # Update the found document's subcategory field and name
        frappe.db.set_value('Compliance Sub Category', doc[0].name, 'sub_category', new_sub_category)
        frappe.rename_doc('Compliance Sub Category', doc[0].name, new_doctype_name, force=True)

        frappe.msgprint("Compliance Subcategory Doctype Name Updated: {} -> {}".format(old_doctype_name, new_doctype_name), indicator="blue", alert=1)
