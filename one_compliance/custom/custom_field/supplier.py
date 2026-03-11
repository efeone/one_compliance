def get_supplier_custom_fields():
	'''
		Method to get custom fields for Supplier doctype
	'''
	return {
		"Supplier": [
			{
				"fieldname": "is_promoter",
				"fieldtype": "Check",
				"insert_after": "supplier_type",
				"label": "Is Promoter",
			},
		]
	}
