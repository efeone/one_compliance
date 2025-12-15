from datetime import datetime, timedelta

import frappe
from frappe import _
from frappe.utils import add_days, date_diff, getdate, json, today

from one_compliance.one_compliance.utils import (
	add_custom as add_assign,
	create_todo,
	get_users_with_role,
	create_compliance_project,
)


# JOURNAL ENTRY HANDLING

@frappe.whitelist()
def update_journal_entry(doc):
	if doc.custom_reimbursement_details:
		for reimbursement_detail in doc.custom_reimbursement_details:
			if frappe.db.exists(
				"Journal Entry",
				reimbursement_detail.journal_entry,
			):
				entry_doc = frappe.get_doc(
					"Journal Entry",
					reimbursement_detail.journal_entry,
				)

				if entry_doc and entry_doc.docstatus == 0:
					entry_doc.posting_date = reimbursement_detail.date
					entry_doc.user_remark = (
						reimbursement_detail.user_remark
					)

					for account in entry_doc.accounts:
						if account.debit_in_account_currency:
							account.debit_in_account_currency = (
								reimbursement_detail.amount
							)
						else:
							account.credit_in_account_currency = (
								reimbursement_detail.amount
							)

					entry_doc.save()
					frappe.msgprint(
						"Journal Entry Updated",
						indicator="blue",
						alert=1,
					)


@frappe.whitelist()
def submit_journal_entry(journal_entry):
	if frappe.db.exists("Journal Entry", journal_entry):
		journal_entry_doc = frappe.get_doc(
			"Journal Entry",
			journal_entry,
		)

		if journal_entry_doc.docstatus == 0:
			journal_entry_doc.submit()
			return True
		else:
			frappe.throw(
				_("Journal Entry is already submitted.")
			)


# SALES ORDER → PROJECT CREATION

@frappe.whitelist()
def create_project_on_submit(doc, method):
	"""
	Hook on Submit:
	Create Projects for items using the utility function.
	"""
	if not doc.custom_create_project_automatically:
		return

	assign_to_ids = []
	for employee_row in doc.custom_assign_to:
		assign_to_ids.append(employee_row.employee)

	for item in doc.items:

		naming_conf = {
			"auto": doc.custom_project_name_automatically,
			"custom_name": doc.custom_project_name,
		}

		project_args = {
			"compliance_sub_category": item.item_code,
			"customer": doc.customer,
			"company": doc.company,
			"start_date": doc.custom_expected_start_date
				or today(),
			"sales_order": doc.name,
			"assign_to_employees": assign_to_ids,
			"is_premium": doc.get("is_premium_project"),
			"priority": doc.custom_priority,
			"custom_instructions": item.custom_instructions,
			"naming_override": naming_conf,
		}

		project = create_compliance_project(
			project_args
		)

		if doc.custom_expected_end_date and project:
			project.expected_end_date = (
				doc.custom_expected_end_date
			)
			project.save(ignore_permissions=True)

		frappe.msgprint(
			f"Project Created for {item.item_name}.",
			alert=1,
		)


@frappe.whitelist()
def get_compliance_subcategory(item_code):
	compliance_subcategory = frappe.get_doc(
		"Compliance Sub Category",
		{"item_code": item_code},
	)

	return {
		"compliance_category": compliance_subcategory.compliance_category,
		"name": compliance_subcategory.name,
		"project_template": compliance_subcategory.project_template,
	}


# SALES ORDER FROM EVENT

@frappe.whitelist()
def create_sales_order_from_event(
	event,
	customer=None,
	sub_category=None,
	rate=None,
	description=None,
	company=None,
):
	missing_fields = []

	if not customer:
		missing_fields.append("Customer")
	if not sub_category:
		missing_fields.append("Service")
	if not description:
		missing_fields.append("Service Description")

	if missing_fields:
		missing_fields_str = (
			", ".join(missing_fields[:-1])
			+ " and "
			+ missing_fields[-1]
			if len(missing_fields) > 1
			else missing_fields[0]
		)
		frappe.throw(
			f"Required Field: {missing_fields_str}."
		)

	sales_orders = frappe.get_all(
		"Sales Order",
		filters={
			"customer": customer,
			"docstatus": 1,
		},
		fields=["name"],
	)

	for sales_order in sales_orders:
		items = frappe.get_all(
			"Sales Order Item",
			filters={
				"parent": sales_order.name,
				"description": description,
			},
			fields=["name"],
		)

		if items:
			frappe.throw(
				"Proforma Invoice is already created for this Event."
			)

	event_doc = frappe.get_doc("Event", event)

	custom_service = (
		event_doc.custom_service or sub_category
	)
	custom_customer = (
		event_doc.custom_customer or customer
	)

	sub_category_doc = frappe.get_doc(
		"Compliance Sub Category",
		sub_category,
	)

	new_sales_order = frappe.new_doc("Sales Order")
	new_sales_order.customer = customer
	new_sales_order.event = event
	new_sales_order.posting_date = frappe.utils.today()
	new_sales_order.delivery_date = frappe.utils.today()

	new_sales_order.append(
		"items",
		{
			"item_code": sub_category_doc.item_code,
			"item_name": sub_category_doc.sub_category,
			"custom_compliance_category": sub_category_doc.compliance_category,
			"custom_compliance_subcategory": sub_category_doc.name,
			"rate": rate,
			"qty": 1,
			"description": description,
		},
	)

	new_sales_order.company = company
	new_sales_order.insert(ignore_permissions=True)
	new_sales_order.submit()

	frappe.db.set_value(
		"Sales Order",
		new_sales_order.name,
		"status",
		"Proforma Invoice",
	)
	frappe.db.set_value(
		"Sales Order",
		new_sales_order.name,
		"workflow_state",
		"Proforma Invoice",
	)

	frappe.msgprint(
		f"Proforma Invoice {new_sales_order.name} Created against {event}",
		alert=True,
	)

	accounts_users = get_users_with_role(
		"Accounts User"
	)

	add_assign(
		{
			"assign_to": accounts_users,
			"doctype": "Sales Order",
			"name": new_sales_order.name,
			"description": (
				f"{custom_service} for "
				f"{custom_customer} is Completed, "
				"Please Proceed with the Invoice"
			),
		}
	)

