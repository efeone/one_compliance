frappe.pages['task-management-tool'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Task Management Tool',
		single_column: true
	});



	page.main.addClass("frappe-card");

	make_filters(page);

	show(page);
}

function make_filters(page) {
	let taskField = page.add_field({
		label: __("Task"),
		fieldname: "task",
		fieldtype: "Link",
		options: "Task",
		change() {
			refresh_tasks(page);
		}
	});
	let projectField = page.add_field({
		label: __("Project"),
		fieldname: "project",
		fieldtype: "Link",
		options: "Project",
		change() {
			refresh_tasks(page);
		}
	});
	let customerField = page.add_field({
		label: __("Customer"),
		fieldname: "customer",
		fieldtype: "Link",
		options:"Customer",
		change() {
			refresh_tasks(page);
		}
	});
	let employeeField = page.add_field({
		label: __("Employee"),
		fieldname: "employee",
		fieldtype: "Link",
		options: "User",
		default: get_employee_id(),
		change() {
			refresh_tasks(page);
		},
		read_only: frappe.session.user === 'Administrator' ? 0 : 1
	});
	let employeeGroupField = page.add_field({
		label: __("Employee Group"),
		fieldname: "employee_group",
		fieldtype: "Link",
		options: "Employee Group",
		change() {
			refresh_tasks(page);
		}
	});
	let categoryField = page.add_field({
		label: __("Compliance Category"),
		fieldname: "compliance_category",
		fieldtype: "Link",
		options: "Compliance Category",
		change() {
			refresh_tasks(page);
		}
	});
	let subcategoryField = page.add_field({
		label: __("Compliance Sub Category"),
		fieldname: "compliance_sub_category",
		fieldtype: "Link",
		options: "Compliance Sub Category",
		change() {
			refresh_tasks(page);
		}
	});
	let fromDateField = page.add_field({
		label: __("From Date"),
		fieldname: "from_date",
		fieldtype: "Date",
		change() {
			refresh_tasks(page);
		}
	});
	let toDateField = page.add_field({
		label: __("To Date"),
		fieldname: "to_date",
		fieldtype: "Date",
		change() {
			refresh_tasks(page);
		}
	});
	let status = page.add_field({
		label: __("Status"),
		fieldname: "status",
		fieldtype: "Select",
		options: [
				{ label: "Open", value: "open" },
				{ label: "Working", value: "working" },
				{ label: "Pending Review", value: "pending_review" },
				{ label: "Overdue", value: "overdue" },
				{ label: "Hold", value: "hold" },
				{ label: "Completed", value: "completed" },
				{ label: "Cancelled", value: "cancelled" },
			],
			default: "open",
		change() {
			refresh_tasks(page);
		}
	});
}

function get_employee_id() {
    if (frappe.session.user === 'Administrator') {
        return '';
    }
		else {
				return frappe.session.user
		}
}

function show(page){
	refresh_tasks(page);
}

function refresh_tasks(page){
	// Clear existing tasks from the page
  page.body.find(".task-entry").remove();

	const selectedStatus = page.fields_dict.status.get_value();
	const taskName = page.fields_dict.task.get_value();
	const projectName = page.fields_dict.project.get_value();
	const customerName = page.fields_dict.customer.get_value();
	const category = page.fields_dict.compliance_category.get_value();
	const subCategory = page.fields_dict.compliance_sub_category.get_value();
	const employee = page.fields_dict.employee.get_value();
	const employeeGroup = page.fields_dict.employee_group.get_value();
	const from_date = page.fields_dict.from_date.get_value();
	const to_date = page.fields_dict.to_date.get_value();

	frappe.call({
			method: "one_compliance.one_compliance.page.task_management_tool.task_management_tool.get_task",
			 args: { status: selectedStatus,
				 			 task: taskName,
							 project: projectName,
							 customer: customerName,
							 category: category,
							 sub_category: subCategory,
							 employee: employee,
							 employee_group: employeeGroup,
							 from_date: from_date,
							 to_date: to_date
							},
			 callback: (r) => {
				if (r.message && r.message.length>0) {
						$(frappe.render_template("task_management_tool", {task_list:r.message})).appendTo(page.body);

						page.body.find(".addAssigneeBtn").on("click", function () {
							var taskName = $(this).attr("task-id");
              showAssignEntryDialog(taskName);
            });

						page.body.find(".timeEntryButton").on("click", function () {
							var taskName = $(this).attr("task-id");
							var projectName = $(this).attr("project-id");
							var assignees = $(this).attr("assignees");
              showTimeEntryDialog(taskName, projectName, assignees);
            });

						page.body.find(".documentButton").on("click", function () {
							var subCategory = $(this).attr("sub-category");
							var customer = $(this).attr("customer");
              cusomerDocuments(subCategory, customer);
            });

						page.body.find(".credentialButton").on("click", function () {
							var subCategory = $(this).attr("sub-category");
							var customer = $(this).attr("customer");
              cusomerCredentials(subCategory, customer);
            });

						set_status_colors();
				}
			},
			freeze: true,
			freeze_message: 'Loading Task List'
		});

}

