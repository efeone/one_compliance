// Copyright (c) 2023, efeone and contributors
// For license information, please see license.txt

frappe.ui.form.on('Compliance Category', {
  setup:function(frm){
    // applied filter for getting head of department
    frm.set_query('head_of_department', function() {
      return{
        filters:{
          'department': frm.doc.department,
          'designation': 'Head Of Department'
        }
      }
    });
    // applied filter for designation in child table
    frm.set_query('employee','compliance_executive', () => {
      return {
        filters:{
          status: 'Active'
        }
    }
  })
  frm.set_query('department', () => {
    return {
      filters:{
        is_compliance: 1
      }
  }
})
    },
	refresh: function(frm) {
    if(!frm.is_new() && frm.doc.compliance_category){
      //custom button to view compliance sub category from compliance category//
      frm.add_custom_button('Add Sub Category', ()=>{
        frappe.model.open_mapped_doc({
          method : 'one_compliance.one_compliance.doctype.compliance_category.compliance_category.custom_button_for_sub_category',
          frm : cur_frm
        });
      });
    }
 },
 department: function(frm) {
  if(frm.doc.department){
    frappe.call({
      method: 'one_compliance.one_compliance.doctype.compliance_category.compliance_category.fetch_employees',
      args:{
        'department':frm.doc.department
      },
      callback: (r) =>{
        if (r.message){
          let compliance_executives = r.message;
          if(compliance_executives && compliance_executives.length){
            frm.clear_table('compliance_executive');
            compliance_executives.forEach((compliance_executive) => {
              let row = frm.add_child('compliance_executive', {
                employee: compliance_executive.name,
                employee_name: compliance_executive.employee_name,
                designation: compliance_executive.designation
              });
            });
          }
          frm.refresh_field('compliance_executive');
        }
      }
    })
  }
},
});

