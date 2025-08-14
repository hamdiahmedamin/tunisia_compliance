import frappe
import os
import shutil
from erpnext.accounts.doctype.chart_of_accounts_importer.chart_of_accounts_importer import import_coa
from frappe.utils.file_manager import save_file

# ==============================================================================
# HOOK TRIGGERS
# ==============================================================================


def after_install():
    """
    Runs ONCE when the app is installed.
    Sets up GLOBAL elements and then triggers the setup for EXISTING companies.
    """
    print("\nRunning Tunisia Compliance initial setup...")
    copy_chart_of_accounts_json()
    create_global_payroll_elements()
    existing_companies = frappe.get_all(
        "Company", filters={"country": "Tunisia"}, pluck="name")
    if existing_companies:
        print("Found existing Tunisian companies. Configuring them now...")
        for company_name in existing_companies:
            setup_tunisian_company(company_name)
    print("Initial setup for Tunisia Compliance completed.\n")


def on_create_company(company_doc, method):
    """
    Runs EVERY time a NEW company is created. This hook is correct.
    """
    if company_doc.country == "Tunisia":
        print(
            f"\nNew Tunisian company created: {company_doc.name}. Running compliance setup...")
        setup_tunisian_company(company_doc.name)

# ==============================================================================
# MASTER SETUP FUNCTION
# ==============================================================================


def setup_tunisian_company(company_name):
    """
    This is the master function that configures a single company.
    It's called by both after_install (for existing companies) and on_create_company.
    """
    print(f"--- Configuring company: {company_name} ---")
    company_doc = frappe.get_doc("Company", company_name)
    # --- Task 1: Create the Chart of Accounts if the correct one isn't set ---
    if not company_doc.chart_of_accounts or "Tunisia" not in company_doc.chart_of_accounts:
        if frappe.db.exists("Account", {"company": company_name}):
            print(
                f"-> Found an existing, non-Tunisian Chart of Accounts for {company_name}. Deleting it before import.")
            frappe.db.delete("Account", {"company": company_name})
            frappe.db.delete("Party Account", {"company": company_name})
        print(
            f"-> Installing Tunisian Chart of Accounts for {company_name}...")
        try:
            app_path = frappe.get_app_path("tunisia_compliance")
            csv_path = os.path.join(
                app_path, "regional", "data", "tn_plan_comptable_general_avec_code.csv")
            if not os.path.exists(csv_path):
                raise FileNotFoundError(
                    f"Chart template CSV not found at {csv_path}")
            with open(csv_path, "rb") as f:
                file_content = f.read()
            saved_file = frappe.get_doc({"doctype": "File", "file_name": "tn_plan_comptable_general_avec_code.csv",
                                        "attached_to_doctype": "Company", "attached_to_name": company_name, "content": file_content, "is_private": 0})
            saved_file.insert(ignore_permissions=True)
            import_coa(company=company_name, file_name=saved_file.file_url)
            frappe.db.set_value(
                "Company", company_name, "chart_of_accounts", "Tunisia - Plan Comptable Tunisien")
            print(
                f"-> Successfully created Chart of Accounts for {company_name}.")
        except Exception as e:
            print(
                f"-> FATAL ERROR: Failed to create Chart of Accounts for {company_name}. Error: {e}")
            frappe.log_error(frappe.get_traceback(),
                             "Tunisia Compliance CoA Setup Failed")
            return
    else:
        print(
            f"-> Tunisian Chart of Accounts already exists for {company_name}. Skipping creation.")
    # --- Task 2: Link Payroll Accounts ---
    if not link_payroll_accounts_to_company(company_name):
        print(
            f"--- Aborting further payroll setup for {company_name} due to account linking failure. ---")
        return
    # --- Task 3: Set Company-Specific Defaults on GLOBAL Components ---
    set_component_defaults_for_company(company_name)
    # --- Task 4: Create Company-Specific Salary Structures ---
    create_payroll_structures(company_name)  # Changed from singular
    # --- Task 5: Other Company-Specific Setups ---
    create_tax_templates(company_name)
    setup_default_vat_accounts_for_company(company_name)

    # --- Task 6: NEW - Set ALL other default accounts ---
    setup_default_accounts_for_company(company_name)
    print(f"--- Finished configuration for {company_name} ---")

# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================


