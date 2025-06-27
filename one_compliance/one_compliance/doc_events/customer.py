import frappe
import json
from frappe.model.mapper import *
from frappe import _
from frappe.utils.user import get_users_with_role
from one_compliance.one_compliance.utils import add_custom as add_assignment
from one_compliance.one_compliance.utils import *
from frappe.email.doctype.notification.notification import get_context

@frappe.whitelist()
def set_customer_type_value(doc):
    '''
        Method used to set value in standard hidden field
    '''
    if doc.compliance_customer_type:
        if doc.compliance_customer_type == 'Individual':
            doc.customer_type = 'Individual'
        else:
            doc.customer_type = 'Company'

@frappe.whitelist()
def set_allow_edit(customer_contacts):
    customer_contacts = json.loads(customer_contacts)
    user = frappe.session.user
    user_roles = frappe.get_roles(user)
    for cu in customer_contacts:
        if "Director" in user_roles or "Compliance Manager" in user_roles:
            frappe.db.set_value('Customer Contacts',cu.get('name'),'allow_edit',1)
            frappe.db.commit()
        else:
            frappe.db.set_value('Customer Contacts',cu.get('name'),'allow_edit',0)
            frappe.db.commit()
    return True

@frappe.whitelist()
def create_agreement_custom_button(source_name, target_doc = None):
    def set_missing_values(source, target):
        target.customer_name= source.customer_name
        target.lead_name = source.lead_name
        target.opportunity_name= source.opportunity_name
    doc = get_mapped_doc(
        'Customer',
        source_name,
        {
        'Customer': {
        'doctype': 'Compliance Agreement',
        },
        },target_doc,set_missing_values)
    return doc

@frappe.whitelist()
def create_project_custom_button(source_name, target_doc = None):
    def set_missing_values(source, target):
        target.customer_name= source.customer_name
        target.lead_name = source.lead_name
        target.opportunity_name= source.opportunity_name
    doc = get_mapped_doc(
        'Customer',
        source_name,
        {
        'Customer': {
        'doctype': 'Project',
        },
        },target_doc,set_missing_values)
    return doc



@frappe.whitelist()
def create_payment_entry(mode_of_payment, paid_amount, customer):
    new_pe_doc = frappe.new_doc('Payment Entry')
    new_pe_doc.party_type = 'Customer'
    new_pe_doc.party = customer
    new_pe_doc.mode_of_payment = mode_of_payment
    new_pe_doc.paid_amount = paid_amount
    new_pe_doc.save()
    return new_pe_doc.name

@frappe.whitelist()
def filter_contact(doctype, txt, searchfield, start, page_len, filters):
    '''
        Method used to filter contact
    '''
    if filters:
        query = """
            SELECT
                c.name
            FROM
                `tabDynamic Link` as dl,
                `tabContact` as c
            WHERE
                dl.link_doctype = "Customer" AND
                dl.link_name = %(customer_name)s AND
                dl.parent = c.name
            LIMIT %(start)s, %(page_len)s
        """
        values = frappe.db.sql(query.format(**{
        }), {
            'customer_name': filters['customer_name'],
            'txt': "%{}%".format(txt),
            'start': start,
            'page_len': page_len
        })
        return values

def customer_on_update(doc, method):
    '''
        Method trigger on on_update of customer.
    '''
    set_customer_type_value(doc)
    create_user_from_customer(doc)

def create_user_from_customer(doc):
    create_user_on_customer_creation = frappe.db.get_single_value('Compliance Settings', 'create_user_on_customer_creation')
    if create_user_on_customer_creation:
        if doc.email_id:
            if not frappe.db.exists('User', doc.email_id):
                user_doc = frappe.new_doc('User')
                user_doc.email = doc.email_id
                user_doc.first_name = doc.customer_name
                user_doc.save(ignore_permissions = True)
                frappe.msgprint('User created for this customer', alert=True, indicator='green')

