# Gumroad Sales - Build Summary

## What We Built

Complete Frappe app for ERPNext that handles:
1. **Gumroad CSV imports** → Sales Invoices + Payment Entries
2. **WA State DOR quarterly tax exports** → CSV for upload to dor.wa.gov

## App Structure

```
gumroad_sales/
├── README.md              # Full documentation
├── INSTALL.md             # Step-by-step setup guide
├── QUICKSTART.md          # 5-minute overview
├── setup.py               # Package definition
├── requirements.txt       # Dependencies
├── license.txt            # MIT license
│
├── gumroad_sales/
│   ├── __init__.py
│   ├── hooks.py           # App configuration
│   ├── modules.txt        # Module definition
│   ├── api.py             # Import/export API methods
│   │
│   ├── fixtures/
│   │   └── custom_field.json  # Custom fields for Sales Invoice
│   │
│   └── gumroad_sales/     # Main module
│       ├── doctype/
│       │   ├── gumroad_sale/
│       │   │   ├── gumroad_sale.json
│       │   │   ├── gumroad_sale.py
│       │   │   └── gumroad_sale_list.js  # CSV import button
│       │   │
│       │   └── gumroad_settings/
│       │       ├── gumroad_settings.json
│       │       └── gumroad_settings.py
│       │
│       └── page/
│           └── dor_export_tool/
│               ├── dor_export_tool.json
│               └── dor_export_tool.js    # Export UI
```

## Components

### 1. DocTypes

**Gumroad Sale**
- Stores individual Gumroad sales
- Fields: purchase_id, date, item, buyer, amounts, fees
- Links to created Sales Invoice + Payment Entry

**Gumroad Settings** (Single)
- Configuration for accounts, company, DOR info
- Stores TRA number, preparer details, B&O classification

### 2. Custom Fields (auto-installed)

**Sales Invoice**:
- `custom_sales_platform` - Select: Gumroad/Stripe/Direct/Other
- `custom_gumroad_purchase_id` - Links to Gumroad sale

### 3. API Methods

**`import_gumroad_csv(file_content)`**
- Parses Gumroad CSV
- Creates Gumroad Sale records
- Generates Sales Invoices with proper accounting
- Creates Payment Entries to Gumroad Clearing
- Returns summary of created/skipped/errors

**`export_dor_csv(year, quarter)`**
- Queries all Sales Invoices for quarter
- Calculates B&O tax base (gross receipts)
- Generates DOR-format CSV
- Returns CSV content + summary

### 4. UI Components

**Import Button** (gumroad_sale_list.js)
- Shows in Gumroad Sale list view
- Upload CSV dialog
- Calls import API
- Shows results

**DOR Export Page** (dor_export_tool)
- Standalone page in Gumroad Sales module
- Year/quarter selector
- Generate button
- Auto-downloads CSV

## Accounting Flow

### Gumroad Sale Import

For each sale, creates:

**Sales Invoice**:
```
Item: Gumroad Product @ $5.00
Tax: Sales Tax (collected) +$1.34
Tax: Gumroad Fees (deduct) -$4.35
---
Total: $2.00 (what you actually receive)
```

**Journal Entry** (via Payment Entry):
```
Dr. Gumroad Clearing    $10.65  (what lands in your account)
Dr. Gumroad Fees        $4.35   (expense)
    Cr. Gumroad Sales           $15.00 (gross income)
```

Sales tax handled separately based on whether Gumroad remits it.

### DOR Export

Queries ALL Sales Invoices (not just Gumroad) for date range.

Generates CSV with:
```
ACCOUNT,<TRA>,Q12026,<preparer>,<email>,<phone>
TAX,2,0,<gross_sales>        # B&O Retailing
TAX,45,0,<sales_tax>          # Sales tax (if applicable)
```

Ready to upload to https://dor.wa.gov/

## Installation

```bash
cd ~/frappe-bench
bench get-app /Users/andrew/git/erpnext/gumroad_sales
bench --site yoursite.local install-app gumroad_sales
bench --site yoursite.local migrate
bench restart
```

## Configuration Required

1. **Chart of Accounts**: Create 4 accounts (clearing, sales, fees, tax)
2. **Item**: Create default Gumroad product item
3. **Settings**: Configure Gumroad Settings with accounts + DOR info

See INSTALL.md for detailed steps.

## Usage

### Import Gumroad CSV
1. Gumroad Sale → Menu → Import CSV
2. Upload file
3. Done

### Export DOR Tax Report
1. DOR Export Tool
2. Select year/quarter
3. Generate
4. Upload to DOR

## Test Data

Sample CSV included in root:
- `Gumroad Payout of 2026-03-12.csv`
- 3 sales, $10.65 net total
- Good for testing import

## Next Steps for User

1. **Install** the app on your ERPNext bench
2. **Create** the required accounts
3. **Configure** Gumroad Settings
4. **Import** your Gumroad history
5. **Test** DOR export for current quarter
6. **Set reminder** for quarterly tax filing

## Features

✅ Automatic Sales Invoice creation
✅ Proper accounting (fees, taxes, clearing)
✅ Customer auto-creation from email
✅ Duplicate detection (won't re-import same sale)
✅ DOR-compliant CSV format
✅ Combines all sales channels (Gumroad + Stripe + others)
✅ UI for import and export
✅ Error handling and logging
✅ Custom fields for platform tracking

## Tech Stack

- **Frappe Framework** 14.x+
- **ERPNext** 14.x+
- **Python** 3.8+
- **JavaScript** (ES6)

## License

MIT - Free to use, modify, distribute

---

**Ready to install!** See QUICKSTART.md for 5-minute setup.
