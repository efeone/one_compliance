import frappe

def set_company_from_task(doc, method):
    if doc.reference_type == "Task" and doc.reference_name:
        company = frappe.db.get_value("Task", doc.reference_name, "company")
        if company:
            doc.company = company

def set_company_from_project(doc, method):
    if doc.reference_type == "Project" and doc.reference_name:
        company = frappe.db.get_value("Project", doc.reference_name, "company")
        if company:
            doc.company = company

def set_company_from_event(doc, method):
    if doc.reference_type == "Sales Order" and doc.reference_name:
        company = frappe.db.get_value("Sales Order", doc.reference_name, "company")
        client = frappe.db.get_value("Sales Order", doc.reference_name, "customer")
        sub_category = frappe.db.get_value(
            "Sales Order Item",
            {"parent": doc.reference_name},
            "custom_compliance_subcategory")
        if company:
            doc.company = company
            doc.client = client
            doc.compliance_sub_category = sub_category
