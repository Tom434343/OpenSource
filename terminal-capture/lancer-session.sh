#!/bin/bash
# ============================================================
# lancer-session.sh — Session Claude Code par projet
# Terminal Capture v3
#
# Usage : ./lancer-session.sh [NOM_PROJET]
# Sans argument : fenetre zenity avec liste des projets
# Avec argument : lancement direct du projet
# ============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONF_FILE="$SCRIPT_DIR/projets.conf"

# --- Lire projets.conf ---
declare -A PROJETS
NOMS_PROJETS=()

if [ ! -f "$CONF_FILE" ]; then
    echo "Erreur : fichier projets.conf introuvable dans $SCRIPT_DIR"
    echo "  Copiez projets.conf.example vers projets.conf et editez-le."
    read -p "Appuyez sur Entree pour fermer..." dummy
    exit 1
fi

while IFS='=' read -r nom chemin; do
    [[ -z "$nom" || "$nom" =~ ^[[:space:]]*# ]] && continue
    nom=$(echo "$nom" | xargs)
    chemin=$(echo "$chemin" | xargs)
    PROJETS["$nom"]="$chemin"
    NOMS_PROJETS+=("$nom")
done < "$CONF_FILE"

# --- Selection du projet ---
PROJET_NOM="$1"

if [ -z "$PROJET_NOM" ]; then
    ZENITY_LIST=""
    for nom in "${NOMS_PROJETS[@]}"; do
        ZENITY_LIST="$ZENITY_LIST $nom"
    done

    PROJET_NOM=$(zenity --list \
        --title="Terminal Capture — Choix du projet" \
        --text="Selectionnez un projet pour demarrer Claude Code :" \
        --column="Projet" \
        $ZENITY_LIST \
        --width=400 --height=500 2>/dev/null) || true

    if [ -z "$PROJET_NOM" ]; then
        echo "Aucun projet selectionne. Annulation."
        read -p "Appuyez sur Entree pour fermer..." dummy
        exit 0
    fi
fi

# --- Verifier que le projet existe ---
PROJET_DIR="${PROJETS[$PROJET_NOM]}"

if [ -z "$PROJET_DIR" ]; then
    echo "Erreur : projet '$PROJET_NOM' non trouve dans projets.conf"
    echo ""
    echo "Projets disponibles :"
    for nom in "${NOMS_PROJETS[@]}"; do
        echo "  - $nom"
    done
    read -p "Appuyez sur Entree pour fermer..." dummy
    exit 1
fi

if [ ! -d "$PROJET_DIR" ]; then
    echo "Erreur : le dossier $PROJET_DIR n'existe pas."
    read -p "Appuyez sur Entree pour fermer..." dummy
    exit 1
fi

# --- Creer le dossier Terminal-Capture ---
TC_DIR="$PROJET_DIR/Documentation/Terminal-Capture"
mkdir -p "$TC_DIR"

# --- Horodatage ---
SESSION_TS=$(date +%Y%m%d_%H%M%S)
CONV_FILE="$TC_DIR/conversation_${SESSION_TS}.md"
START_EPOCH=$(date +%s)

echo ""
echo "=================================================="
echo "  Projet  : $PROJET_NOM"
echo "  Dossier : $PROJET_DIR"
echo "  Session : $SESSION_TS"
echo "=================================================="
echo ""
echo "Demarrage de Claude Code..."
echo "Tapez '/exit' ou Ctrl+D pour terminer la session."
echo ""

# --- Lancer Claude Code ---
(cd "$PROJET_DIR" && claude) || true

sleep 2

echo ""
echo "Session terminee. Generation du log et du journal..."
echo ""

# --- Exporter la conversation ---
python3 "$SCRIPT_DIR/exporter_conversation.py" \
    --projet "$PROJET_NOM" \
    --projet-dir "$PROJET_DIR" \
    --output "$CONV_FILE" \
    --start-epoch "$START_EPOCH"

echo ""
echo "=================================================="
echo "  Transcription : conversation_${SESSION_TS}.md"
echo "  Journal mis a jour : JOURNAL.md"
echo "  Dossier : $TC_DIR"
echo "=================================================="
echo ""

read -p "Appuyez sur Entree pour fermer..." dummy
