// Copyright (c) 2023, efeone and contributors
// For license information, please see license.txt

frappe.ui.form.on('Compliance Settings', {
	refresh: function(frm) {
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
      }
    })
	}
});
