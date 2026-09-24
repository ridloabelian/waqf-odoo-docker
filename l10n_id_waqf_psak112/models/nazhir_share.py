# Copyright 2026 Forum Wakaf Produktif (FWP / fwp.or.id)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError


class WaqfNazhirShare(models.Model):
    _name = "waqf.nazhir.share"
    _description = "Perhitungan & Batasan Hak Nazhir (UU 41/2004)"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "date_to desc, id desc"

    name = fields.Char(
        string="Nomor Referensi",
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _("New"),
    )
    date_from = fields.Date(
        string="Periode Awal",
        required=True,
        default=fields.Date.context_today,
    )
    date_to = fields.Date(
        string="Periode Akhir",
        required=True,
        default=fields.Date.context_today,
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Entitas Nazhir",
        required=True,
        default=lambda self: self.env.company,
    )
    currency_id = fields.Many2one(
        related="company_id.currency_id",
        string="Mata Uang",
        readonly=True,
    )

    # Nilai Finansial Hasil Pengelolaan
    gross_yield = fields.Monetary(
        string="Total Pendapatan/Hasil Pengelolaan Wakaf",
        currency_field="currency_id",
        tracking=True,
        help="Akumulasi pendapatan kotor dari pengelolaan aset wakaf produktif (usaha, sewa, bagi hasil, dividen syariah).",
    )
    direct_expenses = fields.Monetary(
        string="Beban Langsung Pengelolaan & Pemeliharaan",
        currency_field="currency_id",
        tracking=True,
        help="Biaya operasional langsung yang dikeluarkan untuk memelihara dan mengelola aset produktif.",
    )
    net_yield = fields.Monetary(
        string="Hasil Bersih Pengelolaan Wakaf",
        compute="_compute_net_yield",
        store=True,
        currency_field="currency_id",
        tracking=True,
        help="Hasil bersih pengelolaan = Pendapatan Kotor Pengelolaan - Beban Langsung Pengelolaan.",
    )

    # Batasan Regulasi UU 41/2004 Pasal 12 (Maksimal 10%)
    max_nazhir_percentage = fields.Float(
        string="Batas Maksimal Hak Nazhir (%)",
        default=10.0,
        readonly=True,
        help="Berdasarkan UU No. 41 Tahun 2004 Pasal 12: imbalan nazhir tidak melebihi 10% dari hasil bersih.",
    )
    max_allowed_nazhir_share = fields.Monetary(
        string="Maksimal Hak Nazhir yang Diizinkan",
        compute="_compute_max_allowed_nazhir_share",
        store=True,
        currency_field="currency_id",
        help="Nominal tertinggi yang boleh diterima nazhir secara syariah dan legal (10% x Hasil Bersih).",
    )
    actual_nazhir_share = fields.Monetary(
        string="Alokasi Hak Imbalan Nazhir",
        currency_field="currency_id",
        tracking=True,
        help="Nominal hak operasional/imbalan yang diajukan untuk nazhir.",
    )
    actual_percentage = fields.Float(
        string="Persentase Riil Hak Nazhir (%)",
        compute="_compute_actual_percentage",
        store=True,
    )
    surplus_for_mauquf_alaih = fields.Monetary(
        string="Surplus Bersih Hak Mauquf 'Alaih",
        compute="_compute_surplus_mauquf_alaih",
        store=True,
        currency_field="currency_id",
        help="Sisa hasil bersih yang wajib dialokasikan dan disalurkan kepada penerima manfaat (Mauquf 'Alaih).",
    )

    # Akuntansi & Penjurnalan
    journal_id = fields.Many2one(
        comodel_name="account.journal",
        string="Jurnal Penyesuaian",
        domain="[('type', '=', 'general')]",
    )
    nazhir_expense_account_id = fields.Many2one(
        comodel_name="account.account",
        string="Akun Beban Imbalan Nazhir",
        domain="[('psak112_category', '=', 'expense_nazhir_share')]",
    )
    nazhir_payable_account_id = fields.Many2one(
        comodel_name="account.account",
        string="Akun Utang / Titipan Imbalan Nazhir",
        domain="[('account_type', 'in', ('liability_current', 'liability_payable'))]",
    )
    move_id = fields.Many2one(
        comodel_name="account.move",
        string="Entri Jurnal Terbentuk",
        readonly=True,
        copy=False,
    )

    # Status
    state = fields.Selection(
        selection=[
            ("draft", "Draf"),
            ("calculated", "Dihitung"),
            ("verified", "Diverifikasi (Legal/Syariah)"),
            ("posted", "Dijurnal"),
            ("cancel", "Dibatalkan"),
        ],
        string="Status",
        default="draft",
        required=True,
        tracking=True,
    )
    notes = fields.Text(
        string="Catatan Kepatuhan Regulasi",
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", _("New")) == _("New"):
                vals["name"] = self.env["ir.sequence"].next_by_code("waqf.nazhir.share") or _("New")
        return super().create(vals_list)

    @api.depends("gross_yield", "direct_expenses")
    def _compute_net_yield(self):
        for rec in self:
            rec.net_yield = rec.gross_yield - rec.direct_expenses

    @api.depends("net_yield")
    def _compute_max_allowed_nazhir_share(self):
        for rec in self:
            if rec.net_yield > 0:
                rec.max_allowed_nazhir_share = rec.currency_id.round(rec.net_yield * 0.10)
            else:
                rec.max_allowed_nazhir_share = 0.0

    @api.depends("actual_nazhir_share", "net_yield")
    def _compute_actual_percentage(self):
        for rec in self:
            if rec.net_yield > 0 and rec.actual_nazhir_share > 0:
                rec.actual_percentage = (rec.actual_nazhir_share / rec.net_yield) * 100.0
            else:
                rec.actual_percentage = 0.0

    @api.depends("net_yield", "actual_nazhir_share")
    def _compute_surplus_mauquf_alaih(self):
        for rec in self:
            rec.surplus_for_mauquf_alaih = rec.net_yield - rec.actual_nazhir_share

    @api.constrains("actual_nazhir_share", "net_yield")
    def _check_nazhir_share_limit(self):
        """
        Validasi Mutlak UU No. 41 Tahun 2004 Pasal 12:
        Imbalan nazhir MAKSIMAL 10% dari hasil bersih pengelolaan.
        """
        for rec in self:
            if rec.actual_nazhir_share > 0:
                if rec.net_yield <= 0:
                    raise ValidationError(
                        _(
                            "[PELANGGARAN UU NO. 41/2004 PASAL 12]\n\n"
                            "Hasil bersih pengelolaan wakaf nihil atau defisit (Rp %s). "
                            "Nazhir tidak berhak mengambil imbalan pengelolaan saat tidak menghasilkan surplus!"
                        ) % rec.net_yield
                    )
                # Toleransi pembulatan mata uang (0.01)
                max_share = rec.max_allowed_nazhir_share + 0.01
                if rec.actual_nazhir_share > max_share:
                    raise ValidationError(
                        _(
                            "[PELANGGARAN UU NO. 41/2004 PASAL 12 - BATASAN HAK NAZHIR]\n\n"
                            "Alokasi imbalan nazhir melebihi batas maksimal 10%% dari hasil bersih pengelolaan!\n\n"
                            "- Hasil Bersih Pengelolaan: %s\n"
                            "- Maksimal 10%% yang Diizinkan: %s\n"
                            "- Alokasi yang Diinput: %s (%.2f%%)\n\n"
                            "Silakan turunkan nilai hak nazhir maksimal sebesar 10.00%% untuk memenuhi regulasi."
                        )
                        % (
                            rec.currency_id.format(rec.net_yield),
                            rec.currency_id.format(rec.max_allowed_nazhir_share),
                            rec.currency_id.format(rec.actual_nazhir_share),
                            rec.actual_percentage,
                        )
                    )

    def action_fetch_financial_data(self):
        """Menghitung otomatis pendapatan dan beban dari jurnal terposting di periode yang dipilih."""
        self.ensure_one()
        domain = [
            ("move_id.state", "=", "posted"),
            ("date", ">=", self.date_from),
            ("date", "<=", self.date_to),
            ("company_id", "=", self.company_id.id),
        ]

        # 1. Pendapatan Pengelolaan & Pengembangan (Credit - Debit)
        yield_domain = domain + [("account_id.psak112_category", "=", "revenue_yield")]
        yield_lines = self.env["account.move.line"].search(yield_domain)
        gross = sum(yield_lines.mapped(lambda l: l.credit - l.debit))

        # 2. Beban Langsung Pengelolaan (Debit - Credit)
        expense_domain = domain + [("account_id.psak112_category", "=", "expense_management")]
        expense_lines = self.env["account.move.line"].search(expense_domain)
        expenses = sum(expense_lines.mapped(lambda l: l.debit - l.credit))

        self.write({
            "gross_yield": max(gross, 0.0),
            "direct_expenses": max(expenses, 0.0),
            "state": "calculated",
        })
        # Default usulan hak nazhir = 10% jika surplus
        if self.net_yield > 0 and not self.actual_nazhir_share:
            self.actual_nazhir_share = self.max_allowed_nazhir_share

    def action_verify(self):
        self.ensure_one()
        self._check_nazhir_share_limit()
        self.write({"state": "verified"})

    def action_post_journal(self):
        """Membuat jurnal pengakuan hak nazhir (Beban Hak Nazhir pada Utang/Titipan Nazhir)."""
        self.ensure_one()
        if not self.journal_id or not self.nazhir_expense_account_id or not self.nazhir_payable_account_id:
            raise UserError(
                _("Silakan lengkapi Jurnal, Akun Beban Imbalan Nazhir, dan Akun Utang Nazhir terlebih dahulu.")
            )
        if self.actual_nazhir_share <= 0:
            raise UserError(_("Nominal alokasi hak nazhir harus lebih dari 0 untuk membuat entri jurnal."))

        move_vals = {
            "journal_id": self.journal_id.id,
            "date": self.date_to,
            "ref": _("Alokasi Hak Nazhir UU 41/2004 - %s") % self.name,
            "line_ids": [
                (0, 0, {
                    "account_id": self.nazhir_expense_account_id.id,
                    "name": _("Alokasi Hak Nazhir (Maks 10%%) - %s") % self.name,
                    "debit": self.actual_nazhir_share,
                    "credit": 0.0,
                }),
                (0, 0, {
                    "account_id": self.nazhir_payable_account_id.id,
                    "name": _("Utang / Titipan Imbalan Nazhir - %s") % self.name,
                    "debit": 0.0,
                    "credit": self.actual_nazhir_share,
                }),
            ],
        }
        move = self.env["account.move"].create(move_vals)
        move.action_post()
        self.write({
            "move_id": move.id,
            "state": "posted",
        })
        self.message_post(body=_("Entri jurnal pengakuan hak nazhir berhasil diposting: %s") % move.name)

    def action_draft(self):
        self.write({"state": "draft"})

    def action_cancel(self):
        self.write({"state": "cancel"})
