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
		if(frm.doc.digital_signature == 1){
			frm.add_custom_button('Add/View Digital Signature', () =>{
				digital_signature_dialog(frm)
			})
			disable_add_or_view_digital_signature_button(frm)
		}
	},
	onload: function(frm) {
		if(frm.is_new()){
			frm.set_value('purpose',)
		}
	}
});

/* applied dialog instance to add or view digital signature */
let digital_signature_dialog = function (frm) {
	let d = new frappe.ui.Dialog({
		title: 'Add/View Digital Signature',
		fields: [
				{
						label: 'Digital Signature',
						fieldname: 'digital_signature',
						fieldtype: 'Link',
						options: 'Digital Signature',
						reqd: 1,
						get_query : function() {
							return {
								filters: {
									customer: frm.doc.customer
								}
							}
						}
				}
		],
		primary_action_label: 'Update',
    primary_action(values) {
			d.hide()
			if (values.digital_signature){
				frappe.call({
					method:'one_compliance.one_compliance.utils.update_digital_signature',
					args:{
						'digital_signature': values.digital_signature,
						'register_type': frm.doc.doctype,
						'register_name': frm.doc.name
					},
					callback:function(r){
						if (r.message) {
							frappe.show_alert({
								message:__('Digital Signature Updated'),
								indicator:'green'
							}, 5);
						}
					}
				})
			}
    }
});

d.show();
}


let disable_add_or_view_digital_signature_button = function(frm) {
	// Function to disable custom button Add/View Digital Signature after once it updated
	frappe.call({
		method: 'one_compliance.one_compliance.doctype.outward_register.outward_register.disable_add_or_view_digital_signature_button',
		args: {
			'customer' : frm.doc.customer
		},
		callback: (r) => {
			if(r.message) {
				frm.remove_custom_button('Add/View Digital Signature')
			}
		}
	})
}
