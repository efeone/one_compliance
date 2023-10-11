# Copyright (c) 2023, efeone and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import *
from frappe.model.document import Document

class ComplianceSettings(Document):
	pass

@frappe.whitelist()
def manual_project_creations(starting_date):
	if starting_date:
		agreements = frappe.db.get_all('Compliance Agreement', filters = {'status': 'Active'})
		if agreements:
			for agreement in agreements:
				self = frappe.get_doc('Compliance Agreement', agreement.name)
				create_project_if_not_exists(self, starting_date)
			frappe.db.commit()
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
