frappe.pages['task-management-tool'].on_page_load = function (wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Task Management Tool',
		single_column: true
	});

	page.main.addClass("frappe-card");

	page.current_page = 1;
	page.page_length = 20;

	make_filters(page);
	if (!frappe.route_options || !frappe.route_options.project) {
		refresh_tasks(page, true);
	}
}

frappe.pages['task-management-tool'].on_page_show = function (wrapper) {
	var page = wrapper.page;
	
	if (frappe.route_options && frappe.route_options.project) {
		page.fields_dict.project.set_value(frappe.route_options.project);
		
		frappe.route_options = null;
		
		setTimeout(() => {
			refresh_tasks(page);
		}, 500);
	}
}

/*
Creates and configures all filter fields for the Task Management Tool page.
Each filter refreshes the task list when its value changes.
*/
function make_filters(page) {
	const project_id = localStorage.getItem('selected_project_id');

	const filters = [
		{ label: "Task", fieldname: "task", options: "Task" },
		{ label: "Project", fieldname: "project", options: "Project", default: project_id },
		{ label: "Customer", fieldname: "customer", options: "Customer" },
		{
			label: "Employee",
			fieldname: "employee",
			options: "User",
			default: get_employee_id(),
			read_only: frappe.session.user !== "Administrator"
		},
		{ label: "Employee Group", fieldname: "employee_group", options: "Employee Group" },
		{ label: "Department", fieldname: "department", options: "Department" },
		{ label: "Compliance Sub Category", fieldname: "compliance_sub_category", options: "Compliance Sub Category" },
		{ label: "From Date", fieldname: "from_date", fieldtype: "Date" },
		{ label: "To Date", fieldname: "to_date", fieldtype: "Date" }
	];

	localStorage.removeItem('selected_project_id');

	const bind_refresh = (fieldname) => {
		let field = page.fields_dict[fieldname];
		field.$input.on("change", function () {
			refresh_tasks(page);
		});
	};

	filters.forEach(f => {
		page.add_field({
			label: __(f.label),
			fieldname: f.fieldname,
			fieldtype: f.fieldtype || "Link",
			options: f.options,
			default: f.default || "",
			read_only: f.read_only ? 1 : 0,
			change() {
				if (page.fields_dict[f.fieldname].get_value()) {
					refresh_tasks(page);
				}
			}
		});
		bind_refresh(f.fieldname);
	});

	page.add_field({
		label: __("Status"),
		fieldname: "status",
		fieldtype: "Select",
		options: [
			{},
			{ label: "Open", value: "open" },
			{ label: "Working", value: "working" },
			{ label: "Pending Review", value: "pending_review" },
			{ label: "Overdue", value: "overdue" },
			{ label: "Hold", value: "hold" },
		],
		default: "",
		change() {
			refresh_tasks(page);
		}
	});
}

/*
Determines which employee ID to use as default for filters.
Returns blank for Administrator, otherwise returns current session user.
*/

function get_employee_id() {
	return frappe.session.user === "Administrator" ? "" : frappe.session.user;
}

/*
Fetches and displays filtered task data based on selected filters.
Called whenever a filter field changes or the page is refreshed.
*/

function refresh_tasks(page, reset_page = false) {
	if (reset_page) page.current_page = 1;

	page.body.find(".frappe-list, .pagination-container").remove();

	const selected_status = page.fields_dict.status.get_value();
	const task_name = page.fields_dict.task.get_value();
	const project_name = page.fields_dict.project.get_value();
	const customer_name = page.fields_dict.customer.get_value();
	const department = page.fields_dict.department.get_value();
	const sub_category = page.fields_dict.compliance_sub_category.get_value();
	const employee = page.fields_dict.employee.get_value();
	const employee_group = page.fields_dict.employee_group.get_value();
	const from_date = page.fields_dict.from_date.get_value();
	const to_date = page.fields_dict.to_date.get_value();

	frappe.call({
		method: "one_compliance.one_compliance.page.task_management_tool.task_management_tool.get_task",
		args: {
			status: selected_status,
			task: task_name,
			project: project_name,
			customer: customer_name,
			department,
			sub_category,
			employee,
			employee_group,
			from_date,
			to_date,
			page: page.current_page,
			page_length: page.page_length
		},
		callback: (r) => {
			if (r.message && r.message.tasks.length > 0) {
				render_task_list(page, r.message.tasks);
				setup_pagination(page, r.message.total_tasks);
				setup_page_length_buttons(page);
				initialize_task_actions(page);
			} else {
				show_no_task_found(page);
			}
		},
		freeze: true,
		freeze_message: "Loading Task List"
	});
}

