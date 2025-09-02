def get_item_property_setters():
	'''
		Get property setters for Item doctype.
	'''
	return [
		{
			"doc_type": "Item",
			"doctype_or_field": "DocField",
			"field_name": "sales_uom",
			"property": "hidden",
			"property_type": "Check",
			"value": "1",
		},
		{
			"doc_type": "Item",
			"doctype_or_field": "DocField",
			"field_name": "brand",
			"property": "hidden",
			"property_type": "Check",
			"value": "1",
		},
		{
			"doc_type": "Item",
			"doctype_or_field": "DocField",
			"field_name": "has_variants",
			"property": "hidden",
			"property_type": "Check",
			"value": "1",
		},
		{
			"doc_type": "Item",
			"doctype_or_field": "DocField",
			"field_name": "allow_alternative_item",
			"property": "hidden",
			"property_type": "Check",
			"value": "1",
		},
	]
