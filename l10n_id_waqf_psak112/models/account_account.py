# Copyright 2026 Forum Wakaf Produktif (FWP / fwp.or.id)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import fields, models


class AccountAccount(models.Model):
    _inherit = "account.account"

    is_waqf_account = fields.Boolean(
        string="Akun Entitas Wakaf",
        default=False,
        help="Tandai jika akun ini merupakan bagian dari Bagan Akun Standar PSAK 112.",
    )
    waqf_net_asset_type = fields.Selection(
        selection=[
            ("permanent", "Aset Neto Terikat Permanen (Pokok Wakaf Abadi)"),
            ("temporary", "Aset Neto Terikat Temporer (Wakaf Berjangka)"),
            ("unrestricted", "Aset Neto Tidak Terikat (Surplus Pengelolaan)"),
            ("nazhir_share", "Bagian Imbalan Nazhir (Operasional)"),
            ("none", "Bukan Akun Terikat"),
        ],
        string="Klasifikasi Aset Neto (PSAK 112)",
        default="none",
        help="Klasifikasi Aset Neto sesuai Standar Akuntansi Keuangan PSAK 112: "
             "Permanen (tidak boleh berkurang), Temporer (berjangka), atau Tidak Terikat (surplus siap disalurkan).",
    )
    psak112_category = fields.Selection(
        selection=[
            ("asset_cash_waqf", "Kas & Setara Kas Wakaf"),
            ("asset_receivable", "Piutang & Pembiayaan Pengelolaan"),
            ("asset_investment", "Investasi Portofolio Produktif"),
            ("asset_land", "Aset Wakaf - Tanah"),
            ("asset_building", "Aset Wakaf - Bangunan"),
            ("asset_accum_depr", "Akumulasi Penyusutan Aset Fisik"),
            ("liability_short", "Liabilitas Jangka Pendek"),
            ("liability_temporary_due", "Liabilitas Pengembalian Wakaf Temporer"),
            ("net_asset_permanent", "Aset Neto Terikat Permanen"),
            ("net_asset_temporary", "Aset Neto Terikat Temporer"),
            ("net_asset_unrestricted", "Aset Neto Tidak Terikat"),
            ("receipt_waqf_cash_permanent", "Penerimaan Wakaf Uang Permanen"),
            ("receipt_waqf_cash_temporary", "Penerimaan Wakaf Uang Temporer"),
            ("receipt_waqf_noncash", "Penerimaan Wakaf Selain Uang"),
            ("revenue_yield", "Hasil Pengelolaan & Pengembangan Wakaf"),
            ("expense_nazhir_share", "Bagian Hak Nazhir (Maks 10%)"),
            ("expense_management", "Beban Pengelolaan & Pemeliharaan"),
            ("expense_distribution", "Beban Penyaluran Mauquf 'Alaih"),
            ("other", "Lainnya / Umum"),
        ],
        string="Kategori Pelaporan PSAK 112",
        default="other",
        help="Pemetaan akun untuk penyusunan otomatis 4 Laporan Keuangan PSAK 112.",
    )
