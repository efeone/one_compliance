import frappe
import json
from frappe.model.document import Document
from frappe.model.mapper import *
from frappe import _
from frappe.utils import *
from one_compliance.one_compliance.utils import *
from datetime import datetime, timedelta
from frappe import enqueue

class ComplianceAgreement(Document):
	''' Method used for validate Signature '''
	def on_update_after_submit(self):
		set_compliance_dates(self)
		self.sign_validation()
		self.create_project_if_not_exists()

	def before_insert(self):
		# from hrms.hr.doctype.shift_type.shift_type import process_auto_attendance_for_all_shifts

		self.status = "Open"

	def create_project_if_not_exists(self):
		if self.status == 'Active' and self.workflow_state=='Customer Approved':
			if self.compliance_category_details:
				for compliance_category in self.compliance_category_details:
					if not check_project_exists_or_not(compliance_category.compliance_sub_category, self.name):
						if compliance_category.compliance_date and getdate(compliance_category.compliance_date) == getdate(today()):
							enqueue(create_project_against_sub_category, queue = 'long', now  = False, compliance_agreement = self.name, compliance_sub_category = compliance_category.compliance_sub_category, compliance_category_details_id = compliance_category.name, compliance_date = compliance_category.compliance_date)

	def sign_validation(self):
		if self.workflow_state == 'Approved' and not self.authority_signature:
			frappe.throw('Authority Signature is required for Approval')
		if self.workflow_state == 'Customer Approved' and not self.customer_signature:
			frappe.throw('Customer Signature is required for Customer Approval')

	def validate(self):
		self.validate_agreement_dates()
		self.validate_date_range()
		self.change_agreement_status()

	def on_trash(self):
		delete_project_along_with_compliance_agreement = frappe.db.get_single_value('Compliance Settings', 'delete_project_along_with_compliance_agreement')
		if delete_project_along_with_compliance_agreement:
			delete_project_and_task(self.name)
		else:
			if frappe.db.exists('Project',{'compliance_agreement': self.name}):
				project_list = frappe.db.get_all('Project', filters={'compliance_agreement': self.name})
				for project in project_list:
					project_doc = frappe.get_doc('Project',project.name)
					project_doc.set('compliance_agreement', None)
					project_doc.save()


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

	def validate_date_range(self):
		existing_agreements = frappe.get_all(
			"Compliance Agreement",
			filters={
				"customer": self.customer,
				"workflow_state": "Customer Approved",
			},
			fields=["name"],
		)
		for compliance_agreement in existing_agreements:
			agreement = frappe.get_doc("Compliance Agreement", compliance_agreement.name)
			# Get compliance category details of the current agreement
			agreement_categories = [d.sub_category_name for d in agreement.compliance_category_details]
			agreement_valid_from = getdate(agreement.valid_from)
			agreement_valid_upto = getdate(agreement.valid_upto)

			# Get compliance category details of the current instance
			for d in self.compliance_category_details:
				instance_categories = d.sub_category_name
				instance_valid_from = getdate(self.valid_from)
				instance_valid_upto = getdate(self.valid_upto)

				# Check if all categories in the agreement exist in the instance and vice versa
				if instance_categories in set(agreement_categories):
					if self.has_long_term_validity:
						if agreement.has_long_term_validity:
							if instance_valid_from >= agreement_valid_from:
								frappe.throw("The compliance subcategories chosen in the agreement '{}' already exist in the Agreement '{}' within the date range.".format(instance_categories, agreement))
						else:
							if instance_valid_from < agreement_valid_upto:
								frappe.throw("The compliance subcategories chosen in the agreement '{}' already exist in the Agreement '{}' within the date range.".format(instance_categories, agreement))
					else:
						if agreement.has_long_term_validity:
							if agreement_valid_from and instance_valid_from >= instance_valid_from:
								frappe.throw("The compliance subcategories chosen in the agreement '{}' already exist in the Agreement '{}' within the date range.".format(instance_categories, agreement))
						elif agreement_valid_upto and instance_valid_upto:
							if instance_valid_from >= agreement_valid_from and instance_valid_upto <= agreement_valid_upto:
								frappe.throw("The compliance subcategories chosen in the agreement '{}' already exist in the Agreement '{}' within the date range.".format(instance_categories, agreement))

	def make_sales_invoice(self):

		projectlist = frappe.get_all(
			"Project",
			filters={
				"compliance_agreement": self.name,
				"status": "Completed",
				"expected_start_date": (">=", self.invoice_date),
				"expected_end_date": ("<", self.next_invoice_date),
			},
			fields=["name", "customer", "compliance_sub_category", "company"]
		)
		print(projectlist)

		if(projectlist and len(projectlist) > 0):
			sales_invoice = frappe.new_doc("Sales Invoice")
			for project in projectlist:
				sales_invoice.customer = project.customer
				sales_invoice.posting_date = frappe.utils.today()
				income_account = frappe.db.get_value('Company', project.company, 'default_income_account')
				payment_terms = frappe.db.get_value('Compliance Agreement', project.compliance_agreement, 'default_payment_terms_template')
				rate = get_rate_from_compliance_agreement(project.compliance_agreement, project.compliance_sub_category)
				sub_category_doc = frappe.get_doc("Compliance Sub Category", project.compliance_sub_category)
				rate = rate if rate else sub_category_doc.rate

				if payment_terms:
					sales_invoice.default_payment_terms_template = payment_terms

				sales_invoice.append('items', {
					'item_code': sub_category_doc.item_code,
					'item_name': sub_category_doc.sub_category,
					'rate': rate,
					'qty': 1,
					'income_account': income_account,
					'description': sub_category_doc.name
				})

			sales_invoice.insert()
			frappe.db.set_value(self.doctype, self.name, "invoice_date", self.next_invoice_date)
			next_invoice_date = calculate_next_invoice_date(self.next_invoice_date, self.invoice_generation, self.valid_upto)
			frappe.db.set_value(self.doctype, self.name, "next_invoice_date", next_invoice_date)
			frappe.db.commit()

