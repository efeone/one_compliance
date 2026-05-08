frappe.ui.form.on('Timesheet', {
	time_logs_remove: function(frm) {
		frm.trigger('calculate_total_lag_hours');
	},
	calculate_total_lag_hours: function(frm) {
		let total_lag_seconds = 0;
		(frm.doc.time_logs || []).forEach(function(row) {
			if (row.lag_time) {
				total_lag_seconds += flt(row.lag_time);
			}
		});
		frm.set_value('total_lag_hours', total_lag_seconds / 3600.0);
	}
});

frappe.ui.form.on('Timesheet Detail', {
	lag_time: function(frm) {
		frm.trigger('calculate_total_lag_hours');
	}
});
