import frappe
from frappe import _
from frappe.model.naming import make_autoname

def sales_invoice_on_submit(doc, method):
    if doc.project:
        frappe.db.set_value('Project', doc.project, 'status', 'Invoiced')
        frappe.db.set_value('Project', doc.project, 'is_invoiced', 1)
        frappe.db.commit()

def autoname(doc, method=None):
    if doc.company and doc.custom_invoice_type:
        compliance_settings = frappe.get_doc("Compliance Settings")
        invoice_series_name = ''
        for series in compliance_settings.invoice_series:
            if series.company  == doc.company and doc.custom_invoice_type == series.invoice_type and series.sales_invoice_series:
                invoice_series_name = series.sales_invoice_series
        if invoice_series_name:
            doc.name = frappe.model.naming.make_autoname(invoice_series_name)
        else:
            frappe.throw(_("khjg"))
