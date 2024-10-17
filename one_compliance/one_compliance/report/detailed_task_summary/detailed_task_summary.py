# Copyright (c) 2024, efeone and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import get_datetime, has_common


def execute(filters=None):
    """
    Main function to execute the report logic.
    Fetches columns and data based on the provided filters.

    Args:
    filters (dict): Dictionary of filters applied by the user.

    Returns:
    tuple: columns and data for the report.
    """
    columns = get_columns()
    data = get_data(filters)
    return columns, data


def get_columns():
    """
    Defines the structure of the report columns.

    Returns:
    list: List of dictionaries representing column metadata.
    """
    return [
        {
            "label": _("Reference Type"),
            "fieldname": "reference_type",
            "fieldtype": "Data",
            "width": 150,
        },
        {
            "label": _("Reference Name"),
            "fieldname": "id",
            "fieldtype": "Data",
            "width": 175,
        },
        {
            "label": _("Subject"),
            "fieldname": "description",
            "fieldtype": "Data",
            "width": 300,
        },
        {"label": _("Date"), "fieldname": "date", "fieldtype": "Date", "width": 150},
        {
            "label": _("Customer"),
            "fieldname": "client",
            "fieldtype": "Link",
            "options": "Customer",
            "width": 225,
        },
        {
            "label": _("Project"),
            "fieldname": "project",
            "fieldtype": "Link",
            "options": "Project",
            "width": 150,
        },
        {
            "label": _("Department"),
            "fieldname": "department",
            "fieldtype": "Link",
            "options": "Department",
            "width": 200,
        },
        {
            "label": _("Sub Category"),
            "fieldname": "sub_category",
            "fieldtype": "Link",
            "options": "Compliance Sub Category",
            "width": 250,
        },
        {
            "label": _("Employee"),
            "fieldname": "employee",
            "fieldtype": "Data",
            "width": 150,
        },
        {
            "label": _("Status"),
            "fieldname": "status",
            "fieldtype": "Data",
            "width": 150,
        },
        {
            "label": _("Invoiced"),
            "fieldname": "invoiced",
            "fieldtype": "Data",
            "width": 150,
        },
        {
            "label": _("Billing Date"),
            "fieldname": "billing_date",
            "fieldtype": "Date",
            "width": 150,
        },
        {
            "label": _("Invoiced Amount"),
            "fieldname": "invoice_amount",
            "fieldtype": "Data",
            "width": 150,
        },
        {
            "label": _("Payment Received"),
            "fieldname": "payment_received",
            "fieldtype": "Data",
            "width": 150,
        },
        {
            "label": _("Outstanding Amount"),
            "fieldname": "outstanding_amount",
            "fieldtype": "Data",
            "width": 150,
        },
    ]


def get_data(filters):
    """
    Retrieves the report data by fetching tasks and events based on filters.
    Combines tasks and events into one list.

    Args:
    filters (dict): Dictionary of filters applied by the user.

    Returns:
    list: List of combined tasks and events.
    """
    try:
        if filters.get("reference_type") == "Task" or filters.get("project"):
            task_filters = build_task_filters(filters)
            tasks = fetch_tasks(task_filters, filters)
            return tasks
        elif filters.get("reference_type") == "Event":
            event_filters = build_event_filters(filters)
            events = fetch_events(event_filters, filters)
            return events

        task_filters = build_task_filters(filters)
        event_filters = build_event_filters(filters)
        tasks = fetch_tasks(task_filters, filters)
        events = fetch_events(event_filters, filters)
        data = tasks + events
        return sorted(data, key=lambda x: x["date"], reverse=True)
    except Exception as e:
        frappe.log_error(f"Error in get_data function: {e}")
        return []


def build_task_filters(filters):
    """
    Builds a filter dictionary for fetching tasks based on user input.

    Args:
    filters (dict): Dictionary of filters applied by the user.

    Returns:
    dict: Dictionary of task filters.
    """
    task_filters = {"status": ["!=", "Template"]}

    if filters.get("client"):
        task_filters["customer"] = filters["client"]

    if filters.get("from_date") or filters.get("to_date"):
        task_filters["creation"] = build_date_range_filter(filters)

    if filters.get("status"):
        task_filters["status"] = filters["status"]

    if filters.get("sub_category"):
        task_filters["compliance_sub_category"] = filters.get("sub_category")

    if filters.get("project"):
        task_filters["project"] = filters.get("project")

    return task_filters


