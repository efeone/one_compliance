def get_project_template_task_custom_fields():
	'''
		Method to get custom fields for Project Template Task doctype
	'''
	return {
		"Project Template Task": [
			{
				"columns": 2,
				"depends_on": "eval:doc.custom_has_document",
				"fieldname": "custom_documents_required",
				"fieldtype": "Button",
				"in_list_view": 1,
				"insert_after": "custom_has_document",
				"label": "Documents Required",
			},
			{
				"columns": 1,
				"fieldname": "custom_has_document",
				"fieldtype": "Check",
				"in_list_view": 1,
				"insert_after": "custom_column_break_uv20g",
				"label": "Has Document",
			},
			{
				"fieldname": "custom_column_break_uv20g",
				"fieldtype": "Column Break",
				"insert_after": "employee_or_group",
			},
			{
				"columns": 1,
				"fieldname": "custom_task_duration",
				"fieldtype": "Int",
				"in_list_view": 1,
				"insert_after": "subject",
				"label": "Task Duration",
			},
			{
				"columns": 1,
				"fieldname": "type",
				"fieldtype": "Select",
				"in_list_view": 1,
				"insert_after": "task_weightage",
				"label": "Type",
				"options": "\nEmployee\nEmployee Group",
			},
			{
				"fieldname": "employee_or_group",
				"fieldtype": "Dynamic Link",
				"in_list_view": 1,
				"insert_after": "type",
				"label": "Employee or Group",
				"options": "type",
			},
			{
				"fieldname": "task_weightage",
				"fieldtype": "Select",
				"label": "Task Weightage",
				"options": "\n0\n1\n2\n3\n4\n5\n",
				"insert_after": "custom_task_duration",
				"in_list_view": 1
			}
		]
	}
