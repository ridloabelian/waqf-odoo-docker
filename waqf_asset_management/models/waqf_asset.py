# Copyright 2026 Amal Produktif, Forum Wakaf Produktif (FWP) & Asosiasi Nazhir Indonesia (ANI)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class WaqfAsset(models.Model):
    _name = "waqf.asset"
    _description = "Harta Benda Wakaf Fisik (Tanah, Bangunan & Sarana)"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name asc"

    name = fields.Char(
        string="Nama / Identitas Aset",
        required=True,
        tracking=True,
        help="Contoh: Tanah Wakaf Masjid Al-Ikhlas, Gedung Ruko Produktif 3 Lantai, dll.",
    )
    code = fields.Char(
        string="Nomor Registrasi Aset",
        required=True,
        copy=False,
        readonly=True,
        default="/",
        tracking=True,
    )
    asset_type = fields.Selection(
        selection=[
            ("land", "Tanah / Lahan Persil"),
            ("building", "Gedung / Bangunan / Ruko"),
            ("vehicle", "Kendaraan Layanan / Ambulans"),
            ("equipment", "Peralatan, Mesin & Sarana Fisik"),
            ("other", "Aset Fisik Lainnya"),
        ],
        string="Tipe Harta Benda Fisik",
        default="land",
        required=True,
        tracking=True,
    )
    waqf_nature = fields.Selection(
        selection=[
            ("perpetual", "Wakaf Abadi (Permanen)"),
            ("temporary", "Wakaf Berjangka (Temporer)"),
        ],
        string="Sifat Jangka Waktu",
        default="perpetual",
        required=True,
        tracking=True,
        help="Sesuai UU No. 41 Tahun 2004: Wakaf Abadi dilarang dialihkan atau dipindahtangankan.",
    )
    pledge_id = fields.Many2one(
        comodel_name="waqf.pledge",
        string="Akta Ikrar Wakaf (AIW)",
        tracking=True,
        help="Dokumen AIW atau APAIW asal perolehan harta benda wakaf ini.",
    )
    partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Wakif Asal",
        tracking=True,
    )
    utilization_type = fields.Selection(
        selection=[
            ("direct_service", "Layanan Ibadah / Pendidikan / Sosial Non-Profit"),
            ("productive_commercial", "Wakaf Produktif Komersial (Disewakan / Usaha)"),
            ("idle", "Lahan Idle (Belum Didayagunakan)"),
        ],
        string="Pola Pemanfaatan",
        default="direct_service",
        required=True,
        tracking=True,
    )

    # --- Legalitas & Sertifikasi Pertanahan (BPN) ---
    legal_status = fields.Selection(
        selection=[
            ("shm_waqf", "Sertifikat Tanah Wakaf BPN (Terdaftar Resmi)"),
            ("aiw_in_process", "AIW Terbit - Proses Sertifikasi BPN"),
            ("girik_letter_c", "Girik / Letter C / Petok D (Belum BPN)"),
            ("hgb_hp", "Hak Guna Bangunan / Hak Pakai"),
            ("dispute", "Dalam Sengketa / Klaim Pihak Ketiga"),
        ],
        string="Status Legalitas Tanah",
        default="aiw_in_process",
        required=True,
        tracking=True,
    )
    bpn_certificate_number = fields.Char(
        string="Nomor Sertifikat BPN",
        tracking=True,
        help="Nomor Sertifikat Tanah Wakaf resmi yang diterbitkan oleh Badan Pertanahan Nasional (BPN).",
    )
    nib_number = fields.Char(
        string="Nomor Identifikasi Bidang (NIB)",
        help="Nomor Identifikasi Bidang Tanah tunggal dari Kantor Pertanahan.",
    )
    bpn_registration_date = fields.Date(
        string="Tanggal Terbit Sertifikat BPN",
        tracking=True,
    )
    land_area = fields.Float(
        string="Luas Tanah (m²)",
        tracking=True,
        help="Luas bidang tanah dalam satuan meter persegi.",
    )
    building_area = fields.Float(
        string="Luas Bangunan (m²)",
        help="Luas total bangunan fisik yang berdiri di atas tanah wakaf.",
    )
    boundaries_north = fields.Char(string="Batas Utara")
    boundaries_south = fields.Char(string="Batas Selatan")
    boundaries_east = fields.Char(string="Batas Timur")
    boundaries_west = fields.Char(string="Batas Barat")
    geolocation_lat = fields.Float(
        string="Latitude GPS",
        digits=(10, 7),
        help="Titik koordinat Lintang (Latitude) lokasi aset fisik.",
    )
    geolocation_lng = fields.Float(
        string="Longitude GPS",
        digits=(10, 7),
        help="Titik koordinat Bujur (Longitude) lokasi aset fisik.",
    )
    map_url = fields.Char(
        string="Tautan Google Maps",
        compute="_compute_map_url",
    )

    # --- Lokasi & Alamat ---
    street = fields.Char(string="Alamat Jalan")
    village = fields.Char(string="Desa / Kelurahan")
    district = fields.Char(string="Kecamatan")
    city = fields.Char(string="Kabupaten / Kota")
    state_id = fields.Many2one(
        comodel_name="res.country.state",
        string="Provinsi",
    )
    country_id = fields.Many2one(
        comodel_name="res.country",
        string="Negara",
        default=lambda self: self.env.ref("base.id", raise_if_not_found=False),
    )

    # --- Penilaian & Appraisal ---
    acquisition_value = fields.Monetary(
        string="Nilai Perolehan / Ikrar",
        currency_field="currency_id",
        tracking=True,
        help="Nilai estimasi harta benda wakaf saat pertama kali diikrarkan oleh Wakif.",
    )
    current_appraised_value = fields.Monetary(
        string="Nilai Taksiran / Appraisal Terkini",
        currency_field="currency_id",
        tracking=True,
        help="Nilai taksiran pasar wajar terkini berdasarkan penilaian KJPP / Tim Penilai Nazhir.",
    )
    last_appraisal_date = fields.Date(
        string="Tanggal Penilaian Terakhir",
    )
    appraiser_name = fields.Char(
        string="Tim Penilai / KJPP",
    )

    # --- Kondisi Fisik & Asuransi ---
    asset_condition = fields.Selection(
        selection=[
            ("excellent", "Sangat Baik & Terawat"),
            ("good", "Baik / Berfungsi Normal"),
            ("fair", "Cukup / Perlu Perawatan Ringan"),
            ("damaged", "Rusak / Butuh Renovasi Berat"),
        ],
        string="Kondisi Fisik",
        default="good",
        required=True,
        tracking=True,
    )
    insurance_status = fields.Selection(
        selection=[
            ("uninsured", "Belum Diasuransikan"),
            ("insured_shariah", "Terasuransi Syariah (Takaful)"),
            ("expired", "Polis Jatuh Tempo / Kadaluarsa"),
        ],
        string="Status Asuransi Syariah",
        default="uninsured",
        required=True,
        tracking=True,
    )
    insurance_policy_number = fields.Char(string="Nomor Polis")
    insurance_company = fields.Char(string="Perusahaan Asuransi")
    insurance_end_date = fields.Date(string="Masa Berlaku Polis")

    # --- Log Inspeksi ---
    inspection_ids = fields.One2many(
        comodel_name="waqf.asset.inspection",
        inverse_name="asset_id",
        string="Riwayat Inspeksi Lapangan",
    )
    inspection_count = fields.Integer(
        string="Jumlah Inspeksi",
        compute="_compute_inspection_stats",
        store=True,
    )
    last_inspection_date = fields.Date(
        string="Tanggal Inspeksi Terakhir",
        compute="_compute_inspection_stats",
        store=True,
    )

    # --- Meta & Multi-Company ---
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
    active = fields.Boolean(
        string="Aktif",
        default=True,
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("code", "/") == "/":
                vals["code"] = (
                    self.env["ir.sequence"].next_by_code("waqf.asset") or "/"
                )
        return super().create(vals_list)

    @api.depends("geolocation_lat", "geolocation_lng")
    def _compute_map_url(self):
        for record in self:
            if record.geolocation_lat and record.geolocation_lng:
                record.map_url = (
                    f"https://www.google.com/maps?q={record.geolocation_lat},{record.geolocation_lng}"
                )
            else:
                record.map_url = False

    @api.depends("inspection_ids", "inspection_ids.date")
    def _compute_inspection_stats(self):
        for record in self:
            record.inspection_count = len(record.inspection_ids)
            dates = record.inspection_ids.mapped("date")
            record.last_inspection_date = max(dates) if dates else False

    @api.onchange("pledge_id")
    def _onchange_pledge_id(self):
        if self.pledge_id:
            self.partner_id = self.pledge_id.partner_id
            self.waqf_nature = self.pledge_id.waqf_nature
            if self.pledge_id.estimated_value and not self.acquisition_value:
                self.acquisition_value = self.pledge_id.estimated_value
                self.current_appraised_value = self.pledge_id.estimated_value

    @api.constrains("land_area", "building_area")
    def _check_area(self):
        for record in self:
            if record.land_area < 0 or record.building_area < 0:
                raise ValidationError("Luas tanah atau luas bangunan tidak boleh bernilai negatif!")

    @api.constrains("geolocation_lat", "geolocation_lng")
    def _check_geolocation(self):
        for record in self:
            if record.geolocation_lat and not (-90.0 <= record.geolocation_lat <= 90.0):
                raise ValidationError("Titik Latitude GPS harus berada di antara -90.0 dan 90.0 derajat!")
            if record.geolocation_lng and not (-180.0 <= record.geolocation_lng <= 180.0):
                raise ValidationError("Titik Longitude GPS harus berada di antara -180.0 dan 180.0 derajat!")

    def action_view_inspections(self):
        self.ensure_one()
        return {
            "name": f"Inspeksi: {self.name}",
            "type": "ir.actions.act_window",
            "res_model": "waqf.asset.inspection",
            "view_mode": "list,form",
            "domain": [("asset_id", "=", self.id)],
            "context": {"default_asset_id": self.id},
        }
