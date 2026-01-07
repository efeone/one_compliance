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
			frm.set_df_property("custom_task_document_items", "read_only", 0);
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
								compliance_sub_category: frm.doc.compliance_sub_category,
							},
						};
					},
				},
			],
			primary_action_label: "View Credential",
			primary_action(values) {
				frappe.call({
					method: "one_compliance.one_compliance.utils.view_credential_details",
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
										fieldame: "password",
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
					method: "one_compliance.one_compliance.utils.view_customer_documents",
					args: {
						customer: customer,
						compliance_sub_category: values.compliance_sub_category,
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
				options: "Open\nWorking\nPending Review\nCompleted\nHold",
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
	if (!frm.doc.checklist_template || frm.doc.status === 'Completed' || frm.doc.status === 'Cancelled' || frm.doc.status === 'Hold') {
		return;
	}

	// Add button to the form (standalone, not under Actions)
	frm.add_custom_button(__('Open Checklist'), function() {
		// Fetch the checklist template
		frappe.call({
			method: 'frappe.client.get',
			args: {
				doctype: 'Task Checklist Template',
				name: frm.doc.checklist_template
			},
			callback: function(r) {
				if (r.message) {
					show_checklist_popup(frm, r.message);
				}
			}
		});
	});
}

function show_checklist_popup(frm, template) {
	// Get existing checklist items from the task or create from template
	let checklist_items = [];
	
	if (frm.doc.task_checklist_template && frm.doc.task_checklist_template.length > 0) {
		// Use existing checklist items from the task
		checklist_items = frm.doc.task_checklist_template.map((item, index) => ({
			checklist_item: item.checklist_item,
			completed: item.completed || 0,
			idx: item.idx || (index + 1)
		}));
	} else {
		// Create from template (first time)
		checklist_items = template.checklist.map((item, index) => ({
			checklist_item: item.checklist_item,
			completed: 0,
			idx: item.idx || (index + 1)
		}));
	}

	let checklist_html = generate_checklist_html(checklist_items, template.template_name);

	let checklist_popup = new frappe.ui.Dialog({
		title: __('Task Checklist'),
		fields: [
			{
				fieldname: 'checklist_html',
				fieldtype: 'HTML',
			}
		],
		primary_action_label: __('Save & Close'),
		primary_action: function() {
			save_checklist(frm, checklist_items, checklist_popup);
		},
		secondary_action_label: __('Cancel'),
		size: 'large'
	});

	checklist_popup.fields_dict.checklist_html.$wrapper.html(checklist_html);

	// Add event listeners for checkboxes
	checklist_popup.fields_dict.checklist_html.$wrapper.find('.checklist-checkbox').on('change', function() {
		let idx = parseInt($(this).data('idx'));
		let is_checked = $(this).is(':checked');
		
		// Update the checklist_items array
		let item = checklist_items.find(i => i.idx === idx);
		if (item) {
			item.completed = is_checked ? 1 : 0;
		}

		// Update the visual state
		let label = $(this).siblings('label');
		let itemDiv = $(this).closest('.checklist-item');
		
		if (is_checked) {
			itemDiv.addClass('completed');
			label.css({
				'text-decoration': 'line-through',
				'color': '#888'
			});
			// Add checkmark animation
			itemDiv.css('transform', 'scale(0.98)');
			setTimeout(() => itemDiv.css('transform', 'scale(1)'), 200);
		} else {
			itemDiv.removeClass('completed');
			label.css({
				'text-decoration': 'none',
				'color': '#495057'
			});
		}

		// Update progress
		update_progress(checklist_popup, checklist_items);
	});

	// Add click event for labels to toggle checkbox
	checklist_popup.fields_dict.checklist_html.$wrapper.find('.checklist-item label').on('click', function(e) {
		e.preventDefault();
		let idx = parseInt($(this).data('idx'));
		let checkbox = checklist_popup.fields_dict.checklist_html.$wrapper.find(`.checklist-checkbox[data-idx="${idx}"]`);
		checkbox.prop('checked', !checkbox.prop('checked')).trigger('change');
	});

	update_progress(checklist_popup, checklist_items);
	checklist_popup.show();
}

function generate_checklist_html(items, template_name) {
	let completed_count = items.filter(i => i.completed === 1).length;
	let total = items.length;
	let percentage = total > 0 ? Math.round((completed_count / total) * 100) : 0;

	let html = `
		<div class="checklist-container" style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
			<div class="template-header" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 8px; margin-bottom: 24px; color: white;">
				<div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px;">
					<h3 style="margin: 0; font-size: 18px; font-weight: 600;">${frappe.utils.escape_html(template_name)}</h3>
					<span style="background: rgba(255,255,255,0.2); padding: 4px 12px; border-radius: 12px; font-size: 13px; font-weight: 500;">
						${completed_count}/${total} Tasks
					</span>
				</div>
				<div class="progress" style="height: 8px; background: rgba(255,255,255,0.2); border-radius: 4px; overflow: hidden;">
					<div class="progress-bar" role="progressbar" 
						 style="width: ${percentage}%; height: 100%; background: rgba(255,255,255,0.9); transition: width 0.3s ease;" 
						 aria-valuenow="${percentage}" aria-valuemin="0" aria-valuemax="100">
					</div>
				</div>
				<div style="margin-top: 8px; font-size: 13px; opacity: 0.9;">
					<span class="progress-percentage">${percentage}%</span> Complete
				</div>
			</div>
			
			<div class="checklist-items" style="max-height: 400px; overflow-y: auto;">
	`;

	items.forEach((item, index) => {
		let checked = item.completed ? 'checked' : '';
		let completed_class = item.completed ? 'completed' : '';
		let text_style = item.completed ? 'text-decoration: line-through; color: #888;' : 'color: #495057;';
		
		html += `
			<div class="checklist-item ${completed_class}" 
				 style="padding: 16px; 
						margin-bottom: 8px; 
						border: 2px solid ${item.completed ? '#d4edda' : '#e9ecef'}; 
						border-radius: 8px; 
						display: flex; 
						align-items: center; 
						background: ${item.completed ? '#f0f8f0' : 'white'};
						transition: all 0.2s ease;
						cursor: pointer;">
				<div style="display: flex; align-items: center; justify-content: center; min-width: 24px; margin-right: 12px;">
					<input type="checkbox" 
						   class="checklist-checkbox" 
						   data-idx="${item.idx}" 
						   ${checked} 
						   style="width: 20px; 
								  height: 20px; 
								  cursor: pointer; 
								  accent-color: #667eea;
								  border-radius: 4px;">
				</div>
				<label style="margin: 0; 
							  cursor: pointer; 
							  flex: 1; 
							  user-select: none; 
							  font-size: 15px;
							  font-weight: 500;
							  ${text_style}
							  transition: all 0.2s ease;" 
					   data-idx="${item.idx}">
					${frappe.utils.escape_html(item.checklist_item)}
				</label>
				${item.completed ? '<span style="color: #28a745; font-size: 18px; margin-left: 8px;">✓</span>' : ''}
			</div>
		`;
	});

	html += `
			</div>
		</div>
		<style>
			.checklist-item:hover {
				border-color: #667eea !important;
				box-shadow: 0 2px 8px rgba(102, 126, 234, 0.15);
				transform: translateY(-1px);
			}
			
			.checklist-item.completed:hover {
				border-color: #28a745 !important;
			}
			
			.checklist-items::-webkit-scrollbar {
				width: 8px;
			}
			
			.checklist-items::-webkit-scrollbar-track {
				background: #f1f1f1;
				border-radius: 4px;
			}
			
			.checklist-items::-webkit-scrollbar-thumb {
				background: #888;
				border-radius: 4px;
			}
			
			.checklist-items::-webkit-scrollbar-thumb:hover {
				background: #555;
			}
		</style>
	`;

	return html;
}

function update_progress(dialog, items) {
	let completed = items.filter(i => i.completed === 1).length;
	let total = items.length;
	let percentage = total > 0 ? Math.round((completed / total) * 100) : 0;

	dialog.$wrapper.find('.progress-bar').css('width', percentage + '%').attr('aria-valuenow', percentage);
	dialog.$wrapper.find('.progress-percentage').text(percentage + '%');
	dialog.$wrapper.find('.template-header span').text(`${completed}/${total} Tasks`);
}

function save_checklist(frm, checklist_items, dialog) {
	// Clear existing checklist items
	frm.clear_table('task_checklist_template');

	// Add updated checklist items
	checklist_items.forEach(item => {
		let row = frm.add_child('task_checklist_template');
		row.checklist_item = item.checklist_item;
		row.completed = item.completed;
        row.completed_on = item.completed ? frappe.datetime.now_date() : null;
        row.completed_by = item.completed ? frappe.session.user : null;
		row.idx = item.idx;
	});

	// Refresh the table
	frm.refresh_field('task_checklist_template');

	// Check if all items are completed
	let all_completed = checklist_items.every(item => item.completed === 1);
	
	if (all_completed && frm.doc.status !== 'Completed') {
		frappe.show_alert({
			message: __('🎉 All checklist items completed! Task marked as complete.'),
			indicator: 'green'
		}, 5);
		frm.set_value('status', 'Completed');
		// Set completed_on to current date
		frm.set_value('completed_on', frappe.datetime.now_date());
	}

	// Save the document
	frm.save().then(() => {
		frappe.show_alert({
			message: __('✓ Checklist saved successfully'),
			indicator: 'green'
		}, 3);
		dialog.hide();
	});
}
