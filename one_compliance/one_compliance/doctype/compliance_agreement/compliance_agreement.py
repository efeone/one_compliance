import frappe
import json
from frappe.model.document import Document
from frappe.model.mapper import *
from frappe import _
from frappe.utils import *
from one_compliance.one_compliance.utils import *

class ComplianceAgreement(Document):
	''' Method used for validate Signature '''
	def on_update_after_submit(self):
		self.sign_validation()
		self.check_active_status_of_agreement()

	def before_insert(self):
		self.status = "Open"

	def check_active_status_of_agreement(self):
		if self.status == 'Active' and self.workflow_state=='Customer Approved':
			if not check_project_exists_or_not(self.compliance_category_details, self.name):
				self.create_project_from_agreement()

	def sign_validation(self):
		if self.workflow_state == 'Approved' and not self.authority_signature:
			frappe.throw('Authority Signature is required for Approval')
		if self.workflow_state == 'Customer Approved' and not self.customer_signature:
			frappe.throw('Customer Signature is required for Approval')

	def validate(self):
		self.date_validation()
		self.change_agreement_status()

	def date_validation(self):
		if getdate(self.valid_from) > getdate(self.valid_upto) :
			frappe.throw('From Date cannot be greater than Upto Date')

	@frappe.whitelist()
	def list_sub_category(self):
		rate = 0
		if self.compliance_category:
			for compliance_category in self.compliance_category:
				compliance_sub_category_list = get_compliance_sub_category_list(compliance_category)
				if compliance_sub_category_list:
					for compliance_sub_category in compliance_sub_category_list:
						rate += compliance_sub_category.rate
						if not check_exist_list(self, compliance_sub_category):
							self.append('compliance_category_details',{
								'compliance_category':compliance_sub_category.compliance_category,
								'compliance_sub_category':compliance_sub_category.name,
								'rate':compliance_sub_category.rate
							})
			self.total = rate
			return True

	@frappe.whitelist()
	def create_project_from_agreement(self):
		''' Method to create projects from Compliance Agreement '''
		if self.compliance_category_details:
			for compliance_category in self.compliance_category_details:
				if compliance_category.compliance_sub_category:
					project_template  = frappe.db.get_value('Compliance Sub Category', compliance_category.compliance_sub_category, 'project_template')
					if project_template:
						today = getdate(frappe.utils.today())
						project = frappe.new_doc('Project')
						project.project_name = self.customer_name + '-' + compliance_category.compliance_sub_category + '-' + str(today)
						project.customer = self.customer
						project.compliance_agreement = self.name
						project.compliance_sub_category = compliance_category.compliance_sub_category
						project.save()
						frappe.msgprint('Project Created for {0}.'.format(compliance_category.compliance_sub_category), alert = 1)
						project_template_doc = frappe.get_doc('Project Template', project_template)
						for template_task in project_template_doc.tasks:
							''' Method to create task against created project from the Project Template '''
							template_task_doc = frappe.get_doc('Task', template_task.task)
							task_doc = frappe.new_doc('Task')
							task_doc.compliance_sub_category = compliance_category.compliance_sub_category
							task_doc.subject = template_task.subject
							task_doc.project = project.name
							if template_task_doc.expected_time:
								task_doc.expected_time = template_task_doc.expected_time
							task_doc.save(ignore_permissions=True)
							if template_task.type and template_task.employee_or_group:
								frappe.db.set_value('Task',task_doc.name,'assigned_to',template_task.employee_or_group)
								if template_task.type == "Employee":
									employee = frappe.db.get_value('Employee', template_task.employee_or_group, 'user_id')
									if employee:
										create_todo('Task', task_doc.name, employee, employee, 'Tasks Assigned Successfully')
								if template_task.type == "Employee Group":
									employee_group = frappe.get_doc('Employee Group', template_task.employee_or_group)
									if employee_group.employee_list:
										for employee in employee_group.employee_list:
											create_todo('Task', task_doc.name, employee.user_id, employee.user_id, 'Tasks Assigned Successfully')
					else :
						frappe.throw( title = _('ALERT !!'), msg = _('Project Template does not exist for {0}'.format(compliance_category.compliance_sub_category)))
		return 1

	def change_agreement_status(self):
		if self.status != 'Hold':
			if self.valid_from:
				today = getdate(frappe.utils.today())
			if today < getdate(self.valid_from):
				self.status = "Open"
			elif ((self.valid_upto and today > getdate(self.valid_upto)) and not self.has_long_term_validity):
				self.status = "Expired"
			else:
				self.status = "Active"

