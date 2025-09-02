def get_terms_and_conditions_custom_fields():
	'''
		Method to get custom fields for Terms and Conditions doctype
	'''
	return {
		"Terms and Conditions": [
			{
				"default": "1",
				"fieldname": "compliance",
				"fieldtype": "Check",
				"in_list_view": 1,
				"insert_after": "buying",
				"label": "Compliance",
			}
		]
	}
