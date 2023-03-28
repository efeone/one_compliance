
import frappe
import json
from frappe.model.document import Document
from frappe.model.mapper import *
from frappe import _
from frappe.utils import *

class ComplianceAgreement(Document):
	''' Method used for validate Signature '''
	def on_update_after_submit(self):
		self.sign_validation()

	def sign_validation(self):
		if self.workflow_state == 'Approved' and not self.authority_signature:
			frappe.throw('Authority Signature is required for Approval')
		if self.workflow_state == 'Customer Approved' and not self.customer_signature:
			frappe.throw('Customer Signature is required for Approval')

	def validate(self):
		self.date_validation()

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
						rate -= compliance_sub_category.rate
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
					project = frappe.new_doc('Project')
					project.project_name = self.customer_name + '-' + compliance_category.compliance_sub_category
					project.customer = self.customer
					project.compliance_agreement = self.name
					project.compliance_sub_category = compliance_category.compliance_sub_category
					project.save()
					frappe.msgprint('Project Created', alert = 1)
					project_template_doc = frappe.get_doc('Project Template', project_template)
					for task in project_template_doc.tasks:
						''' Method to create task against created project from the Project Template '''
						if not frappe.db.exists('Task',{'project':project.name, 'subject':task.subject}):
							tasks_doc = frappe.get_doc('Task',task.task)
							task_doc = frappe.new_doc('Task')
							task_doc.compliance_sub_category = compliance_category.compliance_sub_category
							task_doc.subject = task.subject
							task_doc.project = project.name
							task_doc.type = 'ToDo'
							if tasks_doc.expected_time:
								task_doc.expected_time = tasks_doc.expected_time
							task_doc.save(ignore_permissions=True)
					return True
				else :
					frappe.throw(
					title = _('ALERT !!'),
					msg = _('Project Template does not exist'))
@frappe.whitelist()
def assign_tasks(source_name, target_doc = None):
	def set_missing_values(source, target):
		for categories in source.compliance_category:
			target.append('category', {
			'compliance_category' : categories.compliance_category
			})
		for task in source.compliance_category_details:
			task_doc = get_task_from_project(task.compliance_sub_category, source.customer_name)
			for tasks in task_doc:
				target.append('task_details', {
					'sub_category' : task.compliance_sub_category,
					'task':tasks.name
				})
	doc = get_mapped_doc(
		'Compliance Agreement',
		source_name,
		{
		'Compliance Agreement': {
		'doctype': 'Compliance Task Assignment',
		},
		}, target_doc, set_missing_values)
	doc.save()
	return doc

@frappe.whitelist()
def get_task_from_project(sub_category, customer_name):
	''' Method to get tasks from project based on Sub Category '''
	task_items = []
	if frappe.db.exists ('Project', { 'customer': customer_name }):
		project_doc = frappe.db.get_list('Project', {'customer': customer_name})
		for projects in project_doc:
			task_list = frappe.db.get_list('Task', filters={'project': projects.name}, fields = ['compliance_sub_category','name'])
			for tasks in task_list:
				if tasks.compliance_sub_category == sub_category:
					task_items.append(tasks)
	return task_items

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
    ''' checking if item allready exist in child table '''
    exist = False
    try:
        if target.items:
            for item in target.items:
                if compliance_category:
                    if item.item_name == compliance_category:
                        exist = True
    except:
        exist = False
    return exist

def calculate_rate(compliance_category_details, compliance_category):
	rate = 0
	for category in compliance_category_details:
		if category.compliance_category == compliance_category:
			rate += category.rate
	return rate

@frappe.whitelist()
def set_value_in_status():
	'''Method used for set value to status field '''
	agreements = frappe.db.get_all('Compliance Agreement', filters = {'status': 'Active', 'docstatus': ['!=', 2]})
	if agreements:
		for agreement in agreements:
			valid_upto = frappe.db.get_value('Compliance Agreement', agreement.name, 'valid_upto')
			if valid_upto:
				today = getdate(frappe.utils.today())
				if today <= getdate(valid_upto) :
					frappe.db.set_value('Compliance Agreement',  agreement.name, 'status', 'Active')
				else:
					frappe.db.set_value('Compliance Agreement',  agreement.name, 'status', 'In-Active')

def get_compliance_sub_category_list(compliance_category):
	sub_category_list = frappe.db.get_list('Compliance Sub Category', filters = {'compliance_category':compliance_category.compliance_category}, fields = ['rate','name','compliance_category'])
	return sub_category_list

def check_exist_list(self, compliance_sub_category):
	exist = False
	try:
		if self.compliance_category_details:
			for item in self.compliance_category_details:
				if compliance_sub_category:
					if item.compliance_sub_category == compliance_sub_category.name and item.compliance_category == compliance_sub_category.compliance_category:
						exist = True
	except:
		exist = False
	return exist
