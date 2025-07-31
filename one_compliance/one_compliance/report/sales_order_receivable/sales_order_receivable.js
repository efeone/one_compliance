// Copyright (c) 2025, efeone and contributors
// For license information, please see license.txt

frappe.query_reports["Sales Order Receivable"] = {
    onload: function (report) {
          report.page.add_inner_button("Sales Order Receivable Aging Summary", function () {
              frappe.set_route("query-report", "Sales Order Receivable Aging Summary");
          });
      },
    filters: [
        {
            fieldname: "company",
            label: __("Company"),
            fieldtype: "Link",
            options: "Company",
            reqd: 1,
            default: frappe.defaults.get_user_default("Company"),
        },
        {
            fieldname: "ageing_based_on",
            label: __("Ageing Based On"),
            fieldtype: "Select",
            options: "Due Date\nPosting Date",
            default: "Due Date",
        },
        {
            fieldname: "from_date",
            label: __("From Date"),
            fieldtype: "Date",
            default: frappe.datetime.add_months(frappe.datetime.get_today(), -1),
        },
        {
            fieldname: "to_date",
            label: __("To Date"),
            fieldtype: "Date",
            default: frappe.datetime.get_today(),
        },
        {
            fieldname: "customer",
            label: __("Customer"),
            fieldtype: "Link",
            options: "Customer",
        },
        {
            fieldname: "customer_group",
            label: __("Customer Group"),
            fieldtype: "Link",
            options: "Customer Group",
        },
        {
            fieldname: "territory",
            label: __("Territory"),
            fieldtype: "Link",
            options: "Territory",
        },
        {
            fieldname: "range",
            label: __("Ageing Range"),
            fieldtype: "Data",
            default: "30, 60, 90, 120",
        },
        {
            fieldname: "include_invoiced",
            label: __("Include Invoiced"),
            fieldtype: "Check",
        },
        {
            fieldname: "include_paid",
            label: __("Include Paid"),
            fieldtype: "Check",
        }
    ],

    formatter: function (value, row, column, data, default_formatter) {
        value = default_formatter(value, row, column, data);
        if (data && data.bold) {
            value = `<b>${value}</b>`;
        }
        return value;
    }
};
