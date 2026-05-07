"""
Scheduled tasks for Gumroad Sales sync
"""
import frappe
from sales_gumroad.services.sync_sales import sync_gumroad_sales
from sales_gumroad.services.process_transactions import process_pending_transactions


def sync_and_process_gumroad_sales():
	"""
	Scheduled task to sync sales from Gumroad API and process them
	Runs based on sync_frequency setting in Gumroad Settings
	"""
	settings = frappe.get_single("Gumroad Settings")

	# Check if auto-sync is enabled
	if not settings.enable_auto_sync:
		frappe.logger().debug("Gumroad auto-sync disabled, skipping")
		return

	# Check if API token is configured
	if not settings.api_access_token:
		frappe.logger().warning("Gumroad API token not configured, skipping sync")
		return

	try:
		# Step 1: Sync sales from API
		frappe.logger().info("Running scheduled Gumroad sales sync")
		sync_stats = sync_gumroad_sales()

		frappe.logger().info(
			f"Gumroad sync completed: {sync_stats.get('new', 0)} new transactions"
		)

		# Step 2: Process NEW transactions into ERP documents
		frappe.logger().info("Processing pending Gumroad transactions")
		process_stats = process_pending_transactions()

		frappe.logger().info(
			f"Transaction processing completed: {process_stats.get('processed', 0)} processed"
		)

	except Exception as e:
		frappe.log_error(
			message=str(e),
			title="Gumroad Scheduled Sync Error"
		)


def sync_gumroad_sales_task():
	"""Sync sales from Gumroad API (Step 1 only)"""
	settings = frappe.get_single("Gumroad Settings")

	if not settings.enable_auto_sync or not settings.api_access_token:
		return

	try:
		sync_gumroad_sales()
	except Exception as e:
		frappe.log_error(
			message=str(e),
			title="Gumroad Sales Sync Task Error"
		)


def process_gumroad_transactions_task():
	"""Process pending Gumroad transactions (Step 2 only)"""
	try:
		process_pending_transactions()
	except Exception as e:
		frappe.log_error(
			message=str(e),
			title="Gumroad Transaction Processing Task Error"
		)
