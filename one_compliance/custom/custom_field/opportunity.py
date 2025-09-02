def get_opportunity_custom_fields():
	'''
		Method to get custom fields for Opportunity doctype
	'''
	return {
		"Opportunity": [
			{
				"fieldname": "custom_documents_required",
				"fieldtype": "Table",
				"insert_after": "custom_section_break_wwmzg",
				"label": "Documents Required",
				"options": "Document Required",
			},
			{
				"fieldname": "custom_section_break_wwmzg",
				"fieldtype": "Section Break",
				"insert_after": "total",
			},
		]
	}
