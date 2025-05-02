// Copyright (c) 2025, efeone and contributors
// For license information, please see license.txt

frappe.ui.form.on('Weekly Work Sheet', {
    week_start_date: function(frm) {
        if (frm.doc.week_start_date && frm.doc.employee) {
            frappe.call({
                method: "one_compliance.one_compliance.doctype.weekly_work_sheet.weekly_work_sheet.get_work_log_data",
                args: {
                    week_start_date: frm.doc.week_start_date,
                    employee: frm.doc.employee
                },
                callback: function(r) {
                    if (r.message) {
                        const data = r.message;

                        frm.set_value("week_end_date", data.week_end_date);
                        frm.clear_table("work_log_details");

                        (data.work_log_details || []).forEach(row => {
                            let child = frm.add_child("work_log_details");

                            // Explicitly assigning all properties, including task_allowed_hours
                            child.task = row.task;
                            child.task_description = row.task_description;
                            child.actuall_hours = row.actuall_hours;
                            child.task_allowed_hours = row.task_allowed_hours;
                            child.log_date = row.log_date;
                            child.status = row.status;

                        });

                        frm.refresh_field("work_log_details");

                        // Ensure totals are recalculated after setting child table rows
                        frm.set_value("total_actuall_hours", data.total_actuall_hours);
                        frm.set_value("total_task_allowed_hours", data.total_task_allowed_hours);
                        calculate_totals(frm);  // Ensure totals are consistent
                    }
                }
            });
        }
    }
});

function calculate_totals(frm) {

    let total_actuall = 0;

    let total_allowed = 0;

    frm.doc.work_log_details.forEach(row => {

        total_actuall += flt(row.actuall_hours);

        total_allowed += flt(row.task_allowed_hours);

    });
    frm.set_value("total_actuall_hours", total_actuall);
    frm.set_value("total_task_allowed_hours", total_allowed);

}
