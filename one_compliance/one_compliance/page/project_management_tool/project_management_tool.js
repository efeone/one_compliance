frappe.pages['project-management_tool'].on_page_load = function (wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Project Management Tool',
		single_column: true
	});

	// Button to refresh the page
	let $button = page.set_secondary_action('Refresh', () => location.reload())

	page.add_button(__('Add Event'), function () {
		const current_time = frappe.datetime.now_datetime();
		frappe.call({
			method: "one_compliance.one_compliance.page.task_management_tool.task_management_tool.start_active_timer",
			args: {
				task: "EVENT-" + frappe.session.user,
				project: "",
				subject: "Event Tracking",
				start_time: current_time
			},
			callback: (r) => {
				if (r.message) {
					const user = frappe.session.user;
					if (user) {
						localStorage.setItem('one-compliance-active-timer-' + user, JSON.stringify(r.message));
					}
					frappe.show_alert({
						message: __("Event tracking started. Go to Task Management Tool to stop it."),
						indicator: "orange"
					});
					toggle_add_event_button(page);
					$(document).trigger('one-compliance-timer-changed', [r.message]);
				}
			}
		});
	});

	page.main.addClass("frappe-card");

	make_filters(page);
	// Initialize pagination
	page.current_page = 1;
	page.page_length = 20;

	refresh_projects(page);
	toggle_add_event_button(page);

}

frappe.pages['project-management_tool'].on_page_show = function (wrapper) {
	var page = wrapper.page;
	toggle_add_event_button(page);
}

/**
 * Toggles the visibility of the "Add Event" button based on active event timers.
 * Uses localStorage for instant feedback.
 */
function toggle_add_event_button(page) {
	const user = frappe.session.user;
	const active_timers = JSON.parse(localStorage.getItem('one-compliance-active-timer-' + user) || '[]');
	const event_timer = active_timers.find(t => t.task && t.task.startsWith("EVENT-"));
	const $btn = page.wrapper.find('.page-actions button:contains("Add Event")');
	
	if (event_timer) {
		$btn.hide();
	} else {
		$btn.show();
	}
}

/*
Creates filter fields on the page and binds change events to refresh the project list.
*/
function make_filters(page) {
	// Define all filters except Status
	const filters = [
		{ label: "Project", fieldname: "project", options: "Project" },
		{ label: "Customer", fieldname: "customer", options: "Customer" },
		{
			label: "Employee",
			fieldname: "employee",
			options: "User",
			default: get_employee_id(),
			read_only: frappe.session.user === 'Administrator' ? 0 : 1
		},
		{ label: "Department", fieldname: "department", options: "Department" },
		{ label: "Compliance Sub Category", fieldname: "compliance_sub_category", options: "Compliance Sub Category" },
		{ label: "From Date", fieldname: "from_date", fieldtype: "Date" },
		{ label: "To Date", fieldname: "to_date", fieldtype: "Date" }
	];

	// Helper function for refresh
	const bind_refresh = (fieldname) => {
		let field = page.fields_dict[fieldname];
		field.$input.on('change', function () {
			refresh_projects(page);
		});
	};

	// Create fields dynamically
	filters.forEach(f => {
		page.add_field({
			label: __(f.label),
			fieldname: f.fieldname,
			fieldtype: f.fieldtype || "Link",
			options: f.options,
			default: f.default || undefined,
			read_only: f.read_only || 0,
			change() {
				if (page.fields_dict[f.fieldname].get_value()) {
					refresh_projects(page);
				}
			}
		});
		bind_refresh(f.fieldname);
	});

	// Add Status filter separately (Select field)
	page.add_field({
		label: __("Status"),
		fieldname: "status",
		fieldtype: "Select",
		options: [
			{},
			{ label: "Open", value: "open" },
			{ label: "Invoiced", value: "invoiced" },
			{ label: "Paid", value: "paid" },
			{ label: "Overdue", value: "overdue" },
			{ label: "Hold", value: "hold" },
			{ label: "Completed", value: "completed" },
			{ label: "Cancelled", value: "cancelled" },
		],
		default: "",
		change() {
			refresh_projects(page);
		}
	});
}

