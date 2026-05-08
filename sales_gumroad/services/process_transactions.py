"""
Gumroad Transaction Processor
Converts NEW Gumroad Transaction records into ERPNext documents
"""
import frappe
from datetime import datetime
from typing import Dict


def process_pending_transactions() -> Dict:
	"""
	Process all NEW Gumroad Transactions into Sales Invoices and Payment Entries

	Returns:
		Dict with processing statistics
	"""
	frappe.logger().info("Starting Gumroad transaction processing")

	settings = frappe.get_single("Gumroad Settings")

	if not settings.company:
		frappe.log_error(
			"Gumroad Settings not configured - company required",
			"Gumroad Transaction Processor"
		)
		return {
			"success": False,
			"error": "Gumroad Settings not configured",
			"processed": 0,
			"failed": 0
		}

	# Get all NEW transactions
	transactions = frappe.get_all(
		"Gumroad Transaction",
		filters={"sync_status": "NEW"},
		order_by="sale_timestamp asc",
		limit=100  # Process in batches
	)

	stats = {
		"success": True,
		"processed": 0,
		"failed": 0,
		"errors": []
	}

	for txn_name in transactions:
		try:
			transaction = frappe.get_doc("Gumroad Transaction", txn_name.name)
			process_transaction(transaction, settings)
			stats["processed"] += 1

		except Exception as e:
			stats["failed"] += 1
			stats["errors"].append({
				"transaction": txn_name.name,
				"error": str(e)
			})
			frappe.log_error(
				message=f"Failed to process transaction {txn_name.name}: {str(e)}",
				title="Gumroad Transaction Processing Error"
			)

	frappe.db.commit()

	frappe.logger().info(
		f"Transaction processing complete: {stats['processed']} processed, "
		f"{stats['failed']} failed"
	)

	return stats


def process_transaction(transaction, settings):
	"""
	Process a single Gumroad Transaction into ERP documents

	Args:
		transaction: Gumroad Transaction document
		settings: Gumroad Settings document
	"""
	try:
		# Skip if already processed
		if transaction.sync_status != "NEW":
			return

		# Get or create customer
		customer_name = get_or_create_customer(
			transaction.purchaser_email,
			transaction.purchaser_name or transaction.purchaser_email,
			settings
		)

		# Get posting date from sale timestamp
		posting_date = transaction.sale_timestamp.date() if transaction.sale_timestamp else datetime.now().date()

		# Create Sales Invoice
		invoice = create_sales_invoice(transaction, settings, customer_name, posting_date)

		# Create Payment Entry
		payment = create_payment_entry(invoice, settings, posting_date)

		# Update transaction status
		transaction.sync_status = "PROCESSED"
		transaction.sales_invoice = invoice.name
		transaction.payment_entry = payment.name
		transaction.synced_at = datetime.now()
		transaction.error_message = None
		transaction.save(ignore_permissions=True)

		frappe.logger().debug(f"Processed transaction {transaction.name}")

	except Exception as e:
		# Mark as FAILED and store error
		transaction.sync_status = "FAILED"
		transaction.error_message = str(e)
		transaction.save(ignore_permissions=True)
		raise


def create_sales_invoice(transaction, settings, customer_name, posting_date):
	"""
	Create Sales Invoice from Gumroad Transaction

	Args:
		transaction: Gumroad Transaction document
		settings: Gumroad Settings document
		customer_name: Customer name
		posting_date: Posting date for invoice

	Returns:
		Sales Invoice document
	"""
	invoice = frappe.get_doc({
		"doctype": "Sales Invoice",
		"customer": customer_name,
		"posting_date": posting_date,
		"due_date": posting_date,
		"company": settings.company,
		"currency": transaction.currency or "USD",
		"custom_sales_platform": "Gumroad",
		"custom_gumroad_purchase_id": transaction.gumroad_sale_id,
		"items": [{
			"item_code": settings.default_gumroad_item,
			"item_name": transaction.product_name or "Gumroad Product",
			"qty": transaction.quantity or 1,
			"rate": transaction.price or 0,
			"income_account": settings.gumroad_sales_account
		}],
		"taxes": []
	})

	# Add sales tax if collected
	if transaction.tax_amount and transaction.tax_amount > 0:
		invoice.append("taxes", {
			"charge_type": "Actual",
			"account_head": settings.sales_tax_payable_account,
			"description": "Sales Tax (collected by Gumroad)",
			"tax_amount": transaction.tax_amount
		})

	# Add Gumroad fees as deduction
	if transaction.gumroad_fee and transaction.gumroad_fee > 0:
		invoice.append("taxes", {
			"charge_type": "Actual",
			"account_head": settings.gumroad_fees_account,
			"description": "Gumroad Processing Fees",
			"tax_amount": -transaction.gumroad_fee,
			"add_deduct_tax": "Deduct"
		})

	# Set posting time flag for backdated invoices
	invoice.set_posting_time = 1

	invoice.insert(ignore_permissions=True)
	invoice.submit()

	return invoice


def create_payment_entry(invoice, settings, posting_date):
	"""
	Create Payment Entry for invoice to Gumroad Clearing account

	Args:
		invoice: Sales Invoice document
		settings: Gumroad Settings document
		posting_date: Posting date for payment

	Returns:
		Payment Entry document
	"""
	from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry

	payment = get_payment_entry(invoice.doctype, invoice.name)
	payment.posting_date = posting_date
	# Use MC-6515 card account directly since Gumroad deposits there
	payment.paid_to = "MC-6515 - Business Debit Card - DC"

	# Set reference for bank transaction (required for clearing account)
	payment.reference_no = invoice.name
	payment.reference_date = posting_date

	# Set posting time flag for backdated payments
	payment.set_posting_time = 1

	payment.insert(ignore_permissions=True)
	payment.submit()

	return payment


def get_or_create_customer(email, name, settings):
	"""
	Get or create customer by email

	Args:
		email: Customer email
		name: Customer name
		settings: Gumroad Settings document

	Returns:
		str: Customer name
	"""
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
	customer.insert(ignore_permissions=True)

	return customer.name


@frappe.whitelist()
def manual_process():
	"""
	Manually trigger transaction processing (callable from UI)

	Returns:
		Processing statistics
	"""
	frappe.only_for("System Manager", "Accounts Manager")

	return process_pending_transactions()


@frappe.whitelist()
def retry_failed_transaction(transaction_name):
	"""
	Retry processing a failed transaction

	Args:
		transaction_name: Gumroad Transaction name

	Returns:
		Success status
	"""
	frappe.only_for("System Manager", "Accounts Manager")

	transaction = frappe.get_doc("Gumroad Transaction", transaction_name)
	settings = frappe.get_single("Gumroad Settings")

	if transaction.sync_status not in ["NEW", "FAILED"]:
		frappe.throw(f"Transaction {transaction_name} is already {transaction.sync_status}")

	# Reset to NEW and process
	transaction.sync_status = "NEW"
	transaction.save(ignore_permissions=True)

	try:
		process_transaction(transaction, settings)
		frappe.db.commit()
		return {"success": True, "message": "Transaction processed successfully"}
	except Exception as e:
		frappe.db.rollback()
		return {"success": False, "error": str(e)}
