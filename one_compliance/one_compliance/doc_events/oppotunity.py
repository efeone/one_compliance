import frappe
from frappe.model.mapper import *
from frappe import _

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
