from datetime import datetime, timedelta

import frappe
from frappe import _
from frappe.utils import add_days, add_months, date_diff, getdate, json, today
from one_compliance.one_compliance.utils import add_custom as add_assign
from one_compliance.one_compliance.utils import create_todo, get_users_with_role


@frappe.whitelist()
def update_journal_entry(doc):
	if doc.custom_reimbursement_details:
		for reimbursement_detail in doc.custom_reimbursement_details:
			if frappe.db.exists('Journal Entry', reimbursement_detail.journal_entry):
				entry_doc = frappe.get_doc('Journal Entry', reimbursement_detail.journal_entry)
				if entry_doc and entry_doc.docstatus == 0:
					entry_doc.posting_date = reimbursement_detail.date
					entry_doc.user_remark = reimbursement_detail.user_remark
					for account in entry_doc.accounts:
						if account.debit_in_account_currency:
							account.debit_in_account_currency = reimbursement_detail.amount
						else:
							account.credit_in_account_currency = reimbursement_detail.amount
					entry_doc.save()
					frappe.msgprint("Journal Entry Updated", indicator="blue", alert=1)

@frappe.whitelist()
def submit_journal_entry(journal_entry):
	if frappe.db.exists('Journal Entry', journal_entry):
		journal_entry_doc = frappe.get_doc('Journal Entry', journal_entry)
		if journal_entry_doc.docstatus == 0:
			journal_entry_doc.submit()
			return True
		else:
			frappe.throw(_("Journal Entry is already submitted."))

@frappe.whitelist()
def create_project_on_submit(doc, method):
	assign_to = []
	if(doc.custom_create_project_automatically):
		for employee_list in doc.custom_assign_to:
			employee_name = frappe.get_doc('Employee', employee_list.employee)
			assign_to.append(employee_name.name)
			assign_to_str = json.dumps(assign_to)
		for item in doc.items:
			create_project_from_sales_order(doc.name, doc.custom_expected_start_date, item.item_code, doc.custom_priority, assign_to_str, doc.custom_expected_end_date, custom_instructions=item.custom_instructions)

@frappe.whitelist()
def get_compliance_subcategory(item_code):
	# Fetch compliance subcategory based on the item code
	compliance_subcategory = frappe.get_doc('Compliance Sub Category', {'item_code': item_code})
	return {
		'compliance_category': compliance_subcategory.compliance_category,
		'name': compliance_subcategory.name,
		'project_template': compliance_subcategory.project_template
	}

