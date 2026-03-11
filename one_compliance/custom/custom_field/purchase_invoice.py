def get_purchase_invoice_custom_fields():
	'''
		Method to get custom fields for Purchase Invoice doctype
	'''
	return {
		"Purchase Invoice": [
			{
				"fieldname": "sales_order",
				"fieldtype": "Link",
				"label": "Sales Order",
				"insert_after": "project",
				"options": "Sales Order",
				"read_only": 1,
			},
			{
				"fieldname": "is_commission_invoice",
				"fieldtype": "Check",
				"label": "Is Commission Invoice",
				"insert_after": "apply_tds",
				"read_only": 1,
			},
			{
				"fieldname": "customer",
				"fieldtype": "Link",
				"label": "Customer",
				"insert_after": "is_commission_invoice",
				"options": "Customer",
				"read_only": 1,
			},
			{
				"fieldname": "compliance_sub_category",
				"fieldtype": "Link",
				"label": "Compliance Sub Category",
				"insert_after": "customer",
				"options": "Compliance Sub Category",
				"read_only": 1,
			}
		]		
	}
  

