
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
      if(child.custom_has_document){
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
      }
    },
    custom_has_document: function (frm, cdt, cdn) {
        var child = locals[cdt][cdn];
        var customDocumentsTable = frm.doc.custom_documents_required || [];

        // If custom_has_document is unchecked, remove related documents from custom_documents_required
        if (!child.custom_has_document) {
            // Filter out rows related to the task
            frm.doc.custom_documents_required = customDocumentsTable.filter(function(row) {
                return row.task !== child.task;
            });

            frm.refresh_field('custom_documents_required'); // Refresh the field to reflect the changes
        }
    }
});