# SALES ORDER LIFECYCLE HOOKS

def so_on_cancel_custom(doc, method=None):
	"""Set workflow state to Cancelled"""
	doc.db_set("workflow_state", "Cancelled")
	if doc.project:
		frappe.db.set_value("Project", doc.project, "status", "Cancelled")

	if doc.project:
		frappe.db.set_value(
			"Project",
			doc.project,
			"status",
			"Cancelled",
		)


def so_on_update_after_submit(doc, method):
	update_journal_entry(doc)
	set_total_reimbursement_amount(doc)
	doc.reload()


def set_total_reimbursement_amount(doc):
	total_reimbursement_amount = 0

	for row in doc.custom_reimbursement_details:
		total_reimbursement_amount += row.amount

	doc.custom_total_reimbursement_amount = (
		total_reimbursement_amount
	)

	frappe.db.set_value(
		"Sales Order",
		doc.name,
		"custom_total_reimbursement_amount",
		total_reimbursement_amount,
	)


# DELETE LINKED RECORDS

@frappe.whitelist()
def delete_linked_records(sales_order):
	"""
	Deletes all records linked with the specified Sales Order.
	"""
	sales_invoice = frappe.db.get_value(
		"Sales Invoice Item",
		{"sales_order": sales_order},
		"parent",
	)

	if frappe.db.exists("Sales Invoice", sales_invoice):
		frappe.throw(
			"Cannot proceed with this operation as it is invoiced"
		)

	project = frappe.db.get_value(
		"Sales Order",
		sales_order,
		"project",
	)

	if frappe.db.exists("Project", project):
		linked_tasks = frappe.get_all(
			"Task",
			filters={"project": project},
		)

		for task in linked_tasks:
			frappe.delete_doc(
				"Task",
				task["name"],
				ignore_permissions=True,
			)

		project_doc = frappe.get_doc(
			"Project",
			project,
		)
		project_doc.sales_order = ""
		project_doc.save(ignore_permissions=True)

		frappe.delete_doc(
			"Project",
			project,
			ignore_permissions=True,
		)

	doc = frappe.get_doc("Sales Order", sales_order)
	doc.flags.ignore_permissions = True
	doc.cancel()

	frappe.delete_doc(
		"Sales Order",
		sales_order,
		ignore_permissions=True,
	)

	return "success"


# OPPORTUNITY CREATION

