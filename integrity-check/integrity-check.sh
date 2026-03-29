#!/bin/bash

# ==============================================================================
# INTEGRITY CHECK — Verification complete integrite machine locale
# ==============================================================================
# Usage : bash integrity-check.sh
# Auto  : systemd one-shot au boot + cron quotidien
# Logs  : ~/logs/security/integrity-YYYYMMDD.log
# ==============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASELINE_DIR="$SCRIPT_DIR/baseline"
LOG_DIR="$HOME/logs/security"
LOG_FILE="$LOG_DIR/integrity-$(date +%Y%m%d).log"
INTERACTIVE=true
[ ! -t 1 ] && INTERACTIVE=false

mkdir -p "$LOG_DIR"

# Couleurs (terminal seulement)
if $INTERACTIVE; then
    RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
    CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'
else
    RED=''; GREEN=''; YELLOW=''; CYAN=''; BOLD=''; NC=''
fi

# Compteurs
WARNINGS=0
CRITICALS=0

# Sortie duale : terminal + log
log() { echo -e "$1" | tee -a "$LOG_FILE"; }
ok()       { log "  ${GREEN}✅ $1${NC}"; }
warn()     { log "  ${YELLOW}⚠️  $1${NC}";     WARNINGS=$((WARNINGS+1)); }
critical() { log "  ${RED}🔴 CRITIQUE : $1${NC}"; CRITICALS=$((CRITICALS+1)); }
info()     { log "  ${CYAN}ℹ  $1${NC}"; }
section()  { log ""; log "━━━ $1 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"; }

# ─── Configuration reseau a ignorer dans les connexions ─────────────────────
# Ajoutez vos subnets VPN ou internes ici
IGNORE_NETS="127\.\|::1"
# Exemple avec WireGuard : IGNORE_NETS="127\.\|10\.10\.10\.\|::1"

# ==============================================================================
# ENTETE
# ==============================================================================
log ""
log "╔════════════════════════════════════════════════════════════════════════════╗"
log "║           INTEGRITY CHECK — Verification systeme                          ║"
log "╚════════════════════════════════════════════════════════════════════════════╝"
log ""
log "  📅 $(date '+%Y-%m-%d %H:%M:%S')"
log "  🖥  $(hostname) | $(uname -r)"
log "  📄 Log : $LOG_FILE"
log ""

# Verifier baseline
if [ ! -f "$BASELINE_DIR/baseline-info.txt" ]; then
    critical "Baseline absente — lancer baseline.sh d'abord !"
    log ""
    log "  → bash $SCRIPT_DIR/baseline.sh"
    log ""
    $INTERACTIVE && read -p "Appuyez sur Entree pour fermer..." dummy
    exit 1
fi
BASELINE_DATE=$(grep "^date=" "$BASELINE_DIR/baseline-info.txt" | cut -d= -f2)
info "Baseline du : $BASELINE_DATE"

# ==============================================================================
# 1. CLES SSH PRIVEES
# ==============================================================================
section "CLES SSH"
SHA_FILE="$BASELINE_DIR/ssh-keys.sha256"
if [ ! -f "$SHA_FILE" ]; then
    warn "Baseline cles SSH absente"
else
    CHANGED=0
    while IFS= read -r line; do
        EXPECTED_HASH=$(echo "$line" | awk '{print $1}')
        KEY_PATH=$(echo "$line" | awk '{print $2}')
        if [ ! -f "$KEY_PATH" ]; then
            critical "Cle SSH DISPARUE : $KEY_PATH"
            CHANGED=1
        else
            CURRENT_HASH=$(sha256sum "$KEY_PATH" | awk '{print $1}')
            if [ "$CURRENT_HASH" != "$EXPECTED_HASH" ]; then
                critical "Cle SSH MODIFIEE : $(basename "$KEY_PATH")"
                CHANGED=1
            fi
        fi
    done < "$SHA_FILE"
    [ $CHANGED -eq 0 ] && ok "Toutes les cles SSH intactes ($(wc -l < "$SHA_FILE") cles)"

    # Verifier les permissions
    PERM_ISSUES=0
    while IFS= read -r line; do
        KEY_PATH=$(echo "$line" | awk '{print $2}')
        if [ -f "$KEY_PATH" ]; then
            PERM=$(stat -c "%a" "$KEY_PATH")
            if [ "$PERM" != "600" ] && [ "$PERM" != "400" ]; then
                warn "Permissions incorrectes sur $(basename "$KEY_PATH") : $PERM (attendu 600)"
                PERM_ISSUES=1
            fi
        fi
    done < "$SHA_FILE"
    [ $PERM_ISSUES -eq 0 ] && ok "Permissions cles SSH correctes (600/400)"
