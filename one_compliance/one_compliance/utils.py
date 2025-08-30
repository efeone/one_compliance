import json

import frappe
from frappe import _
from frappe.desk.form.assign_to import format_message_for_assign_to, get
from frappe.email.doctype.notification.notification import get_context
from frappe.utils import date_diff, get_datetime, getdate
from frappe.utils.user import get_users_with_role
from frappe.desk.doctype.notification_log.notification_log import (
	enqueue_create_notification,
	get_title,
	get_title_html,
)
from frappe.desk.form.document_follow import follow_document
from frappe.utils.data import strip_html


@frappe.whitelist()
def create_notification_log(subject, type, for_user, email_content, document_type, document_name):
	''' Method to Create Notification Log '''
	notification_doc = frappe.new_doc('Notification Log')
	notification_doc.subject = subject
	notification_doc.type = type
	notification_doc.for_user = for_user
	notification_doc.email_content = email_content
	notification_doc.document_type = document_type
	notification_doc.document_name = document_name
	notification_doc.save(ignore_permissions=True)
	frappe.db.commit()

@frappe.whitelist()
def create_todo(doctype, name, assign_to, owner, description):
	''' Method used for create ToDo '''
	due_date = frappe.utils.today()
	if doctype =='Task':
		if frappe.db.get_value(doctype, name, 'exp_end_date'):
			due_date = frappe.db.get_value(doctype, name, 'exp_end_date')
	add_custom(
		{
			"assign_to": [assign_to],
			"doctype": doctype,
			"name": name,
			"description": description,
			"assigned_by": frappe.session.user,
			"date": due_date,
		}
	)

@frappe.whitelist()
def task_daily_sheduler():
	""" Method to send task before due date and overdue notification to employee and task overdue and no action taken notification to director"""
	tasks = frappe.db.get_all('Task', filters= {'status': ['not in', ['Template', 'Completed', 'Cancelled']]})
	if tasks:
		for task in tasks:
			doc = frappe.get_doc('Task', task.name)
			assigns = frappe.db.get_value('Task', doc.name, '_assign')
			if assigns:
				assigns = json.loads(assigns)
				for assign in assigns:
					context = get_context(doc)
					if assign:
						today = frappe.utils.today()
						if doc.exp_end_date:
							days_diff = date_diff(getdate(doc.exp_end_date), getdate(today))
							if days_diff == 0:
								if frappe.db.get_single_value('Compliance Settings', 'enable_task_overdue_notification_for_employee'):
									send_notification(doc, assign, context, 'task_overdue_notification_for_employee')
								if frappe.db.get_single_value('Compliance Settings', 'enable_task_overdue_notification_for_director'):
									send_notification_to_roles(doc, 'Director', context, 'task_overdue_notification_for_director')
							if days_diff == 1:
								if frappe.db.get_single_value('Compliance Settings', 'enable_task_before_due_date_notification'):
									send_notification(doc, assign, context, 'task_before_due_date_notification')
						if doc.exp_start_date:
							if doc.status == 'Open' and (getdate(doc.exp_start_date) < getdate(today)):
								if frappe.db.get_single_value('Compliance Settings', 'enable_task_no_action_taken_notification_for_director'):
									send_notification_to_roles(doc, 'Director', context, 'no_action_taken_notification_for_director')

@frappe.whitelist()
def project_overdue_notification():
	if frappe.db.exists('Project', {'status': ['not in',['Cancelled','Hold','Completed']]}):
		projects = frappe.db.get_all('Project', filters= {'status': ['not in',['Cancelled','Hold','Completed']]})
		if projects:
			for project in projects:
				doc = frappe.get_doc('Project', project.name)
				today = frappe.utils.today()
				context = get_context(doc)
				if doc.expected_end_date:
					days_diff = date_diff(getdate(doc.expected_end_date), getdate(today))
					if days_diff == 1:
						if frappe.db.get_single_value('Compliance Settings', 'enable_project_before_due_date_notification'):
							send_notification_to_roles(doc, 'Director', context, 'project_before_due_date_notification')

