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
				{ label: "Template", value: "template" },
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