def copy_chart_of_accounts_json():
    print("Copying Chart of Accounts template for Setup Wizard...")
    source_app_path = frappe.get_app_path("tunisia_compliance")
    source_file_path = os.path.join(
        source_app_path, "regional", "data", "tn_plan_comptable_general_avec_code.json")
    dest_app_path = frappe.get_app_path("erpnext")
    dest_folder_path = os.path.join(
        dest_app_path, "accounts", "doctype", "account", "chart_of_accounts", "verified")
    os.makedirs(dest_folder_path, exist_ok=True)
    dest_file_path = os.path.join(dest_folder_path, "tn.json")
    if os.path.exists(source_file_path):
        try:
            shutil.copy2(source_file_path, dest_file_path)
        except Exception:
            pass  # Fails in CI, but not critical
    else:
        print(
            f"-> ERROR: Source Chart of Accounts file not found at: {source_file_path}")


def link_payroll_accounts_to_company(company_name):
    print(
        f"-> Linking payroll accounts for {company_name} using direct DB writes...")
    try:
        accounts_to_find = {
            "custom_cnss_liability_account": "%CNSS%",
            "custom_tax_liability_account": "%Etat, impôts et taxes retenus à la source%",
            "custom_salary_expense_account": "%Salaires - 6400%",
            "custom_social_charges_expense_account": "%Cotisations de sécurité sociale sur salaires - 6470%"
        }
        overall_success = True
        for field_name, search_pattern in accounts_to_find.items():
            account_name = frappe.db.get_value("Account", {"account_name": [
                                               "like", search_pattern], "company": company_name, "is_group": 0})
            if account_name:
                frappe.db.set_value("Company", company_name,
                                    field_name, account_name)
            else:
                overall_success = False
        if overall_success:
            return True
        else:
            return False
    except Exception:
        return False


def create_tax_templates(company):
    if frappe.db.exists("Sales Taxes and Charges Template", {"title": "TVA 19% - TN", "company": company}):
        return
    print(f"-> Creating tax templates for {company}...")
    try:
        tva_collected_account = frappe.db.get_value("Account", {"account_name": [
                                                    "like", "TVA collectée sur les débits%"], "company": company})
        stamp_duty_account = frappe.db.get_value("Account", {"account_name": [
                                                 "like", "Produits des activités annexes%"], "company": company})
        tva_deductible_account = frappe.db.get_value("Account", {"account_name": [
                                                     "like", "TVA sur autres biens et services%"], "company": company})
        if not all([tva_collected_account, stamp_duty_account, tva_deductible_account]):
            raise Exception("One or more required tax accounts not found.")
        sales_templates = {"TVA 19% - TN": 19.0,
                           "TVA 13% - TN": 13.0, "TVA 7% - TN": 7.0}
        for title, rate in sales_templates.items():
            st_template = frappe.new_doc("Sales Taxes and Charges Template")
            st_template.title = title
            st_template.company = company
            st_template.append("taxes", {"charge_type": "On Net Total",
                               "account_head": tva_collected_account, "rate": rate, "description": f"TVA @ {int(rate)}%"})
            st_template.append("taxes", {
                               "charge_type": "Actual", "account_head": stamp_duty_account, "tax_amount": 1.0, "description": "Timbre Fiscal"})
            st_template.insert(ignore_permissions=True)
        purchase_templates = {
            "TVA 19% (Achats) - TN": 19.0, "TVA 13% (Achats) - TN": 13.0, "TVA 7% (Achats) - TN": 7.0}
        for title, rate in purchase_templates.items():
            pt_template = frappe.new_doc("Purchase Taxes and Charges Template")
            pt_template.title = title
            pt_template.company = company
            pt_template.append("taxes", {"charge_type": "On Net Total", "account_head": tva_deductible_account,
                               "rate": rate, "description": f"TVA Déductible @ {int(rate)}%"})
            pt_template.insert(ignore_permissions=True)
    except Exception:
        pass


