def get_compliance_sub_category_custom_fields():
    return {
        "Compliance Sub Category": [
            {
                "fieldname": "premium_task",
                "label": "Has Premium Task",
                "fieldtype": "Check",
                "insert_after": "rate",
                "in_list_view": 1
            }
        ]
    }