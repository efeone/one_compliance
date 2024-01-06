# Copyright (c) 2023, efeone and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import json
from frappe import _
from frappe.desk.form.assign_to import add as add_assignment

class TaskReassignment(Document):
	@frappe.whitelist()
	def get_allocation_entries(self):
		self.prepare_task_reassign()
		self.get_employee_list()
		return 'success'

	@frappe.whitelist()
	def prepare_task_reassign(self):
		all_tasks = self.get_all_tasks()

		self.add_task_entries(all_tasks)

	@frappe.whitelist()
	def add_task_entries(self, tasks):
		self.set("task_reassigns", [])

		for task in tasks:
			task_reassign = self.append("task_reassigns", {})
			task_reassign.task_id = task.get("name")
			task_reassign.subject = task.get("subject")
			task_reassign.project = task.get("project_name")
			task_reassign.compliance_sub_category = task.get("compliance_sub_category")

	@frappe.whitelist()
	def get_all_tasks(self, department=None, category=None, subcategory=None, assigned_to=None):
	    filters = {'status': 'Open'}

	    # Adding optional filters if provided
	    if self.department:
	        subcategories = frappe.get_all(
	            'Compliance Sub Category',
	            filters={'department': self.department},
	            fields=['name']
	        )
	        # Fetch all tasks linked to those Compliance Subcategories
	        subcategory_names = [sub['name'] for sub in subcategories]
	        filters['compliance_sub_category'] = ['in', subcategory_names]
	    if self.category:
	        subcategories = frappe.get_all(
	            'Compliance Sub Category',
	            filters={'compliance_category': self.category},
	            fields=['name']
	        )
	        # Fetch all tasks linked to those Compliance Subcategories
	        subcategory_names = [sub['name'] for sub in subcategories]
	        filters['compliance_sub_category'] = ['in', subcategory_names]
	    if self.sub_category:
	        filters['compliance_sub_category'] = self.sub_category

	    # Fetch tasks based on filters
	    all_tasks = frappe.get_all(
	        'Task',
	        filters=filters,
	        fields=['name', 'subject', 'project_name', 'compliance_sub_category']
	    )

	    if self.assigned_to:
	        # Fetch tasks allocated to the specified 'assigned_to'
	        assigned_tasks = self.fetch_tasks_by_assign_from(self.assigned_to)
	        task_ids_assigned_to = [task['task_id'] for task in assigned_tasks]

	        # Filter the fetched tasks to only include those assigned to 'assigned_to'
	        filtered_tasks = [task for task in all_tasks if task['name'] in task_ids_assigned_to]
	        return filtered_tasks

	    return all_tasks

	@frappe.whitelist()
	def fetch_tasks_by_assign_from(self, assign_from):
	    # Query tasks from the ToDo doctype
	    tasks = frappe.get_all('ToDo', filters={'allocated_to': assign_from, 'status': 'Open'}, fields=['reference_type', 'reference_name', 'description'])

	    task_details = []

	    for task in tasks:
	        reference_type = task.reference_type
	        reference_id = task.reference_name
	        task_description = task.description

	        if reference_type == 'Task':
	            # Fetch details from the Task doctype based on the task_id
	            task_details_query = frappe.get_all('Task', filters={'name': reference_id}, fields=['subject', 'project'])
	            if task_details_query:
	                task_details.append({
	                    'task_id': reference_id,
	                    'subject': task_details_query[0]['subject'],
	                    'project': task_details_query[0]['project']
	                })
	        elif reference_type == 'Project':
	            # Fetch task details from the Task doctype based on the project_name
	            tasks_for_project = frappe.get_all('Task', filters={'project': reference_id}, fields=['name', 'project', 'subject'])
	            project_task_details = []
	            for task in tasks_for_project:
	                project_task_details.append({
	                    'task_id': task.name,
	                    'subject': task.subject,
	                    'project': task.project
	                })
	            task_details.extend(project_task_details)

	    return task_details

	@frappe.whitelist()
	def get_employee_list(self, department=None):
	    filters = {}

	    # Check if a department is specified
	    if self.department:
	        filters['department'] = self.department  # Add department filter if specified

	    # Query users who are employees based on filters
	    employees = frappe.get_all(
	        'Employee',
	        filters=filters,
	        fields=['name', 'employee_name', 'designation', 'department']
	    )

	    self.add_employee_entries(employees)

	def add_employee_entries(self, employees):
		self.set("assign_to", [])

		for employee in employees:
			row = self.append("assign_to", {})
			row.employee = employee.get("name")
			row.designation = employee.get("designation")
			row.employee_name = employee.get("employee_name")
			row.department = employee.get("department")