/*
 Returns the current user's Employee ID, or an empty string if user is Administrator.
*/
function get_employee_id() {
	if (frappe.session.user === 'Administrator') {
		return '';
	}
	else {
		return frappe.session.user
	}
}

/*
 Clear existing projects from the page
*/
function refresh_projects(page, page_num = null) {
	// Handle page number
	if (page_num) {
		page.current_page = page_num;
	} else {
		page.current_page = page.current_page || 1;
	}

	// Clear existing project list and pagination controls
	page.body.find(".frappe-list").remove();

	const selected_status = page.fields_dict.status.get_value();
	const project_name = page.fields_dict.project.get_value();
	const customer_name = page.fields_dict.customer.get_value();
	const department = page.fields_dict.department.get_value();
	const sub_category = page.fields_dict.compliance_sub_category.get_value();
	const employee = page.fields_dict.employee.get_value();
	const from_date = page.fields_dict.from_date.get_value();
	const to_date = page.fields_dict.to_date.get_value();

	frappe.call({
		method: "one_compliance.one_compliance.page.project_management_tool.project_management_tool.get_project",
		args: {
			status: selected_status,
			project: project_name,
			customer: customer_name,
			department: department,
			sub_category: sub_category,
			employee: employee,
			from_date: from_date,
			to_date: to_date,
			page: page.current_page,
			page_length: page.page_length
		},
		callback: (r) => {
			if (r.message && r.message.length > 0) {
				$(frappe.render_template("project_management_tool", { project_list: r.message })).appendTo(page.body);

				// Action to redirect to the task management tool 
				page.body.find(".showTask").on("click", function () {
					var project_id = $(this).attr("project");
										
					// Set route options before navigation
					frappe.route_options = {
						project: project_id
					};					
					// Navigate to the task management tool page
					frappe.set_route('task-management-tool');
				});

				// Attach pagination controls and page-length button logic
				render_pagination_controls(page, r.message.length);
				setup_page_length_buttons(page);
			} else {
				// If no projects are found, append a message to the page body
				$('<div class="frappe-list"></div>').appendTo(page.body)
					.append('<div class="no-result text-muted flex justify-center align-center" style="text-align: center;"><p>No Project found with matching filters.</p></div>');
			}
		},
		freeze: true,
		freeze_message: 'Loading Project'
	});
}

/*
Renders pagination controls (Previous, Next, and Page Info) inside #pagination-container.
*/
function render_pagination_controls(page, result_count) {
	const container = $("#pagination-container");
	container.empty();

	const prev_btn = $('<button class="page-btn btn btn-default btn-sm me-2">Previous</button>');
	const next_btn = $('<button class="page-btn btn btn-default btn-sm">Next</button>');
	const info_text = $(`<span style="margin: 0 10px;">Page ${page.current_page}</span>`);

	// Disable logic
	if (page.current_page === 1) prev_btn.prop('disabled', true);
	if (result_count < page.page_length) next_btn.prop('disabled', true);

	// Events
	prev_btn.on('click', () => refresh_projects(page, page.current_page - 1));
	next_btn.on('click', () => refresh_projects(page, page.current_page + 1));

	container.append(prev_btn, info_text, next_btn);
}

/*
Sets up event listeners for page length buttons to change the number of items displayed per page.
*/
function setup_page_length_buttons(page) {
	$(".page-length-btn").removeClass("active");

	$(`.page-length-btn[data-length="${page.page_length}"]`).addClass("active");

	$(".page-length-btn").off('click').on('click', function () {
		$(".page-length-btn").removeClass("active");
		$(this).addClass("active");
		page.page_length = parseInt($(this).attr("data-length"));
		page.current_page = 1;
		refresh_projects(page);
	});
}


