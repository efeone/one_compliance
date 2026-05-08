import frappe

def execute():
	"""Sync Item Defaults income accounts from Compliance Sub Category."""
	sub_categories = frappe.get_all("Compliance Sub Category", 
		filters={"is_billable": 1, "item_code": ["not in", ["", None]]}, 
		fields=["name", "item_code"])

	if not sub_categories:
		return

	sub_cat_names = [d.name for d in sub_categories]
	item_codes = [d.item_code for d in sub_categories]

	all_targets = frappe.get_all("Sub Category Account", 
		filters={"parent": ["in", sub_cat_names]}, 
		fields=["parent", "company", "default_income_account"])
	
	targets_by_subcat = {}
	for t in all_targets:
		targets_by_subcat.setdefault(t.parent, []).append(t)

	all_defaults = frappe.get_all("Item Default", 
		filters={"parent": ["in", item_codes], "parenttype": "Item"}, 
		fields=["parent", "name", "company", "income_account", "idx"],
		order_by="idx desc")
	
	defaults_by_item = {}
	for d in all_defaults:
		defaults_by_item.setdefault(d.parent, []).append(d)

	existing_items = set([d.name for d in frappe.get_all("Item", filters={"name": ["in", item_codes]}, fields=["name"])])

	for sub_cat in sub_categories:
		if sub_cat.item_code not in existing_items:
			continue

		target_accounts = targets_by_subcat.get(sub_cat.name, [])
		if not target_accounts:
			continue

		existing_defaults = defaults_by_item.get(sub_cat.item_code, [])
		
		current_rows = {d.company: d for d in existing_defaults}
		max_idx = existing_defaults[0].idx if existing_defaults else 0
		
		for row in target_accounts:
			if row.company in current_rows:
				if current_rows[row.company].income_account != row.default_income_account:
					frappe.db.set_value("Item Default", current_rows[row.company].name, 
						"income_account", row.default_income_account, update_modified=True)
			else:
				max_idx += 1
				new_row = frappe.get_doc({
					"doctype": "Item Default",
					"parent": sub_cat.item_code,
					"parenttype": "Item",
					"parentfield": "item_defaults",
					"company": row.company,
					"income_account": row.default_income_account,
					"idx": max_idx
				})
				new_row.db_insert()

	frappe.clear_cache(doctype="Item")
