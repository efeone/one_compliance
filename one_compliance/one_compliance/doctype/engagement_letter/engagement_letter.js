// Copyright (c) 2023, efeone and contributors
// For license information, please see license.txt

frappe.ui.form.on('Engagement Letter', {
	// refresh: function(frm) {

	// }
	customer_type: function(frm) {
		console.log("Customer Type:", frm.doc.customer_type);
		console.log("Lead:", frm.doc.lead);
		console.log("Opportunity:", frm.doc.opportunity);
		if (frm.doc.customer_type === 'Lead' && frm.doc.lead) {
			frappe.call({
				method: 'frappe.client.get_value',
				args: {
					doctype: 'Lead',
					filters: { name: frm.doc.lead },
					fieldname: 'lead_name'
				},
				callback: function(response) {
					if (response.message) {
						frm.set_value('full_name', response.message.lead_name);
					}
				}
			});
		} else if (frm.doc.customer_type === 'Opportunity' && frm.doc.opportunity) {
			frappe.call({
				method: 'frappe.client.get_value',
				args: {
					doctype: 'Opportunity',
					filters: { name: frm.doc.opportunity },
					fieldname: 'contact_person'
				},
				callback: function(response) {
					if (response.message) {
						frm.set_value('full_name', response.message.contact_person);
					}
				}
			});
		}
	}
});
