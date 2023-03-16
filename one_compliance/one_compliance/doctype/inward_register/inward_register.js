// Copyright (c) 2023, efeone and contributors
// For license information, please see license.txt

frappe.ui.form.on('Inward Register', {
	refresh: function(frm) {
    if(frm.is_new()){
			// set received by field as session user
      frm.set_value("received_by",frappe.session.user)
    }
		if(!frm.is_new()){
			//custom button to create outward register and route to outward register doctype
			frm.add_custom_button('Create Outward Register', () =>{
				frappe.model.open_mapped_doc({
	        method: 'one_compliance.one_compliance.doctype.inward_register.inward_register.create_outward_register',
	        frm: cur_frm
	      });
			})
		}
		let roles = frappe.user_roles;
		if(roles.includes("Compliance Manager")){
			// Set edit posting date and time checkbox visible for compliance manager
			frm.set_df_property('edit_posting_date_and_time','hidden',0);
		}
		else{
			frm.set_df_property('edit_posting_date_and_time','hidden',1);
		}
	},
});
