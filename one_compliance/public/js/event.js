frappe.ui.form.on('Event',{
    refresh: function(frm) {
      frm.add_custom_button(
        __("Add Employees"),
        function () {
          new frappe.desk.eventParticipants(frm, "Employee");
        },
      );
      frm.remove_custom_button("Add Employees", "Add Participants");
    },
    setup: function(frm) {
      //filter 
      frm.set_query('custom_service', () => {
              return {
                  filters: {
                    is_meeting_only : true
                  }
              }
          })
      },
});
