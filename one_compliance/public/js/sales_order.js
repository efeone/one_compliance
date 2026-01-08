frappe.ui.form.on('Sales Order', {
    onload: function(frm) {
      if(frm.is_new()){
        frappe.db.get_single_value('Compliance Settings', 'create_project_from_sales_order_automatically').then(value => {
            // Set value of check field in Sales Order form
            frm.set_value('custom_create_project_automatically', value);
        });
      }
    },
    refresh: function(frm) {
      if(!frm.is_new() && frm.doc.docstatus == 1 && !frm.doc.custom_create_project_automatically){
        frm.add_custom_button('Create Project', () => {
          create_project_from_sales_order(frm)
        })
      }
      if(frm.is_new()){
        frm.set_value('delivery_date', frappe.datetime.get_today());
      }
      setTimeout(() => {
        frm.fields_dict.items.grid.toggle_reqd("delivery_date")

        frm.remove_custom_button('Pick List', 'Create');
        frm.remove_custom_button('Delivery Note', 'Create');
        frm.remove_custom_button('Work Order', 'Create');
        frm.remove_custom_button('Material Request', 'Create');
        frm.remove_custom_button('Request for Raw Materials', 'Create');
        frm.remove_custom_button('Purchase Order', 'Create');
        frm.remove_custom_button('Project', 'Create');
        }, 500);

        handle_unlinking(frm);

        handle_rework_order(frm);

        // Show button only if checkbox is checked and no PI exists yet
		if (frm.doc.is_outsource_service && !frm.doc.purchase_invoice) {
			frm.add_custom_button(__('Create Purchase Invoice'), () => {
				create_purchase_invoice(frm);
			});
		}
    },

    supplier: (frm) => {
        frm.set_value("purchase_invoice", null);
        apply_filter_to_supplier_purchase_invoice(frm, frm.doc.supplier);
    },

    purchase_invoice: (frm) => {
        make_is_outsource_service_read_only(frm);
    }
});

let create_project_from_sales_order = function (frm) {
  let items = frm.doc.items;
  items = items.map(item => item.item_code);
  let d = new frappe.ui.Dialog({
    title: 'Create Project',
    fields: [
      {
        label: 'Expected Start Date',
        fieldname: 'expected_start_date',
        fieldtype: 'Date',
        reqd: 1,
      },
      {
        label: 'Service',
        fieldname: 'item',
        fieldtype: 'Link',
        options: 'Item',
        onchange: function() {
          let item_code = d.get_value('item');
          // Fetch compliance subcategory based on the selected item
          frappe.call({
            method: 'one_compliance.one_compliance.doc_events.sales_order.get_compliance_subcategory',
            args: {
              item_code: item_code
            },
            callback: function(r) {
              if (r.message) {
                let compliance_sub_category = r.message;
                d.set_value('compliance_category', compliance_sub_category.compliance_category);
                d.set_value('compliance_sub_category', compliance_sub_category.name);
                d.set_value('project_template', compliance_sub_category.project_template);
              }
            }
          });
        }
      },
      {
        label: 'Compliance Category',
        fieldname: 'compliance_category',
        fieldtype: 'Link',
        read_only: true
      },
      {
        label: 'Compliance Sub Category',
        fieldname: 'compliance_sub_category',
        fieldtype: 'Link',
        read_only: true
      },
      {
        fieldtype: "Column Break",
        fieldname: "col_break_1",
      },
      {
        label: 'Expected End Date',
        fieldname: 'expected_end_date',
        fieldtype: 'Date',
      },
      {
        label: 'Priority',
        fieldname: 'priority',
        fieldtype: 'Select',
        options: ["Medium", "Low", "High"],
        reqd: 1
      },
      {
        label: 'Project Template',
        fieldname: 'project_template',
        fieldtype: 'Link',
        read_only: true
      },
      {
          label: __("Assign To"),
          fieldname: "assign_to",
          fieldtype: 'MultiSelectPills',
          get_data: function (txt) {
            return frappe.db.get_link_options("Employee", txt);
          },
      },
      {
        fieldtype: "Section Break",
        fieldname: "col_break_1",
      },
      {
        label: 'Remark',
        fieldname: 'remark',
        fieldtype: 'Small Text'
      }
    ],
    primary_action_label: 'Submit',
    primary_action(values) {
      frm.doc.items.forEach((item) => {
        if (item.item_code == values.item) {
          frappe.call({
            method: 'one_compliance.one_compliance.doc_events.sales_order.create_project_from_sales_order',
            args: {
              sales_order: frm.doc.name,
              start_date: values.expected_start_date,
              expected_end_date: values.expected_end_date,
              item_code: values.item,
              priority: values.priority,
              remark: values.remark,
              assign_to: values.assign_to
            },
            callback: function (r) {
              if (r.message) {
                frm.reload_doc();
              }
            }
          });

        }
      });
      d.hide();
    }
  });

  d.fields_dict.item.get_query = function () {
    return {
      filters: {
        'name': ['in', items]
      }
    };
  };
  d.show();
}

