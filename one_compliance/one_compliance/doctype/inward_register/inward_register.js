// Copyright (c) 2023, efeone and contributors
// For license information, please see license.txt

frappe.ui.form.on('Inward Register', {
	refresh: function(frm) {
    if(frm.is_new()){
      frm.set_value("received_by",frappe.session.user)
    }
	}
});
