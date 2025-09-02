def get_event_participant_property_setters():
	'''
		Get property setters for Event Participants doctype.
	'''
	return [
		{
			"doc_type": "Event Participants",
			"doctype_or_field": "DocType",
			"property": "field_order",
			"property_type": "Data",
			"value": '["reference_doctype", "reference_docname", "email", "custom_participant_name"]',
		}
	]
