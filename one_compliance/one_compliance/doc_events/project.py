import frappe
from frappe.model.mapper import get_mapped_doc

@frappe.whitelist()
def make_sales_invoice(source_name, target_doc=None):
	def set_missing_values(source, target):
		income_account = frappe.db.get_value('Company',source.company, 'default_income_account')
		if frappe.db.exists('Compliance Agreement', source.compliance_agreement):
			compliance_agreement = frappe.get_doc ('Compliance Agreement', source.compliance_agreement)
			if compliance_agreement.compliance_category_details:
				for sub_category in compliance_agreement.compliance_category_details:
					if frappe.db.exists('Compliance Sub Category', sub_category.compliance_sub_category):
						sub_category_doc = frappe.get_doc('Compliance Sub Category', sub_category.compliance_sub_category)
						target.append('items', {
						'item_name' : sub_category.compliance_sub_category,
						'rate' : sub_category_doc.rate,
						'qty' : 1,
						'income_account' : income_account,
						'description' : sub_category_doc.name,
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
