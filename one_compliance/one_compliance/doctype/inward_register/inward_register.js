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
		if(frm.doc.register_type == 'Digital Signature' && frm.doc.customer){
			frm.add_custom_button('Add/View Digital Signature', () =>{
				digital_signature_dialog(frm)
			})
			disable_add_or_view_digital_signature_button(frm)
		}
	},

	document_register_type: function(frm) {
		update_document_register_type(frm);
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
		method: 'one_compliance.one_compliance.doctype.inward_register.inward_register.disable_add_or_view_digital_signature_button',
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

let update_document_register_type = function(frm) {
	// Add or Remove data from  register type table based on multi-select
	let document_register_type = frm.doc.document_register_type;
	let document_register_type_length = frm.doc.document_register_type.length;
	let document_register_type_detail_length = 0
	if (frm.doc.register_type_detail) {
		document_register_type_detail_length = frm.doc.register_type_detail.length
	}
	if (document_register_type_length > document_register_type_detail_length) {
		frm.clear_table('register_type_detail')
		frm.doc.document_register_type.forEach(document_register_type => {
				let document_register_type_table = frm.add_child('register_type_detail');
				document_register_type_table.document_register_type = document_register_type.document_register_type
				frm.refresh_field('register_type_detail')
		})
	}
  else if (document_register_type_length < document_register_type_detail_length) {
		if (document_register_type_length) {
			document_register_type_length = frm.doc.document_register_type.length
			let document_register_types = []
			frm.doc.document_register_type.forEach(document_register_type => {
				document_register_types.push(document_register_type.document_register_type)
			});
			delete_row_from_document_register_type_table(document_register_types)
			document_register_type = frm.doc.document_register_type
			document_register_type_length = frm.doc.document_register_type.length
		}
		else {
			frm.clear_table('register_type_detail')
			frm.refresh_field('register_type_detail')
		}
	}
}


let delete_row_from_document_register_type_table = function (document_register_types) {
		let table = cur_frm.doc.register_type_detail || [];
		let i = table.length;
		while (i--) {
			if(!document_register_types.includes(table[i].document_register_type)) {
				cur_frm.get_field('register_type_detail').grid.grid_rows[i].remove();
			}
		}
		cur_frm.refresh_field('register_type_detail')
}