fi

# ==============================================================================
# 2. UTILISATEURS SYSTEME
# ==============================================================================
section "UTILISATEURS SYSTEME (/etc/passwd)"
PASSWD_BASE="$BASELINE_DIR/passwd.baseline"
if [ ! -f "$PASSWD_BASE" ]; then
    warn "Baseline /etc/passwd absente"
else
    CURRENT_HASH=$(sha256sum /etc/passwd | awk '{print $1}')
    BASELINE_HASH=$(sha256sum "$PASSWD_BASE" | awk '{print $1}')
    if [ "$CURRENT_HASH" != "$BASELINE_HASH" ]; then
        warn "/etc/passwd modifie depuis la baseline"
        NEW_USERS=$(diff "$PASSWD_BASE" /etc/passwd | grep "^>" | cut -d: -f1 | sed 's/^> //')
        [ -n "$NEW_USERS" ] && critical "Nouveaux comptes detectes : $NEW_USERS"
    else
        ok "/etc/passwd inchange ($(wc -l < /etc/passwd) utilisateurs)"
    fi
fi

# ==============================================================================
# 3. SUDOERS
# ==============================================================================
section "SUDOERS (/etc/sudoers)"
SUDOERS_BASE="$BASELINE_DIR/sudoers.sha256"
if [ ! -f "$SUDOERS_BASE" ]; then
    warn "Baseline sudoers absente"
else
    CURRENT=$(sudo sha256sum /etc/sudoers 2>/dev/null | awk '{print $1}')
    STORED=$(head -1 "$SUDOERS_BASE" | awk '{print $1}')
    if [ "$CURRENT" != "$STORED" ]; then
        critical "/etc/sudoers MODIFIE depuis la baseline !"
    else
        ok "/etc/sudoers inchange"
    fi
fi

# ==============================================================================
# 4. CRONTABS
# ==============================================================================
section "CRONTABS"
CRON_BASE="$BASELINE_DIR/crontabs.baseline"
CRON_SHA="$BASELINE_DIR/crontabs.sha256"
if [ ! -f "$CRON_BASE" ]; then
    warn "Baseline crontabs absente"
else
    CRON_CURRENT="/tmp/_integrity_cron.txt"
    > "$CRON_CURRENT"
    echo "=== crontab -l ===" >> "$CRON_CURRENT"
    crontab -l 2>/dev/null >> "$CRON_CURRENT"
    echo "=== /etc/crontab ===" >> "$CRON_CURRENT"
    cat /etc/crontab 2>/dev/null >> "$CRON_CURRENT"
    echo "=== /etc/cron.d/ ===" >> "$CRON_CURRENT"
    ls -la /etc/cron.d/ 2>/dev/null >> "$CRON_CURRENT"
    CURRENT_HASH=$(sha256sum "$CRON_CURRENT" | awk '{print $1}')
    STORED_HASH=$(awk '{print $1}' "$CRON_SHA")
    if [ "$CURRENT_HASH" != "$STORED_HASH" ]; then
        warn "Crontabs modifies depuis la baseline"
        DIFF_OUT=$(diff "$CRON_BASE" "$CRON_CURRENT" | grep "^[<>]" | head -5)
        [ -n "$DIFF_OUT" ] && log "    Diff : $DIFF_OUT"
    else
        ok "Crontabs inchanges"
    fi
    rm -f "$CRON_CURRENT"
fi

# ==============================================================================
# 5. FICHIERS SUID/SGID
# ==============================================================================
section "FICHIERS SUID/SGID"
SUID_BASE="$BASELINE_DIR/suid-files.txt"
if [ ! -f "$SUID_BASE" ]; then
    warn "Baseline SUID absente"
else
    SUID_CURRENT="/tmp/_integrity_suid.txt"
    find / -type f \( -perm -4000 -o -perm -2000 \) 2>/dev/null | sort > "$SUID_CURRENT"
    NEW_SUID=$(comm -23 "$SUID_CURRENT" "$SUID_BASE")
    REMOVED_SUID=$(comm -13 "$SUID_CURRENT" "$SUID_BASE")
    if [ -n "$NEW_SUID" ]; then
        critical "Nouveaux SUID/SGID detectes :"
        echo "$NEW_SUID" | while read -r f; do log "    + $f"; done
    else
        ok "Aucun nouveau SUID/SGID"
    fi
    [ -n "$REMOVED_SUID" ] && info "SUID supprimes (normal apres MAJ) : $(echo "$REMOVED_SUID" | wc -l)"
    rm -f "$SUID_CURRENT"
