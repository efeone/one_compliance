# Copyright (c) 2025, efeone and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from datetime import timedelta


class WeeklyWorkSheet(Document):
	pass



def create_or_update_weekly_work_sheet(doc, method):
    # Fetch the employee from the timesheet
    employee = doc.employee

    # Get AJS Settings
    ajs_settings = get_ajs_settings()
    weekly_working_days = ajs_settings.weekly_working_days  # Number of working days per week
    week_start_day = ajs_settings.week_start_day  # The day the week starts (e.g., Monday)

    # Fetch the existing Weekly Work Sheet based on the employee and dates
    weekly_work_sheet = frappe.get_all('Weekly Work Sheet', filters={
        'employee': employee,
        'week_start_date': doc.start_date,
        'week_end_date': doc.end_date
    }, limit=1)

    if weekly_work_sheet:
        # If the Weekly Work Sheet exists, fetch it for update
        weekly_work_sheet = frappe.get_doc('Weekly Work Sheet', weekly_work_sheet[0].name)
    else:
        # If no Weekly Work Sheet exists, create a new one
        weekly_work_sheet = frappe.new_doc('Weekly Work Sheet')
        weekly_work_sheet.employee = employee
        weekly_work_sheet.week_start_date = doc.start_date
        weekly_work_sheet.week_end_date = doc.end_date

    # Calculate the start and end date based on Week Start Day
    week_start_date_adjusted = adjust_week_start_date(doc.start_date, week_start_day)

    # Initialize variables to calculate total hours
    total_actual_hours = 0
    total_task_allowed_hours = 0

    # Loop through the time_logs child table to calculate actual and task allowed hours
    for row in doc.time_logs:
        total_actual_hours += row.hrs or 0
        total_task_allowed_hours += row.expected_hours or 0

        # Add work log details to the Weekly Work Sheet
        weekly_work_sheet.append('work_log_details', {
            'task': row.activity_type,  # Or map this to an appropriate field in your Weekly Work Sheet
            'task_description': row.activity_type,  # Modify as per your data structure
            'actuall_hours': row.hrs,
            'task_allowed_hours': row.expected_hours,
            'status': 'Completed'  # You can set the status based on your conditions
        })

    # Set the total values in the Weekly Work Sheet
    weekly_work_sheet.total_actuall_hours = total_actual_hours
    weekly_work_sheet.total_task_allowed_hours = total_task_allowed_hours

    # Adjust weekly dates based on the AJS settings
    weekly_work_sheet.week_start_date = week_start_date_adjusted
    weekly_work_sheet.week_end_date = week_start_date_adjusted + timedelta(days=weekly_working_days - 1)

    # Save the Weekly Work Sheet
    weekly_work_sheet.save()
    frappe.db.commit()

def adjust_week_start_date(start_date, week_start_day):
    """
    Adjust the start date based on the 'week_start_day' field from AJS Settings.
    """
    from datetime import datetime

    # Parse the start date and find out which day of the week it is
    start_date_obj = datetime.strptime(str(start_date), "%Y-%m-%d")
    current_day = start_date_obj.weekday()  # Monday is 0 and Sunday is 6

    # Find how many days to subtract to get to the 'week_start_day'
    days_to_subtract = (current_day - week_start_day) % 7

    # Adjust the start date
    adjusted_start_date = start_date_obj - timedelta(days=days_to_subtract)
    return adjusted_start_date.date()  # Return as date (YYYY-MM-DD)
