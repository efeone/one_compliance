def get_customer_custom_fields():
	'''
		Method to get custom fields for Customer doctype
	'''
	return {
		"Customer": [
			{
				"fieldname": "custom_invoice_due_days",
				"fieldtype": "Int",
				"insert_after": "custom_billing_customer",
				"label": "Invoice Due Days",
			},
			{
				"fieldname": "custom_audit_list",
				"fieldtype": "Table",
				"insert_after": "custom_legal_authority_list",
				"label": "Audit List",
				"options": "Audit List",
			},
			{
				"fieldname": "custom_billing_customer",
				"fieldtype": "Link",
				"insert_after": "image",
				"label": "Billing Customer",
				"options": "Customer",
			},
			{
				"fieldname": "custom_legal_authority_list",
				"fieldtype": "Table",
				"insert_after": "custom_section_break_lfnxi",
				"label": "Legal Authority List",
				"options": "Legal Authority List",
			},
			{
				"fieldname": "custom_annual_general_meeting_date",
				"fieldtype": "Date",
				"insert_after": "custom_column_break_izp7v",
				"label": "Annual General Meeting Date",
			},
			{
				"fieldname": "custom_date_of_incorporation",
				"fieldtype": "Date",
				"insert_after": "custom_customer_company_details",
				"label": "Date of Incorporation",
			},
			{
				"fieldname": "custom_section_break_lfnxi",
				"fieldtype": "Section Break",
				"insert_after": "custom_annual_general_meeting_date",
			},
			{
				"fieldname": "custom_column_break_izp7v",
				"fieldtype": "Column Break",
				"insert_after": "custom_date_of_incorporation",
			},
			{
				"fieldname": "custom_customer_company_details",
				"fieldtype": "Tab Break",
				"insert_after": "custom_invoice_due_days",
				"label": "Customer Company Details",
			},
			{
				"fieldname": "trade_name",
				"fieldtype": "Data",
				"in_list_view": 1,
				"insert_after": "customer_name",
				"label": "Trade Name",
			},
			{
				"fieldname": "state",
				"fieldtype": "Data",
				"insert_after": "opportunity_name",
				"label": "State",
			},
			{
				"fieldname": "file_number",
				"fieldtype": "Data",
				"insert_after": "customer_group",
				"label": "File number",
			},
			{
				"default": "1",
				"fieldname": "send_project_completion_mail",
				"fieldtype": "Check",
				"insert_after": "file_number",
				"label": "Send Project Completion Mail",
			},
			{
				"fieldname": "allow_edit",
				"fieldtype": "Check",
				"hidden": 1,
				"insert_after": "address_contacts",
				"label": "allow_edit",
			},
			{
				"depends_on": "",
				"fieldname": "address",
				"fieldtype": "Section Break",
				"insert_after": "allow_edit",
				"label": "Address",
			},
			{
				"fieldname": "other_details",
				"fieldtype": "Tab Break",
				"insert_after": "custom_audit_list",
				"label": "Other Details",
			},
			{
				"fieldname": "compliance_customer_type",
				"fieldtype": "Link",
				"insert_after": "customer_type",
				"label": "Client Type",
				"options": "Customer Type",
				"read_only_depends_on": "eval.doc.customer_type == 1",
				"reqd": 1,
			},
		]
	}
