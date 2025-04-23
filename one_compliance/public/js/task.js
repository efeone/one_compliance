frappe.ui.form.on('Task',{
  refresh(frm){
    let roles = frappe.user_roles;    
    // Make the field 'readiness_status' read-only if the user has the 'Executive' role
    if (roles.includes('Executive')) {
      frm.set_df_property('readiness_status', 'read_only', 1);
    } else {
      frm.set_df_property('readiness_status', 'read_only', 0);
    }
    if(roles.includes('Compliance Manager') || roles.includes('Director')){
      if(!frm.is_new() && frm.doc.is_template == 0){
        frm.add_custom_button('View Credential', () => {
          customer_credentials(frm)
        });
        frm.add_custom_button('View Document', () => {
          customer_document(frm)
        });
      }
    }
    if(!frm.is_new()){
      frm.add_custom_button('Status Update', () => {
        update_status(frm)
      });
    }
    if(frm.doc.custom_task_document_items){
      frm.set_df_property('custom_task_document_items', 'read_only', 0);
    }
    if(frm.doc.project){
      frm.set_df_property('is_group','hidden',1);
      frm.set_df_property('is_template','hidden',1);
    }
    update_readiness_status_field(frm);
  }
});
/* applied dialog instance to show customer Credential */

// Function to update readiness_status visibility based on project_template's enable_task_readiness_flow
function update_readiness_status_field(frm) {
  if (frm.doc.compliance_sub_category) {
    frappe.db.get_value('Compliance Sub Category', frm.doc.compliance_sub_category, 'project_template', (r) => {
      if (r && r.project_template) {
        // Fetch the enable_task_readiness_flow field from the linked project_template
        frappe.db.get_value('Project Template', r.project_template, 'enable_task_readiness_flow', (result) => {
          if (result && result.enable_task_readiness_flow) {
            // If enable_task_readiness_flow is checked, show the readiness_status field
            frm.fields_dict.readiness_status.$wrapper.show();
          } else {
            // If enable_task_readiness_flow is not checked, hide the readiness_status field
            frm.fields_dict.readiness_status.$wrapper.hide();
          }
        });
      }
    });
  }
}

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
           options: 'Credential Type',
           get_query: function () {
             return {
               filters: {
                 'compliance_sub_category':frm.doc.compliance_sub_category
               }
             };
           }
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

let update_status = function(frm){
  let d = new frappe.ui.Dialog({
    title: 'Enter details',
    fields: [
      {
        label: 'Status',
        fieldname: 'status',
        fieldtype: 'Select',
        options: 'Open\nWorking\nPending Review\nCompleted\nHold',
        default: 'Completed'
      },
      {
        label: 'Completed By',
        fieldname: 'completed_by',
        fieldtype: 'Link',
        options: 'User'
      },
      {
        label: 'Completed On',
        fieldname: 'completed_on',
        fieldtype: 'Date',
        default: 'Today'
      },
    ],
    primary_action_label: 'Update',
    primary_action(values) {
      frappe.call({
        method: 'one_compliance.one_compliance.doc_events.task.update_task_status',
        args: {
          'task_id': frm.doc.name,
          'status': values.status,
          'completed_by': values.completed_by,
          'completed_on': values.completed_on
        },
        callback: function(r){
          if (r.message){
            d.hide();
            frm.reload_doc();
          }
        }
      });
    },
  });
  d.set_value('completed_by', frappe.session.user);
d.show();
};
