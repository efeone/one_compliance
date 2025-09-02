def get_contact_property_setters():
	'''
		Get property setters for Contact doctype.
	'''
	return [
		{
			"doc_type": "Contact",
			"doctype_or_field": "DocType",
			"property": "field_order",
			"property_type": "Data",
			"value": '["contact_section", "first_name", "middle_name", "last_name", "email_id", "user", "address", "sync_with_google_contacts", "cb00", "status", "salutation", "designation", "gender", "phone", "mobile_no", "company_name", "image", "sb_00", "google_contacts", "google_contacts_id", "cb_00", "pulled_from_google_contacts", "sb_01", "email_ids", "phone_nos", "contact_details", "links", "is_primary_contact", "is_billing_contact", "more_info", "department", "unsubscribed"]',
		}
	]
