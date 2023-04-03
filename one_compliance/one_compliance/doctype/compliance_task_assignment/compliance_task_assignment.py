		# Copyright (c) 2023, efeone and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from one_compliance.one_compliance.utils import *
import json

class ComplianceTaskAssignment(Document):
	pass

@frappe.whitelist()
def assign_tasks_to_selected_users(task_details):
	''' Method to assign task to the selected users '''
	task_details = json.loads(task_details)
	for task in task_details:
		frappe.db.set_value('Task',task.get('task'),'assigned_to',task.get('employee_or_group'))
		if task.get('type') == 'Employee' and task.get('employee_or_group'):
			employee = frappe.db.get_value('Employee',task.get('employee_or_group'),'user_id')
			if employee:
				create_todo('Task', task.get('task'),employee, employee, 'Tasks Assigned Successfully')
		if task.get('type') == 'Employee Group' and task.get('employee_or_group'):
			if frappe.db.exists('Employee Group',task.get('employee_or_group')):
				employee_group = frappe.get_doc('Employee Group',task.get('employee_or_group'))
				if employee_group.employee_list:
					for employee in employee_group.employee_list:
						create_todo('Task', task.get('task'),employee.user_id, employee.user_id, 'Tasks Assigned Successfully')
		frappe.db.commit()
		''' To set Alert message below '''
	frappe.msgprint(
		msg = 'Tasks assigned Successfully', alert =1
	 )
