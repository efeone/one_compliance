import frappe
from frappe.model.mapper import *
from frappe import _

""" Method used to set value in standard hidden field """

@frappe.whitelist()
def set_customer_type_value(doc, method):
    if doc.compliance_customer_type:
        if doc.compliance_customer_type == 'Individual':
            doc.customer_type = 'Individual'
        else:
            doc.customer_type = 'Company'

""" Method used to create compliance Agreement from customer """

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
