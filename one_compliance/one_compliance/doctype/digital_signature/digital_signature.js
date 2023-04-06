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
