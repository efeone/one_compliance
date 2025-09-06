import frappe
from frappe import _

@frappe.whitelist()
def enqueue_replace_abbr(company, old, new):
	kwargs = dict(queue='long', company=company, old=old, new=new)
	frappe.enqueue(replace_abbr, **kwargs)


@frappe.whitelist()
def replace_abbr(company, old, new):
	"""Replace abbreviation for company and rename related records"""
	new = (new or "").strip()
	if not new:
		frappe.throw(_("Abbr cannot be blank or space"))

	frappe.only_for("System Manager")

	frappe.db.set_value("Company", company, "abbr", new)

	# doctypes where company abbreviation is used in name
	doctypes = [
		"Warehouse",
		"Account",
		"Cost Center",
		"Department",
		"Sales Taxes and Charges Template",
		"Purchase Taxes and Charges Template",
	]

	for dt in doctypes:
		records = frappe.get_all(
			dt,
			filters={"company": company},
			pluck = "name"
		)

		for name in records:
			parts = name.rsplit(" - ", 1)

			# only rename if no abbr or matches old abbr
			if len(parts) == 1 or parts[1].lower() == old.lower():
				new_name = f"{parts[0]} - {new}"

				# Skip if new name already exists
				if frappe.db.exists(dt, new_name):
					continue

				try:
					frappe.rename_doc(dt, name, new_name, force=True)
				except Exception as e:
					frappe.log_error(
						f"Failed renaming {dt} {name} → {new_name}: {e}",
						"Replace Abbreviation"
					)