function showAssignEntryDialog(taskName){
	var dialog = new frappe.ui.Dialog({
        title: __("Add Employees"),
        fields: [
						{
								label: __("Assign To"),
								fieldname: "assign_to",
								fieldtype: 'MultiSelectPills',
								get_data: function (txt) {
									return frappe.db.get_link_options("User", txt, {
										user_type: "System User",
										enabled: 1,
									});
								},
						}
        ],
        primary_action: function (values) {
						frappe.call({
								method: "frappe.desk.form.assign_to.add",
								args: {
                    doctype: "Task",
                    name: taskName,
                    assign_to: values.assign_to,
                },
                callback: function (r) {
                    frappe.msgprint("Assignment added successfully!");
										location.reload();
                }
						});
            dialog.hide();
        },
        primary_action_label: __("Add")
    });
    dialog.show();
}
// Function to show the dialog box
function showTimeEntryDialog(taskName, projectName, assignees) {
	var assigneesList = assignees ? assignees.split(',') : [];

	var dialog = new frappe.ui.Dialog({
        title: __("Time Entry Dialog"),
        fields: [
						{
								label: __("Employee"),
								fieldname: "employee",
								fieldtype: 'Select',
								options: assigneesList,
                default: get_employee(assigneesList, function (employee) {
                    dialog.set_value("employee", employee);
                })
						},
            {
                label: __("Project"),
                fieldname: "project",
                fieldtype: 'Link',
                options: 'Project',
								default: projectName
            },
            {
                label: __("From Time"),
                fieldname: "from_time",
                fieldtype: 'Datetime',
                reqd: true,
            },
						{
							fieldtype: "Column Break",
							fieldname: "col_break_1",
						},
						{
                label: __("Task"),
                fieldname: "task",
                fieldtype: 'Link',
                options: 'Task',
								default: taskName
            },
						{
                label: __("Activity"),
                fieldname: "activity",
                fieldtype: 'Link',
                reqd: true,
								options: 'Activity Type'
            },
            {
                label: __("To Time"),
                fieldname: "to_time",
                fieldtype: 'Datetime',
                reqd: true,
            }
        ],
        primary_action: function (values) {
						frappe.call({
								method: "one_compliance.one_compliance.page.task_management_tool.task_management_tool.create_timesheet",
								args: {
										project: values.project,
										task: values.task,
										employee: values.employee,
										activity: values.activity,
										from_time: values.from_time,
										to_time: values.to_time
								},
								callback: function (r) {
										frappe.msgprint("Timesheet created successfully!");
								}
						});
            dialog.hide();
        },
        primary_action_label: __("Submit")
    });

    // Show the dialog
    dialog.show();
}

function get_employee(assigneesList, callback) {
	if (frappe.session.user === 'Administrator') {
			return assigneesList[0]
	}
	else {
			frappe.call({
					method: "frappe.client.get_value",
					args: {
							doctype: "Employee",
							filters: { "user_id": frappe.session.user },
							fieldname: "employee_name"
					},
					callback: function (response) {
							var employeeName = response.message ? response.message.employee_name : null;
							callback(employeeName);
					}
			});
	}
}

function set_status_colors() {
		const taskElements = document.querySelectorAll('.card.task-entry');

		taskElements.forEach(taskElement => {
				const statusElement = taskElement.querySelector('.col-md-1[status-span]');
				const status = statusElement.getAttribute('status-span');
				const projectElement = taskElement.querySelector('.card-subtitle');
				const isPayable = statusElement.getAttribute('is-payable') === '1';

        if (status === 'Open') {
					statusElement.style.color = 'blue';
					showTicIcon(statusElement, isPayable);
					projectElement.style.color = 'blue';
        } else if (status === 'Completed') {
            statusElement.style.color = 'green';
						projectElement.style.color = 'green';
        } else if (status === 'Overdue') {
            statusElement.style.color = 'red';
						showTicIcon(statusElement, isPayable);
						projectElement.style.color = 'red';
        } else if (status === 'Working') {
            statusElement.style.color = 'tomato';
						showTicIcon(statusElement, isPayable);
						projectElement.style.color = 'tomato';
        }
    });
		function showTicIcon(element, isPayable) {
			if (!element.querySelector('.fa-check-circle')) {
        const ticIcon = document.createElement('i');
        ticIcon.className = 'fas fa-check-circle';
        ticIcon.style.color = 'green';
        ticIcon.style.cursor = 'pointer';
				ticIcon.title = 'Update Status';
				if(isPayable) {
					console.log(isPayable);
            ticIcon.title += '\n(Payable Task)';
        }

        element.appendChild(document.createTextNode(' '));
        element.appendChild(ticIcon);

        const taskName = element.getAttribute('task-name');
        const taskId = element.getAttribute('task-id');
        const projectId = element.getAttribute('project-id');

        ticIcon.addEventListener('click', function () {
            update_status(taskName, projectId, taskId);
        });
			}
    }
}

