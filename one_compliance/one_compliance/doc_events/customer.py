import frappe
import json
from frappe.model.mapper import *
from frappe import _
from frappe.utils.user import get_users_with_role

""" Method used to set value in standard hidden field """

@frappe.whitelist()
def set_customer_type_value(doc, method):
    if doc.compliance_customer_type:
        if doc.compliance_customer_type == 'Individual':
            doc.customer_type = 'Individual'
        else:
            doc.customer_type = 'Company'

@frappe.whitelist()
def set_allow_edit(customer_contacts):
    ''' Method used for set email and ohone number field as editable for particular user role '''
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


""" method used to filter contact """

@frappe.whitelist()
def filter_contact(doctype, txt, searchfield, start, page_len, filters):
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

""" Method to add customer Credential details """

@frappe.whitelist()
def add_credential_details(customer,purpose):
    if frappe.db.exists('Customer Credentials',{'customer':customer}):
        customer_credential = frappe.db.get_value('Customer Credentials',{'customer':customer})
        if frappe.db.exists('Credential Details', {'parent':customer_credential,'purpose':purpose}):
            username, password, url = frappe.db.get_value('Credential Details', {'parent':customer_credential,'purpose':purpose}, ['username', 'password','url'])
            return [username, password, url]
        else:
            frappe.throw(_('Credential not configured for this Purpose'))
