import frappe

def execute():
	"""Sync Item Defaults income accounts from Compliance Sub Category."""
	for s in frappe.get_all("Compliance Sub Category", filters={"is_billable": 1, "item_code": ["is", "set"]}, fields=["name", "item_code"]):
		
		if not frappe.db.exists("Item", s.item_code):
			continue

		target = {d.company: d.default_income_account for d in frappe.get_all("Sub Category Account", filters={"parent": s.name}, fields=["company", "default_income_account"])}
		current = {d.company: d for d in frappe.get_all("Item Default", filters={"parent": s.item_code}, fields=["name", "company", "income_account"])}

		for comp, acc in target.items():
			if comp in current:
				if current[comp].income_account != acc:
					frappe.db.sql("UPDATE `tabItem Default` SET income_account=%s WHERE name=%s", (acc, current[comp].name))
			else:
				frappe.db.sql("""
					INSERT INTO `tabItem Default` (name, parent, parentfield, parenttype, company, income_account, idx)
					VALUES (%s, %s, 'item_defaults', 'Item', %s, %s, 1)
				""", (frappe.generate_hash(length=10), s.item_code, comp, acc))

	frappe.clear_cache(doctype="Item")
