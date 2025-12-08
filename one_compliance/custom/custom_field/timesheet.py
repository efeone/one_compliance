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
				"label": "Tomorrows Plan",
				"fieldtype": "Small Text",
				"insert_after": "custom_column_break_7mef3",
			},
			{
				"fieldname": "custom_end_of_the_day_review",
				"label": "End of the Day Review",
				"fieldtype": "Small Text",
				"insert_after": "custom_section_break_0jvhs",
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
			}
		]
	}
