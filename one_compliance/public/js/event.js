frappe.ui.form.on('Event', {
    refresh: function(frm) {
        frm.add_custom_button(
            __("Add Employees"),
            function () {
                new frappe.desk.eventParticipants(frm, "Employee");
            }
        );
        frm.add_custom_button(
            __("Create Proforma Invoice"),
            function () {
                if (frm.doc.custom_is_billable == 1) {
                    create_sales_order(frm);
                } else {
                    frappe.msgprint('Not Billable');
                }
            }
        );
        frm.add_custom_button(
            __("Employee Timesheet"),
            function () {
                if (frm.doc.status == 'Completed' && frm.doc.starts_on && frm.doc.ends_on) {
                    make_time_sheet_entry(frm);
                } else if (!frm.doc.custom_service && !frm.doc.custom_service_description) {
                    frappe.msgprint('Required fields: Service and Service description');
                } else if (!frm.doc.custom_service) {
                    frappe.msgprint('Required fields: Service');
                } else if (!frm.doc.custom_service_description) {
                    frappe.msgprint('Required fields: Service description');
                }
            }
        );
        frm.remove_custom_button("Add Employees", "Add Participants");
    },

    setup: function(frm) {
        // Filter for custom_service field
        frm.set_query('custom_service', () => {
            return {
                filters: {
                    is_meeting_only: true
                }
            };
        });
    },

    status: function(frm) {
        if (frm.doc.status == 'Completed' && frm.doc.starts_on && frm.doc.ends_on) {
            make_time_sheet_entry(frm);
        } else if (!frm.doc.starts_on || !frm.doc.ends_on) {
            frappe.msgprint("Required fields: Starts On and Ends On.");
        } else if (frm.doc.status != 'Completed') {
            frappe.msgprint("Status should be 'Completed' to create Timesheet.");
        }
    }
});

let create_sales_order = function (frm) {
    frappe.call({
        method: 'one_compliance.one_compliance.doc_events.sales_order.create_sales_order_from_event',
        args: {
            'event': frm.doc.name,
            'customer': frm.doc.custom_customer,
            'sub_category': frm.doc.custom_service,
            'rate': frm.doc.custom_rate,
            'description': frm.doc.custom_service_description
        },
        callback: function(r) {
            if (r.message) {
                frm.reload_doc();
            }
        }
    });
};

let make_time_sheet_entry = function (frm) {
    frappe.call({
        method: 'one_compliance.one_compliance.utils.make_time_sheet_entry',
        args: {
            'event': frm.doc.name
        },
        callback: function(r) {
            if (r.message) {
                frm.reload_doc();
            }
        }
    });
};
