// Copyright (c) 2024, efeone and contributors
// For license information, please see license.txt

frappe.ui.form.on("DIN KYC", {
	refresh(frm) {
		frm.add_custom_button('Create Project', () => {
      create_project(frm)
    });
	},
});
let create_project = function(frm){
  frappe.call({
    method:'one_compliance.one_compliance.doctype.din_kyc.din_kyc.create_project_from_din_kyc',
    args:{
      din_kyc: frm.doc.name,
      expiry_date: frm.doc.expiry_date
    },
		callback: (r) => {
			if(r.message){

			}
		}
  })
}