@frappe.whitelist()
def send_notification(doc, for_user, context, notification_template_fieldname):
	''' Method to send notification for daily task scheduling using Notification Template '''
	notification_template = frappe.db.get_value('Compliance Sub Category', doc.compliance_sub_category, notification_template_fieldname)
	if notification_template:
		subject_template, content_template = frappe.db.get_value('Notification Template', notification_template, ['subject', 'content'])
		subject = frappe.render_template(subject_template, context)
		content = frappe.render_template(content_template, context)
		create_notification_log(subject, 'Mention', for_user, content, doc.doctype, doc.name)

@frappe.whitelist()
def send_notification_to_roles(doc, role, context, notification_template_fieldname):
	""" Method to send notification to perticular role """
	users = get_users_with_role(role)
	for user in users:
		send_notification(doc, user, context, notification_template_fieldname)

@frappe.whitelist()
def view_credential_details(customer,purpose):
	""" Method to view customer Credential details """
	if frappe.db.exists('Customer Credentials',{'customer':customer}):
		customer_credential = frappe.db.get_value('Customer Credentials',{'customer':customer})
		if frappe.db.exists('Credential Details', {'parent':customer_credential,'purpose':purpose}):
			username, cd_name, url = frappe.db.get_value('Credential Details', {'parent':customer_credential,'purpose':purpose}, ['username', 'name','url'])
			password = frappe.utils.password.get_decrypted_password("Credential Details", cd_name, "password")
			return [username, password, url]
		else:
			frappe.throw(_('Credential not configured for this Purpose'))
	else:
		frappe.throw(title = _('ALERT !!'),msg = _('Credential not configured for this Purpose'))

@frappe.whitelist()
def view_customer_documents(customer,compliance_sub_category):
	""" Method to view customer documents """
	if frappe.db.exists('Customer Document',{'customer':customer}):
		customer_document =frappe.db.get_value('Customer Document',{'customer':customer})
		if frappe.db.exists('Customer Document Record',{'parent':customer_document,'compliance_sub_category':compliance_sub_category}):
			document_attachment = frappe.db.get_value('Customer Document Record',{'parent':customer_document,'compliance_sub_category':compliance_sub_category}, ['document_attachment'])
			return [document_attachment]
		else:
			frappe.throw(_('Document not attached for this sub category'))
	else:
		frappe.throw(title = _('ALERT !!'),msg = _('Document not attached for this sub category'))


@frappe.whitelist()
def edit_customer_credentials(customer):
	""" Method to edit or add customer Credential """
	if frappe.db.exists('Customer Credentials',{'customer':customer}):
		customer_credential = frappe.db.get_value('Customer Credentials',{'customer':customer})
		return customer_credential

@frappe.whitelist()
def update_digital_signature(digital_signature, register_type, register_name):
	""" Method to append values to child table digital signature details from inward and outward register """
	if digital_signature and register_name and register_type:
		if not frappe.db.exists('Digital Signature', digital_signature):
			frappe.throw("Digital signature does not exists")
		if not frappe.db.exists(register_type, register_name):
			frappe.throw("Register does not exists")
		digital_signature_doc = frappe.get_doc('Digital Signature', digital_signature)
		register_doc = frappe.get_doc(register_type, register_name)
		digital_signature_detail = digital_signature_doc.append('digital_signature_details')
		digital_signature_detail.register_type = register_doc.doctype
		digital_signature_detail.reference_id = register_doc.name
		if register_type == 'Inward Register':
			digital_signature_detail.posting_date = register_doc.posting_date
			digital_signature_detail.posting_time = register_doc.posting_time
			digital_signature_detail.sender_receiver = register_doc.person_name
		elif register_type == 'Outward Register':
			digital_signature_detail.posting_date = register_doc.returned_date
			digital_signature_detail.posting_time = register_doc.returned_time
			digital_signature_detail.sender_receiver = register_doc.receiver_name
		digital_signature_doc.save(ignore_permissions=True)
		frappe.db.commit()
		digital_signature_doc.reload()
		return True

