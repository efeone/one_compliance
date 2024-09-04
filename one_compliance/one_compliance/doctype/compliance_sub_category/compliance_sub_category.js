// Copyright (c) 2023, efeone and contributors
// For license information, please see license.txt

frappe.ui.form.on('Compliance Sub Category', {
	refresh: function(frm) {
		set_filters(frm);
		if(!frm.is_new() && !frm.doc.project_template){
			//custom button to create project template and route to  project template doctype
			frm.add_custom_button('Create Project Template', () =>{
				frappe.model.open_mapped_doc({
					method: 'one_compliance.one_compliance.doctype.compliance_sub_category.compliance_sub_category.create_project_template_custom_button',
					frm: cur_frm
				});
			});
		}
		if(!frm.is_new() && frm.doc.project_template){
			//custom button to create project and create project
			frm.add_custom_button('Create Project', () =>{
				create_project_dialog(frm)
			});
		}
		if(frm.is_new()){
			set_notification_templates(frm);
		}
		if (frm.doc.item_code) {
        if (frm.doc.enabled) {
            frappe.call({
                method: 'one_compliance.one_compliance.doctype.compliance_sub_category.compliance_sub_category.enable_related_item',
                args: {
                    'item_name': frm.doc.item_code
                }
            });
        } else {
            frappe.call({
                method: 'one_compliance.one_compliance.doctype.compliance_sub_category.compliance_sub_category.disable_related_item',
                args: {
                    'item_name': frm.doc.item_code
                }
            });
        }
    }
	},
	internal: function(frm) {
			if (frm.doc.internal) {
					frm.set_value('is_billable', 0);
					frm.set_df_property('is_billable', 'read_only', 1);
			} else {
					frm.set_df_property('is_billable', 'read_only', 0);
			}
	},
	is_billable: function(frm) {
			if (frm.doc.is_billable) {
					frm.set_value('internal', 0);
					frm.set_df_property('internal', 'read_only', 1);
			} else {
					frm.set_df_property('internal', 'read_only', 0);
			}
	},
	validate: function(frm) {
		if (frm.doc.day) {
			set_validation_for_day(frm)
		}
	},
	day: function(frm){
		set_validation_for_day(frm)
	},
	onload: function(frm) {
		if (frm.is_new()) {
		  frm.clear_table('compliance_executive');
		  frm.refresh_field('compliance_executive');
		}
  }
});

let create_project_dialog = function(frm){

	let d = new frappe.ui.Dialog({
    title: 'Enter details',
    fields: [
        {
            label: 'Customer',
            fieldname: 'customer',
            fieldtype: 'Link',
						options: 'Customer',
						reqd: 1,
						get_query: function () {
              return {
                filters: {
                  disabled: 0
                }
              };
            }
        },
        {
            label: 'Project Template',
            fieldname: 'project_template',
            fieldtype: 'Link',
						options: 'Project Template',
						reqd: 1,
						default: frm.doc.project_template
        },
        {
            label: 'Expected Start Date',
            fieldname: 'expected_start_date',
            fieldtype: 'Date',
						reqd: 1,
						default: 'Today'
        },
				{
            label: 'Expected End Date',
            fieldname: 'expected_end_date',
						reqd: 1,
            fieldtype: 'Date'
        }
    ],
    size: 'lare',
    primary_action_label: 'Create Project',
    primary_action(values) {
			frappe.call({
				method:'one_compliance.one_compliance.doctype.compliance_sub_category.compliance_sub_category.create_project_manually',
				args:{
					'project_template':values.project_template ,
					'customer': values.customer,
					'expected_start_date': values.expected_start_date,
					'expected_end_date': values.expected_end_date,
				},
				callback:function(r){
					if (r.message) {
						frm.reload_doc()
					}
				}
			});
        d.hide();
    }
});

d.show();
}

let set_notification_templates = function(frm){
	frappe.call({
		method:'one_compliance.one_compliance.doctype.compliance_sub_category.compliance_sub_category.get_notification_details',
		callback: (r) => {
			if(r.message){
				// set value to customer and company
				if(!frm.doc.task_before_due_date_notification){
					frm.set_value('task_before_due_date_notification', r.message.task_before_due_date_notification)
				}
				if(!frm.doc.task_complete_notification){
					frm.set_value('task_complete_notification_for_director', r.message.task_complete_notification_for_director)
				}
				if(!frm.doc.task_overdue_notification){
					frm.set_value('task_overdue_notification_for_employee', r.message.task_overdue_notification_for_employee)
				}
				if(!frm.doc.task_overdue_notification){
					frm.set_value('task_overdue_notification_for_director', r.message.task_overdue_notification_for_director)
				}
				if(!frm.doc.no_action_taken_notification){
					frm.set_value('no_action_taken_notification_for_director', r.message.no_action_taken_notification_for_director)
				}
				if(!frm.doc.project_complete_notification_for_customer){
					frm.set_value('project_complete_notification_for_customer', r.message.project_complete_notification_for_customer)
				}
				if(!frm.doc.project_before_due_date_notification){
					frm.set_value('project_before_due_date_notification', r.message.project_before_due_date_notification)
				}
			}
		}
	})
}

let set_validation_for_day = function(frm) {
	//Method to set an error message to enter value day between 1 and 31
	if (frm.doc.day < 1 || frm.doc.day > 31) {
		frappe.throw('The number of days should be between 1 and 31.')
		frm.set_value('day', '');
	}
}

function set_filters(frm) {
	console.log("test");
	let compliance_category = frm.doc.compliance_category
	// Applied filter in child table for active employee
	frm.set_query('employee', 'compliance_executive' ,(frm, cdt, cdn) => {
					// To set filter for employee in Compliance Executive child table
					var d = locals[cdt][cdn];
	if (frm.compliance_category){
		return {
			query: 'one_compliance.one_compliance.doctype.compliance_sub_category.compliance_sub_category.set_filter_for_employee',
			filters: {
				'compliance_category': compliance_category
			}
		};
	}
	});

	frm.set_query('default_income_account', 'default_account', (doc, cdt, cdn) => {
    let d = locals[cdt][cdn];
    return {
      filters: {
        is_group:0,
        company: d.company
      }
    }
  });
}
