frappe.listview_settings['Gumroad Sale'] = {
	onload: function(listview) {
		listview.page.add_action_item(__('Import CSV'), function() {
			show_import_dialog();
		});
	}
};

function show_import_dialog() {
	const d = new frappe.ui.Dialog({
		title: 'Import Gumroad CSV',
		fields: [
			{
				label: 'Gumroad CSV File',
				fieldname: 'csv_file',
				fieldtype: 'Attach',
				reqd: 1,
				description: 'Upload Gumroad payout CSV file'
			}
		],
		primary_action_label: 'Import',
		primary_action(values) {
			// Read file
			frappe.call({
				method: 'frappe.client.get_value',
				args: {
					doctype: 'File',
					filters: { file_url: values.csv_file },
					fieldname: 'content'
				},
				callback: function(r) {
					if (r.message) {
						import_csv(r.message.content);
						d.hide();
					} else {
						// Try to fetch file content directly
						fetch(values.csv_file)
							.then(response => response.text())
							.then(content => {
								import_csv(content);
								d.hide();
							})
							.catch(err => {
								frappe.msgprint(__('Failed to read file'));
							});
					}
				}
			});
		}
	});

	d.show();
}

function import_csv(file_content) {
	frappe.show_alert({
		message: __('Importing Gumroad sales...'),
		indicator: 'blue'
	});

	frappe.call({
		method: 'sales_gumroad.api.import_gumroad_csv',
		args: {
			file_content: file_content
		},
		callback: function(r) {
			if (r.message) {
				const result = r.message;
				const errors_html = result.errors.length > 0
					? `<p><strong>Errors:</strong></p><ul>${result.errors.map(e => `<li>${e}</li>`).join('')}</ul>`
					: '';

				frappe.msgprint({
					title: __('Import Complete'),
					indicator: 'green',
					message: `
						<p><strong>Created:</strong> ${result.created}</p>
						<p><strong>Updated:</strong> ${result.updated}</p>
						${errors_html}
					`
				});

				// Refresh list
				frappe.listview_settings['Gumroad Sale'].refresh();
			}
		},
		error: function(r) {
			frappe.msgprint({
				title: __('Import Failed'),
				indicator: 'red',
				message: r.message || __('An error occurred during import')
			});
		}
	});
}
