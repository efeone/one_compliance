def get_sales_order_custom_fields():
	'''
		Method to get custom fields for Sales Order doctype
	'''
	return {
		"Sales Order": [
			{
				"fieldname": "custom_assign_to",
				"fieldtype": "Table MultiSelect",
				"insert_after": "custom_expected_start_date",
				"label": "Assign To",
				"mandatory_depends_on": "eval: doc.custom_create_project_automatically",
				"options": "Employee Details",
			},
			{
				"allow_on_submit": 1,
				"fieldname": "invoice_generation_date",
				"fieldtype": "Date",
				"insert_after": "transaction_date",
				"label": "Invoice Generation Date",
				"read_only": 1,
			},
			{
				"allow_on_submit": 1,
				"fieldname": "custom_billing_date",
				"fieldtype": "Date",
				"insert_after": "invoice_generation_date",
				"label": "Billing Date",
			},
			{
				"allow_on_submit": 1,
				"fieldname": "custom_billing_instruction",
				"fieldtype": "Long Text",
				"insert_after": "custom_section_break_rlk6s",
				"label": "Billing Instruction",
				"read_only": 1,
			},
			{
				"fieldname": "custom_column_break_nhc2l",
				"fieldtype": "Column Break",
				"insert_after": "custom_assign_to",
			},
			{
				"fieldname": "custom_create_project_automatically",
				"fieldtype": "Check",
				"insert_after": "scan_barcode",
				"label": "Create Project Automatically",
			},
			{
				"fieldname": "custom_expected_end_date",
				"fieldtype": "Date",
				"in_list_view": 1,
				"insert_after": "custom_column_break_nhc2l",
				"label": "Expected End Date",
			},
			{
				"fieldname": "custom_expected_start_date",
				"fieldtype": "Date",
				"insert_after": "custom_project_name",
				"label": "Expected Start Date",
				"mandatory_depends_on": "eval: doc.custom_create_project_automatically",
			},
			{
				"fieldname": "custom_is_rework",
				"fieldtype": "Check",
				"insert_after": "is_export_with_gst",
				"label": "Is Rework",
			},
			{
				"default": "Low",
				"fieldname": "custom_priority",
				"fieldtype": "Select",
				"insert_after": "custom_expected_end_date",
				"label": "Priority",
				"options": "Medium\nLow\nHigh",
			},
			{
				"depends_on": "eval:!doc.custom_project_name_automatically;",
				"fieldname": "custom_project_name",
				"fieldtype": "Data",
				"insert_after": "custom_project_name_automatically",
				"label": "Project Name",
			},
			{
				"fieldname": "custom_project_name_automatically",
				"fieldtype": "Check",
				"insert_after": "custom_section_break_siqmb",
				"label": "Project Name Automatically",
			},
			{
				"fieldname": "custom_reimbursement",
				"fieldtype": "Tab Break",
				"insert_after": "party_account_currency",
				"label": "Reimbursement",
			},
			{
				"allow_on_submit": 1,
				"fieldname": "custom_reimbursement_details",
				"fieldtype": "Table",
				"insert_after": "custom_reimbursement_details_",
				"label": "Reimbursement Details",
				"options": "Reimbursement Details",
			},
			{
				"fieldname": "custom_reimbursement_details_",
				"fieldtype": "Section Break",
				"insert_after": "custom_reimbursement",
				"label": "Reimbursement Details ",
			},
			{
				"fieldname": "custom_section_break_rlk6s",
				"fieldtype": "Section Break",
				"insert_after": "net_total",
			},
			{
				"depends_on": "eval: doc.custom_create_project_automatically",
				"fieldname": "custom_section_break_siqmb",
				"fieldtype": "Section Break",
				"insert_after": "custom_billing_instruction",
				"label": "Project",
			},
			{
				"allow_on_submit": 1,
				"fieldname": "custom_total_reimbursement_amount",
				"fieldtype": "Currency",
				"insert_after": "custom_reimbursement_details",
				"label": "Total Reimbursement Amount",
			},
			{
				"fieldname": "event",
				"fieldtype": "Link",
				"label": "Event",
				"insert_after": "custom_total_reimbursement_amount",
				"options": "Event",
				"read_only": 1,
			},
			{
				"fieldname": "follow_up_for_next_project",
				"fieldtype": "Check",
				"label": "Follow up for next Project",
				"insert_after": "custom_create_project_automatically"
			},
			{
				"fieldname": "follow_up_completed",
				"fieldtype": "Check",
				"label": "Follow up Completed",
				"insert_after": "follow_up_for_next_project",
				"hidden": 1
			},
			{
				"fieldname": "compliance_agreement",
				"fieldtype": "Link",
				"label": "Compliance Agreement",
				"options": "Compliance Agreement",
				"insert_after": "custom_is_rework",
				"read_only": 1
			},
			{

				"fieldname": "is_premium_project",
				"fieldtype": "Check",
				"label": "Is Premium Project",
				"insert_after": "amended_from"
			},
			{
				"fieldname": "is_outsource_service",
				"fieldtype": "Check",
				"label": "Is Outsource Service",
				"insert_after": "is_premium_project",
				"allow_on_submit": 1
			},
			{
				"fieldname": "supplier",
				"fieldtype": "Link",
				"label": "Supplier",
				"options": "Supplier",
				"insert_after": "custom_billing_date",
				"allow_on_submit": 1,
				"depends_on": "eval: doc.is_outsource_service"
			},
			{
				"fieldname": "purchase_invoice",
				"fieldtype": "Link",
				"label": "Purchase Invoice",
				"options": "Purchase Invoice",
				"insert_after": "supplier",
				"allow_on_submit": 1,
				"depends_on": "eval: doc.is_outsource_service"
			},
			{
				"fieldname": "payment_status",
				"fieldtype": "Data",
				"label": "Payment Status",
				"insert_after": "purchase_invoice",
				"read_only": 1,
				"depends_on": "eval: doc.is_outsource_service",
				"fetch_from": "purchase_invoice.status"
			}


		]
	}
