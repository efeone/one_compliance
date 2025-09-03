import frappe
from frappe.desk.page.setup_wizard.setup_wizard import make_records
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

# Custom field method imports
from one_compliance.custom.custom_field.customer import get_customer_custom_fields
from one_compliance.custom.custom_field.department import get_department_custom_fields
from one_compliance.custom.custom_field.event_participant import get_event_participant_custom_fields
from one_compliance.custom.custom_field.event import get_event_custom_fields
from one_compliance.custom.custom_field.item import get_item_custom_fields
from one_compliance.custom.custom_field.opportunity import get_opportunity_custom_fields
from one_compliance.custom.custom_field.project_template import get_project_template_custom_fields
from one_compliance.custom.custom_field.project_template_task import get_project_template_task_custom_fields
from one_compliance.custom.custom_field.project import get_project_custom_fields
from one_compliance.custom.custom_field.sales_invoice import get_sales_invoice_custom_fields
from one_compliance.custom.custom_field.sales_order_item import get_sales_order_item_custom_fields
from one_compliance.custom.custom_field.sales_order import get_sales_order_custom_fields
from one_compliance.custom.custom_field.task import get_task_custom_fields
from one_compliance.custom.custom_field.terms_and_conditions import get_terms_and_conditions_custom_fields
from one_compliance.custom.custom_field.timesheet import get_timesheet_custom_fields
from one_compliance.custom.custom_field.todo import get_todo_custom_fields

# Custom property setter method imports
from one_compliance.custom.property_setter.contact_email import get_contact_email_property_setters
from one_compliance.custom.property_setter.contact_phone import get_contact_phone_property_setters
from one_compliance.custom.property_setter.contact import get_contact_property_setters
from one_compliance.custom.property_setter.customer import get_customer_property_setters
from one_compliance.custom.property_setter.employee_checkin import get_employee_checkin_property_setters
from one_compliance.custom.property_setter.event_participant import get_event_participant_property_setters
from one_compliance.custom.property_setter.event import get_event_property_setters
from one_compliance.custom.property_setter.item import get_item_property_setters
from one_compliance.custom.property_setter.lead import get_lead_property_setters
from one_compliance.custom.property_setter.opportunity import get_opportunity_property_setters
from one_compliance.custom.property_setter.item import get_item_property_setters
from one_compliance.custom.property_setter.project_template_task import get_project_template_task_property_setters
from one_compliance.custom.property_setter.project_template import get_project_template_property_setters
from one_compliance.custom.property_setter.project import get_project_property_setters
from one_compliance.custom.property_setter.quotation_item import get_quotation_item_property_setters
from one_compliance.custom.property_setter.quotation import get_quotation_property_setters
from one_compliance.custom.property_setter.sales_invoice_item import get_sales_invoice_item_property_setters
from one_compliance.custom.property_setter.sales_invoice import get_sales_invoice_property_setters
from one_compliance.custom.property_setter.sales_order_item import get_sales_order_item_property_setters
from one_compliance.custom.property_setter.sales_order import get_sales_order_property_setters
from one_compliance.custom.property_setter.task import get_task_property_setters
from one_compliance.custom.property_setter.timesheet_detail import get_timesheet_detail_property_setters
from one_compliance.custom.property_setter.timesheet import get_timesheet_property_setters

# Fixture method imports
from one_compliance.custom.fixtures.category_type import category_type_fixtures
from one_compliance.custom.fixtures.customer_type import get_customer_type_fixtures
from one_compliance.custom.fixtures.designation import get_designation_fixtures
from one_compliance.custom.fixtures.document_register_type import get_document_register_type_fixtures
from one_compliance.custom.fixtures.module_profile import get_module_profile_fixtures
from one_compliance.custom.fixtures.notification_template import get_notification_template_fixtures
from one_compliance.custom.fixtures.role_profile import get_role_profile_fixtures
from one_compliance.custom.fixtures.role import get_role_fixtures
from one_compliance.custom.fixtures.translations import get_translations_fixtures
from one_compliance.custom.fixtures.web_page import get_web_page_fixtures
from one_compliance.custom.fixtures.workflow_state import get_workflow_state_fixtures
from one_compliance.custom.fixtures.workflow_action_master import get_workflow_action_master_fixtures
from one_compliance.custom.fixtures.workflow import get_workflow_fixtures

