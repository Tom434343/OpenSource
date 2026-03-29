#!/bin/bash

#==============================================================================
# LYNIS FLEET ORCHESTRATOR — Audit securite parallele multi-serveurs
#==============================================================================
# Lance Lynis sur tous les serveurs en parallele (1 SSH par serveur).
# Consolide les scores et suggestions dans un rapport JSON + terminal.
# Usage : bash lynis-fleet.sh
# Config : servers.conf (un serveur par ligne)
#==============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="$SCRIPT_DIR/servers.conf"
REPORT_DIR="$SCRIPT_DIR/reports"
DATE=$(date '+%Y-%m-%d')
REPORT_FILE="$REPORT_DIR/lynis_${DATE}.json"
mkdir -p "$REPORT_DIR"

# Couleurs
GREEN='\033[0;32m'; RED='\033[0;31m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'

# Temporaire
TMP_DIR="/tmp/lynis-fleet-$$"
mkdir -p "$TMP_DIR"
trap "rm -rf $TMP_DIR" EXIT

# ─── Lire la config ─────────────────────────────────────────────────
if [ ! -f "$CONFIG_FILE" ]; then
    echo -e "${RED}ERREUR : $CONFIG_FILE introuvable${NC}"
    echo "  Copiez servers.conf.example vers servers.conf et editez-le."
    read -p "Appuyez sur Entree pour fermer..." dummy
    exit 1
fi

# Charger les serveurs (ignorer commentaires et lignes vides)
declare -a SERVERS
declare -a NAMES
declare -a KEYS
IDX=0

