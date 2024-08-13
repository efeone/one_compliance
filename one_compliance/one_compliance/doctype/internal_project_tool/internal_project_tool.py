import frappe
import json
from frappe.model.document import Document
from frappe.utils import today
from frappe.desk.form.assign_to import add as add_assign

class InternalProjectTool(Document):
    pass

@frappe.whitelist()
def create_project(doc_data):
    doc_data = json.loads(doc_data)
    new_project = frappe.new_doc("Project")
    new_project.project_name = f"{doc_data.get('project_name', '')} {doc_data.get('sub_category', '')} {today()}"
    new_project.department = doc_data.get('department', '')
    new_project.compliance_sub_category = doc_data.get('sub_category', '')
    new_project.expected_start_date = doc_data.get('start_date', '')
    new_project.expected_end_date = doc_data.get('end_date', '')
    new_project.category_type = doc_data.get('category_type', '')
    new_project.priority = 'Medium'
    new_project.status = 'Open'
    new_project.flags.ignore_mandatory = True
    new_project.save()
    frappe.db.commit()
    frappe.msgprint((f'Project {new_project.name} Created'), alert=True)

    assign_to_users = [user.get('user') for user in doc_data.get('assign_to', [])]
    tasks = doc_data.get('tasks', [])

    if not assign_to_users or not tasks:
        frappe.throw("No users or tasks provided for assignment.")

    if len(assign_to_users) == 1:
        user = assign_to_users[0]
        for task in tasks:
            task_doc = frappe.new_doc("Task")
            task_doc.update({
                'project': new_project.name,
                'subject': f"{task.get('subject')} - {user}",
                'status': 'Open',
                'type': task.get('type'),
                'custom_task_duration': task.get('custom_task_duration'),
                'employee_or_group': task.get('employee_or_group')
            })
            task_doc.save(ignore_permissions=True)
            add_assign({"doctype": "Task", "name": task_doc.name, "assign_to": [user]})
    else:
        # Multiple users case: distribute tasks among users, handling any mismatch
        for i, task in enumerate(tasks):
            user = assign_to_users[i % len(assign_to_users)]
            task_doc = frappe.new_doc("Task")
            task_doc.update({
                'project': new_project.name,
                'subject': f"{task.get('subject')} - {user}",
                'status': 'Open',
                'type': task.get('type'),
                'custom_task_duration': task.get('custom_task_duration'),
                'employee_or_group': task.get('employee_or_group')
            })
            task_doc.save(ignore_permissions=True)
            add_assign({"doctype": "Task", "name": task_doc.name, "assign_to": [user]})

    frappe.db.commit()
    frappe.msgprint(f'Tasks created and assigned to users.', alert=True)
    return new_project.name

@frappe.whitelist()
def task_assign(docs):
    docs = json.loads(docs)
    sub_category = docs.get('sub_category')
    if sub_category:
        project_template_name = frappe.db.get_value('Compliance Sub Category', {'name': sub_category}, 'project_template')
        if project_template_name:
            project_template_doc = frappe.get_doc('Project Template', project_template_name)
            tasks = []
            for task in project_template_doc.tasks:
                tasks.append({
                    'task': task.task,
                    'subject': task.subject,
                    'type': task.type,
                    'custom_task_duration': task.custom_task_duration,
                    'employee_or_group': task.employee_or_group
                })
            return tasks
