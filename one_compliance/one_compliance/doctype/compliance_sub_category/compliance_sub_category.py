# Copyright (c) 2023, efeone and contributors
# For license information, please see license.txt

import frappe
from datetime import datetime
from frappe.model.document import Document
from frappe.model.mapper import *
from frappe import _
from frappe.utils import getdate, add_months, today, add_days
from frappe.email.doctype.notification.notification import get_context

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


def send_repeat_notif():
	"""Method sends repeat notifications for compliance subcategories."""
	months_dict = {
		"January": 1,
		"February": 2,
		"March": 3,
		"April": 4,
		"May": 5,
		"June": 6,
		"July": 7,
		"August": 8,
		"September": 9,
		"October": 10,
		"November": 11,
		"December": 12,
	}

	sub_categories = frappe.db.get_all(
		"Compliance Sub Category",
		filters={"enabled": 1, "renew_notif": 1},
		pluck="name",
	)

	for sub_category in sub_categories:
		sub_category_doc = frappe.get_doc("Compliance Sub Category", sub_category)
		current_date = getdate(today())
		day = sub_category_doc.day
		compliance_date = calculate_compliance_date(
			sub_category_doc, current_date, day, months_dict
		)

		if not compliance_date:
			continue

		notification_date = add_days(
			compliance_date, -sub_category_doc.renew_notif_days_before
		)

		if current_date < notification_date:
			continue

		projects_to_notify = frappe.db.get_all(
			"Project",
			filters={
				"status": "Completed",
				"expected_end_date": ["<", notification_date],
				"renew_email_sent_on": ["is", "not set"],
				"compliance_sub_category": sub_category,
			},
			pluck="name",
		)

		send_notification_email(projects_to_notify, sub_category_doc)


def calculate_compliance_date(sub_category_doc, current_date, day, months_dict):
	"""Calculate the next compliance date."""
	try:
		if sub_category_doc.repeat_on == "Monthly":
			compliance_date = datetime(current_date.year, current_date.month, day)
			if compliance_date < current_date:
				compliance_date = add_months(compliance_date, 1)
		else:
			month_flag = {"Quarterly": 3, "Half Yearly": 6, "Yearly": 12}.get(
				sub_category_doc.repeat_on, 0
			)
			month = months_dict.get(sub_category_doc.month, current_date.month)
			compliance_date = getdate(datetime(current_date.year, month, day))
			print("here")
			if compliance_date < current_date:
				print("here2")
				compliance_date = add_months(compliance_date, month_flag)
			print("here3")
		return getdate(compliance_date)
	except Exception as e:
		frappe.log_error(message=str(e), title="Compliance Date Calculation Error")
		return None


def send_notification_email(projects_to_notify, sub_category_doc):
	"""Send notification emails for the given projects."""
	recipients = set()
	for project in projects_to_notify:
		customer = frappe.db.get_value("Project", project, "customer")
		contact = frappe.db.get_value(
			"Dynamic Link",
			{
				"parenttype": "Contact",
				"link_doctype": "Customer",
				"link_name": customer,
			},
			"parent",
		)
		email = frappe.db.get_value("Contact", contact, "email_id")
		if email:
			recipients.add(email)

	if (
		recipients
		and frappe.db.exists(
			"Email Template", sub_category_doc.renew_notification_for_customer
		)
		and frappe.db.get_single_value(
			"Compliance Settings", "enable_renew_notification"
		)
	):
		try:
			email_template = frappe.get_doc(
				"Email Template", sub_category_doc.renew_notification_for_customer
			)
			context = get_context(sub_category_doc)
			subject = frappe.render_template(email_template.subject, context)
			message = frappe.render_template(email_template.response, context)
			frappe.sendmail(
				recipients=list(recipients),
				subject=subject,
				message=message,
			)
			for project in projects_to_notify:
				frappe.db.set_value("Project", project, "renew_email_sent_on", today())
		except Exception as e:
			frappe.log_error(message=str(e), title="Email Sending Error")

@frappe.whitelist()
def create_renewal_opportunities():
    today_date = getdate(today())
    sub_categories = frappe.get_all(
        "Compliance Sub Category",
        filters={"enabled": 1, "allow_repeat": 1},
        fields=["name", "renew_notif_days_before", "sub_category"]
    )
    for sub_cat in sub_categories:
        if not sub_cat.renew_notif_days_before:
            continue
        sales_orders = frappe.get_all(
            "Sales Order",
            filters={"custom_compliance_subcategory": sub_cat.name},
            fields=["name", "custom_expected_end_date", "customer"]
        )
        for order in sales_orders:
            if not order.custom_expected_end_date:
                continue
            renewal_date = getdate(order.custom_expected_end_date)
            notif_date = add_days(renewal_date, -int(sub_cat.renew_notif_days_before))
            if notif_date == today_date:
                existing = frappe.get_all("Opportunity", filters={
                    "opportunity_type": "Sales",
                    "party_name": order.customer
                })
                if not existing:
                    sales_order_doc = frappe.get_doc("Sales Order", order.name)
                    opportunity = frappe.new_doc("Opportunity")
                    opportunity.opportunity_from = "Customer"
                    opportunity.party_name = order.customer
                    opportunity.opportunity_type = "Sales"
                    opportunity.enquiry_date = today_date
                    opportunity.status = "Open"
                    for item in sales_order_doc.items:
                        opportunity.append("items", {
                            "item_code": item.item_code,
                            "qty": item.qty,
                            "rate": item.rate,
                            "amount": item.amount
                        })
                    opportunity.save(ignore_permissions=True)
                    frappe.db.commit()
