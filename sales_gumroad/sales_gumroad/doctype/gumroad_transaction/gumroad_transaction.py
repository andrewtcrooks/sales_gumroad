import frappe
from frappe.model.document import Document

class GumroadTransaction(Document):
	def autoname(self):
		self.name = self.gumroad_sale_id
