def get_department_custom_fields():
	'''
		Method to get custom fields for Department doctype
	'''
	return {
		"Department": [
			{
				"fieldname": "is_compliance",
				"fieldtype": "Check",
				"insert_after": "disabled",
				"label": "Is Compliance",
			},
			{
				"fieldname": "head_of_department",
				"fieldtype": "Link",
				"ignore_user_permissions": 1,
				"label": "Head Of Department",
				"options": "Employee",
			},
		]
	}