/**
Refreshes and reloads the task list manually based on provided filters and updates UI interactions.
*/

function refresh_tasks_manually(page, selected_status, task_name, project_name, customer_name, department, sub_category, employee, employee_group, from_date, to_date) {
	page.body.find(".frappe-list").remove();

	frappe.call({
		method: "one_compliance.one_compliance.page.task_management_tool.task_management_tool.get_task",
		args: {
			status: selected_status,
			task: task_name,
			project: project_name,
			customer: customer_name,
			department,
			sub_category,
			employee,
			employee_group,
			from_date,
			to_date
		},
		callback: (r) => {
			if (r.message && r.message.length > 0) {
				render_task_list(page, r.message);
				initialize_task_actions(page);
			} else {
				show_no_task_found(page);
			}
		},
		freeze: true,
		freeze_message: "Loading Task List"
	});
}

/**
Renders task list into the page
*/

function render_task_list(page, tasks) {
	$(frappe.render_template("task_management_tool", { task_list: tasks })).appendTo(page.body);
}

/**
Handles all task-related button bindings and UI updates
*/

function initialize_task_actions(page) {
	const body = page.body;

	body.find(".paymentEntryButton").off().on("click", function () {
		const task_id = $(this).attr("task-id");
		const payable_amount = $(this).attr("payable-amount");
		const mode_of_Payment = $(this).attr("mode-of-payment");
		const reference_number = $(this).attr("ref-num");
		const reference_date = $(this).attr("ref-date");
		const user_remark = $(this).attr("remark");
		payment_entry_dialog(task_id, payable_amount, mode_of_Payment, reference_number, reference_date, user_remark);
	});

	body.find(".addAssigneeBtn").off().on("click", function () {
		const task_name = $(this).attr("task-id");
		show_assign_entry_dialog(task_name);
	});

	body.find(".timeEntryButton").hide();

	body.find(".startButton").off().on("click", function () {
		const task_name = $(this).attr("task-id");
		const project_name = $(this).attr("project-id");
		const status = page.fields_dict.status.get_value();

		if (["completed", "hold", "cancelled"].includes(status)) return;

		const current_time = frappe.datetime.now_datetime();
		const formatted_time = frappe.datetime.str_to_user(current_time);
		localStorage.setItem(`start-time-task-${task_name}-project-${project_name}`, current_time);

		body.find(`.start-time[task-id='${task_name}'][project-id='${project_name}']`).text(formatted_time);
		update_task_status(page, task_name, project_name, "Working");

		$(this).hide();
		body.find(`.timeEntryButton[task-id='${task_name}'][project-id='${project_name}']`).show();
	});

	body.find(".start-time").each(function () {
		const task_name = $(this).attr("task-id");
		const project_name = $(this).attr("project-id");
		let start_time = localStorage.getItem(`start-time-task-${task_name}-project-${project_name}`);

		if (start_time) {
			const stored_date = new Date(start_time);
			const current_date = new Date();

			if (
				stored_date.getDate() !== current_date.getDate() ||
				stored_date.getMonth() !== current_date.getMonth() ||
				stored_date.getFullYear() !== current_date.getFullYear()
			) {
				localStorage.removeItem(`start-time-task-${task_name}-project-${project_name}`);
				start_time = null;
			}
		}

		if (start_time) {
			const formatted_time = frappe.datetime.str_to_user(start_time);
			$(this).text(formatted_time);
			body.find(`.startButton[task-id='${task_name}'][project-id='${project_name}']`).hide();
			body.find(`.timeEntryButton[task-id='${task_name}'][project-id='${project_name}']`).show();
		} else {
			$(this).text("");
			body.find(`.startButton[task-id='${task_name}'][project-id='${project_name}']`).show();
			body.find(`.timeEntryButton[task-id='${task_name}'][project-id='${project_name}']`).hide();
		}
	});

	body.find(".timeEntryButton").off().on("click", function () {
		const task_name = $(this).attr("task-id");
		const project_name = $(this).attr("project-id");
		const assignees = $(this).attr("assignees");
		const start_time = localStorage.getItem(`start-time-task-${task_name}-project-${project_name}`);
		frappe.db.get_value("Task", task_name, "has_external_dependencies")
		.then(({ message }) => {
			const show_lag = !!message?.has_external_dependencies;

			show_time_entry_dialog(
			page,
			task_name,
			project_name,
			assignees,
			start_time,
			show_lag
			);
		});

	});

	body.find(".documentButton").off().on("click", function () {
		const sub_category = $(this).attr("sub-category");
		const customer = $(this).attr("customer");
		customer_documents(sub_category, customer);
	});

	body.find(".credentialButton").off().on("click", function () {
		const sub_category = $(this).attr("sub-category");
		const customer = $(this).attr("customer");
		customer_credentials(sub_category, customer);
	});

	set_status_colors(page);
	hide_add_assignee_button(page.fields_dict.status.get_value());
	assignee_and_completed_by_section(page.fields_dict.status.get_value());
	hide_start_button_without_assignees(page);
}