def setup_default_vat_accounts_for_company(company):
    print(f"-> Setting up default VAT accounts in Settings for {company}...")
    settings = frappe.get_doc("Tunisia Compliance Settings")
    existing_collected = [d for d in settings.vat_collected_accounts if frappe.get_cached_value(
        "Account", d.account, "company") != company]
    existing_deductible = [d for d in settings.vat_deductible_accounts if frappe.get_cached_value(
        "Account", d.account, "company") != company]
    settings.vat_collected_accounts = existing_collected
    settings.vat_deductible_accounts = existing_deductible
    sales_tax_parent = frappe.db.get_value("Account", {"account_name": [
                                           "like", "Taxes sur le chiffre d'affaires collectées par l'entreprise%"], "company": company, "is_group": 1})
    purchase_tax_parent = frappe.db.get_value("Account", {"account_name": [
                                              "like", "Taxes sur le chiffre d'affaires déductibles%"], "company": company, "is_group": 1})
    if sales_tax_parent:
        for acc in frappe.get_all("Account", filters={"parent_account": sales_tax_parent, "is_group": 0}, pluck="name"):
            settings.append("vat_collected_accounts", {"account": acc})
    if purchase_tax_parent:
        for acc in frappe.get_all("Account", filters={"parent_account": purchase_tax_parent, "is_group": 0}, pluck="name"):
            settings.append("vat_deductible_accounts", {"account": acc})
    settings.save(ignore_permissions=True)

# --- PAYROLL HELPER FUNCTIONS ---


def create_global_payroll_elements():
    """
    Creates Salary Components and Slabs GLOBALLY for all payroll types.
    """
    print("-> Creating global Salary Components and Tax Slabs...")
    components = {
        "Salaire de Base": {"type": "Earning", "abbr": "SB", "is_tax_applicable": 1},
        "Paiement par Feuille de Temps": {"type": "Earning", "abbr": "H", "is_tax_applicable": 1, "salary_slip_based_on_timesheet": 1},
        "Commission sur Ventes": {"type": "Earning", "abbr": "COMM", "is_tax_applicable": 1},
        "Indemnité SIVP": {"type": "Earning", "abbr": "SIVP", "is_tax_applicable": 0},
        "Indemnité de Transport": {"type": "Earning", "abbr": "IND-T", "is_tax_applicable": 0},
        "Prime de Présence": {"type": "Earning", "abbr": "PR-P", "is_tax_applicable": 1},
        "Autres Primes (Imposables)": {"type": "Earning", "abbr": "PR-I", "is_tax_applicable": 1},
        "CNSS - Cotisation Salariale (9.18%)": {"type": "Deduction", "abbr": "CNSS-S", "is_tax_applicable": 1},
        "Frais Professionnels": {"type": "Deduction", "abbr": "FP", "is_tax_applicable": 1},
        "Déduction - Chef de Famille": {"type": "Deduction", "abbr": "DED-CF", "is_tax_applicable": 1},
        "Déduction - Enfant Standard": {"type": "Deduction", "abbr": "DED-ES", "is_tax_applicable": 1},
        "Déduction - Enfant Supérieur": {"type": "Deduction", "abbr": "DED-ESUP", "is_tax_applicable": 1},
        "Déduction - Enfant Handicapé": {"type": "Deduction", "abbr": "DED-EH", "is_tax_applicable": 1},
        "Impôt sur le Revenu (IRPP)": {"type": "Deduction", "abbr": "IRPP", "variable_based_on_taxable_salary": 1},
        "Contribution Sociale de Solidarité (CSS)": {"type": "Deduction", "abbr": "CSS"},
        "Avance sur Salaire": {"type": "Deduction", "abbr": "AVANCE"},
        "CNSS - Part Patronale (16.57%)": {"type": "Deduction", "abbr": "CNSS-P", "do_not_include_in_total": 1},
        "Taxe de Formation Professionnelle (TFP)": {"type": "Deduction", "abbr": "TFP", "do_not_include_in_total": 1},
        "Fonds de Logement Social (FOPROLOS)": {"type": "Deduction", "abbr": "FOPROLOS", "do_not_include_in_total": 1},
    }
    for name, props in components.items():
        if not frappe.db.exists("Salary Component", name):
            doc = frappe.new_doc("Salary Component")
            doc.salary_component = name
            doc.salary_component_abbr = props.get("abbr", name[:5])
            doc.type = props.get("type")
            doc.is_tax_applicable = props.get("is_tax_applicable", 0)
            doc.variable_based_on_taxable_salary = props.get(
                "variable_based_on_taxable_salary", 0)
            doc.do_not_include_in_total = props.get(
                "do_not_include_in_total", 0)
            doc.salary_slip_based_on_timesheet = props.get(
                "salary_slip_based_on_timesheet", 0)
            doc.insert(ignore_permissions=True, ignore_mandatory=True)

    slab_name = "Barème IRPP Tunisie - 2025"
    if not frappe.db.exists("Income Tax Slab", slab_name):
        frappe.get_doc(
            {
                "doctype": "Income Tax Slab", 
                "name": slab_name, 
                "country": "Tunisia", 
                "effective_from": "2025-01-01", 
                "slabs": [
                    {
                        "from_amount": 0,
                        "to_amount": 8000,
                        "percent_deduction": 0
                    },
                    {
                        "from_amount": 8000.01,
                        "to_amount": 20000,
                        "percent_deduction": 26
                    }, 
                    {
                        "from_amount": 20000.01, 
                        "to_amount": 30000, 
                        "percent_deduction": 28
                    },
                    {
                        "from_amount": 30000.01, 
                        "to_amount": 50000, 
                        "percent_deduction": 32
                    },
                    {
                        "from_amount": 80000.01, 
                        "to_amount": 80000, 
                        "percent_deduction": 34
                    },  
                    {
                        "from_amount": 80000.01, 
                        "to_amount": 99999999, 
                        "percent_deduction": 35
                    }]}).insert(ignore_permissions=True, ignore_mandatory=True)


