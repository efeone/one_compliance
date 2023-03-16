// Copyright (c) 2023, efeone and contributors
// For license information, please see license.txt

frappe.ui.form.on('Compliance Category', {
	refresh: function(frm) {
    if(!frm.is_new() && frm.doc.compliance_category){
      //custom button to view compliance sub category from compliance category//
      frm.add_custom_button('Add Sub Category', ()=>{
        frappe.model.open_mapped_doc({
          method : 'one_compliance.one_compliance.doctype.compliance_category.compliance_category.custom_button_for_sub_category',
          frm : cur_frm
        });
      });
    }
 },
});
