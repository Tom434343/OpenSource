#!/bin/bash
# keys-manager.sh — Chiffrement/Dechiffrement cles SSH + WireGuard + GnuPG + rclone
# Utilise OpenSSL AES-256-CBC avec PBKDF2.
#
# Au boot  : dechiffre les archives .enc → restaure les cles → demarre WireGuard
# Au shutdown : chiffre les cles → supprime les fichiers en clair
#
# Usage : bash keys-manager.sh

# ─── CONFIGURATION ──────────────────────────────────────────────────
# Fichiers chiffres (stockes dans $HOME)
SSH_ENC="$HOME/ssh.enc"
WG_ENC="$HOME/wireguard.enc"
GNUPG_ENC="$HOME/gnupg.enc"
RCLONE_ENC="$HOME/rclone.enc"

# Dossiers en clair
SSH_DIR="$HOME/.ssh"
WG_DIR="/etc/wireguard"
GNUPG_DIR="$HOME/.gnupg"
RCLONE_DIR="$HOME/.config/rclone"

# Sous-dossier contenant les cles privees SSH (pour detecter l'etat)
# Adaptez si vous n'utilisez pas de sous-dossier
SSH_KEYS_SUBDIR="$SSH_DIR/restricted"

# ─── COULEURS ───────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m'

# ─── FONCTIONS ──────────────────────────────────────────────────────

decrypt_archive() {
    local enc_file="$1"
    local label="$2"
    local restore_perms="$3"  # optionnel : chemin a chmod 700

    if [ ! -f "$enc_file" ]; then
        echo -e "  ${YELLOW}⚠ ${label} : archive non trouvee (${enc_file})${NC}"
        return 1
    fi

    echo -e "  ${BLUE}Restauration ${label}...${NC}"
    echo "$PASS" | sudo openssl enc -d -aes-256-cbc -pbkdf2 -pass stdin \
        -in "$enc_file" -out /tmp/_restore.tar.gz 2>/dev/null

    if [ $? -ne 0 ]; then
        echo -e "  ${RED}✗ Echec dechiffrement ${label}${NC}"
        sudo rm -f /tmp/_restore.tar.gz
        return 1
    fi

    sudo tar xzf /tmp/_restore.tar.gz -C /
    sudo rm -f /tmp/_restore.tar.gz

    if [ -n "$restore_perms" ] && [ -d "$restore_perms" ]; then
        chmod 700 "$restore_perms"
    fi

    echo -e "  ${GREEN}✓ ${label} restaure${NC}"
    return 0
}

encrypt_directory() {
    local dir="$1"
    local enc_file="$2"
    local label="$3"
    local strip_prefix="$4"  # chemin relatif dans le tar (ex: home/user/.ssh)

    if [ ! -d "$dir" ]; then
        return 0
    fi

    echo -e "  ${BLUE}Chiffrement ${label}...${NC}"

    # Calculer le chemin relatif depuis /
    local rel_path="${dir#/}"
    tar czf /tmp/_backup.tar.gz -C / "$rel_path" 2>/dev/null
    echo "$PASS" | sudo openssl enc -aes-256-cbc -pbkdf2 -pass stdin \
        -in /tmp/_backup.tar.gz -out "$enc_file"
    rm -f /tmp/_backup.tar.gz

    echo -e "  ${GREEN}✓ ${label} chiffre${NC}"
}

# ─── MAIN ───────────────────────────────────────────────────────────

clear
echo -e "${BOLD}╔══════════════════════════════════════════╗${NC}"
echo -e "${BOLD}║       GESTIONNAIRE DE CLES CHIFFREES     ║${NC}"
echo -e "${BOLD}╚══════════════════════════════════════════╝${NC}"
echo ""

# Detection etat : si le dossier de cles privees existe → cles en clair
if [ -d "$SSH_KEYS_SUBDIR" ]; then
    STATE="CLAIR"
    echo -e "  Etat actuel : ${GREEN}● CLES EN CLAIR${NC}"
else
    STATE="CHIFFRE"
    echo -e "  Etat actuel : ${RED}● CLES CHIFFREES${NC}"
fi

echo ""

