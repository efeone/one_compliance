// Copyright (c) 2023, efeone and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Compliance Agreement Summary"] = {
	"filters": [
        {
            "label": __("Customer"),
            "fieldname": "customer",
            "fieldtype": "Link",
            "options": "Customer",
        },
        {
            "label": __("Agreement"),
            "fieldname": "name",
            "fieldtype": "Data",
        },
        {
            "label":__("Valid From"),
            "fieldname":"valid_from",
            "fieldtype":"Date",
        },
        {
            "label":__("Compliance Category"),
            "fieldname": "compliance_category",
            "fieldtype":"Link",
            "options": "Compliance Category",
        },
        {
            "label":__("Compliance Sub Category"),
            "fieldname": "compliance_sub_category",
            "fieldtype":"Link",
            "options": "Compliance Sub Category",
        },
        {
            "label":__("Sub Category Name"),
            "fieldname":"sub_category_name",
            "fieldtype":"Data",
        },
        
        {
            "label":__("Compliance Date"),
            "fieldname":"compliance_date",
            "fieldtype":"Date",
        },
        {
            "label":__("Next Compliance Date"),
            "fieldname":"next_compliance_date",
            "fieldtype":"Date",
        }
	],
};

