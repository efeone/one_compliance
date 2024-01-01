frappe.ui.form.on('Customer',{
  compliance_customer_type: function(frm){
    if(frm.doc.compliance_customer_type){
      if(frm.doc.compliance_customer_type == 'Individual'){
        frm.set_value('customer_type','Individual')
      }
      else{
        frm.set_value('customer_type', 'Company')
      }
      refresh_field('customer_type');
    }
  },
  refresh: function(frm){
    setTimeout(() => {
      frm.remove_custom_button('Pricing Rule','Create');
      frm.remove_custom_button('Get Customer Group Details','Actions');
    })
    if(!frm.is_new()){
      let roles = frappe.user_roles;
      if(roles.includes('Compliance Manager') || roles.includes('Director')){
      frm.add_custom_button('Add/View Credential', () => {
        customer_credentials(frm)
      });
      frm.add_custom_button('View Document',() =>{
        customer_documents(frm)
      });
    }
    if(roles.includes('Employee') || roles.includes('Director')){
      frm.add_custom_button('Sent Clarification', () =>{
        send_clarification_message(frm)
      });
    }
    view_compliance_agreemet(frm)
    view_project(frm)
    view_payment_entry(frm)
    }
    // Create sales invoice against compliance_agreement

    frappe.call({
      method: 'one_compliance.one_compliance.doc_events.customer.check_invoice_based_on_and_project_status',
      args:{
        'customer':frm.doc.name
      },
      callback: (r) =>{
        if (r.message){
          frm.add_custom_button('Create Sales Invoice', () => {
            frappe.model.open_mapped_doc({
              method: "one_compliance.one_compliance.doc_events.customer.make_sales_invoice",
              frm: cur_frm
          })
          })
        }
      }
    })
  }
});
/* applied dialog instance to add or view customer Credential */

let customer_credentials = function (frm) {
  let d = new frappe.ui.Dialog({
    title: 'Enter details',
    fields: [
      {
        label: 'Purpose',
        fieldname: 'purpose',
        fieldtype: 'Link',
        options: 'Credential Type'
      }
    ],
    primary_action_label: 'View Credential',
    primary_action(values) {
      frappe.call({
        method:'one_compliance.one_compliance.utils.view_credential_details',
        args:{
              'customer':frm.doc.name,
              'purpose':values.purpose
             },
        callback:function(r){
          if (r.message){
            d.hide();
            let newd = new frappe.ui.Dialog({
              title: 'Credential details',
              fields: [
                {
                  label: 'Username',
                  fieldname: 'username',
                  fieldtype: 'Data',
                  read_only: 1,
                  default:r.message[0]
                },
                {
                  label: 'Password',
                  fieldame: 'password',
                  fieldtype: 'Data',
                  read_only: 1,
                  default:r.message[1]
                },
                {
                  label: 'Url',
                  fieldname: 'url',
                  fieldtype: 'Data',
                  options: 'URL',
                  read_only: 1,
                  default:r.message[2]
                }
              ],
              primary_action_label: 'Close',
              primary_action(value) {
                  newd.hide();
              },
              secondary_action_label : 'Edit Credential',
              secondary_action(value){
                frappe.call({
                  method:'one_compliance.one_compliance.utils.edit_customer_credentials',
                  args:{
                    'customer':frm.doc.name,
                  },
                  callback:function(r){
                    if (r.message) {
                      d.hide();
                      frappe.set_route('Form','Customer Credentials', r.message, '_blank');
                    }
                  }
                })
              }
          });
          newd.show();
          }
        }
      })
    }
});
d.show();
}

/* applied dialog instance to show customer document */

