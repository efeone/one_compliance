import frappe
import json
from frappe.model.document import Document
from frappe.model.mapper import *
from frappe import _
from frappe.utils import *
from one_compliance.one_compliance.utils import *
from datetime import datetime, timedelta

class ComplianceAgreement(Document):
	''' Method used for validate Signature '''
	def on_update_after_submit(self):
		set_compliance_dates(self)
		self.sign_validation()
		self.create_project_if_not_exists()

	def before_insert(self):
		self.status = "Open"

	def create_project_if_not_exists(self):
		if self.status == 'Active' and self.workflow_state=='Customer Approved':
			if self.compliance_category_details:
				for compliance_category in self.compliance_category_details:
					if not check_project_exists_or_not(compliance_category.compliance_sub_category, self.name):
						if compliance_category.compliance_date and getdate(compliance_category.compliance_date) == getdate(today()):
							create_project_against_sub_category(self.name, compliance_category.compliance_sub_category, compliance_category.name)

	def sign_validation(self):
		if self.workflow_state == 'Approved' and not self.authority_signature:
			frappe.throw('Authority Signature is required for Approval')
		if self.workflow_state == 'Customer Approved' and not self.customer_signature:
			frappe.throw('Customer Signature is required for Customer Approval')

	def validate(self):
		self.validate_agreement_dates()
		self.change_agreement_status()

	def on_trash(self):
		delete_project_and_task(self.name)


	def validate_agreement_dates(self):
		if self.posting_date:
			if getdate(self.posting_date) > getdate(today()):
				frappe.throw('Posting Date cannot be a future date.')
		if self.valid_from and self.valid_upto and not self.has_long_term_validity:
			if getdate(self.valid_from) > getdate(self.valid_upto):
				frappe.throw('From Date cannot be greater than Valid Upto Date')

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
				frappe.db.set_value('Compliance Agreement', agreement.name, 'status', 'Open')
			elif ((self.valid_upto and today > getdate(self.valid_upto)) and not self.has_long_term_validity):
				frappe.db.set_value('Compliance Agreement', agreement.name, 'status', 'Expired')
			else:
				frappe.db.set_value('Compliance Agreement', agreement.name, 'status', 'Active')
				frappe.db.commit()
				self.create_project_if_not_exists()
			frappe.db.commit()

@frappe.whitelist()
def get_compliance_sub_category_list(compliance_category):
	'''method used for list sub category'''
	sub_category_list = frappe.db.get_list('Compliance Sub Category', filters = {'compliance_category':compliance_category, 'enabled':1}, fields = ['rate','name','compliance_category'])
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
	if status == 'Cancelled':
		frappe.db.set_value('Compliance Agreement', agreement_id, 'workflow_state', status)
		frappe.db.set_value('Compliance Agreement', agreement_id, 'docstatus', 2)
	frappe.db.set_value('Compliance Agreement', agreement_id, 'status', status)
	frappe.db.commit()
	return True

@frappe.whitelist()
def delete_project_and_task(agreement_id):
	if frappe.db.exists('Project',{'compliance_agreement': agreement_id}):
		project_list = frappe.db.get_all('Project', filters={'compliance_agreement': agreement_id})
		for project in project_list:
			task_list = frappe.db.get_all('Task', filters={'project': project.name})
			for task in task_list:
				frappe.db.delete('Task', task.name)
			frappe.db.delete('Project', project.name)
		frappe.msgprint('Agreement Deleted {0}.'.format(agreement_id), alert = 1)

@frappe.whitelist()
def check_project_exists_or_not(compliance_sub_category, compliance_agreement):
	'''
		Method used for checking project against Compliance Sub Category
	'''
	if frappe.db.exists('Project', {'status': 'Open', 'compliance_agreement':compliance_agreement, 'compliance_sub_category': compliance_sub_category }):
		return True
	return False

