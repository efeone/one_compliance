
frappe.ui.form.on('Project Template', {
    setup: function(frm) {
        set_filters(frm)
    }
});

frappe.ui.form.on('Project Template Task', {
    custom_documents_required: function (frm, cdt, cdn) {
        var child = locals[cdt][cdn];
        if(child.custom_has_document){
            if(frm.is_new()){
                frappe.throw('You need to save the document to perform this action.')
            }
            else {
                frappe.call({
                    method: 'one_compliance.one_compliance.doc_events.project_template.get_existing_documents',
                    args: {
                        template: frm.doc.name,
                        task: child.task,
                    },
                    callback: function (r) {
                        if (r.message) {
                            var documents_required = r.message;
                            documents_required_popup(frm, documents_required, child);
                        }
                    }
                });    
            }
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

function set_filters(frm){
    //filter the compliance sub category based on compliance category
    frm.set_query('compliance_sub_category', () => {
        return {
            filters: {
                compliance_category : frm.doc.compliance_category
            }
        }
    });
}

function documents_required_popup(frm, documents_required, child){
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
            documents_required_primary_action(frm, values, child);
            dialog.hide();
        },
        primary_action_label: __("Save"),
        secondary_action_label: __("Create a New Task Document"),
        secondary_action: function() {
            // Open a new dialog to create a Task Document
            frappe.new_doc('Task Document', function(doc) {

            });
        }
    });
    dialog.show();
}

function documents_required_primary_action(frm, values, child){
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
            }
            else {
                frappe.msgprint('Error: Unable to update documents required.');
            }
        }
    });
}
