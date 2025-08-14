def get_salary_components():
    # ... return the full dictionary of components ...
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
    return components

def get_income_tax_slab():
    # ... return the dictionary for the tax slab ...
    slab = {
        "doctype": "Income Tax Slab",
        "name": "Barème IRPP Tunisie - 2025",
        # ... all other slab properties
    }
    return slab