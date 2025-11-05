import frappe
from frappe.utils import getdate, nowdate, today


@frappe.whitelist()
def get_available_employees_today():
    checkins = frappe.db.get_all(
        "Employee Checkin",
        filters={
            "log_type": "IN",
            "time": [">=", today()]
        },
        fields=["distinct employee", "employee_name"]
    )

    return len(checkins)


@frappe.whitelist()
def get_employees_on_leave_today():

    leave_application = frappe.db.get_all(
		"Leave Application",
		filters={
			"status": "Approved",
			"from_date": ["<=", today()],
			"to_date": [">=", today()]
		},
		fields = ["employee"]
	)

    return len(leave_application)


@frappe.whitelist()
def get_work_from_home_employees_today():

    today_date = today()

    # Fetch Attendance Requests for "Work From Home" covering today's date
    requests = frappe.db.get_all(
        "Attendance Request",
        filters={
            "reason": "Work From Home",
            "from_date": ["<=", today_date],
            "to_date": [">=", today_date],
        },
        fields=["employee", "employee_name"]
    )

    return len(requests)

@frappe.whitelist()
def get_on_duty_employees_today():

    today_date = today()

    requests = frappe.db.get_all(
        "Attendance Request",
        filters={
            "reason": "On Duty",
            "from_date": ["<=", today_date],
            "to_date": [">=", today_date],
        },
        fields=["employee", "employee_name"]
    )

    return len(requests)

@frappe.whitelist()
def get_all_employees_with_status():

    today_date = today()

    employees = frappe.get_all(
        "Employee",
        filters={"status": "Active"},
        fields=["name", "employee_name", "designation", "user_id"]
    )

    checkins = frappe.get_all(
        "Employee Checkin",
        filters={
            "log_type": "IN",
            "time": ["between", [today_date + " 00:00:00", today_date + " 23:59:59"]]
        },
        pluck="employee"
    )
    leave = frappe.get_all(
        "Leave Application",
        filters={
            "status": "Approved",
            "from_date": ["<=", today_date],
            "to_date": [">=", today_date]
        },
        pluck="employee"
    )

    wfh = frappe.get_all(
        "Attendance Request",
        filters={
            "reason": "Work From Home",
            "from_date": ["<=", today_date],
            "to_date": [">=", today_date]
        },
        pluck="employee"
    )
    on_duty = frappe.get_all(
        "Attendance Request",
        filters={
            "reason": "On Duty",
            "from_date": ["<=", today_date],
            "to_date": [">=", today_date]
        },
        pluck="employee"
    )
    available = set(checkins)
    on_leave = set(leave)
    work_from_home = set(wfh)
    on_duty_set = set(on_duty)

    final = []
    for emp in employees:
        status = "unavailable"

        if emp.name in on_leave:
            status = "on_leave"
        elif emp.name in work_from_home:
            status = "work_from_home"
        elif emp.name in on_duty_set:
            status = "on_duty"
        elif emp.name in available:
            status = "available"

        task_weightages = frappe.get_all(
            "Task",
            filters={
                "assigned_to": emp.user_id,
                "exp_start_date": ["<=", today_date],
                "exp_end_date": [">=", today_date]
            },
            pluck="task_weightage"
        )

        final.append({
            "employee": emp.name,
            "employee_name": emp.employee_name,
            "designation": emp.designation,
            "status": status,
            "email": emp.user_id,
            "task_weightages": task_weightages,
            "total_task_weightage": sum([float(t) for t in task_weightages if t])
        })

    return final

@frappe.whitelist()
def get_employee_tasks_today(employee_id=None):
    """
    Get tasks for an employee that are either starting or ending today.
    """

    if not employee_id:
        employee_id = frappe.form_dict.get('employee_id')

    if not employee_id:
        frappe.throw("Employee ID is required")

    try:
        today_date = today()

        tasks = frappe.db.get_list(
            'Task',
            filters={
                'assigned_to': employee_id,
                'status': ['not in', ['Completed', 'Cancelled', 'Template']]
            },
            fields=[
                'name',
                'subject',
                'status',
                'priority',
                'project',
                'project_name',
                'category_type',
                'type',
                'compliance_sub_category',
                'exp_start_date',
                'exp_end_date',
                'task_weightage'
            ],
            order_by='priority ASC, exp_end_date ASC'
        )

        return tasks

    except Exception as e:
        frappe.log_error(f"Error fetching today's tasks for employee {employee_id}: {e}")
        return []