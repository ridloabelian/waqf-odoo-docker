# Copyright 2026 Forum Wakaf Produktif (FWP / fwp.or.id)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

{
    "name": "Tata Kelola Wakaf - Core & Operasional",
    "summary": "Master Data Wakif, Pencatatan AIW/APAIW, dan Sertifikat Wakaf Standar BWI",
    "version": "17.0.1.0.0",
    "category": "Accounting/Localizations",
    "author": "Forum Wakaf Produktif (FWP), Odoo Community Association (OCA)",
    "website": "https://fwp.or.id",
    "license": "LGPL-3",
    "application": True,
    "installable": True,
    "auto_install": False,
    "depends": [
        "base",
        "mail",
    ],
    "data": [
        "security/waqf_security.xml",
        "security/ir.model.access.csv",
        "data/ir_sequence_data.xml",
        "data/waqf_type_data.xml",
        "views/res_partner_views.xml",
        "views/waqf_type_views.xml",
        "views/waqf_pledge_views.xml",
        "views/waqf_menus.xml",
        "report/waqf_certificate_report.xml",
        "report/waqf_certificate_template.xml",
    ],
    "images": [
        "static/description/icon.png",
    ],
}
