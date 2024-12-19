import frappe
from frappe.desk.form.assign_to import add as add_assignment


def assign_project_tasks(doc, method=None):
    if not doc.reference_type == "Project":
        return
    if not frappe.db.exists("Project", doc.reference_name):
        return
    if "has requested to extend the date of Project" in doc.description:
        return
    tasks = frappe.db.get_all("Task", {"project": doc.reference_name}, pluck="name")
    for task in tasks:
        print(doc.allocated_to, task, doc.description)
        add_assignment(
            {
                "assign_to": [doc.allocated_to],
                "doctype": "Task",
                "name": task,
                "description": doc.description,
            }
        )
