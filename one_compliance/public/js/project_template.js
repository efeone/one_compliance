
frappe.ui.form.on('Project Template', {

  setup: function(frm) {
    //filter the compliance sub category based on compliance category
    frm.set_query('compliance_sub_category', () => {
            return {
                filters: {
                    compliance_category : frm.doc.compliance_category
                }
            }
        })
    }
});
