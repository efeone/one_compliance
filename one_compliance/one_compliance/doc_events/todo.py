import frappe

def set_company_and_related_fields(doc, method):
    """Set company (and related fields) based on reference_type and reference_name."""
    if not doc.reference_type or not doc.reference_name:
        return

    ref_type = doc.reference_type
    ref_name = doc.reference_name

    if ref_type == "Task":
        company = frappe.db.get_value("Task", ref_name, "company")
        if company:
            doc.company = company

    elif ref_type == "Project":
        company = frappe.db.get_value("Project", ref_name, "company")
        if company:
            doc.company = company

    elif ref_type == "Sales Order":
        company, client = frappe.db.get_value("Sales Order", ref_name, ["company", "customer"])
        sub_category = frappe.db.get_value(
            "Sales Order Item",
            {"parent": ref_name},
            "custom_compliance_subcategory"
        )
        if company:
            doc.company = company
            doc.client = client
            doc.compliance_sub_category = sub_category

