import frappe
import json
from frappe.model.document import Document
from frappe.model.mapper import *
from frappe import _
from frappe.utils import *
from one_compliance.one_compliance.utils import *
from datetime import datetime, timedelta
from frappe import enqueue
from frappe.utils import getdate, today, nowdate, add_months, add_days
from one_compliance.one_compliance.utils import create_todo
from datetime import datetime

class ComplianceAgreement(Document):
	''' Method used for validate Signature '''
	def on_update_after_submit(self):
		self.sign_validation()
	def before_insert(self):
		# from hrms.hr.doctype.shift_type.shift_type import process_auto_attendance_for_all_shifts

		self.status = "Open"

	def sign_validation(self):
		if self.workflow_state == 'Approved' and not self.authority_signature:
			frappe.throw('Authority Signature is required for Approval')
		if self.workflow_state == 'Customer Approved' and not self.customer_signature:
			frappe.throw('Customer Signature is required for Customer Approval')

	def validate(self):
		self.validate_agreement_dates()
		self.validate_date_range()

	def on_submit(self):
		self.update_compliance_agreement_status()	

	def on_update_after_submit(self):
		self.update_compliance_agreement_status()

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

	def update_compliance_agreement_status(self):
		"""
		Update Compliance Agreement status based on:
		- Customer freeze/disable state (highest priority)
		- Workflow state
		- Validity period (valid_from and valid_upto)
		- Cancellation state (docstatus)
		"""

		today = getdate(frappe.utils.today())

		if self.customer:
			customer_status = frappe.db.get_value(
				"Customer", self.customer, ["is_frozen", "disabled"], as_dict=True
			)
			if customer_status and (customer_status.is_frozen or customer_status.disabled):
				self.db_set("status", "Hold")
				return

		if self.docstatus == 2:
			self.db_set("status", "Cancelled")
			return

		if self.valid_from and today < getdate(self.valid_from):
			self.db_set("status", "Open")
			return

		if self.valid_upto and today > getdate(self.valid_upto) and not self.has_long_term_validity:
			self.db_set("status", "Expired")
			return

		if self.workflow_state in ["Customer Approval Waiting", "Pending", "Draft"]:
			self.db_set("status", "Draft")
		elif self.workflow_state in ["Customer Approved"]:
			self.db_set("status", "Active")
		else:
			self.db_set("status", "Open")

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

