def get_opportunity_item_custom_fields():
	'''
		Method to get custom fields for Opportunity Item doctype
	'''
	return {
		"Opportunity Item": [
			{
				"fieldname": "compliance_category",
				"label": "Compliance Category",
				"fieldtype": "Link",
				"options": "Compliance Category",
				"insert_after": "item_code",
				"in_list_view": 1,
				"columns": 2,
			},
			{
				"fieldname": "compliance_sub_category",
				"label": "Compliance Sub Category",
				"fieldtype": "Link",				
				"options": "Compliance Sub Category",		
				"insert_after": "compliance_category",
				"in_list_view": 1,
				"columns": 2,	
			},
			{
				"fieldname": "repeat_on",
				"label": "Repeat On",
				"fieldtype": "Check",
				"insert_after": "compliance_sub_category",
				"fetch_from": "compliance_sub_category.allow_repeat",
				"read_only": 1,
				"in_list_view": 1,
			},
			{
				"fieldname": "purpose",
				"label": "Purpose",
				"fieldtype": "Data",
				"insert_after": "repeat_on",
				"in_list_view": 1,
				"columns": 1,
			},
			{
				"fieldname": "initial_due_date",
				"label": "Initial Due Date",
				"fieldtype": "Date",
				"insert_after": "purpose",
			},
			{
				"fieldname": "remarks",
				"label": "Remarks",
				"fieldtype": "Small Text",
				"insert_after": "qty",
			}
		]
}