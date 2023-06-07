frappe.ui.form.on('Lead',{
      refresh: function(frm) {
          if(!frm.is_new()){
            setTimeout(() => {
                frm.remove_custom_button('Customer','Create')
                frm.remove_custom_button('Quotation','Create')
                })
          }
      }
  });