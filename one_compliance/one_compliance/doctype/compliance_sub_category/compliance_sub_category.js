// Copyright (c) 2023, efeone and contributors
// For license information, please see license.txt

frappe.ui.form.on('Compliance Sub Category', {
	refresh: function(frm) {
    if(!frm.is_new() && !frm.doc.project_template){
			//custom button to create project template and route to  project template doctype
     frm.add_custom_button('Create Project Template', () =>{
       frappe.model.open_mapped_doc({
         method: 'one_compliance.one_compliance.doctype.compliance_sub_category.compliance_sub_category.create_project_template_custom_button',
         frm: cur_frm
       });
     });
    }
	},

});
