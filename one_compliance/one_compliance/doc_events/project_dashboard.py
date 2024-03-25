from frappe import _

def get_data(data):
	return {
		"heatmap": True,
		"heatmap_message": _("This is based on the Time Sheets created against this project"),
		"fieldname": "project",
		"transactions": [
			{
				"label": _("Project"),
				"items": ["Task", "Timesheet"],
			},
            {"label": _("Issues and Update"), "items": ["Issue", "Project Update"]},
			{"label": _("Sales and Payaments"), "items": ["Sales Order", "Sales Invoice", "Payment Entry"]},
		],
	}