def get_quotation_property_setters():
	'''
		Get property setters for Quotation doctype.
	'''
	return [
		{
			"doc_type": "Quotation",
			"doctype_or_field": "DocField",
			"field_name": "shipping_rule",
			"property": "hidden",
			"property_type": "Check",
			"value": "1",
		},
		{
			"doc_type": "Quotation",
			"doctype_or_field": "DocField",
			"field_name": "scan_barcode",
			"property": "hidden",
			"property_type": "Check",
			"value": "1",
		},
		{
			"doc_type": "Quotation",
			"doctype_or_field": "DocField",
			"field_name": "items",
			"property": "label",
			"property_type": "Data",
			"value": "Services",
		},
	]
