# Gumroad API Sync Setup Guide

Complete guide for setting up automated Gumroad sales sync via API.

---

## Prerequisites

- ERPNext installed and running
- Gumroad Sales app installed
- Gumroad account with products/sales

---

## Step 1: Get Gumroad API Access Token

### Method 1: Personal Access Token (Recommended)

1. **Login to Gumroad**
   - Go to https://app.gumroad.com

2. **Navigate to API Settings**
   - Go to Settings → Advanced
   - Scroll to "Application" section
   - Click "Create application"

3. **Create Application**
   - Name: `ERPNext Sync` (or any name)
   - Description: `Automated sales sync to ERPNext`
   - Click "Create application"

4. **Generate Access Token**
   - Copy the **Access Token** shown
   - **IMPORTANT:** Save this token securely - it won't be shown again
   - This token acts like a password

### Method 2: OAuth 2.0 (Advanced)

If you need OAuth flow (not typical for self-hosted ERP):

1. Follow Gumroad OAuth documentation: https://gumroad.com/api
2. Implement OAuth callback in ERPNext
3. Store access + refresh tokens

**For most users: Use Method 1 (Personal Access Token)**

---

## Step 2: Install/Update the App

### If Already Installed

```bash
cd ~/frappe-bench
bench --site your-site.local migrate
bench restart
```

### Fresh Install

```bash
cd ~/frappe-bench
bench get-app /path/to/gumroad_sales
bench --site your-site.local install-app gumroad_sales
bench --site your-site.local migrate
bench restart
```

---

## Step 3: Configure Gumroad Settings

1. **Navigate to Gumroad Settings**
   - Go to: **Gumroad Sales > Gumroad Settings**

2. **API Settings** (NEW)
   - **API Access Token:** Paste your token from Step 1
   - **Enable Auto Sync:** Check this box
   - **Sync Frequency:** Choose:
     - Every 15 Minutes (most responsive)
     - Hourly (recommended)
     - Daily (low volume)

3. **Account Settings** (Required)
   - **Company:** Select your company
   - **Gumroad Clearing Account:** e.g., "Gumroad Clearing - USD"
   - **Gumroad Fees Account:** e.g., "Gumroad Fees - USD"
   - **Gumroad Sales Account:** e.g., "Gumroad Sales - USD"
   - **Sales Tax Payable Account:** e.g., "Sales Tax Payable - USD"
   - **Default Gumroad Item:** Create/select item like "Gumroad Product"

4. **Customer Defaults**
   - **Default Customer Group:** e.g., "Individual"
   - **Default Territory:** e.g., "All Territories"

5. **Save**

---

## Step 4: Test the Sync

### Option A: Using Sync Dashboard (Recommended)

1. **Navigate to Dashboard**
   - Go to: **Gumroad Sales > Gumroad Sync Dashboard**

2. **View Status**
   - Check sync settings
   - View transaction statistics

3. **Manual Sync (First Time)**
   - Click **"Sync Sales Now"** button
   - Wait for sync to complete
   - Check results

4. **Process Transactions**
   - Click **"Process Transactions"** button
   - This converts NEW transactions into Sales Invoices

### Option B: Using Console

```python
# SSH to ERPNext
ssh frappe@erpnext

# Start Frappe console
cd ~/frappe-bench
bench --site your-site.local console

# Run sync
from gumroad_sales.services.sync_sales import sync_gumroad_sales
result = sync_gumroad_sales()
print(result)

# Process transactions
from gumroad_sales.services.process_transactions import process_pending_transactions
result = process_pending_transactions()
print(result)
```

---

## Step 5: Verify Results

### Check Gumroad Transactions

1. Go to: **Gumroad Sales > Gumroad Transaction**
2. You should see:
   - All sales from Gumroad API
   - Status: NEW → PROCESSED
   - Linked Sales Invoice and Payment Entry

### Check Sales Invoices

1. Go to: **Accounts > Sales Invoice**
2. Filter by:
   - Custom Sales Platform = "Gumroad"
3. Verify:
   - Customer created from email
   - Correct amounts
   - Gumroad fees deducted
   - Tax recorded

### Check Payment Entries

1. Go to: **Accounts > Payment Entry**
2. Verify:
   - Paid to Gumroad Clearing account
   - Correct amounts (net after fees)

---

## Architecture Overview

### How It Works

```
Gumroad API
    ↓
[Sync Service] (Scheduled/Manual)
    ↓
Gumroad Transaction (Raw Storage)
    ↓
[Transaction Processor]
    ↓
Sales Invoice + Payment Entry
```

### Two-Step Process

**Step 1: Sync (API → Raw Storage)**
- Fetches sales from Gumroad API
- Stores as `Gumroad Transaction` records
- Status: `NEW`
- **Idempotent:** Safe to run multiple times (checks `gumroad_sale_id`)
- **Raw data preserved:** Full JSON stored for audit

