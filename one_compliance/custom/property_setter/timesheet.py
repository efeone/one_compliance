def get_timesheet_property_setters():
	'''
		Get property setters for Timesheet doctype.
	'''
	return [
		{
			"doc_type": "Timesheet",
			"doctype_or_field": "DocType",
			"property": "field_order",
			"property_type": "Data",
			"value": '["title", "naming_series", "company", "customer", "currency", "exchange_rate", "sales_invoice", "column_break_3", "salary_slip", "status", "parent_project", "employee_detail", "employee", "employee_name", "department", "column_break_9", "user", "start_date", "end_date", "section_break_5", "time_logs", "working_hours", "total_hours", "billing_details", "total_billable_hours", "base_total_billable_amount", "base_total_billed_amount", "base_total_costing_amount", "column_break_10", "total_billed_hours", "total_billable_amount", "total_billed_amount", "total_costing_amount", "per_billed", "section_break_18", "note", "custom_section_break_0jvhs", "custom_end_of_the_day_review", "custom_column_break_7mef3", "custom_tomorrows_plan", "amended_from"]',
		}
	]
