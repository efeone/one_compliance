frappe.ui.form.on('Event',{
    refresh: function(frm) {
        frm.add_custom_button(__('Add Employees'), function() {
            frappe.call({
                method: 'one_compliance.one_compliance.utils.get_employee_list_for_hod',
                callback: function(r) {
                    if (r.message) {
                        let employees = r.message;

                        if (!employees.length) {
                            frappe.msgprint(__('No employees available to select.'));
                            return;
                        }

                        let d = new frappe.ui.Dialog({
                            title: __('Select Employee'),
                            fields: [
                                {
                                    fieldtype: 'HTML',
                                    fieldname: 'employee_list',
                                    options: `
                                        <div style="max-height: 300px; overflow-y: auto;">
                                            <input type="text" id="employee_search" placeholder="Search Employees..." style="width: 100%; padding: 5px; margin-bottom: 10px;">
                                            <ul id="employee_list" style="list-style-type: none; padding-left: 0;">
                                                ${employees.map(emp => `
                                                    <li style="padding: 5px 0; border-bottom: 1px solid #ddd;" data-employee-id="${emp.employee_id}" data-employee-name="${emp.employee_name}">
                                                        <strong>${emp.employee_id}</strong> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; ${emp.employee_name}
                                                    </li>
                                                `).join('')}
                                            </ul>
                                        </div>
                                    `
                                }
                            ],
                            primary_action_label: 'Close',
                            primary_action() {
                                d.hide();
                            }
                        });

                        // Handle Search Input
                        d.$wrapper.find('#employee_search').on('input', frappe.utils.debounce(function() {
                            let searchValue = $(this).val().toLowerCase();
                            d.$wrapper.find('#employee_list li').each(function() {
                                let employeeText = $(this).text().toLowerCase();
                                $(this).toggle(employeeText.indexOf(searchValue) > -1);
                            });
                        }, 300));  // Added debounce for better performance

                        // Handle Employee Selection
                        d.$wrapper.find('li').on('click', function() {
                            let $li = $(this);
                            let employee_id = $li.data('employee-id');
                            let employee_name = $li.data('employee-name');

                            if ($li.hasClass('selected')) {
                                frappe.msgprint(__('Employee {0} is already added.', [employee_id]));
                                return;
                            }

                            frm.add_child('event_participants', {
                                reference_doctype: 'Employee',
                                reference_docname: employee_id,
                                custom_participant_name: employee_name
                            });
                            frm.refresh_field('event_participants');
                            frappe.show_alert({
                                message: __('Employee {0} added', [employee_id]),
                                indicator: 'blue'
                            });

                            $li.addClass('selected').off('click').css('background-color', '#e6f7ff'); // Visual cue
                        });

                        d.show();
                    } else {
                        frappe.msgprint(__('You do not have permission to view employees.'));
                    }
                }
            });
        });

        frm.add_custom_button(
            __("Create Proforma Invoice"),
            function () {
                if (frm.doc.status === 'Completed') {
                    if (frm.doc.custom_is_billable == 1) {
                      if(frm.doc.custom_service_description){
                        if(frm.doc.custom_customer){
                          create_sales_order(frm);
                          frappe.msgprint('Proforma Invoice Created Successfully');
                        }else{
                          frappe.msgprint('Please Select the Client');
                        }
                      }else{
                        frappe.msgprint('Pleas Add the Service Description');
                      }
                    }else {
                        frappe.msgprint('Please Mark this Event as Billable');
                    }
                }else {
                    frappe.msgprint('Please mark the event as Completed to proceed.');
                }
            }
        );
        frm.add_custom_button(
            __("Employee Timesheet"),
            function () {
                if (frm.doc.status == 'Completed' && frm.doc.starts_on && frm.doc.ends_on) {
                    make_time_sheet_entry(frm);
                    frappe.msgprint('Timesheet Created Successfully');
                } else {
                    frappe.msgprint('Please Ensure the Event is Marked as Completed and the End Date is Added');
                }
            }
        );
        frm.remove_custom_button("Add Employees", "Add Participants");
    },

    setup: function(frm) {
        frm.set_query('custom_service', () => {
            return {
                filters: {
                    is_meeting_only: true
                }
            };
        });
    },
    custom_service: function(frm) {
        if (frm.doc.custom_service) {
            frappe.db.get_value('Compliance Sub Category', frm.doc.custom_service, 'rate')
            .then(r => {
                if (r.message && r.message.rate) {
                    frm.set_value('custom_rate', r.message.rate);
                    frm.set_df_property('custom_rate', 'read_only', 0);
                    frm.refresh_field('custom_rate');
                }
            });
        }
    },
    set_time_out : function(frm){
      frm.set_df_property("custom_rate", "read_only",frm.doc.__islocal ? 0 : 1);
    }
});

let create_sales_order = function(frm) {
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

let make_time_sheet_entry = function(frm) {
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

frappe.ui.form.on('Event Participants', {
    reference_docname: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (row.reference_doctype === 'Employee') {
            frappe.db.get_value('Employee', row.reference_docname, 'employee_name', (r) => {
                if (r && r.employee_name) {
                    frappe.model.set_value(cdt, cdn, 'custom_participant_name', r.employee_name);
                }
            });
        } else if (row.reference_doctype === 'Lead') {
            frappe.db.get_value('Lead', row.reference_docname, 'title', (r) => {
                if (r && r.title) {
                    frappe.model.set_value(cdt, cdn, 'custom_participant_name', r.title);
                }
            });
        }
    }
});
