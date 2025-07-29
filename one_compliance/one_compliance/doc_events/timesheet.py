import frappe



def check_lag_and_notify(doc, method=None):
    """
    Sent notification if Lag time found in timesheet 
    """
    
    lag_rows_to_notify = []

    for row in doc.time_logs:
        if row.lag_time and not row.lag_notification_sent:
            lag_rows_to_notify.append(row)

    print(f"Found lag rows: {lag_rows_to_notify}")

    if not lag_rows_to_notify:
        print("No lag rows needing notification.")
        return

    role = frappe.db.get_single_value("Compliance Settings", "role_allowed_to_approve_lag_time")
    print(f"Compliance role: {role}")

    if not role:
        frappe.log_error("Compliance Setting is missing a notification_role", "Lag Notification")
        return

    users = frappe.get_all(
        "Has Role",
        filters={"role": role, "parenttype": "User"},
        fields=["parent"]
    )
    user_emails = []
    for u in users:
        user = frappe.db.get_value("User", u["parent"], ["email", "enabled"], as_dict=True)
        if user and user.enabled and user.email:
            user_emails.append(user.email)

    print(f"User emails to notify: {user_emails}")

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

    print(f"Subject: {subject}")
    print(f"Message: {message}")

    try:
        frappe.sendmail(
            recipients=user_emails,
            subject=subject,
            message=message
        )
        print("Notification sent successfully!")
    except Exception as e:
        frappe.log_error(f"Failed to send lag notification: {e}", "Lag Notification")
        print(f"Failed to send email: {e}")
        return

    for row in lag_rows_to_notify:
        frappe.db.set_value("Timesheet Detail", row.name, "lag_notification_sent", 1)
        print(f"Marked notification sent for row: {row.name}")

