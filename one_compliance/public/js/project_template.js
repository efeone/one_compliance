// Copyright (c) 2024, efeone and contributors
// For license information, please see license.txt
frappe.ui.form.on('Project Template', {
	setup(frm) {
		set_filters(frm);
		restrict_task_field(frm, 'tasks');
		restrict_task_field(frm, 'premium_tasks');
	},
	refresh(frm) {
		clear_blank_rows(frm, ["tasks", "premium_tasks"]);
	},
	custom_add_tasks(frm) {
		show_task_popup(frm, 'tasks');
	},
	custom_add_tasks2(frm) {
		show_task_popup(frm, 'premium_tasks');
	}
});

frappe.ui.form.on('Project Template Task', {
	custom_documents_required(frm, cdt, cdn) {
		const child = locals[cdt][cdn];
		if (child.custom_has_document) {
			if (frm.is_new()) {
				frappe.throw('You need to save the document to perform this action.');
			} else {
				frappe.call({
					method: 'one_compliance.one_compliance.doc_events.project_template.get_existing_documents',
					args: {
						template: frm.doc.name,
						task: child.task,
					},
					callback(r) {
						if (r.message) {
							documents_required_popup(frm, r.message, child);
						}
					}
				});
			}
		}
	},
	custom_has_document(frm, cdt, cdn) {
		const child = locals[cdt][cdn];
		if (!child.custom_has_document) {
			frm.doc.custom_documents_required = (frm.doc.custom_documents_required || []).filter(
				row => row.task !== child.task
			);
			frm.refresh_field('custom_documents_required');
		}
	}
});

frappe.ui.form.on('Premium Tasks', {
    documents_required: function(frm, cdt, cdn) {
        handle_documents_required(frm, cdt, cdn);
    },

    has_document: function(frm, cdt, cdn) {
        handle_has_document(frm, cdt, cdn);
    }
});

/**
 * Event handlers for the 'Premium Tasks' child table in the 'Project Template' form.
 * Manages the logic for handling required documents associated with premium tasks.
 */
function handle_documents_required(frm, cdt, cdn) {
    const child = locals[cdt][cdn];

    if (child.has_document) {
        if (frm.is_new()) {
            frappe.throw('You need to save the document to perform this action.');
        } else {
            frappe.call({
                method: 'one_compliance.one_compliance.doc_events.project_template.get_existing_documents',
                args: {
                    template: frm.doc.name,
                    task: child.task,
                },
                callback(r) {
                    if (r.message) {
                        documents_required_popup(frm, r.message, child);
                    }
                }
            });
        }
    }
}

/**
 * Removes entries from the 'documents_required' table when 'has_document' is unchecked.
 */
function handle_has_document(frm, cdt, cdn) {
	const child = locals[cdt][cdn];
	if (!child.has_document) {
		frm.doc.custom_documents_required = (frm.doc.custom_documents_required || []).filter(
			row => row.task !== child.task
		);
		frm.refresh_field('custom_documents_required');
	}
}

/**
 * Sets up filters and restricts row addition for task and premium task tables on the Project Template form.
 * Called during the form's setup event.
 */
function set_filters(frm) {
	frm.set_query('compliance_sub_category', () => ({
		filters: { compliance_category: frm.doc.compliance_category }
	}));
}

/**
 * Displays a dialog to select or create documents required for a task.
 */
function documents_required_popup(frm, documents_required, child) {
	const dialog = new frappe.ui.Dialog({
		title: __("Documents Required"),
		fields: [
			{
				label: __("Documents Required"),
				fieldname: "documents_required",
				fieldtype: 'MultiSelectPills',
				default: documents_required,
				get_data: txt => frappe.db.get_link_options("Task Document", txt),
			}
		],
		primary_action_label: __("Save"),
		primary_action(values) {
			update_documents_required(frm, values, child);
			dialog.hide();
		},
		secondary_action_label: __("Create a New Task Document"),
		secondary_action() {
			frappe.new_doc('Task Document');
		}
	});
	dialog.show();
}

