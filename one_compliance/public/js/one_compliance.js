(function() {
	'use strict';

	var PREFIX = 'one-compliance-active-timer-';

	// =========================
	// CSS injection
	// =========================
	var style = document.createElement('style');
	style.textContent = `
		#oc-timer-wrap {
			position: fixed;
			bottom: 20px;
			right: 20px;
			z-index: 2147483647;
		}

		#oc-timer-box {
			background: #ff851b;
			color: white;
			padding: 10px 15px;
			border-radius: 8px;

			display: flex;
			align-items: center;
			gap: 10px;

			font-weight: bold;
			font-size: 14px;

			cursor: pointer;

			box-shadow: 0 4px 6px rgba(0,0,0,0.1);

			position: relative;
			z-index: 2;

			text-decoration: none;
			white-space: nowrap;

			font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
		}

		/* =========================
		   OUTER BLINK ONLY (no inside effect)
		   ========================= */
		#oc-timer-wrap::before {
			content: "";
			position: absolute;
			top: -2px;
			left: -2px;
			right: -2px;
			bottom: -2px;

			border-radius: 10px;

			pointer-events: none;

			box-shadow: 0 0 0 2px rgba(255,133,27,0.9);

			animation: oc-border-blink 1.2s infinite;
		}

		@keyframes oc-border-blink {
			0% {
				opacity: 1;
				box-shadow: 0 0 0 2px rgba(255,133,27,0.9);
			}
			50% {
				opacity: 0.3;
				box-shadow: 0 0 0 2px rgba(255,133,27,0.3);
			}
			100% {
				opacity: 1;
				box-shadow: 0 0 0 2px rgba(255,133,27,0.9);
			}
		}
	`;
	document.documentElement.appendChild(style);

	// =========================
	// DATA
	// =========================
	function getActiveData() {
		var match = document.cookie.match(/(?:^|; )user_id=([^;]*)/);
		var user = match ? decodeURIComponent(match[1]) : null;

		if (user) {
			var d = localStorage.getItem(PREFIX + user);
			if (d) try {
				var j = JSON.parse(d);
				return Array.isArray(j) ? j : [j];
			} catch(e) {}
		}

		for (var i = 0; i < localStorage.length; i++) {
			var key = localStorage.key(i);
			if (key && key.indexOf(PREFIX) === 0) {
				try {
					var data = JSON.parse(localStorage.getItem(key));
					return Array.isArray(data) ? data : [data];
				} catch(e) {}
			}
		}
		return [];
	}

	function esc(s) {
		if (!s) return "";
		return String(s)
			.replace(/&/g, "&amp;")
			.replace(/</g, "&lt;")
			.replace(/>/g, "&gt;")
			.replace(/"/g, "&quot;");
	}

	function getHTML(timers) {
		if (!timers || timers.length === 0) return '';

		var icon = '<i class="fas fa-stopwatch" style="font-size:1.2em;"></i>';
		var content = '';

		if (timers.length <= 3) {
			var lines = [];
			for (var i = 0; i < timers.length; i++) {
				var d = timers[i];
				var p = d.project ? esc(d.project) + ': ' : '';
				var t = esc(d.formatted_start_time || d.start_time);
				lines.push('<div>Timer is ON: ' + p + esc(d.subject) + ' (' + t + ')</div>');
			}
			content = '<div style="display:flex;flex-direction:column;gap:2px;">' + lines.join('') + '</div>';
		} else {
			content = '<span>Timer is ON: ' + timers.length + ' Tasks running</span>';
		}

		return icon + '<div style="margin-left:10px;">' + content + '</div>';
	}

	// =========================
	// RENDER
	// =========================
	function render() {
		if (document.getElementById('oc-timer-wrap')) return true;
		if (!document.body) return false;

		var wrap = document.createElement('div');
		wrap.id = 'oc-timer-wrap';

		var a = document.createElement('a');
		a.id = 'oc-timer-box';
		a.href = '/app/task-management-tool';

		var timers = getActiveData();
		if (timers.length > 0) {
			a.innerHTML = getHTML(timers);
		} else {
			a.style.display = 'none';
		}

		wrap.appendChild(a);
		document.body.appendChild(wrap);

		return true;
	}

	(function boot() {
		if (!render()) setTimeout(boot, 1);
	})();

	// =========================
	// SYNC (Frappe integration)
	// =========================
	function startSync() {
		if (!window.frappe || !frappe.call || !window.jQuery) {
			setTimeout(startSync, 100);
			return;
		}

		var up = function(data) {
			var el = document.getElementById('oc-timer-box');
			if (!el) return;

			var ts = Array.isArray(data) ? data : (data ? [data] : []);

			if (ts.length > 0) {
				if (frappe.datetime) {
					ts.forEach(function(x){
						if(x.start_time)
							x.formatted_start_time = frappe.datetime.str_to_user(x.start_time);
					});
				}

				el.innerHTML = getHTML(ts);
				el.style.display = 'flex';

				var u = (frappe.session && frappe.session.user) ||
						(frappe.boot && frappe.boot.user && frappe.boot.user.name);

				if (u) localStorage.setItem(PREFIX + u, JSON.stringify(ts));
			} else {
				el.style.display = 'none';

				var u = (frappe.session && frappe.session.user) ||
						(frappe.boot && frappe.boot.user && frappe.boot.user.name);

				if (u) localStorage.removeItem(PREFIX + u);
			}
		};

		$(document).on('one-compliance-timer-changed', function(e, d) { up(d); });

		if (frappe.realtime)
			frappe.realtime.on('one_compliance_timer_update', up);

		frappe.call({
			method: "one_compliance.one_compliance.page.task_management_tool.task_management_tool.get_active_timer",
			callback: function(r) {
				up(r.message);
			}
		});
	}

	startSync();

})();