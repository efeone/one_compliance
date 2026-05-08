frappe.ui.form.on('Opportunity',{
    onload: function(frm) {
        fetch_documents_from_settings(frm);
    },
	refresh: function(frm) {
		if(!frm.is_new()){
			setTimeout(() => {
				frm.remove_custom_button('Supplier Quotation','Create')
				frm.remove_custom_button('Request For Quotation','Create')
			})
			frm.add_custom_button(__('Engagement Letter'), function () {
				frm.trigger("make_engagement_letter");
			},__("Create"));

			frm.add_custom_button('Create Event',() =>{
				create_event(frm)
			});
			make_buttons(frm);
            add_agreement_button(frm);
		}
	},
	make_engagement_letter: function (frm) {
		frappe.model.open_mapped_doc({
			method: 'one_compliance.one_compliance.doc_events.oppotunity.make_engagement_letter',
			frm: cur_frm
		});
	},
    compliance_category(frm) {
        fetch_compliance_sub_categories(frm);
    },
});

function create_event(frm) {
	let d = new frappe.ui.Dialog({
		title: 'Enter details',
		fields: [
			{
				label: 'Event Category',
				fieldname: 'event_category',
				fieldtype: 'Select',
				options: "Events\nMeeting\nCall\nSent/Received Email\nOther",
				default: 'Meeting'
			},
			{
				fieldtype: "Column Break",
				fieldname: "col_break_1",
			},
			{
				label: 'Date',
				fieldname: 'start_on',
				fieldtype: 'Datetime',
				reqd: 1,
			},
			{
				fieldtype: "Section Break",
			},
			{
				label: 'Subject',
				fieldname: 'subject',
				fieldtype: 'Data',
				reqd: 1,
			},
			{
				label: 'Attendees',
				fieldname: 'attendees',
				fieldtype: 'Table',
				fields: [
					{
						label: 'Attendee Type',
						fieldname: 'attendee_type',
						fieldtype: 'Select',
						in_list_view: 1,
						options: ['Customer', 'Employee', 'Lead'],
						onchange: function(row) {
							let attendees = d.get_value('attendees');
							// Iterate over each attendee object in the array
							for (let i = 0; i < attendees.length; i++) {
								let attendeeType = attendees[i].attendee_type;
							}
						}
					},
					{
						label: 'Attendee',
						fieldname: 'attendee',
						fieldtype: 'Link',
						options: function() {
							let attendees = d.get_value('attendees');
							let options = " ";

							for (let i = 0; i < attendees.length; i++) {
								let attendeeType = attendees[i].attendee_type;

								if (attendeeType === "Customer") {
									options = "Customer";
								} else if (attendeeType === "Employee") {
									options = "Employee";
								} else if (attendeeType === "Lead") {
									options = "Lead";
								}
							}
							return options;
						},
						in_list_view: 1,
					},
				],
			}
		],
		primary_action_label: 'Create',
		primary_action(values) {
			frappe.call({
				method: 'one_compliance.one_compliance.doc_events.oppotunity.create_event_from_opportunity',
				args: {
					oppotunity:frm.doc.name,
					event_category: values.event_category,
					start_on: values.start_on,
					subject: values.subject,
					attendees: values.attendees
				},
				callback: function (r) {
					if (r.message) {
						frappe.msgprint('Event created successfully');
						d.hide();
					}
				}
			});
		}
	});
	d.show();
}


function make_buttons(frm){
	if (!frm.is_new() && frm.doc.status !== 'Converted') {
		let msg = 'System will create a Customer and Sales Order. Proceed?';
		if (frm.doc.opportunity_from === 'Customer') {
			msg = 'System will create a Sales Order. Proceed?';
		}

		frm.add_custom_button('Sales Order', () => {
			if (!frm.doc.items.length) {
				frm.scroll_to_field('items');
				frappe.throw({
					message: __("Please fill the `Services` before creating Sales Order."),
					title: __("Missing fields")
				});
			}

			frappe.confirm(msg, () => {
				frappe.call({
					method: 'one_compliance.one_compliance.doc_events.oppotunity.create_sales_order',
					args: { opportunity: frm.doc.name },
					callback: (r) => {
						if (!r.exc) {
							const d = r.message;
							frappe.model.with_doctype('Sales Order', () => {
								const doc = frappe.model.get_new_doc('Sales Order');
								doc.customer = d.customer;
								doc.opportunity = frm.doc.name;
								d.items.forEach(i => {
									let row = frappe.model.add_child(doc, 'items');
									Object.assign(row, i);
								});
								frappe.set_route('Form', 'Sales Order', doc.name);
							});
						}
					}
				});
			});
		}, 'Create');
	}
}

frappe.ui.form.on('Opportunity Item', {
	item_code(frm, cdt, cdn) {
		fetch_item_compliance(frm, cdt, cdn);
	}
});

/*
 * Fetches compliance details for an item and updates the corresponding fields
 * in the Opportunity Item child table.
*/
function fetch_item_compliance(frm, cdt, cdn) {
	let row = locals[cdt][cdn];

	if (!row.item_code) return;

	frappe.call({
		method: 'one_compliance.one_compliance.doc_events.oppotunity.get_item_compliance',
		args: { item_code: row.item_code },
		callback: function(r) {
			if (r.message) {
				frappe.model.set_value(cdt, cdn, 'compliance_category', r.message.compliance_category);
				frappe.model.set_value(cdt, cdn, 'compliance_sub_category', r.message.compliance_sub_category);
			}
		}
	});
}



