(function () {
  'use strict';

  const PREFIX = 'one-compliance-active-timer-';

  // =========================
  // CSS Injection
  // =========================
  function injectStyles() {
	const Z_INDEX = 1040;
	const style = document.createElement('style');

	style.textContent = `
		#oc-timer-wrap {
		position: fixed;
		bottom: 20px;
		right: 20px;
		z-index: ${Z_INDEX};
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

		box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);

		position: relative;
		z-index: 2;

		text-decoration: none;
		white-space: nowrap;

		font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto,
			Helvetica, Arial, sans-serif;
		}

		#oc-timer-wrap::before {
		content: '';
		position: absolute;
		top: -2px;
		left: -2px;
		right: -2px;
		bottom: -2px;

		border-radius: 10px;
		pointer-events: none;

		box-shadow: 0 0 0 2px rgba(255, 133, 27, 0.9);
		animation: oc-border-blink 1.2s infinite;
		}

		@keyframes oc-border-blink {
		0% {
			opacity: 1;
			box-shadow: 0 0 0 2px rgba(255, 133, 27, 0.9);
		}
		50% {
			opacity: 0.3;
			box-shadow: 0 0 0 2px rgba(255, 133, 27, 0.3);
		}
		100% {
			opacity: 1;
			box-shadow: 0 0 0 2px rgba(255, 133, 27, 0.9);
		}
		}
	`;

	document.documentElement.appendChild(style);
	}

  // =========================
  // Utilities
  // =========================

  /**
   * Escape HTML to prevent XSS
   * @param {string} str
   * @returns {string}
   */
  function esc(str) {
    if (!str) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  /**
   * Get active timer data from localStorage (fallback/cache)
   * @returns {Array<Object>}
   */
  function getActiveData() {
    const match = document.cookie.match(/(?:^|; )user_id=([^;]*)/);
    const user = match ? decodeURIComponent(match[1]) : null;

    if (user) {
      const data = localStorage.getItem(PREFIX + user);
      if (data) {
        try {
          const parsed = JSON.parse(data);
          return Array.isArray(parsed) ? parsed : [parsed];
        } catch (e) {
          console.warn('Invalid timer data in localStorage', e);
        }
      }
    }

    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      if (key && key.startsWith(PREFIX)) {
        try {
          const data = JSON.parse(localStorage.getItem(key));
          return Array.isArray(data) ? data : [data];
        } catch (e) {
          console.warn('Error parsing fallback timer data', e);
        }
      }
    }

    return [];
  }

  /**
   * Generate HTML for timer display
   * @param {Array<Object>} timers
   * @returns {string}
   */
  function getHTML(timers) {
    if (!timers || timers.length === 0) return '';

    const icon =
      '<i class="fas fa-stopwatch" style="font-size:1.2em;"></i>';

    let content = '';

    if (timers.length <= 3) {
      const lines = timers.map((d) => {
        const project = d.project ? esc(d.project) + ': ' : '';
        const time = esc(d.formatted_start_time || d.start_time);

        return (
          '<div>' +
          'Timer is ON: ' +
          project +
          esc(d.subject) +
          ' (' +
          time +
          ')' +
          '</div>'
        );
      });

      content =
        '<div style="display:flex;flex-direction:column;gap:2px;">' +
        lines.join('') +
        '</div>';
    } else {
      content =
        '<span>Timer is ON: ' +
        timers.length +
        ' Tasks running</span>';
    }

    return icon + '<div style="margin-left:10px;">' + content + '</div>';
  }

  // =========================
  // Render
  // =========================

  /**
   * Render floating timer UI
   * @returns {boolean}
   */
  function render() {
    if (document.getElementById('oc-timer-wrap')) return true;
    if (!document.body) return false;

    const wrap = document.createElement('div');
    wrap.id = 'oc-timer-wrap';

    const link = document.createElement('a');
    link.id = 'oc-timer-box';
    link.href = '/app/task-management-tool';

    const timers = getActiveData();

    if (timers.length > 0) {
      link.innerHTML = getHTML(timers);
    } else {
      link.style.display = 'none';
    }

    wrap.appendChild(link);
    document.body.appendChild(wrap);

    return true;
  }

  /**
   * Boot renderer safely
   */
  function boot() {
    if (!render()) {
      setTimeout(boot, 10);
    }
  }

  // =========================
  // Sync with Frappe Backend
  // =========================

  /**
   * Start real-time sync with backend
   */
  function startSync() {
    if (!window.frappe || !frappe.call || !window.jQuery) {
      setTimeout(startSync, 100);
      return;
    }

    /**
     * Update UI with timer data
     * @param {Array|Object|null} data
     */
    function update(data) {
      const el = document.getElementById('oc-timer-box');
      if (!el) return;

      const timers = Array.isArray(data)
        ? data
        : data
        ? [data]
        : [];

      const user =
        (frappe.session && frappe.session.user) ||
        (frappe.boot && frappe.boot.user && frappe.boot.user.name);

      if (timers.length > 0) {
        if (frappe.datetime) {
          timers.forEach((t) => {
            if (t.start_time) {
              t.formatted_start_time =
                frappe.datetime.str_to_user(t.start_time);
            }
          });
        }

        el.innerHTML = getHTML(timers);
        el.style.display = 'flex';

        if (user) {
          localStorage.setItem(PREFIX + user, JSON.stringify(timers));
        }
      } else {
        el.style.display = 'none';

        if (user) {
          localStorage.removeItem(PREFIX + user);
        }
      }
    }

    // Custom event
    $(document).on('one-compliance-timer-changed', function (e, data) {
      update(data);
    });

    // Realtime event
    if (frappe.realtime) {
      frappe.realtime.on('one_compliance_timer_update', update);
    }

    // Initial fetch
    frappe.call({
      method:
        'one_compliance.one_compliance.page.task_management_tool.task_management_tool.get_active_timer',
      callback: function (r) {
        update(r.message);
      },
    });
  }

  // =========================
  // Ad-hoc Events
  // =========================

  /**
   * Start a synthetic task timer for an ad-hoc event
   */
  window.start_active_event_timer = function () {
    frappe.call({
      method:
        'one_compliance.one_compliance.page.task_management_tool.task_management_tool.check_active_timer',
      callback: function (r) {
        if (r.message) {
          frappe.msgprint(r.message);
        } else {
          const user = frappe.session.user;
          const task_id = 'EVENT-' + user;
          const start_time = frappe.datetime.now_datetime();

          frappe.call({
            method:
              'one_compliance.one_compliance.page.task_management_tool.task_management_tool.start_active_timer',
            args: {
              task: task_id,
              project: '',
              subject: 'Ad-hoc Event',
              start_time: start_time,
            },
            callback: function (r) {
              $(document).trigger('one-compliance-timer-changed', [
                r.message,
              ]);
              $(document).trigger('one-compliance-refresh-tools');
            },
          });
        }
      },
    });
  };

  /**
   * Show dialog to finalize an ad-hoc event
   * @param {string} start_time
   * @param {string} subject
   */
  window.show_add_event_dialog = function (start_time, subject) {
    frappe.model.with_doctype('Event', function () {
      const meta = frappe.get_meta('Event');
      const catField = meta.fields.find(
        (f) => f.fieldname === 'event_category'
      );
      const options = catField ? catField.options.split('\n') : [];

      const d = new frappe.ui.Dialog({
        title: __('Add Event'),
        fields: [
          {
            label: __('Subject'),
            fieldname: 'subject',
            fieldtype: 'Data',
            reqd: 1,
            default: subject || 'Ad-hoc Event',
          },
          {
            label: __('Starts On'),
            fieldname: 'start_time',
            fieldtype: 'Datetime',
            read_only: 1,
            default: start_time,
          },
          {
            label: __('Company'),
            fieldname: 'company',
            fieldtype: 'Link',
            options: 'Company',
            reqd: 1,
            default: frappe.defaults.get_user_default('company'),
          },
          {
            label: __('Client'),
            fieldname: 'customer',
            fieldtype: 'Link',
            options: 'Customer',
          },
          {
            label: __('Event Category'),
            fieldname: 'event_category',
            fieldtype: 'Select',
            options: options,
            reqd: 1,
          },
          {
            label: __('Description'),
            fieldname: 'description',
            fieldtype: 'Small Text',
          },
          {
            label: __('Ends On'),
            fieldname: 'ends_on',
            fieldtype: 'Datetime',
            reqd: 1,
            default: frappe.datetime.now_datetime(),
          },
        ],
        primary_action_label: __('Add Timesheet'),
        primary_action(values) {
          if (values.ends_on <= values.start_time) {
            frappe.msgprint(__('Ends On must be after Starts On'));
            return;
          }
          d.disable_primary_action();
          frappe.call({
            method:
              'one_compliance.one_compliance.page.task_management_tool.task_management_tool.create_event_from_tool',
            args: values,
            callback: function (r) {
              if (r.message) {
                frappe.show_alert({
                  message: __('Event and Timesheet created successfully'),
                  indicator: 'green',
                });
                d.hide();
                $(document).trigger('one-compliance-timer-changed', [[]]);
                const task_page = frappe.pages['task-management-tool'];
                if (task_page && task_page.page) {
                  task_page.page.completed_event_data = {
                    name: 'EVENT-' + frappe.session.user,
                    subject: values.subject,
                    status: 'Completed',
                    is_event: true,
                    start_time: values.start_time
                  };
                }
                $(document).trigger('one-compliance-refresh-tools');
              }
            },
            always: function () {
              d.enable_primary_action();
            },
          });
        },
      });
      d.show();
    });
  };

  // =========================
  // Init
  // =========================
  injectStyles();
  boot();
  startSync();
})();