# Copyright (c) 2024, efeone and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import get_datetime, get_url_to_form, getdate


def execute(filters=None):
    columns = get_columns(filters)
    data = get_data(filters)
    chart = get_chart_data(data)
    return columns, data, None, chart


def get_columns(filters=None):
    columns = [
        {
            "label": _("Department"),
            "fieldname": "department",
            "fieldtype": "Link",
            "options": "Department",
            "width": 200,
        },
        {
            "label": _("Customer"),
            "fieldname": "customer",
            "fieldtype": "Link",
            "options": "Customer",
            "width": 200,
        },
        {
            "label": _("Project/Event"),
            "fieldname": "project",
            "fieldtype": "Data",
            "options": "Project",
            "width": 400,
        },
        {
            "label": _("Project Name"),
            "fieldname": "project_name",
            "fieldtype": "Data",
            "width": 100,
            "hidden": 1,
        },
        {
            "label": _("Status"),
            "fieldname": "status",
            "fieldtype": "Data",
            "width": 150,
        },
        {
            "label": _("Progress"),
            "fieldname": "progress",
            "fieldtype": "Percent",
            "width": 150,
        },
        {
            "label": _("Pending Tasks"),
            "fieldname": "pending_task",
            "fieldtype": "Int",
            "width": 150,
        },
        {
            "label": _("Completed Tasks"),
            "fieldname": "completed_task",
            "fieldtype": "Int",
            "width": 150,
        },
        {
            "label": _("Overdue Tasks"),
            "fieldname": "overdue_task",
            "fieldtype": "Int",
            "width": 150,
        },
        {
            "label": _("Invoiced"),
            "fieldname": "invoiced",
            "fieldtype": "Data",
            "width": 90,
        },
        {
            "label": _("Invoiced Amount"),
            "fieldname": "invoiced_amount",
            "fieldtype": "Currency",
            "width": 150,
        },
        {
            "label": _("Payment Recieved"),
            "fieldname": "payment_recieved",
            "fieldtype": "Currency",
            "width": 180,
        },
        {
            "label": _("Outstanding Amount"),
            "fieldname": "outstanding_amount",
            "fieldtype": "Currency",
            "width": 180,
        },
    ]
    return columns


def get_data(filters):
    data = []
    departments = []
    if filters.get("department"):
        if frappe.db.exists("Department", filters.get("department")):
            departments.append(filters.get("department"))
    else:
        departments = frappe.db.get_all(
            "Department", {"is_group": 0, "is_compliance": 1}, pluck="name"
        )
    data = prepare_data(departments, filters)
    return data


