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
                        frm.doc.created_project = r.message;
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
    sub_category: function(frm) {
        if (frm.doc.sub_category) {
            frappe.call({
                method: 'one_compliance.one_compliance.doctype.internal_project_tool.internal_project_tool.task_assign',
                args: {
                    docs: JSON.stringify(frm.doc)
                },
                callback: function(r) {
                    if (r.message) {
                        frm.clear_table('tasks');
                        $.each(r.message, function(i, task) {
                            let row = frm.add_child('tasks');
                            row.task = task.task;
                            row.subject = task.subject;
                            row.type = task.type;
                            row.custom_task_duration = task.custom_task_duration;
                            row.employee_or_group = task.employee_or_group;
                        });
                        frm.refresh_field('tasks');
                        frm.set_df_property('tasks', 'hidden', 0);
                    }
                }
            });
        } else {
            frm.set_df_property('tasks', 'hidden', 1);
        }
    }
});
