#!/bin/bash
# Installe les crons VeilleNumerique
# Adaptez les conteneurs et horaires a vos besoins.
# Usage : bash cron-install.sh

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CONTENEURS_DIR="${SCRIPT_DIR}/conteneurs"

# Nettoyer les anciens crons VeilleNumerique
CURRENT=$(crontab -l 2>/dev/null | grep -v "VeilleNumerique" | grep -v "run.sh.*--conteneur")

# Decouvrir les conteneurs et generer les crons
NEW_CRONS=""
HOUR=22
MIN=0

echo "Conteneurs detectes :"
for d in "${CONTENEURS_DIR}"/*/; do
    if [ -f "${d}config.json" ]; then
        ID=$(python3 -c "import json; print(json.load(open('${d}config.json'))['id'])" 2>/dev/null)
        NAME=$(python3 -c "import json; print(json.load(open('${d}config.json'))['name'])" 2>/dev/null)
        if [ -n "$ID" ]; then
            CRON_LINE="${MIN} ${HOUR} * * * bash \"${SCRIPT_DIR}/run.sh\" --conteneur ${ID} >> \"${SCRIPT_DIR}/veille.log\" 2>&1"
            NEW_CRONS="${NEW_CRONS}${CRON_LINE}\n"
            echo "  ${NAME} (${ID}) → tous les jours ${HOUR}h$(printf '%02d' ${MIN})"
            MIN=$((MIN + 15))
            if [ $MIN -ge 60 ]; then
                MIN=0
                HOUR=$((HOUR + 1))
            fi
        fi
    fi
done

# Installer
echo -e "${CURRENT}\n${NEW_CRONS}" | crontab -

echo ""
echo "Crons installes :"
crontab -l | grep "run.sh"

read -p "Appuyez sur Entree pour fermer..." dummy