def set_component_defaults_for_company(company):
    print(f"-> Setting component account defaults for {company}...")
    try:
        company_accounts = frappe.get_cached_doc("Company", company)
        cnss_account = company_accounts.custom_cnss_liability_account
        etat_impots_account = company_accounts.custom_tax_liability_account
        salaire_expense_account = company_accounts.custom_salary_expense_account

        component_account_map = {
            "Salaire de Base": salaire_expense_account,
            "Paiement par Feuille de Temps": salaire_expense_account,
            "Commission sur Ventes": salaire_expense_account,
            "Indemnité SIVP": salaire_expense_account,
            "Indemnité de Transport": salaire_expense_account,
            "Prime de Présence": salaire_expense_account,
            "Autres Primes (Imposables)": salaire_expense_account,
            "CNSS - Cotisation Salariale (9.18%)": cnss_account,
            "Impôt sur le Revenu (IRPP)": etat_impots_account,
            "Contribution Sociale de Solidarité (CSS)": etat_impots_account,
            "CNSS - Part Patronale (16.57%)": cnss_account,
            "Taxe de Formation Professionnelle (TFP)": etat_impots_account,
            "Fonds de Logement Social (FOPROLOS)": etat_impots_account
        }

        for name, account in component_account_map.items():
            if frappe.db.exists("Salary Component", name):
                comp_doc = frappe.get_doc("Salary Component", name)
                if not comp_doc.get("accounts", {"company": company}):
                    comp_doc.append(
                        "accounts", {"company": company, "account": account})
                    comp_doc.save(ignore_permissions=True)
    except Exception:
        pass


def create_payroll_structures(company):
    """Creates all necessary payroll structures for the company."""
    print(f"-> Creating all Salary Structures for {company}...")
    _create_standard_structure(company)
    _create_hourly_structure(company)
    _create_commission_structure(company)
    _create_sivp_structure(company)