@frappe.whitelist()
def create_sales_orders_from_compliance_agreements(posting_date=today()):
	"""
	Create Sales Orders and/or Projects automatically from active Compliance Agreements.
	Sales Order is created only if the Compliance Sub Category is billable.
	Project is created in both cases.
	"""
	current_date = getdate(posting_date)

	MONTH_MAP = {
		"January": 1, "February": 2, "March": 3, "April": 4,
		"May": 5, "June": 6, "July": 7, "August": 8,
		"September": 9, "October": 10, "November": 11, "December": 12
	}

	agreements = frappe.db.sql("""
		SELECT 
			ca.name, ca.customer, ca.company, ca.valid_from, ca.valid_upto, 
			ca.default_payment_terms_template
		FROM `tabCompliance Agreement` ca
		INNER JOIN `tabCustomer` c ON ca.customer = c.name
		WHERE 
			ca.status = 'Active'
			AND IFNULL(c.is_frozen, 0) = 0
			AND IFNULL(c.disabled, 0) = 0
	""", as_dict=True)

	if not agreements:
		return

	for agreement in agreements:
		valid_from = getdate(agreement.valid_from)
		valid_upto = getdate(agreement.valid_upto) if agreement.valid_upto else None

		if current_date < valid_from:
			continue

		category_details = frappe.get_all(
			"Compliance Category Details",
			filters={"parent": agreement.name},
			fields=["name", "compliance_sub_category", "rate"]
		)

		for detail in category_details:
			sub_cat = detail.compliance_sub_category
			if not sub_cat:
				continue

			sub_category = frappe.db.get_value(
				"Compliance Sub Category",
				sub_cat,
				[
					"allow_repeat", "repeat_on", "day", "month", "item_code",
					"project_template", "head_of_department", "category_type",
					"department", "compliance_category", "is_billable"
				],
				as_dict=True
			)
			if not sub_category:
				continue

			allow_repeat = sub_category.allow_repeat
			repeat_on = sub_category.repeat_on
			repeat_day = sub_category.day
			repeat_month = sub_category.month
			item_code = sub_category.item_code
			project_template = sub_category.project_template
			is_billable = sub_category.is_billable

			if valid_upto and current_date > valid_upto:
				continue

			should_create = False
			if not allow_repeat:
				if current_date == valid_from:
					should_create = True
			else:
				month_number = MONTH_MAP.get(repeat_month) if repeat_month else None
				if repeat_on == "Monthly" and repeat_day and current_date.day == int(repeat_day):
					should_create = True
				elif repeat_on in ["Quarterly", "Half Yearly", "Yearly"] and month_number and repeat_day:
					if current_date.month == month_number and current_date.day == int(repeat_day):
						should_create = True

			if not should_create:
				continue

			project = None
			if project_template:
				project = create_project_from_template(
					None,
					project_template,
					agreement.customer,
					agreement.company,
					sub_cat,
					detail.name,
					agreement.name,
					sub_category.compliance_category,
					posting_date
				)

			# === Calculate compliance dates (common for both cases) ===
			base_date = getdate(nowdate())
			compliance_date = None
			next_compliance_date = None

			if allow_repeat:
				if repeat_on == "Monthly":
					compliance_date = add_months(base_date, 1)
					next_compliance_date = add_months(compliance_date, 1)
				elif repeat_on == "Quarterly":
					compliance_date = add_months(base_date, 3)
					next_compliance_date = add_months(compliance_date, 3)
				elif repeat_on == "Half Yearly":
					compliance_date = add_months(base_date, 6)
					next_compliance_date = add_months(compliance_date, 6)
				elif repeat_on == "Yearly":
					compliance_date = add_months(base_date, 12)
					next_compliance_date = add_months(compliance_date, 12)
			else:
				compliance_date = base_date
				next_compliance_date = None

			# === Create Sales Order only if billable ===
			if is_billable:
				if not frappe.db.exists("Sales Order", {
					"compliance_agreement": agreement.name,
					"compliance_sub_category": sub_cat,
					"transaction_date": nowdate()
				}):
					try:
						item_name = frappe.db.get_value("Item", item_code, "item_name") if item_code else None
						if not item_code:
							continue

						so = frappe.new_doc("Sales Order")
						so.customer = agreement.customer
						so.company = agreement.company
						so.compliance_agreement = agreement.name
						so.compliance_sub_category = sub_cat
						so.transaction_date = nowdate()
						so.delivery_date = nowdate()
						if agreement.default_payment_terms_template:
							so.payment_terms_template = agreement.default_payment_terms_template

						so.append("items", {
							"item_code": item_code,
							"item_name": item_name,
							"qty": 1,
							"rate": detail.rate or 0,
						})

						so.insert(ignore_permissions=True)
						so.submit()

						if project:
							project.db_set("sales_order", so.name)
							so.db_set("project", project.name)

						frappe.db.set_value(
							"Compliance Category Details",
							detail.name,
							{
								"compliance_date": compliance_date,
								"next_compliance_date": next_compliance_date
							}
						)

					except Exception:
						frappe.log_error(frappe.get_traceback(), f"SO Creation Failed - {agreement.name}")
			else:
				frappe.db.set_value(
					"Compliance Category Details",
					detail.name,
					{
						"compliance_date": compliance_date,
						"next_compliance_date": next_compliance_date
					}
				)

def create_project_from_template(sales_order, project_template, customer, company,
								 compliance_sub_category, compliance_category_details_id,
								 compliance_agreement, compliance_category, compliance_date=today()):
	"""
	Create Project and Tasks from Project Template for Compliance Sub Category.
	"""
	try:
		compliance_date = getdate(compliance_date)
		project_template_doc = frappe.get_doc("Project Template", project_template)
		sub_category_doc = frappe.get_doc('Compliance Sub Category', compliance_sub_category)
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
		project.company = company
		# project.cost_center = frappe.get_cached_value("Company", company, "cost_center")

		add_compliance_category_in_project_name = frappe.db.get_single_value(
			'Compliance Settings', 'add_compliance_category_in_project_name'
		)

		if add_compliance_category_in_project_name:
			project.project_name = f"{customer}-{compliance_sub_category}-{naming}"
		else:
			sub_category_name = frappe.db.get_value(
				'Compliance Sub Category',
				compliance_sub_category,
				'sub_category'
			)
			project.project_name = f"{customer}-{sub_category_name}-{naming}"

		project.customer = customer
		project.compliance_sub_category = compliance_sub_category
		project.expected_start_date = compliance_date
		project.custom_project_service = f"{compliance_sub_category}-{naming}"
		project.notes = f"{compliance_sub_category}-{naming}"
		project.category_type = frappe.db.get_value(
			'Compliance Sub Category', compliance_sub_category, 'category_type'
		)
		project.department = frappe.db.get_value(
			'Compliance Sub Category', compliance_sub_category, 'department'
		)
		project.sales_order = sales_order
		project.compliance_category = compliance_category
		project.compliance_agreement = compliance_agreement

		if project_template_doc.custom_project_duration:
			project.expected_end_date = add_days(compliance_date, project_template_doc.custom_project_duration)

		project.insert(ignore_permissions=True)
		project.save(ignore_permissions=True)

		# Assign ToDo to HOD
		if sub_category_doc.head_of_department:
			hod_user = frappe.db.get_value('Employee', sub_category_doc.head_of_department, 'user_id')
			if hod_user:
				create_todo("Project", project.name, hod_user, frappe.session.user,
							f"Project assigned to {sub_category_doc.head_of_department}")

		# Create Tasks from Template
		for template_task in project_template_doc.tasks:
			template_task_doc = frappe.get_doc('Task', template_task.task)
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
			if template_task.task_weightage :
				task_doc.task_weightage = template_task.task_weightage

			if template_task.custom_has_document:
				for documents in project_template_doc.custom_documents_required:
					if documents.task == template_task.task:
						for docs in documents.documents.split(', '):
							task_doc.append("custom_task_document_items", {
								"document": docs
							})

			task_doc.insert(ignore_permissions=True)

			assigned_users = []

			# Employee assignment
			if template_task.type == "Employee" and template_task.employee_or_group:
				user_id = frappe.db.get_value("Employee", template_task.employee_or_group, "user_id")
				if user_id:
					assigned_users.append(user_id)

			# Employee Group assignment
			elif template_task.type == "Employee Group" and template_task.employee_or_group:
				group = frappe.get_doc("Employee Group", template_task.employee_or_group)
				for emp in group.employee_list:
					if emp.user_id:
						assigned_users.append(emp.user_id)

			# Add HOD as notification
			hod_user = None
			if sub_category_doc.head_of_department:
				hod_user = frappe.db.get_value("Employee", sub_category_doc.head_of_department, "user_id")

			for user in assigned_users:
				create_todo("Task", task_doc.name, user, frappe.session.user,
							f"Task assigned: {task_doc.subject}")

			if hod_user and hod_user not in assigned_users:
				create_todo("Task", task_doc.name, hod_user, frappe.session.user,
							f"HOD notified for task: {task_doc.subject}")

		return project

	except Exception:
		frappe.log_error(frappe.get_traceback(), "Project Creation Failed")
		return None

