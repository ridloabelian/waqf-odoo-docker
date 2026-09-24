# Copyright 2026 Forum Wakaf Produktif (FWP / fwp.or.id)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class WaqfPledge(models.Model):
    _name = "waqf.pledge"
    _description = "Akta Ikrar Wakaf (AIW) & APAIW"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "date_pledge desc, id desc"

    name = fields.Char(
        string="Nomor Registrasi Sistem",
        required=True,
        copy=False,
        readonly=True,
        index=True,
        default=lambda self: _("New"),
    )
    pledge_type = fields.Selection(
        selection=[
            ("aiw", "Akta Ikrar Wakaf (AIW)"),
            ("apaiw", "Akta Pengganti Akta Ikrar Wakaf (APAIW)"),
        ],
        string="Jenis Akta",
        required=True,
        default="aiw",
        tracking=True,
        help="AIW diterbitkan saat ikrar wakaf baru. APAIW diterbitkan untuk wakaf yang sudah berjalan namun belum diaktakan.",
    )
    document_number = fields.Char(
        string="Nomor Resmi Akta (PPAIW)",
        copy=False,
        tracking=True,
        help="Nomor resmi AIW/APAIW dari Pejabat Pembuat Akta Ikrar Wakaf (KUA / Notaris).",
    )
    date_pledge = fields.Date(
        string="Tanggal Ikrar Wakaf",
        required=True,
        default=fields.Date.context_today,
        tracking=True,
        help="Tanggal pelaksanaan pengucapan ikrar wakaf.",
    )
    partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Wakif (Pemberi Wakaf)",
        required=True,
        domain="[('is_wakif', '=', True)]",
        tracking=True,
        index=True,
        help="Identitas wakif terdaftar dalam sistem.",
    )
    wakif_nik = fields.Char(
        related="partner_id.nik",
        string="NIK Wakif",
        readonly=True,
    )
    wakif_phone = fields.Char(
        related="partner_id.phone",
        string="Telepon Wakif",
        readonly=True,
    )
    wakif_email = fields.Char(
        related="partner_id.email",
        string="Email Wakif",
        readonly=True,
    )

    # Nazhir Details
    nazhir_id = fields.Many2one(
        comodel_name="res.partner",
        string="Nazhir Penerima Amanah",
        required=True,
        tracking=True,
        help="Lembaga atau perorangan nazhir pemegang amanah wakaf.",
    )
    nazhir_registration_number = fields.Char(
        string="Nomor Registrasi Nazhir (BWI)",
        help="Nomor Tanda Bukti Pendaftaran Nazhir dari Badan Wakaf Indonesia (BWI).",
    )

    # PPAIW Details
    ppaiw_name = fields.Char(
        string="Nama PPAIW",
        help="Nama Kepala KUA atau Notaris Pejabat Pembuat Akta Ikrar Wakaf.",
    )
    ppaiw_position = fields.Char(
        string="Jabatan / Wilayah PPAIW",
        help="Contoh: Kepala KUA Kecamatan Gambir, Jakarta Pusat.",
    )
    ppaiw_sk_number = fields.Char(
        string="Nomor SK Pengangkatan PPAIW",
    )

    # Saksi-Saksi (Witnesses)
    witness_1_name = fields.Char(
        string="Nama Saksi I",
    )
    witness_1_nik = fields.Char(
        string="NIK Saksi I",
        size=16,
    )
    witness_1_address = fields.Text(
        string="Alamat Saksi I",
    )
    witness_2_name = fields.Char(
        string="Nama Saksi II",
    )
    witness_2_nik = fields.Char(
        string="NIK Saksi II",
        size=16,
    )
    witness_2_address = fields.Text(
        string="Alamat Saksi II",
    )

    # Harta Benda Wakaf (Mauquf Bih)
    waqf_type_id = fields.Many2one(
        comodel_name="waqf.type",
        string="Jenis Harta Benda Wakaf",
        required=True,
    )
    waqf_category = fields.Selection(
        related="waqf_type_id.category",
        string="Kategori Harta (UU 41/2004)",
        store=True,
        readonly=True,
    )
    waqf_nature = fields.Selection(
        selection=[
            ("perpetual", "Abadi / Muabbad (Permanen)"),
            ("temporary", "Berjangka / Muaqqat (Temporer)"),
        ],
        string="Sifat Jangka Waktu Wakaf",
        required=True,
        default="perpetual",
        tracking=True,
        help="Wakaf abadi: pokok tidak boleh berkurang selamanya. "
             "Wakaf berjangka: pokok dikembalikan setelah jangka waktu berakhir.",
    )
    period_years = fields.Integer(
        string="Jangka Waktu (Tahun)",
        help="Lama waktu wakaf berjangka (minimal sesuai ketentuan BWI).",
    )
    return_date = fields.Date(
        string="Tanggal Pengembalian Pokok",
        help="Tanggal pengembalian dana pokok wakaf berjangka kepada wakif / ahli waris.",
    )
    beneficiary_reversion = fields.Selection(
        selection=[
            ("wakif", "Wakif Sendiri"),
            ("heir", "Ahli Waris Sah Wakif"),
        ],
        string="Penerima Pengembalian Pokok",
        default="wakif",
    )

    # Nilai Finansial
    currency_id = fields.Many2one(
        comodel_name="res.currency",
        string="Mata Uang",
        required=True,
        default=lambda self: self.env.company.currency_id,
    )
    amount_nominal = fields.Monetary(
        string="Nominal Wakaf Uang",
        currency_field="currency_id",
        tracking=True,
        help="Nominal kas jika jenis wakaf adalah Wakaf Uang (Cash Waqf).",
    )
    estimated_value = fields.Monetary(
        string="Taksiran Nilai Aset Non-Uang",
        currency_field="currency_id",
        tracking=True,
        help="Nilai taksiran/apraisal aset fisik atau bergerak selain uang.",
    )
    total_asset_value = fields.Monetary(
        string="Total Nilai Harta Wakaf",
        compute="_compute_total_asset_value",
        store=True,
        currency_field="currency_id",
    )

    # Spesifikasi Fisik & Lokasi (Jika Aset Tetap / Tidak Bergerak)
    asset_description = fields.Text(
        string="Spesifikasi & Rincian Harta Wakaf",
        help="Deskripsi detail mengenai kondisi, batasan, spesifikasi teknis harta benda wakaf.",
    )
    asset_location = fields.Text(
        string="Lokasi Aset Wakaf",
        help="Alamat lengkap lokasi tanah/bangunan wakaf beserta batas-batas tanah.",
    )
    land_certificate_type = fields.Selection(
        selection=[
            ("shm", "Sertifikat Hak Milik (SHM)"),
            ("hgb", "Hak Guna Bangunan (HGB)"),
            ("hgu", "Hak Guna Usaha (HGU)"),
            ("girik", "Girik / Letter C / Adat"),
            ("other", "Lainnya / Belum Bersertifikat"),
        ],
        string="Jenis Bukti Kepemilikan Tanah",
    )
    land_certificate_number = fields.Char(
        string="Nomor Sertifikat Kepemilikan",
    )
    land_area_m2 = fields.Float(
        string="Luas Tanah (m²)",
    )
    building_area_m2 = fields.Float(
        string="Luas Bangunan (m²)",
    )

    # Peruntukan Mauquf 'Alaih
    allotment_purpose = fields.Text(
        string="Peruntukan Wakaf (Mauquf 'Alaih)",
        required=True,
        help="Tujuan penggunaan manfaat/hasil wakaf sesuai kehendak wakif dalam ikrar wakaf "
             "(Contoh: Beasiswa Pendidikan Santri, Operasional Layanan Kesehatan Dhuafa, Pemberdayaan Ekonomi Ummat).",
    )

    # Workflow & Verifikasi
    state = fields.Selection(
        selection=[
            ("draft", "Draf"),
            ("verified_legal", "Terverifikasi Legalitas"),
            ("approved_nazhir", "Disetujui Pimpinan Nazhir"),
            ("issued", "AIW / APAIW Terbit"),
            ("cancel", "Dibatalkan"),
        ],
        string="Status",
        required=True,
        default="draft",
        tracking=True,
    )
    legal_verifier_id = fields.Many2one(
        comodel_name="res.users",
        string="Verifikator Legal",
        readonly=True,
        copy=False,
    )
    legal_verified_date = fields.Date(
        string="Tanggal Verifikasi Legal",
        readonly=True,
        copy=False,
    )
    legal_notes = fields.Text(
        string="Catatan Tim Legal",
    )
    nazhir_approver_id = fields.Many2one(
        comodel_name="res.users",
        string="Disetujui Oleh (Nazhir)",
        readonly=True,
        copy=False,
    )
    nazhir_approved_date = fields.Date(
        string="Tanggal Persetujuan Nazhir",
        readonly=True,
        copy=False,
    )
    issued_date = fields.Date(
        string="Tanggal Terbit AIW",
        readonly=True,
        copy=False,
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Entitas Nazhir (Company)",
        required=True,
        default=lambda self: self.env.company,
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", _("New")) == _("New"):
                vals["name"] = self.env["ir.sequence"].next_by_code("waqf.pledge") or _("New")
        return super().create(vals_list)

    @api.depends("waqf_category", "amount_nominal", "estimated_value")
    def _compute_total_asset_value(self):
        for rec in self:
            if rec.waqf_category == "movable_cash":
                rec.total_asset_value = rec.amount_nominal
            else:
                rec.total_asset_value = rec.estimated_value

    @api.constrains("waqf_nature", "period_years", "return_date", "date_pledge")
    def _check_temporary_waqf_rules(self):
        for rec in self:
            if rec.waqf_nature == "temporary":
                if rec.period_years <= 0:
                    raise ValidationError(
                        _("Untuk wakaf berjangka (temporer), jangka waktu wajib diisi minimal 1 tahun.")
                    )
                if rec.return_date and rec.date_pledge and rec.return_date <= rec.date_pledge:
                    raise ValidationError(
                        _("Tanggal pengembalian pokok wakaf berjangka harus lebih besar dari tanggal ikrar wakaf.")
                    )

    @api.constrains("waqf_category", "amount_nominal", "estimated_value")
    def _check_asset_value(self):
        for rec in self:
            if rec.waqf_category == "movable_cash" and rec.amount_nominal <= 0:
                raise ValidationError(
                    _("Nominal wakaf uang harus lebih besar dari Rp 0.")
                )
            if rec.waqf_category != "movable_cash" and rec.estimated_value < 0:
                raise ValidationError(
                    _("Taksiran nilai aset wakaf tidak boleh bernilai negatif.")
                )

    # Workflow Actions
    def action_verify_legal(self):
        self.ensure_one()
        if not self.partner_id:
            raise ValidationError(_("Data Wakif wajib dilengkapi sebelum verifikasi legal."))
        self.write({
            "state": "verified_legal",
            "legal_verifier_id": self.env.user.id,
            "legal_verified_date": fields.Date.today(),
        })
        self.message_post(body=_("Berkas ikrar wakaf telah diverifikasi legalitasnya oleh %s.") % self.env.user.name)

    def action_approve_nazhir(self):
        self.ensure_one()
        if self.state != "verified_legal":
            raise ValidationError(_("Persetujuan Nazhir hanya dapat dilakukan setelah verifikasi legalitas selesai."))
        self.write({
            "state": "approved_nazhir",
            "nazhir_approver_id": self.env.user.id,
            "nazhir_approved_date": fields.Date.today(),
        })
        self.message_post(body=_("Ikrar wakaf telah disetujui oleh Pimpinan Nazhir (%s).") % self.env.user.name)

    def action_issue_aiw(self):
        self.ensure_one()
        if not self.document_number:
            raise ValidationError(
                _("Nomor resmi Akta Ikrar Wakaf (PPAIW) wajib diisi sebelum status diubah menjadi Terbit.")
            )
        self.write({
            "state": "issued",
            "issued_date": fields.Date.today(),
        })
        self.message_post(body=_("Akta Ikrar Wakaf (Nomor: %s) resmi diterbitkan.") % self.document_number)

    def action_draft(self):
        self.write({"state": "draft"})

    def action_cancel(self):
        self.write({"state": "cancel"})
