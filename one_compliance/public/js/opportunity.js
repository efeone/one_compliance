frappe.ui.form.on('Opportunity',{
    refresh: function(frm) {
        if(!frm.is_new()){
            setTimeout(() => {
                frm.remove_custom_button('Supplier Quotation','Create')
                frm.remove_custom_button('Request For Quotation','Create')
            })
            frm.add_custom_button(__('Engagement Letter'), function () {
                frm.trigger("make_engagement_letter");
            },__("Create"));

            frm.add_custom_button('Create Event',() =>{
                create_event(frm)
            });
            make_buttons(frm);
        }
    },
    make_engagement_letter: function (frm) {
        frappe.model.open_mapped_doc({
            method: 'one_compliance.one_compliance.doc_events.oppotunity.make_engagement_letter',
            frm: cur_frm
        });
    },
});

function create_event(frm) {
    let d = new frappe.ui.Dialog({
        title: 'Enter details',
        fields: [
            {
                label: 'Event Category',
                fieldname: 'event_category',
                fieldtype: 'Select',
                options: "Events\nMeeting\nCall\nSent/Received Email\nOther",
                default: 'Meeting'
            },
            {
                fieldtype: "Column Break",
                fieldname: "col_break_1",
            },
            {
                label: 'Date',
                fieldname: 'start_on',
                fieldtype: 'Datetime',
                reqd: 1,
            },
            {
                fieldtype: "Section Break",
            },
            {
                label: 'Subject',
                fieldname: 'subject',
                fieldtype: 'Data',
                reqd: 1,
            },
            {
                label: 'Attendees',
                fieldname: 'attendees',
                fieldtype: 'Table',
                fields: [
                    {
                        label: 'Attendee Type',
                        fieldname: 'attendee_type',
                        fieldtype: 'Select',
                        in_list_view: 1,
                        options: ['Customer', 'Employee', 'Lead'],
                        onchange: function(row) {
                            let attendees = d.get_value('attendees');
                            // Iterate over each attendee object in the array
                            for (let i = 0; i < attendees.length; i++) {
                                let attendeeType = attendees[i].attendee_type;
                            }
                        }
                    },
                    {
                        label: 'Attendee',
                        fieldname: 'attendee',
                        fieldtype: 'Link',
                        options: function() {
                            let attendees = d.get_value('attendees');
                            let options = " ";

                            for (let i = 0; i < attendees.length; i++) {
                                let attendeeType = attendees[i].attendee_type;

                                if (attendeeType === "Customer") {
                                    options = "Customer";
                                } else if (attendeeType === "Employee") {
                                    options = "Employee";
                                } else if (attendeeType === "Lead") {
                                    options = "Lead";
                                }
                            }
                            return options;
                        },
                        in_list_view: 1,
                    },
                ],
            }
        ],
        primary_action_label: 'Create',
        primary_action(values) {
            frappe.call({
                method: 'one_compliance.one_compliance.doc_events.oppotunity.create_event_from_opportunity',
                args: {
                    oppotunity:frm.doc.name,
                    event_category: values.event_category,
                    start_on: values.start_on,
                    subject: values.subject,
                    attendees: values.attendees
                },
                callback: function (r) {
                    if (r.message) {
                        frappe.msgprint('Event created successfully');
                        d.hide();
                    }
                }
            });
        }
    });
    d.show();
}


function make_buttons(frm){
    if (!frm.is_new() && frm.doc.status !== 'Converted') {
        let msg = 'System will create a Customer and Sales Order. Proceed?';
        if (frm.doc.opportunity_from === 'Customer') {
            msg = 'System will create a Sales Order. Proceed?';
        }

        frm.add_custom_button('Sales Order', () => {
            if (!frm.doc.items.length) {
                frm.scroll_to_field('items');
                frappe.throw({
                    message: __("Please fill the `Services` before creating Sales Order."),
                    title: __("Missing fields")
                });
            }

            frappe.confirm(msg, () => {
                frappe.call({
                    method: 'one_compliance.one_compliance.doc_events.oppotunity.create_sales_order',
                    args: { opportunity: frm.doc.name },
                    callback: (r) => {
                        if (!r.exc) {
                            const d = r.message;
                            frappe.model.with_doctype('Sales Order', () => {
                                const doc = frappe.model.get_new_doc('Sales Order');
                                doc.customer = d.customer;
                                doc.opportunity = frm.doc.name;
                                d.items.forEach(i => {
                                    let row = frappe.model.add_child(doc, 'items');
                                    Object.assign(row, i);
                                });
                                frappe.set_route('Form', 'Sales Order', doc.name);
                            });
                        }
                    }
                });
            });
        }, 'Create');
    }
}