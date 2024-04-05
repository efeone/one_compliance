// Copyright (c) 2023, efeone and contributors
// For license information, please see license.txt

frappe.ui.form.on('Digital Signature', {
  onload: function (frm) {
    // set the value the customer in digital signature doctype
        var prev_route = frappe.get_prev_route();
        if(prev_route[1] == 'Inward Register'){
            frappe.db.get_value('Inward Register', prev_route[2], 'customer').then(r => {
                frm.set_value('customer', r.message.customer);
            });
        }
    if(prev_route[1] == 'Outward Register'){
            frappe.db.get_value('Outward Register', prev_route[2], 'customer').then(r => {
                frm.set_value('customer', r.message.customer);
            });

        }
    },
    refresh: function (frm) {
        if(frm.is_new()){
  			set_notification_templates(frm);
  		}
      frm.add_custom_button('Create Project', () => {
        create_project_from_digital_signature(frm)
      })
    },
    customer: function (frm) {
        if(frm.doc.customer){
            frappe.call({
                method: 'one_compliance.one_compliance.doctype.digital_signature.digital_signature.validation_on_company_name',
                    args:{
                        'customer':frm.doc.customer
                          },
                          callback: (r) =>{
                            if (r.message){
                             frm.set_value('company_name',frm.doc.customer)
                            }
                            else{
                                frm.set_value('company_name','')
                            }
                          }
                    })
  		}
       
    },

    notify_on_expiration: function (frm) {
        if (frm.doc.notify_on_expiration == 1 ) {
            frappe.msgprint('Make sure the Director Email is provided.')   
        }
    }

});

let set_notification_templates = function(frm){
	frappe.call({
		method:'one_compliance.one_compliance.doctype.digital_signature.digital_signature.get_notification_details',
		callback: (r) => {
			if(r.message){
				if(!frm.doc.digital_signature_expiry_notification){
					frm.set_value('digital_signature_expiry_notification', r.message.digital_signature_expiry_notification)
				}
			}
		}
	})
}

let create_project_from_digital_signature = function(frm){
  frappe.call({
    method:'one_compliance.one_compliance.doctype.digital_signature.digital_signature.create_project_from_digital_signature',
    args:{
      digital_signature: frm.doc.name,
      exp_end_date: frm.doc.expiry_date
    },
		callback: (r) => {
			if(r.message){

			}
		}
  })
}
