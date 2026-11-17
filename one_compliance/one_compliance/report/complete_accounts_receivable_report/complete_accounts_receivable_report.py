# Copyright (c) 2025, efeone and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import flt

def execute(filters=None):

    if not filters:
        filters = {}
    columns = get_columns()
    data = get_data(filters)

    return columns, data

def get_columns():
    return [
        {"label": "Posting Date", "fieldname": "posting_date", "fieldtype": "Date", "width": 100},
        {"label": "Customer", "fieldname": "customer", "fieldtype": "Link", "options": "Customer", "width": 200},
        {"label": "Customer Group", "fieldname": "customer_group", "fieldtype": "Link", "options": "Customer Group", "width": 150},
        {"label": "Voucher Type", "fieldname": "voucher_type", "fieldtype": "Data", "width": 120},
        {"label": "Voucher No", "fieldname": "voucher_no", "fieldtype": "Dynamic Link", "options": "voucher_type", "width": 200},
        {"label": "Due Date", "fieldname": "due_date", "fieldtype": "Date", "width": 100},
        {"label": "Amount", "fieldname": "grand_total", "fieldtype": "Currency", "width": 150},
        {"label": "Paid Amount", "fieldname": "paid_amount", "fieldtype": "Currency", "width": 150},
        {"label": "Outstanding Amount", "fieldname": "outstanding_amount", "fieldtype": "Currency", "width": 180},
    ]

def get_conditions(filters):
    conditions = []
    vals = []

    if filters.get("company"):
        conditions.append("so.company = %s")
        vals.append(filters.get("company"))

    if filters.get("customer"):
        conditions.append("so.customer = %s")
        vals.append(filters.get("customer"))

    if filters.get("customer_group"):
        conditions.append("cust.customer_group = %s")
        vals.append(filters.get("customer_group"))

    return " AND ".join(conditions), vals


def get_data(filters):
    date_cond, date_vals = "", []
    if filters.get("from_date") and filters.get("to_date"):
        date_cond = "AND so.transaction_date BETWEEN %s AND %s"
        date_vals = [filters.get("from_date"), filters.get("to_date")]

    conditions, vals = get_conditions(filters)

    w_states = ["Proforma Invoice", "Invoiced"]
    wf_cond = "AND so.workflow_state IN ({})".format(", ".join(["%s"] * len(w_states)))

    bind_vals = w_states + date_vals + vals
    sales_orders = frappe.db.sql(f"""
        SELECT
            so.transaction_date AS posting_date,
            so.customer,
            cust.customer_group,
            ps.due_date,
            so.name AS sales_order,
            so.rounded_total AS so_total,
            si.name AS sales_invoice,
            si.rounded_total AS si_total

        FROM `tabSales Order` so
        LEFT JOIN `tabCustomer` cust ON cust.name = so.customer
        LEFT JOIN `tabPayment Schedule` ps ON ps.parent = so.name
        LEFT JOIN `tabSales Invoice Item` sii ON sii.sales_order = so.name
        LEFT JOIN `tabSales Invoice` si 
            ON si.name = sii.parent AND si.docstatus = 1

        WHERE so.docstatus = 1
        {wf_cond}
        {date_cond}
        {"AND " + conditions if conditions else ""}
    """, bind_vals, as_dict=True)

    result = []

    for row in sales_orders:

        if row.sales_invoice:
            voucher_type = "Sales Invoice"
            voucher_no = row.sales_invoice
            amount = flt(row.si_total)
        else:
            voucher_type = "Sales Order"
            voucher_no = row.sales_order
            amount = flt(row.so_total)

        paid_amount = frappe.db.sql("""
            SELECT SUM(ABS(amount))
            FROM `tabPayment Ledger Entry`
            WHERE against_voucher_no = %s
            AND party = %s
            AND amount < 0
        """, (voucher_no, row.customer))[0][0] or 0

        outstanding = amount - flt(paid_amount)

        result.append({
            "posting_date": row.posting_date,
            "customer": row.customer,
            "customer_group": row.customer_group,
            "voucher_type": voucher_type,
            "voucher_no": voucher_no,
            "due_date": row.due_date,
            "grand_total": amount,
            "paid_amount": paid_amount,
            "outstanding_amount": outstanding
        })
    result.extend(get_journal_entries(filters))
    result.sort(key=lambda x: x.get("posting_date"), reverse=True)
    return result

def get_journal_entries(filters):

    conditions = []
    vals = []

    if filters.get("include_draft_journal_entries"):
        docstatus_condition = "je.docstatus IN (0,1)"
    else:
        docstatus_condition = "je.docstatus = 1"

    if filters.get("company"):
        conditions.append("je.company = %s")
        vals.append(filters["company"])

    if filters.get("customer"):
        conditions.append("jel.party = %s")
        vals.append(filters["customer"])

    if filters.get("from_date") and filters.get("to_date"):
        conditions.append("je.posting_date BETWEEN %s AND %s")
        vals.append(filters["from_date"])
        vals.append(filters["to_date"])

    where = " AND ".join(conditions)
    if where:
        where = "AND " + where

    data = frappe.db.sql(f"""
        SELECT
            je.posting_date,
            jel.party AS customer,
            cust.customer_group,
            'Journal Entry' AS voucher_type,
            je.name AS voucher_no,
            SUM(jel.debit - jel.credit) AS grand_total

        FROM `tabJournal Entry` je
        JOIN `tabJournal Entry Account` jel ON jel.parent = je.name
        LEFT JOIN `tabCustomer` cust ON cust.name = jel.party

        WHERE {docstatus_condition}
        AND jel.party_type = 'Customer'
        {where}

        GROUP BY je.name
    """, vals, as_dict=True)

    result = []

    for row in data:

        paid_amount = frappe.db.sql("""
            SELECT SUM(ABS(amount))
            FROM `tabPayment Ledger Entry`
            WHERE against_voucher_no = %s
            AND party = %s
            AND amount < 0
        """, (row.voucher_no, row.customer))[0][0] or 0

        outstanding = flt(row.grand_total) - flt(paid_amount)

        if abs(outstanding) < 0.01:
            continue

        result.append({
            "posting_date": row.posting_date,
            "customer": row.customer,
            "customer_group": row.customer_group,
            "voucher_type": "Journal Entry",
            "voucher_no": row.voucher_no,
            "due_date": None,
            "grand_total": row.grand_total,
            "paid_amount": paid_amount,
            "outstanding_amount": outstanding
        })

    return result