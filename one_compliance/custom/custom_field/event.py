def get_event_custom_fields():
	'''
		Method to get custom fields for Event doctype
	'''
	return {
		"Event": [
			{
				"depends_on": "custom_is_billable",
				"fieldname": "custom_rate",
				"fieldtype": "Currency",
				"insert_after": "custom_service",
				"label": "Rate",
			},
			{
				"depends_on": "custom_is_billable",
				"fieldname": "custom_service",
				"fieldtype": "Link",
				"insert_after": "custom_is_billable",
				"label": "Service",
				"options": "Compliance Sub Category",
			},
			{
				"depends_on": "custom_is_billable",
				"fieldname": "custom_service_description",
				"fieldtype": "Small Text",
				"insert_after": "custom_rate",
				"label": "Service Description",
			},
			{
				"fieldname": "custom_is_billable",
				"fieldtype": "Check",
				"insert_after": "add_video_conferencing",
				"label": "Is Billable",
			},
			{
				"fieldname": "custom_customer",
				"fieldtype": "Link",
				"in_list_view": 1,
				"insert_after": "subject",
				"label": "Customer",
				"options": "Customer",
			},
			{
				"fieldname": "custom_agenda",
				"fieldtype": "Small Text",
				"insert_after": "custom_customer",
				"label": "Agenda",
			},
			{
				"fieldname": "company",
				"fieldtype": "Link",
				"insert_after": "starts_on",
				"label": "Company",
				"options": "Company",
				"reqd": 1,
			},
		]
	}
