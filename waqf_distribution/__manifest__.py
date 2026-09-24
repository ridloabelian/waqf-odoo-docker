# Copyright 2026 Amal Produktif, Forum Wakaf Produktif (FWP) & Asosiasi Nazhir Indonesia (ANI)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

{
    "name": "Penyaluran Manfaat Wakaf - Mauquf 'Alaih & Program Sosial",
    "summary": "Manajemen Mauquf 'Alaih, Program Penyaluran, Otomasi Beban PSAK 412, dan BAST Standar BWI",
    "version": "19.0.1.0.0",
    "category": "Accounting/Localizations",
    "author": "Amal Produktif, Forum Wakaf Produktif (FWP), Asosiasi Nazhir Indonesia (ANI), Odoo Community Association (OCA)",
    "website": "https://amalproduktif.or.id, https://fwp.or.id, https://ani.or.id",
    "license": "LGPL-3",
    "application": True,
    "installable": True,
    "auto_install": False,
    "depends": [
        "base",
        "mail",
        "account",
        "waqf_core",
        "l10n_id_waqf_psak112",
    ],
    "data": [
        "security/waqf_distribution_security.xml",
        "security/ir.model.access.csv",
        "data/ir_sequence_data.xml",
        "data/waqf_distribution_data.xml",
        "views/waqf_beneficiary_views.xml",
        "views/waqf_distribution_program_views.xml",
        "views/waqf_distribution_views.xml",
        "views/waqf_distribution_menus.xml",
        "report/waqf_distribution_template.xml",
        "report/waqf_distribution_reports.xml",
    ],
}