def update_status_on_customer_change(doc, method):
	"""
	Trigger Compliance Agreement status update when customer is frozen/disabled or re-enabled
	"""
	agreements = frappe.get_all(
		"Compliance Agreement",
		filters={"customer": doc.name, "docstatus": ["!=", 2]},
		pluck="name"
	)

	for agreement_name in agreements:
		self = frappe.get_doc("Compliance Agreement", agreement_name)
		self.update_compliance_agreement_status()

@frappe.whitelist()
def create_sales_order_and_project_from_popup(
	compliance_agreement,
	compliance_sub_category,
	compliance_date,
	compliance_category_details_id
):
	"""
	Create Sales Orders from compliance agreement popup.
	"""
	compliance_date = getdate(compliance_date)
	agreement = frappe.get_doc("Compliance Agreement", compliance_agreement)

	subcat = frappe.db.get_value(
		"Compliance Sub Category",
		compliance_sub_category,
		[
			"item_code",
			"is_billable",
			"project_template",
			"compliance_category"
		],
		as_dict=True
	)

	if not subcat:
		frappe.throw("Compliance Sub Category not found")

	if not subcat.item_code:
		frappe.throw("Item Code missing in Compliance Sub Category")

	rate = frappe.db.get_value(
		"Compliance Category Details",
		compliance_category_details_id,
		"rate"
	) or 0

	project = None
	if subcat.project_template:
		project = create_project_from_template(
			sales_order=None,                      
			project_template=subcat.project_template,
			customer=agreement.customer,
			company=agreement.company,
			compliance_sub_category=compliance_sub_category,
			compliance_category_details_id=compliance_category_details_id,
			compliance_agreement=compliance_agreement,
			compliance_category=subcat.compliance_category,
			compliance_date=compliance_date
		)
	if subcat.is_billable:

		exists = frappe.db.exists("Sales Order", {
			"compliance_agreement": compliance_agreement,
			"compliance_sub_category": compliance_sub_category,
			"transaction_date": compliance_date
		})

		if exists:
			return "Sales Order already exists for this date"

		so = frappe.new_doc("Sales Order")
		so.customer = agreement.customer
		so.company = agreement.company
		so.compliance_agreement = compliance_agreement
		so.compliance_sub_category = compliance_sub_category
		so.transaction_date = compliance_date
		so.delivery_date = compliance_date

		if agreement.default_payment_terms_template:
			so.payment_terms_template = agreement.default_payment_terms_template

		item_name = frappe.db.get_value("Item", subcat.item_code, "item_name")

		so.append("items", {
			"item_code": subcat.item_code,
			"item_name": item_name,
			"qty": 1,
			"rate": rate,
			"description": f"Auto-created from Compliance Agreement {compliance_agreement}"
		})

		so.insert(ignore_permissions=True)
		so.submit()
		if project:
			project.db_set("sales_order", so.name)
			so.db_set("project", project.name)

		frappe.db.set_value(
			"Compliance Category Details",
			compliance_category_details_id,
			{
				"compliance_date": compliance_date,
				"next_compliance_date": None
			}
		)

		return f"Sales Order Created: {so.name} | Project Created: {project.name if project else 'No Template'}"

	frappe.db.set_value(
		"Compliance Category Details",
		compliance_category_details_id,
		{
			"compliance_date": compliance_date,
			"next_compliance_date": None
		}
	)

	return f"Project Created: {project.name if project else 'No Template'} | Not Billable"
