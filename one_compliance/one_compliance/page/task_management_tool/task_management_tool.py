import frappe
from frappe.utils import get_datetime

@frappe.whitelist()
def get_task():
    query = """
	SELECT
        t.name,t.project,t.subject, t.project_name, t.customer, c.compliance_category, t.compliance_sub_category, t.exp_start_date, t.exp_end_date, t._assign, t.status
    FROM
        tabTask t JOIN `tabCompliance Sub Category` c ON t.compliance_sub_category = c.name;"""
    task_list = frappe.db.sql(query, as_dict=1)
    for task in task_list:
        if task['_assign']:
            user_ids = frappe.parse_json(task['_assign'])
            user_names = []

            for user_id in user_ids:
                user_doc = frappe.get_doc('User', user_id)
                user_names.append(user_doc.full_name if user_doc else user_id)

            task['_assign'] = user_names
        else:
            task['_assign'] = []
    return task_list

@frappe.whitelist()
def create_timesheet(project, task, employee, activity, from_time, to_time):

    from_time = get_datetime(from_time)
    to_time = get_datetime(to_time)
    employee_id = frappe.get_value("Employee", {"employee_name": employee}, "name")
    print(project,task,employee_id,from_time,to_time)

    # Check if a timesheet already exists for the employee within the given date range
    existing_timesheets = frappe.get_all("Timesheet", filters={
        "employee": employee_id,
        "start_date": from_time.date(),
        "end_date": to_time.date(),
    })

    if existing_timesheets:
        existing_timesheet = frappe.get_doc("Timesheet", existing_timesheets)
        existing_timesheet.append("time_logs",{
            "activity_type": activity,
            "project": project,
            "task": task,
            "from_time": from_time,
            "to_time": to_time
        })
        existing_timesheet.save()
        frappe.db.commit()
    else:
        timesheet = frappe.new_doc("Timesheet")
        timesheet.employee = employee_id
        timesheet.append("time_logs",{
            "activity_type": activity,
            "project": project,
            "task": task,
            "from_time": from_time,
            "to_time": to_time
        })

        timesheet.insert(ignore_permissions=True)
        frappe.db.commit()
