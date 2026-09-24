#!/usr/bin/env bash
# ==============================================================================
# WAQF ODOO DOCKER - RESTORE UTILITY SCRIPT
# Forum Wakaf Produktif (FWP) - Standar PSAK 112 & LSP BWI
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

if [[ $# -lt 1 ]]; then
    echo "Penggunaan: $0 <path_ke_file_backup.tar.gz>"
    echo "Contoh:     $0 backups/waqf_backup_20260924_120000.tar.gz"
    exit 1
fi

BACKUP_ARCHIVE="$1"

if [[ ! -f "$BACKUP_ARCHIVE" ]]; then
    echo "[ERROR] File backup tidak ditemukan: $BACKUP_ARCHIVE"
    exit 1
fi

# shellcheck disable=SC1091
set -a
source "$PROJECT_ROOT/.env"
set +a

echo "===================================================================="
echo "          PEMULIHAN DATA (RESTORE) ODOO WAKAF ERP                   "
echo "===================================================================="
echo "PERINGATAN: Tindakan ini akan menimpa data database '${POSTGRES_DB:-postgres}'"
echo "dan filestore yang ada saat ini dengan isi dari arsip backup:"
echo "-> $BACKUP_ARCHIVE"
echo ""
read -r -p "Ketik 'YA' untuk melanjutkan proses restore: " CONFIRM

if [[ "$CONFIRM" != "YA" ]]; then
    echo "Pemulihan data dibatalkan oleh pengguna."
    exit 0
fi

TEMP_EXTRACT="$PROJECT_ROOT/backups/restore_tmp_$(date +%s)"
mkdir -p "$TEMP_EXTRACT"

echo "[1/4] Mengekstrak arsip backup..."
tar -xzf "$BACKUP_ARCHIVE" -C "$TEMP_EXTRACT"

if [[ ! -f "$TEMP_EXTRACT/database.sql.gz" ]]; then
    echo "[ERROR] Arsip backup tidak memiliki file 'database.sql.gz' yang valid!"
    rm -rf "$TEMP_EXTRACT"
    exit 1
fi

echo "[2/4] Menghentikan service web Odoo sementara..."
docker compose stop web

echo "[3/4] Memulihkan database PostgreSQL..."
docker compose exec -T db dropdb -U "${POSTGRES_USER:-odoo}" --if-exists "${POSTGRES_DB:-postgres}"
docker compose exec -T db createdb -U "${POSTGRES_USER:-odoo}" "${POSTGRES_DB:-postgres}"
gunzip -c "$TEMP_EXTRACT/database.sql.gz" | docker compose exec -T db psql -U "${POSTGRES_USER:-odoo}" -d "${POSTGRES_DB:-postgres}" > /dev/null

if [[ -f "$TEMP_EXTRACT/filestore.tar.gz" ]]; then
    echo "[4/4] Memulihkan Odoo Filestore..."
    docker compose exec -T web mkdir -p /var/lib/odoo/filestore 2>/dev/null || true
    # Salin filestore ke container web
    docker compose cp "$TEMP_EXTRACT/filestore.tar.gz" web:/tmp/filestore.tar.gz
    docker compose exec -T web tar -xzf /tmp/filestore.tar.gz -C /var/lib/odoo/
    docker compose exec -T web rm -f /tmp/filestore.tar.gz
fi

rm -rf "$TEMP_EXTRACT"

echo "Menghidupkan kembali service web Odoo..."
docker compose start web

echo "===================================================================="
echo "DATA BERHASIL DIPULIHKAN DENGAN SEMPURNA!"
echo "===================================================================="
