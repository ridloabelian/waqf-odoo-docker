# Copyright 2026 Amal Produktif, Forum Wakaf Produktif (FWP) & Asosiasi Nazhir Indonesia (ANI)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError


class WaqfDistribution(models.Model):
    _name = "waqf.distribution"
    _description = "Realisasi Penyaluran Manfaat Wakaf"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "date desc, id desc"

    name = fields.Char(
        string="Nomor Penyaluran",
        required=True,
        copy=False,
        readonly=True,
        default="/",
        tracking=True,
    )
    program_id = fields.Many2one(
        comodel_name="waqf.distribution.program",
        string="Program Penyaluran",
        required=True,
        tracking=True,
    )
    beneficiary_id = fields.Many2one(
        comodel_name="waqf.beneficiary",
        string="Penerima Manfaat (Mauquf 'Alaih)",
        required=True,
        tracking=True,
    )
    sector = fields.Selection(
        related="program_id.sector",
        string="Sektor Peruntukan",
        store=True,
        readonly=True,
    )
    date = fields.Date(
        string="Tanggal Penyaluran",
        default=fields.Date.context_today,
        required=True,
        tracking=True,
    )
    amount = fields.Monetary(
        string="Nominal Penyaluran",
        required=True,
        tracking=True,
        currency_field="currency_id",
    )
    currency_id = fields.Many2one(
        comodel_name="res.currency",
        string="Mata Uang",
        default=lambda self: self.env.company.currency_id,
        required=True,
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Entitas Nazhir",
        default=lambda self: self.env.company,
        required=True,
    )
    disbursement_method = fields.Selection(
        selection=[
            ("bank_transfer", "Transfer Bank Syariah"),
            ("cash", "Kas Tunai Langsung"),
            ("goods", "Barang / Sembako / Sarana (Natura)"),
        ],
        string="Metode Penyaluran",
        default="bank_transfer",
        required=True,
        tracking=True,
    )
    expense_account_id = fields.Many2one(
        comodel_name="account.account",
        string="Akun Beban Penyaluran (PSAK 412)",
        required=True,
        domain="[('is_waqf_account', '=', True), ('waqf_net_asset_type', '=', 'unrestricted'), ('account_type', '=', 'expense')]",
        help="Akun Beban Penyaluran Manfaat Wakaf standar PSAK 412 yang bersumber dari Aset Neto Tidak Terikat.",
    )
    journal_id = fields.Many2one(
        comodel_name="account.journal",
        string="Jurnal Pengeluaran Kas/Bank",
        domain="[('type', 'in', ('bank', 'cash'))]",
        required=True,
        help="Jurnal Kas atau Rekening Bank sumber pembayaran dana penyaluran.",
    )
    disbursement_purpose = fields.Text(
        string="Peruntukan & Deskripsi Bantuan",
        required=True,
        help="Penjelasan rinci peruntukan bantuan yang disalurkan kepada Mauquf 'Alaih.",
    )
    receipt_recipient_name = fields.Char(
        string="Nama Penandatangan Tanda Terima",
        help="Nama orang yang menandatangani Berita Acara Serah Terima (BAST) / Kuitansi.",
    )
    state = fields.Selection(
        selection=[
            ("draft", "Pengajuan (Draft)"),
            ("reviewed", "Ditinjau Tim Program"),
            ("approved", "Disetujui Komite Penyaluran"),
            ("disbursed", "Telah Disalurkan"),
            ("cancel", "Dibatalkan"),
        ],
        string="Status",
        default="draft",
        tracking=True,
        required=True,
    )
    move_id = fields.Many2one(
        comodel_name="account.move",
        string="Entri Jurnal Akuntansi",
        readonly=True,
        copy=False,
    )
    verifier_id = fields.Many2one(
        comodel_name="res.users",
        string="Ditinjau Oleh",
        readonly=True,
        copy=False,
    )
    verified_date = fields.Datetime(
        string="Waktu Verifikasi",
        readonly=True,
        copy=False,
    )
    approver_id = fields.Many2one(
        comodel_name="res.users",
        string="Disetujui Oleh",
        readonly=True,
        copy=False,
    )
    approved_date = fields.Datetime(
        string="Waktu Persetujuan",
        readonly=True,
        copy=False,
    )
    disbursed_by_id = fields.Many2one(
        comodel_name="res.users",
        string="Disalurkan Oleh",
        readonly=True,
        copy=False,
    )
    disbursed_date = fields.Datetime(
        string="Waktu Penyaluran Realisasi",
        readonly=True,
        copy=False,
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "/") == "/":
                vals["name"] = (
                    self.env["ir.sequence"].next_by_code("waqf.distribution") or "/"
                )
        return super().create(vals_list)

    @api.onchange("program_id")
    def _onchange_program_id(self):
        if self.program_id and self.program_id.default_expense_account_id:
            self.expense_account_id = self.program_id.default_expense_account_id
        elif not self.expense_account_id:
            dist_account = self.env["account.account"].search(
                [
                    ("psak112_category", "=", "expense_distribution"),
                    ("company_id", "=", self.company_id.id),
                ],
                limit=1,
            )
            if dist_account:
                self.expense_account_id = dist_account

    @api.onchange("beneficiary_id")
    def _onchange_beneficiary_id(self):
        if self.beneficiary_id and not self.receipt_recipient_name:
            self.receipt_recipient_name = (
                self.beneficiary_id.contact_person or self.beneficiary_id.name
            )

    @api.constrains("amount")
    def _check_amount(self):
        for record in self:
            if record.amount <= 0:
                raise ValidationError(
                    "Nominal penyaluran manfaat wakaf harus lebih besar dari 0 (Nol)!"
                )

    @api.constrains("expense_account_id")
    def _check_shariah_distribution_account(self):
        for record in self:
            if record.expense_account_id and record.expense_account_id.waqf_net_asset_type == "permanent":
                raise ValidationError(
                    "PELANGGARAN SYARIAH PSAK 412 & UU NO. 41/2004!\n"
                    "Penyaluran manfaat kepada Mauquf 'Alaih DILARANG KERAS menggunakan akun Pokok Wakaf Abadi "
                    "(Aset Neto Terikat Permanen). Dana penyaluran HANYA boleh bersumber dari Beban Penyaluran / "
                    "Aset Neto Tidak Terikat (Surplus Bersih Hasil Pengelolaan & Pengembangan)."
                )

    def action_review(self):
        for record in self:
            record.write({
                "state": "reviewed",
                "verifier_id": self.env.user.id,
                "verified_date": fields.Datetime.now(),
            })
            record.message_post(body="Pengajuan penyaluran telah ditinjau dan diverifikasi kelayakannya.")

    def action_approve(self):
        for record in self:
            if record.beneficiary_id.eligibility_status != "eligible":
                raise ValidationError(
                    f"Penerima manfaat '{record.beneficiary_id.name}' belum berstatus 'Layak Menerima Manfaat (Eligible)'.\n"
                    "Harap setujui kelayakan Mauquf 'Alaih terlebih dahulu sebelum menyetujui penyaluran dana!"
                )
            record.write({
                "state": "approved",
                "approver_id": self.env.user.id,
                "approved_date": fields.Datetime.now(),
            })
            record.message_post(body="Penyaluran manfaat disetujui oleh Komite Penyaluran / Pimpinan Nazhir.")

    def action_disburse(self):
        for record in self:
            if record.state != "approved":
                raise UserError("Hanya pengajuan yang telah disetujui (Approved) yang dapat disalurkan.")

            # Resolve credit account from journal
            credit_account = record.journal_id.default_account_id
            if not credit_account:
                raise UserError(
                    f"Jurnal '{record.journal_id.name}' belum memiliki Akun Default. "
                    "Silakan lengkapi konfigurasi akun pada Jurnal Kas/Bank terlebih dahulu."
                )

            # Create accounting entry (account.move)
            move_vals = {
                "journal_id": record.journal_id.id,
                "date": record.date,
                "ref": f"Penyaluran Manfaat: {record.name} - {record.beneficiary_id.name}",
                "move_type": "entry",
                "company_id": record.company_id.id,
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "name": f"Beban Penyaluran: {record.program_id.name} - {record.disbursement_purpose[:60]}",
                            "account_id": record.expense_account_id.id,
                            "debit": record.amount,
                            "credit": 0.0,
                            "company_id": record.company_id.id,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "name": f"Pengeluaran Kas/Bank: {record.name}",
                            "account_id": credit_account.id,
                            "debit": 0.0,
                            "credit": record.amount,
                            "company_id": record.company_id.id,
                        },
                    ),
                ],
            }

            move = self.env["account.move"].create(move_vals)
            move.action_post()

            record.write({
                "state": "disbursed",
                "move_id": move.id,
                "disbursed_by_id": self.env.user.id,
                "disbursed_date": fields.Datetime.now(),
            })
            record.message_post(
                body=f"Manfaat wakaf telah disalurkan sebesar {record.currency_id.symbol} {record.amount:,.2f}. "
                     f"Entri jurnal akuntansi PSAK 412 diterbitkan: {move.name}."
            )

    def action_cancel(self):
        for record in self:
            if record.state == "disbursed" and record.move_id:
                raise UserError(
                    "Penyaluran yang sudah disalurkan dan memiliki entri jurnal tidak dapat langsung dibatalkan. "
                    "Harap batalkan/balik (reverse) entri jurnal akuntansi terlebih dahulu!"
                )
            record.write({"state": "cancel"})
            record.message_post(body="Pengajuan penyaluran manfaat wakaf dibatalkan.")

    def action_draft(self):
        for record in self:
            record.write({"state": "draft"})

    def action_view_move(self):
        self.ensure_one()
        return {
            "name": "Entri Jurnal Penyaluran",
            "type": "ir.actions.act_window",
            "res_model": "account.move",
            "res_id": self.move_id.id,
            "view_mode": "form",
            "target": "current",
        }
