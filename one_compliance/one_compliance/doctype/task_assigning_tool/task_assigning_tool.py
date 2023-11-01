# Copyright (c) 2023, efeone and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import json
from frappe import _

class TaskAssigningTool(Document):
	pass

@frappe.whitelist()
def get_users_by_department(doctype, txt, searchfield, start, page_len, filters):
    # Query the Employee doctype to filter users by department
    employees = frappe.get_all("Employee",
        filters={"department": filters.get("department")},
        fields=["user_id"]
    )

    # Get a list of user IDs from the filtered employees
    user_ids = [employee.user_id for employee in employees]

    # Query the User doctype to fetch users based on user_id
    users = frappe.get_all("User",
        filters={"email": ["in", user_ids], "enabled": 1},
        fields=["name", "full_name"]
    )

    user_info_list = []  # Initialize an empty list to store user information

    for user in users:
        email = user['name']  # Use 'user' instead of 'users'
        full_name = user['full_name']  # Use 'user' instead of 'users'

        user_info_list.append((email, full_name))  # Add email and full name as a tuple to the list

    return user_info_list  # Return the list of email IDs and full names as tuples

@frappe.whitelist()
def get_tasks_for_user(assign_from):
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
def reassign_tasks(assign_from, assign_to, selected_tasks_json):
    # Load the JSON data from selected_tasks_json
    selected_tasks = json.loads(selected_tasks_json)

    print(selected_tasks)  # This will print the selected_tasks array

    for task_id in selected_tasks:
        print(type(task_id), task_id)  # This will print each task_id in the selected_tasks array

        # Get the reference name of the 'ToDo' document associated with the selected task
        todo_reference_name = frappe.get_value('ToDo', {'reference_name': task_id, 'reference_type': 'Task'}, 'name')

        if todo_reference_name:
            # Update the 'allocated_to' field in the 'ToDo' document
            frappe.db.set_value('ToDo', todo_reference_name, 'allocated_to', assign_to)

    # Save changes
    frappe.db.commit()

    # Return a success message
    return "Tasks reassigned successfully"

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
