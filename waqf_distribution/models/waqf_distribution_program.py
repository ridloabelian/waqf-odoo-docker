# Copyright 2026 Amal Produktif, Forum Wakaf Produktif (FWP) & Asosiasi Nazhir Indonesia (ANI)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import api, fields, models


class WaqfDistributionProgram(models.Model):
    _name = "waqf.distribution.program"
    _description = "Program Penyaluran Manfaat Wakaf"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name asc"

    name = fields.Char(
        string="Nama Program",
        required=True,
        tracking=True,
        help="Contoh: Beasiswa Kader Umat, Layanan Klinik Wakaf Sehat, dsb.",
    )
    code = fields.Char(
        string="Kode Program",
        required=True,
        copy=False,
        help="Kode identifikasi program, contoh: PRG-EDU-01",
    )
    sector = fields.Selection(
        selection=[
            ("education", "Pendidikan & Beasiswa"),
            ("health", "Layanan Kesehatan & Medis"),
            ("economic", "Pemberdayaan Ekonomi & UMKM"),
            ("social_religious", "Dakwah, Ibadah & Sarana Keagamaan"),
            ("disaster", "Kemanusiaan & Tanggap Bencana"),
            ("general_welfare", "Kesejahteraan Umum & Lingkungan"),
        ],
        string="Sektor Peruntukan",
        default="education",
        required=True,
        tracking=True,
        help="Sektor peruntukan pemanfaatan wakaf sesuai UU No. 41/2004.",
    )
    default_expense_account_id = fields.Many2one(
        comodel_name="account.account",
        string="Akun Beban Penyaluran (PSAK 412)",
        domain="[('is_waqf_account', '=', True), ('waqf_net_asset_type', '=', 'unrestricted'), ('account_type', '=', 'expense')]",
        help="Akun beban penyaluran standar PSAK 412 yang bersumber dari Aset Neto Tidak Terikat.",
    )
    budget_allocated = fields.Monetary(
        string="Plafon Alokasi Anggaran",
        currency_field="currency_id",
        tracking=True,
        help="Total plafon alokasi hasil bersih pengelolaan wakaf yang dianggarkan untuk program ini.",
    )
    budget_realized = fields.Monetary(
        string="Realisasi Penyaluran",
        currency_field="currency_id",
        compute="_compute_budget_stats",
        store=True,
        help="Total nominal yang telah berhasil disalurkan (status Terbayar/Disbursed).",
    )
    budget_remaining = fields.Monetary(
        string="Sisa Plafon Anggaran",
        currency_field="currency_id",
        compute="_compute_budget_stats",
        store=True,
    )
    distribution_ids = fields.One2many(
        comodel_name="waqf.distribution",
        inverse_name="program_id",
        string="Riwayat Penyaluran",
    )
    distribution_count = fields.Integer(
        string="Jumlah Transaksi",
        compute="_compute_budget_stats",
        store=True,
    )
    start_date = fields.Date(
        string="Tanggal Mulai",
    )
    end_date = fields.Date(
        string="Tanggal Berakhir",
    )
    description = fields.Text(
        string="Deskripsi & Sasaran Manfaat",
    )
    currency_id = fields.Many2one(
        comodel_name="res.currency",
        string="Mata Uang",
        default=lambda self: self.env.company.currency_id,
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Entitas Nazhir",
        default=lambda self: self.env.company,
        required=True,
    )
    active = fields.Boolean(
        string="Aktif",
        default=True,
    )

    @api.depends("distribution_ids", "distribution_ids.state", "distribution_ids.amount", "budget_allocated")
    def _compute_budget_stats(self):
        for record in self:
            disbursed = record.distribution_ids.filtered(lambda d: d.state == "disbursed")
            realized = sum(disbursed.mapped("amount"))
            record.distribution_count = len(disbursed)
            record.budget_realized = realized
            record.budget_remaining = record.budget_allocated - realized
