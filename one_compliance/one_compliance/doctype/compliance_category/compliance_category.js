// Copyright (c) 2023, efeone and contributors
// For license information, please see license.txt

frappe.ui.form.on('Compliance Category', {
	setup: (frm) => {
		set_filters(frm);
	},
	refresh: (frm) => {
		add_sub_category_button(frm);
	},
	department: (frm) => {
		fetch_and_set_compliance_executives(frm);
	}
});

/**
 * Adds a custom button 'Add Sub Category' to create a new Sub Category linked to the current Compliance Category
 */
function add_sub_category_button(frm) {
	if(!frm.is_new() && frm.doc.compliance_category){
	  frm.add_custom_button('Add Sub Category', ()=>{
		frappe.model.open_mapped_doc({
		  method : 'one_compliance.one_compliance.doctype.compliance_category.compliance_category.custom_button_for_sub_category',
		  source_name: frm.doc.name
		});
	  });
	}
}

/**
 * Fetch and set compliance executives based on department
 */
function fetch_and_set_compliance_executives(frm) {
	if (!frm.doc.department) return;

	frappe.call({
		method: 'one_compliance.one_compliance.doctype.compliance_category.compliance_category.fetch_employees',
		args: { department: frm.doc.department },
		callback: r => {
			const executives = r.message;
			if (!executives || !executives.length) return;

			frm.clear_table('compliance_executive');
			executives.forEach(exec => {
				frm.add_child('compliance_executive', {
					employee: exec.name,
					employee_name: exec.employee_name,
					designation: exec.designation
				});
			});
			frm.refresh_field('compliance_executive');
		}
	});
}

/*
 * Set filters for fields in Compliance Category form
 */
function set_filters(frm) {
	frm.set_query('head_of_department', () => ({
		filters: {
			department: frm.doc.department,
			designation: 'Head Of Department'
		}
	}));

	frm.set_query('employee', 'compliance_executive', () => ({
		filters: {
			status: 'Active'
		}
	}));

	frm.set_query('department', () => ({
		filters: {
			is_compliance: 1
		}
	}));
}
