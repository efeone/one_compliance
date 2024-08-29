// Copyright (c) 2024, efeone and contributors
// For license information, please see license.txt

frappe.ui.form.on("Internal Project Management", {
    refresh: function(frm) {
        frm.disable_save();
        frm.add_custom_button(__('Create Project'), function() {
            frm.call("create_project")
        })

        frm.set_query('compliance_sub_category', function() {
            return {
                filters: {
                    internal: 1
                }
            };
        });
    },
    compliance_sub_category: function(frm) {
        if (frm.doc.compliance_sub_category) {
            frappe.call({
                method: 'one_compliance.one_compliance.doctype.internal_project_management.internal_project_management.task_assign',
                args: {
                    compliance_sub_category: frm.doc.compliance_sub_category
                },
                callback: function(r) {
                    if (r.message) {
                        frm.clear_table('task_details');
                        $.each(r.message, function(i, task) {
                            let row = frm.add_child('task_details');
                            row.task = task.task;
                            row.subject = task.subject;
                            row.type = task.type;
                            row.custom_task_duration = task.custom_task_duration;
                            row.employee_or_group = task.employee_or_group;
                        });
                        frm.refresh_field('task_details');
                        frm.set_df_property('task_details', 'hidden', 0);
                    }
                }
            });
        } else {
            frm.set_df_property('task_details', 'hidden', 1);
        }
    }
});