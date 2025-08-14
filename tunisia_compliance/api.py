# Copyright (c) 2025, Aminos and contributors
# For license information, please see license.txt

import frappe
import os
from frappe import _
from erpnext.accounts.doctype.chart_of_accounts_importer.chart_of_accounts_importer import import_coa
from frappe.utils.file_manager import save_file

@frappe.whitelist()
def check_and_get_companies():
    """
    Checks which companies, if any, need a Chart of Accounts.
    This is called by the onboarding script on login.
    Returns a list of company names that have zero accounts.
    """
    companies_without_chart = []
    all_companies = frappe.get_all("Company", fields=["name"])

    for company in all_companies:
        # Check if this company has zero accounts. If so, it needs a chart.
        if not frappe.db.exists("Account", {"company": company.name}):
            companies_without_chart.append(company.name)

    return companies_without_chart

@frappe.whitelist()
def run_chart_import(company):
    """
    Creates a Frappe File from the app's CSV and calls the core Chart of Accounts Importer function.
    This is called by the onboarding wizard or a settings page button.
    """
    if not company or not frappe.db.exists("Company", company):
        frappe.throw(_("A valid Company name is required."))

    # Safety check to prevent running on a company that already has a Tunisian chart
    if frappe.db.exists("Account", {"company": company, "account_name": ["like", "%(Classe %)%"]}):
        frappe.msgprint(_("A Tunisian Chart of Accounts may already exist for {0}. Aborting.").format(company))
        return

    # 1. Get the path to the master CSV file within your app
    app_path = frappe.get_app_path("tunisia_compliance")
    # Ensure this path matches where you stored your CSV file
    csv_path = os.path.join(app_path, "public", "downloads", "tunisian_chart_template.csv")

    if not os.path.exists(csv_path):
        frappe.log_error(f"Chart template not found at {csv_path}", "Tunisia Compliance App Error")
        frappe.throw(_("Tunisian Chart of Accounts template file not found in the app. Please contact the app developer."))

    # 2. Create a Frappe File document from your CSV to pass to the importer
    try:
        with open(csv_path, "rb") as f:
            file_content = f.read()

        saved_file = save_file(
            fname="tunisian_chart_template.csv",
            content=file_content,
            doctype="Company",
            docname=company,
            is_private=1, # Important to keep it private
        )
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Tunisia Compliance: File Creation Failed")
        frappe.throw(_("Failed to create temporary file document from template. Check Error Log for details."))

    # 3. Call the core ERPNext importer function
    try:
        frappe.msgprint(_("Starting import process... This may take a moment."), indicator="orange", title=_("Importing"))

        # This is the core function from the ERPNext DocType we are calling
        import_coa(company=company, file_name=saved_file.name)

        frappe.msgprint(_("Tunisian Chart of Accounts imported successfully for {0}!").format(frappe.bold(company)), indicator='green', title=_('Success'))

    except Exception:
        frappe.log_error(frappe.get_traceback(), "Tunisia Compliance: Chart Import Failed")
        frappe.throw(_("An error occurred during the chart import process. Please check the Error Log for details."))
