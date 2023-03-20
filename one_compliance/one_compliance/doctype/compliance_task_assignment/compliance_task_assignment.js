// Copyright (c) 2023, efeone and contributors
// For license information, please see license.txt

frappe.ui.form.on('Compliance Task Assignment', {
	refresh: function(frm){
		if(!frm.is_new()){
			// Set user field mandatory in childtable in saved doctype
			var df = frappe.meta.get_docfield('Compliance Task Detail', 'user', cur_frm.doc.name);
			df.reqd = 1;
	 }
	},
	validate: function(frm) {
		frappe.call({
			// frappe call to function assign_tasks_to_selected_users to assign the tasks
			method: 'one_compliance.one_compliance.doctype.compliance_task_assignment.compliance_task_assignment.assign_tasks_to_selected_users',
			args: {
				task_details: frm.doc.task_details
			}
		})
	}
});
