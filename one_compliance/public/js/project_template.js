
frappe.ui.form.on('Project Template', {

  setup: function(frm) {
    //filter the compliance sub category based on compliance category
    frm.set_query('compliance_sub_category', () => {
            return {
                filters: {
                    compliance_category : frm.doc.compliance_category
                }
            }
        })
    }
});

frappe.ui.form.on('Project Template Task', {
    custom_documents_required: function (frm, cdt, cdn) {
      var child = locals[cdt][cdn];
      frappe.call({
          method: 'one_compliance.one_compliance.doc_events.project_template.get_existing_documents',
          args: {
              template: frm.doc.name,
              task: child.task,
          },
          callback: function (r) {
              if (r.message) {
                  var documents_required = r.message

                  var dialog = new frappe.ui.Dialog({
                        title: __("Documents Required"),
                        fields: [
                            {
                                label: __("Documents Required"),
                                fieldname: "documents_required",
                                fieldtype: 'MultiSelectPills',
                                default: documents_required,
                                get_data: function (txt) {
                                  return frappe.db.get_link_options("Task Document", txt);
                                },
                            }
                        ],
                        primary_action: function (values) {
                            frappe.call({
                        			method: 'one_compliance.one_compliance.doc_events.project_template.update_documents_required',
                        			args: {
                                  template: frm.doc.name,
                        					documents: values.documents_required,
                        					task: child.task,
                        			},
                        			callback: function(r) {
                                if (r.message === 'success') {
                                      frm.reload_doc();
                                  } else {
                                      frappe.msgprint('Error: Unable to update documents required.');
                                  }
                        			}
                        		});
                            dialog.hide();
                        },
                        primary_action_label: __("Save")
                    });
                    dialog.show();
              }
          }
      });
    },
});