/**
Displays message when no tasks found
*/

function show_no_task_found(page) {
	$('<div class="frappe-list"></div>')
		.appendTo(page.body)
		.append(
			'<div class="no-result text-muted flex justify-center align-center" style="text-align: center;"><p>No Task found with matching filters.</p></div>'
		);
}

/*
Sets up pagination controls (Previous, Next, and Page Info)
inside the #pagination-container element.
*/

function setup_pagination(page, total_tasks) {
	const container = page.body.find("#pagination-container");
	container.empty();

	const total_pages = Math.ceil(total_tasks / page.page_length);

	if (total_pages > 1) {
		const pagination_controls = $('<div class="pagination-controls"></div>');
		const prev_btn = $('<button class="btn btn-default">Previous</button>');
		const next_btn = $('<button class="btn btn-default">Next</button>');
		const info_text = $(`<span style="margin: 0 15px;">Page ${page.current_page} of ${total_pages}</span>`);

		if (page.current_page === 1) prev_btn.prop('disabled', true);
		if (page.current_page === total_pages) next_btn.prop('disabled', true);

		prev_btn.on('click', () => {
			page.current_page--;
			refresh_tasks(page);
		});

		next_btn.on('click', () => {
			page.current_page++;
			refresh_tasks(page);
		});

		pagination_controls.append(prev_btn, info_text, next_btn);
		container.append(pagination_controls);
	}
}

/*
Sets up page length selector buttons (20, 50, 500, 2500, etc.)
that allow users to control how many items are shown per page
*/

function setup_page_length_buttons(page) {
	$(".page-length-btn").removeClass("active");
	$(`.page-length-btn[data-length="${page.page_length}"]`).addClass("active");
	$(".page-length-btn").off("click").on("click", function () {
		$(".page-length-btn").removeClass("active");
		$(this).addClass("active");

		page.page_length = parseInt($(this).attr("data-length"));
		page.current_page = 1;
		refresh_tasks(page, true);
	});
}

/**
Hides the add assignee button if the task is completed, on hold, or cancelled.
@param {string} taskStatus - The status of the task.
*/
function hide_add_assignee_button(taskStatus) {
	if (taskStatus === 'completed' || taskStatus === 'hold' || taskStatus === 'cancelled') {
				$('.startButton').hide();
		$('.addAssigneeBtn').hide();
	} else {
		$('.addAssigneeBtn').show();
	}
}

/**
Toggles the visibility of the "Assignee" and "Completed By" sections
based on the current task status.
*/

function assignee_and_completed_by_section(taskStatus) {
	if (taskStatus === 'completed') {
		$('.assignee-section').hide();
	} else {
		$('.completed-by-section').hide();
	if (taskStatus === 'completed') {
		$('.assignee-section').hide();
	} else {
		$('.completed-by-section').hide();
	}
}
}

