frappe.ui.form.on('Event',{
    refresh: function(frm) {
      frm.add_custom_button(
        __("Add Employees"),
        function () {
          new frappe.desk.eventParticipants(frm, "Employee");
        },
      );
      frm.remove_custom_button("Add Employees", "Add Participants");
    }
});
