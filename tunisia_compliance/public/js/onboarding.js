// tunisia_compliance/public/js/onboarding.js

function run_onboarding_check() {
    if (!frappe.user.has_role("System Manager")) {
        return;
    }

    frappe.call({
        method: "tunisia_compliance.setup.get_onboarding_status",
        callback: function(r) {
            if (!r.message) return;

            const status_data = r.message;
            const status = typeof status_data === 'object' ? status_data.status : status_data;

            if (status === "no_coa") {
                show_coa_setup_dialog(status_data.companies);
            } else if (status === "no_company") {
                show_no_company_dialog();
            } else if (status === "show_welcome") {
                show_welcome_dialog();
            }
        }
    });
}

function show_coa_setup_dialog(companies) {
    let company_options = companies.map(c => ({ label: c, value: c }));

    const dialog = new frappe.ui.Dialog({
        title: __("Complete Your Company Setup"),
        fields: [
            {
                fieldtype: "HTML",
                options: `<p>${__("The following Tunisian companies are missing the correct Chart of Accounts.")}</p>`
            },
            {
                fieldname: "company_to_setup",
                fieldtype: "Select",
                label: __("Select Company to Configure"),
                options: company_options,
                reqd: 1,
                default: company_options[0].value
            }
        ],
        primary_action_label: __("Run Setup Now"),
        primary_action: (values) => {
            dialog.get_primary_btn().prop('disabled', true).text(__('Configuring...'));
            
            frappe.call({
                method: "tunisia_compliance.setup.run_setup_for_company",
                args: {
                    company_name: values.company_to_setup
                },
                callback: (r) => {
                    frappe.msgprint({
                        title: __('Success'),
                        message: __(r.message),
                        indicator: 'green'
                    });
                    // Mark onboarding as complete so we don't show it again
                    frappe.call({ method: "tunisia_compliance.setup.set_onboarding_complete" });
                    dialog.hide();
                    // Optionally, reload the desk
                    setTimeout(() => location.reload(), 2000);
                },
                error: () => {
                     dialog.get_primary_btn().prop('disabled', false).text(__('Run Setup Now'));
                }
            });
        },
        secondary_action_label: __("Do this later"),
        secondary_action: () => {
            frappe.call({ method: "tunisia_compliance.setup.set_onboarding_complete" });
            dialog.hide();
        }
    });

    dialog.show();
}

function show_no_company_dialog() {
    const dialog = new frappe.ui.Dialog({
        title: __("Welcome to Tunisia Compliance"),
        fields: [{ fieldtype: "HTML", options: `<p>${__("The first step is to create a Company with 'Tunisia' as the country.")}</p>` }],
        primary_action_label: __("Go to Company List"),
        primary_action: () => {
            frappe.set_route(["List", "Company", "List"]);
            dialog.hide();
        }
    });
    dialog.show();
}

function show_welcome_dialog() {
    const dialog = new frappe.ui.Dialog({
        title: __("Setup Complete!"),
        fields: [{ fieldtype: "HTML", options: `<p>${__("The Tunisia Compliance app has been successfully configured.")}</p>` }],
        primary_action_label: __("Go to Tunisia Compliance Workspace"),
        primary_action: () => {
            frappe.call({ method: "tunisia_compliance.setup.set_onboarding_complete" });
            frappe.set_route(["Workspaces", "Tunisia Compliance"]);
            dialog.hide();
        },
        secondary_action_label: __("Dismiss"),
        secondary_action: () => {
            frappe.call({ method: "tunisia_compliance.setup.set_onboarding_complete" });
            dialog.hide();
        }
    });
    dialog.show();
}

// Call the main function when the script loads.
run_onboarding_check();