@frappe.whitelist()
def custom_button_for_view_compliance_agreement(customer):
    if frappe.db.exists('Compliance Agreement', {'customer':customer, 'status':'Active'}):
        compliance_agreement = frappe.db.get_value('Compliance Agreement', {'customer':customer, 'status':'Active'})
        return compliance_agreement
    else:
        return 0

@frappe.whitelist()
def custom_button_for_view_project(customer):
    if frappe.db.exists('Project', {'customer':customer}):
        return 1
    else:
        return 0


@frappe.whitelist()
def custom_button_for_view_payment(party_type, party):
    if frappe.db.exists('Payment Entry', {'party_type':party_type, 'party':party}):
        return 1
    else:
        return 0

@frappe.whitelist()
def send_clarification_message(customer,message):
    doc = frappe.get_doc('Customer',customer)
    recipient =doc.email_id
    subject = "Clarification Request"
    body = "Dear {},\n\nWe are writing to request clarification on the following matter: {}".format(customer, message)
    frappe.sendmail(recipients=[recipient],subject=subject, message=body)
    frappe.msgprint(
		msg = 'Mail Send', alert =1
	 )

@frappe.whitelist()
def check_invoice_based_on_and_project_status(customer):
    if frappe.db.exists('Compliance Agreement',{'customer':customer,'status':'Active'}):
        invoice_based_on, compliance_agreement = frappe.db.get_value('Compliance Agreement',{'customer':customer,'status':'Active'}, ['invoice_based_on','name'])
        if invoice_based_on and invoice_based_on == 'Consolidated':
            if frappe.db.exists('Project',{'customer':customer,'compliance_agreement':compliance_agreement,'status':'Completed'}):
                return True

@frappe.whitelist()
def make_sales_invoice(source_name, target_doc=None):
    #Method to create sales_invoice when invoice_based_on is Consolidated
    def set_missing_values(source, target):
        compliance_agreement = frappe.get_doc('Compliance Agreement',{'customer':source_name, 'status':'Active'})
        company = frappe.db.get_value('Project',{'customer':source_name,'compliance_agreement':compliance_agreement.name},'company')
        if company:
            income_account = frappe.db.get_value('Company',company, 'default_income_account')
        if compliance_agreement.compliance_category_details:
            for sub_category in compliance_agreement.compliance_category_details:
                is_billable = frappe.db.get_value('Compliance Sub Category', sub_category.compliance_category, 'is_billable')
                if is_billable:
                    rate = calculate_rate(compliance_agreement.compliance_category_details, sub_category.compliance_category)
                    if compliance_agreement.invoice_based_on == 'Consolidated':
                        if not check_exist(target, sub_category.compliance_category):
                            if source.payment_terms:
                                target.append('items', {
                                    'item_name' : sub_category.compliance_category,
                                    'rate' : rate,
                                    'qty' : 1,
                                    'income_account' : income_account,
                                    'description' : sub_category.name,
                                    'default_payment_terms_template' : source.payment_terms,
                                })
                            else:
                                target.append('items', {
                                    'item_name' : sub_category.compliance_category,
                                    'rate' : rate,
                                    'qty' : 1,
                                    'income_account' : income_account,
                                    'description' : sub_category.name,
                                })
    doclist = get_mapped_doc(
    'Customer',
    source_name,
        {
        'Customer':{
            'doctype':'Sales Invoice'

            },
        },
    target_doc,
        set_missing_values
    )
    doclist.save()
    return doclist

def check_exist(target, compliance_category):
    ''' checking if item already exist in child table '''
    exist = False
    if target.items:
        for item in target.items:
            if compliance_category:
                if item.item_name == compliance_category:
                    exist = True
                    break
    return exist

def calculate_rate(compliance_category_details, compliance_category):
	rate = 0
	for category in compliance_category_details:
		if category.compliance_category == compliance_category:
			rate += category.rate
	return rate

