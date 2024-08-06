frappe.ui.form.on('Internal Project Tool', {
    refresh: function(frm) {
        frm.disable_save();
        frm.doc.created_project = null;
        frm.add_custom_button(__('Create Project'), function() {
            frappe.call({
                method: 'one_compliance.one_compliance.doctype.internal_project_tool.internal_project_tool.create_project',
                args: {
                    'doc_data': JSON.stringify(frm.doc)
                },
                callback: function(r) {
                    if (r.message) {
                        frm.doc.created_project = r.message; // Store the created project ID/name
                        frappe.msgprint(__('Project {0} created successfully', [r.message]));

                        // Add the "View Project" button after the project is created
                        frm.add_custom_button(__('View Project'), function() {
                            frappe.set_route('Form', 'Project', frm.doc.created_project);
                        }).addClass("btn-secondary");
                    } else {
                        frappe.msgprint(__('Failed to create project.'));
                    }
                }
            });
        }).addClass("btn-primary");

        frm.set_query('sub_category', function() {
            return {
                filters: {
                    internal: 1
                }
            };
        });
    },
});
