===========================================
Akuntansi Wakaf PSAK 112 & Regulasi UU 41/2004
===========================================

.. 
   Copyright 2026 Forum Wakaf Produktif (FWP / fwp.or.id)
   License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

Modul ini mengimplementasikan Standar Akuntansi Keuangan Syariah PSAK 112 (Akuntansi Wakaf) yang diterbitkan oleh IAI (Ikatan Akuntan Indonesia) dan kepatuhan terhadap UU No. 41 Tahun 2004 tentang Wakaf, dibangun untuk **Odoo 19.0 Community Edition** (kompatibel Odoo 18 & 19) menggunakan engine pelaporan terbaru ``account.report`` dan sintaks Odoo Web Library (OWL).

Fitur Utama:
------------
1. **Engine Pelaporan Modern (account.report)**:
   - Terintegrasi dengan model pelaporan modern Odoo 18/19: ``account.report``, ``account.report.column``, ``account.report.line``, dan ``account.report.expression``.
   - Perhitungan berbasis ``account_codes`` dan rumus ``aggregation`` otomatis.
   - Mendukung perbandingan antar periode (period comparison).

2. **Dashboard Interaktif Berbasis OWL (Odoo Web Library)**:
   - Client Action OWL modern (``waqf_psak112_dashboard``) dengan antarmuka responsif dan reaktif.
   - Kartu metrik KPI *real-time*: Total Aset Wakaf, Aset Neto Permanen, Aset Neto Temporer, Aset Neto Tidak Terikat (Surplus Siap Salur), dan Rasio Kepatuhan Hak Nazhir.
   - Pilihan filter periode dinamis tanpa memuat ulang seluruh halaman.

3. **Klasifikasi Aset Neto Standar PSAK 112**:
   - *Aset Neto Terikat Permanen*: Pokok wakaf abadi (muabbad) yang wajib dijaga keutuhannya selamanya.
   - *Aset Neto Terikat Temporer*: Pokok wakaf berjangka (muaqqat) yang wajib dikembalikan saat jatuh tempo.
   - *Aset Neto Tidak Terikat*: Akumulasi surplus bersih hasil pengelolaan wakaf produktif yang siap disalurkan kepada Mauquf 'Alaih.

4. **Aturan Validasi Syariah (@api.constrains)**:
   - Sistem menolak transaksi jurnal (``account.move``) yang mendebit/mengurangi Aset Neto Terikat Permanen untuk membiayai beban operasional atau beban penyaluran manfaat kepada Mauquf 'Alaih.
   - Penyaluran manfaat kepada Mauquf 'Alaih diwajibkan bersumber murni dari surplus hasil pengelolaan.

5. **Batasan Otomatis Hak Nazhir (UU 41/2004 Pasal 12)**:
   - Menghitung otomatis surplus/hasil bersih pengelolaan (Pendapatan Kotor Pengelolaan dikurangi Beban Langsung).
   - Membatasi imbalan nazhir secara otomatis maksimal 10% dari hasil bersih.
   - Menghasilkan entri jurnal pengakuan hak nazhir secara otomatis saat diverifikasi.

6. **4 Template Laporan Keuangan Wajib PSAK 112**:
   - Laporan Posisi Keuangan (Statement of Financial Position)
   - Laporan Rincian Aset Wakaf (Statement of Waqf Asset Details)
   - Laporan Aktivitas (Statement of Activities)
   - Laporan Arus Kas (Statement of Cash Flows)
   - Disertai wizard pemilihan periode dan cetak QWeb PDF resmi.

Konfigurasi & Penggunaan:
-------------------------
1. Pasang modul ``l10n_id_waqf_psak112``.
2. Akses menu **Pengelolaan Wakaf > Akuntansi PSAK 112**.
3. Buka **Dashboard & Laporan PSAK 112** untuk tampilan interaktif OWL.
4. Kelola bagan akun melalui menu **Konfigurasi > Bagan Akun PSAK 112**.
5. Lakukan penutupan periode dan alokasi hak nazhir melalui menu **Hak Nazhir (Maks 10% UU 41/2004)**.
6. Cetak laporan resmi berstandar IAI melalui menu **Cetak Laporan PDF (PSAK 112)**.