fi

# ==============================================================================
# 6. BINAIRES SYSTEME
# ==============================================================================
section "BINAIRES SYSTEME (/usr/bin /usr/sbin /bin /sbin)"
BIN_BASE="$BASELINE_DIR/binaries.sha256"
if [ ! -f "$BIN_BASE" ]; then
    warn "Baseline binaires absente"
else
    MODIFIED_BINS=$(sha256sum --check "$BIN_BASE" 2>/dev/null | grep "FAILED" | head -10)
    if [ -n "$MODIFIED_BINS" ]; then
        critical "Binaires systeme modifies :"
        echo "$MODIFIED_BINS" | while read -r line; do log "    $line"; done
    else
        ok "Tous les binaires systeme intacts ($(wc -l < "$BIN_BASE"))"
    fi
fi

# ==============================================================================
# 7. MODIFICATIONS RECENTES /etc
# ==============================================================================
section "FICHIERS RECEMMENT MODIFIES (/etc — 7 jours)"
RECENT_ETC=$(find /etc -type f -mtime -7 2>/dev/null \
    | grep -v ".dpkg\|\.bak\|\.orig\|/mtab\|/resolv\|/hosts\|/adjtime\|leases\|\.cache" \
    | sort)
COUNT_ETC=$(echo "$RECENT_ETC" | grep -c . 2>/dev/null || echo 0)
if [ "$COUNT_ETC" -gt 20 ]; then
    warn "$COUNT_ETC fichiers /etc modifies en 7 jours (>20 = suspect si pas de MAJ systeme)"
    echo "$RECENT_ETC" | head -10 | while read -r f; do log "    $f"; done
elif [ "$COUNT_ETC" -gt 0 ]; then
    ok "$COUNT_ETC fichiers /etc modifies (normal)"
else
    ok "Aucune modification /etc en 7 jours"
fi

# ==============================================================================
# 8. PORTS EN ECOUTE
# ==============================================================================
section "PORTS EN ECOUTE"
PORTS_BASE="$BASELINE_DIR/listening-ports.baseline"
PORTS_CURRENT=$(ss -tlnp 2>/dev/null)
LISTEN_COUNT=$(echo "$PORTS_CURRENT" | grep -c LISTEN || echo 0)
if [ ! -f "$PORTS_BASE" ]; then
    warn "Baseline ports absente"
else
    NEW_PORTS=$(comm -23 \
        <(echo "$PORTS_CURRENT" | grep LISTEN | awk '{print $4}' | sort) \
        <(grep LISTEN "$PORTS_BASE" | awk '{print $4}' | sort))
    if [ -n "$NEW_PORTS" ]; then
        warn "Nouveaux ports en ecoute depuis la baseline :"
        echo "$NEW_PORTS" | while read -r p; do log "    + $p"; done
    else
        ok "$LISTEN_COUNT ports en ecoute — aucun nouveau"
    fi
fi

# ==============================================================================
# 9. CONNEXIONS SORTANTES
# ==============================================================================
section "CONNEXIONS SORTANTES ACTIVES"
EXT_CONNS=$(ss -tnp state established 2>/dev/null \
    | grep -v "$IGNORE_NETS" \
    | grep -v "Local Address" \
    | head -20)
CONN_COUNT=$(echo "$EXT_CONNS" | grep -c . 2>/dev/null || echo 0)
if [ "$CONN_COUNT" -gt 0 ]; then
    info "$CONN_COUNT connexion(s) externe(s) active(s) :"
    echo "$EXT_CONNS" | while read -r line; do info "    $line"; done
else
    ok "Aucune connexion sortante externe active"
fi

# ==============================================================================
# 10. PACKAGES RECENTS
# ==============================================================================
section "PACKAGES INSTALLES RECEMMENT (7 jours)"
RECENT_PKG=$(grep " install " /var/log/dpkg.log 2>/dev/null \
    | awk -v cutoff="$(date -d '7 days ago' '+%Y-%m-%d')" '$1 >= cutoff' \
    | awk '{print $4}' | sort -u | head -20)
