def get_sales_order_item_custom_fields():
	'''
		Method to get custom fields for Sales Order Item doctype
	'''
	return {
		"Sales Order Item": [
			{
				"fieldname": "custom_compliance_category",
				"fieldtype": "Link",
				"in_list_view": 1,
				"insert_after": "reserve_stock",
				"label": "Compliance Category",
				"options": "Compliance Category",
			},
			{
				"fieldname": "custom_compliance_subcategory",
				"fieldtype": "Link",
				"in_list_view": 1,
				"insert_after": "custom_compliance_category",
				"label": "Compliance Subcategory",
				"options": "Compliance Sub Category",
			},
			{
				"fieldname": "custom_instructions",
				"fieldtype": "Long Text",
				"insert_after": "item_name",
				"label": "Instructions",
			},
		]
	}
