from frappe import _


def get_data():
	return {
		"fieldname": "compliance_category",
		"non_standard_fieldnames": {
			"Project": "compliance_category",
			"Compliance Sub Category": "compliance_category",
		},
		"transactions": [
			{"label": _("Project"), "items": ["Project",],},
			{"label": _("Sub Category"), "items": ["Compliance Sub Category"]},
        ],
	}
