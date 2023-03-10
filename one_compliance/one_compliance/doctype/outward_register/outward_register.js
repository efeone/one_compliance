// Copyright (c) 2023, efeone and contributors
// For license information, please see license.txt

frappe.ui.form.on('Outward Register', {
	refresh: function(frm) {
    if(frm.is_new()){
      frm.set_value("returned_by",frappe.session.user)
    }
	}
});
