# Copyright (c) 2025, Aminos and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate, add_months, get_first_day, get_last_day, flt

class VATDeclaration(Document):
    # This will run on save
    def validate(self):
        self.calculate_totals()

    # This is the main server-side method called by the button
    @frappe.whitelist()
    def get_declaration_data(self):
        if not self.fiscal_year or not self.month or not self.company:
            frappe.throw(_("Please select Company, Fiscal Year, and Month first."))

        # Clear existing data
        for field in ["vat_collected_details", "vat_deductible_details_gs", "vat_deductible_details_fa", "withholding_tax_details", "other_taxes_details"]:
            self.set(field, [])

        start_date, end_date = self._get_period_dates()

        self._fetch_vat_collected(start_date, end_date)
        self._fetch_vat_deductible(start_date, end_date)
        self._fetch_withholding_tax(start_date, end_date)
        self._fetch_stamp_duty(start_date, end_date)
        self._fetch_other_taxes(start_date, end_date)
        self._fetch_previous_month_credit(start_date)

        self.calculate_totals()
        self.save()
        frappe.msgprint(_("Declaration details have been fetched successfully."), indicator="green", title=_("Success"))

    def calculate_totals(self):
        # VAT Summary
        self.total_vat_collected = sum(flt(d.vat_amount) for d in self.vat_collected_details)
        total_deductible_gs = sum(flt(d.vat_amount) for d in self.vat_deductible_details_gs)
        total_deductible_fa = sum(flt(d.vat_amount) for d in self.vat_deductible_details_fa)
        self.total_vat_deductible = total_deductible_gs + total_deductible_fa
        total_deductible_with_credit = flt(self.total_vat_deductible) + flt(self.previous_month_credit)
        self.vat_due = flt(self.total_vat_collected) - total_deductible_with_credit

        # Other Taxes Summary
        self.total_withholding_tax_due = sum(flt(d.tax_amount) for d in self.withholding_tax_details)
        
        stamp_duty_rate = flt(frappe.db.get_single_value("Tunisia Compliance Settings", "stamp_duty_per_invoice") or 1.0)
        self.total_stamp_duty_due = flt(self.number_of_invoices_issued) * stamp_duty_rate
        
        self.total_other_taxes_due = sum(flt(d.tax_amount) for d in self.other_taxes_details)

        # Grand Total
        vat_due_payable = flt(self.vat_due) if flt(self.vat_due) > 0 else 0
        self.grand_total_payable = (
            vat_due_payable +
            flt(self.total_withholding_tax_due) +
            flt(self.total_stamp_duty_due) +
            flt(self.total_other_taxes_due)
        )

    def _get_period_dates(self):
        month_map = {
            "January": 1, "February": 2, "March": 3, "April": 4, "May": 5, "June": 6,
            "July": 7, "August": 8, "September": 9, "October": 10, "November": 11, "December": 12
        }
        month_index = month_map.get(self.month)
        fiscal_year_doc = frappe.get_doc("Fiscal Year", self.fiscal_year)
        
        year = fiscal_year_doc.year_start_date.year
        if month_index < fiscal_year_doc.year_start_date.month:
            year = fiscal_year_doc.year_end_date.year
            
        ref_date = f"{year}-{month_index}-01"
        return get_first_day(ref_date), get_last_day(ref_date)

    def _fetch_vat_collected(self, start_date, end_date):
        invoices = frappe.get_all("Sales Invoice", filters={"company": self.company, "docstatus": 1, "posting_date": ["between", [start_date, end_date]]}, pluck="name")
        if not invoices: return

        # Base query for standard VAT
        query = """
            SELECT account_head, rate, SUM(base_tax_amount) as base_amount, SUM(tax_amount) as vat_amount
            FROM `tabSales Taxes and Charges`
            WHERE parent IN %(invoices)s AND (account_head LIKE %(tva_pattern)s)
            GROUP BY rate
        """
        params = {"invoices": tuple(invoices), "tva_pattern": "%TVA%"}
        
        # Conditionally exclude suspended VAT if checkbox is unchecked
        if not self.fetch_suspended_vat:
            query = query.replace("WHERE parent", "WHERE account_head NOT LIKE %(suspendu_pattern)s AND parent")
            params["suspendu_pattern"] = "%Suspendue%"

        sales_vat_details = frappe.db.sql(query, params, as_dict=1)
        
        for row in sales_vat_details:
            self.append("vat_collected_details", { "account": row.account_head, "vat_rate": row.rate, "base_amount": row.base_amount, "vat_amount": row.vat_amount })

    def _fetch_vat_deductible(self, start_date, end_date):
        invoices = frappe.get_all("Purchase Invoice", filters={"company": self.company, "docstatus": 1, "posting_date": ["between", [start_date, end_date]]}, pluck="name")
        if not invoices: return
        
        # Get the specific account for VAT on Fixed Assets
        vat_on_assets_account = frappe.db.get_value("Account", {"company": self.company, "account_name": ["like", "%TVA sur immobilisations%"]}) or ""

        purchase_vat_details = frappe.db.sql("""
            SELECT account_head, rate, SUM(base_tax_amount) as base_amount, SUM(tax_amount) as vat_amount
            FROM `tabPurchase Taxes and Charges`
            WHERE parent IN %(invoices)s AND account_head LIKE %(tva_pattern)s AND rate > 0
            GROUP BY account_head, rate
        """, {"invoices": tuple(invoices), "tva_pattern": "%TVA%"}, as_dict=1)

        for row in purchase_vat_details:
            target_table = "vat_deductible_details_fa" if row.account_head == vat_on_assets_account else "vat_deductible_details_gs"
            self.append(target_table, { "account": row.account_head, "vat_rate": row.rate, "base_amount": row.base_amount, "vat_amount": row.vat_amount })

    def _fetch_withholding_tax(self, start_date, end_date):
        wh_tax_accounts = frappe.get_all("Account", filters={"company": self.company, "account_name": ["like", "%Retenue à la source%"]}, pluck="name")
        if not wh_tax_accounts: return

        purchase_withholding = frappe.db.sql("""
            SELECT account_head as tax_type, SUM(base_tax_amount) as base_amount, SUM(tax_amount) as tax_amount
            FROM `tabPurchase Taxes and Charges`
            WHERE parenttype = 'Purchase Invoice'
            AND account_head IN %(accounts)s
            AND parent IN (SELECT name FROM `tabPurchase Invoice` WHERE company=%(company)s AND docstatus=1 AND posting_date BETWEEN %(start_date)s AND %(end_date)s)
            GROUP BY account_head
        """, {"accounts": tuple(wh_tax_accounts), "company": self.company, "start_date": start_date, "end_date": end_date}, as_dict=1)
        self.extend("withholding_tax_details", purchase_withholding)

    def _fetch_stamp_duty(self, start_date, end_date):
        invoices = frappe.get_all("Sales Invoice", filters={"company": self.company, "docstatus": 1, "posting_date": ["between", [start_date, end_date]]}, pluck="name")
        self.number_of_invoices_issued = len(invoices)

    def _fetch_other_taxes(self, start_date, end_date):
        # --- Payroll Taxes ---
        payroll_taxes = frappe.db.sql("""
            SELECT salary_component as tax_type, SUM(amount) as tax_amount
            FROM `tabSalary Detail`
            WHERE parenttype = 'Salary Slip' AND docstatus = 1
            AND salary_component IN ('Contribution Sociale de Solidarité (CSS)', 'Impôt sur le Revenu (IRPP)', 'Taxe de Formation Professionnelle (TFP)', 'Fonds de Logement Social (FOPROLOS)')
            AND parent IN (SELECT name FROM `tabSalary Slip` WHERE company=%(company)s AND start_date >= %(start_date)s AND end_date <= %(end_date)s)
            GROUP BY salary_component
        """, {"company": self.company, "start_date": start_date, "end_date": end_date}, as_dict=1)
        self.extend("other_taxes_details", payroll_taxes)

        # --- TCL ---
        total_sales_ht = sum(flt(d.base_amount) for d in self.vat_collected_details)
        self.append("other_taxes_details", { "tax_type": "Taxe sur les Collectivités Locales (TCL)", "tax_amount": total_sales_ht * 0.002 })

        # --- FODEC (if enabled) ---
        if self.fetch_fodec:
            invoices = frappe.get_all("Sales Invoice", filters={"company": self.company, "docstatus": 1, "posting_date": ["between", [start_date, end_date]]}, pluck="name")
            if invoices:
                fodec_result = frappe.db.sql("""
                    SELECT SUM(tax_amount)
                    FROM `tabSales Taxes and Charges`
                    WHERE parent IN %(invoices)s AND account_head LIKE %(fodec_pattern)s
                """, {"invoices": tuple(invoices), "fodec_pattern": "%FODEC%"})
                fodec_amount = flt(fodec_result[0][0]) if fodec_result and fodec_result[0] and fodec_result[0][0] else 0.0
                if fodec_amount:
                    self.append("other_taxes_details", { "tax_type": "FODEC", "tax_amount": fodec_amount })

    def _fetch_previous_month_credit(self, start_date):
        previous_period_start = add_months(getdate(start_date), -1)
        
        last_declaration = frappe.db.get_value("VAT Declaration", {
            "company": self.company,
            "docstatus": 1,
            "month": previous_period_start.strftime("%B"),
            "fiscal_year": frappe.db.get_value("Fiscal Year", {"year_start_date": ("<=", previous_period_start), "year_end_date": (">=", previous_period_start)})
        }, "vat_due")
        
        if last_declaration and flt(last_declaration) < 0:
            self.previous_month_credit = abs(last_declaration)