import frappe
from erpnext.accounts.doctype.sales_invoice.sales_invoice import (
	get_mode_of_payment_info,
)
from erpnext.accounts.party import get_party_account
from frappe import _, throw
from frappe.desk.form.assign_to import clear, close_all_assignments
from frappe.email.doctype.notification.notification import get_context
from frappe.utils import add_days, cstr, date_diff, flt, getdate
from frappe.utils.data import format_date
from frappe.utils.nestedset import NestedSet
from erpnext.projects.doctype.task.task import check_if_child_exists, CircularReferenceError

from one_compliance.one_compliance.utils import (
	create_project_completion_todos,
	send_notification,
	send_notification_to_roles,
)


class CustomTask(NestedSet):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from erpnext.projects.doctype.task_depends_on.task_depends_on import (
			TaskDependsOn,
		)
		from frappe.types import DF

		act_end_date: DF.Date | None
		act_start_date: DF.Date | None
		actual_time: DF.Float
		closing_date: DF.Date | None
		color: DF.Color | None
		company: DF.Link | None
		completed_by: DF.Link | None
		completed_on: DF.Date | None
		department: DF.Link | None
		depends_on: DF.Table[TaskDependsOn]
		depends_on_tasks: DF.Code | None
		description: DF.TextEditor | None
		duration: DF.Int
		exp_end_date: DF.Date | None
		exp_start_date: DF.Date | None
		expected_time: DF.Float
		is_group: DF.Check
		is_milestone: DF.Check
		is_template: DF.Check
		issue: DF.Link | None
		lft: DF.Int
		old_parent: DF.Data | None
		parent_task: DF.Link | None
		priority: DF.Literal["Low", "Medium", "High", "Urgent"]
		progress: DF.Percent
		project: DF.Link | None
		review_date: DF.Date | None
		rgt: DF.Int
		start: DF.Int
		status: DF.Literal[
			"Open", "Working", "Pending Review", "Overdue", "Template", "Completed", "Cancelled"
		]
		subject: DF.Data
		task_weight: DF.Float
		template_task: DF.Data | None
		total_billing_amount: DF.Currency
		total_costing_amount: DF.Currency
		type: DF.Link | None
	# end: auto-generated types

	nsm_parent_field = "parent_task"

	def get_customer_details(self):
		cust = frappe.db.sql("select customer_name from `tabCustomer` where name=%s", self.customer)
		if cust:
			ret = {"customer_name": cust and cust[0][0] or ""}
			return ret

	def validate(self):
		self.validate_dates()
		self.validate_progress()
		self.validate_status()
		self.update_depends_on()
		self.validate_dependencies_for_template_task()
		self.validate_completed_on()

	def validate_dates(self):
		self.validate_from_to_dates("exp_start_date", "exp_end_date")
		self.validate_from_to_dates("act_start_date", "act_end_date")
		self.validate_parent_expected_end_date()
		self.validate_parent_project_dates()

	def validate_parent_expected_end_date(self):
		if not self.parent_task or not self.exp_end_date:
			return

		parent_exp_end_date = frappe.db.get_value("Task", self.parent_task, "exp_end_date")
		if not parent_exp_end_date:
			return

		if getdate(self.exp_end_date) > getdate(parent_exp_end_date):
			frappe.throw(
				_(
					"Expected End Date should be less than or equal to parent task's Expected End Date {0}."
				).format(format_date(parent_exp_end_date)),
				frappe.exceptions.InvalidDates,
			)

	def validate_parent_project_dates(self):
		if not self.project or frappe.flags.in_test:
			return

		if project_end_date := frappe.db.get_value("Project", self.project, "expected_end_date"):
			project_end_date = getdate(project_end_date)
			for fieldname in ("exp_start_date", "exp_end_date", "act_start_date", "act_end_date"):
				task_date = self.get(fieldname)
				if task_date and date_diff(project_end_date, getdate(task_date)) < 0:
					frappe.throw(
						_("{0}'s {1} cannot be after {2}'s Expected End Date.").format(
							frappe.bold(frappe.get_desk_link("Task", self.name)),
							_(self.meta.get_label(fieldname)),
							frappe.bold(frappe.get_desk_link("Project", self.project)),
						),
						frappe.exceptions.InvalidDates,
					)

	def validate_status(self):
		if self.is_template and self.status != "Template":
			self.status = "Template"
		if self.status != self.get_db_value("status") and self.status == "Completed":
			for d in self.depends_on:
				if frappe.db.get_single_value("Compliance Settings", "ignore_dependent_task_validation"):
					frappe.db.set_value("Task", self.depends_on, "completed_on", self.completed_on)
					frappe.db.set_value("Task", self.depends_on, "status", "Completed")
				else:
					if frappe.db.get_value("Task", d.task, "status") not in ("Completed", "Cancelled"):
						frappe.throw(
							_(
								"Cannot complete task {0} as its dependant task {1} are not completed / cancelled."
							).format(frappe.bold(self.name), frappe.bold(d.task))
						)

			close_all_assignments(self.doctype, self.name)

	def validate_progress(self):
		if flt(self.progress or 0) > 100:
			frappe.throw(_("Progress % for a task cannot be more than 100."))

		if self.status == "Completed":
			self.progress = 100

	def validate_dependencies_for_template_task(self):
		if self.is_template:
			self.validate_parent_template_task()
			self.validate_depends_on_tasks()

	def validate_parent_template_task(self):
		if self.parent_task:
			if not frappe.db.get_value("Task", self.parent_task, "is_template"):
				parent_task_format = f"""<a href="#Form/Task/{self.parent_task}">{self.parent_task}</a>"""
				frappe.throw(_("Parent Task {0} is not a Template Task").format(parent_task_format))

	def validate_depends_on_tasks(self):
		if self.depends_on:
			for task in self.depends_on:
				if not frappe.db.get_value("Task", task.task, "is_template"):
					dependent_task_format = f"""<a href="#Form/Task/{task.task}">{task.task}</a>"""
					frappe.throw(_("Dependent Task {0} is not a Template Task").format(dependent_task_format))

	def validate_completed_on(self):
		if self.completed_on and getdate(self.completed_on) > getdate():
			frappe.throw(_("Completed On cannot be greater than Today"))

	def update_depends_on(self):
		depends_on_tasks = ""
		for d in self.depends_on:
			if d.task and d.task not in depends_on_tasks:
				depends_on_tasks += d.task + ","
		self.depends_on_tasks = depends_on_tasks

	def update_nsm_model(self):
		frappe.utils.nestedset.update_nsm(self)

	def on_update(self):
		self.update_nsm_model()
		self.check_recursion()
		self.reschedule_dependent_tasks()
		self.update_project()
		self.unassign_todo()
		self.populate_depends_on()

	def unassign_todo(self):
		if self.status == "Completed":
			close_all_assignments(self.doctype, self.name)
		if self.status == "Cancelled":
			clear(self.doctype, self.name)

	def update_time_and_costing(self):
		tl = frappe.db.sql(
			"""select min(from_time) as start_date, max(to_time) as end_date,
			sum(billing_amount) as total_billing_amount, sum(costing_amount) as total_costing_amount,
			sum(hours) as time from `tabTimesheet Detail` where task = %s and docstatus=1""",
			self.name,
			as_dict=1,
		)[0]
		if self.status == "Open":
			self.status = "Working"
		self.total_costing_amount = tl.total_costing_amount
		self.total_billing_amount = tl.total_billing_amount
		self.actual_time = tl.time
		self.act_start_date = tl.start_date
		self.act_end_date = tl.end_date

	def update_project(self):
		if self.project and not self.flags.from_project:
			frappe.get_cached_doc("Project", self.project).update_project()

	def check_recursion(self):
		if self.flags.ignore_recursion_check:
			return
		check_list = [["task", "parent"], ["parent", "task"]]
		for d in check_list:
			task_list, count = [self.name], 0
			while len(task_list) > count:
				tasks = frappe.db.sql(
					" select {} from `tabTask Depends On` where {} = {} ".format(d[0], d[1], "%s"),
					cstr(task_list[count]),
				)
				count = count + 1
				for b in tasks:
					if b[0] == self.name:
						frappe.throw(_("Circular Reference Error"), CircularReferenceError)
					if b[0]:
						task_list.append(b[0])

				if count == 15:
					break

	def reschedule_dependent_tasks(self):
		end_date = self.exp_end_date or self.act_end_date
		if end_date:
			for task_name in frappe.db.sql(
				"""
				select name from `tabTask` as parent
				where parent.project = %(project)s
					and parent.name in (
						select parent from `tabTask Depends On` as child
						where child.task = %(task)s and child.project = %(project)s)
			""",
				{"project": self.project, "task": self.name},
				as_dict=1,
			):
				task = frappe.get_doc("Task", task_name.name)
				if (
					task.exp_start_date
					and task.exp_end_date
					and task.exp_start_date < getdate(end_date)
					and task.status == "Open"
				):
					task_duration = date_diff(task.exp_end_date, task.exp_start_date)
					task.exp_start_date = add_days(end_date, 1)
					task.exp_end_date = add_days(task.exp_start_date, task_duration)
					task.flags.ignore_recursion_check = True
					task.save()

	def has_webform_permission(self):
		project_user = frappe.db.get_value(
			"Project User", {"parent": self.project, "user": frappe.session.user}, "user"
		)
		if project_user:
			return True

	def populate_depends_on(self):
		if self.parent_task:
			parent = frappe.get_doc("Task", self.parent_task)
			if self.name not in [row.task for row in parent.depends_on]:
				parent.append(
					"depends_on", {"doctype": "Task Depends On", "task": self.name, "subject": self.subject}
				)
				parent.save()

	def on_trash(self):
		if check_if_child_exists(self.name):
			throw(_("Child Task exists for this Task. You can not delete this Task."))

		self.update_nsm_model()

	def after_delete(self):
		self.update_project()

	def update_status(self):
		if self.status not in ("Cancelled", "Completed") and self.exp_end_date:
			from datetime import datetime

			if self.exp_end_date < datetime.now().date():
				self.db_set("status", "Overdue", update_modified=False)
				self.update_project()


