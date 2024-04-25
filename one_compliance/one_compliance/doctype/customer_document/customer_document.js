// Copyright (c) 2023, efeone and contributors
// For license information, please see license.txt

frappe.ui.form.on('Customer Document', {
	refresh: function(frm) {
    frm.add_custom_button('Customer Tool Page', function() {
        var customer = frm.doc.customer;
        localStorage.setItem('selected_customer', customer);
        // Replace 'tool-page-url' with the actual URL of the Customer document tool page
        window.location.href = '/app/customer-document-tool';
    });
	}
});
