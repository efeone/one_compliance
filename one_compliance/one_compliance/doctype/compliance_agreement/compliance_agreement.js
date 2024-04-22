frappe.ui.form.on('Compliance Agreement', {

  validate: function (frm) {

    if (frm.doc.has_long_term_validity) {
      frm.doc.valid_upto = null;
    }
  },

  refresh: function (frm) {
    frm.set_df_property('compliance_category', 'reqd', 1)
    frm.set_query('compliance_sub_category', 'compliance_category_details', (frm, cdt, cdn) => {
      // setting filer for sub category //
      let child = locals[cdt][cdn];
      return {
        filters: {
          'compliance_category': child.compliance_category,
          'enabled': 1
        }
      };
    });

    if (!frm.is_new()) {
      frm.add_custom_button('Set Agreement Status', () => {
        set_agreement_status(frm)
      })
      frappe.db.get_single_value('Compliance Settings', 'role_of_project_creator')
        .then(role_of_project_creator => {
          if (frappe.user_roles.includes(role_of_project_creator)) {
            frm.add_custom_button('Create Project', () => {
              create_project(frm)
            });
          }
        })
    }
  },
  invoice_generation: function(frm){
    get_invoice_dates(frm);
  },

  valid_from: function(frm){
    get_invoice_dates(frm);
  },
  compliance_category:function(frm){
    update_compliance_category(frm);
  },
  setup: function (frm) {
    frm.set_query('terms_and_condition', () => {
      return {
        filters: {
          compliance: 1,
          disabled: 0
        }
      }
    });
    frm.set_query('customer', () => {
      return {
        filters: {
          disabled: 0
        }
      }
    });
  }
});

frappe.ui.form.on('Compliance Category Details', {
  // Calculate the total rate from Compliance Category Details child table //
  rate: function (frm, cdt, cdn) {
    let d = locals[cdt][cdn];
    var total = 0
    frm.doc.compliance_category_details.forEach(function (d) {
      total += d.rate;
    })
    frm.set_value('total', total)
  },
  compliance_category_details_remove: function (frm) {
    var total = 0
    frm.doc.compliance_category_details.forEach(function (d) {
      total += d.rate;
    })
    frm.set_value('total', total)
  }
});

let update_compliance_category = function (frm) {
  if (frm.doc.compliance_category.length) {
    frm.clear_table('compliance_category_details')
    let rate = 0;
    frm.doc.compliance_category.forEach(compliance_category => {
      frappe.call('one_compliance.one_compliance.doctype.compliance_agreement.compliance_agreement.get_compliance_sub_category_list', {
        compliance_category: compliance_category.compliance_category
      }).then(r => {
        if (r.message) {
          r.message.forEach(row => {
            let compliance_category_table = frm.add_child('compliance_category_details');
            compliance_category_table.compliance_category = row.compliance_category;
            compliance_category_table.sub_category_name = row.sub_category;
            compliance_category_table.compliance_sub_category = row.name;
            compliance_category_table.rate = row.rate;
            rate = rate + row.rate;
          });
          frm.set_value('total', rate);
          frm.refresh_field('total');
          frm.refresh_field('compliance_category_details');
        }
      })
    });
    frm.refresh_field('compliance_category_details');
  }
  else {
    frm.set_value('total', 0);
    frm.refresh_field('total');
    frm.clear_table('compliance_category_details');
    frm.refresh_field('compliance_category_details');
  }
}

let set_agreement_status = function (frm) {
  //function to set the status of compliance agreement to open and hold
  let d = new frappe.ui.Dialog({
    title: 'Set Agreement Status',
    fields: [
      {
        label: 'Status',
        fieldname: 'status',
        fieldtype: 'Select',
        reqd: 1,
        options: 'Open\nHold\nCancelled',
      },
    ],
    primary_action_label: 'Set Agreement Status',
    primary_action(values) {
      if (values.status) {
        frappe.call({
          method: 'one_compliance.one_compliance.doctype.compliance_agreement.compliance_agreement.set_agreement_status',
          args: {
            'status': values.status,
            'agreement_id': frm.doc.name
          },
          callback: function (r) {
            if (r.message) {
              frm.reload_doc()
              frappe.show_alert({
                message: __('Status Has Been Updated'),
                indicator: 'green'
              }, 5);
            }
          }
        });
      }
      d.hide();
    }
  });
  d.show();
}

let create_project = function (frm) {
  let compliance_categories = frm.doc.compliance_category;
  compliance_categories = compliance_categories.map(item => item.compliance_category);
  let compliance_sub_categories = frm.doc.compliance_category_details;
  compliance_sub_categories = compliance_sub_categories.map(item => item.compliance_sub_category);
  let d = new frappe.ui.Dialog({
    title: 'Create Project',
    fields: [
      {
        label: 'Start Date',
        fieldname: 'start_date',
        fieldtype: 'Date',
        reqd: 1,
      },
      {
        label: 'Compliance Category',
        fieldname: 'compliance_category',
        fieldtype: 'Link',
        reqd: 1,
        options: 'Compliance Category',
      },
      {
        label: 'Compliance Sub Category',
        fieldname: 'compliance_sub_category',
        fieldtype: 'Link',
        reqd: 1,
        options: 'Compliance Sub Category'
      }
    ],
    primary_action_label: 'Submit',
    primary_action(values) {
      frm.doc.compliance_category_details.forEach((item) => {
        if (item.compliance_sub_category == values.compliance_sub_category) {
          frappe.call({
            method: 'one_compliance.one_compliance.doctype.compliance_agreement.compliance_agreement.create_project_against_sub_category',
            args: {
              'compliance_agreement': frm.doc.name,
              'compliance_sub_category': values.compliance_sub_category,
              'compliance_date': values.start_date,
              'compliance_category_details_id': item.name
            },
            callback: function (r) {
              if (r.message) {
                frm.reload_doc();
              }
            }
          });

        }
      });
      d.hide();
    }
  });

  d.fields_dict.compliance_sub_category.get_query = function () {
    return {
      filters: {
        'compliance_category': d.get_value('compliance_category'),
        'name': ['in', compliance_sub_categories]
      }
    };
  };
  d.fields_dict.compliance_category.get_query = function () {
    return {
      filters: {
        'name': ['in', compliance_categories]
      }
    };
  };
  d.show();
};

const get_invoice_dates = (frm) => {
    if (frm.doc.invoice_based_on == 'Consolidated' && frm.doc.invoice_generation && frm.doc.valid_from) {
        frm.set_value('invoice_date', frm.doc.valid_from);

        let next_invoice_date;

        if (frm.doc.invoice_generation == 'Monthly') {
            next_invoice_date = frappe.datetime.add_months(frm.doc.valid_from, 1);
        } else if (frm.doc.invoice_generation == 'Quarterly') {
            next_invoice_date = frappe.datetime.add_months(frm.doc.valid_from, 3);
        } else if (frm.doc.invoice_generation == 'Half Yearly') {
            next_invoice_date = frappe.datetime.add_months(frm.doc.valid_from, 6);
        } else if (frm.doc.invoice_generation == 'Yearly') {
            next_invoice_date = frappe.datetime.add_years(frm.doc.valid_from, 1);
        }

        frm.set_value('next_invoice_date', next_invoice_date);
    }
};
