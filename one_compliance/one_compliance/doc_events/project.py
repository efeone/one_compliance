import frappe
from frappe.model.mapper import get_mapped_doc

@frappe.whitelist()
def make_sales_invoice(source_name, target_doc=None):
	def set_missing_values(source, target):
		if frappe.db.exists('Compliance Sub Category', source.compliance_sub_category):
			compliance_sub_category = frappe.get_doc ('Compliance Sub Category', source.compliance_sub_category)
			income_account = frappe.db.get_value('Company',source.company, 'default_income_account')

			target.append('items', {
			'item_name' : compliance_sub_category.name,
			'rate' : compliance_sub_category.rate,
			'qty' : 1,
			'income_account' : income_account,
			'description' : compliance_sub_category.name,
			})
	doclist = get_mapped_doc(
		'Project',
		source_name,
		{
			'Project':{
                'doctype':'Sales Invoice'
            
				},
			},
		target_doc,
		set_missing_values
	)
	doclist.save()

	return doclist
