
import frappe
from frappe.model.document import Document
from frappe import _

class ComplianceAgreement(Document):
	''' Method used for validate Signature '''
	def on_update_after_submit(self):
		self.sign_validation()

	def sign_validation(self):
		if self.workflow_state == 'Approved' and not self.authority_signature:
			frappe.throw('Authority Signature is required for Approval')
		if self.workflow_state == 'Customer Approved' and not self.customer_signature:
			frappe.throw('Customer Signature is required for Approval')

	@frappe.whitelist()
	def create_project_from_agreement(self):
		if self.compliance_category_details:
			for compliance_category in self.compliance_category_details:
				if compliance_category.compliance_sub_category:
					project_template  = frappe.db.get_value('Compliance Sub Category',compliance_category.compliance_sub_category,'project_template')
					if project_template:
						project = frappe.new_doc('Project')
						project.project_name = self.customer_name + '-' + compliance_category.compliance_sub_category
						project.project_template = project_template
						project.customer = self.customer
						project.save()
						frappe.msgprint("Project Created",alert = 1)
					else :
						frappe.throw(
						title = _('ALERT !!'),
						msg = _('Project Template does not exist')
						)
