frappe.ui.form.on('Customer',{
  compliance_customer_type(frm){
    if(frm.doc.compliance_customer_type){
      if(frm.doc.compliance_customer_type == 'Individual'){
        frm.set_value('customer_type','Individual')
      }
      else{
        frm.set_value('customer_type', 'Company')
      }
      refresh_field('customer_type');
    }
  },
  refresh: function(frm){
    if(!frm.is_new()){
      frm.add_custom_button('Create Agreement', () => { /* Add a custom button to get compliance agreement details */
        frappe.model.open_mapped_doc({
          method: 'one_compliance.one_compliance.doc_events.customer.create_agreement_custom_button',
          frm: cur_frm
        });
      });
      frm.set_query('contact','customer_contacts', (doc, cdt, cdn) => { /* applied filter in contact to get corresponding customer */
      return {
          query: 'one_compliance.one_compliance.doc_events.customer.filter_contact',
          filters: {
            customer_name: doc.name
          }
        }
      })
    }
  }
});
