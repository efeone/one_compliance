import frappe
from frappe.utils import get_datetime

@frappe.whitelist()
def get_project(status=None, project=None, customer=None, department=None, sub_category=None, employee=None, from_date=None, to_date=None):
    current_user = frappe.session.user
    user_id = f'"{employee}"' if employee else None

    # Construct SQL query to fetch list of projects that have at least one task with 'Open' status
    query = """
    SELECT DISTINCT
        p.name, p.project_name, p.customer, p.department, p.compliance_sub_category, p._assign,
        p.expected_start_date, p.expected_end_date, p.status
    FROM
        tabProject p
    INNER JOIN
        tabTask t ON t.project = p.name
    WHERE
        1 = 1
    """
    if current_user != "Administrator":
        query += "AND (t.readiness_status = 'Ready' OR t.readiness_status IS NULL OR t.readiness_status = '')"
        if employee:
            query += f" AND t._assign LIKE '%{user_id}%'"

    if status:
        query += f" AND p.status = '{status}'"
    else:
        query += " AND p.status IN ('Open', 'Working', 'Overdue')"

    if project:
        query += f" AND p.name = '{project}'"

    if customer:
        query += f" AND p.customer = '{customer}'"

    if department:
        query += f" AND p.department = '{department}'"

    if sub_category:
        query += f" AND p.compliance_sub_category = '{sub_category}'"

    if employee:
        query += f" AND t._assign LIKE '%{user_id}%'"

    if from_date:
        query += f" AND p.expected_start_date >= '{from_date}'"

    if to_date:
        query += f" AND p.expected_end_date < '{to_date}'"

    query += " ORDER BY p.modified DESC;"

    project_list = frappe.db.sql(query, as_dict=1)
    # Process employee assignment details
    for project in project_list:
        project['employee_names'] = []
        if project['_assign']:
            user_ids = frappe.parse_json(project['_assign'])
            if user_ids:
                # Query to get employee names
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
