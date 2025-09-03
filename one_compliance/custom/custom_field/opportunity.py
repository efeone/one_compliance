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
			{
				"fieldname": "sales_order",
				"fieldtype": "Link",
				"label": "Sales Order",
				"insert_after": "annual_revenue",
				"options": "Sales Order"
			},
			{
				"fieldname": "opportunity_date",
				"fieldtype": "Date",
				"label": "Opportunity Date",
				"insert_after": "sales_order",
				"default": "Today"
			},
			{
				"fieldname": "notes_html",
				"fieldtype": "HTML",
				"label": "Notes",			
				"insert_after": "custom_documents_required"
			},
			{
				"fieldname": "follow_up_reply",
				"fieldtype": "Small Text",
				"label": "Follow up Reply",			
				"insert_after": "open_activities_html"
			}
		]
	}
