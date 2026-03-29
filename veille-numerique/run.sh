#!/bin/bash
# VeilleNumerique - Lanceur
# Usage : bash run.sh [--conteneur ID] [--test] [--no-email]

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

if [ ! -f "${SCRIPT_DIR}/config.env" ]; then
    echo "ERREUR : config.env introuvable. Copiez config.env.example vers config.env et remplissez-le."
    [ -t 0 ] && read -p "Appuyez sur Entree pour fermer..." dummy
    exit 1
fi

source "${SCRIPT_DIR}/config.env"
cd "${SCRIPT_DIR}"
python3 "${SCRIPT_DIR}/veille.py" "$@"

[ -t 0 ] && read -p "Appuyez sur Entree pour fermer..." dummy
