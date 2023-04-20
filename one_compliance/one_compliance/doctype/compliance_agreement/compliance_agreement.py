
import frappe
import json
from frappe.model.document import Document
from frappe.model.mapper import *
from frappe import _
from frappe.utils import *

class ComplianceAgreement(Document):
	''' Method used for validate Signature '''
	def on_update_after_submit(self):
		self.sign_validation()

	def before_insert(self):
		self.status = "Open"

	def sign_validation(self):
		if self.workflow_state == 'Approved' and not self.authority_signature:
			frappe.throw('Authority Signature is required for Approval')
		if self.workflow_state == 'Customer Approved' and not self.customer_signature:
			frappe.throw('Customer Signature is required for Approval')

	def validate(self):
		self.date_validation()

	def date_validation(self):
		if getdate(self.valid_from) > getdate(self.valid_upto) :
			frappe.throw('From Date cannot be greater than Upto Date')

	@frappe.whitelist()
	def list_sub_category(self):
		rate = 0
		if self.compliance_category:
			for compliance_category in self.compliance_category:
				compliance_sub_category_list = get_compliance_sub_category_list(compliance_category)
				if compliance_sub_category_list:
					for compliance_sub_category in compliance_sub_category_list:
						rate += compliance_sub_category.rate
						if not check_exist_list(self, compliance_sub_category):
							self.append('compliance_category_details',{
							'compliance_category':compliance_sub_category.compliance_category,
							'compliance_sub_category':compliance_sub_category.name,
							'rate':compliance_sub_category.rate
							})
			self.total = rate
			return True


@frappe.whitelist()
def check_project_status(compliance_agreement):
	if frappe.db.exists('Project', {'compliance_agreement':compliance_agreement, 'status':'Completed'}):
		return True

@frappe.whitelist()
def make_sales_invoice(source_name, target_doc=None):
	def set_missing_values(source, target):
		if frappe.db.exists('Project', {'compliance_agreement':source.name}):
			company = frappe.db.get_value('Project', {'compliance_agreement':source.name},'company')
			income_account = frappe.db.get_value('Company',company, 'default_income_account')
		if source.compliance_category_details:
			for sub_category in source.compliance_category_details:
				rate = calculate_rate(source.compliance_category_details, sub_category.compliance_category)
				if source.invoice_based_on == 'Project':
					target.append('items', {
					'item_name' : sub_category.compliance_sub_category,
					'rate' : sub_category.rate,
					'qty' : 1,
					'income_account' : income_account,
					'description' : sub_category.name,
					})
				if source.invoice_based_on == 'Consolidated':
					if not check_exist(target, sub_category.compliance_category):
						target.append('items', {
							'item_name' : sub_category.compliance_category,
							'rate' : rate,
							'qty' : 1,
							'income_account' : income_account,
							'description' : sub_category.name,
						})
	doclist = get_mapped_doc(
		'Compliance Agreement',
		source_name,
		{
			'Compliance Agreement':{
                'doctype':'Sales Invoice'

				},
			},
		target_doc,
		set_missing_values
	)
	doclist.save()

	return doclist

def check_exist(target, compliance_category):
    ''' checking if item allready exist in child table '''
    exist = False
    try:
        if target.items:
            for item in target.items:
                if compliance_category:
                    if item.item_name == compliance_category:
                        exist = True
    except:
        exist = False
    return exist

def calculate_rate(compliance_category_details, compliance_category):
	rate = 0
	for category in compliance_category_details:
		if category.compliance_category == compliance_category:
			rate += category.rate
	return rate

@frappe.whitelist()
def set_value_in_status():
	'''Method used for set value to status field '''
	agreements = frappe.db.get_all('Compliance Agreement', filters = {'status': 'Active', 'docstatus': ['!=', 2]})
	if agreements:
		for agreement in agreements:
			valid_upto = frappe.db.get_value('Compliance Agreement', agreement.name, 'valid_upto')
			if valid_upto:
				today = getdate(frappe.utils.today())
				if today <= getdate(valid_upto) :
					frappe.db.set_value('Compliance Agreement',  agreement.name, 'status', 'Active')
				else:
					frappe.db.set_value('Compliance Agreement',  agreement.name, 'status', 'Expired')

def get_compliance_sub_category_list(compliance_category):
	'''method used for list sub category'''
	sub_category_list = frappe.db.get_list('Compliance Sub Category', filters = {'compliance_category':compliance_category.compliance_category, 'enabled':1}, fields = ['rate','name','compliance_category'])
	return sub_category_list

def check_exist_list(self, compliance_sub_category):
	'''method used for checking sub category in corresponding sub category'''
	exist = False
	try:
		if self.compliance_category_details:
			for item in self.compliance_category_details:
				if compliance_sub_category:
					if item.compliance_sub_category == compliance_sub_category.name and item.compliance_category == compliance_sub_category.compliance_category:
						exist = True
	except:
		exist = False
	return exist

@frappe.whitelist()
def set_agreement_status(agreement_id, status):
    frappe.db.set_value('Compliance Agreement', agreement_id, 'status', status)
    frappe.db.commit()
    return True
