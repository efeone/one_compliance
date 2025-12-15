import frappe
from frappe.model.document import Document
from frappe.utils import add_days, add_months, get_last_day, getdate, nowdate, today
from frappe.utils.data import cint

from one_compliance.one_compliance.utils import create_todo, create_compliance_project


MONTH_MAP = {
	"January": 1, "February": 2, "March": 3, "April": 4,
	"May": 5, "June": 6, "July": 7, "August": 8,
	"September": 9, "October": 10, "November": 11, "December": 12
}


def get_month_name(num):
	return next(name for name, number in MONTH_MAP.items() if number == num)

MONTH_MAP = {
	"January": 1, "February": 2, "March": 3, "April": 4,
	"May": 5, "June": 6, "July": 7, "August": 8,
	"September": 9, "October": 10, "November": 11, "December": 12
}

def get_month_name(num):
    return next(name for name, number in MONTH_MAP.items() if number == num)

class ComplianceAgreement(Document):
	def before_insert(self):
		self.status = "Open"

	def validate(self):
		self.validate_agreement_dates()
		self.validate_date_range()

	def on_submit(self):
		self.update_compliance_agreement_status()
		self.set_compliance_date()

	def on_update_after_submit(self):
		self.sign_validation()
		self.update_compliance_agreement_status()
		self.set_compliance_date()
		self.validate_compliance_dates_on_table()

	def validate_compliance_dates_on_table(self):
		'''
			Validate compliance_date and next_compliance_date for each compliance sub category detail.
		'''
		for row in self.compliance_category_details:
			if row.compliance_date and row.compliance_sub_category:
				compliance_date = getdate(row.compliance_date)
				next_compliance_date = getdate(row.next_compliance_date)
				sub = frappe.get_doc("Compliance Sub Category", row.compliance_sub_category)

				#ignore if not allow repeat
				if not sub.allow_repeat:
					continue

				day = cint(sub.day)
				step = {"Monthly":1, "Quarterly": 3, "Half Yearly": 6, "Yearly": 12}[sub.repeat_on]
				next_compliance_date = add_months(compliance_date, step)
				row.db_set("next_compliance_date", next_compliance_date)

				#Day Check
				if compliance_date.day != day:
					frappe.throw(
						title='Invalid Compliance Date',
						msg=f'Compliance Date must be on day <b>`{day}`</b> on Row <b>#{row.idx}</b>.'
					)

				# Validate Month based on repeat_on
				if sub.repeat_on == "Yearly":
					if sub.month:
						month_num = MONTH_MAP.get(sub.month)
						if compliance_date.month != month_num:
							frappe.throw(
								title='Invalid Compliance Date',
								msg=f'Compliance Date must be on month <b>`{sub.month}`</b> on Row <b>#{row.idx}</b>.'
							)

				# Validate Month for Quarterly
				elif sub.repeat_on == "Quarterly":
					if sub.month:
						start_month = MONTH_MAP.get(sub.month)
						valid_months = [(start_month + i*3 - 1) % 12 + 1 for i in range(4)]

						if compliance_date.month not in valid_months:
							allowed = ", ".join([get_month_name(m) for m in valid_months])
							frappe.throw(
								title='Invalid Compliance Date',
								msg=f'Compliance Date must be on month of <b>`{allowed}`</b> on Row <b>#{row.idx}</b>.'
							)

				# Validate Month for Half Yearly
				elif sub.repeat_on == "Half Yearly":
					if sub.month:
						start_month = MONTH_MAP.get(sub.month)
						valid_months = [start_month, ((start_month + 5) % 12) + 1]

						if compliance_date.month not in valid_months:
							allowed = ", ".join([get_month_name(m) for m in valid_months])
							frappe.throw(
								title='Invalid Compliance Date',
								msg=f'Compliance Date must be on month of <b>`{allowed}`</b> on Row <b>#{row.idx}</b>.'
							)

	def on_trash(self):
		delete_project_along_with_compliance_agreement = frappe.db.get_single_value(
			'Compliance Settings', 
			'delete_project_along_with_compliance_agreement'
		)
		if delete_project_along_with_compliance_agreement:
			delete_project_and_task(self.name)
		else:
			if frappe.db.exists('Project', {'compliance_agreement': self.name}):
				project_list = frappe.db.get_all('Project', filters={'compliance_agreement': self.name})
				for project in project_list:
					project_doc = frappe.get_doc('Project', project.name)
					project_doc.set('compliance_agreement', None)
					project_doc.save()

	def sign_validation(self):
		if self.workflow_state == 'Approved' and not self.authority_signature:
			frappe.throw('Authority Signature is required for Approval')
		if self.workflow_state == 'Customer Approved' and not self.customer_signature:
			frappe.throw('Customer Signature is required for Customer Approval')

	def validate_agreement_dates(self):
		if self.posting_date and getdate(self.posting_date) > getdate(today()):
			frappe.throw('Posting Date cannot be a future date.')
		if self.valid_from and self.valid_upto and not self.has_long_term_validity:
			if getdate(self.valid_from) > getdate(self.valid_upto):
				frappe.throw('From Date cannot be greater than Valid Upto Date')

	def validate_date_range(self):
		instance_valid_from = getdate(self.valid_from)
		instance_valid_upto = getdate(self.valid_upto) if self.valid_upto else None
		instance_categories = {d.sub_category_name for d in self.compliance_category_details}
		if not instance_categories:
			return
		
		existing_agreements = frappe.get_all(
			"Compliance Agreement",
			filters={
				"customer": self.customer,
				"workflow_state": "Customer Approved",
				"name": ["!=", self.name]
			},
			fields=["name", "valid_from", "valid_upto", "has_long_term_validity"]
		)
		
		for agreement_data in existing_agreements:
			agreement_categories = frappe.get_all(
				"Compliance Category Details",
				filters={"parent": agreement_data.name},
				fields=["sub_category_name"],
				pluck="sub_category_name"
			)
			overlapping_categories = instance_categories.intersection(set(agreement_categories))
			
			if not overlapping_categories:
				continue
			
			if self._check_date_overlap(
				instance_valid_from,
				instance_valid_upto,
				self.has_long_term_validity,
				getdate(agreement_data.valid_from),
				getdate(agreement_data.valid_upto) if agreement_data.valid_upto else None,
				agreement_data.has_long_term_validity
			):
				categories_list = ", ".join(sorted(overlapping_categories))
				frappe.throw(
					f"The compliance subcategories ({categories_list}) already exist in "
					f"Agreement '{agreement_data.name}' with overlapping date ranges."
				)

	def _check_date_overlap(self, start1, end1, long_term1, start2, end2, long_term2):
		if long_term1:
			end1 = None
		if long_term2:
			end2 = None
		if end1 is None and end2 is None:
			return True
		if end1 is None:
			return start1 <= end2
		if end2 is None:
			return start2 <= end1
		return start1 <= end2 and start2 <= end1

	def validate_compliance_dates_on_table(self):
		for row in self.compliance_category_details:
			if row.compliance_date and row.compliance_sub_category:
				compliance_date = getdate(row.compliance_date)
				sub = frappe.get_doc("Compliance Sub Category", row.compliance_sub_category)
				day = cint(sub.day)
				
				# Day Check
				if compliance_date.day != day:
					frappe.throw(
						title='Invalid Compliance Date',
						msg=f'Compliance Date must be on day <b>`{day}`</b> on Row <b>#{row.idx}</b>.'
					)

				# Validate Month logic
				if sub.repeat_on == "Yearly" and sub.month:
					if compliance_date.month != MONTH_MAP.get(sub.month):
						frappe.throw(
							title='Invalid Compliance Date',
							msg=f'Compliance Date must be on month <b>`{sub.month}`</b> on Row <b>#{row.idx}</b>.'
						)

				elif sub.repeat_on == "Quarterly" and sub.month:
					start_month = MONTH_MAP.get(sub.month)
					valid_months = [(start_month + i*3 - 1) % 12 + 1 for i in range(4)]
					if compliance_date.month not in valid_months:
						allowed = ", ".join([get_month_name(m) for m in valid_months])
						frappe.throw(
							title='Invalid Compliance Date',
							msg=f'Compliance Date must be on month of <b>`{allowed}`</b> on Row <b>#{row.idx}</b>.'
						)

				elif sub.repeat_on == "Half Yearly" and sub.month:
					start_month = MONTH_MAP.get(sub.month)
					valid_months = [start_month, ((start_month + 5) % 12) + 1]
					if compliance_date.month not in valid_months:
						allowed = ", ".join([get_month_name(m) for m in valid_months])
						frappe.throw(
							title='Invalid Compliance Date',
							msg=f'Compliance Date must be on month of <b>`{allowed}`</b> on Row <b>#{row.idx}</b>.'
						)

	def set_compliance_date(self):
		'''
			Set compliance_date and next_compliance_date for each compliance sub category detail.
		'''
		valid_from = getdate(self.valid_from)
		today_date = getdate(today())

		for row in self.compliance_category_details:
			if not row.compliance_sub_category:
				continue

			sub = frappe.get_doc("Compliance Sub Category", row.compliance_sub_category)

			if sub.allow_repeat:
				day = cint(sub.day)
				if sub.repeat_on == "Monthly":
					try:
						date = valid_from.replace(day=day)
					except Exception:
						date = get_last_day(valid_from)
					if date < valid_from:
						date = add_months(date, 1)
					next_date = add_months(date, 1)
				else:
					month_no = MONTH_MAP.get(sub.month)
					base = getdate(f"{valid_from.year}-{month_no}-01")
					try:
						date = base.replace(day=day)
					except Exception:
						date = get_last_day(base)
					step = {"Quarterly": 3, "Half Yearly": 6, "Yearly": 12}[sub.repeat_on]
					while date < valid_from:
						date = add_months(date, step)
					next_date = add_months(date, step)


				if not row.compliance_date:
					row.db_set("compliance_date", date)
				if not row.next_compliance_date:
					row.db_set("next_compliance_date", next_date)
				continue
			else:
				# One-Time Logic
				if self.status != "Active":
					continue
				if valid_from > today_date:
					continue
				
				project_date = valid_from
				if sub.project_template and not frappe.db.exists(
					"Project",
					{
						"compliance_agreement": self.name,
						"compliance_sub_category": sub.name
					}
				):
					create_compliance_project({
						"compliance_sub_category": sub.name,
						"customer": self.customer,
						"company": self.company,
						"start_date": project_date,
						"compliance_agreement": self.name,
						"compliance_category": sub.compliance_category or "",
						"priority": "Medium"
					})

				project_name = frappe.db.get_value(
					"Project",
					{
						"compliance_agreement": self.name,
						"compliance_sub_category": sub.name
					},
					"name"
				)

				if sub.is_billable:
					exists = frappe.db.exists(
						"Sales Order",
						{
							"compliance_agreement": self.name,
							"compliance_sub_category": sub.name,
							"transaction_date": project_date
						}
					)

					if not exists:
						so = frappe.new_doc("Sales Order")
						so.customer = self.customer
						so.company = self.company
						so.compliance_agreement = self.name
						so.compliance_sub_category = sub.name
						so.transaction_date = today_date
						so.delivery_date = today_date
						if self.default_payment_terms_template:
							so.payment_terms_template = self.default_payment_terms_template
						
						item_code = sub.item_code
						item_name = frappe.db.get_value("Item", item_code, "item_name")
						
						so.append("items", {
							"item_code": item_code,
							"item_name": item_name,
							"qty": 1,
							"rate": sub.rate or 0
						})
						so.insert(ignore_permissions=True)
						so.submit()

						if project_name:
							frappe.db.set_value("Project", project_name, "sales_order", so.name)
							frappe.db.set_value("Sales Order", so.name, "project", project_name)

	def update_compliance_agreement_status(self):
		today = getdate(frappe.utils.today())
		if self.customer:
			customer_status = frappe.db.get_value(
				"Customer",
				self.customer,
				["is_frozen", "disabled"],
				as_dict=True
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

	def make_sales_invoice(self):
		projectlist = frappe.get_all(
			"Project",
			filters={
				"compliance_agreement": self.name,
				"status": "Completed",
				"expected_start_date": (">=", self.invoice_date),
				"expected_end_date": ("<", self.next_invoice_date)
			},
			fields=["name", "customer", "compliance_sub_category", "company"]
		)
		if projectlist:
			sales_invoice = frappe.new_doc("Sales Invoice")
			for project in projectlist:
				sales_invoice.customer = project.customer
				sales_invoice.posting_date = frappe.utils.today()
				income_account = frappe.db.get_value('Company', project.company, 'default_income_account')
				payment_terms = frappe.db.get_value(
					'Compliance Agreement',
					project.compliance_agreement,
					'default_payment_terms_template'
				)
				sub_category_doc = frappe.get_doc("Compliance Sub Category", project.compliance_sub_category)
				rate = get_rate_from_compliance_agreement(
					project.compliance_agreement,
					project.compliance_sub_category
				) or sub_category_doc.rate

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
			next_invoice_date = calculate_next_invoice_date(
				self.next_invoice_date,
				self.invoice_generation,
				self.valid_upto
			)
			frappe.db.set_value(self.doctype, self.name, "next_invoice_date", next_invoice_date)
			frappe.db.commit()


# Utility Functions
def calculate_next_invoice_date(current_invoice_date, invoice_generation, valid_upto):
	if invoice_generation == 'Monthly':
		next_date = frappe.utils.add_months(current_invoice_date, 1)
	elif invoice_generation == 'Quarterly':
		next_date = frappe.utils.add_months(current_invoice_date, 3)
	elif invoice_generation == 'Half Yearly':
		next_date = frappe.utils.add_months(current_invoice_date, 6)
	elif invoice_generation == 'Yearly':
		next_date = frappe.utils.add_years(current_invoice_date, 1)
	else:
		next_date = current_invoice_date

	if valid_upto and next_date > valid_upto:
		return valid_upto
	return next_date


def calculate_rate(compliance_category_details, compliance_category):
	rate = 0
	for category in compliance_category_details:
		if category.compliance_category == compliance_category:
			rate += category.rate
	return rate


def update_status_on_customer_change(doc, method):
	agreements = frappe.get_all(
		"Compliance Agreement",
		filters={"customer": doc.name, "docstatus": ["!=", 2]},
		pluck="name"
	)
	for agreement_name in agreements:
		frappe.get_doc("Compliance Agreement", agreement_name).update_compliance_agreement_status()


# Whitelisted API Functions
@frappe.whitelist()
def check_project_status(compliance_agreement):
	if frappe.db.exists('Project', {'compliance_agreement': compliance_agreement, 'status': 'Completed'}):
		return True


@frappe.whitelist()
def change_agreement_status_scheduler():
	agreements = frappe.db.get_all(
		'Compliance Agreement',
		filters={'status': ['!=', 'Hold'], 'docstatus': ['!=', 2]}
	)
	today = getdate(frappe.utils.today())
	for agreement in agreements:
		self = frappe.get_doc('Compliance Agreement', agreement.name)
		if today < getdate(self.valid_from):
			frappe.db.set_value('Compliance Agreement', agreement.name, 'status', 'Open')
		elif ((self.valid_upto and today > getdate(self.valid_upto)) and not self.has_long_term_validity):
			frappe.db.set_value('Compliance Agreement', agreement.name, 'status', 'Expired')
		else:
			frappe.db.set_value('Compliance Agreement', agreement.name, 'status', 'Active')
		frappe.db.commit()


@frappe.whitelist()
def get_compliance_sub_category_list(compliance_category):
	return frappe.db.get_list(
		'Compliance Sub Category',
		filters={'compliance_category': compliance_category, 'enabled': 1},
		fields=['rate', 'name', 'compliance_category', 'sub_category']
	)


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
	if frappe.db.exists('Project', {'compliance_agreement': agreement_id}):
		project_list = frappe.db.get_all('Project', filters={'compliance_agreement': agreement_id})
		for project in project_list:
			task_list = frappe.db.get_all('Task', filters={'project': project.name})
			for task in task_list:
				frappe.db.delete('Task', task.name)
			frappe.db.delete('Project', project.name)
		frappe.msgprint('Agreement Deleted {0}.'.format(agreement_id), alert=1)


@frappe.whitelist()
def check_project_exists_or_not(compliance_sub_category, compliance_agreement):
	if frappe.db.exists(
		'Project',
		{
			'status': 'Open',
			'compliance_agreement': compliance_agreement,
			'compliance_sub_category': compliance_sub_category
		}
	):
		return True
	return False


@frappe.whitelist()
def get_rate_from_compliance_agreement(compliance_agreement, compliance_sub_category):
	rate_result = frappe.db.sql(
		"""select rate from `tabCompliance Category Details` 
		where parent=%s and compliance_sub_category=%s""",
		(compliance_agreement, compliance_sub_category),
		as_dict=1
	)
	if rate_result:
		return rate_result[0].rate


@frappe.whitelist()
def create_sales_orders_from_compliance_agreements(posting_date=today()):
	current_date = getdate(posting_date)

	agreements = frappe.db.sql("""
		SELECT ca.name, ca.customer, ca.company, ca.valid_from, ca.valid_upto, ca.default_payment_terms_template
		FROM `tabCompliance Agreement` ca
		INNER JOIN `tabCustomer` c ON ca.customer = c.name
		WHERE ca.status = 'Active' AND IFNULL(c.is_frozen, 0) = 0 AND IFNULL(c.disabled, 0) = 0
	""", as_dict=True)

	if not agreements:
		return

	for agreement in agreements:
		valid_from = getdate(agreement.valid_from)
		valid_upto = getdate(agreement.valid_upto) if agreement.valid_upto else None
		if current_date < valid_from or (valid_upto and current_date > valid_upto):
			continue

		category_details = frappe.get_all(
			"Compliance Category Details",
			filters={"parent": agreement.name},
			fields=["name", "compliance_sub_category", "rate"]
		)

		for detail in category_details:
			if not detail.compliance_sub_category:
				continue
			
			sub_category = frappe.db.get_value(
				"Compliance Sub Category",
				detail.compliance_sub_category,
				["allow_repeat", "repeat_on", "day", "month", "item_code", "project_template",
				 "compliance_category", "is_billable"],
				as_dict=True
			)
			if not sub_category:
				continue

			# Scheduling Logic
			should_create = False
			if not sub_category.allow_repeat:
				if current_date == valid_from:
					should_create = True
			else:
				month_number = MONTH_MAP.get(sub_category.month) if sub_category.month else None
				if sub_category.repeat_on == "Monthly" and sub_category.day:
					if current_date.day == int(sub_category.day):
						should_create = True
				elif sub_category.repeat_on in ["Quarterly", "Half Yearly", "Yearly"]:
					if month_number and sub_category.day:
						if current_date.month == month_number and current_date.day == int(sub_category.day):
							should_create = True

			if not should_create:
				continue

			# Create Project via Utility
			project = None
			if sub_category.project_template:
				project = create_compliance_project({
					"compliance_sub_category": detail.compliance_sub_category,
					"customer": agreement.customer,
					"company": agreement.company,
					"start_date": posting_date,
					"compliance_agreement": agreement.name,
					"compliance_category": sub_category.compliance_category,
					"priority": "Medium"
				})

			# Next Date Calculation
			base_date = getdate(nowdate())
			compliance_date = base_date
			next_compliance_date = None

			if sub_category.allow_repeat:
				step = {
					"Monthly": 1,
					"Quarterly": 3,
					"Half Yearly": 6,
					"Yearly": 12
				}.get(sub_category.repeat_on, 0)
				compliance_date = add_months(base_date, step)
				next_compliance_date = add_months(compliance_date, step)

			# Sales Order Creation
			if sub_category.is_billable and sub_category.item_code:
				if not frappe.db.exists(
					"Sales Order",
					{
						"compliance_agreement": agreement.name,
						"compliance_sub_category": detail.compliance_sub_category,
						"transaction_date": nowdate()
					}
				):
					try:
						item_name = frappe.db.get_value("Item", sub_category.item_code, "item_name")
						so = frappe.new_doc("Sales Order")
						so.customer = agreement.customer
						so.company = agreement.company
						so.compliance_agreement = agreement.name
						so.compliance_sub_category = detail.compliance_sub_category
						so.transaction_date = nowdate()
						so.delivery_date = nowdate()
						if agreement.default_payment_terms_template:
							so.payment_terms_template = agreement.default_payment_terms_template
						so.append("items", {
							"item_code": sub_category.item_code,
							"item_name": item_name,
							"qty": 1,
							"rate": detail.rate or 0
						})
						so.insert(ignore_permissions=True)
						so.submit()

						if project:
							project.db_set("sales_order", so.name)
							so.db_set("project", project.name)
					except Exception:
						frappe.log_error(frappe.get_traceback(), f"SO Creation Failed - {agreement.name}")

			frappe.db.set_value(
				"Compliance Category Details",
				detail.name,
				{"compliance_date": compliance_date, "next_compliance_date": next_compliance_date}
			)


@frappe.whitelist()
def create_future_one_time_projects():
	today_date = getdate(today())
	agreements = frappe.get_all(
		"Compliance Agreement",
		filters={"docstatus": 1, "status": "Active", "valid_from": today_date},
		fields=["name", "customer", "company"]
	)
	
	for agr in agreements:
		doc = frappe.get_doc("Compliance Agreement", agr.name)
		for row in doc.compliance_category_details:
			if not row.compliance_sub_category:
				continue
			sub_cat = frappe.get_doc("Compliance Sub Category", row.compliance_sub_category)
			
			if sub_cat.allow_repeat or not sub_cat.project_template:
				continue
			if frappe.db.exists(
				"Project",
				{"compliance_agreement": doc.name, "compliance_sub_category": sub_cat.name}
			):
				continue
			
			try:
				create_compliance_project({
					"compliance_sub_category": sub_cat.name,
					"customer": doc.customer,
					"company": doc.company,
					"start_date": today_date,
					"compliance_agreement": doc.name,
					"compliance_category": sub_cat.compliance_category or "",
					"priority": "Medium"
				})
			except Exception as e:
				frappe.log_error(f"Failed to create project: {e}")

			# Billable Check
			if sub_cat.is_billable:
				if not frappe.db.exists(
					"Sales Order",
					{
						"compliance_agreement": doc.name,
						"compliance_sub_category": sub_cat.name,
						"transaction_date": today_date
					}
				):
					so = frappe.new_doc("Sales Order")
					so.customer = doc.customer
					so.company = doc.company
					so.compliance_agreement = doc.name
					so.compliance_sub_category = sub_cat.name
					so.transaction_date = today_date
					so.delivery_date = today_date
					if doc.default_payment_terms_template:
						so.payment_terms_template = doc.default_payment_terms_template
					so.append("items", {
						"item_code": sub_cat.item_code,
						"item_name": frappe.db.get_value("Item", sub_cat.item_code, "item_name"),
						"qty": 1,
						"rate": sub_cat.rate or 0
					})
					so.insert(ignore_permissions=True)
					so.submit()


@frappe.whitelist()
def create_sales_order_and_project_from_popup(
	compliance_agreement,
	compliance_sub_category,
	compliance_date,
	compliance_category_details_id
):
	compliance_date = getdate(compliance_date)
	agreement = frappe.get_doc("Compliance Agreement", compliance_agreement)
	subcat = frappe.db.get_value(
		"Compliance Sub Category",
		compliance_sub_category,
		["item_code", "is_billable", "project_template", "compliance_category", "allow_repeat", "repeat_on"],
		as_dict=True
	)

	if not subcat:
		frappe.throw("Compliance Sub Category not found")
	
	detail = frappe.db.get_value(
		"Compliance Category Details",
		compliance_category_details_id,
		["rate", "compliance_date", "next_compliance_date"],
		as_dict=True
	)
	base_date = detail.next_compliance_date or detail.compliance_date or compliance_date
	new_compliance_date = base_date
	
	step = {
		"Monthly": 1,
		"Quarterly": 3,
		"Half Yearly": 6,
		"Yearly": 12
	}.get(subcat.repeat_on, 0) if subcat.allow_repeat else 0
	new_next_date = add_months(base_date, step) if step > 0 else None

	project = None
	if subcat.project_template:
		project = create_compliance_project({
			"compliance_sub_category": compliance_sub_category,
			"customer": agreement.customer,
			"company": agreement.company,
			"start_date": new_compliance_date,
			"compliance_agreement": compliance_agreement,
			"compliance_category": subcat.compliance_category,
			"priority": "Medium"
		})

	if not subcat.is_billable:
		frappe.db.set_value(
			"Compliance Category Details",
			compliance_category_details_id,
			{"compliance_date": new_compliance_date, "next_compliance_date": new_next_date}
		)
		return f"Project Created: {project.name if project else 'No Template'} | Not Billable"

	if frappe.db.exists(
		"Sales Order",
		{
			"compliance_agreement": compliance_agreement,
			"compliance_sub_category": compliance_sub_category,
			"transaction_date": new_compliance_date
		}
	):
		return "Sales Order already exists for this date"

	so = frappe.new_doc("Sales Order")
	so.customer = agreement.customer
	so.company = agreement.company
	so.compliance_agreement = compliance_agreement
	so.compliance_sub_category = compliance_sub_category
	so.transaction_date = new_compliance_date
	so.delivery_date = new_compliance_date
	if agreement.default_payment_terms_template:
		so.payment_terms_template = agreement.default_payment_terms_template
	so.append("items", {
		"item_code": subcat.item_code,
		"item_name": frappe.db.get_value("Item", subcat.item_code, "item_name"),
		"qty": 1,
		"rate": detail.rate or 0
	})
	so.insert(ignore_permissions=True)
	so.submit()

	if project:
		project.db_set("sales_order", so.name)
		so.db_set("project", project.name)

	frappe.db.set_value(
		"Compliance Category Details",
		compliance_category_details_id,
		{"compliance_date": new_compliance_date, "next_compliance_date": new_next_date}
	)
	return f"Sales Order Created: {so.name} | Project Created: {project.name if project else 'No Template'}"