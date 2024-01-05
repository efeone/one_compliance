import frappe
import json
from frappe.model.mapper import *
from frappe import _
from frappe.utils.user import get_users_with_role

@frappe.whitelist()
def set_customer_type_value(doc):
    '''
        Method used to set value in standard hidden field
    '''
    if doc.compliance_customer_type:
        if doc.compliance_customer_type == 'Individual':
            doc.customer_type = 'Individual'
        else:
            doc.customer_type = 'Company'

@frappe.whitelist()
def set_allow_edit(customer_contacts):
    customer_contacts = json.loads(customer_contacts)
    user = frappe.session.user
    user_roles = frappe.get_roles(user)
    for cu in customer_contacts:
        if "Director" in user_roles or "Compliance Manager" in user_roles:
            frappe.db.set_value('Customer Contacts',cu.get('name'),'allow_edit',1)
            frappe.db.commit()
        else:
            frappe.db.set_value('Customer Contacts',cu.get('name'),'allow_edit',0)
            frappe.db.commit()
    return True

@frappe.whitelist()
def create_agreement_custom_button(source_name, target_doc = None):
    def set_missing_values(source, target):
        target.customer_name= source.customer_name
        target.lead_name = source.lead_name
        target.opportunity_name= source.opportunity_name
    doc = get_mapped_doc(
        'Customer',
        source_name,
        {
        'Customer': {
        'doctype': 'Compliance Agreement',
        },
        },target_doc,set_missing_values)
    return doc

@frappe.whitelist()
def create_project_custom_button(source_name, target_doc = None):
    def set_missing_values(source, target):
        target.customer_name= source.customer_name
        target.lead_name = source.lead_name
        target.opportunity_name= source.opportunity_name
    doc = get_mapped_doc(
        'Customer',
        source_name,
        {
        'Customer': {
        'doctype': 'Project',
        },
        },target_doc,set_missing_values)
    return doc

@frappe.whitelist()
def create_payment_entry(mode_of_payment, paid_amount, customer):
    new_pe_doc = frappe.new_doc('Payment Entry')
    new_pe_doc.party_type = 'Customer'
    new_pe_doc.party = customer
    new_pe_doc.mode_of_payment = mode_of_payment
    new_pe_doc.paid_amount = paid_amount
    new_pe_doc.save()
    return new_pe_doc.name

@frappe.whitelist()
def filter_contact(doctype, txt, searchfield, start, page_len, filters):
    '''
        Method used to filter contact
    '''
    if filters:
        query = """
            SELECT
                c.name
            FROM
                `tabDynamic Link` as dl,
                `tabContact` as c
            WHERE
                dl.link_doctype = "Customer" AND
                dl.link_name = %(customer_name)s AND
                dl.parent = c.name
            LIMIT %(start)s, %(page_len)s
        """
        values = frappe.db.sql(query.format(**{
        }), {
            'customer_name': filters['customer_name'],
            'txt': "%{}%".format(txt),
            'start': start,
            'page_len': page_len
        })
        return values

def customer_on_update(doc, method):
    '''
        Method trigger on on_update of customer.
    '''
    set_customer_type_value(doc)
    create_user_from_customer(doc)

def create_user_from_customer(doc):
    create_user_on_customer_creation = frappe.db.get_single_value('Compliance Settings', 'create_user_on_customer_creation')
    if create_user_on_customer_creation:
        if doc.email_id:
            if not frappe.db.exists('User', doc.email_id):
                user_doc = frappe.new_doc('User')
                user_doc.email = doc.email_id
                user_doc.first_name = doc.customer_name
                user_doc.save(ignore_permissions = True)
                frappe.msgprint('User created for this customer', alert=True, indicator='green')

@frappe.whitelist()
def custom_button_for_view_compliance_agreement(customer):
    if frappe.db.exists('Compliance Agreement', {'customer':customer, 'status':'Active'}):
        compliance_agreement = frappe.db.get_value('Compliance Agreement', {'customer':customer, 'status':'Active'})
        return compliance_agreement
    else:
        return 0

@frappe.whitelist()
def custom_button_for_view_project(customer):
    if frappe.db.exists('Project', {'customer':customer}):
        return 1
    else:
        return 0

@frappe.whitelist()
def custom_button_for_view_payment(party_type, party):
    if frappe.db.exists('Payment Entry', {'party_type':party_type, 'party':party}):
        return 1
    else:
        return 0

@frappe.whitelist()
def send_clarification_message(customer,message):
    doc = frappe.get_doc('Customer',customer)
    recipient =doc.email_id
    subject = "Clarification Request"
    body = "Dear {},\n\nWe are writing to request clarification on the following matter: {}".format(customer, message)
    frappe.sendmail(recipients=[recipient],subject=subject, message=body)
    frappe.msgprint(
		msg = 'Mail Send', alert =1
	 )

@frappe.whitelist()
def check_invoice_based_on_and_project_status(customer):
    if frappe.db.exists('Compliance Agreement',{'customer':customer,'status':'Active'}):
        invoice_based_on, compliance_agreement = frappe.db.get_value('Compliance Agreement',{'customer':customer,'status':'Active'}, ['invoice_based_on','name'])
        if invoice_based_on and invoice_based_on == 'Consolidated':
            if frappe.db.exists('Project',{'customer':customer,'compliance_agreement':compliance_agreement,'status':'Completed'}):
                return True

@frappe.whitelist()
def make_sales_invoice(source_name, target_doc=None):
    #Method to create sales_invoice when invoice_based_on is Consolidated
    def set_missing_values(source, target):
        compliance_agreement = frappe.get_doc('Compliance Agreement',{'customer':source_name, 'status':'Active'})
        company = frappe.db.get_value('Project',{'customer':source_name,'compliance_agreement':compliance_agreement.name},'company')
        if company:
            income_account = frappe.db.get_value('Company',company, 'default_income_account')
        if compliance_agreement.compliance_category_details:
            for sub_category in compliance_agreement.compliance_category_details:
                is_billable = frappe.db.get_value('Compliance Sub Category', sub_category.compliance_category, 'is_billable')
                if is_billable:
                    rate = calculate_rate(compliance_agreement.compliance_category_details, sub_category.compliance_category)
                    if compliance_agreement.invoice_based_on == 'Consolidated':
                        if not check_exist(target, sub_category.compliance_category):
                            if source.payment_terms:
                                target.append('items', {
                                    'item_name' : sub_category.compliance_category,
                                    'rate' : rate,
                                    'qty' : 1,
                                    'income_account' : income_account,
                                    'description' : sub_category.name,
                                    'default_payment_terms_template' : source.payment_terms,
                                })
                            else:
                                target.append('items', {
                                    'item_name' : sub_category.compliance_category,
                                    'rate' : rate,
                                    'qty' : 1,
                                    'income_account' : income_account,
                                    'description' : sub_category.name,
                                })
    doclist = get_mapped_doc(
    'Customer',
    source_name,
        {
        'Customer':{
            'doctype':'Sales Invoice'

            },
        },
    target_doc,
        set_missing_values
    )
    doclist.save()
    return doclist

def check_exist(target, compliance_category):
    ''' checking if item already exist in child table '''
    exist = False
    if target.items:
        for item in target.items:
            if compliance_category:
                if item.item_name == compliance_category:
                    exist = True
                    break
    return exist

def calculate_rate(compliance_category_details, compliance_category):
	rate = 0
	for category in compliance_category_details:
		if category.compliance_category == compliance_category:
			rate += category.rate
	return rate
