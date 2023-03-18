// Copyright (c) 2023, efeone and contributors
// For license information, please see license.txt

frappe.ui.form.on('Task Assignment', {
	refresh: function(frm) {
    if(frm.is_new()){
      frm.add_custom_button('Assign', () =>{
          
      })
    }
	}
});
