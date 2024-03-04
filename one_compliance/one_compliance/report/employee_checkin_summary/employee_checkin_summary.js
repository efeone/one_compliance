// Copyright (c) 2023, efeone and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Employee Checkin Summary"] = {
	"filters": [
	  {
		"fieldname": "from_date",
		"label": __("From Date"),
		"fieldtype": "Date",
		"default": frappe.datetime.month_start()
	  },
	  {
		"fieldname": "to_date",
		"label": __("To Date"),
		"fieldtype": "Date",
		"default":  frappe.datetime.month_end()
	  },
	  {
		"fieldname": "department",
		"label": __("Department"),
		"fieldtype": "Link",
		"options": "Department",
		"get_query": function () {
			return {
				"doctype": "Department",
			};
		}
	  }	],
  };
  