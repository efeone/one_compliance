# Copyright (c) 2026, efeone and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class ActiveTaskTimer(Document):
	def autoname(self):
		full_name = self.full_name or frappe.db.get_value("User", self.user, "full_name") or self.user
		task_label = self.task if self.task else ("Ad-hoc Event" if self.is_ad_hoc_event else "No Task")
		self.name = f"{full_name}: {task_label}"
