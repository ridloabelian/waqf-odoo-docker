#!/usr/bin/env bash
# ==============================================================================
# WAQF ODOO DOCKER - INITIAL SETUP & PROVISIONING SCRIPT
# Forum Wakaf Produktif (FWP) & Asosiasi Nazhir Indonesia (ANI)
# Standar Akuntansi PSAK 412 (PSAK 112) & Standar LSP BWI
# ==============================================================================
set -euo pipefail

# Pewarnaan Output Terminal
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${GREEN}===================================================================${NC}"
echo -e "${CYAN}   INISIALISASI ODOO WAKAF DOCKER (PSAK 412 / 112 & LSP BWI)      ${NC}"
echo -e "${PURPLE}  Kolaborasi Forum Wakaf Produktif (FWP) & Asosiasi Nazhir (ANI)   ${NC}"
echo -e "${GREEN}===================================================================${NC}"
echo ""

# ------------------------------------------------------------------------------
# 1. Pengecekan Hak Akses Root / Sudo
# ------------------------------------------------------------------------------
if [[ $EUID -ne 0 ]]; then
   echo -e "${YELLOW}[PERINGATAN] Disarankan menjalankan skrip ini dengan hak akses root atau sudo untuk mengonfigurasi Swap file dan izin folder.${NC}"
fi

# ------------------------------------------------------------------------------
# 2. Pengecekan Docker & Docker Compose
# ------------------------------------------------------------------------------
echo -e "${BLUE}[1/5] Memeriksa Instalasi Docker & Docker Compose...${NC}"

if ! command -v docker &> /dev/null; then
    echo -e "${RED}[ERROR] Docker belum terpasang di sistem ini!${NC}"
    echo -e "${YELLOW}Silakan pasang Docker terlebih dahulu dengan menjalankan perintah:${NC}"
    echo -e "  curl -fsSL https://get.docker.com | sh"
    echo -e "  sudo usermod -aG docker \$USER"
    exit 1
fi

if ! docker compose version &> /dev/null; then
    echo -e "${RED}[ERROR] Docker Compose (v2) belum terpasang atau plugin compose tidak ditemukan!${NC}"
    echo -e "${YELLOW}Silakan pasang plugin docker-compose-plugin:${NC}"
    echo -e "  sudo apt-get update && sudo apt-get install -y docker-compose-plugin"
    exit 1
fi

echo -e "  ${GREEN}✓ Docker terdeteksi:${NC} $(docker --version)"
echo -e "  ${GREEN}✓ Docker Compose terdeteksi:${NC} $(docker compose version)"

# ------------------------------------------------------------------------------
# 3. Pengecekan & Pembuatan Swap File (Mencegah Crash OOM di VPS 4 GB)
# ------------------------------------------------------------------------------
echo ""
echo -e "${BLUE}[2/5] Memeriksa Alokasi Swap Memory VPS...${NC}"

SWAP_SIZE_MB=$(free -m | awk '/^Swap:/ {print $2}')

if [[ "$SWAP_SIZE_MB" -lt 2048 ]]; then
    echo -e "  ${YELLOW}! Swap saat ini: ${SWAP_SIZE_MB}MB (Di bawah rekomendasi 2048MB).${NC}"
    if [[ $EUID -eq 0 ]]; then
        echo -e "  ${BLUE}→ Membuat Swap File 2 GB otomatis di /swapfile untuk stabilitas...${NC}"
        if [[ ! -f /swapfile ]]; then
            fallocate -l 2G /swapfile || dd if=/dev/zero of=/swapfile bs=1M count=2048
            chmod 600 /swapfile
            mkswap /swapfile
            swapon /swapfile
            if ! grep -q '/swapfile' /etc/fstab; then
                echo '/swapfile none swap sw 0 0' >> /etc/fstab
            fi
            sysctl vm.swappiness=10
            if ! grep -q 'vm.swappiness' /etc/sysctl.conf; then
                echo 'vm.swappiness=10' >> /etc/sysctl.conf
            fi
            echo -e "  ${GREEN}✓ Swap File 2 GB berhasil dibuat dan diaktifkan.${NC}"
        else
            echo -e "  ${YELLOW}! /swapfile sudah ada tetapi belum aktif. Menjalankan swapon...${NC}"
            swapon /swapfile 2>/dev/null || true
        fi
    else
        echo -e "  ${YELLOW}! Tidak dapat membuat swap otomatis tanpa akses root. Abaikan jika VPS Anda memiliki RAM >= 8GB.${NC}"
    fi
else
    echo -e "  ${GREEN}✓ Alokasi Swap mencukupi:${NC} ${SWAP_SIZE_MB}MB"
fi

# ------------------------------------------------------------------------------
# 4. Pengaturan Variabel Lingkungan (.env) & Pembuatan Kredensial Acak
# ------------------------------------------------------------------------------
echo ""
echo -e "${BLUE}[3/5] Mengonfigurasi Variabel Lingkungan (.env)...${NC}"

generate_password() {
    if command -v openssl &> /dev/null; then
        openssl rand -base64 24 | tr -dc 'a-zA-Z0-9' | head -c 20
    else
        head /dev/urandom | tr -dc 'a-zA-Z0-9' | head -c 20
    fi
}

ENV_FILE=".env"
ENV_EXAMPLE=".env.example"

if [[ ! -f "$ENV_FILE" ]]; then
    if [[ -f "$ENV_EXAMPLE" ]]; then
        cp "$ENV_EXAMPLE" "$ENV_FILE"
        echo -e "  ${GREEN}✓ File .env dibuat dari .env.example${NC}"
    else
        echo -e "${RED}[ERROR] File .env.example tidak ditemukan!${NC}"
        exit 1
    fi