@frappe.whitelist()
def create_project_from_sales_order(sales_order, start_date, item_code, priority, assign_to=None, expected_end_date=None, remark=None, custom_instructions=None):
	if(assign_to):
		employees = json.loads(assign_to)
	self = frappe.get_doc('Sales Order', sales_order)
	compliance_sub_category = frappe.get_doc('Compliance Sub Category',{'item_code':item_code})
	project_template  = compliance_sub_category.project_template
	project_template_doc = frappe.get_doc('Project Template', project_template)
	head_of_department = frappe.db.get_value('Employee', {'employee':compliance_sub_category.head_of_department}, 'user_id')
	if project_template:
		repeat_on = compliance_sub_category.repeat_on
		project_based_on_prior_phase = compliance_sub_category.project_based_on_prior_phase
		previous_month_date = add_months(getdate(start_date), -1)
		naming_year = getdate(previous_month_date).year if project_based_on_prior_phase else getdate(start_date).year
		naming_month = getdate(previous_month_date).strftime("%B") if project_based_on_prior_phase else getdate(start_date).strftime("%B")
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
		if not assign_to and not any(template_task.type and template_task.employee_or_group for template_task in project_template_doc.tasks):
			frappe.msgprint("Project can't be created since no assignees are specified in tasks")
		else:
			project = frappe.new_doc('Project')
			project.company = self.company
			project.cost_center = frappe.get_cached_value("Company", self.company, "cost_center")
			add_compliance_category_in_project_name = frappe.db.get_single_value('Compliance Settings', 'add_compliance_category_in_project_name')
			if self.custom_project_name_automatically:
				if add_compliance_category_in_project_name:
					project.project_name = (self.customer_name or ' ') + '-' + compliance_sub_category.name + '-' + str(naming)
				else:
					project.project_name = (self.customer_name  or ' ') + '-' + compliance_sub_category.sub_category + '-' + str(naming)
			else:
				project.project_name = (self.custom_project_name or ' ') + '-'+ self.customer_name + '-' + compliance_sub_category.name + '-' + str(naming)
			project.customer = self.customer
			project.compliance_sub_category = compliance_sub_category.name
			project.compliance_category = compliance_sub_category.compliance_category
			project.expected_start_date = start_date
			if expected_end_date:
				days_diff = date_diff(getdate(expected_end_date), getdate(start_date))
				if(days_diff > project_template_doc.custom_project_duration):
					project.expected_end_date = expected_end_date
				else:
					project.expected_end_date = add_days(start_date, project_template_doc.custom_project_duration)
			else:
				if project_template_doc.custom_project_duration:
					project.expected_end_date = add_days(start_date, project_template_doc.custom_project_duration)
			project.priority = priority
			project.custom_project_service = compliance_sub_category.name + '-' + str(naming)
			if custom_instructions:
				project.custom_instructions = custom_instructions
			project.notes = remark
			project.sales_order = sales_order
			project.category_type = compliance_sub_category.category_type
			project.department = compliance_sub_category.department
			project.save(ignore_permissions=True)
			if project.compliance_sub_category:
				if compliance_sub_category and compliance_sub_category.head_of_department:
					todo = frappe.new_doc('ToDo')
					todo.status = 'Open'
					todo.allocated_to = head_of_department
					todo.description = "project  Assign to " + head_of_department
					todo.reference_type = 'Project'
					todo.reference_name = project.name
					todo.assigned_by = frappe.session.user
					todo.save(ignore_permissions=True)
					if todo:
						frappe.msgprint(("Project is assigned to {0}".format(head_of_department)),alert = 1)
			if assign_to:
				for employee in employees:
					user = frappe.db.get_value('Employee', employee, 'user_id')
					if user and user != head_of_department:
						create_todo('Project', project.name, user, user, 'Project {0} Assigned Successfully'.format(project.name))
			frappe.msgprint('Project Created for {0}.'.format(compliance_sub_category.name), alert = 1)
			for template_task in reversed(project_template_doc.tasks):
				''' Method to create task against created project from the Project Template '''
				template_task_doc = frappe.get_doc('Task', template_task.task)
				task_doc = frappe.new_doc('Task')
				task_doc.compliance_sub_category = compliance_sub_category.name
				task_doc.subject = template_task.subject
				task_doc.project = project.name
				task_doc.company = project.company
				task_doc.project_name = project.project_name
				task_doc.category_type = project.category_type
				task_doc.exp_start_date = start_date
				task_doc.custom_serial_number = template_task.idx
				task_doc.department = compliance_sub_category.department
				task_doc.task_weightage = template_task_doc.task_weightage or 0
				if template_task_doc.expected_time:
					task_doc.expected_time = template_task_doc.expected_time
				if template_task.custom_task_duration:
					task_doc.duration = template_task.custom_task_duration
					task_doc.exp_end_date = add_days(start_date, template_task.custom_task_duration)
				if template_task_doc.depends_on:
					for depends_task in template_task_doc.depends_on:
						dependent_task = frappe.get_doc('Task', {'project':project.name,'subject':depends_task.subject}, 'name')
						task_doc.append("depends_on", {
							"task": dependent_task.name,
						})
				if template_task.custom_has_document:
					for documents in project_template_doc.custom_documents_required:
						if documents.task == template_task.task:
							for docs in documents.documents.split(', '):
								task_doc.append("custom_task_document_items", {
									"document": docs
								})
				task_doc.save(ignore_permissions=True)
				if project.compliance_sub_category:
					if compliance_sub_category and compliance_sub_category.head_of_department:
						create_todo('Task', task_doc.name, head_of_department, frappe.session.user, "Task Assign to " + head_of_department)
				if assign_to:
					for employee in employees:
						user = frappe.db.get_value('Employee', employee, 'user_id')
						if user and user != head_of_department:
							create_todo('Task', task_doc.name, user, frappe.session.user, 'Task {0} Assigned Successfully'.format(task_doc.name))
				elif not assign_to and template_task.type and template_task.employee_or_group:
					frappe.db.set_value('Task', task_doc.name, 'assigned_to', template_task.employee_or_group)
					if template_task.type == "Employee":
						employee = frappe.db.get_value('Employee', template_task.employee_or_group, 'user_id')
						if employee and employee != head_of_department:
							create_todo('Task', task_doc.name, employee, frappe.session.user, 'Task {0} Assigned Successfully'.format(task_doc.name))
					if template_task.type == "Employee Group":
						employee_group = frappe.get_doc('Employee Group', template_task.employee_or_group)
						if employee_group.employee_list:
							for employee in employee_group.employee_list:
								create_todo('Task', task_doc.name, employee.user_id, frappe.session.user, 'Task {0} Assigned Successfully'.format(task_doc.name))

			frappe.db.commit()
	else:
		frappe.throw( title = _('ALERT !!'), msg = _('Project Template does not exist for {0}'.format(compliance_sub_category)))

