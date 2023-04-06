frappe.ui.form.on('Department',{
  setup: function(frm) {
    //filter the compliance sub category based on compliance category
    frm.set_query('head_of_department', () => {
            return {
                filters: {
                      status : 'Active'
                }
            }
        })
    }
});
