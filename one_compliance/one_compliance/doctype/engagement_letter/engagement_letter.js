// Copyright (c) 2023, efeone and contributors
// For license information, please see license.txt

frappe.ui.form.on('Engagement Letter', {
    setup: function (frm) {
        // Fetch current date and time
        var currentDateTime = frappe.datetime.now_datetime();

        // Set the fetched date and time to the fields
        frm.set_value('posting_date', frappe.datetime.get_today());
    },
    refresh: function (frm) {
        // Add your custom button inside the refresh function
        if (!frm.doc.__islocal) {
            // Form has been saved, add the custom button
            frm.add_custom_button(__('Approve'), function () {
                if (frm.doc.engagement_letter_types === 'Consulting Engagement Letter') {
                    // Execute make_customer and make_project only for Consulting Engagement Letter
                    frm.trigger("make_customer");
                    frm.trigger("make_project");
                }
                else if(frm.doc.engagement_letter_types === 'Preliminary analysis & report') {
                    frm.set_value('engagement_letter_types', 'Consulting Engagement Letter');
                    frm.trigger("create_engagement_letter");
                    
                }
                
                
            });
        }

    },
    make_customer: function (frm) {
        frappe.call({
            method: 'one_compliance.one_compliance.doctype.engagement_letter.engagement_letter.make_customer',
            args: {
                customer: frm.doc.name,
                customer_group: frm.doc.customer_group,
                territory: frm.doc.territory,
                opportunity_name: frm.doc.opportunity,
                customer_type: frm.doc.customer_type,
            },
            freeze: true,
            callback: function (r) {
                console.log(r);
            },
        });
    },
    make_project: function (frm) {
        frappe.model.open_mapped_doc({
            method: 'one_compliance.one_compliance.doctype.engagement_letter.engagement_letter.make_project',
            frm: cur_frm
        });
    },
    create_engagement_letter: function (frm) {

        frappe.model.open_mapped_doc({
            method: 'one_compliance.one_compliance.doctype.engagement_letter.engagement_letter.create_engagement_letter',
            frm: cur_frm
        });
    },
    
    opportunity: function (frm) {
        if (frm.doc.opportunity) {
            frappe.call({
                method: 'frappe.client.get_value',
                args: {
                    doctype: 'Opportunity',
                    filters: { name: frm.doc.opportunity },
                    fieldname: ['contact_person', 'contact_email', 'contact_mobile']
                },
                callback: function (r) {
                    if (r.message) {
                        frm.set_value('full_name', r.message.contact_person);
                        frm.set_value('email', r.message.contact_email);
                        frm.set_value('mobile', r.message.contact_mobile);
                    }
                }
            });
        }
    },
    terms: function (frm) {
        if (frm.doc.terms && !frm.doc.description) {
            frappe.call({
                method: 'one_compliance.one_compliance.doctype.engagement_letter.engagement_letter.get_terms_description',
                args: {
                    terms: frm.doc.terms
                },
                callback: function (r) {
                    if (r.message) {
                        frm.set_value('description', r.message);
                    }
                }
            });
        }
    },
    working_team: function (frm) {
        get_working_team(frm);
    }

});

frappe.ui.form.on('YourDocType', {
    assignEmployeeToProject: function (frm) {
        var engagementLetterName = frm.doc.child_table_name[0].engagement_letter_name;

        frappe.call({
            method: 'one_compliance.one_compliance.doctype.engagement_letter.engagement_letter.assign_employee_to_project',
            args: {
                engagement_letter_name: engagementLetterName
            },
            callback: function (r) {
                if (r.message) {
                    frappe.msgprint(r.message);
            
                }
            }
        });
    }
});


let get_working_team = function (frm){
    frappe.call({
        method:'one_compliance.one_compliance.doctype.engagement_letter.engagement_letter.get_working_team',
        args:{
            employee_group : frm.doc.working_team
        },
        callback: function(r) {
            if (r.message && r.message.length > 0) {
              frm.clear_table('employees');
              r.message.forEach(item => {
                let employee = frm.add_child('employees');
                employee.employee = item.employee;
                employee.employee_name = item.employee_name;
                employee.user_id = item.user_id
                
              });
              frm.refresh_field('employees');
            }
        }      
    })
}