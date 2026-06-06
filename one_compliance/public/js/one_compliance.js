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

		min-width: 50px;
		min-height: 20px;

		font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto,
			Helvetica, Arial, sans-serif;
		}

		#oc-timer-box:empty {
			display: none !important;
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
      wrap.style.display = 'block';
    } else {
      link.style.display = 'none';
      wrap.style.display = 'none';
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
      const wrap = document.getElementById('oc-timer-wrap');
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
        if (wrap) wrap.style.display = 'block';

        if (user) {
          localStorage.setItem(PREFIX + user, JSON.stringify(timers));
        }
      } else {
        el.style.display = 'none';
        if (wrap) wrap.style.display = 'none';

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

  /**
   * Shows a dialog to create a new Event from the tool.
   * Shared between Task Management Tool and Project Management Tool.
   */
  window.show_add_event_dialog = function (opts = {}) {
    frappe.model.with_doctype('Event', function () {
      frappe.call({
        method: 'one_compliance.one_compliance.page.task_management_tool.task_management_tool.check_active_timer',
        callback: function (r) {
          // If starting a NEW event tracking session (no timer_task_id provided), check for overlap
          if (!opts.timer_task_id && r.message && r.message.status === 'warning') {
            frappe.msgprint({
              title: __('Active Task Running'),
              indicator: 'orange',
              message: r.message.message
            });
            return;
          }

          const meta = frappe.get_meta('Event');
          const category_field = meta.fields.find(f => f.fieldname === 'event_category');
          const category_options = category_field ? category_field.options : 'Events\nMeeting\nCall\nSent/Received Email\nOther';

          const dialog = new frappe.ui.Dialog({
            title: __('Add Event'),
            fields: [
              {
                label: __('Subject'),
                fieldname: 'subject',
                fieldtype: 'Data',
                reqd: 1
              },
              {
                label: __('Starts On'),
                fieldname: 'starts_on',
                fieldtype: 'Datetime',
                default: opts.start_time || frappe.datetime.now_datetime(),
                reqd: 1
              },
              {
                label: __('Client'),
                fieldname: 'client',
                fieldtype: 'Link',
                options: 'Customer'
              },
              {
                fieldtype: 'Column Break'
              },
              {
                label: __('Event Category'),
                fieldname: 'event_category',
                fieldtype: 'Select',
                options: category_options,
                default: 'Meeting'
              },
              {
                label: __('Company'),
                fieldname: 'company',
                fieldtype: 'Link',
                options: 'Company',
                default: frappe.defaults.get_user_default('company')
              },
              {
                label: __('End On'),
                fieldname: 'ends_on',
                fieldtype: 'Datetime',
                default: opts.timer_task_id ? frappe.datetime.now_datetime() : null
              }
            ],
            primary_action_label: __('Add Timesheet'),
            primary_action(values) {
              frappe.call({
                method: 'one_compliance.one_compliance.page.task_management_tool.task_management_tool.create_event_from_tool',
                args: {
                  ...values,
                  add_timesheet: true
                },
                callback: function (res) {
                  if (res.message) {
                    frappe.show_alert({
                      message: __('Event and Timesheet created successfully'),
                      indicator: 'green'
                    });
                    if (opts.timer_task_id) {
                      frappe.call({
                        method: 'one_compliance.one_compliance.page.task_management_tool.task_management_tool.stop_active_timer',
                        args: { task: opts.timer_task_id },
                        callback: (r) => {
                          if (r.message) {
                            $(document).trigger('one-compliance-timer-changed', [r.message]);
                            if (frappe.get_route()[0] === 'task-management-tool') {
                                location.reload();
                            }
                          }
                        }
                      });
                    }
                    dialog.hide();
                  }
                }
              });
            }
          });

          dialog.set_secondary_action_label(__('Close'));
          dialog.set_secondary_action(() => {
            if (opts.timer_task_id) {
                frappe.confirm(
                    __('Are you sure you want to close this dialog? Your tracking session will continue until stopped from the list.'),
                    () => {
                        dialog.hide();
                    }
                );
            } else {
                dialog.hide();
            }
          });

          dialog.add_custom_button(__('Edit Full Form'), function () {
            const values = dialog.get_values(true);
            if (opts.timer_task_id) {
              frappe.call({
                method: 'one_compliance.one_compliance.page.task_management_tool.task_management_tool.stop_active_timer',
                args: { task: opts.timer_task_id },
                callback: (r) => {
                  if (r.message) {
                    $(document).trigger('one-compliance-timer-changed', [r.message]);
                  }
                }
              });
            }
            dialog.hide();

            frappe.model.with_doctype('Event', function () {
              const doc = frappe.model.get_new_doc('Event');
              doc.subject = values.subject;
              doc.starts_on = values.starts_on;
              doc.ends_on = values.ends_on;
              doc.custom_customer = values.client;
              doc.event_category = values.event_category;
              doc.company = values.company;

              // Add current employee as participant
              frappe.db.get_value('Employee', { user_id: frappe.session.user }, ['name', 'employee_name']).then(r => {
                let employee = r.message ? r.message.name : null;
                let employee_name = r.message ? r.message.employee_name : null;
                if (employee) {
                  const row = frappe.model.add_child(doc, 'event_participants');
                  row.reference_doctype = 'Employee';
                  row.reference_docname = employee;
                  row.custom_participant_name = employee_name;
                }
                frappe.set_route('Form', 'Event', doc.name);
              });
            });
          });

          dialog.show();
        }
      });
    });
  };

  // =========================
  // Init
  // =========================
  injectStyles();
  boot();
  startSync();
})();