@frappe.whitelist()
def create_opportunity():
	"""
	Creates Opportunities for Sales Orders
	flagged for follow_up_for_next_project
	"""
	today_date = getdate(today())
	this_year = today_date.year
	this_month = today_date.month

	sales_orders = frappe.db.get_all(
		"Sales Order",
		filters={
			"follow_up_for_next_project": 1,
			"follow_up_completed": 0,
		},
		fields=[
			"name",
			"customer",
			"status",
			"workflow_state",
			"company",
			"follow_up_completed",
		],
	)

	for so in sales_orders:
		sales_order_items = frappe.get_all(
			"Sales Order Item",
			filters={"parent": so.name},
			fields=["*"],
		)

		for item in sales_order_items:
			subcat_name = (
				item.custom_compliance_subcategory
			)
			if not subcat_name:
				continue

			compliance = frappe.get_doc(
				"Compliance Sub Category",
				subcat_name,
			)

			if not (
				compliance.allow_repeat
				and compliance.renew_notif
			):
				continue

			day = int(compliance.day or 1)
			notif_days = int(
				float(
					compliance.renew_notif_days_before
					or 0
				)
			)
			repeat_on = compliance.repeat_on
			scheduled_date = None

			try:
				if repeat_on == "Monthly":
					last_day_of_month = (
						(
							datetime(
								this_year,
								this_month + 1,
								1,
							)
							- timedelta(days=1)
						).day
						if this_month < 12
						else 31
					)

					if (
						day == 1
						and today_date.day
						== last_day_of_month
					):
						next_month = (
							this_month + 1
							if this_month < 12
							else 1
						)
						next_year = (
							this_year
							if this_month < 12
							else this_year + 1
						)
						scheduled_date = datetime(
							next_year,
							next_month,
							1,
						).date()
					else:
						scheduled_date = datetime(
							this_year,
							this_month,
							day,
						).date()

				elif repeat_on == "Quarterly":
					for m in [1, 4, 7, 10]:
						try:
							d = datetime(
								this_year,
								m,
								day,
							).date()
							if d >= today_date:
								scheduled_date = d
								break
						except ValueError:
							continue

					if not scheduled_date:
						scheduled_date = datetime(
							this_year + 1,
							1,
							day,
						).date()

				elif repeat_on == "Half Yearly":
					for m in [1, 7]:
						try:
							d = datetime(
								this_year,
								m,
								day,
							).date()
							if d >= today_date:
								scheduled_date = d
								break
						except ValueError:
							continue

					if not scheduled_date:
						scheduled_date = datetime(
							this_year + 1,
							1,
							day,
						).date()

				elif repeat_on == "Yearly":
					if compliance.month:
						m = datetime.strptime(
							compliance.month,
							"%B",
						).month
						try:
							d = datetime(
								this_year,
								m,
								day,
							).date()
							if d >= today_date:
								scheduled_date = d
							else:
								scheduled_date = datetime(
									this_year + 1,
									m,
									day,
								).date()
						except ValueError:
							continue

			except Exception as e:
				frappe.log_error(
					f"Invalid date calculation for {subcat_name}: {e}",
					"Create Opportunity Error",
				)
				continue

			if not scheduled_date:
				continue

			if day == 1 and notif_days > 0:
				prev_month = (
					scheduled_date.month - 1
					if scheduled_date.month > 1
					else 12
				)
				prev_year = (
					scheduled_date.year
					if scheduled_date.month > 1
					else scheduled_date.year - 1
				)
				last_day_prev_month = (
					datetime(
						prev_year,
						prev_month + 1,
						1,
					)
					- timedelta(days=1)
				).date()
				notif_trigger_date = (
					last_day_prev_month
				)
			else:
				notif_trigger_date = add_days(
					scheduled_date,
					-notif_days,
				)

			if notif_trigger_date != today_date:
				continue

			existing_opportunity = frappe.db.exists(
				"Opportunity",
				{"sales_order": so.name},
			)
			if existing_opportunity:
				continue

			try:
				if (
					so.status
					not in ["Draft", "Closed", "Cancelled"]
					or so.workflow_state
					not in ["Pending", "Cancelled"]
				):
					opportunity = frappe.new_doc(
						"Opportunity"
					)
					opportunity.opportunity_from = (
						"Customer"
					)
					opportunity.party_name = (
						so.customer
					)
					opportunity.status = "Open"
					opportunity.opportunity_type = "Sales"
					opportunity.sales_order = so.name
					opportunity.naming_series = (
						"CRM-OPP-.YYYY.-"
					)
					opportunity.company = so.company
					opportunity.opportunity_date = (
						today_date
					)

					for soi in sales_order_items:
						opp_item = opportunity.append(
							"items",
							{},
						)
						opp_item.item_code = (
							soi.item_code
						)
						opp_item.item_name = (
							soi.item_name
						)
						opp_item.qty = soi.qty
						opp_item.rate = soi.rate
						opp_item.amount = soi.amount
						opp_item.compliance_category = (
							soi.custom_compliance_category
						)
						opp_item.compliance_sub_category = (
							soi.custom_compliance_subcategory
						)

					opportunity.insert(
						ignore_permissions=True
					)

					frappe.db.set_value(
						"Sales Order",
						so.name,
						"follow_up_completed",
						1,
					)

					follow_up_user = frappe.db.get_value(
						"Employee",
						compliance.follow_up_person,
						"user_id",
					)

					if follow_up_user:
						create_todo(
							"Opportunity",
							opportunity.name,
							follow_up_user,
							frappe.session.user,
							f"Follow up for compliance sub category: {subcat_name}",
						)

			except Exception as e:
				frappe.log_error(
					f"Failed to create Opportunity for {subcat_name}: {e}",
					"Create Opportunity Error",
				)


# SET COMPLIANCE FIELDS

def set_compliance_fields(doc, method):
	for item in doc.items:
		if item.item_code:
			subcat = frappe.db.get_value(
				"Compliance Sub Category",
				{"item_code": item.item_code},
				[
					"compliance_category",
					"name",
				],
				as_dict=True,
			)

			if subcat:
				item.custom_compliance_category = (
					subcat.compliance_category
				)
				item.custom_compliance_subcategory = (
					subcat.name
				)