def prepare_data(departments, filters):
    data = []
    for department in departments:
        department_row = []

        if filters.get("reference_type") == "Project" or not filters.get(
            "reference_type"
        ):
            projects = []
            if filters.get("project"):
                projects.append(filters.get("project"))
            else:
                projects = frappe.db.get_all(
                    "Project",
                    {
                        "department": department,
                        "expected_start_date": [
                            "between",
                            [
                                getdate(filters.get("from_date")),
                                getdate(filters.get("to_date")),
                            ],
                        ],
                    },
                    pluck="name",
                )
            total_pending_tasks, total_completed_tasks, total_overdue_tasks = 0, 0, 0
            total_invoiced_amount, total_payment_recieved, total_outstanding_amount = (
                0,
                0,
                0,
            )
            for project in projects:
                project_doc = frappe.get_doc("Project", project)
                invoice_details = get_invoiced_and_outstanding_amount_from_project(
                    project
                )
                if filters.get("customer") and (
                    project_doc.customer != filters.get("customer")
                    or not project_doc.customer
                ):
                    continue
                if filters.get("status") and (
                    project_doc.status != filters.get("status")
                    or not project_doc.status
                ):
                    continue
                if filters.get("invoiced") and filters.get(
                    "invoiced"
                ) != is_invoiced_or_not(project):
                    continue
                row = {
                    "department": department,
                    "customer": project_doc.customer,
                    "project": get_hyper_link_to_form(
                        "Project", project_doc.name, project_doc.project_name
                    ),
                    "project_name": project_doc.project_name,
                    "status": project_doc.status,
                    "progress": project_doc.percent_complete,
                    "pending_task": get_project_count_based_on_status(
                        project, "Pending"
                    ),
                    "completed_task": get_project_count_based_on_status(
                        project, "Completed"
                    ),
                    "overdue_task": get_project_count_based_on_status(
                        project, "Overdue"
                    ),
                    "invoiced": is_invoiced_or_not(project),
                    "invoiced_amount": invoice_details.get("invoiced_amount") or 0,
                    "payment_recieved": invoice_details.get("payment_recieved") or 0,
                    "outstanding_amount": invoice_details.get("outstanding_amount")
                    or 0,
                }
                total_pending_tasks += get_project_count_based_on_status(
                    project, "Pending"
                )
                total_completed_tasks += get_project_count_based_on_status(
                    project, "Completed"
                )
                total_overdue_tasks += get_project_count_based_on_status(
                    project, "Overdue"
                )
                total_invoiced_amount += row.get("invoiced_amount")
                total_payment_recieved += row.get("payment_recieved")
                total_outstanding_amount += row.get("outstanding_amount")
                department_row.append(row)
        if (
            filters.get("reference_type") in [None, "Event"]
            and not filters.get("project")
            and not filters.get("invoiced")
        ):
            work = frappe.db.exists(
                "Compliance Sub Category", {"department": department}
            )
            if work:
                event_filters = {"custom_is_billable": 1, "custom_service": work}
                if filters.get("customer"):
                    event_filters["custom_customer"] = filters.get("customer")
                if filters.get("from_date") and filters.get("to_date"):
                    event_filters["starts_on"] = [
                        "between",
                        [
                            get_datetime(filters.get("from_date")),
                            get_datetime(filters.get("to_date")),
                        ],
                    ]
                events = frappe.db.get_all("Event", filters=event_filters, fields=["*"])
                for event in events:
                    event_billing_details = handle_event_billing(
                        {"client": event["custom_customer"], "sub_category": work}
                    )
                    row = {
                        "department": department,
                        "project": get_hyper_link_to_form("Event", event["name"]),
                        "customer": event["custom_customer"],
                        "status": event["status"],
                        "invoiced": "Yes",
                        "invoiced_amount": event_billing_details.get(
                            "invoice_amount", 0
                        ),
                        "payment_received": event_billing_details.get(
                            "payment_received", 0
                        ),
                        "outstanding_amount": event_billing_details.get(
                            "outstanding_amount", 0
                        ),
                        "progress": 100 if event["status"] == "Completed" else 0,
                    }
                    department_row.append(row)
        data.extend(department_row)

    # Fetching billed events that do not have a department
    if (
        filters.get("reference_type") in [None, "Event"]
        and not filters.get("department")
        and not filters.get("project")
        and not filters.get("invoiced")
    ):
        no_department_events = get_events_without_department(filters)
        data += no_department_events
    return data


def get_events_without_department(filters):
    event_rows = []
    valid_works = frappe.db.get_all(
        "Compliance Sub Category", {"department": ""}, pluck="name"
    )
    event_filters = {"custom_is_billable": 1, "custom_service": ["in", valid_works]}
    if filters.get("customer"):
        event_filters["custom_customer"] = filters.get("customer")
    if filters.get("status"):
        event_filters["status"] = filters.get("status")
    if filters.get("from_date") and filters.get("to_date"):
        event_filters["starts_on"] = [
            "between",
            [
                get_datetime(filters.get("from_date")),
                get_datetime(filters.get("to_date")),
            ],
        ]
    events = frappe.db.get_all("Event", event_filters, ["*"])
    for event in events:
        event_billing_details = handle_event_billing(
            {
                "client": event["custom_customer"],
                "sub_category": event["custom_service"],
            }
        )
        row = {
            "invoiced_amount": 0,
            "payment_received": 0,
            "outstanding_amount": 0,
        }
        if event_billing_details:
            if "invoiced_amount" in event_billing_details:
                row["invoiced_amount"] = event_billing_details["invoiced_amount"]
            if "payment_received" in event_billing_details:
                row["payment_received"] = event_billing_details["payment_received"]
            if "outstanding_amount" in event_billing_details:
                row["outstanding_amount"] = event_billing_details["outstanding_amount"]
        row = {
            "project": get_hyper_link_to_form("Event", event["name"]),
            "department": "",
            "customer": event["custom_customer"],
            "status": event["status"],
            "invoiced": "Yes",
        }
        if row["status"] == "Completed":
            row["progress"] = 100
        event_rows.append(row)
    return event_rows


