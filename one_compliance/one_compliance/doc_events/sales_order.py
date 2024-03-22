import frappe
from frappe.utils import *
from one_compliance.one_compliance.utils import *
from datetime import datetime, timedelta

@frappe.whitelist()
def create_project_on_submit(doc, method):
    assign_to = []
    if(doc.custom_create_project_automatically):
        for employee_list in doc.custom_assign_to:
            employee_name = frappe.get_doc('Employee', employee_list.employee)
            assign_to.append(employee_name.name)
            assign_to_str = json.dumps(assign_to)
        for item in doc.items:
            create_project_from_sales_order(doc.name, doc.custom_expected_start_date, item.item_code, doc.custom_priority, assign_to_str, doc.custom_expected_end_date)

@frappe.whitelist()
def get_compliance_subcategory(item_code):
    # Fetch compliance subcategory based on the item code
    compliance_subcategory = frappe.get_doc('Compliance Sub Category', {'item_code': item_code})
    return {
        'compliance_category': compliance_subcategory.compliance_category,
        'name': compliance_subcategory.name,
        'project_template': compliance_subcategory.project_template
    }

@frappe.whitelist()
def create_project_from_sales_order(sales_order, start_date, item_code, priority, assign_to=None, expected_end_date=None, remark=None):
    if(assign_to):
        employees = json.loads(assign_to)
    self = frappe.get_doc('Sales Order', sales_order)
    compliance_sub_category = frappe.get_doc('Compliance Sub Category',{'item_code':item_code})
    project_template  = compliance_sub_category.project_template
    project_template_doc = frappe.get_doc('Project Template', project_template)
    head_of_department = frappe.db.get_value('Employee', {'employee':compliance_sub_category.head_of_department}, 'user_id')
    if project_template:
        repeat_on = compliance_sub_category.repeat_on
        project_based_on_prior_phase = compliance_sub_category.project_based_on_prior_phase
        previous_month_date = add_months(getdate(start_date), -1)
        naming_year = getdate(previous_month_date).year if project_based_on_prior_phase else getdate(start_date).year
        naming_month = getdate(previous_month_date).strftime("%B") if project_based_on_prior_phase else getdate(start_date).strftime("%B")
        if naming_month in ['January', 'February', 'March']:
            naming_quarter = 'Quarter 1'
        elif naming_month in ['April', 'May', 'June']:
            naming_quarter = 'Quarter 2'
        elif naming_month in ['July', 'August', 'September']:
            naming_quarter = 'Quarter 3'
        else:
            naming_quarter = 'Quarter 4'
        if repeat_on == "Yearly":
            naming = naming_year
        elif repeat_on == "Quarterly":
            naming = str(naming_year) + ' ' + naming_quarter
        else:
            naming = str(naming_year) + ' ' + naming_month
        if not assign_to and not any(template_task.type and template_task.employee_or_group for template_task in project_template_doc.tasks):
            frappe.msgprint("Project can't be created since no assignees are specified in tasks")
        else:
            project = frappe.new_doc('Project')
            project.company = self.company
            project.cost_center = frappe.get_cached_value("Company", self.company, "cost_center")
            add_compliance_category_in_project_name = frappe.db.get_single_value('Compliance Settings', 'add_compliance_category_in_project_name')
            if add_compliance_category_in_project_name:
                project.project_name = self.customer_name + '-' + compliance_sub_category.name + '-' + str(naming)
            else:
                project.project_name = self.customer_name + '-' + compliance_sub_category.sub_category + '-' + str(naming)
            project.customer = self.customer
            project.compliance_sub_category = compliance_sub_category.name
            project.compliance_category = compliance_sub_category.compliance_category
            project.expected_start_date = start_date
            if expected_end_date:
                days_diff = date_diff(getdate(expected_end_date), getdate(start_date))
                if(days_diff > project_template_doc.custom_project_duration):
                    project.expected_end_date = expected_end_date
                else:
                    project.expected_end_date = add_days(start_date, project_template_doc.custom_project_duration)
            else:
                if project_template_doc.custom_project_duration:
                    project.expected_end_date = add_days(start_date, project_template_doc.custom_project_duration)
            project.priority = priority
            project.custom_project_service = compliance_sub_category.name + '-' + str(naming)
            project.notes = remark
            project.sales_order = sales_order
            project.category_type = compliance_sub_category.category_type
            project.department = compliance_sub_category.department
            project.save(ignore_permissions=True)
            if project.compliance_sub_category:
                if compliance_sub_category and compliance_sub_category.head_of_department:
                    todo = frappe.new_doc('ToDo')
                    todo.status = 'Open'
                    todo.allocated_to = head_of_department
                    todo.description = "project  Assign to " + head_of_department
                    todo.reference_type = 'Project'
                    todo.reference_name = project.name
                    todo.assigned_by = frappe.session.user
                    todo.save(ignore_permissions=True)
                    if todo:
                        frappe.msgprint(("Project is assigned to {0}".format(head_of_department)),alert = 1)
            if assign_to:
                user_name = frappe.get_cached_value("User", frappe.session.user, "full_name")
                for employee in employees:
                    user = frappe.db.get_value('Employee', employee, 'user_id')
                    if user and user != head_of_department:
                        create_todo('Project', project.name, user, user, 'Project {0} Assigned Successfully'.format(project.name))
                        create_notification_log('{0} Assigned a New Project {1} to You'.format(user_name, project.name),'Mention', user, 'Project {0} Assigned Successfully'.format(project.name), project.doctype, project.name)
            frappe.msgprint('Project Created for {0}.'.format(compliance_sub_category.name), alert = 1)
            for template_task in reversed(project_template_doc.tasks):
                ''' Method to create task against created project from the Project Template '''
                template_task_doc = frappe.get_doc('Task', template_task.task)
                user_name = frappe.get_cached_value("User", frappe.session.user, "full_name")
                task_doc = frappe.new_doc('Task')
                task_doc.compliance_sub_category = compliance_sub_category.name
                task_doc.subject = template_task.subject
                task_doc.project = project.name
                task_doc.company = project.company
                task_doc.project_name = project.project_name
                task_doc.category_type = project.category_type
                task_doc.exp_start_date = start_date
                task_doc.department = compliance_sub_category.department
                if template_task_doc.expected_time:
                    task_doc.expected_time = template_task_doc.expected_time
                if template_task.custom_task_duration:
                    task_doc.duration = template_task.custom_task_duration
                    task_doc.exp_end_date = add_days(start_date, template_task.custom_task_duration)
                if template_task_doc.depends_on:
                    for depends_task in template_task_doc.depends_on:
                        dependent_task = frappe.get_doc('Task', {'project':project.name,'subject':depends_task.subject}, 'name')
                        task_doc.append("depends_on", {
                            "task": dependent_task.name,
                        })
                task_doc.save(ignore_permissions=True)
                if project.compliance_sub_category:
                    if compliance_sub_category and compliance_sub_category.head_of_department:
                        todo = frappe.new_doc('ToDo')
                        todo.status = 'Open'
                        todo.allocated_to = head_of_department
                        todo.description = "Task Assign to " + head_of_department
                        todo.reference_type = 'Task'
                        todo.reference_name = task_doc.name
                        todo.assigned_by = frappe.session.user
                        todo.save(ignore_permissions=True)
                if assign_to:
                    for employee in employees:
                        user = frappe.db.get_value('Employee', employee, 'user_id')
                        if user and user != head_of_department:
                            create_todo('Task', task_doc.name, user, user, 'Task {0} Assigned Successfully'.format(task_doc.name))
                            create_notification_log('{0} Assigned a New Task {1} to You'.format(user_name, task_doc.name),'Mention', user, 'Task {0} Assigned Successfully'.format(task_doc.name), task_doc.doctype, task_doc.name)
                elif not assign_to and template_task.type and template_task.employee_or_group:
                    frappe.db.set_value('Task', task_doc.name, 'assigned_to', template_task.employee_or_group)
                    if template_task.type == "Employee":
                        employee = frappe.db.get_value('Employee', template_task.employee_or_group, 'user_id')
                        if employee and employee != head_of_department:
                            create_todo('Task', task_doc.name, employee, employee, 'Task {0} Assigned Successfully'.format(task_doc.name))
                            create_notification_log('{0} Assigned a New Task {1} to You'.format(user_name, task_doc.name),'Mention', employee, 'Task {0} Assigned Successfully'.format(task_doc.name), task_doc.doctype, task_doc.name)
                    if template_task.type == "Employee Group":
                        employee_group = frappe.get_doc('Employee Group', template_task.employee_or_group)
                        if employee_group.employee_list:
                            for employee in employee_group.employee_list:
                                create_todo('Task', task_doc.name, employee.user_id, employee.user_id, 'Task {0} Assigned Successfully'.format(task_doc.name))
                                create_notification_log('{0} Assigned a New Task {1} to you'.format(user_name, task_doc.name),'Mention', employee.user_id, 'Task {0} Assigned Successfully'.format(task_doc.name), task_doc.doctype, task_doc.name)

            frappe.db.commit()
    else:
        frappe.throw( title = _('ALERT !!'), msg = _('Project Template does not exist for {0}'.format(compliance_sub_category)))
