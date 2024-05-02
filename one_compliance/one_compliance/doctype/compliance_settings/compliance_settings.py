# Copyright (c) 2023, efeone and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import *
from frappe.model.document import Document
from erpnext import get_company_currency, get_default_company

class ComplianceSettings(Document):
	pass

@frappe.whitelist()
def manual_project_creations(starting_date):
	company = get_default_company()
	enqueue_replace_abbr(company, 'A&A', 'ASA')
	# if starting_date:
	# 	agreements = frappe.db.get_all('Compliance Agreement', filters = {'status': 'Active'})
	# 	if agreements:
	# 		for agreement in agreements:
	# 			self = frappe.get_doc('Compliance Agreement', agreement.name)
	# 			create_project_if_not_exists(self, starting_date)
	# 		frappe.db.commit()
	return True

def create_project_if_not_exists(self, starting_date):
	from one_compliance.one_compliance.doctype.compliance_agreement.compliance_agreement import create_project_against_sub_category
	from one_compliance.one_compliance.doctype.compliance_agreement.compliance_agreement import check_project_exists_or_not
	if self.status == 'Active' and self.workflow_state=='Customer Approved':
		if self.compliance_category_details:
			for compliance_category in self.compliance_category_details:
				if not check_project_exists_or_not(compliance_category.compliance_sub_category, self.name):
					if compliance_category.compliance_date and getdate(compliance_category.compliance_date) == getdate(starting_date):
						create_project_against_sub_category(self.name, compliance_category.compliance_sub_category, compliance_category.name)

@frappe.whitelist()
def compliance_date_update(compliance_date, compliance_agreement = None):
	from one_compliance.one_compliance.doctype.compliance_agreement.compliance_agreement import update_compliance_dates

	filters = {'expected_start_date': getdate(compliance_date)}

	if compliance_agreement:
		filters['compliance_agreement'] = compliance_agreement

	projects = frappe.db.get_all('Project',filters = filters, fields = ['name','compliance_agreement'])
	if projects:
		for project in projects:
			agreement = frappe.get_doc('Compliance Agreement', project.compliance_agreement)
			if agreement.status == 'Active' and agreement.workflow_state=='Customer Approved':
				if agreement.compliance_category_details:
					for compliance_category in agreement.compliance_category_details:
						compliance_category_details_id = compliance_category.name
						if frappe.db.get_value('Compliance Category Details', compliance_category_details_id, 'compliance_date') == getdate(compliance_date):
							compliance_date = frappe.db.get_value('Compliance Category Details', compliance_category_details_id, 'compliance_date')
							update_compliance_dates(compliance_category_details_id)

@frappe.whitelist()
def enqueue_replace_abbr(company, old, new):
	replace_abbr(company, old, new)
	# kwargs = dict(queue='long', company=company, old=old, new=new)
	# frappe.enqueue('one_compliance.one_compliance.doctype.compliance_settings.compliance_settings.replace_abbr', **kwargs)


@frappe.whitelist()
def replace_abbr(company, old, new):
	print("qhfjhdcx")
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
