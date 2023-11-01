// Copyright (c) 2023, efeone and contributors
// For license information, please see license.txt

frappe.ui.form.on('Task Assigning Tool', {
	refresh: function(frm) {
    frm.disable_save();
		frm.toggle_display('add_to_subcategories', false);
	},
	setup: function(frm) {
    set_filters(frm);
  },
	assign_from: function(frm) {
		if (frm.doc.assign_from) {
			prepare_task_reassign(frm);
		}
		else {
			clear_values(frm);
		}
	},
	assign: function(frm) {
        // Get the selected 'assign_from' and 'assign_to' values
        var assignFrom = frm.doc.assign_from;
        var assignTo = frm.doc.assign_to;

        if (!assignFrom || !assignTo) {
            frappe.msgprint('Please select both "Assign From" and "Assign To" users.');
            return;
        }

        // Get the selected tasks from the 'task_reassigns' table
        var selectedTasks = frm.doc.task_reassigns || [];

        if (selectedTasks.length === 0) {
            frappe.msgprint('Please select tasks to reassign.');
            return;
        }

        var selectedTaskIds = selectedTasks.map(function(task) {
            return task.task_id;
        });

        frappe.call({
            method: 'one_compliance.one_compliance.doctype.task_assigning_tool.task_assigning_tool.reassign_tasks',
            args: {
                assign_from: assignFrom,
                assign_to: assignTo,
                selected_tasks_json: selectedTaskIds
            },
            freeze: true,
            freeze_message: 'Reassigning tasks...',
            callback: function(r) {
                if (r.message === 'Tasks reassigned successfully') {
                    frappe.msgprint('Tasks reassigned successfully.');
                    // Refresh the form to update the 'task_reassigns' table
                    frm.reload_doc();
                } else {
                    frappe.msgprint('Error: Unable to reassign tasks.');
                }
            }
        });
    },
		compliance_categories: function(frm) {
			 // Get the selected Compliance Category
			 var selectedCategory = frm.doc.compliance_categories;

			 if (selectedCategory) {
					 // Make an AJAX call to the server to fetch executives
					 frappe.call({
							 method: 'one_compliance.one_compliance.doctype.task_assigning_tool.task_assigning_tool.get_compliance_executives',
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
                method: 'one_compliance.one_compliance.doctype.task_assigning_tool.task_assigning_tool.add_employee_to_compliance_executive',
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
	frm.clear_table('compliance_executives');
	frm.refresh_field('compliance_executives');
}

let set_filters = function(frm){
	frm.set_query('assign_from', function() {
			return {
					query: 'one_compliance.one_compliance.doctype.task_assigning_tool.task_assigning_tool.get_users_by_department',
					filters: {
							department: frm.doc.department
					}
			};
	});
	frm.set_query('assign_to', function() {
			return {
					query: 'one_compliance.one_compliance.doctype.task_assigning_tool.task_assigning_tool.get_users_by_department',
					filters: {
							department: frm.doc.department
					}
			};
	});
	frm.set_query('compliance_categories', function() {
    return {
        query: 'one_compliance.one_compliance.doctype.task_assigning_tool.task_assigning_tool.get_compliance_categories_for_user',
        filters: {
            user_id: frm.doc.employee
        }
    };
});

}

function prepare_task_reassign(frm) {
    if (frm.doc.assign_from) {
        frappe.call({
            method: 'one_compliance.one_compliance.doctype.task_assigning_tool.task_assigning_tool.get_tasks_for_user',
            args: {
                assign_from: frm.doc.assign_from
            },
            freeze: true,
            freeze_message: __("Preparing Task Reassign.."),
            callback: (r) => {
                frm.toggle_display('task_reassigns', r && r.message && r.message.length > 0);

                if (r && r.message && r.message.length > 0) {
                    frm.clear_table('task_reassigns');
                    r.message.forEach(task => {
                        let task_reassign = frm.add_child('task_reassigns');
                        task_reassign.task_id = task.task_id;
                        task_reassign.subject = task.subject;
                        task_reassign.project = task.project;
                    });
                    frm.refresh_field('task_reassigns');
                } else {
                    frappe.msgprint(__("Currently, the user '{0}' has no tasks.", [frm.doc.assign_from]));
                }
            }
        })
    } else {
        frm.toggle_display('task_reassigns', false);
        frappe.msgprint(__("Please select an 'assign_from' user."));
    }
}

function get_available_subcategories(frm) {
    if (frm.doc.compliance_categories) {
        frappe.call({
            method: 'one_compliance.one_compliance.doctype.task_assigning_tool.task_assigning_tool.get_available_subcategories',
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
        method: 'one_compliance.one_compliance.doctype.task_assigning_tool.task_assigning_tool.add_to_subcategories',
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
