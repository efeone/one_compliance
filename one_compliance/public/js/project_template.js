// Copyright (c) 2024, efeone and contributors
// For license information, please see license.txt

frappe.ui.form.on('Project Template', {
    setup: function(frm) {
        set_filters(frm)
        restrict_task_field(frm);
        restrict_premium_task_field(frm);
    },
    custom_add_tasks(frm) {
        new_task_popup(frm);
    },
    custom_add_tasks2: function(frm) {
        new_premium_task_popup(frm);
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

/**
 * The functions below are used to show a popup that will add a task into the task table and disable adding rows the native way
 *
 */
function restrict_task_field(frm){
    frm.fields_dict.tasks.grid.update_docfield_property('task', 'only_select', 1);
    frm.set_df_property('tasks', 'cannot_add_rows', true);
    frappe.model.get_children(frm.doc, "tasks").forEach(e=>{
        frappe.meta.get_docfield('Project Template Task', 'task', e.name).only_select = true;
    })
}

function new_task_popup(frm){
    let primary_action_label = 'Create & Add';
    let dialog = new frappe.ui.Dialog({
        title: 'Task details',
        fields: [
            {
                label: 'Is Existing Task',
                fieldname: 'is_existing_task',
                fieldtype: 'Check',
                change: () => {
                    let is_existing_task = dialog.get_value('is_existing_task');
                    if(is_existing_task){
                        primary_action_label = 'Add';
                    }
                    else {
                        primary_action_label = 'Create & Add';
                    }
                    set_primary_action_label(dialog, primary_action_label)
                }
            },
            {
                label: 'Task',
                fieldname: 'task',
                fieldtype: 'Link',
                options: 'Task',
                only_select: 1,
                get_query: function(){
                    return {
                        filters: {
                            is_template: 1
                        }
                    }
                },
                depends_on: 'eval: doc.is_existing_task',
                mandatory_depends_on: 'eval: doc.is_existing_task',
                change: () => {
                    let task = dialog.get_value('task');
                    frappe.db.get_value('Task', task, 'subject').then(r => {
                        if(r.message.subject){
                            dialog.set_value('subject', r.message.subject);
                        }
                        else {
                            dialog.set_value('subject', );
                        }
                    });
                }
            },
            {
                label: 'Subject',
                fieldname: 'subject',
                fieldtype: 'Data',
                depends_on: 'eval: !doc.is_existing_task',
                mandatory_depends_on: 'eval: !doc.is_existing_task',
            }
        ],
        primary_action_label: primary_action_label,
        primary_action(values) {
            if(values.is_existing_task){
                add_task_row(frm, values.task, values.subject)
            }
            else {
                create_task(frm, values.subject);
            }
            dialog.hide();
        }
    });
    dialog.show();
}

function create_task(frm, subject){
    frappe.db.insert({
        doctype: 'Task',
        subject: subject,
        is_template: 1,
        status: 'Template'
    }).then(doc => {
        if(doc.name){
            add_task_row(frm, doc.name, subject)
        }
    });
}

function add_task_row(frm, task, subject){
    frm.add_child('tasks',{
        'task': task,
        'subject': subject
    });
    frm.refresh_field('tasks');
    restrict_task_field(frm);
}

function set_primary_action_label(dialog, primary_action_label) {
    dialog.get_primary_btn().removeClass("hide").html(primary_action_label);
}

/**
 * The functions below are used to show a popup that will add a task into the Premium Task table and disable adding rows the native way
 *
 */
function restrict_premium_task_field(frm) {
    frm.fields_dict.premium_tasks.grid.update_docfield_property('task', 'only_select', 1);
    frm.fields_dict.premium_tasks.grid.cannot_add_rows = true;
    frm.fields_dict.premium_tasks.grid.refresh();
    frm.fields_dict.premium_tasks.grid.wrapper.find('.grid-add-row').hide();
}

function new_premium_task_popup(frm) {
    let primary_action_label = 'Create & Add';

    let dialog = new frappe.ui.Dialog({
        title: 'Task details',
        fields: [
            {
                label: 'Is Existing Task',
                fieldname: 'is_existing_task',
                fieldtype: 'Check',
                change: () => {
                    let is_existing = dialog.get_value('is_existing_task');
                    if (is_existing) {
                        primary_action_label = 'Add';
                    } else {
                        primary_action_label = 'Create & Add';
                    }
                    set_primary_action_label(dialog, primary_action_label);
                }
            },
            {
                label: 'Task',
                fieldname: 'task',
                fieldtype: 'Link',
                options: 'Task',
                only_select: 1,
                get_query: function() {
                    return {
                        filters: {
                            is_template: 1
                        }
                    };
                },
                depends_on: 'eval: doc.is_existing_task',
                mandatory_depends_on: 'eval: doc.is_existing_task',
                change: () => {
                    let task = dialog.get_value('task');
                    if (task) {
                        frappe.db.get_value('Task', task, 'subject').then(r => {
                            if (r.message.subject) {
                                dialog.set_value('subject', r.message.subject);
                            } else {
                                dialog.set_value('subject', '');
                            }
                        });
                    }
                }
            },
            {
                label: 'Subject',
                fieldname: 'subject',
                fieldtype: 'Data',
                depends_on: 'eval: !doc.is_existing_task',
                mandatory_depends_on: 'eval: !doc.is_existing_task'
            }
        ],
        primary_action_label: primary_action_label,
        primary_action(values) {
            if (values.is_existing_task) {
                add_premium_task_row(frm, values.task, values.subject);
            } else {
                create_premium_task(frm, values.subject);
            }
            dialog.hide();
        }
    });

    dialog.show();
}

function set_primary_action_label(dialog, label) {
    dialog.set_primary_action_label(label);
}

function create_premium_task(frm, subject) {
    frappe.db.insert({
        doctype: 'Task',
        subject: subject,
        is_template: 1,
        status: 'Template'
    }).then(doc => {
        if (doc.name) {
            add_premium_task_row(frm, doc.name, subject);
        }
    });
}

function add_premium_task_row(frm, task, subject) {
    frm.add_child('premium_tasks', {
        'task': task,
        'subject': subject
    });
    frm.refresh_field('premium_tasks');
    restrict_premium_task_field(frm);
}
