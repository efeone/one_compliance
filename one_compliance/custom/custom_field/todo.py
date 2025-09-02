def get_todo_custom_fields():
	'''
		Method to get custom fields for ToDo doctype
	'''
	return {
		"ToDo": [
			{
				"fieldname": "company",
				"label": "Company",
				"fieldtype": "Link",
				"options": "Company",
				"insert_after": "priority",
				"in_list_view": 1,
				"in_standard_filter": 1,
			},
			{
				"fieldname": "client",
				"label": "Client",
				"fieldtype": "Link",
				"options": "Customer",
				"insert_after": "reference_name",
				"depends_on": "eval:doc.reference_type == 'Sales Order'",
				"in_list_view": 1,
				"in_standard_filter": 1,
			},
			{
				"fieldname": "compliance_sub_category",
				"label": "Compliance Sub Category",
				"fieldtype": "Link",
				"options": "Compliance Sub Category",
				"insert_after": "client",
				"depends_on": "eval:doc.reference_type == 'Sales Order'",
				"in_list_view": 1,
				"in_standard_filter": 1,
			}
		]
	}
