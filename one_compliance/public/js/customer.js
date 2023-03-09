frappe.ui.form.on('Customer',{
  compliance_customer_type (frm){
    if(frm.doc.compliance_customer_type == 'Individual'){
      frm.set_value('customer_type','Individual')
    }
    else{
      frm.set_value('customer_type', 'Company')
    }
  }
})
