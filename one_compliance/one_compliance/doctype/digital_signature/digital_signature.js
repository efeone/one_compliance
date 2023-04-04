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
    }
});
