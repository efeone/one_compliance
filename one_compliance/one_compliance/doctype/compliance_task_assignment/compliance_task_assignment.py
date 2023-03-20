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
		create_todo('Task', task.get('task'), task.get('user'), task.get('user'), 'Tasks Assigned Successfully')
