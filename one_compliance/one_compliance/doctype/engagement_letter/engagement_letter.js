// Copyright (c) 2023, efeone and contributors
// For license information, please see license.txt

frappe.ui.form.on('Engagement Letter', {
	setup: function(frm) {
        // Fetch current date and time
        var currentDateTime = frappe.datetime.now_datetime();

        // Set the fetched date and time to the fields
        frm.set_value('posting_date', frappe.datetime.get_today());
  },
	lead: function(frm) {
        if (frm.doc.lead) {
            frappe.call({
                method: 'frappe.client.get_value',
                args: {
									doctype: 'Lead',
									filters: { name: frm.doc.lead },
									fieldname: ['lead_name','email_id','mobile_no']
                },
                callback: function(r) {
                    if (r.message) {
                        frm.set_value('full_name', r.message.lead_name);
												frm.set_value('email', r.message.email_id);
												frm.set_value('mobile', r.message.mobile_no);
                    }
                }
            });
        }
    },
    opportunity: function(frm) {
      if (frm.doc.opportunity) {
          frappe.call({
              method: 'frappe.client.get_value',
              args: {
								doctype: 'Opportunity',
								filters: { name: frm.doc.opportunity },
								fieldname: ['contact_person','contact_email','contact_mobile']
              },
              callback: function(r) {
                  if (r.message) {
                      frm.set_value('full_name', r.message.contact_person);
											frm.set_value('email', r.message.contact_email);
											frm.set_value('mobile', r.message.contact_mobile);
                  }
              }
          });
      }
		},
		terms: function(frm) {
        if (frm.doc.terms && !frm.doc.description) {
            frappe.call({
                method: 'one_compliance.one_compliance.doctype.engagement_letter.engagement_letter.get_terms_description',
                args: {
                    terms: frm.doc.terms
                },
                callback: function(r) {
                    if (r.message) {
                        frm.set_value('description', r.message);
                    }
                }
            });
        }
    }
});
