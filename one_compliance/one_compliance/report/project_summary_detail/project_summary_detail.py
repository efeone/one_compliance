#  Copyright (c) 2025, efeone and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data

def get_columns():
    return [
        {
            "label": _("Reference Type"),
            "fieldname": "reference_type",
            "fieldtype": "Data",
            "width": 150
        },
        {
            "label": _("Project"),
            "fieldname": "project",
            "fieldtype": "Link",
            "options": "Project",
            "width": 200
        },
        {
            "label": _("Department"),
            "fieldname": "department",
            "fieldtype": "Link",
            "options": 'Department',
            "width": 200
        },
        {
            "label": _("Customer"),
            "fieldname": "client",
            "fieldtype": "Link",
            "options": "Customer",
            "width": 200
        },
        {
            "label": _("Status"),
            "fieldname": "status",
            "fieldtype": "Data",
            "width": 100
        },
        {
            "label": _("Project End Date"),
            "fieldname": "end_date",
            "fieldtype": "Date",
            "width": 130
        },
        {
            "label": _("Assigned To"),
            "fieldname": "employees",
            "fieldtype": "Data",
            "width": 150
        },
        {
            "label": _("Progress"),
            "fieldname": "progress",
            "fieldtype": "Percent",
            "width": 150
        },
        {
            "label": _("Pending Tasks"),
            "fieldname": "pending_task",
            "fieldtype": "Int",
            "width": 150
        },
        {
            "label": _("Completed Tasks"),
            "fieldname": "completed_task",
            "fieldtype": "Int",
            "width": 150
        },
        {
            "label": _("Overdue Tasks"),
            "fieldname": "overdue_task",
            "fieldtype": "Int",
            "width": 150
        },
        {
            "label": _("Invoiced"),
            "fieldname": "invoiced",
            "fieldtype": "Data",
            "width": 100
        },
        {
            "label": _("Invoice Amount"),
            "fieldname": "invoice_amount",
            "fieldtype": "Currency",
            "width": 150
        },
        {
            "label": _("Payment Received"),
            "fieldname": "payment_received",
            "fieldtype": "Data",
            "width": 130
        },
        {
            "label": _("Outstanding Amount"),
            "fieldname": "outstanding_amount",
            "fieldtype": "Currency",
            "width": 150
        }
    ]

def get_data(filters):
    try:
        if not filters:
            filters = {}

        ref_type = filters.get("reference_type")

        # Show both if reference_type is empty
        include_projects = not ref_type or ref_type == "Project"
        include_events = not ref_type or ref_type == "Event"

        data = []
        if include_projects:
            data.extend(get_project_data(filters))
        if include_events:
            data.extend(get_event_data(filters))

        return data
    except Exception as e:
        frappe.log_error(f"Error in get_data function: {e}")
        return []

def get_project_data(filters):
    employee_user_id = frappe.db.get_value("Employee", filters.get("employee"), "user_id") if filters.get("employee") else None

    # Remove department from server-side filter
    project_filters = {}
    if filters.get("project"):
        project_filters["name"] = filters["project"]
    if filters.get("client"):
        project_filters["customer"] = filters["client"]
    if filters.get("status"):
        project_filters["status"] = filters["status"]

    projects = frappe.get_all(
        "Project",
        fields=["name", "project_name", "customer", "status", "expected_end_date", "department", "percent_complete"],
        filters=project_filters
    )

    # ✅ Apply department filter manually (so that valid ones are kept, and missing ones ignored)
    if filters.get("department"):
        projects = [p for p in projects if p.department == filters["department"]]

    data = []
    for p in projects:
        if employee_user_id:
            assigned_users = frappe.get_all(
                "ToDo",
                filters={
                    "reference_type": "Project",
                    "reference_name": p.name,
                    "status": "Open"
                },
                fields=["owner"]
            )
            assigned_user_ids = {todo.owner for todo in assigned_users}
            if employee_user_id not in assigned_user_ids:
                continue

        employees = get_project_employees(p.name)
        sales_order = frappe.db.get_value("Sales Order", {"project": p.name}, "name")
        inv_data = get_invoice_details(sales_order) if sales_order else {}

        pending_task = frappe.db.count("Task", {"project": p.name, "status": "Open"})
        completed_task = frappe.db.count("Task", {"project": p.name, "status": "Completed"})
        overdue_task = frappe.db.count("Task", {"project": p.name, "status": "Overdue"})

        data.append({
            "reference_type": "Project",
            "department": p.department or "N/A",
            "project": p.name,
            "project_name": p.project_name or p.name,
            "client": p.customer,
            "status": p.status,
            "end_date": p.expected_end_date,
            "employees": ", ".join(employees) if employees else "-",
            "progress": flt(p.percent_complete, 2),
            "pending_task": pending_task,
            "completed_task": completed_task,
            "overdue_task": overdue_task,
            "invoiced": "Yes" if inv_data.get("grand_total") else "No",
            "invoice_amount": inv_data.get("grand_total", 0),
            "payment_received": "Yes" if flt(inv_data.get("grand_total")) > 0 and flt(inv_data.get("outstanding")) == 0 else "No",
            "outstanding_amount": inv_data.get("outstanding", 0)
        })

    return data


