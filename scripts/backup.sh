#!/usr/bin/env bash
# ==============================================================================
# WAQF ODOO DOCKER - AUTOMATED BACKUP SCRIPT
# Forum Wakaf Produktif (FWP) & Asosiasi Nazhir Indonesia (ANI)
# Standar Akuntansi PSAK 412 (PSAK 112) & Standar LSP BWI
# ==============================================================================
# Skrip ini mencadangkan Database PostgreSQL dan Odoo Filestore (lampiran dokumen,
# bukti transfer wakaf, akta ikrar wakaf) ke dalam satu file arsip terkompresi.
#
# Cocok untuk dieksekusi secara harian melalui cron job:
# 0 2 * * * cd /path/to/waqf-odoo-docker && ./scripts/backup.sh >> /var/log/waqf_backup.log 2>&1
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

# Muat variabel lingkungan dari .env
if [[ -f "$PROJECT_ROOT/.env" ]]; then
    # shellcheck disable=SC1091
    set -a
    source "$PROJECT_ROOT/.env"
    set +a
else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [ERROR] File .env tidak ditemukan di $PROJECT_ROOT"
    exit 1
fi

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_DIR="${BACKUP_DIR:-$PROJECT_ROOT/backups}"
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-7}"
TEMP_DIR="$BACKUP_DIR/tmp_${TIMESTAMP}"
BACKUP_FILE="$BACKUP_DIR/waqf_backup_${TIMESTAMP}.tar.gz"

echo "===================================================================="
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Memulai proses pencadangan Odoo Wakaf ERP..."
echo "===================================================================="

# Pastikan direktori backup tersedia
mkdir -p "$TEMP_DIR"

# 1. Pengecekan container yang berjalan
if ! docker compose ps --services --filter "status=running" | grep -q "^db$"; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [ERROR] Container database (db) tidak berjalan!"
    rm -rf "$TEMP_DIR"
    exit 1
fi

if ! docker compose ps --services --filter "status=running" | grep -q "^web$"; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [ERROR] Container web Odoo (web) tidak berjalan!"
    rm -rf "$TEMP_DIR"
    exit 1
fi

# 2. Dump Database PostgreSQL
echo "[$(date '+%Y-%m-%d %H:%M:%S')] [1/4] Mengekspor Database PostgreSQL (${POSTGRES_DB:-postgres})..."
docker compose exec -T db pg_dump -U "${POSTGRES_USER:-odoo}" "${POSTGRES_DB:-postgres}" | gzip > "$TEMP_DIR/database.sql.gz"

if [[ ! -s "$TEMP_DIR/database.sql.gz" ]]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [ERROR] Database dump kosong atau gagal diekspor!"
    rm -rf "$TEMP_DIR"
    exit 1
fi
echo "[$(date '+%Y-%m-%d %H:%M:%S')]       ✓ Database berhasil diekspor ($(du -h "$TEMP_DIR/database.sql.gz" | cut -f1))"

# 3. Kompresi Odoo Filestore
echo "[$(date '+%Y-%m-%d %H:%M:%S')] [2/4] Mengarsipkan Odoo Filestore (/var/lib/odoo/filestore)..."
docker compose exec -T web tar -czf - -C /var/lib/odoo filestore > "$TEMP_DIR/filestore.tar.gz" 2>/dev/null || true

if [[ ! -f "$TEMP_DIR/filestore.tar.gz" ]]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [WARN] Filestore kosong atau belum terbuat. Membuat arsip kosong..."
    tar -czf "$TEMP_DIR/filestore.tar.gz" -T /dev/null
fi
echo "[$(date '+%Y-%m-%d %H:%M:%S')]       ✓ Filestore berhasil diarsipkan ($(du -h "$TEMP_DIR/filestore.tar.gz" | cut -f1))"

# 4. Buat file manifest informasi backup
cat <<EOF > "$TEMP_DIR/manifest.json"
{
  "system": "waqf-odoo-docker",
  "organization": "Forum Wakaf Produktif (FWP) & Asosiasi Nazhir Indonesia (ANI)",
  "standard": "PSAK 412 (112) & LSP BWI",
  "timestamp": "${TIMESTAMP}",
  "database": "${POSTGRES_DB:-postgres}",
  "created_at": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
}
EOF

# 5. Gabungkan ke dalam satu arsip terenkapsulasi
echo "[$(date '+%Y-%m-%d %H:%M:%S')] [3/4] Menggabungkan arsip backup final..."
tar -czf "$BACKUP_FILE" -C "$TEMP_DIR" database.sql.gz filestore.tar.gz manifest.json
rm -rf "$TEMP_DIR"

BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
echo "[$(date '+%Y-%m-%d %H:%M:%S')]       ✓ File backup selesai dibuat: $BACKUP_FILE ($BACKUP_SIZE)"

# 6. Rotasi Backup Lokal (> RETENTION_DAYS hari)
echo "[$(date '+%Y-%m-%d %H:%M:%S')] [4/4] Memeriksa rotasi backup lokal (> $RETENTION_DAYS hari)..."
find "$BACKUP_DIR" -name "waqf_backup_*.tar.gz" -type f -mtime +"$RETENTION_DAYS" -exec rm -f {} \;
echo "[$(date '+%Y-%m-%d %H:%M:%S')]       ✓ Pembersihan file usang selesai."

# 7. Upload Offsite via Rclone (Jika dikonfigurasi)
if [[ -n "${RCLONE_REMOTE:-}" ]]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [OFFSITE] Mengunggah backup ke cloud storage (${RCLONE_REMOTE}:${RCLONE_DEST_PATH:-WaqfOdooBackups})..."
    if command -v rclone &> /dev/null; then
        rclone copy "$BACKUP_FILE" "${RCLONE_REMOTE}:${RCLONE_DEST_PATH:-WaqfOdooBackups}" --stats-one-line -v
        echo "[$(date '+%Y-%m-%d %H:%M:%S')]       ✓ Upload offsite selesai."
        
        # Rotasi offsite jika didukung rclone
        rclone delete --min-age "${RETENTION_DAYS}d" "${RCLONE_REMOTE}:${RCLONE_DEST_PATH:-WaqfOdooBackups}" 2>/dev/null || true
    else
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] [WARN] Rclone tidak terpasang di host. Lewati upload offsite."
    fi
fi

echo "===================================================================="
echo "[$(date '+%Y-%m-%d %H:%M:%S')] PROSES BACKUP SELESAI DENGAN SUKSES!"
echo "===================================================================="