let customer_documents = function (frm) {
  let d = new frappe.ui.Dialog({
    title: 'Enter details',
    fields: [
      {
        label: 'Compliance Sub Category',
        fieldname: 'compliance_sub_category',
        fieldtype: 'Link',
        options: 'Compliance Sub Category'
      }
    ],
    primary_action_label: 'View Document',
    primary_action(values) {
      frappe.call({
        method:'one_compliance.one_compliance.utils.view_customer_documents',
        args:{
              'customer':frm.doc.name,
              'compliance_sub_category':values.compliance_sub_category
             },
        callback:function(r){
          if (r.message){
            d.hide();
            let newd = new frappe.ui.Dialog({
              title: 'Document details',
              fields: [
                {
                  label: 'Document Attachment',
                  fieldname: 'document_attachment',
                  fieldtype: 'Data',
                  read_only: 1,
                  default:r.message[0]
                },
              ],
              primary_action_label: 'Close',
              primary_action(value) {
                  newd.hide();
              },
              secondary_action_label : 'Download',
              secondary_action(value){
                window.open(r.message[0])
                }
          });
          newd.show();
          }
        }
      })
    }
});
d.show();
}

let view_compliance_agreemet = function(frm) {
  frappe.call({
    method : 'one_compliance.one_compliance.doc_events.customer.custom_button_for_view_compliance_agreement',
    args :{
      'customer' : frm.doc.name
     },
   callback : function(r){
     if(r.message){
       frm.add_custom_button('View Agreement', ()=>{
         frappe.set_route('Form','Compliance Agreement', r.message)
      }, __('Create'))
     }
     else{
       frm.add_custom_button('Agreement', () => { /* Add a custom button to get compliance agreement details */
         frappe.model.open_mapped_doc({
           method: 'one_compliance.one_compliance.doc_events.customer.create_agreement_custom_button',
           frm: cur_frm
         });
       }, __('Create'));
      }
     }
 })
}
let view_project = function(frm) {
  frappe.call({
    method : 'one_compliance.one_compliance.doc_events.customer.custom_button_for_view_project',
    args :{
      'customer' : frm.doc.name
     },
     callback : function(r){
       if(r.message){
         frm.add_custom_button('Consultant Project', ()=>{
           frappe.model.open_mapped_doc({
             method: 'one_compliance.one_compliance.doc_events.customer.create_project_custom_button',
             frm: cur_frm
           });
         }, __('Create'));
       }
}
})
}
let view_payment_entry = function(frm) {
  frm.add_custom_button('Payment', () => {
    let d = new frappe.ui.Dialog({
      title: 'Enter Details',
      fields: [
        {
          label: 'Mode of Payment',
          fieldname: 'mode_of_payment',
          fieldtype: 'Link',
          reqd: 1,
          options: 'Mode of Payment',
        },
        {
          label: 'Paid Amount',
          fieldname: 'paid_amount',
          fieldtype: 'Currency',
          reqd: 1,
        },
      ],
      primary_action_label: 'Create Payment',
      primary_action(values) {
        // Use the values directly in the frappe.model.open_mapped_doc
        frappe.call('one_compliance.one_compliance.doc_events.customer.create_payment_entry', {
            mode_of_payment: values.mode_of_payment,
            paid_amount: values.paid_amount,
            customer: frm.doc.name
        }).then(r => {
            console.log(`Payment Entry ${r.message} has been created`)
        })
        d.hide();
      },
    });
    d.show();
  }, __('Create'));
};

let send_clarification_message = function (frm){
  let d = new frappe.ui.Dialog({
    title: 'Message',
    fields: [
      {
        'fieldname': 'message',
        'fieldtype': 'Text',
        'label': 'Clarification Message',
        'reqd': 1
      }
    ],
    primary_action_label: 'Send',
    primary_action(values) {
      frappe.call({
        method: 'one_compliance.one_compliance.doc_events.customer.send_clarification_message',
        args: {
          'customer': frm.doc.name,
          'message': values.message
        },
        callback: function(r) {
          if (r.message) {
            frappe.show_alert(r.message);
          }
        }
      });
      d.hide();
    }
  });
  d.show()
}
