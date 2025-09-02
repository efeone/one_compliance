def get_project_template_custom_fields():
	'''
		Method to get custom fields for Project doctype
	'''
	return {
		"Project Template": [
			{
				"fieldname": "custom_documents_required",
				"fieldtype": "Table",
				"insert_after": "tasks",
				"label": "Documents Required",
				"options": "Document Item",
			},
			{
				"fieldname": "enable_task_readiness_flow",
				"fieldtype": "Check",
				"label": "Enable Task Readiness Flow",
				"insert_after": "custom_project_duration",
			},
			{
				"fieldname": "custom_project_duration",
				"fieldtype": "Int",
				"insert_after": "project_type",
				"label": "Project Duration(Days)",
			},
			{
				"fetch_from": "compliance_sub_category.category_type",
				"fieldname": "category_type",
				"fieldtype": "Link",
				"insert_after": "compliance_sub_category",
				"label": "Category Type",
				"options": "Category Type",
			},
			{
				"fieldname": "description",
				"fieldtype": "Small Text",
				"insert_after": "custom_documents_required",
				"label": "Description",
			},
			{
				"fieldname": "section_break_e01k0",
				"fieldtype": "Section Break",
				"insert_after": "category_type",
			},
			{
				"fieldname": "column_break_igely",
				"fieldtype": "Column Break",
				"insert_after": "custom_project_duration",
			},
			{
				"fieldname": "compliance_sub_category",
				"fieldtype": "Link",
				"insert_after": "compliance_category",
				"label": "Compliance Sub Category",
				"options": "Compliance Sub Category",
			},
			{
				"fieldname": "compliance_category",
				"fieldtype": "Link",
				"insert_after": "column_break_igely",
				"label": "Compliance Category",
				"options": "Compliance Category",
				"reqd": 1,
			},
			{
				"fieldname": "custom_add_tasks",
				"fieldtype": "Button",
				"insert_after": "tasks",
				"label": "Add Tasks",
			},
			{
				"fieldname": "premium_tasks",
				"fieldtype": "Table",
				"label": "Premium Tasks",
				"options": "Premium Tasks",
				"insert_after": "custom_add_tasks",
			},
			{
				"fieldname": "custom_add_tasks2",
				"fieldtype": "Button",
				"label": "Add Tasks",
				"insert_after": "premium_tasks",
			},
		]
	}
