frappe.pages['gumroad_sync_dashboard'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Gumroad Sync Dashboard',
		single_column: true
	});

	page.add_inner_button(__('Sync Sales Now'), function() {
		sync_sales_now(page);
	});

	page.add_inner_button(__('Process Transactions'), function() {
		process_transactions_now(page);
	});

	page.add_inner_button(__('Refresh'), function() {
		load_dashboard(page);
	});

	load_dashboard(page);
}

function load_dashboard(page) {
	frappe.call({
		method: 'sales_gumroad.services.sync_sales.get_sync_status',
		callback: function(r) {
			if (r.message) {
				render_dashboard(page, r.message);
			}
		}
	});
}

function render_dashboard(page, data) {
	let html = `
		<div class="gumroad-sync-dashboard" style="padding: 20px;">
			<div class="row">
				<div class="col-md-6">
					<div class="card">
						<div class="card-header"><h5>Sync Status</h5></div>
						<div class="card-body">
							<table class="table table-bordered">
								<tr>
									<td><strong>Auto Sync Enabled</strong></td>
									<td>${data.auto_sync_enabled ? 'Yes' : 'No'}</td>
								</tr>
								<tr>
									<td><strong>Sync Frequency</strong></td>
									<td>${data.sync_frequency || 'N/A'}</td>
								</tr>
								<tr>
									<td><strong>Last Sales Sync</strong></td>
									<td>${data.last_sales_sync || 'Never'}</td>
								</tr>
								<tr>
									<td><strong>Last Payout Sync</strong></td>
									<td>${data.last_payout_sync || 'Never'}</td>
								</tr>
							</table>
						</div>
					</div>
				</div>

				<div class="col-md-6">
					<div class="card">
						<div class="card-header"><h5>Transaction Statistics</h5></div>
						<div class="card-body">
							<table class="table table-bordered">
								<tr>
									<td><strong>Total Transactions</strong></td>
									<td>${data.total_transactions || 0}</td>
								</tr>
								<tr>
									<td><strong>NEW (Pending)</strong></td>
									<td><span class="badge badge-warning">${data.status_counts.NEW || 0}</span></td>
								</tr>
								<tr>
									<td><strong>PROCESSED</strong></td>
									<td><span class="badge badge-success">${data.status_counts.PROCESSED || 0}</span></td>
								</tr>
								<tr>
									<td><strong>FAILED</strong></td>
									<td><span class="badge badge-danger">${data.status_counts.FAILED || 0}</span></td>
								</tr>
								<tr>
									<td><strong>REFUNDED</strong></td>
									<td><span class="badge badge-secondary">${data.status_counts.REFUNDED || 0}</span></td>
								</tr>
								<tr>
									<td><strong>SKIPPED</strong></td>
									<td><span class="badge badge-secondary">${data.status_counts.SKIPPED || 0}</span></td>
								</tr>
							</table>
						</div>
					</div>
				</div>
			</div>

			<div class="row" style="margin-top: 20px;">
				<div class="col-md-12">
					<div class="alert alert-info">
						<strong>How it works:</strong>
						<ol>
							<li><strong>Sync Sales:</strong> Fetches sales from Gumroad API and stores as Gumroad Transaction records</li>
							<li><strong>Process Transactions:</strong> Converts NEW transactions into Sales Invoices and Payment Entries</li>
						</ol>
						<p><strong>Note:</strong> Configure API token in Gumroad Settings before syncing.</p>
					</div>
				</div>
			</div>
		</div>
	`;

	page.$body.html(html);
}

function sync_sales_now(page) {
	frappe.show_alert({message: 'Starting sales sync...', indicator: 'blue'});

	frappe.call({
		method: 'sales_gumroad.services.sync_sales.manual_sync',
		freeze: true,
		freeze_message: 'Syncing sales from Gumroad...',
		callback: function(r) {
			if (r.message) {
				let stats = r.message;
				if (stats.success) {
					frappe.show_alert({
						message: `Sync complete: ${stats.new} new, ${stats.duplicate} duplicate, ${stats.failed} failed`,
						indicator: 'green'
					});
				} else {
					frappe.msgprint({
						title: 'Sync Error',
						message: stats.error || 'Unknown error',
						indicator: 'red'
					});
				}
				load_dashboard(page);
			}
		},
		error: function(r) {
			frappe.msgprint({
				title: 'Sync Error',
				message: r.message || 'Failed to sync sales',
				indicator: 'red'
			});
		}
	});
}

function process_transactions_now(page) {
	frappe.show_alert({message: 'Starting transaction processing...', indicator: 'blue'});

	frappe.call({
		method: 'sales_gumroad.services.process_transactions.manual_process',
		freeze: true,
		freeze_message: 'Processing Gumroad transactions...',
		callback: function(r) {
			if (r.message) {
				let stats = r.message;
				if (stats.success) {
					frappe.show_alert({
						message: `Processing complete: ${stats.processed} processed, ${stats.failed} failed`,
						indicator: 'green'
					});
				} else {
					frappe.msgprint({
						title: 'Processing Error',
						message: stats.error || 'Unknown error',
						indicator: 'red'
					});
				}
				load_dashboard(page);
			}
		},
		error: function(r) {
			frappe.msgprint({
				title: 'Processing Error',
				message: r.message || 'Failed to process transactions',
				indicator: 'red'
			});
		}
	});
}
