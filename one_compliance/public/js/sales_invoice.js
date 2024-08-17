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
        if (!frm.is_new() && frm.doc.docstatus === 1 && frm.doc.status !== 'Paid') {
        frm.add_custom_button('TDS Booking', () => {
            let d = new frappe.ui.Dialog({
                title: __("TDS Booking"),
                fields: [
                    {
                        label: 'TDS Account',
                        fieldname: 'tds_account',
                        fieldtype: 'Link',
                        options: 'Account'
                    },
                    {
                        label: 'Percentage of TDS',
                        fieldname: 'percentage_of_tds',
                        fieldtype: 'Percent'
                    },
                    {
                        label: 'Total Amount',
                        fieldname: 'total_amount',
                        fieldtype: 'Currency',
                        default: frm.doc.rounded_total,
                    },
                    {
                        label: 'TDS Amount',
                        fieldname: 'tds_amount',
                        fieldtype: 'Currency',
                        read_only: true
                    }
                ],
                primary_action_label: 'Submit',
                primary_action(values) {
                    d.hide();
                    // Call the backend function to create the Journal Entry
                    frappe.call({
                        method: 'one_compliance.one_compliance.doc_events.sales_invoice.create_tds_journal_entry',
                        args: {
                            'tds_account': values.tds_account,
                            'tds_amount': values.tds_amount,
                            'customer': frm.doc.customer,
                            'sales_invoice': frm.doc.name,
                            'project': frm.doc.project
                        },
                        callback: function(r) {
                          if (r.message) {
                           let journal_entry_link = `<a href="/app/journal-entry/${r.message}" style="color:black;">Journal Entry</a>`;
                           frappe.show_alert({
                               message:__('Journal Entry Created Successfully: ') + journal_entry_link,
                               indicator:'green'
                            });
                          }
                        }
                    });
                }
            });
            /*
            * Function to calculate the tds
            */
            function calculateTDSAmount() {
                let percentage_of_tds = d.get_value('percentage_of_tds');
                let total_amount = d.get_value('total_amount');

                if (percentage_of_tds && total_amount) {
                    let tds_amount = (total_amount * (percentage_of_tds / 100));
                    d.set_value('tds_amount', tds_amount);
                } else {
                    d.set_value('tds_amount', 0);
                }
            }
            // Add event listeners to recalculate TDS Amount when Percentage of TDS or Total Amount changes
            d.fields_dict.percentage_of_tds.$input.on('change', calculateTDSAmount);
            d.fields_dict.total_amount.$input.on('change', calculateTDSAmount);

            d.show();
        });
      }
    }
});