@frappe.whitelist()
def notification_for_digital_signature_expiry():
	''' Method to send notification for notifying Digital Signature expiration to director email '''
	digital_signature_list = frappe.get_all('Digital Signature', filters= {'notify_on_expiration': 1})
	if digital_signature_list:
		today = getdate(frappe.utils.today())
		for digital_signature in digital_signature_list:
			digital_signature_doc = frappe.get_doc('Digital Signature', digital_signature.name)
			context = get_context(digital_signature_doc)
			director_mail = digital_signature_doc.director_email
			due_date = getdate(digital_signature_doc.expiry_date)
			if digital_signature_doc.notify_before and frappe.db.get_single_value('Compliance Settings', 'enable_digital_signature_expiry_notification'):
				if digital_signature_doc.notify_before_unit == 'Day':
					notification_date = frappe.utils.add_to_date(due_date, days=-1*digital_signature_doc.notify_before)
					if getdate(notification_date) == today:
						send_notification_for_digital_signature(digital_signature_doc, director_mail, context, 'digital_signature_expiry_notification')
				if digital_signature_doc.notify_before_unit == 'Week':
					notification_date = frappe.utils.add_to_date(due_date, days=-7*digital_signature_doc.notify_before)
					if getdate(notification_date) == today:
						send_notification_for_digital_signature(digital_signature_doc, director_mail, context, 'digital_signature_expiry_notification')
				if digital_signature_doc.notify_before_unit == 'Month':
					notification_date = frappe.utils.add_months(due_date, (-1*digital_signature_doc.notify_before))
					if getdate(notification_date) == today:
						send_notification_for_digital_signature(digital_signature_doc, director_mail, context, 'digital_signature_expiry_notification')

@frappe.whitelist()
def send_notification_for_digital_signature(doc, for_user, context, notification_template_fieldname):
	''' Method to send email for digital signature expiration using Notification Template '''
	notification_template = frappe.db.get_value('Digital Signature', doc.name, notification_template_fieldname)
	if notification_template:
		subject_template, content_template = frappe.db.get_value('Notification Template', notification_template, ['subject', 'content'])
		subject = frappe.render_template(subject_template, context)
		content = frappe.render_template(content_template, context)
		frappe.sendmail(recipients=[for_user], subject=subject, message=content)
		frappe.db.commit()

@frappe.whitelist()
def gst_overdue():
	'''Method to view GST overdue in number card'''
	query = """
	SELECT
		COUNT(*) as count
	FROM
		`tabProject`
	WHERE
		status = 'Overdue' AND category_type = 'GST'
	"""
	project_count = frappe.db.sql(query, as_dict=True)
	if project_count and project_count[0].get('count') is not None:
		return project_count[0]['count']
	else:
		return 0

@frappe.whitelist()
def income_tax_overdue():
	'''Method to view Income Tax overdue in number card'''
	query = """
	SELECT
		COUNT(*) as count
	FROM
		`tabProject`
	WHERE
		status = 'Overdue' AND category_type = 'Income Tax'
	"""
	project_count = frappe.db.sql(query, as_dict=True)
	if project_count and project_count[0].get('count') is not None:
		return project_count[0]['count']
	else:
		return 0

@frappe.whitelist()
def consulting_overdue():
	'''Method to view Income Tax overdue in number card'''
	query = """
	SELECT
		COUNT(*) as count
	FROM
		`tabProject`
	WHERE
		status = 'Overdue' AND category_type = 'Income Tax'
	"""
	project_count = frappe.db.sql(query, as_dict=True)
	if project_count and project_count[0].get('count') is not None:
		return project_count[0]['count']
	else:
		return 0

@frappe.whitelist()
def compliance_overdue():
	'''Method to view  Compliance overdue in number card'''
	query = """
	SELECT
		COUNT(*) as count
	FROM
		`tabProject`
	WHERE
		status = 'Overdue' AND category_type = 'Compliance'
	"""
	project_count = frappe.db.sql(query, as_dict=True)
	if project_count and project_count[0].get('count') is not None:
		return project_count[0]['count']
	else:
		return 0

@frappe.whitelist()
def audit_overdue():
	'''Method to view  Audit overdue in number card'''
	query = """
	SELECT
		COUNT(*) as count
	FROM
		`tabProject`
	WHERE
		status = 'Overdue' AND category_type = 'Audit'
	"""
	project_count = frappe.db.sql(query, as_dict=True)
	if project_count and project_count[0].get('count') is not None:
		return project_count[0]['count']
	else:
		return 0

