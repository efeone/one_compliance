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
		fieldtype: "Data",
		change() {
			frappe.msgprint(taskField.get_value());
		}
	});
	let projectField = page.add_field({
		label: __("Project"),
		fieldname: "project",
		fieldtype: "Data",
		change() {
			frappe.msgprint(projectField.get_value());
		}
	});
	let customerField = page.add_field({
		label: __("Customer"),
		fieldname: "customer",
		fieldtype: "Data",
		change() {
			frappe.msgprint(customerField.get_value());
		}
	});
	let employeeField = page.add_field({
		label: __("Employee"),
		fieldname: "employee",
		fieldtype: "Data",
		change() {
			frappe.msgprint(employeeField.get_value());
		}
	});
	let employeeGroupField = page.add_field({
		label: __("Employee Group"),
		fieldname: "employee_group",
		fieldtype: "Data",
		change() {
			frappe.msgprint(employeeGroupField.get_value());
		}
	});
	let categoryField = page.add_field({
		label: __("Compliance Category"),
		fieldname: "compliance_category",
		fieldtype: "Data",
		change() {
			frappe.msgprint(categoryField.get_value());
		}
	});
	let subcategoryField = page.add_field({
		label: __("Compliance Sub Category"),
		fieldname: "compliance_sub_category",
		fieldtype: "Data",
		change() {
			frappe.msgprint(subcategoryField.get_value());
		}
	});
	let fromDateField = page.add_field({
		label: __("From Date"),
		fieldname: "from_date",
		fieldtype: "Data",
		change() {
			frappe.msgprint(fromDateField.get_value());
		}
	});
	let toDateField = page.add_field({
		label: __("To Date"),
		fieldname: "to_date",
		fieldtype: "Data",
		change() {
			frappe.msgprint(toDateField.get_value());
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
			refresh_jobs(page);
		}
	});
}

function show(page){
	refresh_jobs(page);
}

function refresh_jobs(page){
	// Clear existing tasks from the page
  page.body.find(".task-entry").remove();

	const selectedStatus = page.fields_dict.status.get_value();

	frappe.call({
			method: "one_compliance.one_compliance.page.task_management_tool.task_management_tool.get_task",
			 args: { status: selectedStatus },
			 callback: (r) => {
				if (r.message && r.message.length>0) {
						$(frappe.render_template("task_management_tool", {task_list:r.message})).appendTo(page.body);

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
                default: assigneesList[0]
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
										// Handle the response if needed
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

function set_status_colors() {
    const statusElements = document.querySelectorAll('.col-md-1[status-span]');

    statusElements.forEach(element => {
        const status = element.getAttribute('status-span');

        if (status === 'Open') {
            element.style.color = 'blue';
        } else if (status === 'Completed') {
            element.style.color = 'green';
        } else if (status === 'Overdue') {
            element.style.color = 'red';
        }
    });
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
