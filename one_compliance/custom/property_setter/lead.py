def get_lead_property_setters():
	'''
		Get property setters for Lead doctype.
	'''
	return [
		{
			"doc_type": "Lead",
			"doctype_or_field": "DocField",
			"field_name": "qualification_tab",
			"property": "hidden",
			"property_type": "Check",
			"value": "1",
		},
		{
			"doc_type": "Lead",
			"doctype_or_field": "DocField",
			"field_name": "market_segment",
			"property": "hidden",
			"property_type": "Check",
			"value": "1",
		},
		{
			"doc_type": "Lead",
			"doctype_or_field": "DocField",
			"field_name": "fax",
			"property": "hidden",
			"property_type": "Check",
			"value": "1",
		},
		{
			"doc_type": "Lead",
			"doctype_or_field": "DocField",
			"field_name": "job_title",
			"property": "hidden",
			"property_type": "Check",
			"value": "1",
		},
		{
			"doc_type": "Lead",
			"doctype_or_field": "DocField",
			"field_name": "request_type",
			"property": "hidden",
			"property_type": "Check",
			"value": "1",
		},
		{
			"doc_type": "Lead",
			"doctype_or_field": "DocField",
			"field_name": "industry",
			"property": "hidden",
			"property_type": "Check",
			"value": "1",
		},
	]