def _create_standard_structure(company):
    structure_name = f"Structure Salariale Standard - {company}"
    if frappe.db.exists("Salary Structure", structure_name):
        return
    print(f"   - Creating Standard Salary Structure...")
    try:
        company_doc = frappe.get_doc("Company", company)
        social_charges_expense_account = company_doc.custom_social_charges_expense_account
        doc = frappe.new_doc("Salary Structure")
        doc.name = structure_name
        doc.company = company
        doc.is_active = "Yes"
        doc.income_tax_slab = "Barème IRPP Tunisie - 2025"
        doc.append("earnings", {"salary_component": "Salaire de Base",
                   "amount_based_on_formula": 1, "formula": "base", "default_amount": 1000})
        doc.append("earnings", {
                   "salary_component": "Indemnité de Transport", "default_amount": 70})
        doc.append("earnings", {"salary_component": "Prime de Présence"})
        doc.append(
            "earnings", {"salary_component": "Autres Primes (Imposables)"})
        doc.append("deductions", {"salary_component": "CNSS - Cotisation Salariale (9.18%)",
                   "amount_based_on_formula": 1, "formula": "base * 0.0918"})
        doc.append("deductions", {"salary_component": "Frais Professionnels",
                   "amount_based_on_formula": 1, "formula": "min(base * 0.10, 2000 / 12)"})
        doc.append("deductions", {"salary_component": "Déduction - Chef de Famille",
                   "condition": "employee.custom_head_of_household == 1", "amount_based_on_formula": 1, "formula": "300 / 12"})
        doc.append("deductions", {"salary_component": "Déduction - Enfant Standard", "condition": "employee.custom_standard_children > 0",
                   "amount_based_on_formula": 1, "formula": "employee.custom_standard_children * 100"})
        doc.append("deductions", {"salary_component": "Déduction - Enfant Supérieur", "condition": "employee.custom_he_children > 0",
                   "amount_based_on_formula": 1, "formula": "employee.custom_he_children * (2000 / 12)"})
        doc.append("deductions", {"salary_component": "Déduction - Enfant Handicapé", "condition": "employee.custom_disabled_children > 0",
                   "amount_based_on_formula": 1, "formula": "employee.custom_disabled_children * (2000 / 12)"})
        doc.append("deductions", {
                   "salary_component": "Impôt sur le Revenu (IRPP)"})
        doc.append("deductions", {"salary_component": "Contribution Sociale de Solidarité (CSS)",
                   "amount_based_on_formula": 1, "formula": "taxable_earning * 0.01"})
        doc.append("deductions", {"salary_component": "Avance sur Salaire"})
        doc.append("deductions", {"salary_component": "CNSS - Part Patronale (16.57%)", "amount_based_on_formula": 1,
                   "formula": "base * 0.1657", "expense_account": social_charges_expense_account})
        doc.append("deductions", {"salary_component": "Taxe de Formation Professionnelle (TFP)",
                   "amount_based_on_formula": 1, "formula": "base * 0.02", "expense_account": social_charges_expense_account})
        doc.append("deductions", {"salary_component": "Fonds de Logement Social (FOPROLOS)",
                   "amount_based_on_formula": 1, "formula": "base * 0.01", "expense_account": social_charges_expense_account})
        doc.insert(ignore_permissions=True, ignore_mandatory=True)
    except Exception as e:
        print(
            f"-> ERROR while creating Standard Salary Structure for {company}. Error: {e}")


def _create_hourly_structure(company):
    structure_name = f"Structure Salariale Horaire - {company}"
    if frappe.db.exists("Salary Structure", structure_name):
        return
    print(f"   - Creating Hourly (Timesheet) Salary Structure...")
    try:
        company_doc = frappe.get_doc("Company", company)
        social_charges_expense_account = company_doc.custom_social_charges_expense_account
        doc = frappe.new_doc("Salary Structure")
        doc.name = structure_name
        doc.company = company
        doc.is_active = "Yes"
        doc.income_tax_slab = "Barème IRPP Tunisie - 2025"
        doc.payroll_frequency = "Monthly"
        doc.salary_slip_based_on_timesheet = 1
        doc.salary_component = "Paiement par Feuille de Temps"
        doc.append("earnings", {
                   "salary_component": "Indemnité de Transport", "default_amount": 70})
        doc.append("deductions", {"salary_component": "CNSS - Cotisation Salariale (9.18%)",
                   "amount_based_on_formula": 1, "formula": "base * 0.0918"})
        doc.append("deductions", {"salary_component": "Frais Professionnels",
                   "amount_based_on_formula": 1, "formula": "min(base * 0.10, 2000 / 12)"})
        doc.append("deductions", {
                   "salary_component": "Impôt sur le Revenu (IRPP)"})
        doc.append("deductions", {"salary_component": "Contribution Sociale de Solidarité (CSS)",
                   "amount_based_on_formula": 1, "formula": "taxable_earning * 0.01"})
        doc.append("deductions", {"salary_component": "Avance sur Salaire"})
        doc.append("deductions", {"salary_component": "CNSS - Part Patronale (16.57%)", "amount_based_on_formula": 1,
                   "formula": "base * 0.1657", "expense_account": social_charges_expense_account})
        doc.append("deductions", {"salary_component": "Taxe de Formation Professionnelle (TFP)",
                   "amount_based_on_formula": 1, "formula": "base * 0.02", "expense_account": social_charges_expense_account})
        doc.append("deductions", {"salary_component": "Fonds de Logement Social (FOPROLOS)",
                   "amount_based_on_formula": 1, "formula": "base * 0.01", "expense_account": social_charges_expense_account})
        doc.insert(ignore_permissions=True, ignore_mandatory=True)
    except Exception as e:
        print(
            f"-> ERROR while creating Hourly Salary Structure for {company}. Error: {e}")