// Function to get frappe.session.user in the employee field to filter the task
function get_employee(assigneesList, callback) {
	if (frappe.session.user === 'Administrator') {
			return assigneesList[0]
	}
}

/**
Opens a dialog for adding or updating payment information related to a specific task.
*/

function payment_entry_dialog(task_id, payable_amount, mode_of_payment, reference_number, reference_date, user_remark) {
	const dialog = new frappe.ui.Dialog({
		title: __("Add Payment Info"),
		fields: [
			{
				label: __("Task"),
				fieldname: "task",
				fieldtype: "Link",
				options: "Task",
				default: task_id,
				read_only: 1,
			},
			{
				label: __("Payable Amount"),
				fieldname: "payable_amount",
				fieldtype: "Currency",
				reqd: 1,
				default: payable_amount,
			},
			{
				label: __("Mode of Payment"),
				fieldname: "mode_of_payment",
				fieldtype: "Link",
				options: "Mode of Payment",
				reqd: 1,
				default: mode_of_payment,
			},
			{ fieldtype: "Column Break" },
			{
				label: __("Reference Number"),
				fieldname: "reference_number",
				fieldtype: "Data",
				default: reference_number,
			},
			{
				label: __("Reference Date"),
				fieldname: "reference_date",
				fieldtype: "Date",
				default: reference_date,
			},
			{
				label: __("User Remark"),
				fieldname: "user_remark",
				fieldtype: "Small Text",
				default: user_remark,
			},
		],
		primary_action_label: __("Save"),
		primary_action(values) {
			frappe.call({
				method: "one_compliance.one_compliance.page.task_management_tool.task_management_tool.add_payment_info",
				args: {
					task_id,
					payable_amount: values.payable_amount,
					mode_of_payment: values.mode_of_payment,
					reference_number: values.reference_number,
					reference_date: values.reference_date,
					user_remark: values.user_remark,
				},
				callback: function (r) {
					frappe.msgprint("Payment info added successfully!");
					frm.reload_doc();
				},
				error: (r) => frappe.msgprint(__("Error adding payment info: {0}", [r.message || "Unknown error"])),
			});
			dialog.hide();

		},
	});
	dialog.show();
}

/**
Opens a dialog to assign one or more employees (users) to a specific task.
*/

function show_assign_entry_dialog(task_name) {
	const dialog = new frappe.ui.Dialog({
		title: __("Add Employees"),
		fields: [
			{
				label: __("Assign To"),
				fieldname: "assign_to",
				fieldtype: "MultiSelectPills",
				get_data(txt) {
					return frappe.db.get_link_options("User", txt, {
						user_type: "System User",
						enabled: 1,
					});
				},
			},
		],
		primary_action_label: __("Add"),
		primary_action(values) {
			frappe.call({
				method: "frappe.desk.form.assign_to.add",
				args: { doctype: "Task", name: task_name, assign_to: values.assign_to },
				callback() {
					frappe.msgprint(__("Assignment added successfully!"));
					location.reload();
				},
				error: (r) => frappe.msgprint(__("Error adding assignment: {0}", [r.message || "Unknown error"])),
			});
			dialog.hide();
		},
	});
	dialog.show();
}

/**
Shows a dialog for time entry linked to a specific task.
*/

