frappe.ui.form.on('Sales Invoice', {
    refresh: function(frm) {
        if (frm.doc.workflow_state == 'Proforma Invoice') {
            frm.set_df_property('customer', 'read_only', 1);
                  frm.set_df_property('is_pos', 'read_only', 1);
                  frm.set_df_property('is_return', 'read_only', 1);
                    frm.set_df_property('is_debit_note', 'read_only', 1);
                      frm.set_df_property('scan_barcode', 'read_only', 1);
                        frm.set_df_property('update_stock', 'read_only', 1);
                          frm.set_df_property('project', 'read_only', 1);
                            frm.set_df_property('cost_center', 'read_only', 1);
                              frm.set_df_property('items', 'read_only', 1);
                              frm.set_df_property('tax_category', 'read_only', 1);
                              frm.set_df_property('taxes', 'read_only', 1);
                              frm.set_df_property('shipping_rule', 'read_only', 1);
                                frm.set_df_property('incoterm', 'read_only', 1);
                                  frm.set_df_property('use_company_roundoff_cost_center', 'read_only', 1);
                                    frm.set_df_property('disable_rounded_total', 'read_only', 1);
                                      frm.set_df_property('allocate_advances_automatically', 'read_only', 1);
                                        frm.set_df_property('get_advances', 'read_only', 1);
                                          frm.set_df_property('apply_discount_on', 'read_only', 1);
                                          frm.set_df_property('taxes_and_charges', 'read_only', 1);
        }
    }
});