@frappe.whitelist()
def append_users_to_project(doc, method):
	if doc.assigned_to and doc.project:
		if frappe.db.exists('Employee Group', doc.assigned_to):
			employee_group = frappe.get_doc('Employee Group', doc.assigned_to)
			for employee in employee_group.employee_list:
				if employee.user_id:
					add_project_user_if_not_exists(doc.project, employee.user_id)
@frappe.whitelist()
def set_task_status_to_hold(doc, method):
	if doc.hold == 1:
		frappe.db.set_value("Task", doc.name, "status", "Hold")

@frappe.whitelist()
def update_expected_dates_in_task(doc):
	if doc.doctype == "Task":
		doc.exp_start_date = frappe.utils.today()
		doc.exp_end_date = add_days(doc.exp_start_date, doc.duration)
		doc.save()
	frappe.db.commit()

def add_project_user_if_not_exists(project, user_id):
	project_doc = frappe.get_doc('Project', project)
	exists = False
	for project_user in project_doc.users:
		if project_user.user == user_id:
			exists = True
	if not exists:
		project_doc.append('users', {
			'user': user_id
		})
		project_doc.save()

@frappe.whitelist()
def task_on_update(doc, method):
	set_task_time_line(doc)
	if doc.status == 'Completed':
		if frappe.db.get_single_value("Compliance Settings", "enable_task_complete_notification_for_director"):
			task_complete_notification_for_director(doc)
		if doc.custom_is_payable:
			create_journal_entry(doc)
		if doc.project:
			if frappe.db.exists('Project', doc.project):
				project = frappe.get_doc ('Project', doc.project)
				if project.status == 'Completed':
					if not frappe.db.get_value("Sales Order", project.sales_order, "custom_is_rework"):
						create_project_completion_todos(project.sales_order, project.name)
					# send_project_completion_mail = frappe.db.get_value('Customer', project.customer, 'send_project_completion_mail')
					# if send_project_completion_mail:
					# 	email_id = frappe.db.get_value('Customer', project.customer, 'email_id')
					# 	if email_id:
					# 		project_complete_notification_for_customer(project, email_id)
		# Check if this task is a dependency for other tasks
		dependent_tasks = frappe.get_all('Task Depends On', filters={'task': doc.name}, fields=['parent'])
		for dependent_task in dependent_tasks:
			task = frappe.get_doc('Task', dependent_task.parent)
			all_dependencies_completed = True
			# Check if all dependent tasks are completed
			for dependency in task.depends_on:
				dependency_doc = frappe.get_doc('Task', dependency.task)
				if dependency_doc.status != 'Completed':
					all_dependencies_completed = False
					break
			# If all dependencies are completed, mark the dependent task as completed
			if all_dependencies_completed and task.status != 'Completed':
				task.status = 'Completed'
				task.save()

