import frappe
from frappe.model.mapper import *
from frappe import _
from frappe.utils import getdate, today, get_link_to_form

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
		"compliance_customer_type": (
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

