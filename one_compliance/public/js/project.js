frappe.ui.form.on('Project',{
    refresh(frm){
      if(!frm.is_new()){
        setTimeout(() => {
            frm.remove_custom_button('Duplicate Project with Tasks','Actions')
            frm.remove_custom_button('Set Project Status','Actions')
            })
      }

        let roles = frappe.user_roles;
        if (roles.includes('Compliance Manager') || roles.includes('Director')) {
          if (!frm.is_new()) {
              frm.add_custom_button('Customer Credentials', () => {
                  customer_credentials(frm);
              }, 
              __("View")
            );
              frm.add_custom_button('Customer Documents', () => {
                customer_documents(frm);
            },
            __("View")
          );
          }
      }
      
    if(!frm.is_new()){
      frm.add_custom_button('Set Project Status', () => {
        update_project_status(frm)
      });
    }

    field_perms(frm)
  }
});

let set_status = function(frm, status, comment) {
  frappe.confirm(__('Set Project and all Tasks to status {0}?', [status.bold()]), () => {
    frappe.xcall('one_compliance.one_compliance.doc_events.project.set_project_status',
      {project: frm.doc.name, status: status, comment: comment}).then(() => {
      frm.reload_doc();
    });
  });
}

let update_project_status = function(frm){
  let d = new frappe.ui.Dialog({
      title: 'Set Project Status',
      fields: [
        {
          "fieldname": "status",
          "fieldtype": "Select",
          "label": "Status",
          "reqd": 1,
          "options": "\nOpen\nHold\nCompleted\nCancelled",
        },
        {
          "fieldname": "comment",
          "fieldtype": "Small Text",
          "label": "Comment",
          "depends_on": "eval:doc.status == 'Hold'",
          "mandatory_depends_on": "eval:doc.status == 'Hold'",
        },
      ],
      size: 'small',
      primary_action: function() {
        set_status(frm, d.get_values().status, d.get_values().comment);
        d.hide();
      },
      primary_action_label: __("Set Project Status")
  });

  d.show();
}

/* applied dialog instance to show customer Credential */
let customer_credentials = function (frm) {
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
              'customer':frm.doc.customer,
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
              'customer':frm.doc.customer,
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

/**
 *function sets the edit expected end date field as read only according to the permissions set
 *
 */
function field_perms(frm) {
  frappe.db.get_single_value('Compliance Settings', 'role_allowed_to_edit_expected_end_date_in_project')
  .then(role => {
    if (role && frappe.user_roles.includes(role)) {
      frm.set_df_property('edit_expected_end_date', 'read_only', 0)
    } else {
      frm.set_df_property('edit_expected_end_date', 'read_only', 1)
    }
  })
}
