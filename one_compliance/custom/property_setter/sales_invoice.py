def get_sales_invoice_property_setters():
	'''
		Get property setters for Sales Invoice doctype.
	'''
	return [
		{
			"doc_type": "Sales Invoice",
			"doctype_or_field": "DocField",
			"field_name": "incoterm",
			"property": "hidden",
			"property_type": "Check",
			"value": "1",
		},
		{
			"doc_type": "Sales Invoice",
			"doctype_or_field": "DocField",
			"field_name": "shipping_rule",
			"property": "hidden",
			"property_type": "Check",
			"value": "1",
		},
		{
			"doc_type": "Sales Invoice",
			"doctype_or_field": "DocField",
			"field_name": "scan_barcode",
			"property": "hidden",
			"property_type": "Check",
			"value": "1",
		},
		{
			"doc_type": "Sales Invoice",
			"doctype_or_field": "DocField",
			"field_name": "items",
			"property": "label",
			"property_type": "Data",
			"value": "Services",
		},
	]