/**
 * Calls the backend to update the documents required for a task.
 */
function update_documents_required(frm, values, child) {
	frappe.call({
		method: 'one_compliance.one_compliance.doc_events.project_template.update_documents_required',
		args: {
			template: frm.doc.name,
			documents: values.documents_required,
			task: child.task,
		},
		callback(r) {
			if (r.message === 'success') {
				frm.reload_doc();
			} else {
				frappe.msgprint('Error: Unable to update documents required.');
			}
		}
	});
}

/**
 * Restricts native row addition in a child table and enforces use of the popup dialog.
 * Also sets the 'task' field to only allow selection from existing tasks.
 * @param {string} table_field - The name of the child table field (e.g., 'tasks' or 'premium_tasks').
 */
function restrict_task_field(frm, table_field) {
	const grid = frm.fields_dict[table_field].grid;
	grid.update_docfield_property('task', 'only_select', 1);
	grid.cannot_add_rows = true;
	grid.refresh();
	if (grid.wrapper) {
		grid.wrapper.find('.grid-add-row').hide();
	}
}

/**
 * Shows a dialog to add a new task or select an existing one for a given table (tasks or premium_tasks).
 * Handles both creation and selection logic.
 * @param {string} table_field - The name of the child table field.
 */
function show_task_popup(frm, table_field) {
	let primary_action_label = 'Create & Add';
	const dialog = new frappe.ui.Dialog({
		title: 'Task details',
		fields: [
			{
				label: 'Is Existing Task',
				fieldname: 'is_existing_task',
				fieldtype: 'Check',
				change: () => {
					primary_action_label = dialog.get_value('is_existing_task') ? 'Add' : 'Create & Add';
					set_primary_action_label(dialog, primary_action_label);
				}
			},
			{
				label: 'Task',
				fieldname: 'task',
				fieldtype: 'Link',
				options: 'Task',
				only_select: 1,
				get_query: () => ({ filters: { is_template: 1 } }),
				depends_on: 'eval: doc.is_existing_task',
				mandatory_depends_on: 'eval: doc.is_existing_task',
				change: () => {
					const task = dialog.get_value('task');
					if (task) {
						frappe.db.get_value('Task', task, 'subject').then(r => {
							dialog.set_value('subject', r.message.subject || '');
						});
					}
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
		primary_action_label,
		primary_action(values) {
			if (values.is_existing_task) {
				add_task_row(frm, table_field, values.task, values.subject);
			} else {
				create_task(frm, table_field, values.subject);
			}
			dialog.hide();
		}
	});
	dialog.show();
}

/**
 * Creates a new Task document and adds it as a row to the specified child table.
 * @param {object} frm - The current form object.
 * @param {string} table_field - The name of the child table field.
 * @param {string} subject - The subject/title of the new task.
 */
function create_task(frm, table_field, subject) {
	frappe.db.insert({
		doctype: 'Task',
		subject,
		is_template: 1,
		status: 'Template'
	}).then(doc => {
		if (doc.name) {
			add_task_row(frm, table_field, doc.name, subject);
		}
	});
}

/**
 * Adds a row to the specified child table with the given task and subject.
 * Refreshes the table and re-applies restrictions.
 * @param {string} table_field - The name of the child table field.
 * @param {string} task - The name of the Task document.
 * @param {string} subject - The subject/title of the task.
 */
function add_task_row(frm, table_field, task, subject) {
	frm.add_child(table_field, { task, subject });
	frm.refresh_field(table_field);
	restrict_task_field(frm, table_field);
}

/**
 * Clears unwanted blank rows from specified child tables
 * if the parent doc is new (unsaved).
 * @param {Array<string>} tables - List of child table fieldnames.
 */
function clear_blank_rows(frm, tables) {
	if (frm.is_new()) {
		tables.forEach(table_field => {
			frm.clear_table(table_field);
			frm.refresh_field(table_field);
		});
	}
}

function set_primary_action_label(dialog, primary_action_label) {
	dialog.get_primary_btn().removeClass("hide").html(primary_action_label);
}