@frappe.whitelist()
def task_complete_notification_for_director(doc):
	context = get_context(doc)
	send_notification_to_roles(doc, 'Director', context, 'task_complete_notification_for_director')

@frappe.whitelist()
def create_journal_entry(doc):
	if doc.custom_payable_amount and doc.custom_mode_of_payment:
		account = get_party_account('Customer', doc.customer, doc.company)
		payment_account = get_mode_of_payment_info(doc.custom_mode_of_payment, doc.company)
		default_account = payment_account[0]['default_account']
		journal_entry = frappe.new_doc('Journal Entry')
		journal_entry.voucher_type = 'Bank Entry'
		journal_entry.cheque_no = doc.custom_reference_number
		journal_entry.cheque_date = doc.custom_reference_date
		journal_entry.user_remark = doc.custom_user_remark
		journal_entry.posting_date = frappe.utils.today()
		journal_entry.append('accounts', {
			'account': account,
			'party_type': 'Customer',
			'party': doc.customer,
			'project': doc.project,
			'debit_in_account_currency': doc.custom_payable_amount
		})
		journal_entry.append('accounts', {
			'account': default_account,
			'project': doc.project,
			'credit_in_account_currency': doc.custom_payable_amount
		})
		journal_entry.insert(ignore_permissions = True)
		frappe.msgprint("Journal Entry is created Successfully", alert=True)

