# Copyright (c) 2023, efeone and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils.dateutils import get_from_date_from_timespan
from frappe.utils import today

def execute(filters=None):
    if not filters:
        filters = {}

    if "from_date" not in filters:
        filters["from_date"] = None

    if "to_date" not in filters:
        filters["to_date"] = None

    columns = get_columns(filters)
    data = get_data(filters)
    return columns, data, None, None, None


def get_columns(filters):
    columns = [
        {
            "label": _("ID"),
            "fieldname": "employee_checkin_id",
            "fieldtype": "Link",
            "options": "Employee Checkin",
            "width": 200
        },
        {
            "label": _("Employee Name"),
            "fieldname": "employee_name",
            "fieldtype": "Data",
            "width": 150
        },
        {
            "label": _("Department"),
            "fieldname": "department",
            "fieldtype": "Data",
            "width": 150
        },
        {
            "label": _("Date"),
            "fieldname": "date",
            "fieldtype": "Date",
            "width": 100
        },
        {
            "label": _("Check In Time"),
            "fieldname": "check_in_time",
            "fieldtype": "Time",
            "width": 150
        },
        {
            "label": _("Check Out Time"),
            "fieldname": "check_out_time",
            "fieldtype": "Time",
            "width": 150
        },
    ]
    return columns


def get_data(filters):
    data = []
    query = """
        SELECT
          ec.name AS employee_checkin_id,
          ec.employee_name,
          e.department,
          DATE(ec.time) AS date,
          MIN(TIME(ec.time)) AS check_in_time,
          MAX(CASE WHEN ec.log_type = 'OUT' THEN TIME(ec.time) ELSE NULL END) AS check_out_time
        FROM 
            `tabEmployee Checkin` as ec
        JOIN
            `tabEmployee` as e
        ON 
            ec.employee = e.name
        WHERE 
            ec.log_type IN ('IN', 'OUT')
    """
    if filters.get("from_date") and filters.get("to_date"):
        query += " AND ec.creation BETWEEN '{from_date}' AND '{to_date}'".format(from_date=filters.from_date, to_date=filters.to_date)
    
    if filters.get("department"):
        query += " AND e.department = '{0}'".format(filters.get("department"))  

    query += " GROUP BY ec.employee, ec.employee_name, e.department, DATE(ec.time)"
    query += " ORDER BY date DESC" 

    data = frappe.db.sql(query, as_dict=1)
    return data