**Step 2: Process (Raw → ERP)**
- Converts `NEW` transactions
- Creates Sales Invoice
- Creates Payment Entry
- Updates status: `NEW` → `PROCESSED`
- **Decoupled:** Can retry failed transactions

---

## Scheduled Sync

Once configured, sync runs automatically based on **Sync Frequency** setting:

- **Every 15 Minutes:** Uses cron schedule
- **Hourly:** Uses hourly scheduler
- **Daily:** Uses daily scheduler

### Check Scheduler Status

```bash
ssh frappe@erpnext
cd ~/frappe-bench
bench --site your-site.local execute frappe.utils.scheduler.get_scheduler_status
```

### Manually Trigger Scheduled Task

```bash
bench --site your-site.local execute gumroad_sales.tasks.sync_and_process_gumroad_sales
```

---

## Transaction Statuses

| Status | Meaning |
|--------|---------|
| **NEW** | Fetched from API, waiting to be processed |
| **PROCESSED** | Successfully converted to Sales Invoice + Payment Entry |
| **FAILED** | Processing failed (see Error Message field) |
| **REFUNDED** | Sale was refunded in Gumroad |
| **SKIPPED** | Disputed/chargebacked - not processed |

---

## Troubleshooting

### "Invalid API token" Error

- Verify token in Gumroad Settings
- Token must be from https://app.gumroad.com/settings/advanced
- Check for copy/paste errors (no spaces)

### "Gumroad Settings not configured" Error

- Go to Gumroad Settings
- Fill in ALL required fields:
  - Company
  - Account mappings
  - Default item

### No Transactions Created

- Check Error Log: **Setup > Error Log**
- Verify date range (last_sales_sync)
- Try manual sync with specific date:
  ```python
  sync_gumroad_sales(after_date="2026-01-01")
  ```

### Transactions Stuck in "NEW" Status

- Run transaction processor:
  - Via Dashboard: Click "Process Transactions"
  - Via console: `process_pending_transactions()`

### Failed Transactions

1. Check error message in Gumroad Transaction
2. Fix underlying issue (e.g., missing account)
3. Retry via console:
   ```python
   from gumroad_sales.services.process_transactions import retry_failed_transaction
   retry_failed_transaction("SALE_ID_HERE")
   ```

---

## API Endpoints Reference

Based on research, Gumroad API v2 endpoints:

### Sales
```
GET https://api.gumroad.com/v2/sales
Parameters:
  - after: YYYY-MM-DD
  - before: YYYY-MM-DD
  - page: integer
  - product_id: string
  - email: string
```

### Payouts (May Not Be Available Yet)
```
GET https://api.gumroad.com/v2/payouts
Parameters:
  - page: integer
```

**Note:** Payouts API was proposed in GitHub issue #585 but may not be publicly available. The app handles this gracefully.

---

## Data Flow Comparison

### Old System (CSV Import)
```
Gumroad Payout CSV
    ↓
Manual Download
    ↓
Manual Upload to ERPNext
    ↓
Gumroad Sale + Sales Invoice
```

### New System (API Sync)
```
Gumroad API (automatic)
    ↓
Gumroad Transaction (raw storage)
    ↓
Sales Invoice + Payment Entry (automatic)
```

**Benefits:**
- ✅ Automatic syncing
- ✅ Real-time (or near real-time)
- ✅ Idempotent (safe to retry)
- ✅ Raw data preserved
- ✅ Failed transactions can be retried
- ✅ Audit trail in raw JSON

---

## Best Practices

1. **Start with Manual Sync**
   - Test first sync manually
   - Verify all results
   - Then enable auto-sync

2. **Monitor Sync Dashboard**
   - Check regularly for FAILED status
   - Review error messages
   - Retry failed transactions

3. **Keep Raw Data**
   - Don't delete Gumroad Transaction records
   - They provide audit trail
   - Can regenerate invoices if needed

4. **Reconcile Payouts**
   - When Gumroad pays out to your bank
   - Create Journal Entry:
     ```
     Dr. Bank Account
         Cr. Gumroad Clearing
     ```

5. **Handle Refunds**
   - Refunded sales marked as "REFUNDED" status
   - Create Credit Note manually in ERPNext
   - Link to original invoice

---

## Security Notes

- **API Token is a Password**
  - Treat like password
  - Don't share
  - Don't commit to git
  - Stored encrypted in ERPNext

- **Token Permissions**
  - Token has full access to your Gumroad account
  - Can read all sales data
  - Cannot modify or delete

- **Rotate Tokens**
  - Generate new token periodically
  - Update in Gumroad Settings
  - Old token becomes invalid

---

## Further Reading

- [Gumroad API Documentation](https://gumroad.com/api)
- [NoCodeAPI Gumroad Docs](https://nocodeapi.com/docs/gumroad-api/)
- [Gumroad Help Center](https://gumroad.com/help)

---

## Support

For issues:
1. Check Error Log in ERPNext
2. Review this documentation
3. Check [GitHub Issues](https://github.com/yourusername/gumroad_sales)

---

**Last Updated:** 2026-05-07
