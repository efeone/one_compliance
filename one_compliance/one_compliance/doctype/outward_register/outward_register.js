// Copyright (c) 2023, efeone and contributors
// For license information, please see license.txt

frappe.ui.form.on('Outward Register', {
	refresh: function(frm) {
    if(frm.is_new()) {
			//Set the return_by default as session user
      frm.set_value("returned_by",frappe.session.user)
    }

		let roles = frappe.user_roles;
		if(roles.includes('Compliance Manager') || roles.includes('Director')) {
			// Set edit Return date and time checkbox visible for compliance manager
			frm.set_df_property('edit_return_date_and_time','hidden',0);
		}
		else {
			frm.set_df_property('edit_return_date_and_time','hidden',1);
		}
	},
	onload: function(frm) {
		if(frm.is_new()){
			frm.set_value('purpose')
		}
	}
});
