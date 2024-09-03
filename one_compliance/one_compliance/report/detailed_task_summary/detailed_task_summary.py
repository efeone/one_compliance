# Copyright (c) 2024, efeone and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import getdate

def execute(filters=None):
    columns = get_columns(filters)
    data = get_data(filters)
    chart = get_chart_data(data)
    return columns, data, None, chart

def get_columns(filters=None):
    columns = [
        {"label": _("Department"), "fieldname": "department", "fieldtype": "Link", "options": 'Department', "width": 200},
        {"label": _("Customer"), "fieldname": "customer", "fieldtype": "Link", "options": 'Customer', "width": 200},
        {"label": _("Project"), "fieldname": "project", "fieldtype": "Link", "options": 'Project', "width": 400},
        {"label": _("Project Name"), "fieldname": "project_name", "fieldtype": "Data", "width": 100, "hidden": 1},
        {"label": _("Project Status"), "fieldname": "project_status", "fieldtype": "Data", "width": 150},
        {"label": _("Invoiced"),"fieldname": "invoiced","fieldtype": "Data","width": 150},
        {"label": _("Task"), "fieldname": "task", "fieldtype": "Link", "options": 'Task', "width": 150},
        {"label": _("Task Status"), "fieldname": "task_status", "fieldtype": "Data", "width": 150},
        {"label": _("Completed By"), "fieldname": "completed_by", "fieldtype": "Data", "width": 150},
        {"label": _("Open Tasks"), "fieldname": "open_tasks", "fieldtype": "Int", "width": 150, "hidden": 1},
        {"label": _("Pending Tasks"), "fieldname": "pending_task", "fieldtype": "Int", "width": 150, "hidden": 1},
        {"label": _("Completed Tasks"), "fieldname": "completed_task", "fieldtype": "Int", "width": 150, "hidden": 1},
        {"label": _("Overdue Tasks"), "fieldname": "overdue_task", "fieldtype": "Int", "width": 150, "hidden": 1},
    ]
    return columns

def get_data(filters):
    data = []
    departments = []
    try:
        if filters.get('department'):
            department_name = filters.get('department')
            if frappe.db.exists('Department', department_name):
                departments.append(department_name)
        else:
            departments = frappe.db.get_all('Department', {'is_group': 0, 'is_compliance': 1}, pluck='name')

        data = prepare_data(departments, filters)
    except Exception as e:
        frappe.log_error(f"Error in get_data function: {e}")

    return data

def get_project_count_based_on_status(project, status):
    count = 0
    available_statuses = ['Overdue', 'Completed']
    if status == 'Pending':
        count = frappe.db.count('Task', {
            'project': project,
            'status': ['in', ['Open', 'Working', 'Pending Review', 'Hold']]
        })
    elif status in available_statuses:
        count = frappe.db.count('Task', {'project': project, 'status': status})
    return count

def is_invoiced_or_not(project):
	'''
		Method to check wether the project is invoiced or not
		Submitted Sales Invoice with Project link in accounting Dimensions
		Return Yes or No
	'''
	invoiced = 'No'
	if frappe.db.exists('Sales Invoice', { 'project':project, 'docstatus':1 }):
		invoiced = 'Yes'
	return invoiced

def prepare_data(departments, filters):
    data = []

    for department in departments:
        try:
            projects = frappe.db.get_all('Project', {
                'department': department,
                'expected_start_date': ['between', [getdate(filters.get('from_date')), getdate(filters.get('to_date'))]]
            }, pluck='name')

            for project in projects:
                tasks = frappe.db.get_all('Task', {'project': project}, pluck='name')
                project_doc = frappe.get_doc('Project', project)

                if not tasks:
                    continue

                total_pending_tasks = get_project_count_based_on_status(project, 'Pending')
                total_completed_tasks = get_project_count_based_on_status(project, 'Completed')
                total_overdue_tasks = get_project_count_based_on_status(project, 'Overdue')

                project_row = {
                    'department': department,
                    'customer': project_doc.customer,
                    'project': project_doc.name,
                    'project_name': project_doc.project_name,
                    'project_status': project_doc.status,
                    'invoiced': is_invoiced_or_not(project),
                    'open_tasks': get_project_count_based_on_status(project, 'Open'),
                    'pending_task': total_pending_tasks,
                    'completed_task': total_completed_tasks,
                    'overdue_task': total_overdue_tasks,
                    'task': '',
                    'task_status': '',
                    'completed_by': ''
                }
                data.append(project_row)

                for task in tasks:
                    task_doc = frappe.get_doc('Task', task)
                    task_row = {
                        'department': '',
                        'customer': '',
                        'project': '',
                        'project_name': '',
                        'project_status': '',
                        'open_tasks': '',
                        'pending_task': '',
                        'completed_task': '',
                        'overdue_task': '',
                        'task': task_doc.name,
                        'task_status': task_doc.status,
                        'completed_by': task_doc.completed_by
                    }
                    data.append(task_row)

        except Exception as e:
            frappe.log_error(f"Error processing department '{department}': {e}")

    return data

def get_chart_data(data):
    labels = []
    open_tasks = []
    pending_tasks = []
    completed_tasks = []
    overdue_tasks = []

    for row in data:
        if row.get('project') and not row.get('task'):
            labels.append(row.get('department'))
            open_tasks.append(row.get('open_tasks'))
            pending_tasks.append(row.get('pending_task'))
            completed_tasks.append(row.get('completed_task'))
            overdue_tasks.append(row.get('overdue_task'))

    return {
        "data": {
            "labels": labels[:30],
            "datasets": [
                {"name": _("Open Task"), "values": open_tasks[:30]},
                {"name": _("Pending Task"), "values": pending_tasks[:30]},
                {"name": _("Completed Task"), "values": completed_tasks[:30]},
                {"name": _("Overdue Task"), "values": overdue_tasks[:30]},
            ],
        },
        "type": "line",
        "colors": ["#FFFF00", "#fc4f51", "#29cd42", "#7575ff"],
        "barOptions": {"stacked": True},
    }
