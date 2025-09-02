def get_sales_invoice_custom_fields():
	'''
		Method to get custom fields for Sales Invoice doctype
	'''
	return {
		"Sales Invoice": [
			{
				"default": "1",
				"fieldname": "is_compliance_invoice",
				"fieldtype": "Check",
				"label": "Is Compliance Invoice",
			}
		]
	}
