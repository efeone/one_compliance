import frappe
from frappe.model.mapper import get_mapped_doc

@frappe.whitelist()
def get_compliance_categories(customer = None):
    query = """
	SELECT
        S.compliance_category, S.name, R.document_attachment,D.customer
    FROM
        `tabCompliance Sub Category` S LEFT JOIN `tabCustomer Document Record` R ON R.compliance_sub_category = S.name
    LEFT JOIN `tabCustomer Document` D on R.parent = D.name
    """
    if customer:
            query += f" WHERE D.customer = '{customer}';"

    document_list = frappe.db.sql(query, as_dict=1)
    hierarchical_data = []
    for item in document_list:
        # Check if the category already exists
        category_exists = False
        for category_item in hierarchical_data:
            if category_item['category'] == item['compliance_category']:
                category_exists = True
                # Check if the sub-category already exists
                sub_category_exists = False
                for sub_category in category_item['sub_categories']:
                    if sub_category['sub_category'] == item['name']:
                        sub_category_exists = True
                        sub_category['documents'].append({
                            'document_attachment': item['document_attachment'],
                            'customer': item['customer']
                        })
                        break
                if not sub_category_exists:
                    category_item['sub_categories'].append({
                        'sub_category': item['name'],
                        'documents': [{
                            'document_attachment': item['document_attachment'],
                            'customer': item['customer']
                        }]
                    })
                break

        # If category doesn't exist, add it to the hierarchical_data
        if not category_exists:
            hierarchical_data.append({
                'category': item['compliance_category'],
                'sub_categories': [{
                    'sub_category': item['name'],
                    'documents': [{
                        'document_attachment': item['document_attachment'],
                        'customer': item['customer']
                    }]
                }]
            })

    return hierarchical_data

@frappe.whitelist()
def add_customer_document(sub_category, customer):
    # Search for an existing Customer Document for the selected customer
    if customer:
        existing_doc = frappe.get_doc('Customer Document', {'customer': customer}, 'name')
        print(existing_doc)
        if existing_doc:
            # If an existing Customer Document is found, return it
            return existing_doc