def create_task_from_opportunity(doc, method):
    if(doc.opportunity_name):
        opportunity = frappe.get_doc('Opportunity',doc.opportunity_name)
        if(opportunity.custom_documents_required):
            for document_required in opportunity.custom_documents_required:
                task = frappe.new_doc('Task')
                task.subject = document_required.document_required
                task.custom_serial_number = document_required.idx
                task.insert(ignore_permissions = True)

                user_id = frappe.get_value('Employee', document_required.responsibilities, 'user_id')
                add_assignment({"doctype": "Task", "name": task.name, "assign_to": [user_id]})

def create_project_from_customer(doc, method=None):
    customer_type = doc.compliance_customer_type
    regularisation_process = frappe.get_value('Customer Type', {'name':customer_type}, ['regularisation_process'])
    if regularisation_process and doc.custom_annual_general_meeting_date:
        for legal_authority in doc.custom_legal_authority_list:
            if legal_authority.is_regularised == 0 and legal_authority.appointment_date:
                if getdate(legal_authority.appointment_date) < getdate(doc.custom_annual_general_meeting_date) and getdate(doc.custom_annual_general_meeting_date) == getdate(today()):
                    company_list = frappe.get_all("Company")
                    company = frappe.get_doc("Company", company_list)
                    if frappe.get_doc('Compliance Settings').get('din_kyc_sub_category'):
                        sub_category = frappe.db.get_single_value("Compliance Settings", 'din_kyc_sub_category')
                        compliance_sub_category = frappe.get_doc('Compliance Sub Category', sub_category)
                        project_template  = compliance_sub_category.project_template
                        project_template_doc = frappe.get_doc('Project Template', project_template)
                        head_of_department = frappe.db.get_value('Employee', {'employee':compliance_sub_category.head_of_department}, 'user_id')
                        if project_template:
                            repeat_on = compliance_sub_category.repeat_on
                            project_based_on_prior_phase = compliance_sub_category.project_based_on_prior_phase
                            previous_month_date = add_months(getdate(doc.custom_annual_general_meeting_date), -1)
                            naming_year = getdate(previous_month_date).year if project_based_on_prior_phase else getdate(doc.custom_annual_general_meeting_date).year
                            naming_month = getdate(previous_month_date).strftime("%B") if project_based_on_prior_phase else getdate(doc.custom_annual_general_meeting_date).strftime("%B")
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
                            project.company = company
                            add_compliance_category_in_project_name = frappe.db.get_single_value('Compliance Settings', 'add_compliance_category_in_project_name')
                            if add_compliance_category_in_project_name:
                                project.project_name = doc.customer_name + '-' + compliance_sub_category.name + '-' + str(naming)
                            else:
                                project.project_name = doc.customer_name + '-' + 'DIN' + '-' +compliance_sub_category.sub_category + '-' + str(naming)

                            project.project_name = project.project_name+ '-' + legal_authority.legal_authority
                            project.customer = doc.customer_name
                            project.compliance_sub_category = compliance_sub_category.name
                            project.compliance_category = compliance_sub_category.compliance_category
                            project.expected_start_date = doc.custom_annual_general_meeting_date
                            project.priority = 'Low'
                            project.custom_project_service = compliance_sub_category.name + '-' + str(naming)
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
                            frappe.db.commit()
                            frappe.msgprint('Project Created for {0}.'.format(compliance_sub_category.name), alert = 1)
                            for template_task in reversed(project_template_doc.tasks):
                                ''' Method to create task against created project from the Project Template '''
                                template_task_doc = frappe.get_doc('Task', template_task.task)
                                user_name = frappe.get_cached_value("User", frappe.session.user, "full_name")
                                task_doc = frappe.new_doc('Task')
                                task_doc.compliance_sub_category = compliance_sub_category.name
                                task_doc.subject = template_task.subject
                                task_doc.project = project.name
                                task_doc.project_name = project.project_name
                                task_doc.category_type = project.category_type
                                task_doc.exp_start_date = doc.custom_annual_general_meeting_date
                                task_doc.custom_serial_number = template_task.idx
                                task_doc.department = compliance_sub_category.department
                                if template_task_doc.expected_time:
                                    task_doc.expected_time = template_task_doc.expected_time
                                if template_task.custom_task_duration:
                                    task_doc.duration = template_task.custom_task_duration
                                    task_doc.exp_end_date = exp_end_date
                                if template_task_doc.depends_on:
                                    for depends_task in template_task_doc.depends_on:
                                        dependent_task = frappe.get_doc('Task', {'project':project.name,'subject':depends_task.subject}, 'name')
                                        task_doc.append("depends_on", {
                                            "task": dependent_task.name,
                                        })
                                task_doc.save(ignore_permissions=True)
                                if template_task.type and template_task.employee_or_group:
                                    frappe.db.set_value('Task', task_doc.name, 'assigned_to', template_task.employee_or_group)
                                    if template_task.type == "Employee":
                                        employee = frappe.db.get_value('Employee', template_task.employee_or_group, 'user_id')
                                        if employee and employee != head_of_department:
                                            create_todo('Task', task_doc.name, employee, employee, 'Task {0} Assigned Successfully'.format(task_doc.name))
                                    if template_task.type == "Employee Group":
                                        employee_group = frappe.get_doc('Employee Group', template_task.employee_or_group)
                                        if employee_group.employee_list:
                                            for employee in employee_group.employee_list:
                                                create_todo('Task', task_doc.name, employee.user_id, employee.user_id, 'Task {0} Assigned Successfully'.format(task_doc.name))

                                frappe.db.commit()
                        else:
                            frappe.throw( title = _('ALERT !!'), msg = _('Project Template does not exist for {0}'.format(compliance_sub_category)))
                    else:
                        frappe.throw( title = _('ALERT !!'), msg = _('Sub Category is not selected'))

