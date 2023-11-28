# Copyright (c) 2023, efeone and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class EngagementLetter(Document):
    pass
    # def validate(self):
    #     if self.customer_type == 'Lead' and self.lead:
    #         lead = frappe.get_doc('Lead', self.lead)
    #         if lead:
    #             self.full_name = lead.lead_name
    #     elif self.customer_type == 'Opportunity' and self.opportunity:
    #         opportunity = frappe.get_doc('Opportunity', self.opportunity)
    #         if opportunity:
    #             self.full_name = opportunity.contact_person
