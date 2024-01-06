// Copyright (c) 2023, efeone and contributors
// For license information, please see license.txt

frappe.ui.form.on('Task Reassignment', {
	refresh: function(frm) {
    frm.disable_save();
		frm.toggle_display('add_to_subcategories', false);
		frm.set_df_property('task_reassigns', 'cannot_delete_rows', true);
		frm.set_df_property('assign_to', 'cannot_delete_rows', true);

		frm.set_df_property('task_reassigns', 'cannot_add_rows', true);
		frm.set_df_property('assign_to', 'cannot_add_rows', true);

		if(frm.doc.assignment_type === 'Transfer'){
			frm.add_custom_button('Get Allocation Entries', () => {
				get_allocation_entries(frm)
			});
			frm.change_custom_button_type('Get Allocation Entries', null, 'primary');
		}
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
	assignment_type: function(frm) {
		if(frm.doc.assignment_type === 'Transfer'){
			frm.add_custom_button('Get Allocation Entries', () => {
				get_allocation_entries(frm)
			});
			frm.change_custom_button_type('Get Allocation Entries', null, 'primary');
		}
	},
	compliance_categories: function(frm) {
			 // Get the selected Compliance Category
			 var selectedCategory = frm.doc.compliance_categories;

			 if (selectedCategory) {
					 // Make an AJAX call to the server to fetch executives
					 frappe.call({
							 method: 'one_compliance.one_compliance.doctype.task_reassignment.task_reassignment.get_compliance_executives',
							 args: { compliance_category: selectedCategory },
							 callback: function(response) {
									 if (response.message) {
											 // Clear the existing "Compliance Executives" table
											 frm.clear_table('compliance_executives');

											 // Iterate through the response and add records to the table
											 response.message.forEach(function(executive) {
												 var row = frappe.model.add_child(frm.doc, 'Compliance Executives', 'compliance_executives');
													row.employee = executive.employee;
													row.designation = executive.designation;
													row.employee_name = executive.employee_name;
													// Set other child table fields as needed
											 });

											 frm.refresh_field('compliance_executives');
									 }
									 var selectedEmployee = frm.doc.employee;

									 // Fetch the name of the employee using user_id
									 fetchEmployeeName(selectedEmployee, function(employeeName) {

									    // Check if the selected employee is in Compliance Executives and show the button
									    var isEmployeeInExecutives = response.message.some(function(executive) {
									        return executive.employee === employeeName;
									    });

									    frm.toggle_display('add_to_subcategories', isEmployeeInExecutives);
											frm.toggle_display('add_employee', !isEmployeeInExecutives);
									});
							 }
					 });
			 }
	 },
	 add_employee: function(frm) {
        var selectedEmployee = frm.doc.employee;
        var selectedCategory = frm.doc.compliance_categories;

        if (selectedEmployee && selectedCategory) {
            // Make a server call to add the employee to the Compliance Category
            frappe.call({
                method: 'one_compliance.one_compliance.doctype.task_reassignment.task_reassignment.add_employee_to_compliance_executive',
                args: {
                    employee: selectedEmployee,
                    compliance_category: selectedCategory
                },
                callback: function(response) {
                    if (response.message) {
                        frappe.msgprint('Employee added to Compliance Category.');
												frm.events.compliance_categories(frm);

                    } else {
                        frappe.msgprint('Error adding employee.');
                    }
                }
            });
        } else {
            frappe.msgprint('Please select an employee and a Compliance Category.');
        }
    },
		add_to_subcategories: function(frm) {
        get_available_subcategories(frm);
    }
});

let clear_values = function (frm) {
	// clear field values
	frm.clear_table('task_reassigns');
	frm.refresh_field('task_reassigns');
	frm.clear_table('assign_to');
	frm.refresh_field('assign_to');
	frm.clear_table('compliance_executives');
	frm.refresh_field('compliance_executives');
}

let set_filters = function(frm){
	frm.set_query('assigned_to', function() {
		if (frm.doc.department) {
					return {
							query: 'one_compliance.one_compliance.doctype.task_reassignment.task_reassignment.get_users_by_department',
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
            query: 'one_compliance.one_compliance.doctype.task_reassignment.task_reassignment.get_subcategories_by_department_and_category',
            filters: {
                department: frm.doc.department,
                category: frm.doc.category
            }
        };
	    } else if (frm.doc.category) {
	        return {
	            query: 'one_compliance.one_compliance.doctype.task_reassignment.task_reassignment.get_subcategories_by_category',
	            filters: {
	                category: frm.doc.category
	            }
	        };
	    } else if (frm.doc.department) {
	        return {
	            query: 'one_compliance.one_compliance.doctype.task_reassignment.task_reassignment.get_subcategories_by_department',
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
					query: 'one_compliance.one_compliance.doctype.task_reassignment.task_reassignment.get_categories_by_department',
					filters: {
							department: frm.doc.department
					}
			};
		} else {
				return {};
		}
	});
	frm.set_query('compliance_categories', function() {
    return {
        query: 'one_compliance.one_compliance.doctype.task_reassignment.task_reassignment.get_compliance_categories_for_user',
        filters: {
            user_id: frm.doc.employee
        }
    };
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
			method: 'one_compliance.one_compliance.doctype.task_reassignment.task_reassignment.allocate_tasks_to_employee',
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

function get_available_subcategories(frm) {
    if (frm.doc.compliance_categories) {
        frappe.call({
            method: 'one_compliance.one_compliance.doctype.task_reassignment.task_reassignment.get_available_subcategories',
            args: {
                compliance_category: frm.doc.compliance_categories,
								employee: frm.doc.employee
            },
            freeze: true,
            freeze_message: __("Preparing Subcategory Reassignment..."),
            callback: (r) => {
                if (r && r.message) {
										console.log(r.message);
                    const subcategories = r.message;
                    const subcategoryOptions = subcategories.map(subcategory => ({

                        value: subcategory.name,
                        label: `${subcategory.name} (${subcategory.status})`
                    }));

                    frappe.prompt({
                        label: __("Select Subcategories for Reassignment"),
                        fieldname: "selected_subcategories",
                        fieldtype: "MultiSelectList",
                        options: subcategoryOptions,
                        reqd: true
                    }, function(values) {
                        const selectedSubcategories = values.selected_subcategories;
                        add_employee_to_subcategories(frm, selectedSubcategories);
                    }, __("Select Subcategories"), "Select");
                }
            }
        });
    }
}

function add_employee_to_subcategories(frm, selectedSubcategories) {
    frappe.call({
        method: 'one_compliance.one_compliance.doctype.task_reassignment.task_reassignment.add_to_subcategories',
        args: {
            employee: frm.doc.employee,
            compliance_category: frm.doc.compliance_categories,
            selected_subcategories: selectedSubcategories
        },
        callback: function(response) {
            if (response.message) {
                frappe.msgprint('Employee added to selected subcategories.');
            } else {
                frappe.msgprint('Error adding employee to subcategories.');
            }
        }
    });
}


function fetchEmployeeName(user_id, callback) {
    frappe.call({
        method: 'frappe.client.get_value',
        args: {
            doctype: 'Employee',
            fieldname: "name",
            filters: { user_id: user_id }
        },
        callback: function(res) {
            if (res.message && res.message.name) {
                callback(res.message.name);
            } else {
                callback('');
            }
        }
    });
}