def _create_commission_structure(company):
    """Helper function to create the commission-based salary structure."""
    structure_name = f"Structure Salariale Vente (Commission) - {company}"
    if frappe.db.exists("Salary Structure", structure_name):
        return
    print(f"   - Creating Commission-Based Salary Structure...")
    try:
        company_doc = frappe.get_doc("Company", company)
        social_charges_expense_account = company_doc.custom_social_charges_expense_account
        doc = frappe.new_doc("Salary Structure")
        doc.name = structure_name
        doc.company = company
        doc.is_active = "Yes"
        doc.income_tax_slab = "Barème IRPP Tunisie - 2025"
        doc.append("earnings", {"salary_component": "Salaire de Base",
                   "amount_based_on_formula": 1, "formula": "base", "default_amount": 1000})
        doc.append("earnings", {"salary_component": "Commission sur Ventes"})
        doc.append("deductions", {"salary_component": "CNSS - Cotisation Salariale (9.18%)",
                   "amount_based_on_formula": 1, "formula": "base * 0.0918"})
        doc.append("deductions", {"salary_component": "Frais Professionnels",
                   "amount_based_on_formula": 1, "formula": "min(base * 0.10, 2000 / 12)"})
        doc.append("deductions", {
                   "salary_component": "Impôt sur le Revenu (IRPP)"})
        doc.append("deductions", {"salary_component": "Contribution Sociale de Solidarité (CSS)",
                   "amount_based_on_formula": 1, "formula": "taxable_earning * 0.01"})
        doc.append("deductions", {"salary_component": "Avance sur Salaire"})
        doc.append("deductions", {"salary_component": "CNSS - Part Patronale (16.57%)", "amount_based_on_formula": 1,
                   "formula": "base * 0.1657", "expense_account": social_charges_expense_account})
        doc.append("deductions", {"salary_component": "Taxe de Formation Professionnelle (TFP)",
                   "amount_based_on_formula": 1, "formula": "base * 0.02", "expense_account": social_charges_expense_account})
        doc.append("deductions", {"salary_component": "Fonds de Logement Social (FOPROLOS)",
                   "amount_based_on_formula": 1, "formula": "base * 0.01", "expense_account": social_charges_expense_account})
        doc.insert(ignore_permissions=True, ignore_mandatory=True)
    except Exception as e:
        print(
            f"-> ERROR while creating Commission Salary Structure for {company}. Error: {e}")


def _create_sivp_structure(company):
    """Helper function to create the special SIVP contract salary structure."""
    structure_name = f"Structure Salariale SIVP - {company}"
    if frappe.db.exists("Salary Structure", structure_name):
        return
    print(f"   - Creating SIVP Salary Structure...")
    try:
        company_doc = frappe.get_doc("Company", company)
        social_charges_expense_account = company_doc.custom_social_charges_expense_account
        doc = frappe.new_doc("Salary Structure")
        doc.name = structure_name
        doc.company = company
        doc.is_active = "Yes"
        doc.append("earnings", {"salary_component": "Indemnité SIVP"})
        doc.append("deductions", {"salary_component": "CNSS - Part Patronale (16.57%)", "amount_based_on_formula": 1,
                   "formula": "base * 0.1657", "expense_account": social_charges_expense_account})
        doc.append("deductions", {"salary_component": "Taxe de Formation Professionnelle (TFP)",
                   "amount_based_on_formula": 1, "formula": "base * 0.02", "expense_account": social_charges_expense_account})
        doc.append("deductions", {"salary_component": "Fonds de Logement Social (FOPROLOS)",
                   "amount_based_on_formula": 1, "formula": "base * 0.01", "expense_account": social_charges_expense_account})
        doc.insert(ignore_permissions=True, ignore_mandatory=True)
    except Exception as e:
        print(
            f"-> ERROR while creating SIVP Salary Structure for {company}. Error: {e}")


