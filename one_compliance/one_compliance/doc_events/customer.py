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
def custom_button_for_view_Compliance_agreement(customer):
    if frappe.db.exists('Compliance Agreement', {'customer':customer, 'status':'Active'}):
        compliance_agreement = frappe.db.get_value('Compliance Agreement', {'customer':customer, 'status':'Active'})
        return compliance_agreement
    else:
        return 0
