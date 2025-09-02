def get_event_property_setters():
	'''
		Get property setters for Event doctype.
	'''
	return [
		{
			"doc_type": "Event",
			"doctype_or_field": "DocType",
			"property": "field_order",
			"property_type": "Data",
			"value": '["details", "subject", "custom_customer", "custom_agenda", "event_category", "event_type", "color", "send_reminder", "repeat_this_event", "column_break_4", "starts_on", "ends_on", "status", "sender", "all_day", "sync_with_google_calendar", "add_video_conferencing", "custom_is_billable", "custom_service", "custom_rate", "custom_service_description", "sb_00", "google_calendar", "google_calendar_id", "cb_00", "google_calendar_event_id", "google_meet_link", "pulled_from_google_calendar", "section_break_13", "repeat_on", "repeat_till", "column_break_16", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday", "section_break_8", "description", "participants", "event_participants"]',
		},
		{
			"doc_type": "Event",
			"doctype_or_field": "DocField",
			"field_name": "subject",
			"property": "in_list_view",
			"property_type": "Check",
			"value": "1",
		},
		{
			"doc_type": "Event",
			"doctype_or_field": "DocField",
			"field_name": "status",
			"property": "in_list_view",
			"property_type": "Check",
			"value": "1",
		},
		{
			"doc_type": "Event",
			"doctype_or_field": "DocField",
			"field_name": "starts_on",
			"property": "in_list_view",
			"property_type": "Check",
			"value": "1",
		},
		{
			"doc_type": "Event",
			"doctype_or_field": "DocField",
			"field_name": "event_type",
			"property": "in_list_view",
			"property_type": "Check",
			"value": "0",
		},
		{
			"doc_type": "Event",
			"doctype_or_field": "DocField",
			"field_name": "custom_customer",
			"property": "in_list_view",
			"property_type": "Check",
			"value": "1",
		},
		{
			"doc_type": "Event",
			"doctype_or_field": "DocField",
			"field_name": "starts_on",
			"property": "width",
			"property_type": "Data",
			"value": "3",
		},
	]
