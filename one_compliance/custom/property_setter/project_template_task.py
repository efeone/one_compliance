def get_project_template_task_property_setters():
	'''
	Get property setters for Project Template Task doctype.
	'''
	return [
		{
			"doc_type": "Project Template Task",
			"doctype_or_field": "DocField",
			"field_name": "subject",
			"property": "columns",
			"property_type": "Int",
			"value": "2",
		},
		{
			"doc_type": "Project Template Task",
			"doctype_or_field": "DocField",
			"field_name": "task",
			"property": "columns",
			"property_type": "Int",
			"value": "2",
		},
		{
			"doc_type": "Project Template Task",
			"doctype_or_field": "DocType",
			"property": "field_order",
			"property_type": "Data",
			"value": '["task", "subject", "task_duration_minutes", "custom_task_duration", "task_weightage", "type", "employee_or_group", "custom_column_break_uv20g", "custom_has_document", "custom_documents_required", "has_external_dependencies", "send_email_notification_for_lag_time"]',
		},
		{
			"doc_type": "Project Template Task",
			"doctype_or_field": "DocField",
			"field_name": "custom_documents_required",
			"property": "columns",
			"property_type": "Int",
			"value": "1",
		},
		{
			"doc_type": "Project Template Task",
			"doctype_or_field": "DocField",
			"field_name": "employee_or_group",
			"property": "columns",
			"property_type": "Int",
			"value": "1",
		},
		{
			"doc_type": "Project Template Task",
			"doctype_or_field": "DocField",
			"field_name": "task_weightage",
			"property": "columns",
			"property_type": "Int",
			"value": "1",
		},
	]