def after_migrate():
	# Creating One Compliance specific custom fields
	create_custom_fields(get_custom_fields(), ignore_validate=True)

	# Creating One Compliance specific Property Setters
	create_property_setters(get_property_setters())

	# Creating One Compliance specific fixtures
	create_fixtures()

def before_migrate():
	delete_custom_fields_for_app()

def create_custom_fields_for_app():
	create_custom_fields(get_custom_fields())

def delete_custom_fields_for_app():
	delete_custom_fields(get_custom_fields())

def create_property_setters_for_app():
    create_property_setters(get_property_setters())


def create_fixtures():
	'''
		Method to create One Compliance specific fixtures
	'''
	make_records(category_type_fixtures())
	make_records(get_role_fixtures())
	make_records(get_web_page_fixtures())
	make_records(get_workflow_state_fixtures())
	make_records(get_workflow_action_master_fixtures())
	make_records(get_workflow_fixtures())
	make_records(get_web_page_fixtures())
	make_records(get_designation_fixtures())
	make_records(get_role_profile_fixtures())
	make_records(get_translations_fixtures())
	make_records(get_customer_type_fixtures())
	make_records(get_module_profile_fixtures())
	make_records(get_notification_template_fixtures())
	make_records(get_document_register_type_fixtures())

def delete_custom_fields(custom_fields: dict):
	'''
		Method to Delete custom fields
		args:
			custom_fields: a dict like `{"Item": [{fieldname: "is_pixel", ...}]}`
	'''
	for doctype, fields in custom_fields.items():
		frappe.db.delete(
			'Custom Field',
			{
				'fieldname': ('in', [field.get('fieldname') for field in fields]),
				'dt': doctype,
			},
		)
		frappe.clear_cache(doctype=doctype)

def create_property_setters(property_setter_datas):
	'''
		Method to create custom property setters
		args:
			property_setter_datas : list of dict of property setter obj
	'''
	for property_setter_data in property_setter_datas:
		if frappe.db.exists('Property Setter', property_setter_data):
			continue
		property_setter = frappe.new_doc('Property Setter')
		property_setter.update(property_setter_data)
		property_setter.flags.ignore_permissions = True
		property_setter.insert()

def get_custom_fields():
	'''
		Method to get custom fields to be created for One Compliance
	'''
	custom_fields = get_customer_custom_fields()
	custom_fields.update(get_department_custom_fields())
	custom_fields.update(get_event_participant_custom_fields())
	custom_fields.update(get_event_custom_fields())
	custom_fields.update(get_item_custom_fields())
	custom_fields.update(get_opportunity_custom_fields())
	custom_fields.update(get_project_template_custom_fields())
	custom_fields.update(get_project_template_task_custom_fields())
	custom_fields.update(get_project_custom_fields())
	custom_fields.update(get_sales_invoice_custom_fields())
	custom_fields.update(get_sales_order_item_custom_fields())
	custom_fields.update(get_sales_order_custom_fields())
	custom_fields.update(get_task_custom_fields())
	custom_fields.update(get_terms_and_conditions_custom_fields())
	custom_fields.update(get_timesheet_custom_fields())
	custom_fields.update(get_todo_custom_fields())
	custom_fields.update(())
	return custom_fields

def get_property_setters():
	'''
		One Compliance specific property setters that need to be added to the Standard DocTypes
	'''
	property_setters = get_contact_email_property_setters()
	property_setters.extend(get_contact_phone_property_setters())
	property_setters.extend(get_contact_property_setters())
	property_setters.extend(get_customer_property_setters())
	property_setters.extend(get_employee_checkin_property_setters())
	property_setters.extend(get_event_participant_property_setters())
	property_setters.extend(get_event_property_setters())
	property_setters.extend(get_item_property_setters())
	property_setters.extend(get_lead_property_setters())
	property_setters.extend(get_opportunity_property_setters())
	property_setters.extend(get_project_template_task_property_setters())
	property_setters.extend(get_project_template_property_setters())
	property_setters.extend(get_project_property_setters())
	property_setters.extend(get_quotation_item_property_setters())
	property_setters.extend(get_quotation_property_setters())
	property_setters.extend(get_sales_invoice_item_property_setters())
	property_setters.extend(get_sales_invoice_property_setters())
	property_setters.extend(get_sales_order_item_property_setters())
	property_setters.extend(get_sales_order_property_setters())
	property_setters.extend(get_task_property_setters())
	property_setters.extend(get_timesheet_detail_property_setters())
	property_setters.extend(get_timesheet_property_setters())
	return property_setters
