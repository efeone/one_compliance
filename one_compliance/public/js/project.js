frappe.ui.form.on('Project', {

	onload(frm) {
		load_project_tasks(frm);
	},

	refresh(frm) {
	if (!frm.is_new()) {
		setTimeout(() => {
		frm.remove_custom_button('Duplicate Project with Tasks', 'Actions');
		frm.remove_custom_button('Set Project Status', 'Actions');
		});
	}

	let roles = frappe.user_roles;
	if (roles.includes('Compliance Manager') || roles.includes('Director')) {
		if (!frm.is_new()) {
		frm.add_custom_button(
			'Customer Credentials',
			() => {
			customer_credentials(frm);
			},
			__('View')
		);
		frm.add_custom_button(
			'Customer Documents',
			() => {
			customer_documents(frm);
			},
			__('View')
		);
		}
	}

	if (!frm.is_new()) {
		frm.add_custom_button('Set Project Status', () => {
		update_project_status(frm);
		});
	}
	// Add 'Convert to Premium' button on existing Project
	if (!frm.is_new() && !frm.doc.is_premium) {
		frappe.db
		.get_value(
			'Compliance Sub Category',
			frm.doc.compliance_sub_category,
			'premium_task'
		)
		.then((value) => {
			if (value.message && value.message.premium_task) {
			frm.add_custom_button(__('Convert to Premium'), function () {
				frappe.call({
				method:
					'one_compliance.one_compliance.doc_events.project.convert_project_to_premium',
				args: {
					project: frm.doc.name,
				},
				callback: function (r) {
					if (r.message === 'success') {
					frappe.msgprint(
						__('Project converted to Premium successfully.')
					);
					frm.reload_doc();
					} else {
					frappe.msgprint(
						__('Failed to convert project to Premium.')
					);
					}
				},
				});
			});
			}
		});

		// Add 'Create Tasks' button if no tasks exist
		frappe.db
		.count('Task', {
			filters: { project: frm.doc.name },
		})
		.then(function (count) {
			if (count === 0) {
			frm.add_custom_button(
				__('Create Tasks'),
				function () {
				frappe.call({
					method:
					'one_compliance.one_compliance.doc_events.project.create_tasks_from_template',
					args: { project: frm.doc.name },
					callback: function (r) {
					if (!r.exc) {
						frappe.msgprint(
						__('Tasks created from Project Template')
						);
						frm.reload_doc();
					}
					},
				});
				},
				__('Actions')
			);
			}
		});
	}

	load_project_tasks(frm);
	},
});

let set_status = function (frm, status, comment) {
	frappe.confirm(
	__('Set Project and all Tasks to status {0}?', [status.bold()]),
	() => {
		frappe
		.xcall(
			'one_compliance.one_compliance.doc_events.project.set_project_status',
			{ project: frm.doc.name, status: status, comment: comment }
		)
		.then(() => {
			frm.reload_doc();
		});
	}
	);
};

let update_project_status = function (frm) {
	let d = new frappe.ui.Dialog({
	title: 'Set Project Status',
	fields: [
		{
		fieldname: 'status',
		fieldtype: 'Select',
		label: 'Status',
		reqd: 1,
		options: '\nOpen\nHold\nCompleted\nCancelled',
		},
		{
		fieldname: 'comment',
		fieldtype: 'Small Text',
		label: 'Comment',
		depends_on: 'eval:doc.status == "Hold"',
		mandatory_depends_on: 'eval:doc.status == "Hold"',
		},
	],
	size: 'small',
	primary_action: function () {
		set_status(frm, d.get_values().status, d.get_values().comment);
		d.hide();
	},
	primary_action_label: __('Set Project Status'),
	});

	d.show();
};

/* applied dialog instance to show customer Credential */
let customer_credentials = function (frm) {
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
				compliance_sub_category: frm.doc.compliance_sub_category,
			},
			};
		},
		},
	],
	primary_action_label: 'View Credential',
	primary_action(values) {
		frappe.call({
		method: 'one_compliance.one_compliance.utils.view_credential_details',
		args: {
			customer: frm.doc.customer,
			purpose: values.purpose,
		},
		callback: function (r) {
			if (r.message) {
			d.hide();
			let newd = new frappe.ui.Dialog({
				title: 'Credential details',
				fields: [
				{
					label: 'Username',
					fieldname: 'username',
					fieldtype: 'Data',
					read_only: 1,
					default: r.message[0],
				},
				{
					label: 'Password',
					fieldame: 'password',
					fieldtype: 'Data',
					read_only: 1,
					default: r.message[1],
				},
				{
					label: 'Url',
					fieldname: 'url',
					fieldtype: 'Data',
					options: 'URL',
					read_only: 1,
					default: r.message[2],
				},
				],
				primary_action_label: 'Close',
				primary_action(value) {
				newd.hide();
				},
				secondary_action_label: 'Go To URL',
				secondary_action(value) {
				window.open(r.message[2]);
				},
			});
			newd.show();
			}
		},
		});
	},
	});
	d.show();
};

