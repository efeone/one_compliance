// Copyright (c) 2024, efeone and contributors
// For license information, please see license.txt

frappe.query_reports["Detailed Project Summary"] = {
	"filters": [
		{
            label: __("From Date"),
            fieldname: "from_date",
            fieldtype: "Date",
			default: frappe.datetime.add_months(frappe.datetime.get_today(), -1),
			reqd: 1
        },
		{
            label: __("To Date"),
            fieldname: "to_date",
            fieldtype: "Date",
			default: frappe.datetime.get_today(),
			reqd: 1
        },
		{
            label: __("Department"),
            fieldname: "department",
            fieldtype: "Link",
            options: "Department",
			get_query: function(){
					return {
						filters: {
							'is_compliance': 1
						}
					}
				}
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
	}
};
