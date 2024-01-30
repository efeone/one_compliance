frappe.listview_settings['Task'] = {
    onload: function(listview) {
        let roles = frappe.user_roles
        listview.page.add_actions_menu_item(__("Update"), function() {
            Update(listview);
        })
    }
};

let Update = function(listview){
    let docnames = listview.get_checked_items(true);

    if (docnames.length === 0) {
        frappe.msgprint('No tasks selected.');
        return;
    }


    let Dialog = new frappe.ui.Dialog({
      title: 'Enter details',
      fields: [
        {
          label: 'Status',
          fieldname: 'status',
          fieldtype: 'Select',
          options: 'Open\nWorking\nPending Review\nCompleted\nHold',
          default: 'Completed'
        },
        {
          label: 'Completed By',
          fieldname: 'completed_by',
          fieldtype: 'Link',
          options: 'User'
        },
        {
          label: 'Completed On',
          fieldname: 'completed_on',
          fieldtype: 'Date',
          default: 'Today'
        },
      ],
      primary_action_label: 'Update',
        primary_action(values) {
            bulk_update_task_status(values, docnames, listview);
        },
    });
    Dialog.set_value('completed_by', frappe.session.user);
    Dialog.show();
};

function bulk_update_task_status(values, docnames, listview) {
  console.log(docnames);

  frappe.call({
    method: 'one_compliance.one_compliance.doc_events.task.update_task_status',
    args: {
      'task_id': docnames,
      'status': values.status,
      'completed_by': values.completed_by,
      'completed_on': values.completed_on
    },
    callback: function(r) {
      if (r.message) {
          frappe.msgprint('Tasks updated successfully.');
          listview.refresh();
          Dialog.hide();
      } 
    }
  });
}
