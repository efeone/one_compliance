import frappe

def execute():
	tasks = frappe.get_all(
		"Task",
		filters={
			"custom_payable_amount": [">", 0],
			"custom_mode_of_payment": ["!=", ""]
		},
		fields=[
			"name",
			"custom_payable_amount",
			"custom_mode_of_payment",
			"custom_reference_number",
			"custom_reference_date"
		]
	)

	for task in tasks:
		if not task.custom_payable_amount:
			continue
		exists = frappe.db.exists(
			"Task Payment Information",
			{
				"parent": task.name,
				"parenttype": "Task",
				"parentfield": "custom_task_payment_informations",
				"mode_of_payment": task.custom_mode_of_payment,
				"payable_amount": task.custom_payable_amount
			}
		)

		if exists:
			continue

		frappe.get_doc({
			"doctype": "Task Payment Information",
			"parent": task.name,
			"parenttype": "Task",
			"parentfield": "custom_task_payment_informations",
			"mode_of_payment": task.custom_mode_of_payment,
			"payable_amount": task.custom_payable_amount,
			"reference_number": task.custom_reference_number,
			"reference_date": task.custom_reference_date
		}).insert(ignore_permissions=True)

	frappe.db.commit()
