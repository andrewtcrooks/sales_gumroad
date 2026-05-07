"""
Gumroad Sales Sync Service
Pulls sales from Gumroad API and stores as Gumroad Transaction records
"""
import frappe
import json
from datetime import datetime, timedelta
from typing import List, Dict
from sales_gumroad.services.gumroad_api import get_gumroad_client


def sync_gumroad_sales(after_date: str = None, before_date: str = None) -> Dict:
	"""
	Sync sales from Gumroad API to Gumroad Transaction records

	Args:
		after_date: Fetch sales after this date (YYYY-MM-DD). If None, uses last_sales_sync
		before_date: Fetch sales before this date (YYYY-MM-DD)

	Returns:
		Dict with sync statistics
	"""
	frappe.logger().info("Starting Gumroad sales sync")

	settings = frappe.get_single("Gumroad Settings")

	# Determine date range
	if not after_date and settings.last_sales_sync:
		# Fetch from last sync with 1 hour overlap to catch any delayed records
		from frappe.utils import get_datetime
		last_sync = get_datetime(settings.last_sales_sync)
		overlap = last_sync - timedelta(hours=1)
		after_date = overlap.strftime("%Y-%m-%d")

	# Get API client
	try:
		client = get_gumroad_client()
	except Exception as e:
		frappe.log_error(
			message=str(e),
			title="Gumroad Sync: API Client Error"
		)
		return {
			"success": False,
			"error": str(e),
			"fetched": 0,
			"new": 0,
			"duplicate": 0,
			"failed": 0
		}

	# Fetch sales
	try:
		frappe.publish_realtime(
			"gumroad_sync_progress",
			{"message": "Fetching sales from Gumroad API..."},
			user=frappe.session.user
		)

		sales = client.fetch_all_sales(
			after_date=after_date,
			before_date=before_date
		)

		frappe.logger().info(f"Fetched {len(sales)} sales from Gumroad API")

	except Exception as e:
		frappe.log_error(
			message=str(e),
			title="Gumroad Sync: API Fetch Error"
		)
		return {
			"success": False,
			"error": str(e),
			"fetched": 0,
			"new": 0,
			"duplicate": 0,
			"failed": 0
		}

	# Process sales with idempotency
	stats = {
		"success": True,
		"fetched": len(sales),
		"new": 0,
		"duplicate": 0,
		"failed": 0,
		"errors": []
	}

	for sale in sales:
		try:
			result = create_transaction_from_sale(sale)
			if result == "created":
				stats["new"] += 1
			elif result == "duplicate":
				stats["duplicate"] += 1

		except Exception as e:
			stats["failed"] += 1
			stats["errors"].append({
				"sale_id": sale.get("id"),
				"error": str(e)
			})
			frappe.log_error(
				message=f"Failed to create transaction for sale {sale.get('id')}: {str(e)}",
				title="Gumroad Sync: Transaction Creation Error"
			)

	# Update last sync timestamp
	settings.last_sales_sync = datetime.now()
	settings.save(ignore_permissions=True)
	frappe.db.commit()

	frappe.logger().info(
		f"Gumroad sync complete: {stats['new']} new, "
		f"{stats['duplicate']} duplicate, {stats['failed']} failed"
	)

	return stats


