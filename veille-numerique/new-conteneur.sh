#!/bin/bash
# Cree un nouveau conteneur de veille
# Usage : bash new-conteneur.sh <id> [nom]

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CONTENEURS_DIR="${SCRIPT_DIR}/conteneurs"

if [ -z "$1" ]; then
    echo "Usage : bash new-conteneur.sh <id> [nom]"
    echo "  id  : identifiant (ex: geopolitique-marches)"
    echo "  nom : nom affiche (ex: Geopolitique & Marches)"
    echo ""
    echo "Conteneurs existants :"
    for d in "${CONTENEURS_DIR}"/*/; do
        if [ -f "${d}config.json" ]; then
            name=$(python3 -c "import json; print(json.load(open('${d}config.json'))['name'])" 2>/dev/null || echo "?")
            echo "  - $(basename "$d") → ${name}"
        fi
    done
    read -p "Appuyez sur Entree pour fermer..." dummy
    exit 1
fi

ID="$1"
NOM="${2:-$1}"
TARGET="${CONTENEURS_DIR}/${ID}"

if [ -d "$TARGET" ]; then
    echo "ERREUR : le conteneur '${ID}' existe deja dans ${TARGET}"
    read -p "Appuyez sur Entree pour fermer..." dummy
    exit 1
fi

# Creer arborescence
mkdir -p "${TARGET}/syntheses/"{jour,semaine,mois,trimestre,annee,cumul}

# Creer config.json template
cat > "${TARGET}/config.json" << ENDJSON
{
  "name": "${NOM}",
  "id": "${ID}",
  "enabled": true,
  "days_back": 1,
  "sources": [
    {"name": "Source 1", "url": "https://example.com/rss.xml", "lang": "fr"},
    {"name": "Source 2", "url": "https://example.com/feed/", "lang": "en"}
  ],
  "source_colors": {
    "Source 1": "#7c3aed",
    "Source 2": "#1d4ed8"
  },
  "keywords_alert": [
    "mot-cle-1", "mot-cle-2", "mot-cle-3"
  ],
  "analyse_prompt": "Tu es un expert en [DOMAINE]. Analyse les articles fournis de maniere factuelle.",
  "email_subject_prefix": "🔍 Veille [${NOM}]"
}
ENDJSON

# Creer seen_articles vide
echo "[]" > "${TARGET}/seen_articles.json"

echo "Conteneur '${NOM}' cree dans ${TARGET}"
echo ""
echo "Structure :"
find "${TARGET}" -type f -o -type d | sort | sed "s|${CONTENEURS_DIR}/||"
echo ""
echo "→ Editez ${TARGET}/config.json pour configurer les sources RSS et mots-cles."

read -p "Appuyez sur Entree pour fermer..." dummy
