# Copyright (c) 2025, efeone and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import getdate, nowdate
from collections import defaultdict

DEFAULT_RANGES = [30, 60, 90, 120]

def parse_ageing_ranges(filters: dict | None) -> list[int]:
    raw = (filters or {}).get("range", "")
    try:
        edges = [int(x.strip()) for x in raw.split(",")]
        edges = sorted({edge for edge in edges if edge > 0})
        return edges or DEFAULT_RANGES
    except Exception:
        return DEFAULT_RANGES

def make_bucket_labels(edges: list[int]) -> list[str]:
    if not edges:
        return ["0‑Above"]
    labels = [f"0‑{edges[0]}"]
    labels += [f"{edges[i-1] + 1}‑{edges[i]}" for i in range(1, len(edges))]
    labels.append(f"{edges[-1] + 1}‑Above")
    return labels

def execute(filters: dict | None = None):
    if not filters:
        filters = {}

    columns = get_columns(filters)
    data = get_data_grouped_by_customer(filters)
    return columns, data

def get_columns(filters: dict) -> list[dict]:
    edges = parse_ageing_ranges(filters)
    labels = make_bucket_labels(edges)

    columns = [
        {"label": "Party Type", "fieldname": "party_type", "fieldtype": "Data", "width": 90},
        {"label": "Party", "fieldname": "customer", "fieldtype": "Link", "options": "Customer", "width": 150},
        {"label": "Sales Order Amount", "fieldname": "grand_total", "fieldtype": "Currency", "width": 120},
        {"label": "Paid Amount", "fieldname": "paid_amount", "fieldtype": "Currency", "width": 110},
        {"label": "Outstanding Amount", "fieldname": "outstanding_amount", "fieldtype": "Currency", "width": 130},
        {"label": "Age (Days)", "fieldname": "age", "fieldtype": "Int", "width": 70},
    ]

    for idx, lbl in enumerate(labels, 1):
        columns.append({
            "label": lbl,
            "fieldname": f"range{idx}",
            "fieldtype": "Currency",
            "width": 100
        })

    columns.extend([
        {"label": "Currency", "fieldname": "currency", "fieldtype": "Link", "options": "Currency", "width": 80},
        {"label": "Territory", "fieldname": "territory", "fieldtype": "Link", "options": "Territory", "width": 110},
        {"label": "Customer Group", "fieldname": "customer_group", "fieldtype": "Link", "options": "Customer Group", "width": 130},
        {"label": "Customer Contact", "fieldname": "customer_contact", "fieldtype": "Link", "options": "Contact", "width": 140},
    ])
    return columns

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
    edges = parse_ageing_ranges(filters)
    bucket_count = len(edges) + 1

    date_cond, date_vals = "", []
    fd, td = filters.get("from_date"), filters.get("to_date")

    if filters.get("ageing_based_on") == "Posting Date" and fd and td:
        date_cond = "AND so.transaction_date BETWEEN %s AND %s"
        date_vals.extend([fd, td])
    elif filters.get("ageing_based_on") == "Due Date" and fd and td:
        date_cond = "AND ps.due_date BETWEEN %s AND %s"
        date_vals.extend([fd, td])

    extra_cond, extra_vals = get_conditions(filters)

    # Workflow State filtering
    workflow_states = ["Proforma Invoice"]  # default state
    if filters.get("include_invoiced"):
        workflow_states.append("Invoiced")
    if filters.get("include_paid"):
        workflow_states.append("Paid")

    wf_cond = "AND so.workflow_state IN ({})".format(", ".join(["%s"] * len(workflow_states)))
    bind_vals = [today] + workflow_states + date_vals + extra_vals

    raw_results = frappe.db.sql(f"""
        SELECT
            so.transaction_date AS posting_date,
            'Customer' AS party_type,
            so.customer,
            soi.cost_center,
            ps.due_date,
            'Sales Order' AS voucher_type,
            so.name AS voucher_no,
            so.grand_total,
            so.advance_paid AS paid_amount,
            (so.grand_total - so.advance_paid) AS outstanding_amount,
            DATEDIFF(%s, so.transaction_date) AS age,
            so.currency,
            cust.territory,
            cust.customer_group,
            cust.customer_primary_contact AS customer_contact
        FROM `tabSales Order` so
        LEFT JOIN `tabSales Order Item` soi ON soi.parent = so.name
        LEFT JOIN `tabCustomer` cust ON cust.name = so.customer
        LEFT JOIN `tabPayment Schedule` ps ON ps.parent = so.name
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
        "age": 0,
        "currency": "",
        "territory": "",
        "customer_group": "",
        "customer_contact": "",
        **{f"range{i+1}": 0 for i in range(bucket_count)}
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
        entry["age"] = max(entry["age"], row["age"] or 0)

        age = row["age"] or 0
        placed = False
        for i, edge in enumerate(edges):
            if age <= edge:
                entry[f"range{i+1}"] += row["outstanding_amount"]
                placed = True
                break
        if not placed:
            entry[f"range{bucket_count}"] += row["outstanding_amount"]

    return list(summary.values())
