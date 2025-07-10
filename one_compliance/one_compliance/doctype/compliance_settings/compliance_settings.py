# Copyright (c) 2023, efeone and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import getdate


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
	from one_compliance.one_compliance.doctype.compliance_agreement.compliance_agreement import (
		check_project_exists_or_not,
		create_project_against_sub_category,
	)
	if self.status == 'Active' and self.workflow_state=='Customer Approved':
		if self.compliance_category_details:
			for compliance_category in self.compliance_category_details:
				if not check_project_exists_or_not(compliance_category.compliance_sub_category, self.name):
					if compliance_category.compliance_date and getdate(compliance_category.compliance_date) == getdate(starting_date):
						try:
							create_project_against_sub_category(self.name, compliance_category.compliance_sub_category, compliance_category.name, compliance_category.compliance_date)
						except Exception as e:
							frappe.log_error(str(e), 'Error in Compliance Agreement Creating Project' + self.name)

@frappe.whitelist()
def compliance_date_update(compliance_date, compliance_agreement = None):
	from one_compliance.one_compliance.doctype.compliance_agreement.compliance_agreement import (
		update_compliance_dates,
	)

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