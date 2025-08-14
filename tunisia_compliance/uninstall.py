import frappe
import os
import shutil

# ==============================================================================
# MAIN UNINSTALL HOOK
# ==============================================================================

def before_uninstall():
    """
    This function is called by the before_uninstall hook in hooks.py.
    It orchestrates the complete cleanup of all app-related data and files.
    """
    print("\nRunning Tunisia Compliance cleanup...")
    delete_payroll_elements()
    delete_tax_templates()
    clear_compliance_settings()
    remove_chart_of_accounts_json()
    print("Tunisia Compliance cleanup completed successfully.\n")


# ==============================================================================
# HELPER FUNCTIONS (WITH ROBUST DELETION AND FEEDBACK)
# ==============================================================================

def delete_payroll_elements():
    """
    Deletes all payroll elements created by this app in the CORRECT order.
    """
    print("Removing ALL app-specific payroll elements...")

    structure_patterns = [
        "Structure Salariale Standard - %",
        "Structure Salariale Horaire - %",
        "Structure Salariale Vente (Commission) - %",
        "Structure Salariale SIVP - %"
    ]
    slab_name_to_delete = "Barème IRPP Tunisie - 2025"
    components_to_delete = [
        "Salaire de Base", "Paiement par Feuille de Temps", "Commission sur Ventes", "Indemnité SIVP",
        "Indemnité de Transport", "Prime de Présence", "Autres Primes (Imposables)",
        "CNSS - Cotisation Salariale (9.18%)", "Frais Professionnels", "Déduction - Chef de Famille",
        "Déduction - Enfant Standard", "Déduction - Enfant Supérieur", "Déduction - Enfant Handicapé",
        "Impôt sur le Revenu (IRPP)", "Contribution Sociale de Solidarité (CSS)", "Avance sur Salaire",
        "CNSS - Part Patronale (16.57%)", "Taxe de Formation Professionnelle (TFP)",
        "Fonds de Logement Social (FOPROLOS)"
    ]

    # --- THIS IS THE CRITICAL FIX: Query for each pattern individually ---
    structures_names = []
    for pattern in structure_patterns:
        structures_found = frappe.get_all("Salary Structure", filters={"name": ["like", pattern]}, pluck="name")
        if structures_found:
            structures_names.extend(structures_found)
    # --- END OF FIX ---

    # --- Step 1: Delete Salary Structure Assignments ---
    if structures_names:
        try:
            assignments_to_delete = frappe.get_all("Salary Structure Assignment",
                filters={"salary_structure": ["in", structures_names]}, pluck="name")
            if assignments_to_delete:
                print(f"-> Removing {len(assignments_to_delete)} Salary Structure Assignments...")
                for assignment in assignments_to_delete:
                    frappe.delete_doc("Salary Structure Assignment", assignment, ignore_permissions=True, force=True)
        except Exception:
            print("-> Could not find Salary Structure Assignment DocType, skipping.")

    # --- Step 2: Delete Salary Structures ---
    if structures_names:
        print(f"-> Removing {len(structures_names)} Salary Structures...")
        for structure in structures_names:
            try:
                frappe.delete_doc("Salary Structure", structure, ignore_permissions=True, force=True)
            except Exception as e:
                print(f"-> FAILED to delete '{structure}'. It is likely linked to a submitted Salary Slip. Please cancel the document and try again.")
                print(f"   (Reason: {e})")


    # --- Step 3: Delete the Income Tax Slab ---
    try:
        if frappe.db.exists("Income Tax Slab", slab_name_to_delete):
            print(f"-> Removing Income Tax Slab: {slab_name_to_delete}...")
            frappe.delete_doc("Income Tax Slab", slab_name_to_delete, ignore_permissions=True, force=True)
    except Exception:
        print(f"-> Could not remove Income Tax Slab '{slab_name_to_delete}', it may be in use by a custom document.")

    # --- Step 4: Delete Salary Components ---
    deleted_count = 0
    print(f"-> Removing {len(components_to_delete)} Salary Components...")
    for component_name in components_to_delete:
        if frappe.db.exists("Salary Component", component_name):
            try:
                frappe.delete_doc("Salary Component", component_name, ignore_permissions=True, force=True)
                deleted_count += 1
            except Exception:
                print(f"-> Could not remove component '{component_name}', it may be in use by a custom document.")
    print(f"-> Successfully removed {deleted_count} Salary Components.")


def delete_tax_templates():
    """Deletes tax templates created by this app."""
    print("Removing app-specific Tax Templates...")
    try:
        sales_templates = frappe.get_all("Sales Taxes and Charges Template", filters={"title": ["like", "%- TN%"]}, pluck="name")
        for template in sales_templates:
            frappe.delete_doc("Sales Taxes and Charges Template", template, ignore_permissions=True, force=True)
        purchase_templates = frappe.get_all("Purchase Taxes and Charges Template", filters={"title": ["like", "%(Achats) - TN%"]}, pluck="name")
        for template in purchase_templates:
            frappe.delete_doc("Purchase Taxes and Charges Template", template, ignore_permissions=True, force=True)
        print(f"-> Removed {len(sales_templates)} Sales Tax Templates and {len(purchase_templates)} Purchase Tax Templates.")
    except Exception:
        pass


def clear_compliance_settings():
    """Clears the data from the Tunisia Compliance Settings DocType."""
    print("Clearing Tunisia Compliance Settings...")
    try:
        # Check if the Doctype itself exists before trying to access it
        if frappe.db.exists("DocType", "Tunisia Compliance Settings"):
            settings = frappe.get_doc("Tunisia Compliance Settings")
            settings.vat_collected_accounts = []
            settings.vat_deductible_accounts = []
            settings.save(ignore_permissions=True)
            print("-> Tunisia Compliance Settings have been cleared.")
    except Exception:
        print("-> Tunisia Compliance Settings DocType not found or already deleted. Skipping.")


def remove_chart_of_accounts_json():
    """Removes the copied CoA JSON file from the ERPNext verified charts folder."""
    print("Removing Chart of Accounts template...")
    try:
        dest_app_path = frappe.get_app_path("erpnext")
        dest_file_path = os.path.join(dest_app_path, "accounts", "doctype", "account", "chart_of_accounts", "verified", "tn.json")
        if os.path.exists(dest_file_path):
            os.remove(dest_file_path)
            print("-> Successfully removed Tunisian Chart of Accounts template.")
        else:
            print("-> Chart of Accounts template not found, skipping.")
    except Exception:
        pass