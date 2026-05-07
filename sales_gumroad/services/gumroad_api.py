"""
Gumroad API Client Service
Handles all API communication with Gumroad
"""
import frappe
import requests
from typing import List, Dict, Optional
from datetime import datetime


class GumroadAPIClient:
	"""Client for Gumroad API v2"""

	BASE_URL = "https://api.gumroad.com/v2"

	def __init__(self, access_token: str):
		"""Initialize client with access token"""
		if not access_token:
			frappe.throw("Gumroad API access token is required")

		self.access_token = access_token
		self.headers = {
			"Authorization": f"Bearer {self.access_token}",
			"Content-Type": "application/json"
		}

	def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
		"""Make GET request to Gumroad API"""
		url = f"{self.BASE_URL}{endpoint}"

		try:
			response = requests.get(url, headers=self.headers, params=params, timeout=30)
			response.raise_for_status()
			return response.json()
		except requests.exceptions.HTTPError as e:
			if e.response.status_code == 401:
				frappe.throw("Invalid Gumroad API token. Check your settings.")
			elif e.response.status_code == 404:
				frappe.throw(f"Gumroad API endpoint not found: {endpoint}")
			else:
				frappe.throw(f"Gumroad API error: {str(e)}")
		except requests.exceptions.RequestException as e:
			frappe.throw(f"Network error connecting to Gumroad: {str(e)}")

	def fetch_sales(
		self,
		after_date: Optional[str] = None,
		before_date: Optional[str] = None,
		product_id: Optional[str] = None,
		email: Optional[str] = None,
		page: int = 1
	) -> Dict:
		"""
		Fetch sales from Gumroad API

		Args:
			after_date: Filter sales after this date (YYYY-MM-DD)
			before_date: Filter sales before this date (YYYY-MM-DD)
			product_id: Filter by product ID
			email: Filter by customer email
			page: Page number for pagination

		Returns:
			Dict with 'sales' list and pagination info
		"""
		params = {}

		if after_date:
			params['after'] = after_date
		if before_date:
			params['before'] = before_date
		if product_id:
			params['product_id'] = product_id
		if email:
			params['email'] = email
		if page:
			params['page'] = page

		return self._make_request("/sales", params)

	def fetch_all_sales(
		self,
		after_date: Optional[str] = None,
		before_date: Optional[str] = None,
		max_pages: int = 100
	) -> List[Dict]:
		"""
		Fetch all sales with automatic pagination

		Args:
			after_date: Filter sales after this date (YYYY-MM-DD)
			before_date: Filter sales before this date (YYYY-MM-DD)
			max_pages: Maximum number of pages to fetch (safety limit)

		Returns:
			List of all sale records
		"""
		all_sales = []
		page = 1

		while page <= max_pages:
			frappe.publish_realtime(
				"gumroad_sync_progress",
				{"message": f"Fetching page {page}...", "page": page},
				user=frappe.session.user
			)

			result = self.fetch_sales(
				after_date=after_date,
				before_date=before_date,
				page=page
			)

			sales = result.get('sales', [])

			if not sales:
				break

			all_sales.extend(sales)

			# Check if there are more pages
			# Gumroad API returns empty list when no more results
			if len(sales) == 0:
				break

			page += 1

		return all_sales

	def fetch_sale(self, sale_id: str) -> Dict:
		"""
		Fetch a single sale by ID

		Args:
			sale_id: The Gumroad sale ID

		Returns:
			Sale data dict
		"""
		return self._make_request(f"/sales/{sale_id}")

	def fetch_payouts(self, page: int = 1) -> Dict:
		"""
		Fetch payouts from Gumroad API (if available)

		NOTE: This endpoint may not be publicly available yet.
		As of 2026, there was a GitHub PR to add this feature.

		Args:
			page: Page number for pagination

		Returns:
			Dict with 'payouts' list and pagination info
		"""
		try:
			params = {'page': page} if page else {}
			return self._make_request("/payouts", params)
		except Exception as e:
			frappe.log_error(
				message=f"Payouts API not available: {str(e)}",
				title="Gumroad Payouts API Error"
			)
			return {"payouts": [], "error": "Payouts API not available"}

	def verify_license(self, product_permalink: str, license_key: str) -> Dict:
		"""
		Verify a license key for a product

		Args:
			product_permalink: Product permalink
			license_key: License key to verify

		Returns:
			Verification result
		"""
		params = {
			'product_permalink': product_permalink,
			'license_key': license_key
		}
		return self._make_request("/licenses/verify", params)


def get_gumroad_client() -> GumroadAPIClient:
	"""Get configured Gumroad API client from settings"""
	settings = frappe.get_single("Gumroad Settings")

	if not settings.api_access_token:
		frappe.throw(
			"Gumroad API token not configured. "
			"Please set it in Gumroad Settings."
		)

	return GumroadAPIClient(settings.get_password("api_access_token"))
