def get_timesheet_detail_custom_fields():
    """
    Returns custom fields for Timesheet Detail doctype.
    """
    return {
		"Timesheet Detail": [
			{
				"fieldname": "lag_time",
				"fieldtype": "Duration",
				"label": "Lag Time",
				"insert_after": "to_time",
			}
		]
	}
