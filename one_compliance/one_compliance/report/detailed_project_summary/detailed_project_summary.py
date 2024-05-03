# Copyright (c) 2024, efeone and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import getdate

def execute(filters=None):
	columns = get_columns(filters)
	data = get_data(filters)
	return columns, data

def get_columns(filters=None):
	columns = [
		{
			"label": _("Department"),
			"fieldname": "department",
			"fieldtype": "Link",
			"options": 'Department',
			"width": 200
		},
		{
			"label": _("Customer"),
			"fieldname": "customer",
			"fieldtype": "Link",
			"options": 'Customer',
			"width": 200
		},
		{
			"label": _("Project"),
			"fieldname": "project",
			"fieldtype": "Link",
			"options": 'Project',
			"width": 400
		},
		{
			"label": _("Project Name"),
			"fieldname": "project_name",
			"fieldtype": "Data",
			"width": 100,
			"hidden":1
		},
		{
			"label": _("Status"),
			"fieldname": "status",
			"fieldtype": "Data",
			"width": 150
		},
		{
			"label": _("Progress"),
			"fieldname": "progress",
			"fieldtype": "Percent",
			"width": 150
		},
		{
			"label": _("Pending Tasks"),
			"fieldname": "pending_task",
			"fieldtype": "Int",
			"width": 150
		},
		{
			"label": _("Completed Tasks"),
			"fieldname": "completed_task",
			"fieldtype": "Int",
			"width": 150
		},
		{
			"label": _("Overdue Tasks"),
			"fieldname": "overdue_task",
			"fieldtype": "Int",
			"width": 150
		},
		{
			"label": _("Invoiced"),
			"fieldname": "invoiced",
			"fieldtype": "Data",
			"width": 90
		},
		{
			"label": _("Invoiced Amount"),
			"fieldname": "invoiced_amount",
			"fieldtype": "Currency",
			"width": 150
		},
		{
			"label": _("Payment Recieved"),
			"fieldname": "payment_recieved",
			"fieldtype": "Currency",
			"width": 180
		},
		{
			"label": _("Outstanding Amount"),
			"fieldname": "outstanding_amount",
			"fieldtype": "Currency",
			"width": 180
		}
	]
	return columns

def get_data(filters):
	data=[]
	departments = []
	if filters.get('department'):
		if frappe.db.exists('Department', filters.get('department')):
			departments.append(filters.get('department'))
	else:
		departments = frappe.db.get_all('Department', { 'is_group':0 }, pluck='name')
	data = prepare_data(departments, filters)
	return data

def prepare_data(departments, filters):
	data=[]
	for department in departments:
		data.append({
			'department': department
		})
		projects = frappe.db.get_all('Project', { 'department': department, 'expected_start_date':['between', [ getdate(filters.get('from_date')), getdate(filters.get('to_date'))]] }, pluck='name')
		for project in projects:
			project_doc = frappe.get_doc('Project', project)
			invoice_details = get_invoiced_and_outstanding_amount_from_project(project)
			row = {
				'department': department,
				'customer': project_doc.customer,
				'project': project_doc.name,
				'project_name': project_doc.project_name,
				'status': project_doc.status,
				'progress': project_doc.percent_complete,
				'pending_task': get_project_count_based_on_status(project, 'Pending'),
				'completed_task': get_project_count_based_on_status(project, 'Completed'),
				'overdue_task': get_project_count_based_on_status(project, 'Overdue'),
				'invoiced': is_invoiced_or_not(project),
				'invoiced_amount': invoice_details.get('invoiced_amount') or 0,
				'payment_recieved': invoice_details.get('payment_recieved') or 0,
				'outstanding_amount': invoice_details.get('outstanding_amount') or 0
			}
			data.append(row)
	return data

def get_project_count_based_on_status(project, status):
	'''
		Method to get count of Tasks with respect to Project and status
	'''
	count = 0
	available_statuses = ['Overdue', 'Completed']
	if status == 'Pending':
		if frappe.db.exists('Task', { 'project':project, 'status':['in', ['Open', 'Working', 'Pending Review', 'Hold']] }):
			count = frappe.db.count('Task', { 'project':project, 'status':['in', ['Open', 'Working', 'Pending Review', 'Hold']] })
	elif status in available_statuses:
		if frappe.db.exists('Task', { 'project':project, 'status':status }):
			count = frappe.db.count('Task', { 'project':project, 'status':status })
	return count

def is_invoiced_or_not(project):
	'''
		Method to check wether the project is invoiced or not
		Submitted Sales Invoice with Project link in accounting Dimensions
		Return Yes or No
	'''
	invoiced = 'No'
	if frappe.db.exists('Sales Invoice', { 'project':project, 'docstatus':1 }):
		invoiced = 'Yes'
	return invoiced

def get_invoiced_and_outstanding_amount_from_project(project):
	invoice_details = { 'invoiced_amount': 0, 'payment_recieved': 0, 'outstanding_amount': 0 }
	query = """
		SELECT
			coalesce(SUM(rounded_total), 0) as invoiced_amount,
			coalesce(SUM(outstanding_amount), 0) as outstanding_amount
		FROM
			`tabSales Invoice`
		WHERE
			project = %(project)s AND
			docstatus = 1
	"""
	output = frappe.db.sql(query, { 'project':project }, as_dict=True)
	if output and output[0]:
		invoice_details['invoiced_amount'] = output[0].get('invoiced_amount') or 0
		invoice_details['outstanding_amount'] = output[0].get('outstanding_amount') or 0
		invoice_details['payment_recieved'] = invoice_details['invoiced_amount'] - invoice_details['outstanding_amount']
	return invoice_details
