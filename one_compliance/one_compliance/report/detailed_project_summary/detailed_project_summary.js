// Copyright (c) 2024, efeone and contributors
// For license information, please see license.txt

frappe.query_reports["Detailed Project Summary"] = {
  filters: [
    {
      label: __("From Date"),
      fieldname: "from_date",
      fieldtype: "Date",
      default: "Today",
      reqd: 1,
    },
    {
      label: __("To Date"),
      fieldname: "to_date",
      fieldtype: "Date",
      default: "Today",
      reqd: 1,
    },
    {
      label: __("Department"),
      fieldname: "department",
      fieldtype: "Link",
      options: "Department",
      get_query: function () {
        return {
          filters: {
            is_compliance: 1,
          },
        };
      },
    },
    {
      label: __("Customer"),
      fieldname: "customer",
      fieldtype: "Link",
      options: "Customer",
    },
    {
      label: __("Status"),
      fieldname: "status",
      fieldtype: "Select",
      options: "\nOpen\nInvoiced\nPaid\nHold\nOverdue\nCompleted\nCancelled",
    },
    {
      label: __("Reference Type"),
      fieldname: "reference_type",
      fieldtype: "Select",
      options: "\nProject\nEvent",
    },
    {
      label: __("Project"),
      fieldname: "project",
      fieldtype: "Link",
      options: "Project",
    },
    {
      label: __("Invoiced"),
      fieldname: "invoiced",
      fieldtype: "Select",
      options: "\nYes\nNo",
    },
    // {
    //     label: __("Employee"),
    //     fieldname: "employee",
    //     fieldtype: "Link",
    //     options: "Employee",
    // 	get_query: function(){
    // 		return {
    // 			filters: {
    // 				'department': frappe.query_report.get_filter_value('department')
    // 			}
    // 		}
    // 	}
    // },
  ],
  formatter: function (value, row, column, data, default_formatter) {
    value = default_formatter(value, row, column, data);
    if (data.department_row) {
      value = $(`<span>${value}</span>`);
      var $value = $(value).css("font-weight", "bold");
      value = $value.wrap("<p></p>").parent().html();
    }
    return value;
  },
};
