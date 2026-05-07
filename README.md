# Gumroad Sales

Frappe/ERPNext app for syncing Gumroad sales via API or CSV import.

## Features

### 🆕 Automated API Sync (NEW!)
- **Automated Sales Sync**: Sync sales from Gumroad API automatically
  - Scheduled sync (hourly, every 15 min, or daily)
  - Idempotent sync - safe to run multiple times
  - Raw API data preserved for audit trail
  - Transaction status tracking (NEW → PROCESSED → FAILED)
  - Manual sync via dashboard
  - Retry failed transactions
  - See [GUMROAD_API_SETUP.md](GUMROAD_API_SETUP.md) for complete setup guide

### Legacy CSV Import
- **Gumroad CSV Import**: Import Gumroad payout CSVs directly into ERPNext
  - Creates Sales Invoices automatically
  - Tracks Gumroad fees separately
  - Records sales tax collected
  - Creates Payment Entries to Gumroad Clearing account
  - Auto-creates customers from buyer emails

## Installation

```bash
cd ~/frappe-bench
bench get-app /path/to/sales_gumroad
bench --site your-site.local install-app sales_gumroad
bench --site your-site.local migrate
bench restart
```

## Setup

### 1. Configure Chart of Accounts

Create these accounts in your Chart of Accounts (if not already present):

- **Gumroad Clearing - USD** (Asset/Bank type)
- **Gumroad Fees - USD** (Expense)
- **Gumroad Sales - USD** (Income)
- **Sales Tax Payable - USD** (Liability)

### 2. Create Default Item

Create an Item called "Gumroad Product" (or similar) for Gumroad sales.

### 3. Configure Gumroad Settings

Go to: **Gumroad Sales > Gumroad Settings**

Fill in:
- Company
- Account mappings (clearing, fees, sales, tax)
- Default item for Gumroad products
- Default customer group and territory

## Usage

### Importing Gumroad Sales

1. Download CSV from Gumroad payouts
2. Go to **Gumroad Sales > Gumroad Sale > Menu > Import CSV**
3. Upload the CSV file
4. Review created Sales Invoices and Payment Entries

Or via API:

```python
import frappe

with open('Gumroad Payout of 2026-03-12.csv', 'r') as f:
    content = f.read()

result = frappe.call(
    'sales_gumroad.api.import_gumroad_csv',
    file_content=content
)

print(result)
```

## Account Flow

### Gumroad Sale

```
Dr. Gumroad Clearing - USD        $10.65
Dr. Gumroad Fees - USD            $4.35
    Cr. Gumroad Sales - USD                $15.00
```

Net effect: Clearing account shows what you'll receive from Gumroad.

### When Gumroad Payout Hits Bank

Create Journal Entry manually:

```
Dr. Bank Account                  $10.65
    Cr. Gumroad Clearing - USD             $10.65
```

## Tax Reporting

For Washington State DOR tax reporting, install the companion app:

**wa_dor_taxes** - Generates quarterly DOR CSV files combining ALL sales sources (Gumroad, Stripe, Direct, etc.)

## Development

To modify:

```bash
cd ~/frappe-bench/apps/sales_gumroad
# Edit files
bench --site your-site.local migrate
bench restart
```

## License

MIT