@frappe.whitelist()
def create_project_from_customer_scheduler():
    customers = frappe.db.get_all('Customer', filters = {'disabled': 'No'})
    if customers:
        for customer in customers:
            doc = frappe.get_doc('Customer', customer.name)
            create_project_from_customer(doc)
            send_expiry_notif_and_create_proj(doc)
            send_mail_to_auditors(doc)

def send_mail_to_auditors(company_auditor):
    if frappe.db.exists('Company Auditor', company_auditor):
        doc = frappe.get_doc('Company Auditor', company_auditor)
        recipient = doc.email_id
        customer = doc.name
        subject = "Appointment Date Expiration"
        body = "Dear {0},\n\nYour Appointment will expirie in 20 days.".format(customer)
        frappe.sendmail(recipients=[recipient], subject=subject, message=body)
        frappe.msgprint(
    		msg = 'Mail Send', alert =1
    	 )


def set_expiry_dates(doc, method=None):
    for row in doc.custom_audit_list:
        if row.appoint_date:
            row.expiry_date = frappe.utils.add_years(row.appoint_date, 5)
            row.notify_before_expiry_date = frappe.utils.add_days(row.expiry_date, -20)

def send_expiry_notif_and_create_proj(doc, method=None):
    customer_type = doc.compliance_customer_type
    auditing_process = frappe.get_value('Customer Type', {'name':customer_type}, ['auditing_process'])
    if auditing_process and doc.custom_audit_list:
        for audit in doc.custom_audit_list:
            expiry_date = audit.notify_before_expiry_date
            if getdate(expiry_date) == getdate(today()):
                sub_category = frappe.db.get_single_value("Compliance Settings", 'din_kyc_sub_category')
                compliance_sub_category = frappe.get_doc('Compliance Sub Category', sub_category)
                company_list = frappe.defaults.get_user_default("company")
                company = frappe.get_doc("Company", company_list)
                project_template  = compliance_sub_category.project_template
                project_template_doc = frappe.get_doc('Project Template', project_template)
                head_of_department = frappe.db.get_value('Employee', {'employee':compliance_sub_category.head_of_department}, 'user_id')
                if project_template:
                    repeat_on = compliance_sub_category.repeat_on
                    project_based_on_prior_phase = compliance_sub_category.project_based_on_prior_phase
                    previous_month_date = add_months(getdate(expiry_date), -1)
                    naming_year = getdate(previous_month_date).year if project_based_on_prior_phase else getdate(expiry_date).year
                    naming_month = getdate(previous_month_date).strftime("%B") if project_based_on_prior_phase else getdate(expiry_date).strftime("%B")
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
                    # project_name = ''
                    # add_compliance_category_in_project_name = frappe.db.get_single_value('Compliance Settings', 'add_compliance_category_in_project_name')
                    # if add_compliance_category_in_project_name:
                    #     project_name = doc.customer_name + '-' + compliance_sub_category.name + '-' + str(naming)
                    # else:
                    #     project_name = doc.customer_name + '-' + 'DIN' + '-' +compliance_sub_category.sub_category + '-' + str(naming)
                    project_name = doc.customer_name + '-' + audit.firm_name
                    if not frappe.db.exists('Project', { 'project_name':project_name }):
                        project = frappe.new_doc('Project')
                        project.company = company
                        project.project_name = project_name
                        project.customer = doc.customer_name
                        project.compliance_sub_category = compliance_sub_category.name
                        project.compliance_category = compliance_sub_category.compliance_category
                        project.expected_start_date = expiry_date
                        project.priority = 'Low'
                        project.custom_project_service = compliance_sub_category.name + '-' + str(naming)
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
                            frappe.db.commit()
                        frappe.msgprint('Project Created for {0}.'.format(compliance_sub_category.name), alert = 1)
                        for template_task in reversed(project_template_doc.tasks):
                            ''' Method to create task against created project from the Project Template '''
                            template_task_doc = frappe.get_doc('Task', template_task.task)
                            user_name = frappe.get_cached_value("User", frappe.session.user, "full_name")
                            task_doc = frappe.new_doc('Task')
                            task_doc.compliance_sub_category = compliance_sub_category.name
                            task_doc.subject = template_task.subject
                            task_doc.project = project.name
                            task_doc.project_name = project.project_name
                            task_doc.category_type = project.category_type
                            task_doc.exp_start_date = expiry_date
                            task_doc.custom_serial_number = template_task.idx
                            task_doc.department = compliance_sub_category.department
                            if template_task_doc.expected_time:
                                task_doc.expected_time = template_task_doc.expected_time
                            if template_task.custom_task_duration:
                                task_doc.duration = template_task.custom_task_duration
                                task_doc.exp_end_date = exp_end_date
                            if template_task_doc.depends_on:
                                for depends_task in template_task_doc.depends_on:
                                    dependent_task = frappe.get_doc('Task', {'project':project.name,'subject':depends_task.subject}, 'name')
                                    task_doc.append("depends_on", {
                                    "task": dependent_task.name,
                                    })
                            task_doc.save(ignore_permissions=True)
                            if template_task.type and template_task.employee_or_group:
                                frappe.db.set_value('Task', task_doc.name, 'assigned_to', template_task.employee_or_group)
                                if template_task.type == "Employee":
                                    employee = frappe.db.get_value('Employee', template_task.employee_or_group, 'user_id')
                                    if employee and employee != head_of_department:
                                        create_todo('Task', task_doc.name, employee, employee, 'Task {0} Assigned Successfully'.format(task_doc.name))
                                if template_task.type == "Employee Group":
                                    employee_group = frappe.get_doc('Employee Group', template_task.employee_or_group)
                                    if employee_group.employee_list:
                                        for employee in employee_group.employee_list:
                                            create_todo('Task', task_doc.name, employee.user_id, employee.user_id, 'Task {0} Assigned Successfully'.format(task_doc.name))
                                            frappe.db.commit()
                else:
                    frappe.throw( title = _('ALERT !!'), msg = _('Project Template does not exist for {0}'.format(compliance_sub_category)))
