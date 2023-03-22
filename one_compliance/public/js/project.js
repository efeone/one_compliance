frappe.ui.form.on('Project',{
    refresh(frm){
        frm.add_custom_button('Sales Invoice', () => {
            frappe.model.open_mapped_doc({
                method: "one_compliance.one_compliance.doc_events.project.make_sales_invoice",
                frm: cur_frm
            })
        }, 'Create');
        let roles = frappe.user_roles;
    		if(roles.includes('Compliance Manager') || roles.includes('Director')){
        frm.add_custom_button('View Credential', () => {
  				customer_credentials(frm)
  				})

    }
  }
});
/* applied dialog instance to show customer Credential */

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
        method:'one_compliance.one_compliance.doc_events.project.add_credential_details',
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
