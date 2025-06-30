// Copyright (c) 2025, efeone and contributors
// For license information, please see license.txt

frappe.query_reports["Task Summary"] = {
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
      fieldname: "employee",
      label: __("Employee"),
      fieldtype: "Link",
      options: "Employee",
    },
    {
      fieldname: "status",
      label: __("Status"),
      fieldtype: "Select",
      options: "\nOpen\nWorking\nCompleted",
    },
    {
      fieldname: "reference_type",
      label: __("Reference Type"),
      fieldtype: "Select",
      options: "\nTask\nEvent",
    },
    {
      fieldname: "compliance_sub_category",
      label: __("Compliance Sub Category"),
      fieldtype: "Link",
      options: "Compliance Sub Category",
    },
    {
      fieldname: "department",
      label: __("Department"),
      fieldtype: "Link",
      options: "Department",
    },
	]
};
