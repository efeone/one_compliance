frappe.ui.form.on('Compliance Agreement',{
  refresh :function(frm){
    frm.set_query('compliance_sub_category','compliance_category_details',(frm,cdt,cdn) => {
      let child = locals[cdt][cdn];
  		return {
  			filters: {'compliance_category': child.compliance_category}
  		};
  	});
  },
  compliance_category:function(frm){
    update_compliance_category(frm);
  }
});
let update_compliance_category = function (frm) {
	let compliance_category = frm.doc.compliance_category;
	let compliance_category_length = frm.doc.compliance_category.length;
  let compliance_category_details_length = 0
  if(frm.doc.compliance_category_details){
    compliance_category_details_length = frm.doc.compliance_category_details.length;
  }
	if (compliance_category_length > compliance_category_details_length) {
    frm.clear_table('compliance_category_details')
    frm.doc.compliance_category.forEach(compliance_category => {
            let compliance_category_table = frm.add_child('compliance_category_details');
            compliance_category_table.compliance_category = compliance_category.compliance_category
            frm.refresh_field('compliance_category_details')
    });
	}
	else if (compliance_category_length < compliance_category_details_length) {
		if (compliance_category_length) {
			compliance_category_length = frm.doc.compliance_category.length
			let compliance_categorys = []
			frm.doc.compliance_category.forEach(compliance_category => {
				compliance_categorys.push(compliance_category.compliance_category)
			});
			delete_row_from_compliance_category_table(compliance_categorys)
      compliance_category = frm.doc.compliance_category
			compliance_category_length = frm.doc.compliance_category.length
		}
		else {
			frm.clear_table('compliance_category_details')
			frm.refresh_field('compliance_category_details')
		}
	}
}

let delete_row_from_compliance_category_table = function (compliance_categorys) {
			let table = cur_frm.doc.compliance_category_details || [];
			let i = table.length;
			while (i--) {
				if(!compliance_categorys.includes(table[i].compliance_category)) {
					cur_frm.get_field('compliance_category_details').grid.grid_rows[i].remove();
				}
			}
			cur_frm.refresh_field('compliance_category_details');
}
