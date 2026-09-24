# Copyright 2026 Forum Wakaf Produktif (FWP / fwp.or.id)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class AccountMove(models.Model):
    _inherit = "account.move"

    waqf_pledge_id = fields.Many2one(
        comodel_name="waqf.pledge",
        string="Rujukan AIW / APAIW",
        help="Akta Ikrar Wakaf terkait transaksi keuangan ini.",
        copy=False,
    )
    is_waqf_transaction = fields.Boolean(
        string="Transaksi Wakaf",
        compute="_compute_is_waqf_transaction",
        store=True,
    )

    @api.depends("line_ids.account_id.is_waqf_account", "waqf_pledge_id")
    def _compute_is_waqf_transaction(self):
        for move in self:
            move.is_waqf_transaction = bool(
                move.waqf_pledge_id or any(line.account_id.is_waqf_account for line in move.line_ids)
            )

    @api.constrains("state", "line_ids")
    def _check_psak112_syariah_rules(self):
        """
        Validasi Kepatuhan Syariah & Standar PSAK 112:
        1. Dana Pokok Wakaf Permanen (Aset Neto Terikat Permanen) HARAM berkurang atau dijadikan sumber beban penyaluran/operasional.
        2. Penyaluran kepada Mauquf 'Alaih hanya boleh bersumber dari Aset Neto Tidak Terikat (Surplus Hasil Pengelolaan).
        """
        for move in self:
            if move.state != "posted":
                continue

            # Deteksi debit pada akun Aset Neto Terikat Permanen
            debit_permanent_lines = move.line_ids.filtered(
                lambda l: (
                    l.account_id.waqf_net_asset_type == "permanent"
                    or l.account_id.psak112_category == "net_asset_permanent"
                ) and l.debit > 0
            )

            if debit_permanent_lines:
                # Cek apakah transaksi ini mendebit pokok permanen untuk membiayai beban atau pengeluaran
                expense_or_distribution_lines = move.line_ids.filtered(
                    lambda l: (
                        l.account_id.psak112_category in (
                            "expense_distribution",
                            "expense_management",
                            "expense_nazhir_share",
                        )
                        or (l.account_id.account_type in ("expense", "expense_direct_cost", "expense_depreciation")
                            and l.debit > 0)
                    )
                )

                if expense_or_distribution_lines:
                    raise ValidationError(
                        _(
                            "[PELANGGARAN PRINSIP SYARIAH & PSAK 112]\n\n"
                            "Dana Pokok Wakaf Permanen (Aset Neto Terikat Permanen) HARAM berkurang "
                            "atau dijadikan sumber beban penyaluran/operasional!\n\n"
                            "Ayat Hukum & Standar:\n"
                            "- UU No. 41 Tahun 2004 Pasal 40: Harta benda wakaf yang sudah diwakafkan dilarang dijaminkan, disita, dihibahkan, dijual, diwariskan, dialihkan, atau diubah peruntukannya selain yang diikrarkan.\n"
                            "- PSAK 112 Paragraf 26-28: Pokok wakaf permanen diakui sebagai Aset Neto Terikat Permanen dan tidak boleh tergerus beban penyaluran.\n\n"
                            "Penyaluran manfaat kepada Mauquf 'Alaih HANYA boleh dibiayai dari "
                            "Aset Neto Tidak Terikat (Surplus Bersih Hasil Pengelolaan & Pengembangan)."
                        )
                    )


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    waqf_net_asset_type = fields.Selection(
        related="account_id.waqf_net_asset_type",
        string="Klasifikasi Aset Neto",
        store=True,
        readonly=True,
    )
    psak112_category = fields.Selection(
        related="account_id.psak112_category",
        string="Kategori PSAK 112",
        store=True,
        readonly=True,
    )