@frappe.whitelist()
def create_project_against_sub_category(compliance_agreement, compliance_sub_category, compliance_category_details_id=None):
	'''
		Method to create Project against selected Sub Category
	'''
	self = frappe.get_doc('Compliance Agreement', compliance_agreement)
	project_template  = frappe.db.get_value('Compliance Sub Category', compliance_sub_category, 'project_template')
	if project_template:
		compliance_date = False
		if compliance_category_details_id:
			if frappe.db.get_value('Compliance Category Details', compliance_category_details_id, 'compliance_date'):
				compliance_date = frappe.db.get_value('Compliance Category Details', compliance_category_details_id, 'compliance_date')
				update_compliance_dates(compliance_category_details_id)
		if not compliance_date:
			compliance_date = getdate(frappe.utils.today())
		repeat_on = frappe.db.get_value('Compliance Sub Category', compliance_sub_category, 'repeat_on')
		previous_month_date = add_months(getdate(today()), -1)
		naming_year = getdate(today()).year
		naming_month = getdate(previous_month_date).strftime("%B")
		if naming_month in ['January', 'February', 'March']:
			naming_quarter = 'Quarter 1'
		elif naming_month in ['April', 'May', 'June']:
			naming_quarter = 'Quarter 2'
		elif naming_month in ['July', 'August', 'September']:
			naming_quarter = 'Quarter 3'
		else:
			naming_quarter = 'Quarter 4'
		if repeat_on == "Yearly":
			naming = naming_year
		elif repeat_on == "Quarterly":
			naming = naming_year + ' ' + naming_quarter
		else:
			naming = naming_year + ' ' + naming_month
		project = frappe.new_doc('Project')
		project.project_name = self.customer_name + '-' + compliance_sub_category + '-' + str(naming)
		project.customer = self.customer
		project.compliance_agreement = self.name
		project.compliance_sub_category = compliance_sub_category
		project.expected_start_date = compliance_date
		project.category_type = frappe.db.get_value('Compliance Sub Category', compliance_sub_category, 'category_type')
		project.save(ignore_permissions=True)
		frappe.db.commit()
		frappe.msgprint('Project Created for {0}.'.format(compliance_sub_category), alert = 1)
		project_template_doc = frappe.get_doc('Project Template', project_template)
		for template_task in project_template_doc.tasks:
			''' Method to create task against created project from the Project Template '''
			template_task_doc = frappe.get_doc('Task', template_task.task)
			user_name = frappe.get_cached_value("User", frappe.session.user, "full_name")
			task_doc = frappe.new_doc('Task')
			task_doc.compliance_sub_category = compliance_sub_category
			task_doc.subject = template_task.subject
			task_doc.project = project.name
			task_doc.project_name = project.project_name
			task_doc.exp_start_date = compliance_date
			if template_task_doc.expected_time:
				task_doc.expected_time = template_task_doc.expected_time
			if template_task_doc.duration:
				task_doc.duration = template_task_doc.duration
			task_doc.save(ignore_permissions=True)
			if template_task.type and template_task.employee_or_group:
				frappe.db.set_value('Task', task_doc.name, 'assigned_to', template_task.employee_or_group)
				if template_task.type == "Employee":
					employee = frappe.db.get_value('Employee', template_task.employee_or_group, 'user_id')
					if employee:
						create_todo('Task', task_doc.name, employee, employee, 'Task {0} Assigned Successfully'.format(task_doc.name))
						create_notification_log('{0} Assigned a New Task {1} to You'.format(user_name, task_doc.name),'Mention', employee, 'Task {0} Assigned Successfully'.format(task_doc.name), task_doc.doctype, task_doc.name)
				if template_task.type == "Employee Group":
					employee_group = frappe.get_doc('Employee Group', template_task.employee_or_group)
					if employee_group.employee_list:
						for employee in employee_group.employee_list:
							create_todo('Task', task_doc.name, employee.user_id, employee.user_id, 'Task {0} Assigned Successfully'.format(task_doc.name))
							create_notification_log('{0} Assigned a New Task {1} to you'.format(user_name, task_doc.name),'Mention', employee.user_id, 'Task {0} Assigned Successfully'.format(task_doc.name), task_doc.doctype, task_doc.name)

		frappe.db.commit()
	else:
		frappe.throw( title = _('ALERT !!'), msg = _('Project Template does not exist for {0}'.format(compliance_sub_category)))


