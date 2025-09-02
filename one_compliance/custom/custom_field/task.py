def get_task_custom_fields():
	'''
		Method to get custom fields for Task doctype
	'''
	return {
		"Task": [
			{
				"depends_on": "eval:doc.custom_is_payable",
				"fieldname": "custom_task_payment_informations",
				"fieldtype": "Table",
				"insert_after": "custom_section_break_ayygy",
				"label": "Task Payment Informations",
				"options": "Task Payment Information",
			},
			{
				"fieldname":"readiness_status",
				"fieldtype":"Select",
				"label":"Readiness Status",
				"options":"\nNot Ready\nReady",
				"in_list_view":1,
				"insert_after":"status",
			},
			{
				"fieldname": "custom_section_break_ayygy",
				"fieldtype": "Section Break",
				"insert_after": "custom_user_remark",
			},
			{
				"depends_on": "eval:!doc.is_template",
				"fieldname": "custom_task_document_items",
				"fieldtype": "Table",
				"insert_after": "custom_document_checklist",
				"label": "Task Document Items",
    			"options": "Task Document Item",
				"read_only": 1,
			},
			{
				"fieldname": "custom_document_checklist",
				"fieldtype": "Section Break",
				"insert_after": "custom_is_payable",
				"label": "Document Checklist",
			},
			{
				"fieldname": "custom_serial_number",
				"fieldtype": "Data",
				"insert_after": "completed_on",
				"label": "Serial Number",
			},
			{
				"fieldname": "custom_user_remark",
				"fieldtype": "Small Text",
				"insert_after": "custom_reference_date",
				"label": "User Remark",
			},
			{
				"fieldname": "custom_column_break_hrdgn",
				"fieldtype": "Column Break",
				"insert_after": "custom_mode_of_payment",
			},
			{
				"fieldname": "custom_reference_date",
				"fieldtype": "Date",
				"insert_after": "custom_reference_number",
				"label": "Reference Date",
			},
			{
				"fieldname": "custom_reference_number",
				"fieldtype": "Data",
				"insert_after": "custom_column_break_hrdgn",
				"label": "Reference Number",
			},
			{
				"depends_on": "eval:doc.custom_is_payable",
				"fieldname": "custom_payment_info",
				"fieldtype": "Section Break",
				"insert_after": "custom_task_document_items",
				"label": "Payment Info",
			},
			{
				"fieldname": "custom_mode_of_payment",
				"fieldtype": "Link",
				"insert_after": "custom_payable_amount",
				"label": "Mode of Payment",
				"mandatory_depends_on": "eval:doc.custom_is_payable",
				"options": "Mode of Payment",
			},
			{
				"fieldname": "custom_payable_amount",
				"fieldtype": "Currency",
				"insert_after": "custom_payment_info",
				"label": "Payable Amount",
				"mandatory_depends_on": "eval:doc.custom_is_payable",
			},
			{
				"fieldname": "custom_is_payable",
				"fieldtype": "Check",
				"insert_after": "hold",
				"label": "Is Payable",
			},
			{
				"fetch_from": "project.project_name",
				"fetch_if_empty": 0,
				"fieldname": "project_name",
				"fieldtype": "Data",
				"insert_after": "project",
				"label": "Project Name",
			},
			{
				"fieldname": "hold",
				"fieldtype": "Check",
				"hidden": 1,
				"insert_after": "is_template",
				"label": "Hold",
				"read_only": 1,
			},
			{
				"fetch_from": "project.category_type",
				"fetch_if_empty": 0,
				"fieldname": "category_type",
				"fieldtype": "Data",
				"insert_after": "project_name",
				"label": "Category Type",
			},
			{
				"fetch_from": "project.customer",
				"fetch_if_empty": 0,
				"fieldname": "customer",
				"fieldtype": "Link",
				"in_list_view": 1,
				"insert_after": "category_type",
				"label": "Customer",
				"options": "Customer",
			},
			{
				"depends_on": 'eval: doc.is_template == "0"',
				"fieldname": "assigned_to",
				"fieldtype": "Data",
				"insert_after": "parent_task",
				"label": "Assigned To",
			},
			{
				"fieldname": "compliance_sub_category",
				"fieldtype": "Link",
				"insert_after": "type",
				"label": "Compliance Sub Category",
				"options": "Compliance Sub Category",
				"read_only": 1,
			},
			{
				"fieldname": "task_weightage",
				"fieldtype": "Select",
				"label": "Task Weightage",
				"options": "\n0\n1\n2\n3\n4\n5\n",
				"insert_after": "start"
			}
		]
	}