PKG_COUNT=$(echo "$RECENT_PKG" | grep -c '[^[:space:]]' 2>/dev/null); PKG_COUNT=${PKG_COUNT:-0}
if [ "$PKG_COUNT" -gt 0 ]; then
    info "$PKG_COUNT package(s) installe(s) ces 7 derniers jours :"
    echo "$RECENT_PKG" | while read -r p; do info "    + $p"; done
else
    ok "Aucun package installe en 7 jours"
fi

# ==============================================================================
# 11. PROCESSUS SUSPECTS
# ==============================================================================
section "PROCESSUS SUSPECTS"
SUSPECT_PROCS=$(ps aux 2>/dev/null | grep -iE "xmrig|minerd|cryptonight|kinsing|masscan|zmap|nmap|nc -l|bash -i|python.*-c.*import|perl.*socket" | grep -v grep)
if [ -n "$SUSPECT_PROCS" ]; then
    critical "Processus suspects detectes :"
    echo "$SUSPECT_PROCS" | while read -r line; do log "    $line"; done
else
    ok "Aucun processus suspect connu"
fi

# ==============================================================================
# 12. ESPACE DISQUE
# ==============================================================================
section "ESPACE DISQUE"
while IFS= read -r line; do
    USAGE=$(echo "$line" | awk '{print $5}' | tr -d '%')
    MOUNT=$(echo "$line" | awk '{print $6}')
    if [ "$USAGE" -ge 90 ] 2>/dev/null; then
        critical "Disque $MOUNT a ${USAGE}% — critique !"
    elif [ "$USAGE" -ge 80 ] 2>/dev/null; then
        warn "Disque $MOUNT a ${USAGE}% — attention"
    else
        ok "Disque $MOUNT : ${USAGE}%"
    fi
done < <(df -h | grep -vE "tmpfs|udev|Filesystem" | awk 'NF>=5')

# ==============================================================================
# 13. RKHUNTER (optionnel)
# ==============================================================================
section "RKHUNTER (rootkits)"
RKH_LOG="$LOG_DIR/rkhunter-$(date +%Y%m%d).log"
if ! command -v rkhunter &>/dev/null; then
    info "rkhunter non installe — installez avec : sudo apt install rkhunter"
else
    info "Lancement rkhunter (peut prendre 1-2 min)..."
    sudo rkhunter --check --skip-keypress --logfile "$RKH_LOG" --cronjob 2>/dev/null
    WARN_COUNT=$(grep -c "Warning" "$RKH_LOG" 2>/dev/null || echo 0)
    # Filtrer les faux positifs connus — adaptez cette liste a votre systeme
    REAL_WARNS=$(grep "Warning" "$RKH_LOG" 2>/dev/null \
        | grep -v "SSH root access\|SSH.*configuration options\|syslog remote\|Download.*failed\|Download of\|Unable to determine" \
        | wc -l)
    if [ "$REAL_WARNS" -gt 0 ]; then
        critical "$REAL_WARNS warning(s) reel(s) rkhunter :"
        grep "Warning" "$RKH_LOG" 2>/dev/null \
            | grep -v "SSH root access\|SSH.*configuration options\|syslog remote\|Download.*failed\|Download of\|Unable to determine" \
            | head -5 | while read -r line; do log "    $line"; done
    else
        ok "rkhunter : 0 warning reel ($WARN_COUNT faux positifs filtres)"
    fi
fi

# ==============================================================================
# BILAN FINAL
# ==============================================================================
log ""
log "╔════════════════════════════════════════════════════════════════════════════╗"
log "║                          BILAN INTEGRITE                                  ║"
log "╚════════════════════════════════════════════════════════════════════════════╝"
log ""

if [ $CRITICALS -gt 0 ]; then
    log "  ${RED}🚨 $CRITICALS ALERTE(S) CRITIQUE(S) — ACTION REQUISE${NC}"
elif [ $WARNINGS -gt 0 ]; then
    log "  ${YELLOW}⚠️  $WARNINGS avertissement(s) — a verifier${NC}"
else
    log "  ${GREEN}✅ Integrite OK — aucune anomalie detectee${NC}"
fi

log ""
log "  Critiques : $CRITICALS"
log "  Warnings  : $WARNINGS"
log "  Log       : $LOG_FILE"
log ""

$INTERACTIVE && read -p "Appuyez sur Entree pour fermer..." dummy
exit $CRITICALS
