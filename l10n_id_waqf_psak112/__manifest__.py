# Copyright 2026 Forum Wakaf Produktif (FWP) & Asosiasi Nazhir Indonesia (ANI)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

{
    "name": "Akuntansi Wakaf PSAK 412 (PSAK 112) & Regulasi UU 41/2004",
    "summary": "Standar Akuntansi Wakaf PSAK 412 (sebelumnya PSAK 112), Engine account.report, Klasifikasi Aset Neto, Batasan Hak Nazhir 10%, dan Dashboard OWL",
    "version": "19.0.1.0.0",
    "category": "Accounting/Localizations",
    "author": "Forum Wakaf Produktif (FWP), Asosiasi Nazhir Indonesia (ANI), Odoo Community Association (OCA)",
    "website": "https://fwp.or.id, https://ani.or.id",
    "license": "LGPL-3",
    "application": False,
    "installable": True,
    "auto_install": False,
    "depends": [
        "account",
        "waqf_core",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/account_chart_template_data.xml",
        "data/account_report_psak112_data.xml",
        "views/account_account_views.xml",
        "views/account_move_views.xml",
        "views/nazhir_share_views.xml",
        "views/psak112_report_wizard_views.xml",
        "views/psak112_dashboard_views.xml",
        "views/waqf_accounting_menus.xml",
        "report/psak112_reports.xml",
        "report/psak112_report_templates.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "l10n_id_waqf_psak112/static/src/components/**/*",
        ],
    },
    "images": [
        "static/description/icon.png",
    ],
}
