import frappe
from frappe.model.document import Document

class GumroadPayout(Document):
	def autoname(self):
		self.name = self.gumroad_payout_id
