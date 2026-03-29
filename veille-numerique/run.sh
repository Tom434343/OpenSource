#!/bin/bash
# VeilleNumerique - Lanceur
# Usage : bash run.sh [--conteneur ID] [--test] [--no-email]

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "${SCRIPT_DIR}/config.env"
cd "${SCRIPT_DIR}"
python3 "${SCRIPT_DIR}/veille.py" "$@"

read -p "Appuyez sur Entree pour fermer..." dummy
