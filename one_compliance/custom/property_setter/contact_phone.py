def get_contact_phone_property_setters():
	return [
		{
			"doc_type": "Contact Phone",
			"doctype_or_field": "DocField",
			"field_name": "is_primary_mobile_no",
			"property": "default",
			"property_type": "Text",
			"value": "1",
		},
		{
			"doc_type": "Contact Phone",
			"doctype_or_field": "DocField",
			"field_name": "is_primary_mobile_no",
			"property": "reqd",
			"property_type": "Check",
			"value": "1",
		},
	]
