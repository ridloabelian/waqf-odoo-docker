# Copyright 2026 Amal Produktif, Forum Wakaf Produktif (FWP) & Asosiasi Nazhir Indonesia (ANI)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

import re
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class WaqfBeneficiary(models.Model):
    _name = "waqf.beneficiary"
    _description = "Mauquf 'Alaih (Penerima Manfaat Wakaf)"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name asc"

    name = fields.Char(
        string="Nama Mauquf 'Alaih",
        required=True,
        tracking=True,
        help="Nama lengkap individu penerima manfaat atau nama lembaga/institusi.",
    )
    beneficiary_type = fields.Selection(
        selection=[
            ("individual", "Individu / Perorangan (Mustahiq / Dhuafa)"),
            ("institution", "Lembaga / Yayasan / BKM Masjid / Pesantren"),
        ],
        string="Tipe Penerima",
        default="individual",
        required=True,
        tracking=True,
    )
    identity_number = fields.Char(
        string="Nomor Identitas (NIK / Legalitas)",
        tracking=True,
        help="Nomor Induk Kependudukan (NIK 16 digit) untuk perorangan, "
             "atau Nomor SK Kemenkumham / Izin Operasional Kemenag untuk lembaga.",
    )
    partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Kontak Rekanan Terkait",
        help="Hubungkan dengan master partner Odoo jika ada.",
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
        string="Sektor Peruntukan Utama",
        default="education",
        required=True,
        tracking=True,
        help="Bidang pemanfaatan wakaf sesuai UU No. 41 Tahun 2004 Pasal 22.",
    )
    contact_person = fields.Char(
        string="Nama Penanggung Jawab (PIC)",
        help="Diisi nama penanggung jawab atau ketua pengurus jika penerima berbentuk lembaga.",
    )
    phone = fields.Char(
        string="Telepon / WhatsApp",
        tracking=True,
    )
    email = fields.Char(
        string="Email",
    )
    street = fields.Char(
        string="Alamat Lengkap",
    )
    city = fields.Char(
        string="Kota / Kabupaten",
    )
    state_id = fields.Many2one(
        comodel_name="res.country.state",
        string="Provinsi",
    )
    country_id = fields.Many2one(
        comodel_name="res.country",
        string="Negara",
        default=lambda self: self.env.ref("base.id", raise_if_not_found=False),
    )
    bank_id = fields.Many2one(
        comodel_name="res.bank",
        string="Bank Penyaluran",
    )
    bank_account_number = fields.Char(
        string="Nomor Rekening",
    )
    bank_account_name = fields.Char(
        string="Nama Pemilik Rekening",
    )
    eligibility_status = fields.Selection(
        selection=[
            ("pending", "Asesmen & Verifikasi Dokumen"),
            ("eligible", "Layak Menerima Manfaat (Eligible)"),
            ("suspended", "Ditangguhkan Sementara"),
            ("rejected", "Tidak Memenuhi Syarat"),
        ],
        string="Status Kelayakan Syariah",
        default="pending",
        required=True,
        tracking=True,
        help="Status penilaian kelayakan penerima manfaat berdasarkan asesmen kebutuhan dan kriteria syariah.",
    )
    assessment_notes = fields.Text(
        string="Catatan Asesmen Kelayakan",
        help="Hasil wawancara, survei lapangan, atau telaah dokumen kelayakan Mauquf 'Alaih.",
    )
    distribution_ids = fields.One2many(
        comodel_name="waqf.distribution",
        inverse_name="beneficiary_id",
        string="Riwayat Penyaluran",
    )
    distribution_count = fields.Integer(
        string="Frekuensi Penyaluran",
        compute="_compute_distribution_stats",
        store=True,
    )
    total_distributed_amount = fields.Monetary(
        string="Total Manfaat Diterima",
        currency_field="currency_id",
        compute="_compute_distribution_stats",
        store=True,
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

    @api.depends("distribution_ids", "distribution_ids.state", "distribution_ids.amount")
    def _compute_distribution_stats(self):
        for record in self:
            disbursed = record.distribution_ids.filtered(lambda d: d.state == "disbursed")
            record.distribution_count = len(disbursed)
            record.total_distributed_amount = sum(disbursed.mapped("amount"))

    @api.constrains("identity_number", "beneficiary_type")
    def _check_identity_number(self):
        for record in self:
            if record.beneficiary_type == "individual" and record.identity_number:
                clean_nik = re.sub(r"\D", "", record.identity_number)
                if len(clean_nik) != 16:
                    raise ValidationError(
                        "Format NIK tidak valid! NIK KTP untuk individu penerima manfaat "
                        "harus terdiri dari tepat 16 digit angka."
                    )

    def action_set_eligible(self):
        for record in self:
            record.write({"eligibility_status": "eligible"})
            record.message_post(
                body="Status penerima manfaat disetujui: Layak Menerima Manfaat (Eligible)."
            )

    def action_set_suspended(self):
        for record in self:
            record.write({"eligibility_status": "suspended"})
            record.message_post(body="Status penerima manfaat ditangguhkan sementara.")

    def action_set_rejected(self):
        for record in self:
            record.write({"eligibility_status": "rejected"})
            record.message_post(body="Status penerima manfaat dinyatakan tidak memenuhi syarat.")
