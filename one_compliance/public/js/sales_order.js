frappe.ui.form.on('Sales Order', {
    refresh: function(frm) {
      if(!frm.is_new() && frm.doc.docstatus == 1){
        frm.add_custom_button('Create Project', () => {
          create_project_from_sales_order(frm)
        })
      }
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
              remark: values.remark
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
