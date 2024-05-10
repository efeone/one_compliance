frappe.ui.form.on('Lead',{
    refresh: function(frm) {
        if(!frm.is_new()){
            setTimeout(() => {
                frm.remove_custom_button('Customer','Create')
                frm.remove_custom_button('Quotation','Create')
                frm.remove_custom_button('Opportunity','Create')
            })
            frm.add_custom_button(__('Sales Invoice'), function () {
                create_sales_invoice(frm);
            },__("Create"));
            frm.add_custom_button(__('Opportunity '), function () {
                create_opportunity(frm);
            },__("Create"));
        }
    }
});

function create_sales_invoice(frm) {
    let d = new frappe.ui.Dialog({
        title: 'Enter details',
        fields: [
            {
                label: __("Services"),
                fieldname: "services",
                fieldtype: 'MultiSelectPills',
                get_data: function (txt) {
                    return frappe.db.get_link_options("Item", txt);
                },
            },
        ],
        primary_action_label: 'Create',
        primary_action(values) {
            frappe.call({
                method: 'one_compliance.one_compliance.doc_events.lead.create_sales_invoice',
                args: {
                    doc_name: frm.doc.name,
                    services:values.services,
                },
                callback: function (r) {
                    if (r.message) {
                        d.hide();
                    }
                }
            });
        }
    });
    d.show();
}

function create_opportunity(frm){
    frappe.model.open_mapped_doc({
        method: "erpnext.crm.doctype.lead.lead.make_opportunity",
        frm: frm,
    });
}
