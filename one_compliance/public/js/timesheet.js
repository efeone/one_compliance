frappe.ui.form.on('Timesheet', {
    refresh: function (frm) {
        frm.set_query('project', 'time_logs', () => {
            return {
                filters: {
                    status: ['not in', ['Completed', 'Cancelled']]
                }
            };
        });
      frm.set_query('project', () => {
          return {
            filters: {
                status: ['not in', ['Completed', 'Cancelled']]
          }
      }
  })

    }
});