@frappe.whitelist()
def set_compliance_dates(doc):
	'''
		Method to set Date in each Compliance Sub Category for Task Assignment
	'''
	months_dict = { 'January': 1, 'February': 2, 'March': 3, 'April': 4, 'May': 5, 'June': 6, 'July': 7, 'August': 8, 'September': 9, 'October': 10, 'November': 11, 'December': 12 }
	if doc.compliance_category_details:
		for compliance_category in doc.compliance_category_details:
			if compliance_category.compliance_sub_category:
				if not compliance_category.compliance_date:
					sub_category_doc = frappe.get_doc('Compliance Sub Category', compliance_category.compliance_sub_category)
					if sub_category_doc.allow_repeat:
						current_date = getdate(today())
						day = sub_category_doc.day
						if sub_category_doc.repeat_on == "Monthly":
							new_date = datetime(current_date.year, current_date.month, day).strftime('%Y-%m-%d')
							compliance_date = getdate(new_date)
							if compliance_date < current_date:
								compliance_date = add_months(compliance_date, 1)
							next_compliance_date = add_months(compliance_date, 1)
						else:
							if sub_category_doc.repeat_on == "Quarterly":
								month_flag = 3
							elif sub_category_doc.repeat_on == "Half Yearly":
								month_flag = 6
							elif sub_category_doc.repeat_on == "Yearly":
								month_flag = 12
							month = months_dict[sub_category_doc.month]
							new_date = datetime(current_date.year, month, day).strftime('%Y-%m-%d')
							compliance_date = getdate(new_date)
							if compliance_date < current_date:
								compliance_date = add_months(compliance_date, month_flag)
							next_compliance_date = add_months(compliance_date, month_flag)
						compliance_category.compliance_date = compliance_date
						compliance_category.next_compliance_date = next_compliance_date
						frappe.db.set_value(compliance_category.doctype, compliance_category.name, 'compliance_date', compliance_date)
						frappe.db.set_value(compliance_category.doctype, compliance_category.name, 'next_compliance_date', next_compliance_date)
						frappe.db.commit()
					else:
						compliance_category.compliance_date = doc.valid_from
						frappe.db.commit()

@frappe.whitelist()
def compliance_agreement_daily_scheduler():
	agreements = frappe.db.get_all('Compliance Agreement', filters = {'status': 'Active'})
	if agreements:
		for agreement in agreements:
			self = frappe.get_doc('Compliance Agreement', agreement.name)
			self.create_project_if_not_exists()
		frappe.db.commit()

@frappe.whitelist()
def update_compliance_dates(compliance_category_details_id):
	compliance_sub_category, compliance_date, next_compliance_date = frappe.db.get_value('Compliance Category Details', compliance_category_details_id, ['compliance_sub_category', 'compliance_date', 'next_compliance_date'])
	repeat_on = frappe.db.get_value('Compliance Sub Category', compliance_sub_category, 'repeat_on')
	month_flag = 0
	if repeat_on:
		if repeat_on == "Quarterly":
			month_flag = 3
		elif repeat_on == "Half Yearly":
			month_flag = 6
		elif repeat_on == "Yearly":
			month_flag = 12
		elif repeat_on == "Monthly":
			month_flag = 1
		if month_flag:
			frappe.db.set_value('Compliance Category Details', compliance_category_details_id, 'compliance_date', next_compliance_date)
			frappe.db.set_value('Compliance Category Details', compliance_category_details_id, 'next_compliance_date', add_months(next_compliance_date, month_flag))
			frappe.db.commit()

	else:
		frappe.db.set_value('Compliance Category Details', compliance_category_details_id, 'compliance_date', getdate(today()))
		frappe.db.commit()
