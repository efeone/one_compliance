// Copyright (c) 2023, efeone and contributors
// For license information, please see license.txt

frappe.ui.form.on('Task Bulk Assignment', {
	refresh: function(frm) {
    frm.disable_save();
		frm.set_df_property('task_reassigns', 'cannot_delete_rows', true);
		frm.set_df_property('assign_to', 'cannot_delete_rows', true);

		frm.set_df_property('task_reassigns', 'cannot_add_rows', true);
		frm.set_df_property('assign_to', 'cannot_add_rows', true);


		frm.add_custom_button('Get Allocation Entries', () => {
			get_allocation_entries(frm)
		});
		frm.change_custom_button_type('Get Allocation Entries', null, 'primary');
		if (frm.doc.task_reassigns.length || frm.doc.assign_to.length) {
			frm.add_custom_button('Allocate', () => {
				allocate_tasks_to_employee(frm)
			});
			frm.change_custom_button_type('Allocate', null, 'primary');
			frm.change_custom_button_type('Get Allocation Entries', null, 'default');
		}
	},
	setup: function(frm) {
    set_filters(frm);
  },
});

let clear_values = function (frm) {
	// clear field values
	frm.clear_table('task_reassigns');
	frm.refresh_field('task_reassigns');
	frm.clear_table('assign_to');
	frm.refresh_field('assign_to');
}

let set_filters = function(frm){
	frm.set_query('assigned_to', function() {
		if (frm.doc.department) {
					return {
							query: 'one_compliance.one_compliance.doctype.task_bulk_assignment.task_bulk_assignment.get_users_by_department',
							filters: {
									department: frm.doc.department
							}
					};
			} else {
					return {};
			}
	});
	frm.set_query('sub_category', function() {
    if (frm.doc.department && frm.doc.category) {
        return {
            query: 'one_compliance.one_compliance.doctype.task_bulk_assignment.task_bulk_assignment.get_subcategories_by_department_and_category',
            filters: {
                department: frm.doc.department,
                category: frm.doc.category
            }
        };
	    } else if (frm.doc.category) {
	        return {
	            query: 'one_compliance.one_compliance.doctype.task_bulk_assignment.task_bulk_assignment.get_subcategories_by_category',
	            filters: {
	                category: frm.doc.category
	            }
	        };
	    } else if (frm.doc.department) {
	        return {
	            query: 'one_compliance.one_compliance.doctype.task_bulk_assignment.task_bulk_assignment.get_subcategories_by_department',
	            filters: {
	                department: frm.doc.department
	            }
	        };
	    } else {
	        return {};
	    }
	});
	frm.set_query('category', function() {
		if (frm.doc.department) {
			return {
					query: 'one_compliance.one_compliance.doctype.task_bulk_assignment.task_bulk_assignment.get_categories_by_department',
					filters: {
							department: frm.doc.department
					}
			};
		} else {
				return {};
		}
	});
}

function get_allocation_entries(frm) {
	frappe.call({
		doc:frm.doc,
		method: 'get_allocation_entries',
		callback: (r) => {
			if (r.message === 'success') {
							frm.refresh();
					} else {
							frappe.msgprint('Error retrieving data');
					}
			}
	});
}

function allocate_tasks_to_employee(frm){

		let selectedTasks = frm.fields_dict.task_reassigns.grid.get_selected_children();

		if (selectedTasks.length === 0) {
			frappe.msgprint('Please select tasks to allocate.');
			return;
		}

		// Get the selected employees to whom tasks will be allocated
		var selectedEmployees = frm.fields_dict.assign_to.grid.get_selected_children();

		if (selectedEmployees.length === 0) {
			frappe.msgprint('Please select employees to whom tasks will be allocated.');
			return;
		}

		// Extract task IDs and employee IDs for allocation
		var selectedTaskIds = selectedTasks.map(function(task) {
			return task.task_id;
		});

		var selectedEmployeeIds = selectedEmployees.map(function(employee) {
			return employee.employee; // Replace 'employee_id' with the actual field name containing the employee ID
		});

		frappe.call({
			method: 'one_compliance.one_compliance.doctype.task_bulk_assignment.task_bulk_assignment.allocate_tasks_to_employee',
			args: {
					selected_task_ids: selectedTaskIds,
					selected_employee_ids: selectedEmployeeIds
			},
			freeze: true,
			freeze_message: 'Allocating tasks...',
			callback: function(r) {
					if (r.message === 'Tasks allocated successfully') {
							frappe.msgprint('Tasks allocated successfully.');
							// Refresh the form or perform necessary updates
							// For example, if you want to reload the form:
							frm.reload_doc();
					} else {
							frappe.msgprint('Error: Unable to allocate tasks.');
					}
			}
		});

}
