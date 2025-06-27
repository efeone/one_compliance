// Copyright (c) 2025, efeone and contributors
// For license information, please see license.txt

frappe.query_reports["Sales Order Receivable Summary"] = {
  onload: function (report) {
    if (!report.get_filter_value('range')) {
      report.set_filter_value('range', '30,60,90,120');
    }

    if (!report.get_filter_value('ageing_based_on')) {
      report.set_filter_value('ageing_based_on', 'Posting Date');
    }

    if (!report.get_filter_value('report_date')) {
      report.set_filter_value('report_date', frappe.datetime.get_today());
    }

    // Add custom button
    report.page.add_inner_button('Sales Order Receivable', () => {
      frappe.set_route('query-report', 'Sales Order Receivable');
    });
  },

  filters: [
    {
      fieldname: "company",
      label: "Company",
      fieldtype: "Link",
      options: "Company"
    },
    {
      fieldname: "customer",
      label: "Customer",
      fieldtype: "Link",
      options: "Customer"
    },
    {
      fieldname: "report_date",
      label: "Report Date",
      fieldtype: "Date",
      default: frappe.datetime.get_today()
    },
    {
      fieldname: "from_date",
      label: "From Date",
      fieldtype: "Date"
    },
    {
      fieldname: "to_date",
      label: "To Date",
      fieldtype: "Date"
    },
    {
      fieldname: "ageing_based_on",
      label: "Ageing Based On",
      fieldtype: "Select",
      options: ["Posting Date", "Due Date"],
      default: "Posting Date"
    },
    {
      fieldname: "range",
      label: "Ageing Ranges",
      fieldtype: "Data",
      default: "30,60,90,120",
      description: "Comma-separated e.g. 30,60,90"
    },
    {
      fieldname: "territory",
      label: "Territory",
      fieldtype: "Link",
      options: "Territory"
    },
    {
      fieldname: "customer_group",
      label: "Customer Group",
      fieldtype: "Link",
      options: "Customer Group"
    },
    {
      fieldname: "include_invoiced",
      label: "Include Invoiced",
      fieldtype: "Check",
      default: 0
    },
    {
      fieldname: "include_paid",
      label: "Include Paid",
      fieldtype: "Check",
      default: 0
    }
  ]
};