function show_time_entry_dialog(page, task_name, project_name, assignees, start_time, show_lag_time_fields) {
	const status = page.fields_dict.status.get_value();
	if (["completed", "hold", "cancelled"].includes(status)) return;

	const assignees_list = assignees ? assignees.split(",") : [];
	const from_time = start_time;
	const to_time = frappe.datetime.now_datetime();

	const dialog = new frappe.ui.Dialog({
		title: __("Time Entry"),
		fields: [
			{
				label: __("Employee"),
				fieldname: "employee",
				fieldtype: "Select",
				options: assignees_list,
			},
			{
				label: __("Project"),
				fieldname: "project",
				fieldtype: "Link",
				options: "Project",
				default: project_name,
			},
			{
				label: __("From Time"),
				fieldname: "from_time",
				fieldtype: "Datetime",
				reqd: 1,
				read_only: 1,
				default: from_time,
			},
			{ fieldtype: "Column Break" },
			{
				label: __("Task"),
				fieldname: "task",
				fieldtype: "Link",
				options: "Task",
				default: task_name,
			},
			{
				label: __("Activity"),
				fieldname: "activity",
				fieldtype: "Link",
				options: "Activity Type",
				reqd: 1,
			},
			{
				label: __("To Time"),
				fieldname: "to_time",
				fieldtype: "Datetime",
				reqd: 1,
				read_only: 1,
				default: to_time,
			},
			{
				label: __("Lag Time"),
				fieldname: "lag_time",
				fieldtype: 'Duration',
				hidden: !show_lag_time_fields
			},
			{
				label: __("Reason for Lag Time"),
				fieldname: "reason_for_lag_time",
				fieldtype: 'Small Text',
				hidden: !show_lag_time_fields
			}
		],
		primary_action_label: __("Submit"),
		primary_action(values) {
			localStorage.removeItem(`start-time-task-${task_name}-project-${project_name}`);
			frappe.call({
				method: "one_compliance.one_compliance.page.task_management_tool.task_management_tool.create_timesheet",
				args: values,
				callback() {
					frappe.msgprint(__("Timesheet created successfully!"));
					page.body.find(`.start-time[task-id='${task_name}'][project-id='${project_name}']`).hide();
					page.body.find(`.startButton[task-id='${task_name}'][project-id='${project_name}']`).show();
					page.body.find(`.timeEntryButton[task-id='${task_name}'][project-id='${project_name}']`).hide();
					dialog.hide();
				},
				error: (r) => frappe.msgprint(__("Error creating timesheet: {0}", [r.message || "Unknown error"])),
			});
		},
	});

	get_employee(assignees_list, (emp) => emp && dialog.set_value("employee", emp));
	dialog.show();
}

/**
Fetches the employee name for the current logged-in user.
*/

function get_employee(assignees_list, callback) {
	if (frappe.session.user === "Administrator") {
		callback(assignees_list[0]);
		return;
	}

	frappe.db.get_value("Employee", { user_id: frappe.session.user }, "employee_name")
		.then((r) => {
			console.log("Employee fetched:", r.message?.employee_name);
			callback(r.message?.employee_name || null);
		})
		.catch((err) => {
			console.error("Error fetching employee:", err);
			callback(null);
		});
}

/**
Applies color styling and interactive icons to task cards based on their status.
*/

function set_status_colors(page) {
	page.body.find(".card.task-entry").each(function () {
		const task_el = $(this);
		const status_el = task_el.find("[status-span]");
		const status = status_el.attr("status-span");
		const project_el = task_el.find(".card-subtitle");
		const project_color = project_el.attr("color");

		const color_map = {
			"Open": "blue",
			"Completed": "green",
			"Overdue": "red",
			"Working": "tomato",
			"Pending Review": "orange",
			"Hold": "gray",
		};

		const color = color_map[status] || project_color;
		status_el.css("color", color);
		project_el.css("color", color);

		if (["Open", "Overdue", "Working", "Pending Review", "Hold"].includes(status)) add_check_icon(status_el[0]);
	});

	function add_check_icon(element) {
		if (element.querySelector(".fa-check-circle")) return;
		const icon = document.createElement("i");
		icon.className = "fas fa-check-circle";
		icon.style.color = "green";
		icon.style.cursor = "pointer";
		icon.title = __("Update Status");

		element.append(" ", icon);

		icon.addEventListener("click", () => {
			const task_name = element.getAttribute("task-name");
			const task_id = element.getAttribute("task-id");
			const project_id = element.getAttribute("project-id");
			update_status(page, task_name, project_id, task_id);
		});
	}
}

/**
Opens a dialog displaying a customer's document details for a specific compliance sub-category.
*/

function customer_documents(sub_category, customer) {
	frappe.call({
		method: "one_compliance.one_compliance.utils.view_customer_documents",
		args: { customer, compliance_sub_category: sub_category },
		callback(r) {
			if (r.message?.length) {
				const d = new frappe.ui.Dialog({
					title: __("Document Details"),
					fields: [
						{
							label: __("Document Attachment"),
							fieldname: "document_attachment",
							fieldtype: "Data",
							read_only: 1,
							default: r.message[0],
						},
					],
					primary_action_label: __("Download"),
					primary_action() {
						window.open(r.message[0]);
					},
				});
				d.show();
			}
		},
	});
}

