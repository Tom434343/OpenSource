#!/bin/bash

# ==============================================================================
# BASELINE — Creer les references d'integrite systeme
# ==============================================================================
# A lancer UNE FOIS manuellement apres installation propre.
# Re-lancer si changement volontaire du systeme (nouveau package, nouvelle cle...).
# ==============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASELINE_DIR="$SCRIPT_DIR/baseline"
mkdir -p "$BASELINE_DIR"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'

ok()   { echo -e "  ${GREEN}✅ $1${NC}"; }
info() { echo -e "  ${CYAN}ℹ  $1${NC}"; }
warn() { echo -e "  ${YELLOW}⚠️  $1${NC}"; }

echo ""
echo "╔════════════════════════════════════════════════════════════════════════════╗"
echo "║           BASELINE — Creation references integrite                         ║"
echo "╚════════════════════════════════════════════════════════════════════════════╝"
echo ""
echo "  📅 $(date '+%Y-%m-%d %H:%M:%S')"
echo "  📁 Baseline : $BASELINE_DIR"
echo ""

# ==============================================================================
# 1. Cles SSH privees
# ==============================================================================
echo "━━━ Cles SSH ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
SSH_DIR="$HOME/.ssh"
SHA_FILE="$BASELINE_DIR/ssh-keys.sha256"
> "$SHA_FILE"

# Detecte automatiquement toutes les cles privees (fichiers sans extension .pub)
KEY_COUNT=0
for key in "$SSH_DIR"/*; do
    if [ -f "$key" ] && [ "${key##*.}" != "pub" ] && [ "$(basename "$key")" != "known_hosts" ] && [ "$(basename "$key")" != "authorized_keys" ] && [ "$(basename "$key")" != "config" ]; then
        # Verifier que c'est bien une cle privee (commence par -----BEGIN)
        if head -1 "$key" 2>/dev/null | grep -q "BEGIN"; then
            sha256sum "$key" >> "$SHA_FILE"
            ok "$(basename "$key")"
            KEY_COUNT=$((KEY_COUNT+1))
        fi
    fi
done
# Aussi chercher dans les sous-dossiers (find au lieu de ** qui necessite globstar)
while IFS= read -r key; do
    if [ "${key##*.}" != "pub" ]; then
        if head -1 "$key" 2>/dev/null | grep -q "BEGIN"; then
            grep -q "$key" "$SHA_FILE" 2>/dev/null || {
                sha256sum "$key" >> "$SHA_FILE"
                ok "$(basename "$key")"
                KEY_COUNT=$((KEY_COUNT+1))
            }
        fi
    fi
done < <(find "$SSH_DIR" -mindepth 2 -type f 2>/dev/null)

chmod 600 "$SHA_FILE"
info "$KEY_COUNT cles privees referenceees → $SHA_FILE"
echo ""

# ==============================================================================
# 2. Utilisateurs systeme (/etc/passwd)
# ==============================================================================
echo "━━━ Utilisateurs ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
cp /etc/passwd "$BASELINE_DIR/passwd.baseline"
sha256sum /etc/passwd > "$BASELINE_DIR/passwd.sha256"
ok "/etc/passwd — $(wc -l < /etc/passwd) utilisateurs"
echo ""

# ==============================================================================
# 3. Sudoers
# ==============================================================================
echo "━━━ Sudoers ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
sudo sha256sum /etc/sudoers > "$BASELINE_DIR/sudoers.sha256" 2>/dev/null
if [ -d /etc/sudoers.d ]; then
    find /etc/sudoers.d -type f | sort | xargs sudo sha256sum 2>/dev/null \
        >> "$BASELINE_DIR/sudoers.sha256"
fi
chmod 600 "$BASELINE_DIR/sudoers.sha256"
ok "/etc/sudoers + sudoers.d/"
echo ""

# ==============================================================================
# 4. Crontabs
# ==============================================================================
echo "━━━ Crontabs ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
CRON_FILE="$BASELINE_DIR/crontabs.baseline"
> "$CRON_FILE"
echo "=== crontab -l ===" >> "$CRON_FILE"
crontab -l 2>/dev/null >> "$CRON_FILE"
echo "=== /etc/crontab ===" >> "$CRON_FILE"
cat /etc/crontab 2>/dev/null >> "$CRON_FILE"
echo "=== /etc/cron.d/ ===" >> "$CRON_FILE"
ls -la /etc/cron.d/ 2>/dev/null >> "$CRON_FILE"
sha256sum "$CRON_FILE" > "$BASELINE_DIR/crontabs.sha256"
ok "crontab user + /etc/crontab + /etc/cron.d/"
echo ""

# ==============================================================================
# 5. Fichiers SUID/SGID
# ==============================================================================
echo "━━━ Fichiers SUID/SGID ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
SUID_FILE="$BASELINE_DIR/suid-files.txt"
find / -type f \( -perm -4000 -o -perm -2000 \) 2>/dev/null | sort > "$SUID_FILE"
ok "$(wc -l < "$SUID_FILE") fichiers SUID/SGID references"
echo ""

# ==============================================================================
# 6. Binaires systeme (/usr/bin, /usr/sbin, /bin, /sbin)
# ==============================================================================
echo "━━━ Binaires systeme ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
BIN_FILE="$BASELINE_DIR/binaries.sha256"
find /usr/bin /usr/sbin /bin /sbin -type f 2>/dev/null \
    | sort | xargs sha256sum 2>/dev/null > "$BIN_FILE"
ok "$(wc -l < "$BIN_FILE") binaires hashes"
info "→ Verification lente au check — patience"
echo ""

# ==============================================================================
# 7. Ports en ecoute
# ==============================================================================
echo "━━━ Ports en ecoute ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
ss -tlnp 2>/dev/null > "$BASELINE_DIR/listening-ports.baseline"
ok "$(grep -c LISTEN "$BASELINE_DIR/listening-ports.baseline" 2>/dev/null || echo 0) ports references"
echo ""

# ==============================================================================
# Metadata
# ==============================================================================
cat > "$BASELINE_DIR/baseline-info.txt" << EOF
date=$(date '+%Y-%m-%d %H:%M:%S')
hostname=$(hostname)
kernel=$(uname -r)
user=$(whoami)
EOF

echo ""
echo "╔════════════════════════════════════════════════════════════════════════════╗"
echo "║                        BASELINE CREEE                                     ║"
echo "╚════════════════════════════════════════════════════════════════════════════╝"
echo ""
echo "  Fichiers crees dans : $BASELINE_DIR/"
ls -lh "$BASELINE_DIR/"
echo ""
echo -e "  ${YELLOW}⚠️  Relancer ce script si changement volontaire du systeme.${NC}"
echo ""

read -p "Appuyez sur Entree pour fermer..." dummy
