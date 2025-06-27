from . import __version__ as app_version

app_name = "one_compliance"
app_title = "One Compliance"
app_publisher = "efeone"
app_description = "Frappe app to facilitate operations in Compliances and Tasks"
app_email = "info@efeone.com"
app_license = "MIT"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/one_compliance/css/one_compliance.css"
# app_include_js = "/assets/one_compliance/js/one_compliance.js"

# include js, css files in header of web template
# web_include_css = "/assets/one_compliance/css/one_compliance.css"
# web_include_js = "/assets/one_compliance/js/one_compliance.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "one_compliance/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
doctype_js = {
    "Project Template" : "public/js/project_template.js",
    "Customer" : "public/js/customer.js",
    "Project": "public/js/project.js",
    "Task": "public/js/task.js",
    "Department": "public/js/department.js",
    "Lead":"public/js/lead.js",
    "Opportunity":"public/js/opportunity.js",
    "Sales Invoice":"public/js/sales_invoice.js",
    "Sales Order":"public/js/sales_order.js",
    "Company" : "public/js/company.js",
    "Event":"public/js/event.js"
}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
#	"methods": "one_compliance.utils.jinja_methods",
#	"filters": "one_compliance.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "one_compliance.install.before_install"
after_install = "one_compliance.install.after_install"

before_uninstall = "one_compliance.install.before_uninstall"

after_migrate = "one_compliance.setup.after_migrate"

before_migrate = "one_compliance.setup.before_migrate"

# Uninstallation
# ------------

# before_uninstall = "one_compliance.uninstall.before_uninstall"
# after_uninstall = "one_compliance.uninstall.after_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "one_compliance.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

permission_query_conditions = {
	"Project": "one_compliance.one_compliance.doc_events.project.get_permission_query_conditions",
    "Task": "one_compliance.one_compliance.doc_events.task.get_permission_query_conditions",
}
#
# has_permission = {
#	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

override_doctype_class = {
	"Task": "one_compliance.one_compliance.doc_events.task.CustomTask"
}

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
    'Project Template':{
        'after_insert': 'one_compliance.one_compliance.doc_events.project_template.update_project_template',
        'on_trash': 'one_compliance.one_compliance.doc_events.project_template.on_trash',
        'validate': 'one_compliance.one_compliance.doc_events.project_template.validate',
    },
    'Task':{
        'on_update':[
            'one_compliance.one_compliance.doc_events.task.task_on_update',
            'one_compliance.one_compliance.doc_events.task.make_sales_invoice',
            'one_compliance.one_compliance.doc_events.task.subtask_on_update',
        ],
        'validate':[
            'one_compliance.one_compliance.doc_events.task.append_users_to_project',
            'one_compliance.one_compliance.doc_events.task.set_task_status_to_hold',
        ],
        'autoname': 'one_compliance.one_compliance.doc_events.task.autoname'
    },
    'Project':{
        'on_update': 'one_compliance.one_compliance.doc_events.project.project_on_update',
        'after_insert': 'one_compliance.one_compliance.doc_events.project.project_after_insert'
    },
    'Customer':{
        'on_update':[
            'one_compliance.one_compliance.doc_events.customer.customer_on_update',
            'one_compliance.one_compliance.doc_events.customer.create_project_from_customer'
        ],
        'before_save':[
            'one_compliance.one_compliance.doc_events.customer.create_task_from_opportunity',
            'one_compliance.one_compliance.doc_events.customer.set_expiry_dates'
        ]
    },
    'Sales Invoice':{
        'on_submit': 'one_compliance.one_compliance.doc_events.sales_invoice.sales_invoice_on_submit'
    },
    'Opportunity':{
        'after_save':'one_compliance.one_compliance.doc_events.oppotunity.make_engagement_letter'
    },
    'Sales Order':{
        'on_submit':'one_compliance.one_compliance.doc_events.sales_order.create_project_on_submit',
        'on_cancel': 'one_compliance.one_compliance.doc_events.sales_order.so_on_cancel_custom',
        'on_update_after_submit': 'one_compliance.one_compliance.doc_events.sales_order.so_on_update_after_submit',
    },
    'Payment Entry':{
        'on_submit': 'one_compliance.one_compliance.doc_events.payment_entry.payment_entry_on_submit'
    },
    'ToDo':{
        'before_insert':[
            'one_compliance.one_compliance.doc_events.todo.set_company_from_task',
            'one_compliance.one_compliance.doc_events.todo.set_company_from_project',
            'one_compliance.one_compliance.doc_events.todo.set_company_from_event'
        ]
    }
}

