import frappe

def execute():
	"""Sync Item Defaults income accounts from Compliance Sub Category."""
	for sub_cat in frappe.get_all("Compliance Sub Category", filters={"is_billable": 1, "item_code": ["is", "set"]}):
		doc = frappe.get_doc("Compliance Sub Category", sub_cat.name)
		item = frappe.get_doc("Item", doc.item_code)
		mismatch = False

		for row in doc.default_account:
			found = False
			for d in item.item_defaults:
				if d.company == row.company:
					found = True
					if d.income_account != row.default_income_account:
						d.income_account = row.default_income_account
						mismatch = True
					break
			if not found:
				item.append("item_defaults", {"company": row.company, "income_account": row.default_income_account})
				mismatch = True

		if mismatch:
			item.flags.ignore_mandatory = True
			item.flags.ignore_validate = True
			item.save(ignore_permissions=True)
