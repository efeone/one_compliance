// Copyright (c) 2023, efeone and contributors
// For license information, please see license.txt

frappe.ui.form.on('Task Bulk Assignment', {
  refresh: function (frm) {
    if (!frm.doc.assignment_based_on) {
      frm.set_value('assignment_based_on', 'Task');
    }
    frm.disable_save();
    frm.set_df_property('task_reassigns', 'cannot_delete_rows', true);
    frm.set_df_property('assign_to', 'cannot_delete_rows', true);

    frm.set_df_property('task_reassigns', 'cannot_add_rows', true);
    frm.set_df_property('assign_to', 'cannot_add_rows', true);

    frm.add_custom_button('Get Allocation Entries', () => {
      get_allocation_entries(frm);
    });
    frm.change_custom_button_type('Get Allocation Entries', null, 'primary');
    if (frm.doc.task_reassigns.length || frm.doc.assign_to.length) {
      frm.add_custom_button('Allocate', () => {
        allocate_tasks_to_employee(frm);
      });
      frm.change_custom_button_type('Allocate', null, 'primary');
      frm.change_custom_button_type('Get Allocation Entries', null, 'default');
    }
  },
  setup: function (frm) {
    set_filters(frm);
  },
});

let clear_values = function (frm) {
  // clear field values
  frm.clear_table('task_reassigns');
  frm.refresh_field('task_reassigns');
  frm.clear_table('assign_to');
  frm.refresh_field('assign_to');
};

let set_filters = function (frm) {
  frm.set_query('assigned_to', function () {
    if (frm.doc.department) {
      return {
        query:
          'one_compliance.one_compliance.doctype.task_bulk_assignment.task_bulk_assignment.get_users_by_department',
        filters: {
          department: frm.doc.department,
        },
      };
    } else {
      return {};
    }
  });
  frm.set_query('sub_category', function () {
    if (frm.doc.department && frm.doc.category) {
      return {
        query:
          'one_compliance.one_compliance.doctype.task_bulk_assignment.task_bulk_assignment.get_subcategories_by_department_and_category',
        filters: {
          department: frm.doc.department,
          category: frm.doc.category,
        },
      };
    } else if (frm.doc.category) {
      return {
        query:
          'one_compliance.one_compliance.doctype.task_bulk_assignment.task_bulk_assignment.get_subcategories_by_category',
        filters: {
          category: frm.doc.category,
        },
      };
    } else if (frm.doc.department) {
      return {
        query:
          'one_compliance.one_compliance.doctype.task_bulk_assignment.task_bulk_assignment.get_subcategories_by_department',
        filters: {
          department: frm.doc.department,
        },
      };
    } else {
      return {};
    }
  });
  frm.set_query('category', function () {
    if (frm.doc.department) {
      return {
        query:
          'one_compliance.one_compliance.doctype.task_bulk_assignment.task_bulk_assignment.get_categories_by_department',
        filters: {
          department: frm.doc.department,
        },
      };
    } else {
      return {};
    }
  });
};

function get_allocation_entries(frm) {
  frappe.call({
    doc: frm.doc,
    method: 'get_allocation_entries',
    callback: (r) => {
      if (r.message === 'success') {
        frm.refresh();
      } else {
        frappe.msgprint('Error retrieving data');
      }
    },
  });
}

function allocate_tasks_to_employee(frm) {
  const assignment_handlers = {
    task: {
      selector: 'task_reassigns',
      method: 'allocate_tasks_to_employee',
      success_message: 'Tasks allocated successfully.',
      error_message: 'Error: Unable to allocate tasks.',
    },
    project: {
      selector: 'project_reassigns',
      method: 'allocate_projects_to_employee',
      success_message: 'Projects allocated successfully.',
      error_message: 'Error: Unable to allocate Projects.',
    },
  };

  const handler =
    assignment_handlers[frm.doc.assignment_based_on.toLowerCase()];

  if (!handler) {
    frappe.msgprint('Invalid assignment type.');
    return;
  }

  const selected_items =
    frm.fields_dict[handler.selector].grid.get_selected_children();

  if (selected_items.length === 0) {
    frappe.msgprint(
      `Please select ${frm.doc.assignment_based_on}s to allocate.`
    );
    return;
  }

  const selected_employees =
    frm.fields_dict.assign_to.grid.get_selected_children();

  if (selected_employees.length === 0) {
    frappe.msgprint('Please select employees to whom tasks will be allocated.');
    return;
  }

  const selected_ids = selected_items.map(
    (item) => item[frm.doc.assignment_based_on.toLowerCase()]
  );
  const selected_employee_ids = selected_employees.map(
    (employee) => employee.employee
  );

  frappe.call({
    method: `one_compliance.one_compliance.doctype.task_bulk_assignment.task_bulk_assignment.${handler.method}`,
    args: {
      selected_ids: selected_ids,
      selected_employee_ids: selected_employee_ids,
    },
    freeze: true,
    freeze_message: `Allocating ${frm.doc.assignment_based_on}s...`,
    callback: function (r) {
      if (r.message === handler.success_message) {
        frappe.msgprint(handler.success_message);
        frm.reload_doc();
      } else {
        frappe.msgprint(handler.error_message);
      }
    },
  });
}
