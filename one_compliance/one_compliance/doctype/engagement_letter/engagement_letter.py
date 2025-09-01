

import frappe
from frappe.model.document import Document


class EngagementLetter(Document):
    

    def before_submit(self):
        """Set the Engagement Letter status to 'Submitted'"""
        self.status = "Submitted"