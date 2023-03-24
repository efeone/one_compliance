frappe.ui.form.on('Task',{
  refresh(frm){
    let roles = frappe.user_roles;
    if(roles.includes('Compliance Manager') || roles.includes('Director')){
      frm.add_custom_button('View Credential', () => {
        customer_credentials(frm)
      });
      frm.add_custom_button('View Document', () => {
        customer_document(frm)
      });
    }
  }
});
/* applied dialog instance to show customer Credential */

let customer_credentials = function (frm) {
  frappe.db.get_value('Project', frm.doc.project, 'customer')
   .then(r =>{
     let customer = r.message.customer;
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
             'customer': customer,
             'purpose': values.purpose
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
                    secondary_action_label : 'Go To URL',
                    secondary_action(value){
                      window.open(r.message[2])
                    }
                  });
                  newd.show();
                }
              }
            })
          }
        });
        d.show();
      })
    }

let customer_document = function (frm) {
  frappe.db.get_value('Project', frm.doc.project, 'customer')
  .then(r =>{
    let customer = r.message.customer;
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
              'customer': customer,
              'compliance_sub_category': values.compliance_sub_category
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
         })
       }
