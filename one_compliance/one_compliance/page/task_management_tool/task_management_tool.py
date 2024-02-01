import frappe
from frappe.utils import get_datetime

@frappe.whitelist()
def get_task(status = None, task = None, project = None, customer = None, department = None, sub_category = None, employee = None, employee_group = None, from_date = None, to_date = None):

    user_id = f'"{employee}"' if id else None

    query = """
	SELECT
        t.name,t.project,t.subject, t.project_name, t.customer, c.department, t.compliance_sub_category, t.exp_start_date, t.exp_end_date, t._assign, t.status, t.assigned_to, t.completed_by, t.color
    FROM
        tabTask t JOIN `tabCompliance Sub Category` c ON t.compliance_sub_category = c.name
    """

    if status:
            query += f" WHERE t.status = '{status}'"

    if task:
            query += f" AND t.name = '{task}'"

    if project:
            query += f" AND t.project = '{project}'"

    if customer:
            query += f" AND t.customer = '{customer}'"

    if department:
            query += f" AND c.department = '{department}'"

    if sub_category:
            query += f" AND t.compliance_sub_category = '{sub_category}'"

    if employee:
            query += f" AND JSON_CONTAINS(t._assign, '{user_id}', '$')"

    if employee_group:
            query += f" AND t.assigned_to = '{employee_group}'"

    if from_date:
            query += f" AND t.exp_start_date >= '{from_date}'"

    if to_date:
            query += f" AND t.exp_end_date < '{to_date}'"

    query += """ORDER BY
            t.modified DESC;"""

    task_list = frappe.db.sql(query, as_dict=1)
    for task in task_list:
        task['employee_names'] = []
        if task['_assign']:
            user_ids = frappe.parse_json(task['_assign'])

            if user_ids:
                user_names_query = """
                    SELECT name, employee_name, user_id FROM `tabEmployee`
                    WHERE user_id IN ({})
                """.format(', '.join(['%s' for _ in user_ids]))

                user_names = frappe.db.sql(user_names_query, tuple(user_ids), as_dict=True)
                task['_assign'] = [{'employee_name': user['employee_name'], 'employee_id': user['name']} for user in user_names]
                task['employee_names'] = [user['employee_name'] for user in user_names]
            else:
                task['_assign'] = []
                task['employee_names'] = []
        else:
            task['_assign'] = []
            task['employee_names'] = []

        if task['completed_by']:
            if task['completed_by'] == 'Administrator':
                task['completed_by_name'] = 'Administrator'
            else:
                completed_by = frappe.get_value("Employee", {"user_id": task['completed_by']}, ["name", "employee_name"], as_dict=True)
                task['completed_by_name'] = completed_by["employee_name"]
                task['completed_by_id'] = completed_by["name"]
        else:
            task['completed_by_name'] = []
            task['completed_by_id'] = []

        task['is_payable'] = check_payable_task(task['subject'])
    return task_list

@frappe.whitelist()
def check_payable_task(task):
    query = f"""
    SELECT custom_is_payable FROM `tabTask` WHERE subject = '{task}' AND status = 'Template';
    """
    result = frappe.db.sql(query, as_dict=True)
    return result[0]['custom_is_payable'] if result else None

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

@frappe.whitelist()
def update_task_status(task, project, status):
    task_doc = frappe.get_doc("Task", {"name":task,"project":project})

    task_doc.status = status

    task_doc.save()
    return "success"
