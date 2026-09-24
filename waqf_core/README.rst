======================================
Tata Kelola Wakaf - Core & Operasional
======================================

.. 
   Copyright 2026 Forum Wakaf Produktif (FWP / fwp.or.id)
   License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

Modul ini merupakan modul fondasi (*core operational module*) dalam rangkaian sistem digitalisasi wakaf nasional yang diprakarsai oleh Forum Wakaf Produktif (FWP), dirancang untuk **Odoo 19.0 Community Edition** (kompatibel Odoo 18 & 19).

Fitur Utama:
------------
1. **Master Data Wakif (KYC & Profil Donatur)**:
   - Pencatatan identitas individu, organisasi/korporasi, atau kelompok.
   - Validasi kepatuhan format NIK 16 digit dan NPWP/NIB.
   - Status verifikasi KYC sesuai skema SKKNI LSP BWI.
2. **Pencatatan AIW & APAIW**:
   - Akta Ikrar Wakaf (AIW) dan Akta Pengganti AIW (APAIW).
   - Klasifikasi harta wakaf (Benda Bergerak Uang, Benda Bergerak Selain Uang, Benda Tidak Bergerak).
   - Pengelolaan wakaf abadi (*muabbad*) vs. berjangka (*muaqqat*).
   - Integrasi data Pejabat Pembuat AIW (PPAIW / KUA) dan saksi-saksi.
3. **Alur Verifikasi Standar BWI**:
   - Draf -> Terverifikasi Legalitas -> Disetujui Pimpinan Nazhir -> AIW/APAIW Terbit.
4. **Sertifikat Wakaf Digital (QWeb PDF)**:
   - Template resmi siap cetak berstandar Badan Wakaf Indonesia (BWI) dengan ornamen formal dan blok tanda tangan para pihak.
5. **Modern Odoo 18/19 UI/UX**:
   - Menggunakan sintaks modern ``<list>`` dan ``view_mode="list,form"`` yang sepenuhnya selaras dengan arsitektur web Odoo 18 & 19.

Konfigurasi & Penggunaan:
-------------------------
1. Masuk ke menu **Pengelolaan Wakaf > Operasional Wakaf**.
2. Daftarkan wakif melalui menu **Data Wakif**.
3. Buat ikrar wakaf baru melalui menu **Ikrar Wakaf (AIW / APAIW)**.
4. Lakukan verifikasi legalitas, persetujuan pimpinan, dan terbitkan akta.
5. Unduh atau cetak Sertifikat Ikrar Wakaf melalui menu Cetak (Print).