@frappe.whitelist()
def project_complete_notification_for_customer(doc, email_id):
	context = get_context(doc)
	send_notification(doc, email_id, context, 'project_complete_notification_for_customer')

@frappe.whitelist()
def set_task_time_line(doc):
	if doc.duration and doc.exp_start_date:
		exp_end_date = add_days(doc.exp_start_date, doc.duration)
		doc.db_set('exp_end_date', exp_end_date, update_modified=False)
		frappe.db.commit()

@frappe.whitelist()
def make_sales_invoice(doc, method):
	# The sales order will be automatic on the on update of the project
	if doc.status == 'Completed':
		if frappe.db.exists('Project', doc.project):
			project = frappe.get_doc ('Project',doc.project)
			if project.status == 'Completed':
				if frappe.db.exists('Compliance Sub Category', project.compliance_sub_category):
					sub_category_doc = frappe.get_doc('Compliance Sub Category', project.compliance_sub_category)
					if sub_category_doc.is_billable:
						sales_order = frappe.db.exists('Sales Order', project.sales_order)
						if not sales_order:
							sales_order = frappe.db.exists("Sales Order", {"project":project.name})
							if sales_order:
								project.sales_order = sales_order
								project.save(ignore_permissions=True)
						if sales_order:
							sales_order_status = frappe.db.get_value("Sales Order", sales_order, "workflow_state")
							if sales_order_status == "In Progress":
								if frappe.db.get_value("Sales Order", sales_order, "custom_is_rework"):
									frappe.db.set_value("Sales Order", sales_order, "workflow_state", "Completed")
								else:
									frappe.db.set_value("Sales Order", sales_order, "workflow_state", "Proforma Invoice")
							elif sales_order_status == "Pre-Invoice":
								frappe.db.set_value("Sales Order", sales_order, "workflow_state", "Invoiced")
						else:
							payment_terms = None
							rate = None
							if frappe.db.exists('Compliance Agreement', project.compliance_agreement):
								payment_terms = frappe.db.get_value('Compliance Agreement', project.compliance_agreement,'default_payment_terms_template')
								rate = get_rate_from_compliance_agreement(project.compliance_agreement, project.compliance_sub_category)
							rate = rate if rate else sub_category_doc.rate
							create_sales_order(project, rate, sub_category_doc, payment_terms)