def create_project_completion_todos(sales_order, project_name):
	"""method to create ToDo for accounts user on project completion

	Args:
		sales_order (str): ID of Sales Order linked with project
		project_name (str): Project Name of the Project to handle completion
	"""
	project_id = frappe.db.exists("Project", {"project_name": project_name})
	if not project_id:
		frappe.throw(f"Project {project_name} does not exist")
	project = frappe.get_doc("Project", project_id)

	if project.get("custom_is_internal"):
		return

	compliance_sub_category = project.get("compliance_sub_category")
	customer = project.get("customer")
	company = project.get("company")

	# Validate necessary fields
	if not customer:
		frappe.throw(f"Customer is missing in Project: {project_name}")
	if not compliance_sub_category:
		frappe.throw(f"Compliance Sub Category is missing in Project: {project_name}")

	# Construct task description
	description = f"{compliance_sub_category} for {customer} is Completed, Please Proceed with the invoice"
	if frappe.db.exists("ToDo", {
		"reference_type": "Sales Order",
		"reference_name": sales_order,
		"description": description
	}):
		return

	accounts_users = get_users_with_role("Accounts User")

	# Assign the task
	todos = add_custom(
		args={
			"assign_to": accounts_users,
			"doctype": "Sales Order",
			"name": sales_order,
			"description": description
		},
		ignore_permissions=True
	)

	for todo in todos:
		frappe.db.set_value("ToDo", todo.name, "company", company)

@frappe.whitelist()
def make_time_sheet_entry(event):
	event_doc = frappe.get_doc("Event", event)
	from_time = get_datetime(event_doc.starts_on)
	to_time = get_datetime(event_doc.ends_on)
	activity_type = 'Communication'
	if event_doc.event_participants:
		for participant in event_doc.event_participants:
			if participant.reference_doctype == "Employee":
				employee_id = participant.reference_docname
				if employee_id:
					create_timesheet(employee_id, activity_type, from_time, to_time)


@frappe.whitelist()
def create_timesheet(employee, activity_type, from_time, to_time):
	from_time = get_datetime(from_time)
	to_time = get_datetime(to_time)
	employee_id = frappe.get_value("Employee", {"name": employee}, "name")

	# Check if a timesheet already exists for the employee within the given date range
	if frappe.db.exists("Timesheet", {"employee": employee_id, "start_date": from_time.date(), "end_date": to_time.date()}):
		frappe.throw(_("Timesheet already Created"))
	else:
		timesheet = frappe.new_doc("Timesheet")
		timesheet.employee = employee_id
		timesheet.append("time_logs",{
			"activity_type": activity_type,
			"from_time": from_time,
			"to_time": to_time
		})

		timesheet.insert(ignore_permissions=True)
		frappe.db.commit()

@frappe.whitelist()
def get_employee_list_for_hod():
	user_roles = frappe.get_roles(frappe.session.user)
	if "Head Of Department" in user_roles or "System Manager" in user_roles:
		employees = frappe.db.sql("""
			SELECT
				employee as employee_id, employee_name
			FROM
				`tabEmployee`
			WHERE
				status = 'Active'
		""", as_dict=True)
	else:
		employees = frappe.db.sql("""
			SELECT
				employee as employee_id, employee_name
			FROM
				`tabEmployee`
			WHERE
				user_id = %s
		""", frappe.session.user, as_dict=True)
	return employees

