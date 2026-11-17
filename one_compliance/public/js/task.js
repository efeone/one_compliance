frappe.ui.form.on("Task", {
	refresh(frm) {
		let roles = frappe.user_roles;
		let current_user = frappe.session.user;

		// Call a custom method to check permission
		frappe.call({
			method:
				"one_compliance.one_compliance.doc_events.task.check_readiness_edit_permission",
			args: {
				user: current_user,
			},
			callback: function (r) {
				if (r.message === true) {
					frm.set_df_property("readiness_status", "read_only", 0);
				} else {
					frm.set_df_property("readiness_status", "read_only", 1);
				}
			},
		});

		if (roles.includes("Compliance Manager") || roles.includes("Director")) {
			if (!frm.is_new() && frm.doc.is_template == 0) {
				frm.add_custom_button("View Credential", () => {
					customer_credentials(frm);
				});

				frm.add_custom_button("View Document", () => {
					customer_document(frm);
				});
			}
		}

		if (!frm.is_new()) {
			frm.add_custom_button("Status Update", () => {
				update_status(frm);
			});
		}

		if (frm.doc.custom_task_document_items) {
			frm.set_df_property(
				"custom_task_document_items",
				"read_only",
				0
			);
		}

		if (frm.doc.project) {
			frm.set_df_property("is_group", "hidden", 1);
			frm.set_df_property("is_template", "hidden", 1);
		}

		handle_task_checklist(frm);
	},
});