def setup_default_accounts_for_company(company):
    """
    Sets all default accounts in Company, Stock Settings, and other doctypes
    based on the final, correct configuration. This is a company-specific task.
    """
    print(f"-> Setting up all default accounts for company: {company}...")

    try:
        # --- Define the mapping of fields to account numbers ---
        # This map is based on your final screenshots and our discussions.
        company_defaults = {
            "default_bank_account": "Comptes en dinars - 5321",
            "default_cash_account": "Caisse en dinars - 5411",
            "default_receivable_account": "Clients - ventes de biens ou de prestations de services - 4111",
            "default_payable_account": "Fournisseurs - achats de biens ou de prestations de services - 4011",
            "default_expense_account": "Achats de marchandises - 607",
            "default_income_account": "Ventes de marchandises - 707",
            "default_discount_account": "Frais sur effets - 6275",
            "round_off_account": "Charges financières liées à une modif. comptable - 658",
            "default_deferred_revenue_account": "Produits constatés d'avance - 472",
            "default_deferred_expense_account": "Charges constatées d'avance - 471",
            "accumulated_depreciation_account": "Amortissements des immob. corporelles - 282",
            "depreciation_expense_account": "Immobilisations corporelles - 68112",
            "capital_work_in_progress_account": "Immobilisations corporelles en cours - 232",
            "asset_received_but_not_billed": "Fournisseurs d'immobilisations - 4084",
            "default_payroll_payable_account": "Personnel - rémunérations dues - 421",
            "default_employee_advance_account": "Personnel - avances et acomptes - 425",
            "default_expense_claim_payable_account": "Personnel - rémunérations dues - 421",
            # Corrected from 311 for trading
            "default_inventory_account": "Matières premières - 311",
            "stock_adjustment_account": "Variation des stocks (approvisionnements et marchandises) - 603",
            "stock_received_but_not_billed": "Fournisseurs d'exploitation - 4081",
            "default_provisional_account": "Fournisseurs d'exploitation - 4081",
        }

        # --- Set defaults on the Company doctype ---
        for field, account_name_fragment in company_defaults.items():
            # Find the full account name from the CoA for this company
            full_account_name = frappe.db.get_value("Account", {"account_name": [
                                                    "like", f"%{account_name_fragment}%"], "company": company, "is_group": 0})
            if full_account_name:
                frappe.db.set_value("Company", company,
                                    field, full_account_name)
                print(f"   - Company.{field} set to: {full_account_name}")
            else:
                print(
                    f"   - WARNING: Could not find account for '{account_name_fragment}' to set Company.{field}")

        print("-> Default accounts setup completed.")

    except Exception as e:
        print(
            f"-> ERROR: An error occurred while setting default accounts for {company}. Error: {e}")
        frappe.log_error(frappe.get_traceback(),
                         "Tunisia Default Accounts Setup Failed")

# Renamed function call in setup_tunisian_company to match the new plural name


def create_payroll_structure(company):
    create_payroll_structures(company)

@frappe.whitelist()
def get_onboarding_status():
    """
    Checks the onboarding flag and system status.
    Returns a list of Tunisian companies that are missing the correct CoA.
    """
    if bool(frappe.db.get_single_value('Tunisia Compliance Settings', 'custom_onboarding_complete')):
        return "complete"

    tunisian_companies = frappe.get_all("Company", filters={"country": "Tunisia"}, fields=["name", "chart_of_accounts"])
    if not tunisian_companies:
        return "no_company"

    # Find companies that are missing the correct Chart of Accounts
    companies_needing_setup = []
    for company in tunisian_companies:
        if not company.chart_of_accounts or "Tunisia" not in company.chart_of_accounts:
            companies_needing_setup.append(company.name)

    if companies_needing_setup:
        # Return the list of companies that need fixing
        return {"status": "no_coa", "companies": companies_needing_setup}

    # If everything is set up, show the welcome message
    return "show_welcome"

@frappe.whitelist()
def run_setup_for_company(company_name):
    """
    A dedicated whitelisted function to re-run the setup for a single company.
    This is what the new dialog will call.
    """
    from tunisia_compliance.setup import setup_tunisian_company # Import the main function
    try:
        setup_tunisian_company(company_name)
        return f"Setup for {company_name} completed successfully."
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), f"Onboarding Setup Failed for {company_name}")
        frappe.throw(_("An error occurred while running the setup for {0}. Please check the Error Log.").format(company_name))


@frappe.whitelist()
def set_onboarding_complete():
    """
    Sets the 'custom_onboarding_complete' flag in Tunisia Compliance Settings to 1.
    This is called when the user dismisses any onboarding dialog.
    """
    try:
        settings = frappe.get_doc("Tunisia Compliance Settings")
        settings.custom_onboarding_complete = 1
        settings.save(ignore_permissions=True)
        return True
    except Exception:
        # Fail silently if settings doctype isn't created yet
        return False