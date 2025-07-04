// Copyright (c) 2025, efeone and contributors
// For license information, please see license.txt

frappe.query_reports["Project Summary Detail"] = {
	"filters": [
{
  fieldname: "from_date",
  label: __("From Date"),
  fieldtype: "Date",
  default: "Today",
},
{
  fieldname: "to_date",
  label: __("To Date"),
  fieldtype: "Date",
  default: "Today",
},
{
	fieldname: "employee",
	label: __("Employee"),
	fieldtype: "Link",
	options: "Employee",
},
{
	fieldname: "client",
	label: __("Customer"),
	fieldtype: "Link",
	options: "Customer",
},
{
	fieldname: "project",
	label: __("Project"),
	fieldtype: "Link",
	options: "Project",
},
{
	fieldname: "status",
	label: __("Status"),
	fieldtype: "Select",
	options: "\nOpen\nWorking\nCompleted\nOverdue",
},
{
	fieldname: "reference_type",
	label: __("Reference Type"),
	fieldtype: "Select",
	options: "\nProject\nEvent",
},
{
	fieldname: "department",
	label: __("Department"),
	fieldtype: "Link",
	options: "Department",
},
	]
};
