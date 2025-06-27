# Copyright (c) 2024, efeone and contributors
# For license information, please see license.txt


import frappe
from frappe import _
from one_compliance.one_compliance.utils import add_custom as add_assign
from frappe.model.document import Document


class InternalProjectManagement(Document):
	
	@frappe.whitelist()
	def create_project(self):
		"""method created a project based on the data selected in Internal Project Management Tool
		Returns:
			str: name of the project
		"""
		if not self.project_name:
			frappe.throw(_("Project Name is Mandatory"))
		new_project = frappe.new_doc("Project")
		new_project.custom_is_internal = 1
		new_project.project_name = f"{self.get('project_name', '')} {self.get('compliance_sub_category', '')} {self.get('posting_date')}"
		new_project.department = self.get("department", "")
		new_project.compliance_sub_category = self.get("compliance_sub_category", "")
		new_project.expected_start_date = self.get("expected_start_date", "")
		new_project.expected_end_date = self.get("expected_end_date", "")
		new_project.project_type = "Internal"
		new_project.priority = self.get("priority", "")
		new_project.status = "Open"
		new_project.flags.ignore_mandatory = True
		new_project.save()
		frappe.msgprint(_(f"Project {new_project.name} Created"), alert=True)

		assign_to_users = []
		for row in self.get("assign_to", []):
			employee = row.get("employee", "")
			employee_user_id = frappe.db.get_value("Employee", employee, "user_id")
			if not employee_user_id:
				frappe.throw(_(f"User ID not found for {employee}"))
			assign_to_users.append(employee_user_id)
		task_details = self.get("task_details", [])
		if not assign_to_users or not task_details:
			frappe.throw("No users or tasks provided for assignment.")

		if assign_to_users:
			for task in task_details:
				task_doc = frappe.new_doc("Task")
				task_doc.update(
					{
						"project": new_project.name,
						"subject": f"{task.get('subject')}",
						"status": "Open",
						"type": task.get("type"),
						"custom_task_duration": task.get("custom_task_duration"),
						"employee_or_group": task.get("employee_or_group"),
					}
				)
				task_doc.save(ignore_permissions=True)
				add_assign(
					{
						"doctype": "Task",
						"name": task_doc.name,
						"assign_to": assign_to_users,
					}
				)
			add_assign(
				{
					"doctype": "Project",
					"name": new_project.name,
					"assign_to": assign_to_users,
				}
			)
		frappe.msgprint(_("Tasks created and assigned to users."), alert=True)
		return new_project.name



@frappe.whitelist()
def task_assign(compliance_sub_category):
	"""method fetches and returns the list of tasks from project template of a compliance sub category

	Args:
		compliance_sub_category (str): name of the compliance sub category

	Returns:
		list: list of tasks in project template of the given compliance sub category
	"""
	sub_category = compliance_sub_category
	if sub_category:
		project_template_name = frappe.db.get_value(
			"Compliance Sub Category", {"name": sub_category}, "project_template"
		)
		if project_template_name:
			project_template_doc = frappe.get_doc(
				"Project Template", project_template_name
			)
			tasks = []
			for task in project_template_doc.tasks:
				tasks.append(
					{
						"task": task.task,
						"subject": task.subject,
						"type": task.type,
						"custom_task_duration": task.custom_task_duration,
						"employee_or_group": task.employee_or_group,
					}
				)
			return tasks
