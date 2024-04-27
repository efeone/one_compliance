frappe.pages['project-management_tool'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Project Management Tool',
		single_column: true
	});

	// Button to refresh the page
	let $button = page.set_secondary_action('Refresh',() => location.reload())

	page.main.addClass("frappe-card");

	make_filters(page);

	refresh_projects(page);
}

function make_filters(page) {
	let projectField = page.add_field({
		label: __("Project"),
		fieldname: "project",
		fieldtype: "Link",
		options: "Project",
		change() {
			if (page.fields_dict.project.get_value()) {
          refresh_projects(page);
      }
		}
	});
	page.fields_dict.project.$input.on('change', function() {
		if (!page.fields_dict.project.get_value()) {
				refresh_projects(page);
		}
  });
	let customerField = page.add_field({
		label: __("Customer"),
		fieldname: "customer",
		fieldtype: "Link",
		options:"Customer",
		change() {
			if (page.fields_dict.customer.get_value()) {
          refresh_projects(page);
      }
		}
	});
	page.fields_dict.customer.$input.on('change', function() {
		if (!page.fields_dict.customer.get_value()) {
				refresh_projects(page);
		}
  });
	let employeeField = page.add_field({
		label: __("Employee"),
		fieldname: "employee",
		fieldtype: "Link",
		options: "User",
		default: get_employee_id(),
		change() {
			if (page.fields_dict.employee.get_value()) {
          refresh_projects(page);
      }
		},
		read_only: frappe.session.user === 'Administrator' ? 0 : 1
	});
	page.fields_dict.employee.$input.on('change', function() {
		if (!page.fields_dict.employee.get_value()) {
				refresh_projects(page);
		}
  });
	let categoryField = page.add_field({
		label: __("Department"),
		fieldname: "department",
		fieldtype: "Link",
		options: "Department",
		change() {
			if (page.fields_dict.department.get_value()) {
          refresh_projects(page);
      }
		}
	});
	page.fields_dict.department.$input.on('change', function() {
		if (!page.fields_dict.department.get_value()) {
				refresh_projects(page);
		}
  });
	let subcategoryField = page.add_field({
		label: __("Compliance Sub Category"),
		fieldname: "compliance_sub_category",
		fieldtype: "Link",
		options: "Compliance Sub Category",
		change() {
			if (page.fields_dict.compliance_sub_category.get_value()) {
          refresh_projects(page);
      }
		}
	});
	page.fields_dict.compliance_sub_category.$input.on('change', function() {
		if (!page.fields_dict.compliance_sub_category.get_value()) {
				refresh_projects(page);
		}
  });
	let fromDateField = page.add_field({
		label: __("From Date"),
		fieldname: "from_date",
		fieldtype: "Date"
	});
	page.fields_dict.from_date.$input.off('change').on('change', function() {
      refresh_projects(page);
  });
	let toDateField = page.add_field({
		label: __("To Date"),
		fieldname: "to_date",
		fieldtype: "Date"
	});
	page.fields_dict.to_date.$input.off('change').on('change', function() {
      refresh_projects(page);
  });
	let status = page.add_field({
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

function get_employee_id() {
    if (frappe.session.user === 'Administrator') {
        return '';
    }
		else {
				return frappe.session.user
		}
}

function refresh_projects(page){
	// Clear existing projects from the page
  page.body.find(".frappe-list").remove();

	const selectedStatus = page.fields_dict.status.get_value();
	const projectName = page.fields_dict.project.get_value();
	const customerName = page.fields_dict.customer.get_value();
	const department = page.fields_dict.department.get_value();
	const subCategory = page.fields_dict.compliance_sub_category.get_value();
	const employee = page.fields_dict.employee.get_value();
	const from_date = page.fields_dict.from_date.get_value();
	const to_date = page.fields_dict.to_date.get_value();

	frappe.call({
			method: "one_compliance.one_compliance.page.project_management_tool.project_management_tool.get_project",
			 args: { status: selectedStatus,
							 project: projectName,
							 customer: customerName,
							 department: department,
							 sub_category: subCategory,
							 employee: employee,
							 from_date: from_date,
							 to_date: to_date
							},
			 callback: (r) => {
				if (r.message && r.message.length>0) {
						$(frappe.render_template("project_management_tool", {project_list:r.message})).appendTo(page.body);

						// Action to redirect to the task management tool 
						page.body.find(".showTask").on("click", function () {
							var project_id = $(this).attr("project");
							console.log(project_id);

							// Store the selected project ID in localStorage
					    localStorage.setItem('selected_project_id', project_id);

					    // Navigate to the task management tool page
					    window.location.href = '/app/task-management-tool';
						});
				} else {
            // If no projects are found, append a message to the page body
            $('<div class="frappe-list"></div>').appendTo(page.body).append('<div class="no-result text-muted flex justify-center align-center" style="text-align: center;"><p>No Project found with matching filters.</p></div>');
        }
			},
			freeze: true,
			freeze_message: 'Loading Project'
		});

}
