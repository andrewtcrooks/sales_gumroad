# Quick Start Guide

## What This Does

**Gumroad Sales** is a Frappe app that:

1. **Imports Gumroad sales** from CSV into ERPNext
   - Creates Sales Invoices automatically
   - Tracks fees and taxes separately
   - Records payouts to clearing account

2. **Exports WA State tax reports**
   - Combines ALL sales (Gumroad, Stripe, etc.)
   - Generates DOR-compliant CSV
   - Ready to upload for quarterly B&O tax filing

## Installation (5 minutes)

```bash
cd ~/frappe-bench
bench get-app /Users/andrew/git/erpnext/gumroad_sales
bench --site your-site.local install-app gumroad_sales
bench --site your-site.local migrate
bench restart
```

## Setup (10 minutes)

### 1. Create Accounts

In **Chart of Accounts**, create:
- Gumroad Clearing - USD (Asset/Bank)
- Gumroad Sales - USD (Income)
- Gumroad Fees - USD (Expense)
- Sales Tax Payable - USD (Liability/Tax)

### 2. Create Item

Create item: `GUMROAD-PRODUCT`
- Item Group: Products
- Is Stock Item: No
- Default Income Account: Gumroad Sales - USD

### 3. Configure Settings

Go to **Gumroad Settings**, fill in:
- Company
- All account mappings
- Default item
- DOR TRA number, email, phone
- B&O classification (probably "Retailing")

## Usage

### Import Gumroad Sales

1. Download CSV from Gumroad
2. Go to **Gumroad Sale** list
3. Click **Menu > Import CSV**
4. Upload file
5. Done! Invoices and payments created.

### Export DOR Tax Report

1. Go to **DOR Export Tool**
2. Select year and quarter
3. Click **Generate**
4. CSV downloads automatically
5. Upload to https://dor.wa.gov/

## Example Workflow

### Monthly: Import Gumroad
- Download payout CSV from Gumroad
- Import via **Gumroad Sale**
- Verify invoices created

### When Gumroad pays out:
Create Journal Entry:
```
Dr. Bank Account          $10.65
    Cr. Gumroad Clearing          $10.65
```

### Quarterly: File Taxes
- Run **DOR Export Tool**
- Download CSV
- Upload to DOR website
- Pay B&O tax

## Data Flow

```
Gumroad CSV
  ↓ Import
Gumroad Sale record
  ↓ Creates
Sales Invoice
  ↓ Accounting
  Dr. Gumroad Clearing  $10.65
  Dr. Gumroad Fees      $4.35
  Dr. Sales Tax         $1.34
      Cr. Sales                    $15.00
      Cr. Sales Tax Payable        $1.34

Quarterly
  ↓ Export
All Sales Invoices → DOR CSV → Upload to WA State
```

## Tax Notes

### B&O Tax (Business & Occupation)
- Taxed on **gross receipts** (before Gumroad fees)
- Rate ~0.47% for retailing, varies by classification
- Quarterly filing required

### Sales Tax
- If Gumroad collects, they may remit directly
- Check your Gumroad settings
- May not need to report if Gumroad handles it

### What Gets Reported
DOR export includes:
- ✅ Gumroad sales
- ✅ Stripe sales (if in ERPNext)
- ✅ Direct sales
- ✅ All submitted invoices in date range

## Files

- `/gumroad_sales/api.py` - Import/export logic
- `/doctype/gumroad_sale/` - Sale record
- `/doctype/gumroad_settings/` - Configuration
- `/page/dor_export_tool/` - Export UI

## Troubleshooting

**Import fails**: Check settings configured correctly

**No accounts**: Create accounts in Chart of Accounts first

**DOR shows $0**: Ensure invoices are submitted, not draft

**Custom fields missing**: Run `bench --site yoursite migrate`

## Next Steps

1. Import your Gumroad history
2. Configure Stripe (if not already)
3. Run test DOR export
4. Set quarterly reminder to file taxes

---

For detailed setup, see INSTALL.md
For technical details, see README.md