@frappe.whitelist()
def create_sales_order_from_event(event, customer=None, sub_category=None, rate=None, description=None, company=None):
	missing_fields = []
	if not customer:
		missing_fields.append("Customer")
	if not sub_category:
		missing_fields.append("Service")
	if not description:
		missing_fields.append("Service Description")
	if missing_fields:
		if len(missing_fields) > 1:
			missing_fields_str = ', '.join(missing_fields[:-1]) + ' and ' + missing_fields[-1]
		else:
			missing_fields_str = missing_fields[0]

		frappe.throw(f"Required Field: {missing_fields_str}.")

	sales_orders = frappe.get_all(
		"Sales Order",
		filters={"customer": customer, "docstatus": 1},
		fields=["name"]
	)
	for sales_order in sales_orders:
		items = frappe.get_all(
			"Sales Order Item",
			filters={"parent": sales_order.name, "description": description},
			fields=["name"]
		)
		if items:
			frappe.throw("Proforma Invoice is already created for this Event.")
	event_doc = frappe.get_doc("Event", event)
	custom_service = event_doc.custom_service or sub_category
	custom_customer = event_doc.custom_customer or customer
	sub_category_doc = frappe.get_doc("Compliance Sub Category", sub_category)
	new_sales_order = frappe.new_doc("Sales Order")
	new_sales_order.customer = customer
	new_sales_order.event = event
	new_sales_order.posting_date = frappe.utils.today()
	new_sales_order.delivery_date = frappe.utils.today()
	new_sales_order.append('items', {
		'item_code': sub_category_doc.item_code,
		'item_name': sub_category_doc.sub_category,
		'custom_compliance_category': sub_category_doc.compliance_category,
		'custom_compliance_subcategory': sub_category_doc.name,
		'rate': rate,
		'qty': 1,
		'description': description
	})
	new_sales_order.company = company
	new_sales_order.insert(ignore_permissions=True)
	new_sales_order.submit()
	frappe.db.set_value("Sales Order", new_sales_order.name, "status", "Proforma Invoice")
	frappe.db.set_value("Sales Order", new_sales_order.name, "workflow_state", "Proforma Invoice")
	frappe.db.set_value("Sales Order", sales_order, "invoice_generation_date", today())
	frappe.msgprint(f"Proforma Invoice {new_sales_order.name} Created against {event}", alert=True)
	accounts_users = get_users_with_role("Accounts User")
	add_assign({
		"assign_to": accounts_users,
		"doctype": "Sales Order",
		"name": new_sales_order.name,
		"description": f"{custom_service} for {custom_customer} is Completed, Please Proceed with the Invoice"
	})


def so_on_cancel_custom(doc, method=None):
	"""Set workflow state to Cancelled when cancelling sales order"""
	doc.db_set("workflow_state", "Cancelled")

def so_on_update_after_submit(doc, method):
	'''
		Method trigger on so_on_update_after_submit of Sales Order
	'''
	update_journal_entry(doc)
	set_total_reimbursement_amount(doc)
	doc.reload()