# This is the same code from detailed task summary refactor, once that is merged import that method instead of re-defining it
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
    return record


def get_project_count_based_on_status(project, status):
    """
    Method to get count of Tasks with respect to Project and status
    """
    count = 0
    available_statuses = ["Overdue", "Completed"]
    if status == "Pending":
        if frappe.db.exists(
            "Task",
            {
                "project": project,
                "status": ["in", ["Open", "Working", "Pending Review", "Hold"]],
            },
        ):
            count = frappe.db.count(
                "Task",
                {
                    "project": project,
                    "status": ["in", ["Open", "Working", "Pending Review", "Hold"]],
                },
            )
    elif status in available_statuses:
        if frappe.db.exists("Task", {"project": project, "status": status}):
            count = frappe.db.count("Task", {"project": project, "status": status})
    return count


def is_invoiced_or_not(project):
    """
    Method to check wether the project is invoiced or not
    Submitted Sales Invoice with Project link in accounting Dimensions
    Return Yes or No
    """
    invoiced = "No"
    if frappe.db.exists("Sales Invoice", {"project": project, "docstatus": 1}):
        invoiced = "Yes"
    return invoiced


def get_invoiced_and_outstanding_amount_from_project(project):
    invoice_details = {
        "invoiced_amount": 0,
        "payment_recieved": 0,
        "outstanding_amount": 0,
    }
    query = """
        SELECT
            coalesce(SUM(rounded_total), 0) as invoiced_amount,
            coalesce(SUM(outstanding_amount), 0) as outstanding_amount
        FROM
            `tabSales Invoice`
        WHERE
            project = %(project)s AND
            docstatus = 1
    """
    output = frappe.db.sql(query, {"project": project}, as_dict=True)
    if output and output[0]:
        invoice_details["invoiced_amount"] = output[0].get("invoiced_amount") or 0
        invoice_details["outstanding_amount"] = output[0].get("outstanding_amount") or 0
        invoice_details["payment_recieved"] = (
            invoice_details["invoiced_amount"] - invoice_details["outstanding_amount"]
        )
    return invoice_details


def get_chart_data(data):
    labels = []
    pending_tasks = []
    completed_tasks = []
    overdue_tasks = []

    for row in data:
        if not row.get("customer"):
            labels.append(row.get("department"))
            pending_tasks.append(row.get("pending_task"))
            completed_tasks.append(row.get("completed_task"))
            overdue_tasks.append(row.get("overdue_task"))

    return {
        "data": {
            "labels": labels[:30],
            "datasets": [
                {"name": _("Pending Task"), "values": pending_tasks[:30]},
                {"name": _("Completed Task"), "values": completed_tasks[:30]},
                {"name": _("Overdue Task"), "values": overdue_tasks[:30]},
            ],
        },
        "type": "line",
        "colors": ["#fc4f51", "#29cd42", "#7575ff"],
        "barOptions": {"stacked": True},
    }


def get_hyper_link_to_form(doctype, docname, link_text=None):
    """Generate an HTML hyperlink for a form.

    Args:
        doctype (str): Name of the doctype (e.g., "Employee").
        docname (str): Name of the document (e.g., "EMP-0001").
        link_text (str, optional): Custom text for the link. Defaults to the document name.

    Returns:
        str: HTML hyperlink formatted as <a href='URL'>link_text</a>.
    """
    link_text = docname if not link_text else f"{docname} : {link_text}"
    return f"<a href='{get_url_to_form(doctype, docname)}'>{link_text}</a>"
