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
			}
		]		
	}
  