/* applied dialog instance to show customer document */
let customer_documents = function (frm) {
	let d = new frappe.ui.Dialog({
	title: 'Enter details',
	fields: [
		{
		label: 'Compliance Sub Category',
		fieldname: 'compliance_sub_category',
		fieldtype: 'Link',
		options: 'Compliance Sub Category',
		},
	],
	primary_action_label: 'View Document',
	primary_action(values) {
		frappe.call({
		method: 'one_compliance.one_compliance.utils.view_customer_documents',
		args: {
			customer: frm.doc.customer,
			compliance_sub_category: values.compliance_sub_category,
		},
		callback: function (r) {
			if (r.message) {
			d.hide();
			let newd = new frappe.ui.Dialog({
				title: 'Document details',
				fields: [
				{
					label: 'Document Attachment',
					fieldname: 'document_attachment',
					fieldtype: 'Data',
					read_only: 1,
					default: r.message[0],
				},
				],
				primary_action_label: 'Close',
				primary_action(value) {
				newd.hide();
				},
				secondary_action_label: 'Download',
				secondary_action(value) {
				window.open(r.message[0]);
				},
			});
			newd.show();
			}
		},
		});
	},
	});
	d.show();
};

/**
 * Load Project Tasks and display in HTML field
 */
function load_project_tasks(frm) {
	frappe.call({
		method: 'one_compliance.one_compliance.doc_events.project.get_project_tasks',
		args: {
			project: frm.doc.name
		},
		callback: function (r) {
			if (!r.message || !r.message.tasks || r.message.tasks.length === 0 || !r.message.show) {
				frm.set_df_property('project_dashboard_html', 'hidden', 1);
				return;
			}
			
			const html = generate_task_dashboard(r.message.tasks);
			frm.set_df_property('project_dashboard_html', 'options', html);
		},
		error: function(r) {
			frappe.show_alert({
				message: __('Failed to load project tasks'),
				indicator: 'red'
			});
			frm.set_df_property('project_dashboard_html', 'options', '');
		}
	});
}

function generate_task_dashboard(tasks) {
	const task_rows = tasks.map(task => generate_task_row(task)).join('');
	
	return `
		<div class="project-task-dashboard">
			<h5>Task Status</h5>
			<div class="task-table-wrapper">
				<table class="table table-bordered table-sm" style="width: 100%; margin-bottom: 0;">
					<thead>
						<tr>
							<th style="width: 15%">Task ID</th>
							<th style="width: 40%">Subject</th>
							<th style="width: 15%">Status</th>
							<th style="width: 15%">Completed By</th>
							<th style="width: 15%">Completed On</th>
						</tr>
					</thead>
					<tbody>
						${task_rows}
					</tbody>
				</table>
			</div>
		</div>
		${get_table_styles()}
	`;
}

function generate_task_row(task) {
	const is_completed = task.status === 'Completed';
	const status_class = is_completed ? 'green' : 'blue';
	
	// Escape HTML to prevent XSS
	const escaped_name = frappe.utils.escape_html(task.name || '');
	const escaped_subject = frappe.utils.escape_html(task.subject || '');
	const escaped_status = frappe.utils.escape_html(task.status || '');
	
	// Generate user link with full name
	const completed_by_html = is_completed && task.completed_by 
		? generate_user_link(task.completed_by)
		: '';
	
	const completed_date = is_completed && task.completed_on 
		? frappe.format(task.completed_on, {'fieldtype': 'Date'}) 
		: '';
	
	return `
		<tr>
			<td>
				<a href="/app/task/${encodeURIComponent(task.name)}" target="_blank">
					${escaped_name}
				</a>
			</td>
			<td>${escaped_subject}</td>
			<td>
				<span class="indicator ${status_class}">
					${escaped_status}
				</span>
			</td>
			<td>${completed_by_html}</td>
			<td>${completed_date}</td>
		</tr>
	`;
}

function generate_user_link(user_email) {
	if (!user_email) return '';

	const full_name = frappe.user_info(user_email).fullname;

	const escaped_email = frappe.utils.escape_html(user_email);
	const display_name = full_name 
		? frappe.utils.escape_html(full_name) 
		: escaped_email;
	
	return `<a href="/app/user/${encodeURIComponent(user_email)}" target="_blank">${display_name}</a>`;
}

function get_table_styles() {
	return `
		<style>
			.task-table-wrapper {
				max-height: 300px;
				overflow-y: auto;
				border: 1px solid var(--border-color);
				border-radius: 6px;
			}
			.task-table-wrapper thead th {
				position: sticky;
				top: 0;
				background: var(--card-bg);
				z-index: 1;
				box-shadow: 0 2px 2px -1px rgba(0, 0, 0, 0.1);
			}
			.task-table-wrapper tbody tr:hover {
				background-color: var(--table-hover-bg);
			}
		</style>
	`;
}
