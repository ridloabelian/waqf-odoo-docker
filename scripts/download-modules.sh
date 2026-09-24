#!/usr/bin/env bash
# ==============================================================================
# WAQF ODOO DOCKER - MODULE DOWNLOAD & UPDATE UTILITY
# Forum Wakaf Produktif (FWP) - Standar PSAK 112 & LSP BWI
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
EXTRA_ADDONS_DIR="$PROJECT_ROOT/extra-addons"

# Default repositori ekosistem modul wakaf FWP & ANI
REPO_URL="${WAQF_MODULES_REPO:-https://github.com/ridloabelian/waqf-odoo-modules.git}"
BRANCH="${WAQF_MODULES_BRANCH:-19.0}"

echo "===================================================================="
echo "    UNDUH / PERBARUI MODUL WAKAF (PSAK 412/112 & LSP BWI)          "
echo "===================================================================="
echo "Direktori target: $EXTRA_ADDONS_DIR"
echo "Repositori:       $REPO_URL"
echo "Branch:           $BRANCH"
echo ""

mkdir -p "$EXTRA_ADDONS_DIR"

TARGET_DIR="$EXTRA_ADDONS_DIR/waqf-odoo-modules"

if [[ -d "$TARGET_DIR/.git" ]]; then
    echo "Memperbarui modul yang sudah ada (git pull)..."
    git -C "$TARGET_DIR" checkout "$BRANCH" 2>/dev/null || true
    git -C "$TARGET_DIR" pull --ff-only || {
        echo "[WARN] Gagal auto-pull fast forward. Mengabaikan perubahan lokal..."
        git -C "$TARGET_DIR" fetch origin "$BRANCH"
        git -C "$TARGET_DIR" reset --hard "origin/$BRANCH"
    }
else
    echo "Mengkloning modul wakaf dari repositori FWP..."
    if git clone --branch "$BRANCH" --depth 1 "$REPO_URL" "$TARGET_DIR"; then
        echo "✓ Kloning modul wakaf berhasil."
    else
        echo "[INFO] Repositori publik belum tersedia di URL ini, atau sedang dalam mode privat."
        echo "Anda dapat meletakkan folder modul Odoo Wakaf secara manual ke dalam folder:"
        echo "  $EXTRA_ADDONS_DIR/"
    fi
fi

# Set izin akses folder agar container Odoo dapat membacanya
chmod -R 755 "$EXTRA_ADDONS_DIR"

echo ""
echo "Daftar modul yang tersedia di extra-addons:"
ls -la "$EXTRA_ADDONS_DIR"
echo ""
echo "Untuk memperbarui daftar aplikasi di Odoo:"
echo "1. Masuk ke Odoo dengan hak akses Administrator."
echo "2. Aktifkan Mode Pengembang (Developer Mode)."
echo "3. Buka menu Apps -> Update Apps List."
echo "4. Cari 'Waqf' atau 'PSAK 112' dan klik 'Install'."
echo "===================================================================="