@frappe.whitelist()
def create_sales_invoice(project, payment_terms, rate, sub_category_doc):
	sales_invoice = frappe.new_doc('Sales Invoice')
	sales_invoice.customer = project.customer
	sales_invoice.posting_date = frappe.utils.today()
	sales_invoice.project = project.name
	sales_invoice.company = project.company
	sub_category_income_account = get_company_income_account(project.company,sub_category_doc.name)
	income_account = sub_category_income_account if sub_category_income_account else frappe.db.get_value('Company',project.company, 'default_income_account')

	if payment_terms:
		sales_invoice.default_payment_terms_template = payment_terms
	sales_invoice.append('items', {
		'item_code' : sub_category_doc.item_code,
		'item_name' : sub_category_doc.sub_category,
		'rate' : rate,
		'qty' : 1,
		'income_account' : income_account,
		'description' : project.custom_project_service
	})
	sales_invoice.save(ignore_permissions=True)

@frappe.whitelist()
def create_sales_order(project, rate, sub_category_doc, payment_terms=None, submit=False):
	"""method creates a new sales order

	Args:
		project (EmployeeProject): Document Object of Project DocType
		payment_terms (str): Name of the Payment Terms Template
		rate (float): Rate of the Item
		sub_category_doc (ComplianceSubCategory): Document Object of Compliance Sub Category
		submit (bool): True or False, to submit the sales order or not
	"""
	new_sales_order = frappe.new_doc("Sales Order")
	new_sales_order.customer = project.customer
	new_sales_order.posting_date = frappe.utils.today()
	new_sales_order.delivery_date = frappe.utils.today()
	new_sales_order.project = project.name
	new_sales_order.company = project.company
	if payment_terms:
		new_sales_order.payment_terms_template = payment_terms
	new_sales_order.append('items', {
		'item_code' : sub_category_doc.item_code,
		'item_name' : sub_category_doc.sub_category,
		'rate' : rate,
		'qty' : 1,
		'description' : project.custom_project_service
	})
	new_sales_order.insert(ignore_permissions=True, ignore_mandatory=True)
	new_sales_order.submit()
	frappe.db.set_value("Project", project.name, "sales_order", new_sales_order.name)
	frappe.msgprint("Sales Order {0} Created against {1}".format(new_sales_order.name, project.name), alert=True)

@frappe.whitelist()
def update_task_status(task_id, status, completed_by, completed_on):
	# Load the task document from the database
	task_doc = frappe.get_doc("Task", task_id)
	task_doc.completed_on = frappe.utils.getdate(completed_on)
	task_doc.status = status
	task_doc.completed_by = completed_by
	task_doc.save()
	frappe.db.commit()
	frappe.msgprint("Task Status has been set to {0}".format(status), alert=True)
	return True

@frappe.whitelist()
def get_permission_query_conditions(user):

	if not user:
		user = frappe.session.user

	user_roles = frappe.get_roles(user)
	if "Administrator" in user_roles:
		return None

	if "Manager" in user_roles or "Executive" in user_roles:
		conditions = """(tabTask._assign like '%{user}%')""" \
			.format(user=user)
		return conditions
	else:
		return None

@frappe.whitelist()
def get_rate_from_sales_order(sales_order, compliance_sub_category):
	rate_result = frappe.db.sql(
		"""
		select rate
		from `tabCompliance Category Details`
		where parent=%s and compliance_sub_category=%s""",
		(sales_order, compliance_sub_category),
		as_dict=1,
		)
	if rate_result:
		return rate_result[0].rate

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

