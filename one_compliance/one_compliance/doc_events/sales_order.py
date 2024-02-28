import frappe
from frappe.utils import *
from one_compliance.one_compliance.utils import *
from datetime import datetime, timedelta

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
def create_project_from_sales_order(sales_order, start_date, item_code, priority, expected_end_date=None, remark=None):
    self = frappe.get_doc('Sales Order', sales_order)
    compliance_sub_category = frappe.get_doc('Compliance Sub Category',{'item_code':item_code})
    project_template  = compliance_sub_category.project_template
    project_template_doc = frappe.get_doc('Project Template', project_template)
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
        project = frappe.new_doc('Project')
        project.company = self.company
        project.cost_center = frappe.get_cached_value("Company", self.company, "cost_center")
        project.project_name = self.customer_name + '-' + compliance_sub_category.name + '-' + self.name + '-' + str(naming)
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
        project.save(ignore_permissions=True)
        frappe.db.commit()
        frappe.msgprint('Project Created for {0}.'.format(compliance_sub_category.name), alert = 1)
        for template_task in project_template_doc.tasks:
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
            if template_task_doc.expected_time:
                task_doc.expected_time = template_task_doc.expected_time
            if template_task.custom_task_duration:
                task_doc.duration = template_task.custom_task_duration
                task_doc.exp_end_date = add_days(start_date, template_task.custom_task_duration)
            task_doc.save(ignore_permissions=True)
            if template_task.type and template_task.employee_or_group:
                frappe.db.set_value('Task', task_doc.name, 'assigned_to', template_task.employee_or_group)
                if template_task.type == "Employee":
                    employee = frappe.db.get_value('Employee', template_task.employee_or_group, 'user_id')
                    if employee:
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
