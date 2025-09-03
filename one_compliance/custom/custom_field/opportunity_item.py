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
			},
			{
				"fieldname": "compliance_sub_category",
				"label": "Compliance Sub Category",
				"fieldtype": "Link",				
				"options": "Compliance Sub Category",		
				"insert_after": "compliance_category",
				"in_list_view": 1,	
			}
		]
}