def get_employee_checkin_property_setters():
	'''
		Get property setters for Employee Checkin doctype.
	'''
	return [
		{
			"doc_type": "Employee Checkin",
			"doctype_or_field": "DocField",
			"field_name": "time",
			"property": "read_only",
			"property_type": "Check",
			"value": "1",
		},
		{
			"doc_type": "Employee Checkin",
			"doctype_or_field": "DocField",
			"field_name": "log_type",
			"property": "reqd",
			"property_type": "Check",
			"value": "1",
		},
	]
