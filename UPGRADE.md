# Upgrading to API Sync Version

Guide for upgrading existing Gumroad Sales installations to the new API sync version.

---

## What's New

- **Gumroad Transaction DocType** - stores raw API data
- **Gumroad Payout DocType** - tracks payout batches
- **Gumroad Settings** - new API fields (token, sync settings)
- **API Services** - automated sync from Gumroad API
- **Sync Dashboard** - manual controls and status monitoring
- **Scheduled Tasks** - automatic sync based on frequency

---

## Upgrade Steps

### 1. Pull Latest Code

```bash
cd ~/frappe-bench/apps/gumroad_sales
git pull origin main  # or your branch
```

### 2. Run Migration

```bash
cd ~/frappe-bench
bench --site your-site.local migrate
```

This will:
- Create new DocTypes (Gumroad Transaction, Gumroad Payout)
- Add new fields to Gumroad Settings
- Create new page (Gumroad Sync Dashboard)

### 3. Restart Services

```bash
bench restart
```

### 4. Configure API Settings

1. Go to **Gumroad Sales > Gumroad Settings**
2. Fill in new **API Settings** section:
   - API Access Token (get from Gumroad)
   - Enable Auto Sync (optional)
   - Sync Frequency (optional)
3. Verify existing **Account Settings** still configured
4. Save

---

## Backward Compatibility

✅ **Fully Compatible**

- Existing Gumroad Sale records: Unchanged
- CSV import still works
- All existing invoices/payments: Unchanged
- Can use both CSV and API sync

**Migration is non-destructive.**

---

## Testing After Upgrade

### 1. Verify Gumroad Settings

```bash
ssh frappe@erpnext
cd ~/frappe-bench
bench --site your-site.local console
```

```python
settings = frappe.get_single("Gumroad Settings")
print(settings.as_dict())
```

Verify new fields exist:
- `api_access_token`
- `enable_auto_sync`
- `sync_frequency`
- `last_sales_sync`
- `last_payout_sync`

### 2. Check New DocTypes

```python
# Check Gumroad Transaction exists
frappe.get_doc("DocType", "Gumroad Transaction")

# Check Gumroad Payout exists
frappe.get_doc("DocType", "Gumroad Payout")
```

### 3. Test Sync Dashboard

1. Go to **Gumroad Sales > Gumroad Sync Dashboard**
2. Should load without errors
3. Shows sync status and statistics

---

## Migration Issues

### Issue: "DocType Gumroad Transaction does not exist"

**Solution:**
```bash
bench --site your-site.local migrate --skip-failing
bench --site your-site.local clear-cache
bench --site your-site.local migrate
```

### Issue: "Field api_access_token does not exist"

**Solution:**
```bash
bench --site your-site.local clear-cache
bench --site your-site.local migrate
bench restart
```

### Issue: Sync Dashboard not showing

**Solution:**
```bash
bench --site your-site.local build
bench restart
```

---

## Rollback (If Needed)

If you need to rollback:

```bash
cd ~/frappe-bench/apps/gumroad_sales
git checkout <previous-commit>
cd ~/frappe-bench
bench --site your-site.local migrate
bench restart
```

**Note:** New DocTypes will remain but won't cause issues if unused.

---

## Data Migration (Optional)

If you want to import historical CSV data as Gumroad Transactions:

```python
# This is optional - CSV import still works independently
# Only do this if you want historical data in new format

from gumroad_sales.services.sync_sales import create_transaction_from_sale

# Fetch historical data from Gumroad API
from gumroad_sales.services.gumroad_api import get_gumroad_client

client = get_gumroad_client()
sales = client.fetch_all_sales(after_date="2024-01-01")

for sale in sales:
    create_transaction_from_sale(sale)
```

---

## Next Steps

After successful upgrade:

1. **Configure API Token**
   - See [GUMROAD_API_SETUP.md](GUMROAD_API_SETUP.md)

2. **Test Manual Sync**
   - Use Sync Dashboard
   - Run small date range first

3. **Enable Auto Sync**
   - Once tested, enable in settings

4. **Monitor**
   - Check dashboard regularly
   - Review Error Log for issues

---

**Questions?**

- Check [GUMROAD_API_SETUP.md](GUMROAD_API_SETUP.md)
- Review [README.md](README.md)
- Check ERPNext Error Log
