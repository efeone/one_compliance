frappe.ui.form.on('Compliance Agreement',{
  refresh :function(frm){
    frm.set_df_property('compliance_category', 'reqd', 1)
    frm.set_query('compliance_sub_category','compliance_category_details',(frm,cdt,cdn) => {
      // setting filer for sub category //
      let child = locals[cdt][cdn];
      return {
        filters: {
          'compliance_category': child.compliance_category,
          'enabled': 1
        }
      };
    });

    if(!frm.is_new()){
      frm.add_custom_button('Set Agreement Status', () => {
        set_agreement_status(frm)
      })
    }
  },
  compliance_category:function(frm){
    update_compliance_category(frm);
  },
  setup :function(frm){
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

frappe.ui.form.on('Compliance Category Details',{
  // Calculate the total rate from Compliance Category Details child table //
  rate : function(frm, cdt, cdn){
    let d = locals[cdt][cdn];
    var total = 0
    frm.doc.compliance_category_details.forEach(function(d){
      total += d.rate;
    })
    frm.set_value('total', total)
  },
  compliance_category_details_remove : function(frm){
    var total = 0
    frm.doc.compliance_category_details.forEach(function(d){
      total += d.rate;
    })
    frm.set_value('total',total)
  }
});

let update_compliance_category = function(frm){
  if(frm.doc.compliance_category.length){
    frm.clear_table('compliance_category_details')
    let rate = 0;
    frm.doc.compliance_category.forEach(compliance_category => {
      frappe.call('one_compliance.one_compliance.doctype.compliance_agreement.compliance_agreement.get_compliance_sub_category_list', {
        compliance_category: compliance_category.compliance_category
      }).then(r => {
        if(r.message){
          r.message.forEach(row =>{
            let compliance_category_table = frm.add_child('compliance_category_details');
            compliance_category_table.compliance_category = row.compliance_category;
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
  else{
    frm.set_value('total', 0);
    frm.refresh_field('total');
    frm.clear_table('compliance_category_details');
    frm.refresh_field('compliance_category_details');
  }
}

let set_agreement_status = function(frm){
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
      if(values.status){
        frappe.call({
          method:'one_compliance.one_compliance.doctype.compliance_agreement.compliance_agreement.set_agreement_status',
          args:{
            'status': values.status,
            'agreement_id': frm.doc.name
          },
          callback:function(r){
            if (r.message) {
              frm.reload_doc()
              frappe.show_alert({
                message:__('Status Has Been Updated'),
                indicator:'green'
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
