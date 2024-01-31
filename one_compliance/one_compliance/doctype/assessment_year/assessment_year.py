# Copyright (c) 2024, efeone and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class AssessmentYear(Document):
    def autoname(self):
        self.name = self.generate_assessment_year_name()

    def generate_assessment_year_name(self):
        start_year = frappe.utils.getdate(self.year_start_date).year
        end_year = frappe.utils.getdate(self.year_end_date).year
        return str(start_year) + '-' + str(end_year)
