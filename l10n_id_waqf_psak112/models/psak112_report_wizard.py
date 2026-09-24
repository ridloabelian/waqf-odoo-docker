# Copyright 2026 Forum Wakaf Produktif (FWP / fwp.or.id)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import api, fields, models, _


class WaqfPsak112ReportWizard(models.TransientModel):
    _name = "waqf.psak112.report.wizard"
    _description = "Wizard Laporan Keuangan PSAK 112"

    report_type = fields.Selection(
        selection=[
            ("financial_position", "1. Laporan Posisi Keuangan"),
            ("asset_detail", "2. Laporan Rincian Aset Wakaf"),
            ("activity", "3. Laporan Aktivitas"),
            ("cash_flow", "4. Laporan Arus Kas"),
        ],
        string="Jenis Laporan PSAK 112",
        required=True,
        default="financial_position",
    )
    date_from = fields.Date(
        string="Tanggal Awal Periode",
        required=True,
        default=lambda self: fields.Date.today().replace(month=1, day=1),
    )
    date_to = fields.Date(
        string="Tanggal Akhir Periode / Per Tanggal",
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

    def _get_category_balance(self, category_code, date_limit, cumulative=True):
        """Menghitung saldo akun per kategori PSAK 112."""
        domain = [
            ("account_id.psak112_category", "=", category_code),
            ("company_id", "=", self.company_id.id),
            ("move_id.state", "=", "posted"),
        ]
        if cumulative:
            domain.append(("date", "<=", date_limit))
        else:
            domain.extend([("date", ">=", self.date_from), ("date", "<=", date_limit)])

        lines = self.env["account.move.line"].search(domain)
        # Untuk akun aset & beban: Saldo = Debit - Credit
        # Untuk akun liabilitas, ekuitas/aset neto, & pendapatan: Saldo = Credit - Debit
        if category_code.startswith("asset_") or category_code.startswith("expense_"):
            return sum(lines.mapped(lambda l: l.debit - l.credit))
        else:
            return sum(lines.mapped(lambda l: l.credit - l.debit))

    def get_report_data(self):
        """Menyiapkan struktur data teragregasi untuk 4 laporan PSAK 112."""
        self.ensure_one()
        data = {
            "wizard": self,
            "company": self.company_id,
            "currency": self.currency_id,
            "report_type": self.report_type,
            "date_from": self.date_from,
            "date_to": self.date_to,
        }

        if self.report_type == "financial_position":
            # 1. Laporan Posisi Keuangan
            kas_wakaf = self._get_category_balance("asset_cash_waqf", self.date_to)
            piutang = self._get_category_balance("asset_receivable", self.date_to)
            investasi = self._get_category_balance("asset_investment", self.date_to)
            tanah = self._get_category_balance("asset_land", self.date_to)
            bangunan = self._get_category_balance("asset_building", self.date_to)
            penyusutan = self._get_category_balance("asset_accum_depr", self.date_to)

            total_aset = kas_wakaf + piutang + investasi + tanah + bangunan - abs(penyusutan)

            liab_pendek = self._get_category_balance("liability_short", self.date_to)
            liab_temporer = self._get_category_balance("liability_temporary_due", self.date_to)
            total_liabilitas = liab_pendek + liab_temporer

            neto_permanen = self._get_category_balance("net_asset_permanent", self.date_to)
            neto_temporer = self._get_category_balance("net_asset_temporary", self.date_to)
            neto_tidak_terikat = self._get_category_balance("net_asset_unrestricted", self.date_to)
            total_aset_neto = neto_permanen + neto_temporer + neto_tidak_terikat

            data["position"] = {
                "kas_wakaf": kas_wakaf,
                "piutang": piutang,
                "investasi": investasi,
                "tanah": tanah,
                "bangunan": bangunan,
                "penyusutan": abs(penyusutan),
                "total_aset": total_aset,
                "liab_pendek": liab_pendek,
                "liab_temporer": liab_temporer,
                "total_liabilitas": total_liabilitas,
                "neto_permanen": neto_permanen,
                "neto_temporer": neto_temporer,
                "neto_tidak_terikat": neto_tidak_terikat,
                "total_aset_neto": total_aset_neto,
                "total_liab_neto": total_liabilitas + total_aset_neto,
            }

        elif self.report_type == "asset_detail":
            # 2. Laporan Rincian Aset Wakaf
            pledges = self.env["waqf.pledge"].search([
                ("company_id", "=", self.company_id.id),
                ("state", "=", "issued"),
                ("date_pledge", "<=", self.date_to),
            ])
            data["asset_detail"] = {
                "pledges": pledges,
                "cash_permanent": sum(pledges.filtered(lambda p: p.waqf_category == "movable_cash" and p.waqf_nature == "perpetual").mapped("amount_nominal")),
                "cash_temporary": sum(pledges.filtered(lambda p: p.waqf_category == "movable_cash" and p.waqf_nature == "temporary").mapped("amount_nominal")),
                "immovable_land": sum(pledges.filtered(lambda p: p.waqf_type_id.code == "WQF-LAND").mapped("estimated_value")),
                "immovable_building": sum(pledges.filtered(lambda p: p.waqf_type_id.code == "WQF-BLD").mapped("estimated_value")),
                "movable_other": sum(pledges.filtered(lambda p: p.waqf_category == "movable_other").mapped("estimated_value")),
            }

        elif self.report_type == "activity":
            # 3. Laporan Aktivitas
            terima_permanen = self._get_category_balance("receipt_waqf_cash_permanent", self.date_to, cumulative=False)
            terima_temporer = self._get_category_balance("receipt_waqf_cash_temporary", self.date_to, cumulative=False)
            terima_nonkas = self._get_category_balance("receipt_waqf_noncash", self.date_to, cumulative=False)
            hasil_kelola = self._get_category_balance("revenue_yield", self.date_to, cumulative=False)

            hak_nazhir = self._get_category_balance("expense_nazhir_share", self.date_to, cumulative=False)
            beban_kelola = self._get_category_balance("expense_management", self.date_to, cumulative=False)
            beban_salur = self._get_category_balance("expense_distribution", self.date_to, cumulative=False)

            total_penerimaan = terima_permanen + terima_temporer + terima_nonkas + hasil_kelola
            total_beban = hak_nazhir + beban_kelola + beban_salur
            surplus_periode = total_penerimaan - total_beban

            data["activity"] = {
                "terima_permanen": terima_permanen,
                "terima_temporer": terima_temporer,
                "terima_nonkas": terima_nonkas,
                "hasil_kelola": hasil_kelola,
                "hak_nazhir": hak_nazhir,
                "beban_kelola": beban_kelola,
                "beban_salur": beban_salur,
                "total_penerimaan": total_penerimaan,
                "total_beban": total_beban,
                "surplus_periode": surplus_periode,
            }

        elif self.report_type == "cash_flow":
            # 4. Laporan Arus Kas
            kas_terima_permanen = self._get_category_balance("receipt_waqf_cash_permanent", self.date_to, cumulative=False)
            kas_terima_temporer = self._get_category_balance("receipt_waqf_cash_temporary", self.date_to, cumulative=False)
            kas_hasil_kelola = self._get_category_balance("revenue_yield", self.date_to, cumulative=False)

            kas_salur = self._get_category_balance("expense_distribution", self.date_to, cumulative=False)
            kas_hak_nazhir = self._get_category_balance("expense_nazhir_share", self.date_to, cumulative=False)
            kas_beban_kelola = self._get_category_balance("expense_management", self.date_to, cumulative=False)

            arus_kas_operasi = kas_hasil_kelola - (kas_salur + kas_hak_nazhir + kas_beban_kelola)
            arus_kas_wakaf = kas_terima_permanen + kas_terima_temporer
            kenaikan_bersih_kas = arus_kas_operasi + arus_kas_wakaf

            saldo_awal_kas = self._get_category_balance("asset_cash_waqf", self.date_from)
            saldo_akhir_kas = saldo_awal_kas + kenaikan_bersih_kas

            data["cash_flow"] = {
                "kas_terima_permanen": kas_terima_permanen,
                "kas_terima_temporer": kas_terima_temporer,
                "kas_hasil_kelola": kas_hasil_kelola,
                "kas_salur": kas_salur,
                "kas_hak_nazhir": kas_hak_nazhir,
                "kas_beban_kelola": kas_beban_kelola,
                "arus_kas_operasi": arus_kas_operasi,
                "arus_kas_wakaf": arus_kas_wakaf,
                "kenaikan_bersih_kas": kenaikan_bersih_kas,
                "saldo_awal_kas": saldo_awal_kas,
                "saldo_akhir_kas": saldo_akhir_kas,
            }

        return data

    def action_print_pdf(self):
        """Mencetak laporan PSAK 112 dalam format PDF."""
        self.ensure_one()
        return self.env.ref("l10n_id_waqf_psak112.action_report_psak112_document").report_action(self)
