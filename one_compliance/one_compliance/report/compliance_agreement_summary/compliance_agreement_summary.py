# Copyright (c) 2023, efeone and contributors
# For license information, please see license.txt

import frappe
from frappe import _

def execute(filters=None):
    if not filters:
        filters = {}

    if "customer" not in filters:
        filters["customer"] = None

    columns = get_columns(filters)
    data = get_data(filters)
    return columns, data

def get_columns(filters):
    columns = [
        {
            "label": _("Customer"),
            "fieldname": "customer",
            "fieldtype": "Link",
            "options": "Customer",
            "width": 200
        },
        {
            "label": _("Agreement"),
            "fieldname": "name",
            "fieldtype": "data",
            "width": 200
        },
        {
            "label":_("Valid From"),
            "fieldname":"valid_from",
            "fieldtype":"Date",
            "width": 200
        },
        {
            "label":_("Compliance Category"),
            "fieldname": "compliance_category",
            "fieldtype":"Link",
            "options": "Compliance Category",
            "width": 200
        },
        {
            "label":_("Compliance Sub Category"),
            "fieldname":"compliance_sub_category",
            "fieldtype":"Link",
            "options":"Compliance Sub Category",
            "width": 200
        },
        {
            "label":_("Sub Category Name"),
            "fieldname":"sub_category_name",
            "fieldtype":"Data",
            "width": 200
        },
        {
            "label":_("Compliance Date"),
            "fieldname":"compliance_date",
            "fieldtype":"Date",
            "width": 200
        },
        {
            "label":_("Next Compliance Date"),
            "fieldname":"next_compliance_date",
            "fieldtype":"Date",
            "width": 200
        }
    ]
    return columns

def get_data(filters):
    data = []
    query = """
        SELECT
            ca.customer AS customer,
            ca.name,
            ca.valid_from,
            ccd.compliance_category,
            ccd.compliance_sub_category,
            ccd.sub_category_name,
            ccd.compliance_date,
            ccd.next_compliance_date
        FROM 
            `tabCompliance Agreement` as ca,
            `tabCompliance Category Details` as ccd
        WHERE
            ccd.parent = ca.name AND
            ccd.parentfield = 'compliance_category_details' AND
            ccd.parenttype = 'Compliance Agreement' 
    """

    if filters.get("customer"):
        query += " AND ca.customer = '{0}'".format(filters.get("customer"))

    if filters.get("name"):
        query += " AND ca.name = '{0}'".format(filters.get("name"))

    if filters.get("compliance_category"):
        query += " AND ccd.compliance_category = '{0}'".format(filters.get("compliance_category"))

    if filters.get("compliance_sub_category"):
        query += " AND ccd.compliance_sub_category = '{0}'".format(filters.get("compliance_sub_category"))

    if filters.get("sub_category_name"):
        query += " AND ccd.sub_category_name = '{0}'".format(filters.get("sub_category_name"))

    if filters.get("compliance_date"):
        query += " AND ccd.compliance_date = '{0}'".format(filters.get("compliance_date"))

    if filters.get("next_compliance_date"):
        query += " AND ccd.next_compliance_date = '{0}'".format(filters.get("next_compliance_date"))

    query += " GROUP BY ca.name, ccd.compliance_category,ccd.compliance_sub_category, ccd.sub_category_name, ca.valid_from, ccd.compliance_date, ccd.next_compliance_date;"

    # Execute the query and fetch data
    data = frappe.db.sql(query, as_dict=True)

    return data