def create_transaction_from_sale(sale: Dict) -> str:
	"""
	Create Gumroad Transaction from sale data with idempotency

	Args:
		sale: Sale data dict from Gumroad API

	Returns:
		"created" if new record created, "duplicate" if already exists
	"""
	sale_id = sale.get("id")

	if not sale_id:
		raise ValueError("Sale missing 'id' field")

	# IDEMPOTENCY CHECK - critical for safe syncing
	if frappe.db.exists("Gumroad Transaction", {"gumroad_sale_id": sale_id}):
		frappe.logger().debug(f"Transaction {sale_id} already exists, skipping")
		return "duplicate"

	# Parse sale data
	transaction = frappe.new_doc("Gumroad Transaction")
	transaction.gumroad_sale_id = sale_id

	# Timestamps
	sale_timestamp = sale.get("created_at") or sale.get("timestamp")
	if sale_timestamp:
		# Gumroad returns ISO format timestamps like "2026-02-24T14:53:34Z"
		from frappe.utils import get_datetime
		dt = get_datetime(sale_timestamp)
		# Remove timezone info for MySQL compatibility
		transaction.sale_timestamp = dt.replace(tzinfo=None) if dt else None

	# Product info
	transaction.product_id = sale.get("product_id")
	transaction.product_name = sale.get("product_name")
	transaction.permalink = sale.get("product_permalink") or sale.get("permalink")

	# Purchaser info
	transaction.purchaser_email = sale.get("email") or sale.get("purchaser_email")
	transaction.purchaser_name = sale.get("full_name") or sale.get("purchaser_name")
	transaction.purchaser_id = sale.get("purchaser_id")
	transaction.ip_country = sale.get("country_iso2") or sale.get("ip_country")

	# Financial data (Gumroad returns cents, convert to dollars)
	price_cents = sale.get("price") or 0
	fee_cents = sale.get("gumroad_fee") or 0
	transaction.price = price_cents / 100.0 if price_cents else 0
	transaction.gumroad_fee = fee_cents / 100.0 if fee_cents else 0
	transaction.currency = "USD"  # Gumroad API doesn't return currency code directly
	transaction.formatted_display_price = sale.get("formatted_display_price")
	transaction.tax_amount = sale.get("tax", 0) / 100.0 if sale.get("tax") else 0

	# Flags
	transaction.is_gift_receiver_purchase = sale.get("is_gift_receiver_purchase", False)
	transaction.refunded = sale.get("refunded", False)
	transaction.disputed = sale.get("disputed", False)
	transaction.dispute_won = sale.get("dispute_won", False)
	transaction.chargebacked = sale.get("chargebacked", False)

	# Subscription info
	transaction.subscription_id = sale.get("subscription_id")
	transaction.is_recurring_charge = sale.get("is_recurring_billing") or sale.get("is_recurring_charge", False)
	transaction.cancelled = sale.get("cancelled", False)
	transaction.ended = sale.get("ended", False)

	# License info
	transaction.license_key = sale.get("license_key")
	transaction.quantity = sale.get("quantity", 1)
	transaction.license_disabled = sale.get("license_disabled", False)

	# Affiliate
	transaction.affiliate = sale.get("affiliate")

	# Store raw JSON for auditability
	transaction.raw_json = json.dumps(sale, indent=2)

	# Set initial status
	if transaction.refunded:
		transaction.sync_status = "REFUNDED"
	elif transaction.chargebacked or transaction.disputed:
		transaction.sync_status = "SKIPPED"
	else:
		transaction.sync_status = "NEW"

	# Save
	transaction.insert(ignore_permissions=True)
	frappe.db.commit()

	frappe.logger().debug(f"Created transaction {sale_id}")

	return "created"


@frappe.whitelist()
def manual_sync(after_date=None, before_date=None):
	"""
	Manually trigger sales sync (callable from UI)

	Args:
		after_date: Optional date string (YYYY-MM-DD)
		before_date: Optional date string (YYYY-MM-DD)

	Returns:
		Sync statistics
	"""
	frappe.only_for("System Manager", "Accounts Manager")

	return sync_gumroad_sales(after_date, before_date)


@frappe.whitelist()
def get_sync_status():
	"""Get current sync status and statistics"""
	frappe.only_for("System Manager", "Accounts Manager")

	settings = frappe.get_single("Gumroad Settings")

	# Count transactions by status
	status_counts = {}
	for status in ["NEW", "PROCESSED", "FAILED", "REFUNDED", "SKIPPED"]:
		count = frappe.db.count(
			"Gumroad Transaction",
			{"sync_status": status}
		)
		status_counts[status] = count

	return {
		"last_sales_sync": settings.last_sales_sync,
		"last_payout_sync": settings.last_payout_sync,
		"auto_sync_enabled": settings.enable_auto_sync,
		"sync_frequency": settings.sync_frequency,
		"total_transactions": frappe.db.count("Gumroad Transaction"),
		"status_counts": status_counts
	}