@frappe.whitelist()
def add_custom(args=None, *, ignore_permissions=False):
	"""add in someone's to do list
	args = {
			"assign_to": [],
			"doctype": ,
			"name": ,
			"description": ,
			"assignment_rule":
	}

	"""
	if not args:
		args = frappe.local.form_dict

	users_with_duplicate_todo = []
	shared_with_users = []

	for assign_to in frappe.parse_json(args.get("assign_to")):
		filters = {
			"reference_type": args["doctype"],
			"reference_name": args["name"],
			"status": "Open",
			"allocated_to": assign_to,
		}
		if not ignore_permissions:
			frappe.get_doc(args["doctype"], args["name"]).check_permission()

		if frappe.get_all("ToDo", filters=filters):
			users_with_duplicate_todo.append(assign_to)
		else:
			from frappe.utils import nowdate

			description = str(args.get("description", ""))
			has_content = strip_html(description) or "<img" in description
			if not has_content:
				args["description"] = _("Assignment for {0} {1}").format(args["doctype"], args["name"])

			d = frappe.get_doc(
				{
					"doctype": "ToDo",
					"allocated_to": assign_to,
					"reference_type": args["doctype"],
					"reference_name": str(args["name"]),
					"description": args.get("description"),
					"priority": args.get("priority", "Medium"),
					"status": "Open",
					"date": args.get("date", nowdate()),
					"assigned_by": args.get("assigned_by", frappe.session.user),
					"assignment_rule": args.get("assignment_rule"),
				}
			).insert(ignore_permissions=True)

			# set assigned_to if field exists
			if frappe.get_meta(args["doctype"]).get_field("assigned_to"):
				frappe.db.set_value(args["doctype"], args["name"], "assigned_to", assign_to)

			doc = frappe.get_doc(args["doctype"], args["name"])

			# if assignee does not have permissions, share or inform
			if not frappe.has_permission(doc=doc, user=assign_to):
				if frappe.get_system_settings("disable_document_sharing"):
					msg = _("User {0} is not permitted to access this document.").format(
						frappe.bold(assign_to)
					)
					msg += "<br>" + _(
						"As document sharing is disabled, please give them the required permissions before assigning."
					)
					frappe.throw(msg, title=_("Missing Permission"))
				else:
					frappe.share.add(doc.doctype, doc.name, assign_to)
					shared_with_users.append(assign_to)

			# make this document followed by assigned user
			if frappe.get_cached_value("User", assign_to, "follow_assigned_documents"):
				follow_document(args["doctype"], args["name"], assign_to)

			# notify
			ignore_email = frappe.db.get_value("Ignore ToDo Notifications Detail", {
	   			"parent": "Compliance Settings",
		  		"doctype_to_ignore":d.reference_type
			}, "email")
			ignore_system_notification = frappe.db.get_value("Ignore ToDo Notifications Detail", {
	   			"parent": "Compliance Settings",
		  		"doctype_to_ignore":d.reference_type
			}, "system_notification")
			print("ignore_email", ignore_email)
			print("ignore_system_notification", ignore_system_notification)
			notify_assignment(
				d.assigned_by,
				d.allocated_to,
				d.reference_type,
				d.reference_name,
				action="ASSIGN",
				description=args.get("description"),
				ignore_email=ignore_email,
				ignore_system_notification=ignore_system_notification
			)

	if shared_with_users:
		user_list = format_message_for_assign_to(shared_with_users)
		frappe.msgprint(
			_("Shared with the following Users with Read access:{0}").format(user_list, alert=True)
		)

	if users_with_duplicate_todo:
		user_list = format_message_for_assign_to(users_with_duplicate_todo)
		frappe.msgprint(_("Already in the following Users ToDo list:{0}").format(user_list, alert=True))

	return get(args)

def notify_assignment(assigned_by, allocated_to, doc_type, doc_name, action="CLOSE", description=None, ignore_email=False, ignore_system_notification=False):
	"""
	Notify assignee that there is a change in assignment
	"""
	if not (assigned_by and allocated_to and doc_type and doc_name):
		return

	assigned_user = frappe.db.get_value("User", allocated_to, ["language", "enabled"], as_dict=True)

	# return if self assigned or user disabled
	if assigned_by == allocated_to or not assigned_user.enabled:
		return

	# Search for email address in description -- i.e. assignee
	user_name = frappe.get_cached_value("User", frappe.session.user, "full_name")
	title = get_title(doc_type, doc_name)
	description_html = f"<div>{description}</div>" if description else None

	if action == "CLOSE":
		subject = _("Your assignment on {0} {1} has been removed by {2}", lang=assigned_user.language).format(
			frappe.bold(_(doc_type)), get_title_html(title), frappe.bold(user_name)
		)
	else:
		user_name = frappe.bold(user_name)
		document_type = frappe.bold(_(doc_type, lang=assigned_user.language))
		title = get_title_html(title)
		subject = _("{0} assigned a new task {1} {2} to you", lang=assigned_user.language).format(
			user_name, document_type, title
		)

	if not ignore_email or not ignore_system_notification:
		type = "Assignment"
		if ignore_email:
			type = "Alert"
		notification_doc = {
			"type": type,
			"document_type": doc_type,
			"subject": subject,
			"document_name": doc_name,
			"from_user": frappe.session.user,
			"email_content": description_html,
		}

		enqueue_create_notification(allocated_to, notification_doc)