# Check for uncompleted documents on updation of task to completed
@frappe.whitelist()
def subtask_on_update(doc, event):
	if doc.status == "Completed":
		items = frappe.get_all("Task Document Item", filters={"parent": doc.name}, fields=["is_completed"])
		if any(item.get("is_completed") == 0 for item in items):
			frappe.throw(_("Please complete all documents before marking the task as complete"))

# Set series for task if it's template
@frappe.whitelist()
def autoname(doc, event):
	if doc.is_template:
		series = frappe.get_single("Compliance Settings").get("task_template_series")
		if series:
			doc.name = frappe.model.naming.make_autoname(series + '.#####')
		else:
			frappe.throw(_("Please set the Task Template Series in Compliance Settings"))
	else:
		pass

# Set Income Account as per the Company Name
@frappe.whitelist()
def get_company_income_account(company, compliance_sub_category):
	income_result = frappe.db.sql(
		"""
		select default_income_account
		from `tabSub Category Account`
		where parent=%s and company=%s""",
		(compliance_sub_category, company),
		as_dict=1,
		)
	if income_result:
		return income_result[0].default_income_account

def set_task_readiness_flow_on_creation(doc, method=None):
    if not doc.compliance_sub_category:
        return

    compliance_subcategory = frappe.get_doc("Compliance Sub Category", doc.compliance_sub_category)
    if not compliance_subcategory.project_template:
        return

    project_template = frappe.get_doc("Project Template", compliance_subcategory.project_template)
    if not project_template.enable_task_readiness_flow:
        return

    # Fetch ordered task subjects from project template
    template_task_subjects = [task.subject for task in project_template.tasks]

    if not template_task_subjects:
        return

    # Check if subject matches the first one
    if doc.subject == template_task_subjects[0]:
        # Find the earliest task with this subject in this project
        earliest_task = frappe.get_all(
            "Task",
            filters={
                "project": doc.project,
                "subject": doc.subject
            },
            fields=["name"],
            order_by="creation asc",
            limit=1
        )

        if earliest_task and earliest_task[0].name == doc.name:
            frappe.db.set_value("Task", doc.name, "readiness_status", "Ready")
        else:
            frappe.db.set_value("Task", doc.name, "readiness_status", "Not Ready")
    else:
        # For all tasks not matching the first subject
        frappe.db.set_value("Task", doc.name, "readiness_status", "Not Ready")



def on_task_update(doc, method=None):
    if doc.status != "Completed" or doc.readiness_status != "Ready":
        return

    project = frappe.get_doc("Project", doc.project)
    if not project.compliance_sub_category:
        return

    compliance_subcategory = frappe.get_doc("Compliance Sub Category", project.compliance_sub_category)
    if not compliance_subcategory.project_template:
        return

    project_template = frappe.get_doc("Project Template", compliance_subcategory.project_template)
    template_task_subjects = [task.subject for task in project_template.tasks]

    try:
        current_index = template_task_subjects.index(doc.subject)
        if current_index + 1 < len(template_task_subjects):
            next_subject = template_task_subjects[current_index + 1]

            next_task = frappe.get_all(
                "Task",
                filters={
                    "project": doc.project,
                    "subject": next_subject,
                    "readiness_status": ["!=", "Ready"],
                    "status": ["not in", ["Completed", "Cancelled"]]
                },
                fields=["name", "readiness_status"],
                order_by="creation asc",
                limit=1
            )

            if next_task:
                frappe.db.set_value("Task", next_task[0].name, "readiness_status", "Ready")

    except ValueError:
        pass

@frappe.whitelist()
def check_readiness_edit_permission(user):
    # Get the role allowed to change readiness status from Compliance Settings
    allowed_role = frappe.db.get_single_value("Compliance Settings", "role_allowed_to_change_readiness_status")

    # Check if the given user has this role
    has_role = frappe.db.exists("Has Role", {"parent": user, "role": allowed_role})

    return True if has_role else False