def calculate_next_invoice_date(current_invoice_date, invoice_generation, valid_upto):
	if invoice_generation == 'Monthly':
		next_invoice_date = frappe.utils.add_months(current_invoice_date, 1)
	elif invoice_generation == 'Quarterly':
		next_invoice_date = frappe.utils.add_months(current_invoice_date, 3)
	elif invoice_generation == 'Half Yearly':
		next_invoice_date = frappe.utils.add_months(current_invoice_date, 6)
	elif invoice_generation == 'Yearly':
		next_invoice_date = frappe.utils.add_years(current_invoice_date, 1)
	else:
		next_invoice_date = current_invoice_date

	if valid_upto and next_invoice_date <= valid_upto:
		return next_invoice_date
	elif valid_upto and next_invoice_date > valid_upto:
		return valid_upto
	else:
		return next_invoice_date

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
			frappe.db.commit()

@frappe.whitelist()
def get_compliance_sub_category_list(compliance_category):
	'''method used for list sub category'''
	sub_category_list = frappe.db.get_list('Compliance Sub Category', filters = {'compliance_category':compliance_category, 'enabled':1}, fields = ['rate','name','compliance_category', 'sub_category'])
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
def create_project_against_sub_category(compliance_agreement, compliance_sub_category, compliance_category_details_id, compliance_date):
	'''
		Method to create Project against selected Sub Category
	'''
	self = frappe.get_doc('Compliance Agreement', compliance_agreement)
	project_template  = frappe.db.get_value('Compliance Sub Category', compliance_sub_category, 'project_template')
	project_template_doc = frappe.get_doc('Project Template', project_template)
	sub_category_doc = frappe.get_doc('Compliance Sub Category',compliance_sub_category)
	head_of_department = frappe.db.get_value('Employee', {'employee':sub_category_doc.head_of_department}, 'user_id')
	if project_template:
		# compliance_date = False
		if compliance_category_details_id:
			if frappe.db.get_value('Compliance Category Details', compliance_category_details_id, 'compliance_date'):
				compliance_date = frappe.db.get_value('Compliance Category Details', compliance_category_details_id, 'compliance_date')
				update_compliance_dates(compliance_category_details_id)
		if not compliance_date:
			compliance_date = getdate(frappe.utils.today())
		repeat_on = frappe.db.get_value('Compliance Sub Category', compliance_sub_category, 'repeat_on')
		project_based_on_prior_phase = frappe.db.get_value('Compliance Sub Category', compliance_sub_category, 'project_based_on_prior_phase')
		previous_month_date = add_months(getdate(compliance_date), -1)
		naming_year = getdate(previous_month_date).year if project_based_on_prior_phase else getdate(compliance_date).year
		naming_month = getdate(previous_month_date).strftime("%B") if project_based_on_prior_phase else getdate(compliance_date).strftime("%B")
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
			naming = str(naming_year) + ' ' + naming_quarter
		else:
			naming = str(naming_year) + ' ' + naming_month
		project = frappe.new_doc('Project')
		project.company = self.company
		project.cost_center = frappe.get_cached_value("Company", self.company, "cost_center")
		add_compliance_category_in_project_name = frappe.db.get_single_value('Compliance Settings', 'add_compliance_category_in_project_name')
		if add_compliance_category_in_project_name:
			project.project_name = self.customer_name + '-' + compliance_sub_category + '-' + str(naming)
		else:
			project.project_name = self.customer_name + '-' + frappe.db.get_value('Compliance Sub Category', compliance_sub_category, 'sub_category') + '-' + str(naming)
		# project.project_template = project_template
		project.customer = self.customer
		project.compliance_agreement = self.name
		project.compliance_sub_category = compliance_sub_category
		project.expected_start_date = compliance_date
		project.custom_project_service = compliance_sub_category + '-' + str(naming)
		project.notes = compliance_sub_category + '-' + str(naming)
		project.category_type = frappe.db.get_value('Compliance Sub Category', compliance_sub_category, 'category_type')
		project.department = frappe.db.get_value('Compliance Sub Category', compliance_sub_category, 'department')
		if project_template_doc.custom_project_duration:
			project.expected_end_date = add_days(compliance_date, project_template_doc.custom_project_duration)
		project.save(ignore_permissions=True)
		if project.compliance_sub_category:
			if sub_category_doc and sub_category_doc.head_of_department:
				# user = sub_category_doc.head_of_department
				todo = frappe.new_doc('ToDo')
				todo.status = 'Open'
				if frappe.db.exists('Employee', sub_category_doc.head_of_department):
					employee_user_id = frappe.db.get_value('Employee', sub_category_doc.head_of_department, 'user_id')
					if employee_user_id:
						todo.allocated_to = employee_user_id
				todo.description = "project  Assign to" + sub_category_doc.head_of_department
				todo.reference_type = 'Project'
				todo.reference_name = project.name
				todo.assigned_by = frappe.session.user
				todo.save(ignore_permissions=True)
				if todo:
					frappe.msgprint(("Project is assigned to {0}".format(sub_category_doc.head_of_department)),alert = 1)
		frappe.db.commit()
		frappe.msgprint('Project Created for {0}.'.format(compliance_sub_category), alert = 1)
		for template_task in project_template_doc.tasks:
			''' Method to create task against created project from the Project Template '''
			template_task_doc = frappe.get_doc('Task', template_task.task)
			user_name = frappe.get_cached_value("User", frappe.session.user, "full_name")
			task_doc = frappe.new_doc('Task')
			task_doc.compliance_sub_category = compliance_sub_category
			task_doc.subject = template_task.subject
			task_doc.project = project.name
			task_doc.company = project.company
			task_doc.project_name = project.project_name
			task_doc.category_type = project.category_type
			task_doc.exp_start_date = compliance_date
			task_doc.custom_serial_number = template_task.idx
			if template_task_doc.expected_time:
				task_doc.expected_time = template_task_doc.expected_time
			if template_task.custom_task_duration:
				task_doc.duration = template_task.custom_task_duration
				task_doc.exp_end_date = add_days(compliance_date, template_task.custom_task_duration)
			task_doc.save(ignore_permissions=True)
			if template_task.type and template_task.employee_or_group:
				frappe.db.set_value('Task', task_doc.name, 'assigned_to', template_task.employee_or_group)
				if template_task.type == "Employee":
					employee = frappe.db.get_value('Employee', template_task.employee_or_group, 'user_id')
					if employee:
						create_todo('Task', task_doc.name, employee, employee, 'Task {0} Assigned Successfully'.format(task_doc.name))
				if template_task.type == "Employee Group":
					employee_group = frappe.get_doc('Employee Group', template_task.employee_or_group)
					if employee_group.employee_list:
						for employee in employee_group.employee_list:
							create_todo('Task', task_doc.name, employee.user_id, employee.user_id, 'Task {0} Assigned Successfully'.format(task_doc.name))

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
			if self.invoice_based_on == 'Consolidated' and self.next_invoice_date == date.today():
				print(self.name)
				self.make_sales_invoice()
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

@frappe.whitelist()
def get_rate_from_compliance_agreement(compliance_agreement, compliance_sub_category):
	rate_result = frappe.db.sql(
		"""
		select rate
		from `tabCompliance Category Details`
		where parent=%s and compliance_sub_category=%s""",
		(compliance_agreement, compliance_sub_category),
		as_dict=1,
		)
	if rate_result:
		return rate_result[0].rate
