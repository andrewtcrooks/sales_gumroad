# Installation Guide

## Prerequisites

- Frappe/ERPNext bench already installed
- Access to bench command line
- ERPNext site configured

## Step 1: Install the App

```bash
# Navigate to your bench directory
cd ~/frappe-bench

# Get the app
bench get-app /Users/andrew/git/erpnext/gumroad_sales

# Install on your site
bench --site your-site.local install-app gumroad_sales

# Migrate
bench --site your-site.local migrate

# Restart
bench restart
```

## Step 2: Create Chart of Accounts

Go to: **Accounting > Chart of Accounts**

Create these accounts if they don't exist:

### Assets
- **Gumroad Clearing - USD**
  - Account Type: Bank
  - Parent: Current Assets

### Income
- **Gumroad Sales - USD**
  - Account Type: Income Account
  - Parent: Direct Income

### Expenses
- **Gumroad Fees - USD**
  - Account Type: Expense Account
  - Parent: Direct Expenses

### Liabilities
- **Sales Tax Payable - USD**
  - Account Type: Tax
  - Parent: Current Liabilities

## Step 3: Create Item

Go to: **Stock > Item**

Create new item:
- Item Code: `GUMROAD-PRODUCT`
- Item Name: `Gumroad Product`
- Item Group: `Products` (or `Services`)
- Stock UOM: `Nos`
- Is Stock Item: No
- Default Income Account: Gumroad Sales - USD

## Step 4: Configure Gumroad Settings

Go to: **Gumroad Sales > Gumroad Settings**

Fill in:

### Account Settings
- Company: Select your company
- Gumroad Clearing Account: Select the account created above
- Gumroad Fees Account: Select the account created above
- Gumroad Sales Account: Select the account created above
- Sales Tax Payable Account: Select the account created above
- Default Gumroad Item: Select GUMROAD-PRODUCT
- Default Customer Group: Individual
- Default Territory: All Territories

### WA State DOR Settings
- DOR TRA Number: Your WA State tax registration number
- DOR Preparer Name: Your name
- DOR Email: Your email
- DOR Phone: Your phone (format: 123-456-7890)
- B&O Tax Classification: Select appropriate classification
  - **Retailing** for product sales
  - **Service and Other Activities** for services/SaaS
  - **Wholesaling** for wholesale

Save settings.

## Step 5: Test Import

1. Go to **Gumroad Sales > Gumroad Sale**
2. Click **Menu > Import CSV** (top right)
3. Upload your Gumroad CSV file
4. Check that Sales Invoices were created
5. Verify Payment Entries in Gumroad Clearing account

## Step 6: Test DOR Export

1. Go to **Gumroad Sales > DOR Export Tool**
2. Select year and quarter
3. Click **Generate DOR CSV**
4. File will download automatically
5. Review CSV contents

## Troubleshooting

### Import fails with "Account not found"
- Verify all accounts exist in Chart of Accounts
- Check account names match exactly in Settings
- Ensure accounts are linked to correct company

### Custom fields not showing
```bash
bench --site your-site.local migrate
bench --site your-site.local clear-cache
```

### DOR export shows $0
- Ensure Sales Invoices are submitted (not draft)
- Check posting dates fall within quarter
- Verify company matches settings

## Next Steps

1. Import historical Gumroad sales
2. Set up recurring imports (manual or automated)
3. Reconcile Gumroad payouts to bank
4. Generate quarterly DOR reports
5. File taxes at https://dor.wa.gov/

## Support

For issues or questions, check:
- README.md in app directory
- ERPNext documentation: https://docs.erpnext.com/
- Frappe framework docs: https://frappeframework.com/docs
