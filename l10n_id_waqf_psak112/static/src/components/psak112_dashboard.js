/** @odoo-module **/

import { Component, useState, onWillStart } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

export class Psak112Dashboard extends Component {
    static template = "l10n_id_waqf_psak112.Psak112Dashboard";

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.notification = useService("notification");

        const today = new Date();
        const year = today.getFullYear();
        const firstDayOfYear = `${year}-01-01`;
        const todayStr = today.toISOString().split("T")[0];

        this.state = useState({
            reportType: "financial_position",
            dateFrom: firstDayOfYear,
            dateTo: todayStr,
            loading: true,
            kpis: {},
            reportData: {},
            companyName: "",
            currencySymbol: "Rp",
        });

        onWillStart(async () => {
            await this.loadData();
        });
    }

    async loadData() {
        this.state.loading = true;
        try {
            const res = await this.orm.call(
                "waqf.psak112.report.wizard",
                "get_dashboard_data",
                [],
                {
                    date_from: this.state.dateFrom,
                    date_to: this.state.dateTo,
                    report_type: this.state.reportType,
                }
            );
            this.state.kpis = res.kpis || {};
            this.state.reportData = res.data || {};
            this.state.companyName = res.company_name || "";
            this.state.currencySymbol = res.currency_symbol || "Rp";
        } catch (error) {
            this.notification.add(`Gagal memuat data laporan: ${error.message || error}`, {
                type: "danger",
            });
        } finally {
            this.state.loading = false;
        }
    }

    async onSelectReportType(type) {
        this.state.reportType = type;
        await this.loadData();
    }

    async onDateFromChange(ev) {
        this.state.dateFrom = ev.target.value;
        await this.loadData();
    }

    async onDateToChange(ev) {
        this.state.dateTo = ev.target.value;
        await this.loadData();
    }

    async openPdfWizard() {
        return this.action.doAction({
            name: "Cetak Laporan PSAK 112 (PDF)",
            type: "ir.actions.act_window",
            res_model: "waqf.psak112.report.wizard",
            view_mode: "form",
            views: [[false, "form"]],
            target: "new",
            context: {
                default_report_type: this.state.reportType,
                default_date_from: this.state.dateFrom,
                default_date_to: this.state.dateTo,
            },
        });
    }
}

registry.category("actions").add("waqf_psak112_dashboard", Psak112Dashboard);
