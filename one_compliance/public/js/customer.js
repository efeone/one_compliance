frappe.ui.form.on('Customer',{
  compliance_customer_type(frm){
    frm.set_df_property('compliance_customer_type', 'read_only',frm.is_new() ? 0 : 1);
    if(frm.doc.compliance_customer_type){
      if(frm.doc.compliance_customer_type == 'Individual'){
        frm.set_value('customer_type','Individual')
      }
      else{
        frm.set_value('customer_type', 'Company')
      }
      refresh_field('customer_type');
    }
    }
})
