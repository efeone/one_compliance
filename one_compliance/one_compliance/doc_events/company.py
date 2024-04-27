import frappe
from frappe import _

@frappe.whitelist()
def enqueue_replace_abbr(company, old, new):
	kwargs = dict(queue='long', company=company, old=old, new=new)
	frappe.enqueue('one_compliance.one_compliance.doc_events.company.replace_abbr', **kwargs)

@frappe.whitelist()
def replace_abbr(company, old, new):
	new = new.strip()
	if not new:
		frappe.throw(_("Abbr can not be blank or space"))

	frappe.only_for("System Manager")

	frappe.db.set_value("Company", company, "abbr", new)

	def _rename_record(doc):
		parts = doc[0].rsplit(" - ", 1)
		if len(parts) == 1 or parts[1].lower() == old.lower():
			frappe.rename_doc(dt, doc[0], parts[0] + " - " + new, force=True)

	def _rename_records(dt):
		# rename is expensive so let's be economical with memory usage
		doc = (d for d in frappe.db.sql("select name from `tab%s` where company=%s" % (dt, '%s'), company))
		for d in doc:
			_rename_record(d)

	for dt in ["Warehouse", "Account", "Cost Center", "Department",
			"Sales Taxes and Charges Template", "Purchase Taxes and Charges Template"]:
		_rename_records(dt)
