frappe.ui.form.on('Opportunity',{
    refresh: function(frm) {
        if(!frm.is_new()){
          setTimeout(() => {
              frm.remove_custom_button('Quotation','Create')
              frm.remove_custom_button('Supplier Quotation','Create')
              frm.remove_custom_button('Request For Quotation','Create')
              })
        }
        
        frm.add_custom_button(__('Engagement Letter'), function () {
            frm.trigger("make_engagement_letter");
        },__("Create"));
    
    },
    make_engagement_letter: function (frm) {
        frappe.model.open_mapped_doc({
            method: 'one_compliance.one_compliance.doc_events.oppotunity.make_engagement_letter',
            frm: cur_frm
        });
    },
});