/**
Displays and retrieves customer credential details for a specific compliance sub-category.
*/

function customer_credentials(sub_category, customer) {
	const dialog = new frappe.ui.Dialog({
		title: __("Enter Details"),
		fields: [
			{
				label: 'Purpose',
				fieldname: 'purpose',
				fieldtype: 'Link',
				options: 'Credential Type',
				reqd: 1,
				get_query: function () {
					return {
						filters: {
							'compliance_sub_category': sub_category
						}
					};
				}
			}
		],
		primary_action_label: 'View Credential',
		primary_action(values) {
			if (!values.purpose) {
				frappe.msgprint(__('Please select a Purpose before viewing credentials.'));
				return;
			}
			frappe.call({
				method: 'one_compliance.one_compliance.utils.view_credential_details',
				args: {
					'customer': customer,
					'purpose': values.purpose
				},
				callback(r) {
					if (r.message?.length >= 3) {
						dialog.hide();
						const details = new frappe.ui.Dialog({
							title: __("Credential Details"),
							fields: [
								{ label: __("Username"), fieldname: "username", fieldtype: "Data", read_only: 1, default: r.message[0] },
								{ label: __("Password"), fieldname: "password", fieldtype: "Data", read_only: 1, default: r.message[1] },
								{ label: __("URL"), fieldname: "url", fieldtype: "Data", read_only: 1, default: r.message[2] },
							],
							primary_action_label: __("Close"),
							primary_action() { details.hide(); },
							secondary_action_label: __("Go To URL"),
							secondary_action() { window.open(r.message[2]); },
						});
						details.show();
					}
				},
			});
		},
	});
	dialog.show();
}

/**
Opens a dialog to update the status of a specific task and refreshes the task list upon completion.
*/

function update_status(page, task_name, project_id, task_id) {
	const dialog = new frappe.ui.Dialog({
		title: __("Update Task Status"),
		fields: [
			{
				label: __("Status"),
				fieldname: "status",
				fieldtype: "Select",
				options: "Open\nWorking\nPending Review\nHold\nCompleted",
				default: "Completed",
			},
			{
				label: __("Completed By"),
				fieldname: "completed_by",
				fieldtype: "Link",
				options: "User",
				default: frappe.session.user,
			},
			{
				label: __("Completed On"),
				fieldname: "completed_on",
				fieldtype: "Date",
				default: frappe.datetime.get_today(),
			},
		],
		primary_action_label: __("Update"),
		primary_action(values) {
			frappe.call({
				method: "one_compliance.one_compliance.doc_events.task.update_task_status",
				args: { task_id, ...values },
				callback(r) {
					if (r.message) {
						dialog.hide();
						refresh_tasks(page);
					}
				},
			});
		},
	});
	dialog.show();
}

/**
Updates the task status to "Working" when start time is clicked.
*/

function update_task_status(page, task_name, project_name, status) {
	frappe.call({
		method: "one_compliance.one_compliance.page.task_management_tool.task_management_tool.update_task_status",
		args: { task: task_name, project: project_name, status },
		callback(r) {
			if (r.message === "success") {
                refresh_tasks(page); 
			} else {
				console.warn("Failed to update task status");
			}
		},
	});
}

/**
Hide start buttons if no assignees are set OR if task already has a start time.
*/

function hide_start_button_without_assignees(page) {
	if (!page || !page.body) return;

	page.body.find(".startButton").each(function () {
		const $btn = $(this);
		let assignees = $btn.attr("assignees") || "";
		const task_id = $btn.attr("task-id");
		const project_id = $btn.attr("project-id");

		assignees = assignees.replace(/\s+/g, "").trim();

		const start_time_key = "start-time-task-" + task_id + "-project-" + project_id;
		const start_time = localStorage.getItem(start_time_key);

		if (!assignees || start_time) {
			$btn.hide();
		} else {
			$btn.show();
		}
	});
}
