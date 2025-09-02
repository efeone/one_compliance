def get_project_template_property_setters():
	'''
		Get property setters for Project Template doctype.
	'''
	return [
		{
			"doc_type": "Project Template",
			"doctype_or_field": "DocType",
			"property": "field_order",
			"property_type": "Data",
			"value": '["project_type", "custom_project_duration", "column_break_igely", "compliance_category", "compliance_sub_category", "category_type", "section_break_e01k0", "tasks", "custom_documents_required", "description"]',
		}
	]
