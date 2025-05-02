# Copyright (c) 2025, efeone and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import getdate, add_days

class WeeklyWorkSheet(Document):
    pass

@frappe.whitelist()
def get_work_log_data(week_start_date, employee):
    from collections import defaultdict

    settings = frappe.get_single("AJS Settings")
    weekly_working_days = int(settings.weekly_working_days or 7)

    week_start = getdate(week_start_date)
    week_end = add_days(week_start, weekly_working_days - 1)

    timesheets = frappe.get_all(
        "Timesheet",
        filters={
            "employee": employee,
            "start_date": ["<=", week_end],
            "end_date": [">=", week_start]
        },
        fields=["name"]
    )

    task_log_map = defaultdict(lambda: {
        "task": "",
        "task_description": "",
        "actuall_hours": 0.0,
        "task_allowed_hours": 0.0,
        "log_date": None,
        "status": ""
    })

    for ts in timesheets:
        timesheet = frappe.get_doc("Timesheet", ts.name)

        for log in timesheet.time_logs:
            if not log.task:
                continue

            task = log.task
            entry = task_log_map[task]

            entry["task"] = task
            entry["task_description"] = log.description or entry["task_description"]
            entry["actuall_hours"] += log.hours or 0.0

            if not entry["task_allowed_hours"]:
                entry["task_allowed_hours"] = get_task_allowed_hours(task)
            if not entry["log_date"]:
                entry["log_date"] = log.from_time.date() if log.from_time else week_start
            if not entry["status"]:
                entry["status"] = frappe.db.get_value("Task", task, "status") or "Unknown"

    work_log_details = list(task_log_map.values())
    total_actuall_hours = sum(row["actuall_hours"] for row in work_log_details)
    total_task_allowed_hours = sum(row["task_allowed_hours"] for row in work_log_details)

    return {
        "work_log_details": work_log_details,
        "total_actuall_hours": total_actuall_hours,
        "total_task_allowed_hours": total_task_allowed_hours,
        "week_end_date": week_end
    }

def get_task_allowed_hours(task):
    # Get the project from the Task
    project = frappe.db.get_value("Task", task, "project")
    if not project:
        return 0.0

    # Get the project template from the Project
    template = frappe.db.get_value("Project", project, "project_template")
    if not template:
        return 0.0

    # Get the allowed hours from Project Template Task
    allowed_hours = frappe.db.get_value(
        "Project Template Task",
        {"parent": template, "task": task},
        "custom_task_duration"
    )

    return float(allowed_hours or 0.0)
