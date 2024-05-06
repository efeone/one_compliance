// Copyright (c) 2024, efeone and contributors
// For license information, please see license.txt

frappe.query_reports["Department wise Project and Invoice Summary"] = {
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
        }
	]
};