# Scheduled Tasks
# ---------------

scheduler_events = {
# "all": [
# "one_compliance.tasks.hourly"
# ],
	"daily": [
        'one_compliance.one_compliance.utils.task_daily_sheduler',
        'one_compliance.one_compliance.doctype.compliance_agreement.compliance_agreement.change_agreement_status_scheduler',
        'one_compliance.one_compliance.doctype.compliance_agreement.compliance_agreement.compliance_agreement_daily_scheduler',
        'one_compliance.one_compliance.doc_events.customer.create_project_from_customer_scheduler',
        'one_compliance.one_compliance.utils.notification_for_digital_signature_expiry',
        'one_compliance.one_compliance.utils.project_overdue_notification',
        'one_compliance.one_compliance.doc_events.project.set_status_to_overdue',
        'one_compliance.one_compliance.doctype.compliance_sub_category.compliance_sub_category.send_repeat_notif'
    ],
#	"hourly": [
#		"one_compliance.tasks.hourly"
#	],
	# "weekly": [
    #
	# ],
	# "monthly": [
    #
	# ],
}

# Testing
# -------

# before_tests = "one_compliance.install.before_tests"

# Overriding Methods
# ------------------------------
#
override_whitelisted_methods = {
	"frappe.desk.form.assign_to.add": "one_compliance.one_compliance.utils.add_custom"
}
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
override_doctype_dashboards = {
	"Item": "one_compliance.one_compliance.doc_events.item_dashboard.get_data",
    "Project": "one_compliance.one_compliance.doc_events.project_dashboard.get_data"
}

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]


# User Data Protection
# --------------------

# user_data_fields = [
#	{
#		"doctype": "{doctype_1}",
#		"filter_by": "{filter_by}",
#		"redact_fields": ["{field_1}", "{field_2}"],
#		"partial": 1,
#	},
#	{
#		"doctype": "{doctype_2}",
#		"filter_by": "{filter_by}",
#		"partial": 1,
#	},
#	{
#		"doctype": "{doctype_3}",
#		"strict": False,
#	},
#	{
#		"doctype": "{doctype_4}"
#	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
#	"one_compliance.auth.validate"
# ]
fixtures = [
    {
        'dt': 'Role',
        'filters': [['name', 'in', ['Founder','Director','Compliance Manager','Senior Manager','Manager','Executive','Head Of Department']]]
    },
    {
        'dt': "Document Register Type"
    },
    {
        'dt': 'Customer Type'
    },
    {
        'dt': 'Workflow State',
        'filters': [['name', 'in', ['Draft','Approved','Rejected','Pending','Sent to Customer','Customer Approval Waiting','Customer Approved',
                                    'Customer Rejected','Cancelled','Verified','Tax Invoice','Proforma Invoice', 'Closed', 'In Progress',
                                    'Pre-Invoice', 'Partially Paid', 'Paid', 'Invoiced', 'Completed']]]
    },
    {
        'dt': 'Workflow',
        'filters': [['name', 'in', ['Compliance Agreement Workflow', 'Sales Order Workflow']]]
    },
    {
        'dt': 'Workflow Action Master',
        'filters': [['name', 'in', ['Rejected','Approved','Request for Review','Review','Reject','Approve','Sent to Customer','Customer Approval',
                                    'Customer Reject','Customer Approval waiting','Cancelled','Generate Proforma Invoice','Generate Tax Invoice',
                                    'Cancel', 'Proceed', 'Close', 'Create Pre-Invoice']]]
    },
    {
        'dt' : 'Notification Template'
    },
    {
        'dt': 'Designation',
        'filters': [['name', 'in',['Founder','Director','Head Of Department','Senior Manager','Manager','Executive']]]
    },
    {
        'dt': 'Module Profile',
        'filters': [['name', 'in', ['Founder','Director','Head Of Department','Super Admin','Senior Manager','Manager','Executive']]]
    },
    {
        'dt': 'Web Page',
        'filters': [['name', 'in', ['customer-credentials', 'project-status', 'agreement-approval', 'login-page', 'customer-documents']]]
    },
    {
        'dt': 'Role Profile'
    },
    {
        'dt': 'Category Type',
        'filters': [['name','in',['Audit','Compliance','Tax','Consulting']]]
    },
    {
        'dt': 'Translation'
    },
    {
        'dt': 'Property Setter',
        'filters': [['module', '=', 'One Compliance']]
    }
]
