# ==============================================================================
# DOCKERFILE - ODOO 19.0 PRODUCTION FOR ERP WAKAF FWP
# Forum Wakaf Produktif (FWP) - Standar PSAK 112 & LSP BWI
# ==============================================================================
# Base image resmi Odoo 19.0
ARG ODOO_BASE_IMAGE=odoo:19.0
FROM ${ODOO_BASE_IMAGE}

LABEL maintainer="Forum Wakaf Produktif (FWP) <info@fwp.or.id>"
LABEL description="Odoo 19.0 Community Edition dengan dependensi akuntansi PSAK 112, QR Code Wakaf, dan ekspor laporan keuangan"

USER root

# Pasang paket sistem yang diperlukan untuk kompilasi dan utilitas
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    libpq-dev \
    libxml2-dev \
    libxslt1-dev \
    zlib1g-dev \
    git \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Pasang dependensi Python penting untuk ERP Wakaf:
# - num2words: Konversi angka nominal ke huruf terbilang (Rupiah) pada Akta Ikrar Wakaf & Kuitansi
# - openpyxl & xlsxwriter: Ekspor laporan keuangan PSAK 112 (Neraca, Arus Kas, Perubahan Aset Neto) ke Excel
# - qrcode: Pembuatan QR Code verifikasi keaslian Sertifikat Wakaf BWI
# - phonenumbers: Format dan validasi nomor telepon/WhatsApp wakif di Indonesia
RUN pip3 install --no-cache-dir --break-system-packages \
    num2words \
    openpyxl \
    xlsxwriter \
    qrcode[pil] \
    phonenumbers

# Buat direktori kustom addons jika belum ada
RUN mkdir -p /mnt/extra-addons && chown -R odoo:odoo /mnt/extra-addons

# Kembalikan user ke non-root 'odoo' demi keamanan
USER odoo

EXPOSE 8069 8072