let customer_credentials = function (frm) {
	frappe.db.get_value("Project", frm.doc.project, "customer").then((r) => {
		let customer = r.message.customer;

		let d = new frappe.ui.Dialog({
			title: "Enter details",
			fields: [
				{
					label: "Purpose",
					fieldname: "purpose",
					fieldtype: "Link",
					options: "Credential Type",
					get_query: function () {
						return {
							filters: {
								compliance_sub_category:
									frm.doc.compliance_sub_category,
							},
						};
					},
				},
			],

			primary_action_label: "View Credential",

			primary_action(values) {
				frappe.call({
					method:
						"one_compliance.one_compliance.utils.view_credential_details",

					args: {
						customer: customer,
						purpose: values.purpose,
					},

					callback: function (r) {
						if (r.message) {
							d.hide();

							let newd = new frappe.ui.Dialog({
								title: "Credential details",

								fields: [
									{
										label: "Username",
										fieldname: "username",
										fieldtype: "Data",
										read_only: 1,
										default: r.message[0],
									},
									{
										label: "Password",
										fieldname: "password",
										fieldtype: "Data",
										read_only: 1,
										default: r.message[1],
									},
									{
										label: "Url",
										fieldname: "url",
										fieldtype: "Data",
										options: "URL",
										read_only: 1,
										default: r.message[2],
									},
								],

								primary_action_label: "Close",

								primary_action(value) {
									newd.hide();
								},

								secondary_action_label: "Go To URL",

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
	});
};

let customer_document = function (frm) {
	frappe.db.get_value("Project", frm.doc.project, "customer").then((r) => {
		let customer = r.message.customer;

		let d = new frappe.ui.Dialog({
			title: "Enter details",

			fields: [
				{
					label: "Compliance Sub Category",
					fieldname: "compliance_sub_category",
					fieldtype: "Link",
					options: "Compliance Sub Category",
				},
			],

			primary_action_label: "View Document",

			primary_action(values) {
				frappe.call({
					method:
						"one_compliance.one_compliance.utils.view_customer_documents",

					args: {
						customer: customer,
						compliance_sub_category:
							values.compliance_sub_category,
					},

					callback: function (r) {
						if (r.message) {
							d.hide();

							let newd = new frappe.ui.Dialog({
								title: "Document details",

								fields: [
									{
										label: "Document Attachment",
										fieldname: "document_attachment",
										fieldtype: "Data",
										read_only: 1,
										default: r.message[0],
									},
								],

								primary_action_label: "Close",

								primary_action(value) {
									newd.hide();
								},

								secondary_action_label: "Download",

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
	});
};

let update_status = function (frm) {
	let d = new frappe.ui.Dialog({
		title: "Enter details",

		fields: [
			{
				label: "Status",
				fieldname: "status",
				fieldtype: "Select",
				options:
					"Open\nWorking\nPending Review\nCompleted\nHold",
				default: "Completed",
			},
			{
				label: "Completed By",
				fieldname: "completed_by",
				fieldtype: "Link",
				options: "User",
			},
			{
				label: "Completed On",
				fieldname: "completed_on",
				fieldtype: "Date",
				default: "Today",
			},
			{
				label: "Comment",
				fieldname: "comment",
				fieldtype: "Small Text",
			},
		],

		primary_action_label: "Update",

		primary_action(values) {
			frappe.call({
				method:
					"one_compliance.one_compliance.doc_events.task.update_task_status",

				args: {
					task_id: frm.doc.name,
					status: values.status,
					completed_by: values.completed_by,
					completed_on: values.completed_on,
					comment: values.comment,
				},

				callback: function (r) {
					if (r.message) {
						d.hide();
						frm.reload_doc();
					}
				},
			});
		},
	});

	d.set_value("completed_by", frappe.session.user);
	d.show();
};

function handle_task_checklist(frm) {
	if (
		!frm.doc.checklist_template ||
		frm.doc.status === "Completed" ||
		frm.doc.status === "Cancelled" ||
		frm.doc.status === "Hold"
	) {
		return;
	}

	frm.add_custom_button(__("Open Checklist"), function () {
		frappe.call({
			method: "frappe.client.get",

			args: {
				doctype: "Task Checklist Template",
				name: frm.doc.checklist_template,
			},

			callback: function (r) {
				if (r.message) {
					show_checklist_popup(frm, r.message);
				}
			},
		});
	});
}

function show_checklist_popup(frm, template) {
	let checklist_items = [];

	if (
		frm.doc.task_checklist_template &&
		frm.doc.task_checklist_template.length > 0
	) {
		checklist_items = frm.doc.task_checklist_template.map(
			(item, index) => ({
				checklist_item: item.checklist_item,
				completed: item.completed || 0,
				idx: item.idx || index + 1,
			})
		);
	} else {
		checklist_items = template.checklist.map((item, index) => ({
			checklist_item: item.checklist_item,
			completed: 0,
			idx: item.idx || index + 1,
		}));
	}

	let checklist_html = generate_checklist_html(
		checklist_items,
		template.template_name
	);

	let checklist_popup = new frappe.ui.Dialog({
		title: __("Task Checklist"),

		fields: [
			{
				fieldname: "checklist_html",
				fieldtype: "HTML",
			},
		],

		primary_action_label: __("Save & Close"),

		primary_action: function () {
			save_checklist(frm, checklist_items, checklist_popup);
		},

		secondary_action_label: __("Cancel"),
		size: "large",
	});

	checklist_popup.fields_dict.checklist_html.$wrapper.html(
		checklist_html
	);

	checklist_popup.fields_dict.checklist_html.$wrapper
		.find(".checklist-checkbox")
		.on("change", function () {
			let idx = parseInt($(this).data("idx"));
			let is_checked = $(this).is(":checked");

			let item = checklist_items.find((i) => i.idx === idx);

			if (item) {
				item.completed = is_checked ? 1 : 0;
			}

			update_progress(checklist_popup, checklist_items);
		});

	update_progress(checklist_popup, checklist_items);

	checklist_popup.show();
}

function generate_checklist_html(items, template_name) {
	let completed_count = items.filter(
		(i) => i.completed === 1
	).length;

	let total = items.length;

	let percentage =
		total > 0
			? Math.round((completed_count / total) * 100)
			: 0;

	let html = `
		<div>
			<h3>${template_name}</h3>

			<div class="progress" style="margin-bottom:15px;">
				<div class="progress-bar"
					style="width:${percentage}%;">
					${percentage}%
				</div>
			</div>
	`;

	items.forEach((item) => {
		html += `
			<div style="margin-bottom:10px;">
				<input type="checkbox"
					class="checklist-checkbox"
					data-idx="${item.idx}"
					${item.completed ? "checked" : ""}>

				<label>
					${item.checklist_item}
				</label>
			</div>
		`;
	});

	html += `</div>`;

	return html;
}

function update_progress(dialog, items) {
	let completed = items.filter(
		(i) => i.completed === 1
	).length;

	let total = items.length;

	let percentage =
		total > 0
			? Math.round((completed / total) * 100)
			: 0;

	dialog.$wrapper
		.find(".progress-bar")
		.css("width", percentage + "%")
		.text(percentage + "%");
}

function save_checklist(frm, checklist_items, dialog) {
	frm.clear_table("task_checklist_template");

	checklist_items.forEach((item) => {
		let row = frm.add_child("task_checklist_template");

		row.checklist_item = item.checklist_item;
		row.completed = item.completed;
		row.completed_on = item.completed
			? frappe.datetime.now_date()
			: null;

		row.completed_by = item.completed
			? frappe.session.user
			: null;

		row.idx = item.idx;
	});

	frm.refresh_field("task_checklist_template");

	let all_completed = checklist_items.every(
		(item) => item.completed === 1
	);

	if (all_completed && frm.doc.status !== "Completed") {
		frappe.show_alert(
			{
				message: __(
					"🎉 All checklist items completed! Task marked as complete."
				),
				indicator: "green",
			},
			5
		);

		frm.set_value("status", "Completed");

		frm.set_value(
			"completed_on",
			frappe.datetime.now_date()
		);
	}

	frm.save().then(() => {
		frappe.show_alert(
			{
				message: __("✓ Checklist saved successfully"),
				indicator: "green",
			},
			3
		);

		dialog.hide();
	});
}