# ─── DECHIFFREMENT ──────────────────────────────────────────────────
if [ "$STATE" = "CHIFFRE" ]; then

    echo -e "  ${YELLOW}Entrez le mot de passe pour dechiffrer :${NC}"
    read -s -p "  Mot de passe : " PASS
    echo ""

    # Verifier le mot de passe sur ssh.enc
    echo "$PASS" | sudo openssl enc -d -aes-256-cbc -pbkdf2 -pass stdin \
        -in "$SSH_ENC" -out /tmp/_verify.tar.gz 2>/dev/null
    if [ $? -ne 0 ]; then
        echo -e "\n  ${RED}✗ Mot de passe incorrect${NC}"
        sudo rm -f /tmp/_verify.tar.gz
        read -p "  Appuyez sur Entree pour fermer..." dummy
        exit 1
    fi
    # Le fichier de verification est aussi le fichier SSH — on le restaure
    sudo tar xzf /tmp/_verify.tar.gz -C /
    chmod 700 "$SSH_DIR"
    [ -d "$SSH_KEYS_SUBDIR" ] && chmod 700 "$SSH_KEYS_SUBDIR"
    find "$SSH_KEYS_SUBDIR" -type f -name "*_key" -exec chmod 600 {} \; 2>/dev/null
    find "$SSH_KEYS_SUBDIR" -type f -name "*.pub" -exec chmod 644 {} \; 2>/dev/null
    sudo rm -f /tmp/_verify.tar.gz
    echo -e "  ${GREEN}✓ SSH restaure${NC}"

    # WireGuard
    decrypt_archive "$WG_ENC" "WireGuard"
    echo -e "  ${BLUE}Demarrage WireGuard...${NC}"
    sudo wg-quick up wg0 2>/dev/null \
        && echo -e "  ${GREEN}✓ WireGuard actif${NC}" \
        || echo -e "  ${YELLOW}⚠ WireGuard deja actif ou erreur${NC}"

    # GnuPG (optionnel)
    decrypt_archive "$GNUPG_ENC" "GnuPG" "$GNUPG_DIR"

    # rclone (optionnel)
    decrypt_archive "$RCLONE_ENC" "rclone"

    echo -e "\n  ${GREEN}✓ Cles dechiffrees — acces operationnel${NC}"

# ─── CHIFFREMENT ────────────────────────────────────────────────────
else

    echo -e "  Voulez-vous chiffrer et verrouiller les cles ? ${BOLD}[o/N]${NC}"
    read -p "  Choix : " CONFIRM
    if [[ "$CONFIRM" != "o" && "$CONFIRM" != "O" ]]; then
        echo -e "\n  Annule."
        read -p "  Appuyez sur Entree pour fermer..." dummy
        exit 0
    fi

    echo -e "\n  ${YELLOW}Entrez le mot de passe pour chiffrer :${NC}"
    read -s -p "  Mot de passe : " PASS
    echo ""
    read -s -p "  Confirmer    : " PASS2
    echo ""

    if [ "$PASS" != "$PASS2" ]; then
        echo -e "\n  ${RED}✗ Mots de passe differents${NC}"
        read -p "  Appuyez sur Entree pour fermer..." dummy
        exit 1
    fi

    # Arreter WireGuard
    sudo wg-quick down wg0 2>/dev/null

    # Chiffrer chaque composant
    encrypt_directory "$SSH_DIR"    "$SSH_ENC"    "SSH"
    encrypt_directory "$WG_DIR"     "$WG_ENC"     "WireGuard"
    encrypt_directory "$GNUPG_DIR"  "$GNUPG_ENC"  "GnuPG"
    encrypt_directory "$RCLONE_DIR" "$RCLONE_ENC" "rclone"

    # Supprimer cles en clair
    rm -rf "$SSH_DIR"
    sudo rm -rf "$WG_DIR"
    rm -rf "$GNUPG_DIR"
    rm -rf "$RCLONE_DIR"

    echo -e "\n  ${GREEN}✓ Cles chiffrees — acces verrouille${NC}"

fi

echo ""
read -p "  Appuyez sur Entree pour fermer..." dummy
