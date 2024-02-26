// Copyright (c) 2023, efeone and contributors
// For license information, please see license.txt

frappe.ui.form.on('Compliance Settings', {
	refresh: function(frm) {
    if (frappe.session.user == "Administrator"){
      frm.add_custom_button('Create Projects', () => {
        create_projects_manually_perticular_date(frm)
      })
    }
		if (frappe.session.user == "Administrator"){
      frm.add_custom_button('Change Compliance Date', () => {
        change_perticular_compliance_date(frm)
      })
    }
    //filter for task_before_due_date_notification based on doctype
    frm.set_query('task_before_due_date_notification', function(){
      return {
        filters: {
          doctype_name : 'Task'
        }
      }
    })

    //filter for task_overdue_notification_for_employee based on doctype
    frm.set_query('task_overdue_notification_for_employee', function(){
      return {
        filters: {
          doctype_name : 'Task'
        }
      }
    })

    //filter for task_overdue_notification_for_director based on doctype
    frm.set_query('task_overdue_notification_for_director', function(){
      return {
        filters: {
          doctype_name : 'Task'
        }
      }
    })

    //filter for task_complete_notification_for_director based on doctype
    frm.set_query('task_complete_notification_for_director', function(){
      return {
        filters: {
          doctype_name : 'Task'
        }
      }
    })

    //filter for no_action_taken_notification_for_director based on doctype
    frm.set_query('no_action_taken_notification_for_director', function(){
      return {
        filters: {
          doctype_name : 'Task'
        }
      }
    })

    //filter for project_complete_notification_for_customer based on doctype
    frm.set_query('project_complete_notification_for_customer', function(){
      return {
        filters: {
          doctype_name : 'Project'
        }
      }
    })

    //filter for digital_signature_expiry_notification based on doctype
    frm.set_query('digital_signature_expiry_notification', function(){
      return {
        filters: {
          doctype_name : 'Digital Signature'
        }
      };
    });
	}
});

let create_projects_manually_perticular_date = function(frm){
  //function to set the craete of compliance project manually
  let d = new frappe.ui.Dialog({
    title: 'Manual Project Creation',
    fields: [
        {
            label: 'Starting Date',
            fieldname: 'starting_date',
            fieldtype: 'Date',
            reqd: 1
        },
    ],
    primary_action_label: 'Create Project',
    primary_action(values) {
      if(values.starting_date){
        frappe.call({
          method:'one_compliance.one_compliance.doctype.compliance_settings.compliance_settings.manual_project_creations',
          args:{
            'starting_date': values.starting_date,
          },
          callback:function(r){
            if (r.message) {
              frm.reload_doc()
            }
          }
        });
      }
        d.hide();
    }
  });
  d.show();
}

let change_perticular_compliance_date = function(frm){
  //function to change the compliance date manually
  let d = new frappe.ui.Dialog({
    title: 'Compliance Date Updation',
    fields: [
        {
            label: 'Compliance Date',
            fieldname: 'compliance_date',
            fieldtype: 'Date',
            reqd: 1
        },
				{
						label: 'Compliance Agreement',
						fieldname: 'compliance_agreement',
						fieldtype: 'Link',
						options: 'Compliance Agreement'
				},
    ],
    primary_action_label: 'Change Compliance Date',
    primary_action(values) {
      if(values.compliance_date){
        frappe.call({
          method:'one_compliance.one_compliance.doctype.compliance_settings.compliance_settings.compliance_date_update',
          args:{
            'compliance_date': values.compliance_date,
						'compliance_agreement': values.compliance_agreement,
          },
          callback:function(r){
            if (r.message) {
              frm.reload_doc()
            }
          }
        });
      }
        d.hide();
    }
  });
  d.show();
}