@frappe.whitelist()
def check_project_status(compliance_agreement):
	if frappe.db.exists('Project', {'compliance_agreement':compliance_agreement, 'status':'Completed'}):
		return True

@frappe.whitelist()
def make_sales_invoice(source_name, target_doc=None):
	def set_missing_values(source, target):
		if frappe.db.exists('Project', {'compliance_agreement':source.name}):
			company = frappe.db.get_value('Project', {'compliance_agreement':source.name},'company')
			income_account = frappe.db.get_value('Company',company, 'default_income_account')
		if source.compliance_category_details:
			for sub_category in source.compliance_category_details:
				rate = calculate_rate(source.compliance_category_details, sub_category.compliance_category)
				if source.invoice_based_on == 'Project':
					target.append('items', {
						'item_name' : sub_category.compliance_sub_category,
						'rate' : sub_category.rate,
						'qty' : 1,
						'income_account' : income_account,
						'description' : sub_category.name,
					})
				if source.invoice_based_on == 'Consolidated':
					if not check_exist(target, sub_category.compliance_category):
						target.append('items', {
							'item_name' : sub_category.compliance_category,
							'rate' : rate,
							'qty' : 1,
							'income_account' : income_account,
							'description' : sub_category.name,
						})
	doclist = get_mapped_doc(
		'Compliance Agreement',
		source_name,
		{
			'Compliance Agreement':{
                'doctype':'Sales Invoice'

				},
			},
		target_doc,
		set_missing_values
	)
	doclist.save()

	return doclist

def check_exist(target, compliance_category):
	''' checking if item already exist in child table '''
	exist = False
	if target.items:
		for item in target.items:
			if compliance_category:
				if item.item_name == compliance_category:
					exist = True
	return exist

def calculate_rate(compliance_category_details, compliance_category):
	rate = 0
	for category in compliance_category_details:
		if category.compliance_category == compliance_category:
			rate += category.rate
	return rate

@frappe.whitelist()
def change_agreement_status_scheduler():
	'''Method used for set value to status field '''
	agreements = frappe.db.get_all('Compliance Agreement', filters = {'status': ['!=', 'Hold'], 'docstatus': ['!=', 2]})
	if agreements:
		for agreement in agreements:
			self = frappe.get_doc('Compliance Agreement', agreement.name)
			if self.valid_from:
				today = getdate(frappe.utils.today())
			if today < getdate(self.valid_from):
				self.status = "Open"
			elif ((self.valid_upto and today > getdate(self.valid_upto)) and not self.has_long_term_validity):
				self.status = "Expired"
			else:
				self.status = "Active"
			self.save()

def get_compliance_sub_category_list(compliance_category):
	'''method used for list sub category'''
	sub_category_list = frappe.db.get_list('Compliance Sub Category', filters = {'compliance_category':compliance_category.compliance_category, 'enabled':1}, fields = ['rate','name','compliance_category'])
	return sub_category_list

def check_exist_list(self, compliance_sub_category):
	'''method used for checking sub category in corresponding sub category'''
	exist = False
	if self.compliance_category_details:
		for item in self.compliance_category_details:
			if compliance_sub_category:
				if item.compliance_sub_category == compliance_sub_category.name and item.compliance_category == compliance_sub_category.compliance_category:
					exist = True
	return exist

@frappe.whitelist()
def set_agreement_status(agreement_id, status):
    frappe.db.set_value('Compliance Agreement', agreement_id, 'status', status)
    frappe.db.commit()
    return True

@frappe.whitelist()
def check_project_exists_or_not(compliance_categories, compliance_agreement):
	'''method used for checking project against Compliance Sub Category'''
	for category in compliance_categories:
		if frappe.db.exists('Project', {'status': 'Completed', 'compliance_agreement':compliance_agreement, 'compliance_sub_category':category.get('compliance_sub_category')}):
			return True
	return False
