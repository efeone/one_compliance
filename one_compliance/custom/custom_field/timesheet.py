def get_timesheet_custom_fields():
	'''
		Method to get custom fields for Timesheet doctype
	'''
	return {
		"Timesheet": [
			{
				"fieldname": "custom_section_break_0jvhs",
				"fieldtype": "Section Break",
				"insert_after": "note",
			},
			{
				"fieldname": "custom_tomorrows_plan",
				"fieldtype": "Small Text",
				"insert_after": "custom_column_break_7mef3",
				"label": "Tomorrows Plan",
			},
			{
				"fieldname": "custom_end_of_the_day_review",
				"fieldtype": "Small Text",
				"insert_after": "custom_section_break_0jvhs",
				"label": "End of the Day Review",
			},
			{
				"fieldname": "custom_column_break_7mef3",
				"fieldtype": "Column Break",
				"insert_after": "custom_end_of_the_day_review",
			},
			{
				"fieldname": "total_lag_hours",
				"fieldtype": "Float",
				"label": "Total Lag Hours",
				"insert_after": "column_break_8meg",
			},
			{
				"fieldname": "column_break_8meg",
				"fieldtype": "Column Break",
				"insert_after": "total_hours",
			},
			{
				"fieldname": "lag_notification_sent",
				"fieldtype": "Check",
				"label": "Lag Notification Sent",
				"insert_after": "reason_for_lag_time",
                "hidden": 1,
			}
		]
	}