def set_total_reimbursement_amount(doc):
	'''
		Method to set total_reimbursement_amount
	'''
	total_reimbursement_amount = 0
	for row in doc.custom_reimbursement_details:
		total_reimbursement_amount += row.amount
	doc.custom_total_reimbursement_amount = total_reimbursement_amount
	frappe.db.set_value('Sales Order', doc.name, 'custom_total_reimbursement_amount', total_reimbursement_amount)

@frappe.whitelist()
def delete_linked_records(sales_order):
	"""
	Deletes all records linked with the specified sales order.

	Args:
	project (str): The name of the project to delete linked records for.
	"""
	sales_invoice = frappe.db.get_value(
		"Sales Invoice Item", {"sales_order": sales_order}, "parent"
	)
	if frappe.db.exists("Sales Invoice", sales_invoice):
		frappe.throw("Cannot proceed with this operation as it is invoiced")

	project = frappe.db.get_value("Sales Order", sales_order, "project")

	if frappe.db.exists("Project", project):
		linked_tasks = frappe.get_all("Task", filters={"project": project})
		for task in linked_tasks:
			frappe.delete_doc("Task", task["name"], ignore_permissions=True)

		project_doc = frappe.get_doc("Project", project)
		project_doc.sales_order = ""
		project_doc.save(ignore_permissions=True)
		frappe.delete_doc("Project", project, ignore_permissions=True)

	doc = frappe.get_doc("Sales Order", sales_order)
	doc.flags.ignore_permissions = True
	doc.cancel()
	frappe.delete_doc("Sales Order", sales_order, ignore_permissions=True)

	return "success"