def get_event_data(filters):
    event_filters = {"event_type": "Public"}

    if filters.get("client"):
        event_filters["custom_customer"] = filters["client"]

    if filters.get("status"):
        event_filters["status"] = filters["status"]

    if filters.get("project"):
        event_filters["name"] = filters["project"]

    if filters.get("reference_type") == "Event" and filters.get("department"):
        event_filters["custom_department"] = filters["department"]


    employee_user_id = frappe.db.get_value("Employee", filters.get("employee"), "user_id") if filters.get("employee") else None

    events = frappe.db.get_all(
        "Event",
        fields=["name", "starts_on", "status", "subject", "custom_customer", "custom_service"],
        filters=event_filters
    )

    data = []
    for e in events:
        if employee_user_id:
            assigned_users = frappe.get_all(
                "ToDo",
                filters={
                    "reference_type": "Event",
                    "reference_name": e.name,
                    "status": "Open"
                },
                fields=["owner"]
            )
            assigned_user_ids = {todo.owner for todo in assigned_users}
            if employee_user_id not in assigned_user_ids:
                continue

        data.append({
            "reference_type": "Event",
            "department": filters.get("department") or "N/A",
            "project": e.name,
            "project_name": e.subject,
            "client": e.custom_customer,
            "status": e.status,
            "end_date": e.starts_on,
            "employees": "-",
            "progress": 0,
            "pending_task": 0,
            "completed_task": 0,
            "overdue_task": 0,
            "invoiced": "",
            "invoice_amount": 0,
            "payment_received": "",
            "outstanding_amount": 0
        })

    return data

# 👇 This function no longer filters department — it's applied later
def build_project_filters(filters):
    project_filters = {}

    if filters.get("project"):
        project_filters["name"] = filters["project"]

    if filters.get("client"):
        project_filters["customer"] = filters["client"]

    if filters.get("status"):
        project_filters["status"] = filters["status"]

    return project_filters

def get_project_employees(project_name):
    employee_set = set()

    assigned_todos = frappe.get_all(
        "ToDo",
        filters={
            "reference_type": "Project",
            "reference_name": project_name,
            "status": "Open"
        },
        fields=["owner"]
    )

    for todo in assigned_todos:
        user_id = todo.owner
        employee_name = frappe.db.get_value("Employee", {"user_id": user_id}, "employee_name")
        if employee_name:
            employee_set.add(employee_name)

    return list(employee_set)

def get_invoice_details(sales_order_name):
    if not sales_order_name:
        return {}

    result = frappe.db.sql("""
        SELECT
            SUM(si.grand_total) AS grand_total,
            SUM(si.outstanding_amount) AS outstanding
        FROM `tabSales Invoice` si
        JOIN `tabSales Invoice Item` sii ON si.name = sii.parent
        WHERE sii.sales_order = %s AND si.docstatus = 1
    """, (sales_order_name,), as_dict=True)

    return result[0] if result else {}
