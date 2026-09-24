# Copyright 2026 Forum Wakaf Produktif (FWP / fwp.or.id)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

import re
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ResPartner(models.Model):
    _inherit = "res.partner"

    is_wakif = fields.Boolean(
        string="Adalah Wakif",
        default=False,
        help="Tandai jika kontak ini merupakan wakif (pewakaf).",
        index=True,
    )
    wakif_type = fields.Selection(
        selection=[
            ("individual", "Perorangan / Individu"),
            ("institution", "Badan Hukum / Yayasan / Korporasi"),
            ("group", "Kelompok / Bersama"),
        ],
        string="Kategori Wakif",
        default="individual",
        help="Klasifikasi jenis wakif berdasarkan regulasi UU No. 41 Tahun 2004.",
    )
    nik = fields.Char(
        string="NIK (KTP)",
        size=16,
        help="Nomor Induk Kependudukan (16 digit) sesuai KTP.",
        index=True,
    )
    nib = fields.Char(
        string="NIB (Nomor Induk Berusaha)",
        help="Nomor Induk Berusaha untuk wakif badan hukum / korporasi.",
    )
    npwp = fields.Char(
        string="NPWP",
        help="Nomor Pokok Wajib Pajak wakif.",
    )
    kyc_status = fields.Selection(
        selection=[
            ("unverified", "Belum Diverifikasi"),
            ("verified", "Terverifikasi (KYC Valid)"),
            ("rejected", "Ditolak / Data Tidak Sesuai"),
        ],
        string="Status KYC Wakif",
        default="unverified",
        tracking=True,
        help="Status kepatuhan Know Your Customer (KYC) sesuai SKKNI BWI.",
    )
    kyc_notes = fields.Text(
        string="Catatan Verifikasi KYC",
        help="Catatan verifikasi identitas, domisili, atau dokumen pendukung.",
    )
    kyc_verified_date = fields.Date(
        string="Tanggal Verifikasi KYC",
        readonly=True,
    )
    kyc_verified_by_id = fields.Many2one(
        comodel_name="res.users",
        string="Diverifikasi Oleh",
        readonly=True,
    )
    waqf_pledge_ids = fields.One2many(
        comodel_name="waqf.pledge",
        inverse_name="partner_id",
        string="Daftar Ikrar Wakaf",
    )
    waqf_pledge_count = fields.Integer(
        string="Jumlah Ikrar Wakaf",
        compute="_compute_waqf_pledge_count",
    )
    total_waqf_amount = fields.Monetary(
        string="Total Akumulasi Wakaf Uang",
        compute="_compute_total_waqf_amount",
        currency_field="currency_id",
    )

    @api.constrains("nik")
    def _check_nik_format(self):
        for partner in self:
            if partner.is_wakif and partner.wakif_type == "individual" and partner.nik:
                cleaned_nik = partner.nik.strip()
                if not re.match(r"^\d{16}$", cleaned_nik):
                    raise ValidationError(
                        _("Format NIK tidak valid untuk wakif individu '%s'. "
                          "NIK harus berupa 16 digit angka.") % partner.name
                    )

    @api.depends("waqf_pledge_ids")
    def _compute_waqf_pledge_count(self):
        for partner in self:
            partner.waqf_pledge_count = len(partner.waqf_pledge_ids)

    @api.depends("waqf_pledge_ids.amount_nominal", "waqf_pledge_ids.state")
    def _compute_total_waqf_amount(self):
        for partner in self:
            valid_pledges = partner.waqf_pledge_ids.filtered(
                lambda p: p.state in ("approved_nazhir", "issued") and p.waqf_category == "movable_cash"
            )
            partner.total_waqf_amount = sum(valid_pledges.mapped("amount_nominal"))

    def action_verify_kyc(self):
        self.write({
            "kyc_status": "verified",
            "kyc_verified_date": fields.Date.today(),
            "kyc_verified_by_id": self.env.user.id,
        })

    def action_reject_kyc(self):
        self.write({
            "kyc_status": "rejected",
            "kyc_verified_date": fields.Date.today(),
            "kyc_verified_by_id": self.env.user.id,
        })

    def action_view_waqf_pledges(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("waqf_core.action_waqf_pledge")
        action["domain"] = [("partner_id", "=", self.id)]
        action["context"] = {"default_partner_id": self.id, "default_is_wakif": True}
        return action
