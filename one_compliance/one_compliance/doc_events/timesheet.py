import frappe
from apps.one_compliance.one_compliance.one_compliance.utils import (
	create_notification_log,
)


def check_lag_and_notify(doc, method=None):
	"""
		Send notification if Lag time found in timesheet
	"""
	lag_rows_to_notify = []
	lag_rows_to_mail = []

	for row in doc.time_logs:
		if row.lag_time and not row.lag_notification_sent:
			lag_rows_to_notify.append(row)

			# Only check for email flag if task exists
			if row.task:
				send_mail_for_row = frappe.db.get_value(
					"Task", row.task, "send_email_notification_for_lag_time"
				)
				if send_mail_for_row:
					lag_rows_to_mail.append(row)

	if not lag_rows_to_notify:
		return

	role = frappe.db.get_single_value(
		"Compliance Settings", "role_allowed_to_approve_lag_time"
	)
	if not role:
		frappe.log_error(
			"Compliance Setting is missing a notification_role", "Lag Notification"
		)
		return

	users = frappe.get_all(
		"Has Role", filters={"role": role, "parenttype": "User"}, fields=["parent"]
	)

	user_emails = []
	for u in users:
		user = frappe.db.get_value(
			"User", u["parent"], ["email", "enabled"], as_dict=True
		)
		if user and user.enabled and user.email:
			user_emails.append(user.email)

	if not user_emails:
		frappe.log_error(f"No enabled users found with role {role}", "Lag Notification")
		return

	subject = f"Lag Time Detected in Timesheet {doc.name}"
	message = f"""
		<p><strong>{len(lag_rows_to_notify)}</strong> lag entry(ies) detected in Timesheet <strong>{doc.name}</strong> for Employee <strong>{doc.employee}</strong>.</p>
		<ul>
			{''.join([f"<li>{r.activity_type or 'Activity'}: {r.lag_time}</li>" for r in lag_rows_to_notify])}
		</ul>
		<p>Please review them in the system.</p>
	"""

	try:
		for recipient in user_emails:
			create_notification_log(
				subject, "Alert", recipient, message, doc.doctype, doc.name
			)
	except Exception as e:
		frappe.log_error(f"Failed to send lag notification: {e}", "Lag Notification")

	# Mark all notified rows as processed
	for row in lag_rows_to_notify:
		frappe.db.set_value("Timesheet Detail", row.name, "lag_notification_sent", 1)

	# Send email only for rows with tasks that have email notification enabled
	if not lag_rows_to_mail:
		return

	email_content = f"""
		<p><strong>{len(lag_rows_to_mail)}</strong> lag entry(ies) detected in Timesheet <strong>{doc.name}</strong> for Employee <strong>{doc.employee}</strong>.</p>
		<ul>
			{''.join([f"<li>{r.activity_type or 'Activity'}: {r.lag_time}</li>" for r in lag_rows_to_mail])}
		</ul>
		<p>Please review them in the system.</p>
	"""

	try:
		frappe.sendmail(recipients=user_emails, subject=subject, message=email_content)
	except Exception as e:
		frappe.log_error(f"Failed to send lag email: {e}", "Lag Email")
