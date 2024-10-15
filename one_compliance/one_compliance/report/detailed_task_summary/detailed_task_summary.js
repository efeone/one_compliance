// Copyright (c) 2024, efeone Pvt Ltd and contributors
// For license information, please see license.txt

frappe.query_reports["Detailed Task Summary"] = {
  filters: [
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
      label: __("Client"),
      fieldtype: "Link",
      options: "Customer",
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
      fieldname: "sub_category",
      label: __("Sub Category"),
      fieldtype: "Link",
      options: "Compliance Sub Category",
    },
    {
      fieldname: "department",
      label: __("Department"),
      fieldtype: "Link",
      options: "Department",
    },
  ],
};
