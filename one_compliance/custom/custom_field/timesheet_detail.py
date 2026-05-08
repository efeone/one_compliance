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
			},
			{
				"fieldname": "reason_for_lag_time",
				"fieldtype": "Small Text",
				"label": "Reason for Lag Time",
				"insert_after": "lag_time",
			},
			{
				"fieldname": "lag_notification_sent",
				"fieldtype": "Check",
				"label": "Lag Notification Sent",
				"insert_after": "reason_for_lag_time",
				"hidden": 1,
			},
			{
				"fieldname": "approval_status",
				"fieldtype": "Select",
				"label": "Approval Status(Lag Time)",
				"options": "\nPending\nApproved\nRejected",
				"default": "Pending",
				"insert_after": "lag_notification_sent",
			},
		]
	}
