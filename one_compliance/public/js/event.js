frappe.ui.form.on('Event',{
    refresh: function(frm) {
      frm.add_custom_button(
        __("Add Employees"),
        function () {
          new frappe.desk.eventParticipants(frm, "Employee");
        },
      );
      frm.add_custom_button(
        __("Create Proforma Invoice"),
        function () {
          if(frm.doc.custom_is_billable == 1){
            create_sales_order(frm)
          }
          else{
            frappe.msgprint('Please Mark this Event as Billable');
          }
        },
      );
      frm.add_custom_button(
        __("Employee Timsheet"),
        function () {
          if(frm.doc.status =='Completed' && frm.doc.starts_on && frm.doc.ends_on){
            //create time for employees
            make_time_sheet_enrty(frm)
          }
          else{
            frappe.msgprint('Not valid');
          }
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
    status:function(frm){
      if(frm.doc.status =='Completed' && frm.doc.starts_on && frm.doc.ends_on){
        //create time for employees
        make_time_sheet_enrty(frm)
      }
    }
});

let create_sales_order = function (frm) {
  frappe.call({
    method: 'one_compliance.one_compliance.doc_events.sales_order.create_sales_order_from_event',
    args: {
      'event':frm.doc.name,
      'customer': frm.doc.custom_customer,
      'sub_category': frm.doc.custom_service,
      'rate': frm.doc.custom_rate,
      'description': frm.doc.custom_service_description
    },
    callback: function(r){
      if (r.message){
        frm.reload_doc();
      }
    }
  })
}

let make_time_sheet_enrty = function (frm) {
  frappe.call({
    method: 'one_compliance.one_compliance.utils.make_time_sheet_enrty',
    args: {
      'event':frm.doc.name
    },
    callback: function(r){
      if (r.message){
        frm.reload_doc();
      }
    }
  })
}
frappe.ui.form.on('Event Participants', {
    reference_docname: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (row.reference_doctype === 'Employee') {
            frappe.db.get_value('Employee', row.reference_docname, 'employee_name', (r) => {
                if (r && r.employee_name) {
                    frappe.model.set_value(cdt, cdn, 'custom_participant_name', r.employee_name);
                }
            });
        } else if (row.reference_doctype === 'Lead') {
            frappe.db.get_value('Lead', row.reference_docname, 'title', (r) => {
                if (r && r.title) {
                    frappe.model.set_value(cdt, cdn, 'custom_participant_name', r.title);
                }
            });
        }
    }
});
