"""API methods for Gumroad sales import and DOR export."""

import csv
import frappe
from frappe import _
from io import StringIO
from datetime import datetime


@frappe.whitelist()
def import_gumroad_csv(file_content):
	"""
	Import Gumroad sales from CSV file content.

	Args:
		file_content: CSV file content as string

	Returns:
		dict: Summary of import results
	"""
	settings = frappe.get_single("Gumroad Settings")

	if not settings.company:
		frappe.throw(_("Please configure Gumroad Settings first"))

	results = {
		"created": 0,
		"updated": 0,
		"errors": [],
		"invoices": []
	}

	# Parse CSV
	reader = csv.DictReader(StringIO(file_content))

	for row in reader:
		if row.get("Type") != "Sale":
			continue  # Skip totals/summary rows

		try:
			purchase_id = row["Purchase ID"]

			# Check if already imported
			existing = frappe.db.exists("Gumroad Sale", {"purchase_id": purchase_id})

			if existing:
				results["updated"] += 1
				continue

			# Create Gumroad Sale record
			sale = frappe.get_doc({
				"doctype": "Gumroad Sale",
				"purchase_id": purchase_id,
				"sale_date": datetime.strptime(row["Date"], "%Y-%m-%d"),
				"item_name": row["Item Name"],
				"buyer_name": row["Buyer Name"],
				"buyer_email": row["Buyer Email"],
				"sale_price": float(row["Sale Price ($)"] or 0),
				"taxes": float(row["Taxes ($)"] or 0),
				"shipping": float(row["Shipping ($)"] or 0),
				"gumroad_fees": float(row["Gumroad Fees ($)"] or 0),
				"net_total": float(row["Net Total ($)"] or 0),
				"import_status": "Imported"
			})
			sale.insert()

			# Create Sales Invoice
			invoice_name = create_sales_invoice_from_gumroad_sale(sale, settings)

			# Update sale with invoice reference
			sale.sales_invoice = invoice_name
			sale.save()

			results["created"] += 1
			results["invoices"].append(invoice_name)

		except Exception as e:
			results["errors"].append(f"Row {purchase_id}: {str(e)}")
			frappe.log_error(f"Gumroad import error: {str(e)}", "Gumroad CSV Import")

	frappe.db.commit()

	return results


def create_sales_invoice_from_gumroad_sale(sale, settings):
	"""
	Create Sales Invoice from Gumroad Sale.

	Args:
		sale: Gumroad Sale document
		settings: Gumroad Settings document

	Returns:
		str: Sales Invoice name
	"""
	# Get or create customer
	customer_name = get_or_create_customer(
		sale.buyer_email,
		sale.buyer_name or sale.buyer_email,
		settings
	)

	# Create invoice
	invoice = frappe.get_doc({
		"doctype": "Sales Invoice",
		"customer": customer_name,
		"posting_date": sale.sale_date,
		"due_date": sale.sale_date,
		"company": settings.company,
		"custom_sales_platform": "Gumroad",
		"custom_gumroad_purchase_id": sale.purchase_id,
		"items": [{
			"item_code": settings.default_gumroad_item,
			"item_name": sale.item_name,
			"qty": 1,
			"rate": sale.sale_price,
			"income_account": settings.gumroad_sales_account
		}],
		"taxes": []
	})

	# Add sales tax if collected
	if sale.taxes > 0:
		invoice.append("taxes", {
			"charge_type": "Actual",
			"account_head": settings.sales_tax_payable_account,
			"description": "Sales Tax (collected by Gumroad)",
			"tax_amount": sale.taxes
		})

	# Add Gumroad fees as deduction
	if sale.gumroad_fees > 0:
		invoice.append("taxes", {
			"charge_type": "Actual",
			"account_head": settings.gumroad_fees_account,
			"description": "Gumroad Processing Fees",
			"tax_amount": -sale.gumroad_fees,
			"add_deduct_tax": "Deduct"
		})

	invoice.insert()
	invoice.submit()

	# Create payment entry
	create_payment_entry_for_invoice(invoice, settings, sale.sale_date)

	return invoice.name


def get_or_create_customer(email, name, settings):
	"""Get or create customer by email."""
	# Use email as customer ID for uniqueness
	customer_name = email

	if frappe.db.exists("Customer", customer_name):
		return customer_name

	customer = frappe.get_doc({
		"doctype": "Customer",
		"customer_name": name,
		"customer_type": "Individual",
		"customer_group": settings.default_customer_group or "Individual",
		"territory": settings.default_territory or "All Territories",
		"email_id": email
	})
	customer.insert()

	return customer.name


def create_payment_entry_for_invoice(invoice, settings, posting_date):
	"""Create payment entry for invoice to Gumroad Clearing account."""
	from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry

	payment = get_payment_entry(invoice.doctype, invoice.name)
	payment.posting_date = posting_date
	payment.reference_date = posting_date
	payment.paid_to = settings.gumroad_clearing_account

	payment.insert()
	payment.submit()

	return payment.name
