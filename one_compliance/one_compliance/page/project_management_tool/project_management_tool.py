import frappe
from frappe.utils import get_datetime

@frappe.whitelist()
def get_project(status = None, project = None, customer = None, department = None, sub_category = None, employee = None, from_date = None, to_date = None):
    user_id = f'"{employee}"' if id else None
    # Construct the SQL query to fetch list of projects
    query = """
	SELECT
        name, project_name, customer, department, compliance_sub_category, _assign, expected_start_date, expected_end_date, status
    FROM
        tabProject
    """

    if status:
            query += f" WHERE status = '{status}'"
    else:
        query += " WHERE status IN ('open', 'working', 'overdue')"

    if project:
            query += f" AND name = '{project}'"

    if customer:
            query += f" AND customer = '{customer}'"

    if department:
            query += f" AND department = '{department}'"

    if sub_category:
            query += f" AND compliance_sub_category = '{sub_category}'"

    if employee:
            query += f" AND _assign LIKE '%{user_id}%'"

    if from_date:
            query += f" AND expected_start_date >= '{from_date}'"

    if to_date:
            query += f" AND expected_end_date < '{to_date}'"

    query += """ ORDER BY
            modified DESC;"""

    project_list = frappe.db.sql(query, as_dict=1)
    for project in project_list:
        project['employee_names'] = []
        if project['_assign']:
            user_ids = frappe.parse_json(project['_assign'])
            if user_ids:
                # Query to get the employee name from id
                user_names_query = """
                    SELECT name, employee_name, user_id FROM `tabEmployee`
                    WHERE user_id IN ({})
                """.format(', '.join(['%s' for _ in user_ids]))

                user_names = frappe.db.sql(user_names_query, tuple(user_ids), as_dict=True)
                project['_assign'] = [{'employee_name': user['employee_name'], 'employee_id': user['name']} for user in user_names]
                project['employee_names'] = [user['employee_name'] for user in user_names]
            else:
                project['_assign'] = []
                project['employee_names'] = []
        else:
            project['_assign'] = []
            project['employee_names'] = []

    return project_list
