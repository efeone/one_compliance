frappe.ui.form.on('Project',{
    refresh(frm){
        frm.add_custom_button('Sales Invoice', () => {
            frappe.model.open_mapped_doc({
                method: "one_compliance.one_compliance.doc_events.project.make_sales_invoice",
                frm: cur_frm
            })
        }, 'Create');
        
    }
})
