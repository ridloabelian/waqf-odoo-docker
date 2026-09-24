# Copyright 2026 Forum Wakaf Produktif (FWP / fwp.or.id)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import fields, models


class WaqfType(models.Model):
    _name = "waqf.type"
    _description = "Jenis Harta Benda Wakaf"
    _order = "sequence, name"

    name = fields.Char(
        string="Nama Jenis Harta Wakaf",
        required=True,
        translate=True,
    )
    code = fields.Char(
        string="Kode Klasifikasi",
        required=True,
    )
    category = fields.Selection(
        selection=[
            ("immovable", "Benda Tidak Bergerak (Tanah/Bangunan)"),
            ("movable_cash", "Benda Bergerak - Uang (Wakaf Uang)"),
            ("movable_other", "Benda Bergerak Selain Uang (HAKI, Kendaraan, Mesin, dll.)"),
        ],
        string="Kategori Harta Wakaf (UU 41/2004)",
        required=True,
        default="movable_cash",
    )
    description = fields.Text(
        string="Deskripsi & Ketentuan Syariah",
    )
    active = fields.Boolean(
        string="Aktif",
        default=True,
    )
    sequence = fields.Integer(
        string="Urutan",
        default=10,
    )