@frappe.whitelist()
def get_users_by_department(doctype, txt, searchfield, start, page_len, filters):
    # Query the Employee doctype to filter users by department
    employees = frappe.get_all("Employee",
        filters={"department": filters.get("department")},
        fields=["user_id"]
    )

    # Get a list of user IDs from the filtered employees
    user_ids = [employee.user_id for employee in employees]

    users = frappe.get_all("User",
        filters={"email": ["in", user_ids], "enabled": 1},
        fields=["name", "full_name"]
    )

    user_info_list = []

    for user in users:
        email = user['name']
        full_name = user['full_name']

        user_info_list.append((email, full_name))

    return user_info_list

@frappe.whitelist()
def get_subcategories_by_department(doctype, txt, searchfield, start, page_len, filters):

    compliance_categories = frappe.get_all(
        "Compliance Category",
        filters={"department": filters.get("department")},
        fields=["name"]
    )

    sub_category_list = []

    # Fetch ComplianceSubCategory based on the ComplianceCategories found
    for category in compliance_categories:
        sub_categories = frappe.get_all(
            "Compliance Sub Category",
            filters={"compliance_category": category.name},
            fields=["name", "sub_category"]
        )

        # Accumulate subcategories in the list
        for sub_category in sub_categories:
            name = sub_category['name']
            sub_category_name = sub_category['sub_category']
            sub_category_list.append((name, sub_category_name))

    return sub_category_list

@frappe.whitelist()
def get_subcategories_by_category(doctype, txt, searchfield, start, page_len, filters):
	sub_category_list = []
	subcategories = frappe.get_all(
		"Compliance Sub Category",
		filters={"compliance_category": filters.get("category")},
		fields=["name", "sub_category"]
	)
	for sub_category in subcategories:
		name = sub_category['name']
		sub_category_name = sub_category['sub_category']
		sub_category_list.append((name, sub_category_name))

	return sub_category_list

@frappe.whitelist()
def get_subcategories_by_department_and_category(doctype, txt, searchfield, start, page_len, filters):
	sub_category_list = []
	subcategories = frappe.get_all(
		"Compliance Sub Category",
		filters={"department": filters.get("department"), "compliance_category": filters.get("category")},
		fields=["name", "sub_category"]
	)
	for sub_category in subcategories:
		name = sub_category['name']
		sub_category_name = sub_category['sub_category']
		sub_category_list.append((name, sub_category_name))

	return sub_category_list

@frappe.whitelist()
def get_categories_by_department(doctype, txt, searchfield, start, page_len, filters):
	compliance_categories = frappe.get_all("Compliance Category",
		filters={"department": filters.get("department")},
		fields=["name", "department"]
	)

	category_list = []

	for category in compliance_categories:
		name = category['name']
		department = category['department']

		category_list.append((name, department))

	return category_list

@frappe.whitelist()
def allocate_tasks_to_employee(selected_task_ids, selected_employee_ids):
	print(selected_task_ids)
	print(selected_employee_ids)
	for task_id in json.loads(selected_task_ids):
		for employee_id in json.loads(selected_employee_ids):
			# Get the user_id from Employee doctype based on the employee_id
			user_id = frappe.get_value('Employee', employee_id, 'user_id')

			if user_id:

				# Add assignment for the ToDo
				add_assignment({"doctype": "Task", "name": task_id, "assign_to": [user_id]})

	# Return a success message
	return "Tasks allocated successfully"

