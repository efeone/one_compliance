// Copyright (c) 2024, efeone and contributors
// For license information, please see license.txt

frappe.ui.form.on('Project Name Year Type', {
	
reference_docname: function (frm) {
        frappe.call({
            method: 'one_compliance.one_compliance.doctype.project_name_year_type.project_name_year_type.get_reference_doctype',
            args: {
                reference_doctype: frm.doc.reference_doctype,
                reference_docname: frm.doc.reference_docname
            },
            callback: function (r) {
                if (r.message) {
                    // Access the fetched document using r.message
                    var doc = r.message;
                    // Perform actions based on the fetched document
                    frm.set_value('from_date', doc.from_date);
                    frm.set_value('to_date', doc.to_date);
                }
            }
        });
    }
});
