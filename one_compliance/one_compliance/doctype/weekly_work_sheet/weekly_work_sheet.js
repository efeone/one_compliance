// Copyright (c) 2025, efeone and contributors
// For license information, please see license.txt

// frappe.ui.form.on("Weekly Work Sheet", {
// 	refresh(frm) {

// 	},
// });
//
// frappe.ui.form.on('Weekly Work Sheet', {
//     refresh: function(frm) {
//         calculate_total_hours(frm);
//     }
// });
//
// frappe.ui.form.on('Work Log Details', {
//     actuall_hours: function(frm, cdt, cdn) {
//         // Trigger the calculation of totals as soon as the value is entered in 'actuall_hours'
//         calculate_total_hours(frm);
//     },
//     task_allowed_hours: function(frm, cdt, cdn) {
//         // Trigger the calculation of totals as soon as the value is entered in 'task_allowed_hours'
//         calculate_total_hours(frm);
//     },
//     work_log_details_remove: function(frm) {
//         // Recalculate totals when a row is removed from the child table
//         calculate_total_hours(frm);
//     }
// });
//
// function calculate_total_hours(frm) {
//     let total_actual_hours = 0;
//     let total_task_allowed_hours = 0;
//
//     // Loop through the child table rows and sum up the values for 'actuall_hours' and 'task_allowed_hours'
//     frm.doc.work_log_details.forEach(function(row) {
//         total_actual_hours += row.actuall_hours || 0;
//         total_task_allowed_hours += row.task_allowed_hours || 0;
//     });
//
//     // Set the calculated total values into the parent fields
//     frm.set_value('total_actuall_hours', total_actual_hours);
//     frm.set_value('total_task_allowed_hours', total_task_allowed_hours);
//
//     // Refresh the parent fields so that the updated values are reflected immediately
//     frm.refresh_field('total_actuall_hours');
//     frm.refresh_field('total_task_allowed_hours');
// }


frappe.ui.form.on('Weekly Work Sheet', {
    refresh: function(frm) {
        calculate_total_hours(frm);
    }
});

frappe.ui.form.on('Work Log Details', {
    actuall_hours: function(frm, cdt, cdn) {
        calculate_total_hours(frm);
    },
    task_allowed_hours: function(frm, cdt, cdn) {
        calculate_total_hours(frm);
    },
    work_log_details_add: function(frm) {
        calculate_total_hours(frm);  // Recalculate total when row is added
    },
    work_log_details_remove: function(frm) {
        calculate_total_hours(frm);  // Recalculate total when row is removed
    }
});

function calculate_total_hours(frm) {
    let total_actual_hours = 0;
    let total_task_allowed_hours = 0;

    frm.doc.work_log_details.forEach(function(row) {
        total_actual_hours += row.actuall_hours || 0;
        total_task_allowed_hours += row.task_allowed_hours || 0;
    });

    frm.set_value('total_actuall_hours', total_actual_hours);
    frm.set_value('total_task_allowed_hours', total_task_allowed_hours);

    // Refresh the fields so the updated values are reflected immediately
    frm.refresh_field('total_actuall_hours');
    frm.refresh_field('total_task_allowed_hours');
}
