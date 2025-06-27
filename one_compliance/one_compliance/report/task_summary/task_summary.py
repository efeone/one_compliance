# Copyright (c) 2024, efeone and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt, getdate


def execute(filters=None):
    """
    Main function to execute the report and return columns and data.
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
            "fieldtype": "Currency",
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
            "fieldtype": "Currency",
            "width": 150,
        },
    ]


def get_data(filters):
    """
    Fetches and processes data from Task and Event doctypes based on filters.
    """
    data = []
  
    # Get Task data if reference_type is not specified or is "Task"
    if not filters.get("reference_type") or filters.get("reference_type") == "Task":
        task_data = get_task_data(filters)
        data.extend(task_data)
  
    # Get Event data if reference_type is not specified or is "Event"
    if not filters.get("reference_type") or filters.get("reference_type") == "Event":
        event_data = get_event_data(filters)
        data.extend(event_data)
  
    # Sort data by date (handle None and string values properly)
    data.sort(key=lambda x: x.get("date") or getdate("1900-01-01"), reverse=True)
  
    return data


def get_task_data(filters):
    """
    Fetches Task data with invoice information based on filters.
    """
    conditions = get_task_conditions(filters)

    # Enhanced query to include invoice information
    query = """
        SELECT
            t.name as id,
            t.subject as description,
            COALESCE(t.exp_start_date, t.act_start_date, t.completed_on) as date,
            t.customer as client,
            t.project,
            t.department,
            t.compliance_sub_category as sub_category,
            CASE
                WHEN t.status = 'Completed' THEN t.completed_by
                ELSE t.assigned_to
            END as employee_id,
            t.status,
            t.custom_payable_amount,
            p.name as project_name,
            so.name as sales_order_name,
            so.custom_billing_date as billing_date,
            si.name as sales_invoice_name,
            si.grand_total as invoiced_amount,
            si.outstanding_amount as outstanding_amount,
            CASE 
                WHEN si.name IS NOT NULL AND si.outstanding_amount = 0 THEN 'Yes'
                WHEN si.name IS NOT NULL AND si.outstanding_amount > 0 THEN 'Partial'
                ELSE 'No'
            END as invoiced_status,
            CASE 
                WHEN si.name IS NOT NULL AND si.outstanding_amount = 0 THEN 'Yes'
                ELSE 'No'
            END as payment_received
        FROM `tabTask` t
        LEFT JOIN `tabProject` p ON t.project = p.name
        LEFT JOIN `tabSales Order` so ON p.sales_order = so.name
        LEFT JOIN `tabSales Invoice Item` sii ON so.name = sii.sales_order
        LEFT JOIN `tabSales Invoice` si ON si.name = sii.parent AND si.docstatus = 1
        WHERE {conditions}
        ORDER BY date DESC
    """.format(conditions=conditions)
  
    task_records = frappe.db.sql(query, filters, as_dict=True)
    
    
  
    # Get employee names
    employee_names = get_employee_names([t.get("employee_id") for t in task_records if t.get("employee_id")])
  
    # Format task data
    formatted_data = []
    for task in task_records:
        # Use invoice amount if available, otherwise use custom_payable_amount
        invoice_amount = flt(task.get("invoiced_amount")) or 0
        outstanding_amount = flt(task.get("outstanding_amount")) or 0
        
        # Determine invoiced status
        if task.get("sales_invoice_name"):
            invoiced = task.get("invoiced_status", "No")
        else:
            invoiced = "No"
        
        row = {
            "reference_type": "Task",
            "id": task.get("id"),
            "description": task.get("description"),
            "date": task.get("date"),
            "client": task.get("client"),
            "project": task.get("project"),
            "department": task.get("department"),
            "sub_category": task.get("sub_category"),
            "employee": employee_names.get(task.get("employee_id"), task.get("employee_id") or ""),
            "status": task.get("status"),
            "invoiced": invoiced,
            "billing_date": task.get("billing_date"),
            "invoice_amount": invoice_amount,
            "payment_received": "Yes" if invoice_amount != outstanding_amount else "No",
            "outstanding_amount": outstanding_amount
        }
        formatted_data.append(row)
  
    return formatted_data


def get_event_data(filters):
    """
    Fetches Event data with enhanced invoice logic based on filters.
    """
    conditions = get_event_conditions(filters)

    query = """
        SELECT
            e.name as id,
            e.subject as description,
            DATE(e.starts_on) as date,
            e.custom_customer as client,
            e.company,
            e.custom_service,
            e.custom_rate,
            e.status,
            so.custom_billing_date,
            si.grand_total,
            si.outstanding_amount as outstanding_amount
        FROM `tabEvent` e
        LEFT JOIN `tabSales Order` so ON so.event = e.name
        LEFT JOIN `tabSales Invoice Item` sii ON so.name = sii.sales_order
        LEFT JOIN `tabSales Invoice` si ON si.name = sii.parent AND si.docstatus = 1
        WHERE {conditions}
        ORDER BY e.starts_on DESC
        """.format(conditions=conditions)
  
    event_records = frappe.db.sql(query, filters, as_dict=True)
  
    # Get event participants (employees)
    event_employees = get_event_employees([e.get("id") for e in event_records])
  
    # Format event data
    formatted_data = []
    for event in event_records:
        employees = event_employees.get(event.get("id"), [])
        employee_names = ", ".join(employees) if employees else ""
        
        grand_total         = flt(event.get("grand_total")) or 0
        outstanding_amount  = flt(event.get("outstanding_amount")) or 0
        
        row = {
            "reference_type": "Event",
            "id": event.get("id"),
            "description": event.get("description"),
            "date": event.get("date"),
            "client": event.get("client"),
            "project": None,  
            "department": None,  
            "sub_category": None, 
            "employee": employee_names,
            "status": event.get("status"),
            "invoiced": "Yes" if outstanding_amount > 0 else "No",
            "billing_date": event.get("custom_billing_date"),
            "invoice_amount": grand_total,
            "payment_received": "Yes" if grand_total != outstanding_amount else "No", 
            "outstanding_amount": outstanding_amount
        }
        formatted_data.append(row)
  
    return formatted_data


def get_task_conditions(filters):
    """
    Builds WHERE conditions for Task query based on filters.
    """
    conditions = ["t.docstatus < 2"]  
  
    if filters.get("from_date"):
        conditions.append("(t.exp_start_date >= %(from_date)s OR t.act_start_date >= %(from_date)s OR t.completed_on >= %(from_date)s)")
  
    if filters.get("to_date"):
        conditions.append("(t.exp_start_date <= %(to_date)s OR t.act_start_date <= %(to_date)s OR t.completed_on <= %(to_date)s)")
  
    if filters.get("client"):
        conditions.append("t.customer = %(client)s")
  
    if filters.get("project"):
        conditions.append("t.project = %(project)s")
  
    if filters.get("status"):
        conditions.append("t.status = %(status)s")
  
    if filters.get("sub_category"):
        conditions.append("t.compliance_sub_category = %(sub_category)s")
  
    if filters.get("department"):
        conditions.append("t.department = %(department)s")
  
    if filters.get("employee"):
        # Get user ID from Employee ID
        user_id = frappe.db.get_value("Employee", filters.get("employee"), "user_id")
        if user_id:
            conditions.append("(t.assigned_to = %(user_id)s OR t.completed_by = %(user_id)s)")
            filters["user_id"] = user_id  
        else:
            conditions.append("1=0")

       
    return " AND ".join(conditions)


def get_event_conditions(filters):
    """
    Builds WHERE conditions for Event query based on filters.
    """
    conditions = ["e.docstatus < 2"] 
  
    if filters.get("from_date"):
        conditions.append("DATE(e.starts_on) >= %(from_date)s")
  
    if filters.get("to_date"):
        conditions.append("DATE(e.starts_on) <= %(to_date)s")
  
    if filters.get("client"):
        conditions.append("e.custom_customer = %(client)s")
  
    if filters.get("status"):
        # Map task status to event status if needed
        event_status = filters.get("status")
        if event_status in ["Open", "Working"]:
            conditions.append("e.status IN ('Open', 'Confirmed')")
        elif event_status == "Completed":
            conditions.append("e.status = 'Closed'")
        else:
            conditions.append("e.status = %(status)s")
  
    # For employee filter, we need to check event participants
    if filters.get("employee"):
        conditions.append("""
            e.name IN (
                SELECT ep.parent
                FROM `tabEvent Participants` ep
                WHERE ep.reference_docname = %(employee)s
                AND ep.reference_doctype = 'Employee'
            )
        """)

  
    return " AND ".join(conditions)


def get_employee_names(employee_ids):
    """
    Fetches employee names for given employee IDs.
    """
    if not employee_ids:
        return {}
  
    valid_ids = [emp_id for emp_id in employee_ids if emp_id]
  
    if not valid_ids:
        return {}
  
    employees = frappe.db.sql("""
        SELECT name, employee_name
        FROM `tabEmployee`
        WHERE name IN ({})
    """.format(",".join(["%s"] * len(valid_ids))), valid_ids, as_dict=True)
  
    return {emp.name: emp.employee_name for emp in employees}


def get_event_employees(event_ids):
    """
    Fetches employee participants for given event IDs.
    """
    if not event_ids:
        return {}
  
    participants = frappe.db.sql("""
        SELECT
            ep.parent as event_id,
            emp.employee_name
        FROM `tabEvent Participants` ep
        LEFT JOIN `tabEmployee` emp ON ep.reference_docname = emp.name
        WHERE ep.parent IN ({})
        AND ep.reference_doctype = 'Employee'
        AND emp.employee_name IS NOT NULL
    """.format(",".join(["%s"] * len(event_ids))), event_ids, as_dict=True)
  
    event_employees = {}
    for participant in participants:
        event_id = participant.get("event_id")
        employee_name = participant.get("employee_name")
      
        if event_id not in event_employees:
            event_employees[event_id] = []
      
        if employee_name:
            event_employees[event_id].append(employee_name)
  
    return event_employees