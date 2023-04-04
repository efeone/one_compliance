// Copyright (c) 2023, efeone and contributors
// For license information, please see license.txt

frappe.ui.form.on('Inward Register', {
	refresh: function(frm) {
    if(frm.is_new()){
			// set received by field as session user
      frm.set_value("received_by",frappe.session.user)
    }
		if(!frm.is_new() && frm.doc.docstatus == 1){
			//custom button to create outward register and route to outward register doctype
			frm.add_custom_button('Create Outward Register', () =>{
				frappe.model.open_mapped_doc({
	        method: 'one_compliance.one_compliance.doctype.inward_register.inward_register.create_outward_register',
	        frm: cur_frm
	      });
			})
		}
		let roles = frappe.user_roles;
		if(roles.includes("Compliance Manager") || roles.includes('Director')){
			// Set edit posting date and time checkbox visible for compliance manager
			frm.set_df_property('edit_posting_date_and_time','hidden',0);
		}
		else{
			frm.set_df_property('edit_posting_date_and_time','hidden',1);
		}
		if(frm.doc.digital_signature == 1 && frm.doc.customer){
			disable_add_or_view_digital_signature_button(frm)
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
	frappe.call({
		method: 'one_compliance.one_compliance.doctype.inward_register.inward_register.disable_add_or_view_digital_signature_button',
		args: {
			'customer' : frm.doc.customer
		},
		callback: (r) => {
			if(r.message) {
				frm.add_custom_button('Add/View Digital Signature', () =>{
					digital_signature_dialog(frm)
				})
			}
		}
	})
}
