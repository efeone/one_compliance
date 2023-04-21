frappe.ui.form.on('Compliance Agreement',{
  refresh :function(frm){
    frm.set_df_property('compliance_category', 'reqd', 1)
    frm.set_query('compliance_sub_category','compliance_category_details',(frm,cdt,cdn) => {
      // setting filer for sub category //
      let child = locals[cdt][cdn];
          return {
              filters: {
                'compliance_category': child.compliance_category,
                enabled: 1
              }
          };
      });

    // Create sales invoice against project and compliance_agreement
    if(frm.doc.invoice_based_on){
      frappe.call({
        method: 'one_compliance.one_compliance.doctype.compliance_agreement.compliance_agreement.check_project_status',
        args:{
          'compliance_agreement':frm.doc.name
        },
        callback: (r) =>{
          if (r.message){
            frm.add_custom_button('Create Sales Invoice', () => {
              frappe.model.open_mapped_doc({
                method: "one_compliance.one_compliance.doctype.compliance_agreement.compliance_agreement.make_sales_invoice",
                frm: cur_frm
            })
            })
          }
        }
      })
    }

   if(!frm.is_new()){
     frm.add_custom_button('Set Agreement Status', () => {
       set_agreement_status(frm)
     })
   }
  },
  compliance_category:function(frm){
    set_sub_category_list(frm);
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

let update_compliance_category = function (frm) {
  // Add or Remove data from compliance category table multi-select//
	let compliance_category = frm.doc.compliance_category;
	let compliance_category_length = frm.doc.compliance_category.length;
  let compliance_category_details_length = 0
  if(frm.doc.compliance_category_details){
    compliance_category_details_length = frm.doc.compliance_category_details.length;
  }
	if (compliance_category_length > compliance_category_details_length) {
    frm.clear_table('compliance_category_details')
    frm.doc.compliance_category.forEach(compliance_category => {
            let compliance_category_table = frm.add_child('compliance_category_details');
            compliance_category_table.compliance_category = compliance_category.compliance_category
            frm.refresh_field('compliance_category_details')
    });
	}
	else if (compliance_category_length < compliance_category_details_length) {
		if (compliance_category_length) {
			compliance_category_length = frm.doc.compliance_category.length
			let compliance_categorys = []
			frm.doc.compliance_category.forEach(compliance_category => {
				compliance_categorys.push(compliance_category.compliance_category)
			});
			delete_row_from_compliance_category_table(compliance_categorys)
      compliance_category = frm.doc.compliance_category
			compliance_category_length = frm.doc.compliance_category.length
		}
		else {
			frm.clear_table('compliance_category_details')
			frm.refresh_field('compliance_category_details')
		}
	}
}


let delete_row_from_compliance_category_table = function (compliance_categorys) {
			let table = cur_frm.doc.compliance_category_details || [];
			let i = table.length;
			while (i--) {
				if(!compliance_categorys.includes(table[i].compliance_category)) {
					cur_frm.get_field('compliance_category_details').grid.grid_rows[i].remove();
				}
			}
			cur_frm.refresh_field('compliance_category_details');
}

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

let set_sub_category_list = function(frm){
  frm.call('list_sub_category', {throw_if_missing : true})
    .then(r =>{
      if(r.message){
        frm.refresh_field('compliance_category_details');
      }
    })
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
            options: 'Open\nHold',
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