while IFS='|' read -r name target key; do
    # Ignorer commentaires et lignes vides
    [[ "$name" =~ ^[[:space:]]*# ]] && continue
    [[ -z "$name" ]] && continue
    name=$(echo "$name" | xargs)  # trim
    target=$(echo "$target" | xargs)
    key=$(echo "$key" | xargs)
    NAMES[$IDX]="$name"
    SERVERS[$IDX]="$target"
    KEYS[$IDX]="$key"
    IDX=$((IDX + 1))
done < "$CONFIG_FILE"

SERVER_COUNT=${#NAMES[@]}

if [ $SERVER_COUNT -eq 0 ]; then
    echo -e "${RED}Aucun serveur configure dans servers.conf${NC}"
    read -p "Appuyez sur Entree pour fermer..." dummy
    exit 1
fi

# ─── Entete ──────────────────────────────────────────────────────────
echo "╔════════════════════════════════════════════════════════════════════════════╗"
echo "║            LYNIS FLEET ORCHESTRATOR — AUDIT PARALLELE                      ║"
echo "╚════════════════════════════════════════════════════════════════════════════╝"
echo ""
echo "  $SERVER_COUNT serveur(s) a auditer"
echo "  1 connexion SSH par serveur = SAFE Fail2Ban"
echo ""

for i in $(seq 0 $((SERVER_COUNT - 1))); do
    echo "   🔄 ${NAMES[$i]}: Audit en cours..."
done

echo ""
echo "  Attente fin des audits (~2-3 minutes)..."
echo ""

START_TIME=$(date +%s)

# ─── Lancement parallele ────────────────────────────────────────────
PIDS=()

for i in $(seq 0 $((SERVER_COUNT - 1))); do
    name="${NAMES[$i]}"
    target="${SERVERS[$i]}"
    key="${KEYS[$i]}"

    (
        if [ -z "$target" ]; then
            # Audit LOCAL
            sudo lynis audit system --quick --no-colors > /dev/null 2>&1
            SCORE=$(sudo grep "hardening_index=" /var/log/lynis-report.dat 2>/dev/null | cut -d= -f2)
            sudo grep "^suggestion\[\]=" /var/log/lynis-report.dat 2>/dev/null > "$TMP_DIR/${name}.suggestions"
            echo "$SCORE" > "$TMP_DIR/${name}.score"
        else
            # Audit DISTANT via SSH
            SSH_OPTS="-o ConnectTimeout=10 -o StrictHostKeyChecking=no -o BatchMode=yes"
            [ -n "$key" ] && SSH_OPTS="-i $key $SSH_OPTS"

            ssh $SSH_OPTS "$target" "
                sudo /usr/sbin/lynis audit system --quick --no-colors > /dev/null 2>&1
                echo '===SCORE==='
                sudo grep 'hardening_index=' /var/log/lynis-report.dat 2>/dev/null | cut -d= -f2
                echo '===SUGGESTIONS==='
                sudo grep '^suggestion\[\]=' /var/log/lynis-report.dat 2>/dev/null
            " 2>/dev/null > "$TMP_DIR/${name}.raw"

            SCORE=$(sed -n '/===SCORE===/,/===SUGGESTIONS===/p' "$TMP_DIR/${name}.raw" | grep -v "===" | head -1)
            sed -n '/===SUGGESTIONS===/,$p' "$TMP_DIR/${name}.raw" | grep -v "===" > "$TMP_DIR/${name}.suggestions"
            echo "$SCORE" > "$TMP_DIR/${name}.score"
        fi

        echo "   ✅ ${name}: Termine (Score: $(cat "$TMP_DIR/${name}.score" 2>/dev/null | tr -d '[:space:]')/100)"
    ) &
    PIDS+=($!)
done

# Attendre tous les audits
wait "${PIDS[@]}"

END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

echo ""
echo "  Tous les audits termines en ${DURATION} secondes"
echo ""

# ─── Scores ──────────────────────────────────────────────────────────
echo "╔════════════════════════════════════════════════════════════════════════════╗"
echo "║                        SCORES HARDENING                                    ║"
echo "╚════════════════════════════════════════════════════════════════════════════╝"
echo ""

TOTAL=0
COUNT=0
SCORES_JSON=""

for i in $(seq 0 $((SERVER_COUNT - 1))); do
    name="${NAMES[$i]}"
    score=$(cat "$TMP_DIR/${name}.score" 2>/dev/null | tr -d '[:space:]')

    if [[ -n "$score" && "$score" =~ ^[0-9]+$ ]]; then
        TOTAL=$((TOTAL + score))
        COUNT=$((COUNT + 1))
        # Couleur selon score
        if [ "$score" -ge 90 ]; then
            COLOR=$GREEN
        elif [ "$score" -ge 70 ]; then
            COLOR=$YELLOW
        else
            COLOR=$RED
        fi
        printf "   ${COLOR}${BOLD}%-15s %s/100${NC}\n" "$name" "$score"
    else
        printf "   ${RED}%-15s ??/100${NC}\n" "$name"
        score=0
    fi

    [ -n "$SCORES_JSON" ] && SCORES_JSON="${SCORES_JSON},"
    SCORES_JSON="${SCORES_JSON}{\"name\":\"$name\",\"score\":${score:-0}}"
done

AVERAGE=0
[ $COUNT -gt 0 ] && AVERAGE=$((TOTAL / COUNT))
echo ""
printf "   ${GREEN}${BOLD}%-15s %s/100${NC}\n" "MOYENNE" "$AVERAGE"
echo ""

# ─── Suggestions consolidees ────────────────────────────────────────
echo "╔════════════════════════════════════════════════════════════════════════════╗"
echo "║                     SUGGESTIONS (Quick Wins en premier)                    ║"
echo "╚════════════════════════════════════════════════════════════════════════════╝"
echo ""

declare -A SUGGESTIONS_MAP
declare -A SUGGESTIONS_DESC
declare -A COUNT_MAP

for i in $(seq 0 $((SERVER_COUNT - 1))); do
    name="${NAMES[$i]}"
    [ ! -f "$TMP_DIR/${name}.suggestions" ] && continue

    while IFS= read -r line; do
        ID=$(echo "$line" | sed 's/suggestion\[\]=//' | cut -d'|' -f1)
        DESC=$(echo "$line" | cut -d'|' -f2)

        if [[ -n "$ID" && "$ID" != "LYNIS" ]]; then
            if [[ -z "${SUGGESTIONS_MAP[$ID]}" ]]; then
                SUGGESTIONS_MAP[$ID]="$name"
            elif [[ ! "${SUGGESTIONS_MAP[$ID]}" =~ $name ]]; then
                SUGGESTIONS_MAP[$ID]="${SUGGESTIONS_MAP[$ID]}, $name"
            fi
            [ -z "${SUGGESTIONS_DESC[$ID]}" ] && SUGGESTIONS_DESC[$ID]="$DESC"
        fi
    done < "$TMP_DIR/${name}.suggestions"
done

for ID in "${!SUGGESTIONS_MAP[@]}"; do
    servers="${SUGGESTIONS_MAP[$ID]}"
    COUNT_MAP[$ID]=$(echo "$servers" | tr ',' '\n' | wc -l)
done

DISPLAYED=0
for count in $(seq $SERVER_COUNT -1 1); do
    for ID in "${!COUNT_MAP[@]}"; do
        if [[ "${COUNT_MAP[$ID]}" -eq $count ]]; then
            servers="${SUGGESTIONS_MAP[$ID]}"
            desc="${SUGGESTIONS_DESC[$ID]}"

            if [[ $count -ge $((SERVER_COUNT - 1)) ]]; then
                COLOR=$GREEN; PRIORITY="[QUICK WIN - $count serveur(s)]"
            elif [[ $count -ge 2 ]]; then
                COLOR=$YELLOW; PRIORITY="[$count serveur(s)]"
            else
                COLOR=$CYAN; PRIORITY="[1 serveur - specifique]"
            fi

            echo -e "   ${COLOR}${PRIORITY}${NC} ${BOLD}$ID${NC}"
            echo "              $desc"
            echo -e "              Sur: ${BOLD}$servers${NC}"
            echo ""
            DISPLAYED=$((DISPLAYED + 1))
        fi
    done
done

[ $DISPLAYED -eq 0 ] && echo "   Aucune suggestion — Fleet parfaitement securisee !"
echo ""

# ─── Resume ──────────────────────────────────────────────────────────
echo "╔════════════════════════════════════════════════════════════════════════════╗"
echo "║                           RESUME                                           ║"
echo "╚════════════════════════════════════════════════════════════════════════════╝"
echo ""
echo "   Duree totale      : ${DURATION} secondes ($SERVER_COUNT serveurs en parallele)"
echo "   Score moyen       : ${AVERAGE}/100"
echo "   Suggestions       : ${#SUGGESTIONS_MAP[@]} uniques"
echo ""

# ─── JSON ────────────────────────────────────────────────────────────
SUGGESTIONS_JSON=""
for ID in "${!SUGGESTIONS_MAP[@]}"; do
    servers_raw="${SUGGESTIONS_MAP[$ID]}"
    desc="${SUGGESTIONS_DESC[$ID]}"
    count="${COUNT_MAP[$ID]}"
    desc_escaped=$(echo "$desc" | sed 's/"/\\"/g')
    servers_arr=$(echo "$servers_raw" | sed 's/, /","/g')
    [ -n "$SUGGESTIONS_JSON" ] && SUGGESTIONS_JSON="${SUGGESTIONS_JSON},"
    SUGGESTIONS_JSON="${SUGGESTIONS_JSON}{\"id\":\"$ID\",\"description\":\"$desc_escaped\",\"servers\":[\"$servers_arr\"],\"count\":$count}"
done

cat > "$REPORT_FILE" << JSONEOF
{
  "date": "$DATE",
  "generated_at": "$(date '+%Y-%m-%dT%H:%M:%S')",
  "duration_seconds": $DURATION,
  "summary": {
    "average_score": $AVERAGE,
    "total_suggestions": ${#SUGGESTIONS_MAP[@]},
    "servers_count": $COUNT
  },
  "servers": [$SCORES_JSON],
  "suggestions": [$SUGGESTIONS_JSON]
}
JSONEOF

echo "  Rapport JSON : $REPORT_FILE"
echo ""

read -p "Appuyez sur Entree pour fermer..." dummy
