// Copyright (c) 2023, efeone and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Employee Checkin Summary"] = {
	"filters": [
	  {
		"fieldname": "from_date",
		"label": __("From Date"),
		"fieldtype": "Date",
		"default": frappe.datetime.get_today()
	  },
	  {
		"fieldname": "to_date",
		"label": __("To Date"),
		"fieldtype": "Date",
		"default": frappe.datetime.get_today()
	  },
	  {
		"fieldname": "period",
		"label": __("Period"),
		"fieldtype": "Select",
		"options": [
		  { "value": "", "label": __("Select Period") },
		  { "value": "Last Week", "label": __("Weekly") },
		  { "value": "Last Month", "label": __("Monthly") },
		  { "value": "Last Quarter", "label": __("Quarterly") },
		  { "value": "Last Year", "label": __("Yearly") },
		],
	  },
	  {
		"fieldname": "department",
		"label": __("Department"),
		"fieldtype": "Select",
		"options": "\nGST - C\nIncome Tax - C\nROC - C\nConsulting - C",
	  },
	],
  };
  
  // Add event listeners to handle clearing of date filters
  frappe.ui.form.on("Employee Checkin Summary", {
	from_date: function(frm) {
	  if (!frm.doc.from_date) {
		frm.doc.from_date = "";
	  }
	},
	to_date: function(frm) {
	  if (!frm.doc.to_date) {
		frm.doc.to_date = "";
	  }
	},
  });
  