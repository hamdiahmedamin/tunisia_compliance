// Copyright (c) 2025, Aminos and contributors
// For license information, please see license.txt

frappe.ui.form.on("VAT Declaration", {
	refresh: function (frm) {
		if (frm.doc.docstatus === 0) {
			frm.add_custom_button(__("Get Declaration Data"), function () {
				frm.call("get_declaration_data").then(() => {
                    // Success message is handled on the server
					frm.refresh();
				});
			}).addClass("btn-primary");
		}
	},

    // Add client-side triggers for any manual change to re-calculate totals
    company: function(frm) {
        if (!frm.doc.fiscal_year) {
            frappe.db.get_value("Company", { "name": frm.doc.company }, "default_fiscal_year").then(r => {
                if (r.message && r.message.default_fiscal_year) {
                    frm.set_value("fiscal_year", r.message.default_fiscal_year);
                }
            });
        }
    },
    previous_month_credit: function(frm) {
        frm.trigger("recalculate_totals");
    },
    number_of_invoices_issued: function(frm) {
        frm.trigger("recalculate_totals");
    },

    recalculate_totals: function(frm) {
        // This is a client-side re-calculation for immediate feedback
        let total_collected = 0;
        (frm.doc.vat_collected_details || []).forEach(d => total_collected += flt(d.vat_amount));
        frm.set_value("total_vat_collected", total_collected);

        let total_deductible_gs = 0;
        (frm.doc.vat_deductible_details_gs || []).forEach(d => total_deductible_gs += flt(d.vat_amount));
        let total_deductible_fa = 0;
        (frm.doc.vat_deductible_details_fa || []).forEach(d => total_deductible_fa += flt(d.vat_amount));
        let total_deductible = total_deductible_gs + total_deductible_fa;
        frm.set_value("total_vat_deductible", total_deductible);

        let total_deductible_with_credit = total_deductible + flt(frm.doc.previous_month_credit);
        frm.set_value("vat_due", total_collected - total_deductible_with_credit);

        let total_withholding = 0;
        (frm.doc.withholding_tax_details || []).forEach(d => total_withholding += flt(d.tax_amount));
        frm.set_value("total_withholding_tax_due", total_withholding);
        
        let total_other_taxes = 0;
        (frm.doc.other_taxes_details || []).forEach(d => total_other_taxes += flt(d.tax_amount));
        frm.set_value("total_other_taxes_due", total_other_taxes);

        // Fetch stamp duty rate from settings if not already loaded
        if (!frappe.sys_defaults.stamp_duty_per_invoice) {
            frappe.db.get_single_value("Tunisia Compliance Settings", "stamp_duty_per_invoice").then(rate => {
                frappe.sys_defaults.stamp_duty_per_invoice = flt(rate) || 1.0;
                frm.trigger("recalculate_stamp_duty_and_grand_total");
            });
        } else {
            frm.trigger("recalculate_stamp_duty_and_grand_total");
        }
    },

    recalculate_stamp_duty_and_grand_total: function(frm) {
        let stamp_duty_rate = flt(frappe.sys_defaults.stamp_duty_per_invoice);
        let stamp_duty_due = flt(frm.doc.number_of_invoices_issued) * stamp_duty_rate;
        frm.set_value("total_stamp_duty_due", stamp_duty_due);

        let vat_due_payable = frm.doc.vat_due > 0 ? frm.doc.vat_due : 0;
        frm.set_value(
            "grand_total_payable",
            vat_due_payable + flt(frm.doc.total_withholding_tax_due) + stamp_duty_due + flt(frm.doc.total_other_taxes_due)
        );
    }
});