@frappe.whitelist()
def create_opportunity():
	"""
	Creates Opportunities for Sales Orders flagged for follow_up_for_next_project
	and assigns a Task to follow_up_person from Compliance Sub Category
	"""
	today_date = getdate(today())
	this_year = today_date.year
	this_month = today_date.month

	sales_orders = frappe.db.get_all(
		"Sales Order",
		filters={"follow_up_for_next_project": 1, "follow_up_completed": 0},
		fields=["name", "customer", "status", "workflow_state", "company", "follow_up_completed"]
	)

	for so in sales_orders:
		sales_order_items = frappe.get_all(
			"Sales Order Item",
			filters={"parent": so.name},
			fields=[
				"item_code", "item_name", "uom", "qty",
				"brand", "item_group", "description",
				"image", "base_rate", "base_amount", "rate", "amount",
				"custom_compliance_subcategory as compliance_sub_category",
				"custom_compliance_category as compliance_category"
			]
		)

		for item in sales_order_items:
			subcat_name = item.compliance_sub_category
			if not subcat_name:
				continue

			compliance = frappe.get_doc("Compliance Sub Category", subcat_name)

			if not (compliance.allow_repeat and compliance.renew_notif):
				continue

			day = int(compliance.day or 1)
			notif_days = int(float(compliance.renew_notif_days_before or 0))
			repeat_on = compliance.repeat_on
			scheduled_date = None

			try:
				# ---------------- Monthly ----------------
				if repeat_on == "Monthly":
					last_day_of_month = (datetime(this_year, this_month + 1, 1) - timedelta(days=1)).day \
						if this_month < 12 else 31

					if day == 1 and today_date.day == last_day_of_month:
						next_month = this_month + 1 if this_month < 12 else 1
						next_year = this_year if this_month < 12 else this_year + 1
						scheduled_date = datetime(next_year, next_month, 1).date()
					else:
						scheduled_date = datetime(this_year, this_month, day).date()

				# ---------------- Quarterly ----------------
				elif repeat_on == "Quarterly":
					for m in [1, 4, 7, 10]:
						d = datetime(this_year, m, day).date()
						if d >= today_date:
							scheduled_date = d
							break
					if not scheduled_date:
						scheduled_date = datetime(this_year + 1, 1, day).date()

				# ---------------- Half Yearly ----------------
				elif repeat_on == "Half Yearly":
					for m in [1, 7]:
						d = datetime(this_year, m, day).date()
						if d >= today_date:
							scheduled_date = d
							break
					if not scheduled_date:
						scheduled_date = datetime(this_year + 1, 1, day).date()

				# ---------------- Yearly ----------------
				elif repeat_on == "Yearly":
					if compliance.month:
						m = datetime.strptime(compliance.month, "%B").month
						d = datetime(this_year, m, day).date()
						if d >= today_date:
							scheduled_date = d
						else:
							scheduled_date = datetime(this_year + 1, m, day).date()

			except Exception as e:
				frappe.log_error(f"Invalid date calculation for {subcat_name}: {e}", "Create Opportunity Error")
				continue

			if not scheduled_date:
				continue

			# --- Notification trigger date ---
			if day == 1 and notif_days > 0:
				prev_month = scheduled_date.month - 1 if scheduled_date.month > 1 else 12
				prev_year = scheduled_date.year if scheduled_date.month > 1 else scheduled_date.year - 1
				last_day_prev_month = (datetime(prev_year, prev_month + 1, 1) - timedelta(days=1)).date()
				notif_trigger_date = last_day_prev_month
			else:
				notif_trigger_date = add_days(scheduled_date, -notif_days)

			if notif_trigger_date != today_date:
				continue

			# Skip if Opportunity already exists
			existing_opportunity = frappe.db.exists("Opportunity", {"sales_order": so.name})
			if existing_opportunity:
				continue

			try:
				# Only create for active sales orders
				if so.status not in ["Draft", "Closed", "Cancelled"] or so.workflow_state not in ["Pending", "Cancelled"]:
					opportunity = frappe.new_doc("Opportunity")
					opportunity.opportunity_from = "Customer"
					opportunity.party_name = so.customer
					opportunity.status = "Open"
					opportunity.opportunity_type = "Sales"
					opportunity.sales_order = so.name
					opportunity.naming_series = "CRM-OPP-.YYYY.-"
					opportunity.company = so.company
					opportunity.opportunity_date = today_date

					for soi in sales_order_items:
						opp_item = opportunity.append("items", {})
						opp_item.item_code = soi.item_code
						opp_item.item_name = soi.item_name
						opp_item.uom = soi.uom
						opp_item.qty = soi.qty
						opp_item.brand = soi.brand
						opp_item.item_group = soi.item_group
						opp_item.description = soi.description
						opp_item.image = soi.image
						opp_item.base_rate = soi.base_rate
						opp_item.base_amount = soi.base_amount
						opp_item.rate = soi.rate
						opp_item.amount = soi.amount
						opp_item.compliance_category = soi.compliance_category
						opp_item.compliance_sub_category = soi.compliance_sub_category

					opportunity.insert(ignore_permissions=True)
					frappe.db.commit()
	 
					frappe.db.set_value("Sales Order", so.name, "follow_up_completed", 1)
					frappe.db.commit()

					follow_up_user = frappe.db.get_value("Employee", compliance.follow_up_person, "user_id")

					try:
						if follow_up_user:
							todo = frappe.new_doc("ToDo")
							todo.owner = follow_up_user
							todo.assigned_by = frappe.session.user
							todo.allocated_to = follow_up_user
							todo.reference_type = "Opportunity"
							todo.reference_name = opportunity.name
							todo.description = f"Follow up for compliance sub category: {subcat_name}"
							todo.status = "Open"
							todo.priority = "Medium"
							todo.date = today()
							todo.insert(ignore_permissions=True)
							frappe.db.commit()

					except Exception as e:
						frappe.log_error(f"Failed to create ToDo for {subcat_name}: {e}", "Create Opportunity Error")

			except Exception as e:
				frappe.log_error(f"Failed to create Opportunity for {subcat_name}: {e}", "Create Opportunity Error")



def set_compliance_fields(doc, method):
	"""
	For each item , this function fetches the related compliance category 
	and subcategory 
	"""
	for item in doc.items:
		if item.item_code:
			subcat =  frappe.db.get_value(
				"Compliance Sub Category",
				 {"item_code": item.item_code},
				 ["compliance_category", "name"],
				 as_dict=True
			)
			if subcat:
				item.custom_compliance_category     = subcat.compliance_category
				item.custom_compliance_subcategory  = subcat.name