def build_event_filters(filters):
    """
    Builds a query string for fetching events based on user input.

    Args:
    filters (dict): Dictionary of filters applied by the user.

    Returns:
    str: SQL query conditions as a string for filtering events.
    """
    query = ""

    if filters.get("client"):
        query += f" AND e.custom_customer = '{filters.get('client')}'"

    if filters.get("from_date") or filters.get("to_date"):
        query += build_date_query(filters)

    if filters.get("status"):
        query += f" AND status = '{filters['status']}'"

    if filters.get("sub_category"):
        query += f" AND e.custom_service = '{filters.get('sub_category')}'"

    return query


def build_date_range_filter(filters):
    """
    Builds a date range filter for tasks based on 'from_date' and 'to_date' values.

    Args:
    filters (dict): Dictionary of filters applied by the user.

    Returns:
    list: List containing the filter condition for the creation date range.
    """
    from_date, to_date = filters.get("from_date"), filters.get("to_date")

    if from_date and to_date:
        return ["between", [get_datetime(from_date), get_datetime(to_date)]]
    elif from_date:
        return [">=", get_datetime(from_date)]
    elif to_date:
        return ["<=", get_datetime(to_date)]

    return None


def build_date_query(filters):
    """
    Builds a date range query for events based on 'from_date' and 'to_date' values.

    Args:
    filters (dict): Dictionary of filters applied by the user.

    Returns:
    str: SQL condition for filtering events based on date range.
    """
    from_date, to_date = filters.get("from_date"), filters.get("to_date")

    if from_date and to_date:
        return f" AND e.starts_on BETWEEN '{from_date}' AND '{to_date}'"
    elif from_date:
        return f" AND e.starts_on >= '{from_date}'"
    elif to_date:
        return f" AND e.starts_on <= '{to_date}'"

    return ""


def fetch_tasks(task_filters, filters):
    """
    Fetches tasks based on task filters and processes employee data.

    Args:
    task_filters (dict): Dictionary of task filters.
    filters (dict): Dictionary of filters applied by the user.

    Returns:
    list: List of processed tasks with employee data.
    """
    tasks = frappe.db.get_all(
        "Task",
        filters=task_filters,
        fields=[
            "name as id",
            "creation as date",
            "customer as client",
            "subject as description",
            "status",
            "assigned_to",
            "completed_by",
            "compliance_sub_category as sub_category",
            "project",
        ],
    )
    return process_employee_data(tasks, filters, "task")


def fetch_events(event_filters, filters):
    """
    Fetches events based on event filters and processes employee data.

    Args:
    event_filters (str): Query string for filtering events.
    filters (dict): Dictionary of filters applied by the user.

    Returns:
    list: List of processed events with employee data.
    """
    query = (
        """
        SELECT DISTINCT ep.reference_docname as employee_id, e.name as id, e.starts_on as date, e.custom_customer as client, e.subject as description, e.status, e.custom_service as sub_category
        FROM `tabEvent Participants` as ep, `tabEvent` as e
        WHERE ep.parent = e.name AND ep.reference_doctype = 'Employee'
    """
        + event_filters
    )

    events = frappe.db.sql(query, as_dict=True)
    return process_employee_data(events, filters, "event")


def process_employee_data(records, filters, record_type):
    """
    Processes the list of records (tasks or events) by fetching employee data and
    generating links for both employees and tasks/events.

    Args:
    records (list): List of records (tasks/events).
    filters (dict): Dictionary of filters applied by the user.
    record_type (str): Type of record being processed ('task' or 'event').

    Returns:
    list: List of records with employee details and hyperlinks.
    """
    result, employee_filtered = [], []

    for record in records:
        employee_user = get_employee_user(record, record_type)
        record["employee"] = ""

        if employee_user and frappe.db.exists("Employee", {"user_id": employee_user}):
            employee_id, employee_full_name = frappe.db.get_value(
                "Employee", {"user_id": employee_user}, ["name", "employee_name"]
            )
            record["employee"] = (
                f"<a href='{frappe.utils.get_url()}/app/employee/{employee_id}'>{employee_full_name}</a>"
            )

            if filters.get("employee") and employee_id == filters["employee"]:
                employee_filtered.append(record)

        if not has_common(record["id"], "<a"):
            record["id"] = (
                f"<a href='{frappe.utils.get_url()}/app/{record_type}/{record['id']}'>{record['id']}</a>"
            )

        record["reference_type"] = "Task"
        if record_type == "event":
            record["reference_type"] = "Event"

        record["department"] = (
            frappe.db.get_value(
                "Compliance Sub Category", record["sub_category"], "department"
            )
            if record["sub_category"]
            else ""
        )

        if (
            filters.get("department")
            and filters.get("department") != record["department"]
        ):
            continue

        fetch_billing_details(record, record_type)

        result.append(record)

    return employee_filtered if filters.get("employee") else result


