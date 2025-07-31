# Copyright (c) 2025, efeone and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import getdate, nowdate
from collections import defaultdict

def execute(filters: dict | None = None):
    if not filters:
        filters = {}

    columns = get_columns()
    data = get_data_grouped_by_customer(filters)
    return columns, data

def get_columns() -> list[dict]:
    return [
        {"label": "Party Type", "fieldname": "party_type", "fieldtype": "Data", "width": 90},
        {"label": "Party", "fieldname": "customer", "fieldtype": "Link", "options": "Customer", "width": 150},
        {"label": "Sales Order Amount", "fieldname": "grand_total", "fieldtype": "Currency", "width": 120},
        {"label": "Received Amount", "fieldname": "paid_amount", "fieldtype": "Currency", "width": 140},
        {"label": "Outstanding Amount", "fieldname": "outstanding_amount", "fieldtype": "Currency", "width": 130},
        {"label": "Currency", "fieldname": "currency", "fieldtype": "Link", "options": "Currency", "width": 80},
        {"label": "Territory", "fieldname": "territory", "fieldtype": "Link", "options": "Territory", "width": 110},
        {"label": "Customer Group", "fieldname": "customer_group", "fieldtype": "Link", "options": "Customer Group", "width": 130},
        {"label": "Customer Contact", "fieldname": "customer_contact", "fieldtype": "Link", "options": "Contact", "width": 140},
    ]

def get_conditions(filters: dict) -> tuple[str, list]:
    conditions, vals = [], []

    if cust := filters.get("customer"):
        conditions.append("so.customer = %s")
        vals.append(cust)

    if company := filters.get("company"):
        conditions.append("so.company = %s")
        vals.append(company)

    if terr := filters.get("territory"):
        terr_doc = frappe.get_doc("Territory", terr)
        terr_list = [terr]
        if terr_doc.is_group:
            terr_list = [d.name for d in frappe.get_all("Territory", filters={"lft": [">=", terr_doc.lft], "rgt": ["<=", terr_doc.rgt]})]
        conditions.append("cust.territory IN ({})".format(", ".join(["%s"] * len(terr_list))))
        vals.extend(terr_list)

    if cgrp := filters.get("customer_group"):
        cgrp_doc = frappe.get_doc("Customer Group", cgrp)
        cgrp_list = [cgrp]
        if cgrp_doc.is_group:
            cgrp_list = [d.name for d in frappe.get_all("Customer Group", filters={"lft": [">=", cgrp_doc.lft], "rgt": ["<=", cgrp_doc.rgt]})]
        conditions.append("cust.customer_group IN ({})".format(", ".join(["%s"] * len(cgrp_list))))
        vals.extend(cgrp_list)

    return " AND ".join(conditions), vals

def get_data_grouped_by_customer(filters: dict) -> list[dict]:
    today = getdate(filters.get("report_date") or nowdate())

    date_cond, date_vals = "", []
    fd, td = filters.get("from_date"), filters.get("to_date")

    if fd and td:
        date_cond = "AND so.transaction_date BETWEEN %s AND %s"
        date_vals.extend([fd, td])

    extra_cond, extra_vals = get_conditions(filters)

    # Workflow State filtering
    workflow_states = ["Proforma Invoice"]  # default state
    if filters.get("include_invoiced"):
        workflow_states.append("Invoiced")
    if filters.get("include_paid"):
        workflow_states.append("Paid")

    wf_cond = "AND so.workflow_state IN ({})".format(", ".join(["%s"] * len(workflow_states)))
    bind_vals = workflow_states + date_vals + extra_vals

    raw_results = frappe.db.sql(f"""
        SELECT
            'Customer' AS party_type,
            so.customer,
            soi.cost_center,
            'Sales Order' AS voucher_type,
            so.name AS voucher_no,
            so.grand_total,
            so.advance_paid AS paid_amount,
            (so.grand_total - so.advance_paid) AS outstanding_amount,
            so.currency,
            cust.territory,
            cust.customer_group,
            cust.customer_primary_contact AS customer_contact
        FROM `tabSales Order` so
        LEFT JOIN `tabSales Order Item` soi ON soi.parent = so.name
        LEFT JOIN `tabCustomer` cust ON cust.name = so.customer
        WHERE so.docstatus = 1
          AND so.customer IS NOT NULL
          AND so.customer != ''
          {wf_cond}
          {date_cond}
          {"AND " + extra_cond if extra_cond else ""}
        GROUP BY so.name
    """, bind_vals, as_dict=True)

    summary = defaultdict(lambda: {
        "party_type": "Customer",
        "customer": "",
        "grand_total": 0,
        "paid_amount": 0,
        "outstanding_amount": 0,
        "currency": "",
        "territory": "",
        "customer_group": "",
        "customer_contact": ""
    })

    for row in raw_results:
        key = row["customer"]
        entry = summary[key]
        entry["customer"] = row["customer"]
        entry["currency"] = row["currency"]
        entry["territory"] = row["territory"]
        entry["customer_group"] = row["customer_group"]
        entry["customer_contact"] = row["customer_contact"]
        entry["grand_total"] += row["grand_total"] or 0
        entry["paid_amount"] += row["paid_amount"] or 0
        entry["outstanding_amount"] += row["outstanding_amount"] or 0

    return list(summary.values())