@frappe.whitelist()
def get_compliance_categories_for_user(doctype, txt, searchfield, start, page_len, filters):
    user_id = filters.get('user_id')
    print(user_id)

    # Find the Employee based on the user_id
    employee = frappe.get_doc("Employee", {"user_id": user_id})

    if employee:
        # Get the department of the employee
        department = employee.department

        # Query the Compliance Category DocType
        compliance_categories = frappe.get_all("Compliance Category", filters={"department": department}, fields=["name", "department"])

        category_names = []  # Initialize an empty list to store user information

        for category in compliance_categories:
            name = category['name']
            department = category['department']

            category_names.append((name, department))  # Add email and full name as a tuple to the list

        return category_names  # Return the list of email IDs and full names as tuples
    return []

import frappe

@frappe.whitelist()
def get_compliance_executives(compliance_category):
    child_table_data = frappe.get_all(
        'Compliance Executive',
        filters={'parent': compliance_category},
        fields=['employee', 'designation', 'employee_name']
    )
    return child_table_data

@frappe.whitelist()
def add_employee_to_compliance_executive(employee, compliance_category):
    try:
        # Check if the employee and compliance category exist
        employee_doc = frappe.get_doc("Employee", {"user_id": employee})
        compliance_category_doc = frappe.get_doc("Compliance Category", compliance_category)

        if employee_doc and compliance_category_doc:
            # Check if the employee is already in the Compliance Executive table for the category
            existing_executive = None
            for executive in compliance_category_doc.compliance_executive:
                if executive.employee == employee_doc.name:
                    existing_executive = executive
                    break

            if not existing_executive:
                # Create a new "Compliance Executive" document and set its fields
                executive = frappe.new_doc("Compliance Executive")
                executive.employee = employee_doc.name
                executive.designation = employee_doc.designation
                executive.employee_name = employee_doc.employee_name

                # Append the new executive to the Compliance Executive table
                compliance_category_doc.append("compliance_executive", executive)

                # Save the Compliance Category document with the updated table
                compliance_category_doc.save()

                frappe.db.commit()
                return True
            else:
                frappe.msgprint("Employee is already existing")
                return False  # Employee is already in the table
        else:
            return False  # Employee or Compliance Category does not exist
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), _("Error in adding employee to Compliance Executive"))
        return False

@frappe.whitelist()
def get_available_subcategories(compliance_category, employee):
    # Query the database to retrieve subcategories related to the selected category
    subcategories = frappe.get_all(
        "Compliance Sub Category",
        filters={"compliance_category": compliance_category},
        fields=["name"]
    )

    # Check if the employee exists in the compliance executive of each subcategory
    employee_doc = frappe.get_doc("Employee", {"user_id": employee})
    for subcategory in subcategories:
        compliance_subcategory_doc = frappe.get_doc("Compliance Sub Category", subcategory["name"])

        is_added = False
        for executive in compliance_subcategory_doc.compliance_executive:
            if executive.employee == employee_doc.name:
                is_added = True
                break

        subcategory["status"] = "added" if is_added else "not added"

    return subcategories

@frappe.whitelist()
def add_to_subcategories(employee, compliance_category, selected_subcategories):

    try:
        # Check if the employee and compliance category exist
        employee_doc = frappe.get_doc("Employee", {"user_id": employee})
        compliance_category_doc = frappe.get_doc("Compliance Category", compliance_category)
        compliance_subcategories = json.loads(selected_subcategories)

        if employee_doc and compliance_category_doc:
            for subcategory in compliance_subcategories:

                compliance_subcategory_doc = frappe.get_doc("Compliance Sub Category", {"name": subcategory})

                if compliance_subcategory_doc:

                    existing_executive = None
                    for executive in compliance_subcategory_doc.compliance_executive:
                        if executive.employee == employee_doc.name:
                            existing_executive = executive
                            break

                    if not existing_executive:
                        # Create a new "Compliance Executive" document and set its fields
                        executive = frappe.new_doc("Compliance Executive")
                        executive.employee = employee_doc.name
                        executive.designation = employee_doc.designation
                        executive.employee_name = employee_doc.employee_name

                        # Append the new executive to the Compliance Executive table
                        compliance_subcategory_doc.append("compliance_executive", executive)

                        # Save the Compliance Sub Category document with the updated table
                        compliance_subcategory_doc.save()

            frappe.db.commit()
            return True
        else:
            return False
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), _("Error in adding employee to Compliance Sub Categories"))
        return False