def fetch_billing_details(record, record_type):
    """
    Fetches billing and payment details for the given task or event record.

    Args:
    record (dict): The record (task/event) being processed.
    record_type (str): The type of record ('task' or 'event').

    Returns:
    None: Updates the record in place with billing details.
    """
    try:
        record["invoiced"] = ""

        if record_type == "task":
            handle_task_billing(record)

        elif record_type == "event":
            handle_event_billing(record)

    except Exception as e:
        frappe.log_error(
            f"Error fetching billing details for {record_type} {record.get('id')}: {e}"
        )


def handle_task_billing(record):
    """
    Handles fetching billing details for task records.

    Args:
    record (dict): The task record to be updated.

    Returns:
    None: Updates the record in place with billing details.
    """
    record["invoiced"] = "No"
    so = frappe.db.exists(
        "Sales Order", {"customer": record["client"], "project": record.get("project")}
    )
    if so:
        record["billing_date"] = frappe.db.get_value(
            "Sales Order", so, "custom_billing_date"
        )
        record["invoice_amount"] = frappe.utils.fmt_money(
            frappe.db.get_value("Sales Order", so, "grand_total"), currency="INR"
        )
        item_code = frappe.db.get_value(
            "Compliance Sub Category", record.get("sub_category"), "item_code"
        )
        record["invoiced"] = "Yes"

        # Fetch related Sales Invoice and payment details
        si = frappe.db.get_value(
            "Sales Invoice Item", {"sales_order": so, "item_code": item_code}, "parent"
        )
        if si:
            record["payment_received"] = (
                frappe.db.get_value("Sales Invoice", si, "grand_total") or 0
            )
            grand_total = frappe.db.get_value("Sales Order", so, "grand_total") or 0
            record["outstanding_amount"] = frappe.utils.fmt_money(
                grand_total - record["payment_received"], currency="INR"
            )
            record["payment_received"] = frappe.utils.fmt_money(
                record["payment_received"], currency="INR"
            )


def handle_event_billing(record):
    """
    Handles fetching billing details for event records.

    Args:
    record (dict): The event record to be updated.

    Returns:
    None: Updates the record in place with billing details.
    """
    record["invoiced"] = "Not Billlable"
    item_code = frappe.db.get_value(
        "Compliance Sub Category", record.get("sub_category"), "item_code"
    )
    if item_code:
        sales_order = frappe.db.sql(
            f"""
            SELECT DISTINCT so.name 
            FROM `tabSales Order` as so, `tabSales Order Item` as soi 
            WHERE soi.parent = so.name AND soi.item_code = '{item_code}' AND so.customer = '{record['client']}'
            """,
            as_dict=True,
        )

        if sales_order:
            record["billing_date"] = frappe.db.get_value(
                "Sales Order", sales_order, "custom_billing_date"
            )
            record["invoiced"] = "Yes"
            si = frappe.db.get_value(
                "Sales Invoice Item", {"sales_order": sales_order[0]["name"]}, "parent"
            )
            record["invoice_amount"] = frappe.utils.fmt_money(
                frappe.db.get_value("Sales Order", sales_order, "grand_total"),
                currency="INR",
            )

            if si:
                record["payment_received"] = (
                    frappe.db.get_value("Sales Invoice", si, "grand_total") or 0
                )
                grand_total = (
                    frappe.db.get_value(
                        "Sales Order", sales_order[0]["name"], "grand_total"
                    )
                    or 0
                )
                record["outstanding_amount"] = frappe.utils.fmt_money(
                    grand_total - record["payment_received"], currency="INR"
                )
                record["payment_received"] = frappe.utils.fmt_money(
                    record["payment_received"], currency="INR"
                )


def get_employee_user(record, record_type):
    """
    Retrieves the user ID of the employee associated with a task or event.

    Args:
    record (dict): A dictionary representing the task or event.
    record_type (str): Type of record ('task' or 'event').

    Returns:
    str: User ID of the employee associated with the task/event.
    """
    if record_type == "task":
        if record["status"] != "Completed":
            return (
                frappe.db.get_value(
                    "ToDo",
                    {
                        "reference_name": record["id"],
                        "status": ["not in", ["Closed", "Cancelled"]],
                    },
                    "allocated_to",
                )
                or ""
            )
        return record["completed_by"]

    if record_type == "event":
        return frappe.db.get_value("Employee", record["employee_id"], "user_id")
