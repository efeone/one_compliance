def get_customer_group_custom_fields():
	'''
		Method to get custom fields for Customer Group doctype
	'''
	return {
		"Customer Group": [
			{
				"fieldname": "hod",
				"fieldtype": "Link",
				"insert_after": "parent_customer_group",
				"label": "HOD",
				"options": "Employee",
			},
			{
				"fieldname": "hod_name",
				"fieldtype": "Data",
				"insert_after": "hod",
				"label": "HOD Name",
				"fetch_from": "hod.employee_name",
				"read_only": 1,
			}
		]
	}