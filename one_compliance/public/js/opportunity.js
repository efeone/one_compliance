frappe.ui.form.on('Opportunity',{
    refresh: function(frm) {
        if(!frm.is_new()){
          setTimeout(() => {
              frm.remove_custom_button('Quotation','Create')
              frm.remove_custom_button('Supplier Quotation','Create')
              frm.remove_custom_button('Request For Quotation','Create')
              })
        }
    }
});