function cusomerDocuments(subCategory, customer) {
	frappe.call({
		method:'one_compliance.one_compliance.utils.view_customer_documents',
		args:{
			'customer': customer,
			'compliance_sub_category': subCategory
		},
		callback:function(r){
			if (r.message){
					var newd = new frappe.ui.Dialog({
						 title: 'Document details',
						 fields: [
							 {
								 label: 'Document Attachment',
								 fieldname: 'document_attachment',
								 fieldtype: 'Data',
								 read_only: 1,
								 default:r.message[0]
							 },
						 ],
						 primary_action_label : 'Download',
						 primary_action(value){
							 window.open(r.message[0])
						 }
					 });
					 newd.show();
				 }
			 }
	 });
}

function cusomerCredentials(subCategory, customer){
	let d = new frappe.ui.Dialog({
		title: 'Enter details',
		fields: [
			{
				label: 'Purpose',
				fieldname: 'purpose',
				fieldtype: 'Link',
				options: 'Credential Type',
				get_query: function () {
					return {
						filters: {
							'compliance_sub_category': subCategory
						}
					};
				}
			}
		],
		primary_action_label: 'View Credential',
		primary_action(values) {
			frappe.call({
				method:'one_compliance.one_compliance.utils.view_credential_details',
				args:{
					'customer': customer,
					'purpose': values.purpose
				},
				callback:function(r){
					if (r.message){
						d.hide();
						let newd = new frappe.ui.Dialog({
							title: 'Credential details',
							fields: [
								{
									label: 'Username',
									fieldname: 'username',
									fieldtype: 'Data',
									read_only: 1,
									default:r.message[0]
								},
								{
									label: 'Password',
									fieldame: 'password',
									fieldtype: 'Data',
									read_only: 1,
									default:r.message[1]
								},
								{
									label: 'Url',
									fieldname: 'url',
									fieldtype: 'Data',
									options: 'URL',
									read_only: 1,
									default:r.message[2]
								 }
								],
								 primary_action_label: 'Close',
								 primary_action(value) {
									 newd.hide();
								 },
								 secondary_action_label : 'Go To URL',
								 secondary_action(value){
									 window.open(r.message[2])
								 }
							 });
							 newd.show();
						 }
					 }
				 })
			 }
		 });
		 d.show();
}

function update_status(taskName, projectId, taskId) {
	let d = new frappe.ui.Dialog({
		title: 'Enter details',
		fields: [
			{
				label: 'Status',
				fieldname: 'status',
				fieldtype: 'Select',
				options: 'Open\nWorking\nPending Review\nCompleted\nHold',
				default: 'Completed'
			},
			{
				label: 'Completed By',
				fieldname: 'completed_by',
				fieldtype: 'Link',
				options: 'User'
			},
			{
				label: 'Completed On',
				fieldname: 'completed_on',
				fieldtype: 'Date',
				default: 'Today'
			},
		],
		primary_action_label: 'Update',
		primary_action(values) {
			frappe.call({
				method: 'one_compliance.one_compliance.doc_events.task.check_payable_task',
				args: {
					'task': taskName,
				},
				callback: function(r){
					if (r.message){
						frappe.call({
							method: 'one_compliance.one_compliance.doc_events.task.check_reimbursement',
							args: {
								'project_id': projectId
							},
							callback: function(resp){
								if (!resp.message){
									d.hide();
									frappe.msgprint('Reimbursement Amount is not given.');
									frappe.set_route("Form", "Project", projectId);
								}
								else {
									update_task_status(values, d, taskId);
								}
							}
						});
					}
					else {
						update_task_status(values, d, taskId);
					}
				}
			});
		},
	});
	d.set_value('completed_by', frappe.session.user);
d.show();
}

function update_task_status(values, d, taskId) {
  frappe.call({
    method: 'one_compliance.one_compliance.doc_events.task.update_task_status',
    args: {
      'task_id': taskId,
      'status': values.status,
      'completed_by': values.completed_by,
      'completed_on': values.completed_on
    },
    callback: function(r){
      if (r.message){
        d.hide();
				location.reload();
      }
    }
  });
}
