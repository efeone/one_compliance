import frappe
from frappe.model.mapper import *
from frappe import _
from frappe.utils import getdate, today, get_link_to_form, add_days, nowdate

@frappe.whitelist()
def make_engagement_letter(source_name,target_name=None):

	doclist = get_mapped_doc(
		"Opportunity",
		source_name,
		{
			"Opportunity": {
				"doctype": "Engagement Letter",
				"field_map": {"name": "engagement_letter","engagement_letter_type":"Preliminary analysis & report"},

			}
		},
		target_name
	)


	return doclist

@frappe.whitelist()
def create_event_from_opportunity(oppotunity,event_category,start_on,subject,attendees):
	attendees = json.loads(attendees)
	event = frappe.new_doc('Event')
	event.event_category = event_category
	event.subject = subject
	event.starts_on = start_on
	event.append('event_participants', {
		'reference_doctype': 'Opportunity',
		'reference_docname': oppotunity
	})
	for attendee in attendees:
		event.append('event_participants', {
			'reference_doctype': attendee.get('attendee_type'),
			'reference_docname': attendee.get('attendee')
		})
	event.insert(ignore_permissions = True)
	return event.name

def set_opportunity_converted(doc, method):
	'''
		Set Opportunity status to 'Converted' when a Customer is created from it.
	'''
	if getattr(doc, 'opportunity_name', None):
		frappe.db.set_value('Opportunity', doc.opportunity_name, 'status', 'Converted')


@frappe.whitelist()
def create_sales_order(opportunity):
	if not frappe.db.exists('Opportunity', opportunity):
		frappe.throw("Opportunity not found")

	opp = frappe.get_doc('Opportunity', opportunity)
	customer = create_if_customer_not_exists(opp)

	items = [
		{
			"item_code": i.item_code,
			"item_name": i.item_name,
			"uom": i.uom,
			"qty": i.qty,
			"rate": i.rate,
			"custom_compliance_category": i.compliance_category,
			"custom_compliance_subcategory": i.compliance_sub_category,
		}
		for i in opp.items
	]

	return {"customer": customer, "items": items}

def create_if_customer_not_exists(opp):
	if opp.opportunity_from == 'Customer':
		return opp.party_name

	existing = frappe.db.get_value('Customer', {'opportunity_name': opp.name})
	if existing:
		return existing

	customer = frappe.new_doc('Customer')

	customer.update({
		"opportunity_name": opp.name,
		"customer_name": opp.contact_person or "Unnamed Customer",
		"custom_customer_type": (
			opp.custom_customer_type
			or frappe.db.get_single_value("Compliance Settings", "customer_type")
		),
	})

	customer.flags.ignore_mandatory = True
	customer.insert(ignore_permissions=True)

	return customer.name

@frappe.whitelist()
def get_item_compliance(item_code):
	"""
	Fetches compliance_category and compliance_sub_category
	from Compliance Sub Category doctype based on Item Code.
	"""

	if not item_code:
		return {}

	data = frappe.db.get_value(
		'Compliance Sub Category',
		{'item_code': item_code},
		['name', 'compliance_category', 'sub_category'],
		as_dict=True
	)

	if not data:
		return {}

	return {
		"compliance_category": data.get("compliance_category"),
		"compliance_sub_category": data.get("name")
	}

def create_opportunity_todos(doc, method=None):
	"""
	Create ToDo(s) based on Opportunity ToDo Template
	"""
	compliance_settings = frappe.get_single("Compliance Settings")

	if not compliance_settings.opportunity_todo_template:
		return

	for row in compliance_settings.opportunity_todo_template:
		due_date = add_days(nowdate(), row.due_date_rule) if row.due_date_rule else None

		users = []

		if row.role:
			role_users = frappe.get_all(
				"Has Role",
				filters={"role": row.role},
				pluck="parent"
			)

			users = frappe.get_all(
				"User",
				filters={
					"name": ["in", role_users],
					"enabled": 1
				},
				pluck="name"
			)
		if users:
			for user in users:
				todo = frappe.new_doc("ToDo")
				todo.description = row.description
				todo.reference_type = "Opportunity"
				todo.reference_name = doc.name
				todo.allocated_to = user
				todo.date = due_date
				todo.insert(ignore_permissions=True)
		else:
			todo = frappe.new_doc("ToDo")
			todo.description = row.description
			todo.reference_type = "Opportunity"
			todo.reference_name = doc.name
			todo.date = due_date
			todo.insert(ignore_permissions=True)

@frappe.whitelist()
def get_compliance_sub_category_list(compliance_category):
	return frappe.get_all(
		"Compliance Sub Category",
		filters={"compliance_category": compliance_category},
		fields=["name", "item_code"]
	)

@frappe.whitelist()
def create_customer_from_opportunity(opportunity):
    """
    Create Customer from Opportunity if enquiry_from = New Client
    Return Customer name
    """

    opp = frappe.get_doc("Opportunity", opportunity)
    if opp.enquiry_from != "New Client":
        return opp.party_name

    if not opp.organization_name:
        frappe.throw("Organization Name is required to create Customer")
    existing_customer = frappe.db.exists(
        "Customer",
        {"customer_name": opp.organization_name}
    )
    if existing_customer:
        return existing_customer
    customer_type = frappe.db.get_single_value(
        "Compliance Settings",
        "customer_type"
    )
    customer = frappe.get_doc({
        "doctype": "Customer",
        "customer_name": opp.organization_name,
		"compliance_customer_type": customer_type
    })

    customer.insert(ignore_permissions=True)
    return customer.name