function fetch_documents_from_settings(frm) {
	if (!frm.is_new()) {
		return;
	}
	frappe.call({
		method: "one_compliance.one_compliance.doctype.compliance_settings.compliance_settings.get_documents_template",
		callback: function (r) {

			if (!r.message || !r.message.length) return;

			frm.clear_table("custom_documents_required");

			r.message.forEach(row => {
				let d = frm.add_child("custom_documents_required");
				d.document_required = row.document_name;
			});

			frm.refresh_field("custom_documents_required");
		}
	});
}

/**
 * Create compliance agreement from opportunity
 */
function add_agreement_button(frm) {
	frappe.db.get_single_value("Compliance Settings", "create_agreement_from_opportunity").then(value => {
		if (value) {
			frm.add_custom_button(
				__("Agreement"),
				() => {
					open_service_dialog(frm);
				},
				__("Create")
			);
		}
	});
}

/**
 * Show popup to create compliance agreement from opportunity
 */
function open_service_dialog(frm) {

	let d = new frappe.ui.Dialog({
		title: __("Create Agreement"),
		size: "extra-large",
		fields: [
			{ fieldtype: "HTML", fieldname: "services_html" }
		],
		primary_action_label: __("Create Agreement"),
		primary_action() {

			let selected_items = [];
			let compliance_categories = [];

			d.$wrapper.find(".service-check:checked").each(function () {
				let row = frm.doc.items[$(this).data("idx")];
				selected_items.push(row);

				if (row.compliance_category) {
					compliance_categories.push(row.compliance_category);
				}
			});

			if (!selected_items.length) {
				frappe.msgprint(__("Please select at least one service"));
				return;
			}

			compliance_categories = [...new Set(compliance_categories)];
			frappe.new_doc("Compliance Agreement");

			frappe.after_ajax(() => {

				let agreement_frm = cur_frm;
				agreement_frm.doc.opportunity_name = frm.doc.name;
				agreement_frm.refresh_field("opportunity_name");
				if (frm.doc.enquiry_from === "Existing Client") {
					agreement_frm.doc.customer = frm.doc.party_name;
					agreement_frm.refresh_field("customer");

				} else if (frm.doc.enquiry_from === "New Client") {
					frappe.call({
						method: "one_compliance.one_compliance.doc_events.oppotunity.create_customer_from_opportunity",
						args: {
							opportunity: frm.doc.name
						},
						callback: function (r) {
							if (r.message) {
								agreement_frm.doc.customer = r.message;
								agreement_frm.refresh_field("customer");
							}
						}
					});
				}
				agreement_frm.clear_table("compliance_category");

				compliance_categories.forEach(cat => {
					let row = agreement_frm.add_child("compliance_category");
					row.compliance_category = cat;
				});

				agreement_frm.refresh_field("compliance_category");
				selected_items.forEach(item => {
					let child = agreement_frm.add_child("compliance_category_details");
					child.compliance_category = item.compliance_category;
					child.compliance_sub_category = item.compliance_sub_category;
					child.rate = item.rate;
				});

				agreement_frm.refresh_field("compliance_category_details");
			});

			d.hide();
		}
	});

	d.show();
	let html = `
	<table class="table table-bordered table-hover">
	<thead>
	<tr>
		<th><input type="checkbox" id="select_all_services"></th>
		<th>Service</th>
		<th>Compliance Category</th>
		<th>Sub Category</th>
		<th>Qty</th>
		<th>Rate</th>
		<th>Amount</th>
	</tr>
	</thead><tbody>
	`;

	(frm.doc.items || []).forEach((row, i) => {
		html += `
		<tr>
			<td><input type="checkbox" class="service-check" data-idx="${i}"></td>
			<td>${row.item_name || ""}</td>
			<td>${row.compliance_category || ""}</td>
			<td>${row.compliance_sub_category || ""}</td>
			<td>${row.qty || 0}</td>
			<td>${row.rate || 0}</td>
			<td>${row.amount || 0}</td>
		</tr>`;
	});

	html += `</tbody></table>`;
	d.fields_dict.services_html.$wrapper.html(html);

	d.$wrapper.find("#select_all_services").on("change", function () {
		d.$wrapper.find(".service-check").prop("checked", $(this).is(":checked"));
	});
}


/**
 * Fetch compliance sub categories from the selected compliance categories
 */
function fetch_compliance_sub_categories(frm){
	if (frm.doc.compliance_category.length) {
		frm.clear_table('items')
		frm.doc.compliance_category.forEach(compliance_category => {
			frappe.call('one_compliance.one_compliance.doc_events.oppotunity.get_compliance_sub_category_list', {
				compliance_category: compliance_category.compliance_category
			}).then(r => {
				if (r.message) {
					r.message.forEach(row => {
						let d = frm.add_child('items');
						d.compliance_sub_category = row.name;
                        d.compliance_category = compliance_category.compliance_category;
                        d.item_code = row.item_code;
					});
					frm.refresh_field('items');
				}
			})
		});
		frm.refresh_field('items');
	}
}