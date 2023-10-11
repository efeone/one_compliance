frappe.ui.form.on('Department',{
  setup: function(frm) {
    //filter the active employee in head_of_department
    frm.set_query('head_of_department', () => {
            return {
                filters: {
                      status : 'Active'
                }
            }
        })
    },
    refresh: function(frm) {
        if(frm.is_new()){
            frm.set_value('is_compliance',1)
        }
    }
});
