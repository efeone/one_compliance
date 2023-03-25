// Copyright (c) 2023, efeone and contributors
// For license information, please see license.txt

frappe.ui.form.on('Compliance Sub Category', {
	refresh: function(frm) {
    if(!frm.is_new() && !frm.doc.project_template){
			//custom button to create project template and route to  project template doctype
     frm.add_custom_button('Create Project Template', () =>{
       frappe.model.open_mapped_doc({
         method: 'one_compliance.one_compliance.doctype.compliance_sub_category.compliance_sub_category.create_project_template_custom_button',
         frm: cur_frm
       });
     });
    }
		set_notification_templates(frm);
	}
});

let set_notification_templates = function(frm){
	frappe.call({
		method:'one_compliance.one_compliance.doctype.compliance_sub_category.compliance_sub_category.get_notification_details',
		callback: (r) => {
			if(r.message){

				// set value to customer and company
				if(!frm.doc.task_before_due_date__notification){
					frm.set_value('task_before_due_date__notification', r.message.task_before_due_date__notification)
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
			}
		}
	})
}
