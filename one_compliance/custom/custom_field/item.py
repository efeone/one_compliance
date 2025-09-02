def get_item_custom_fields():
	'''
		Method to get custom fields for Item doctype
	'''
	return {
		"Item": [
			{
				"fieldname": "is_service_item",
				"fieldtype": "Check",
				"insert_after": "disabled",
				"label": "Is Service Item",
				"read_only": 1,
			}
		]
	}