frappe.ui.form.on('Sales Order Item', {
  item_code: function(frm, cdt, cdn) {
    var child_doc = locals[cdt][cdn];
    if (child_doc.item_code) {
      frappe.call({
        method: 'frappe.client.get_value',
        args: {
            doctype: 'Compliance Sub Category',
            filters: {
                item_code: child_doc.item_code
            },
            fieldname: ['compliance_category', 'name']
        },
        callback: function(response) {
          if (response.message) {
              child_doc.custom_compliance_category = response.message.compliance_category
              child_doc.custom_compliance_subcategory = response.message.name
          }
        }
      });
    }
	}
});

frappe.ui.form.on('Reimbursement Details', {
  approve: function(frm, cdt, cdn) {
    let child = locals[cdt][cdn];
    frappe.call({
        method: 'one_compliance.one_compliance.doc_events.sales_order.submit_journal_entry',
        args: {
            'journal_entry':  child.journal_entry
        },
        callback: function(r) {
            if (r.message) {
                frappe.msgprint(__('Journal Entry Submitted Successfully'));
                frm.refresh_fields();
            }
        }
    });
  }
});

function handle_unlinking(frm) {
  if (!frm.is_new() && frm.doc.workflow_state == "In Progress") {
    frappe.db
      .get_single_value("Compliance Settings", "role_allowed_to_unlink_and_delete_sales_orders")
      .then((role) => {
        if (role && frappe.user_roles.includes(role)) {
          frm.add_custom_button("Unlink and Delete", () => {
            frappe.confirm(
              __(
                `Are you sure you want to unlink and delete all linked records of <b>${frm.doc.name}</b>?`
              ),
              function () {
                frappe.call({
                  method:
                    "one_compliance.one_compliance.doc_events.sales_order.delete_linked_records",
                  args: {
                    sales_order: frm.doc.name,
                  },
                  callback: function (r) {
                    if (r.message === "success") {
                      frappe.msgprint(
                        __("All linked records have been successfully deleted.")
                      );
                      frappe.set_route("List", "Sales Order");
                    } else {
                      frappe.throw(
                        __("An error occurred while deleting linked records.")
                      );
                    }
                  },
                });
              }
            );
          });
        }
      });
  }
}

function handle_rework_order(frm) {
  // If the sales order is a rework order, remove buttons to create payments or invoice
  if (frm.doc.custom_is_rework) {
    setTimeout(() => {
      frm.remove_custom_button("Payment", "Create");
      frm.remove_custom_button("Sales Invoice", "Create");
      frm.remove_custom_button("Payment Request", "Create");
    }, 500);
  }
}


// Get list of Projects linked to the given Sales Order
const get_projects_from_sales_order = async (sales_order) => {
    const r = await frappe.call({
        method: "frappe.client.get_list",
        args: {
            doctype: "Project",
            filters: {
                sales_order: sales_order
            },
            fields: ["name"]
        }
    });

    return (r.message || []).map(p => p.name);
};


/**
 * Apply filter to Purchase Invoice field based on Supplier and linked Projects
 */
const apply_filter_to_supplier_purchase_invoice = async (frm, supplier) => {
    if (!frm.doc.name || !supplier) return;

    const projects = await get_projects_from_sales_order(frm.doc.name);

    frm.set_query("purchase_invoice", () => {
        // Supplier-only filter
        if (!projects || !projects.length) {
            return {
                filters: {
                    supplier: supplier
                }
            };
        }
        // Supplier + Projects filter
        return {
            filters: {
                supplier: supplier,
                project: ["in", projects]
            }
        };
    });
};




function create_purchase_invoice(frm) {
	// Prompt user to add Service Item(s) and Rate(s)
	frappe.prompt([
		{
			fieldname: 'item_code',
			fieldtype: 'Link',
			label: 'Service Item',
			options: 'Item',
			reqd: 1,
            get_query: () => {
                return {
                    filters: {
                        is_purchase_item: 1,
                        is_service_item: 1,
                        is_stock_item: 0
                    }
                }
            }
		},
		{
			fieldname: 'rate',
			fieldtype: 'Currency',
			label: 'Rate',
			reqd: 1
		}
	],
	(values) => {
		frappe.call({
			method: 'one_compliance.one_compliance.doc_events.sales_order.create_purchase_invoice',
			args: {
				docname: frm.doc.name,
				items: [values]
			},
			callback: function(r) {
				if (r.message) {
					frm.set_value('purchase_invoice', r.message);
					frm.refresh_field('purchase_invoice');
                    frm.reload_doc();
					frappe.msgprint(__('Purchase Invoice {0} created successfully', [r.message]));
				}
			}
		});
	},
	'Add Service Item',
	'Create'
	);
}


// Make 'is_outsource_service' field read-only if Purchase Invoice is linked
const make_is_outsource_service_read_only = (frm) => {
    if (frm.doc.purchase_invoice) {
        frm.set_df_property("is_outsource_service", "read_only", true);
    }
    else {
        frm.set_df_property("is_outsource_service", "read_only", false);
    }
}
