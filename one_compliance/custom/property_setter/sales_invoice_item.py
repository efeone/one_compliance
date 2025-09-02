def get_sales_invoice_item_property_setters():
	'''
		Get property setters for Sales Invoice Item doctype.
	'''
	return [
		{
			"doc_type": "Sales Invoice Item",
			"doctype_or_field": "DocField",
			"field_name": "section_break_54",
			"property": "hidden",
			"property_type": "Check",
			"value": "1",
		},
		{
			"doc_type": "Sales Invoice Item",
			"doctype_or_field": "DocField",
			"field_name": "internal_transfer_section",
			"property": "hidden",
			"property_type": "Check",
			"value": "1",
		},
		{
			"doc_type": "Sales Invoice Item",
			"doctype_or_field": "DocField",
			"field_name": "section_break_18",
			"property": "hidden",
			"property_type": "Check",
			"value": "1",
		},
		{
			"doc_type": "Sales Invoice Item",
			"doctype_or_field": "DocField",
			"field_name": "drop_ship",
			"property": "hidden",
			"property_type": "Check",
			"value": "1",
		},
		{
			"doc_type": "Sales Invoice Item",
			"doctype_or_field": "DocField",
			"field_name": "grant_commission",
			"property": "hidden",
			"property_type": "Check",
			"value": "1",
		},
		{
			"doc_type": "Sales Invoice Item",
			"doctype_or_field": "DocField",
			"field_name": "is_free_item",
			"property": "hidden",
			"property_type": "Check",
			"value": "1",
		},
		{
			"doc_type": "Sales Invoice Item",
			"doctype_or_field": "DocType",
			"property": "field_order",
			"property_type": "Data",
			"value": '["barcode", "has_item_scanned", "item_code", "col_break1", "item_name", "customer_item_code", "description_section", "description", "gst_hsn_code", "item_group", "brand", "image_section", "image", "image_view", "quantity_and_rate", "qty", "stock_uom", "col_break2", "uom", "conversion_factor", "stock_qty", "section_break_17", "price_list_rate", "base_price_list_rate", "discount_and_margin", "margin_type", "margin_rate_or_amount", "rate_with_margin", "column_break_19", "discount_percentage", "discount_amount", "base_rate_with_margin", "section_break1", "rate", "amount", "item_tax_template", "gst_treatment", "col_break3", "base_rate", "base_amount", "pricing_rules", "stock_uom_rate", "is_free_item", "grant_commission", "section_break_21", "net_rate", "net_amount", "column_break_24", "base_net_rate", "base_net_amount", "taxable_value", "gst_details_section", "igst_rate", "cgst_rate", "sgst_rate", "cess_rate", "cess_non_advol_rate", "cb_gst_details", "igst_amount", "cgst_amount", "sgst_amount", "cess_amount", "cess_non_advol_amount", "drop_ship", "delivered_by_supplier", "accounting", "income_account", "is_fixed_asset", "asset", "finance_book", "col_break4", "expense_account", "discount_account", "deferred_revenue", "deferred_revenue_account", "service_stop_date", "enable_deferred_revenue", "column_break_50", "service_start_date", "service_end_date", "section_break_18", "weight_per_unit", "total_weight", "column_break_21", "weight_uom", "warehouse_and_reference", "warehouse", "target_warehouse", "quality_inspection", "pick_serial_and_batch", "serial_and_batch_bundle", "batch_no", "incoming_rate", "col_break5", "allow_zero_valuation_rate", "serial_no", "item_tax_rate", "actual_batch_qty", "actual_qty", "edit_references", "sales_order", "so_detail", "sales_invoice_item", "column_break_74", "delivery_note", "dn_detail", "delivered_qty", "internal_transfer_section", "purchase_order", "column_break_92", "purchase_order_item", "accounting_dimensions_section", "cost_center", "dimension_col_break", "project", "section_break_54", "page_break"]',
		},
		{
			"doc_type": "Sales Invoice Item",
			"doctype_or_field": "DocField",
			"field_name": "target_warehouse",
			"property": "hidden",
			"property_type": "Check",
			"value": "1",
		},
		{
			"doc_type": "Sales Invoice Item",
			"doctype_or_field": "DocField",
			"field_name": "barcode",
			"property": "hidden",
			"property_type": "Check",
			"value": "0",
		},
		{
			"doc_type": "Sales Invoice Item",
			"doctype_or_field": "DocField",
			"field_name": "discount_account",
			"property": "mandatory_depends_on",
			"property_type": "Code",
			"value": "",
		},
		{
			"doc_type": "Sales Invoice Item",
			"doctype_or_field": "DocField",
			"field_name": "discount_account",
			"property": "hidden",
			"property_type": "Check",
			"value": "1",
		},
	]

