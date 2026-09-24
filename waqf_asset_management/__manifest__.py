# Copyright 2026 Amal Produktif, Forum Wakaf Produktif (FWP) & Asosiasi Nazhir Indonesia (ANI)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

{
    "name": "Penjagaan Aset Wakaf - Manajemen Tanah, Bangunan & Sertifikasi BPN",
    "summary": "Inventarisasi Tanah & Bangunan, Sertifikasi BPN, Tapal Batas Persil, Asuransi Syariah, dan Log Inspeksi Rutin",
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
        "waqf_core",
    ],
    "data": [
        "security/waqf_asset_security.xml",
        "security/ir.model.access.csv",
        "data/ir_sequence_data.xml",
        "views/waqf_asset_views.xml",
        "views/waqf_asset_inspection_views.xml",
        "views/waqf_asset_menus.xml",
        "report/waqf_asset_template.xml",
        "report/waqf_asset_reports.xml",
    ],
}
