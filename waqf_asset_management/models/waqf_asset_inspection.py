# Copyright 2026 Amal Produktif, Forum Wakaf Produktif (FWP) & Asosiasi Nazhir Indonesia (ANI)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import api, fields, models


class WaqfAssetInspection(models.Model):
    _name = "waqf.asset.inspection"
    _description = "Log Inspeksi & Pemeliharaan Aset Fisik Wakaf"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "date desc, id desc"

    name = fields.Char(
        string="Nomor Inspeksi",
        required=True,
        copy=False,
        readonly=True,
        default="/",
        tracking=True,
    )
    asset_id = fields.Many2one(
        comodel_name="waqf.asset",
        string="Aset Fisik Wakaf",
        required=True,
        tracking=True,
    )
    date = fields.Date(
        string="Tanggal Inspeksi",
        default=fields.Date.context_today,
        required=True,
        tracking=True,
    )
    inspector_id = fields.Many2one(
        comodel_name="res.users",
        string="Petugas Pemeriksa",
        default=lambda self: self.env.user,
        required=True,
        tracking=True,
    )
    inspection_type = fields.Selection(
        selection=[
            ("routine", "Inspeksi Rutin Berkala"),
            ("boundary_check", "Pemeriksaan Patok & Tapal Batas"),
            ("incident", "Insidental / Pasca Bencana"),
            ("pre_renovation", "Pemeriksaan Pra-Renovasi / Pemeliharaan"),
        ],
        string="Tipe Inspeksi",
        default="routine",
        required=True,
        tracking=True,
    )
    condition_observed = fields.Selection(
        selection=[
            ("excellent", "Sangat Baik & Terawat"),
            ("good", "Baik / Berfungsi Normal"),
            ("fair", "Cukup / Perlu Perawatan Ringan"),
            ("damaged", "Rusak / Butuh Renovasi Berat"),
        ],
        string="Kondisi Fisik Teramati",
        default="good",
        required=True,
        tracking=True,
    )
    boundary_status = fields.Selection(
        selection=[
            ("safe", "Patok Batas Aman & Sesuai Sertifikat BPN"),
            ("threatened", "Indikasi Pergeseran Patok / Penyerobotan"),
            ("disputed", "Terjadi Sengketa / Klaim Tapal Batas"),
        ],
        string="Keamanan Tapal Batas",
        default="safe",
        required=True,
        tracking=True,
    )
    findings = fields.Text(
        string="Temuan Lapangan & Kondisi Fisik",
        required=True,
        help="Uraikan kondisi visual, kerusakan fisik, utilitas, atau interaksi dengan masyarakat sekitar.",
    )
    recommended_action = fields.Text(
        string="Rekomendasi Tindak Lanjut",
        help="Langkah pemeliharaan fisik, pemagaran, pengecatan, atau advokasi hukum batas tanah.",
    )
    action_status = fields.Selection(
        selection=[
            ("no_action_needed", "Aman / Tidak Butuh Tindakan"),
            ("pending", "Menunggu Rencana Pemeliharaan"),
            ("in_progress", "Dalam Proses Perbaikan / Advokasi"),
            ("completed", "Selesai Ditindaklanjuti"),
        ],
        string="Status Tindak Lanjut",
        default="no_action_needed",
        required=True,
        tracking=True,
    )
    estimated_cost = fields.Monetary(
        string="Estimasi Biaya Perbaikan",
        currency_field="currency_id",
    )
    realized_cost = fields.Monetary(
        string="Realisasi Biaya Perbaikan",
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

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "/") == "/":
                vals["name"] = (
                    self.env["ir.sequence"].next_by_code("waqf.asset.inspection") or "/"
                )
        records = super().create(vals_list)
        for rec in records:
            # Otomatis mutakhirkan kondisi aset induk
            if rec.asset_id and rec.condition_observed:
                rec.asset_id.write({"asset_condition": rec.condition_observed})
        return records

    def action_mark_in_progress(self):
        for record in self:
            record.write({"action_status": "in_progress"})
            record.message_post(body="Tindak lanjut pemeliharaan/pengamanan sedang diproses.")

    def action_mark_completed(self):
        for record in self:
            record.write({"action_status": "completed"})
            record.message_post(body="Tindak lanjut pemeliharaan fisik aset wakaf telah selesai.")