fi

# Cek apakah password masih default atau placeholder
RAND_DB_PASS=$(generate_password)
RAND_ADMIN_PASS=$(generate_password)

if grep -q "GantiDenganPasswordDatabaseYangSangatKuatDanAman123!" "$ENV_FILE"; then
    sed -i "s|POSTGRES_PASSWORD=GantiDenganPasswordDatabaseYangSangatKuatDanAman123!|POSTGRES_PASSWORD=${RAND_DB_PASS}|g" "$ENV_FILE"
    echo -e "  ${GREEN}✓ Generated Database Password baru yang aman.${NC}"
fi

if grep -q "GantiDenganMasterPasswordOdooYangSangatKuatDanAman123!" "$ENV_FILE"; then
    sed -i "s|ADMIN_PASSWORD=GantiDenganMasterPasswordOdooYangSangatKuatDanAman123!|ADMIN_PASSWORD=${RAND_ADMIN_PASS}|g" "$ENV_FILE"
    echo -e "  ${GREEN}✓ Generated Odoo Admin Master Password baru yang aman.${NC}"
fi

# ------------------------------------------------------------------------------
# 5. Sinkronisasi config/odoo.conf dari .env
# ------------------------------------------------------------------------------
echo ""
echo -e "${BLUE}[4/5] Mensinkronkan Konfigurasi Odoo (config/odoo.conf)...${NC}"

# Baca nilai aktual dari .env
CURRENT_ADMIN_PASS=$(grep -E '^ADMIN_PASSWORD=' "$ENV_FILE" | cut -d '=' -f2-)
CURRENT_WORKERS=$(grep -E '^ODOO_WORKERS=' "$ENV_FILE" | cut -d '=' -f2- || echo "4")
CURRENT_LIMIT_SOFT=$(grep -E '^ODOO_LIMIT_MEMORY_SOFT=' "$ENV_FILE" | cut -d '=' -f2- || echo "2147483648")
CURRENT_LIMIT_HARD=$(grep -E '^ODOO_LIMIT_MEMORY_HARD=' "$ENV_FILE" | cut -d '=' -f2- || echo "2684354560")
CURRENT_TIME_CPU=$(grep -E '^ODOO_LIMIT_TIME_CPU=' "$ENV_FILE" | cut -d '=' -f2- || echo "600")
CURRENT_TIME_REAL=$(grep -E '^ODOO_LIMIT_TIME_REAL=' "$ENV_FILE" | cut -d '=' -f2- || echo "1200")

if [[ -f "config/odoo.conf.template" ]]; then
    sed -e "s|\${ADMIN_PASSWORD}|${CURRENT_ADMIN_PASS}|g" \
        -e "s|\${ODOO_WORKERS}|${CURRENT_WORKERS}|g" \
        -e "s|\${ODOO_LIMIT_MEMORY_SOFT}|${CURRENT_LIMIT_SOFT}|g" \
        -e "s|\${ODOO_LIMIT_MEMORY_HARD}|${CURRENT_LIMIT_HARD}|g" \
        -e "s|\${ODOO_LIMIT_TIME_CPU}|${CURRENT_TIME_CPU}|g" \
        -e "s|\${ODOO_LIMIT_TIME_REAL}|${CURRENT_TIME_REAL}|g" \
        config/odoo.conf.template > config/odoo.conf
    echo -e "  ${GREEN}✓ config/odoo.conf berhasil digenerate dari template.${NC}"
fi

# ------------------------------------------------------------------------------
# 6. Pembuatan Folder & Izin Akses Direktori
# ------------------------------------------------------------------------------
echo ""
echo -e "${BLUE}[5/5] Menyiapkan Struktur Direktori & Izin Akses...${NC}"

mkdir -p ./extra-addons
mkdir -p ./backups
mkdir -p ./config

# Odoo container runs as user 'odoo' (UID 101 biasanya di debian)
# Memberikan izin baca/tulis agar container Odoo dapat membaca modul
chmod -R 755 ./extra-addons
chmod -R 755 ./waqf_core 2>/dev/null || true
chmod -R 755 ./l10n_id_waqf_psak112 2>/dev/null || true
chmod -R 755 ./scripts
chmod -R 700 ./backups

echo -e "  ${GREEN}✓ Direktori extra-addons, backups, dan config siap.${NC}"

# ------------------------------------------------------------------------------
# SELESAI
# ------------------------------------------------------------------------------
echo ""
echo -e "${GREEN}===================================================================${NC}"
echo -e "${GREEN}        INISIALISASI SELESAI & SISTEM SIAP DI-DEPLOY!              ${NC}"
echo -e "${GREEN}===================================================================${NC}"
echo ""
echo -e "${YELLOW}LANGKAH BERIKUTNYA:${NC}"
echo -e "1. Buka file ${CYAN}.env${NC} jika ingin menyesuaikan nama domain dan email SSL:"
echo -e "   ${BLUE}nano .env${NC}"
echo -e "   (Ubah ${CYAN}DOMAIN_NAME${NC} dan ${CYAN}ACME_EMAIL${NC} sesuai domain yayasan/nazhir Anda)"
echo ""
echo -e "2. Jalankan sistem Odoo Wakaf dengan perintah:"
echo -e "   ${GREEN}docker compose up -d${NC}"
echo ""
echo -e "3. Pantau log proses startup:"
echo -e "   ${BLUE}docker compose logs -f${NC}"
echo ""
echo -e "4. Akses melalui browser:"
echo -e "   ${PURPLE}https://<domain-anda>/web/database/manager${NC}"
echo -e "   Gunakan Master Password yang tersimpan di .env untuk membuat database pertama."
echo ""
