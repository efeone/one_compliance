def get_opportunity_property_setters():
	'''
		Get property setters for Opportunity doctype.
	'''
	return [
		{
			"doc_type": "Opportunity",
			"doctype_or_field": "DocType",
			"property": "field_order",
			"property_type": "Data",
			"value": '["naming_series", "opportunity_from", "party_name", "customer_name", "status", "column_break0", "opportunity_type", "source", "opportunity_owner", "column_break_10", "sales_stage", "expected_closing", "probability", "organization_details_section", "no_of_employees", "annual_revenue", "customer_group", "column_break_23", "industry", "market_segment", "website", "column_break_31", "city", "state", "country", "territory", "section_break_14", "currency", "column_break_36", "conversion_rate", "column_break_17", "opportunity_amount", "base_opportunity_amount", "more_info", "company", "campaign", "transaction_date", "column_break1", "language", "amended_from", "title", "first_response_time", "lost_detail_section", "lost_reasons", "order_lost_reason", "column_break_56", "competitors", "contact_info", "primary_contact_section", "contact_person", "job_title", "column_break_54", "contact_email", "contact_mobile", "column_break_22", "whatsapp", "phone", "phone_ext", "address_contact_section", "address_html", "customer_address", "address_display", "column_break3", "contact_html", "contact_display", "items_section", "items", "section_break_32", "base_total", "column_break_33", "total", "section_break_dsrp", "documents_required", "activities_tab", "open_activities_html", "all_activities_section", "all_activities_html", "notes_tab", "notes_html", "notes", "dashboard_tab"]',
		},
		{
			"doc_type": "Opportunity",
			"doctype_or_field": "DocField",
			"field_name": "items_section",
			"property": "label",
			"property_type": "Data",
			"value": "Services",
		},
		{
			"doc_type": "Opportunity",
			"doctype_or_field": "DocField",
			"field_name": "items",
			"property": "label",
			"property_type": "Data",
			"value": "Services",
		},
		{
			"doc_type": "Opportunity",
			"doctype_or_field": "DocField",
			"field_name": "dashboard_tab",
			"property": "hidden",
			"property_type": "Check",
			"value": "1",
		},
		{
			"doc_type": "Opportunity",
			"doctype_or_field": "DocField",
			"field_name": "section_break_14",
			"property": "hidden",
			"property_type": "Check",
			"value": "1",
		},
	]
