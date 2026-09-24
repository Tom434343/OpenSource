# Keys Manager

**Author** : Thomas ROUGER ([Digital Consulting & Training](https://www.digitalct.io))

Chiffrement/déchiffrement de clés sensibles (SSH, WireGuard, GnuPG, rclone) avec OpenSSL AES-256-CBC.

Protection contre le vol physique : quand la machine est éteinte ou verrouillée, les clés sont chiffrées sur le disque. Au démarrage, un mot de passe les déchiffre et démarre WireGuard.

## Ce que ça fait

```
BOOT (déchiffrement) :
  ssh.enc       → ~/.ssh/           (clés SSH restaurées)
  wireguard.enc → /etc/wireguard/   (config WG restaurée + wg-quick up)
  gnupg.enc     → ~/.gnupg/         (optionnel)
  rclone.enc    → ~/.config/rclone/ (optionnel)

SHUTDOWN (chiffrement) :
  ~/.ssh/           → ssh.enc       (chiffre AES-256-CBC)
  /etc/wireguard/   → wireguard.enc (wg-quick down + chiffre)
  ~/.gnupg/         → gnupg.enc     (optionnel)
  ~/.config/rclone/ → rclone.enc    (optionnel)
  + suppression des fichiers en clair
```

## Prérequis

- Linux
- OpenSSL (`apt install openssl`)
- WireGuard (`apt install wireguard`) si vous l'utilisez
- sudo (pour /etc/wireguard)

## Installation

```bash
# 1. Copier le script
cp keys-manager.sh ~/keys-manager.sh
chmod +x ~/keys-manager.sh

# 2. Premier chiffrement (vos clés doivent être en place)
bash ~/keys-manager.sh
# → Choisir "o" pour chiffrer, entrer un mot de passe

# 3. (Optionnel) Autostart au login — fichier .desktop
cp keys-manager.desktop ~/.config/autostart/
```

## Usage

```bash
# Lancer le gestionnaire
bash keys-manager.sh

# Le script détecte automatiquement l'état :
#   Clés chiffrées → demande le mot de passe → déchiffre
#   Clés en clair  → demande confirmation   → chiffre
```

## Configuration

Éditez les variables en haut du script pour adapter à votre setup :

```bash
# Fichiers chiffrés
SSH_ENC="$HOME/ssh.enc"
WG_ENC="$HOME/wireguard.enc"

# Dossiers en clair
SSH_DIR="$HOME/.ssh"
WG_DIR="/etc/wireguard"

# Sous-dossier pour détecter l'état (doit contenir les clés privées)
SSH_KEYS_SUBDIR="$SSH_DIR/restricted"
```

Si vous n'utilisez pas WireGuard, GnuPG ou rclone, le script les ignore automatiquement (il ne chiffre que ce qui existe).

## Autostart au login (GNOME)

```ini
# ~/.config/autostart/keys-manager.desktop
[Desktop Entry]
Type=Application
Name=Keys Manager
Exec=gnome-terminal -- bash /chemin/vers/keys-manager.sh
Hidden=false
X-GNOME-Autostart-enabled=true
```

## Sécurité

- **Algorithme** : AES-256-CBC avec dérivation PBKDF2
- **Mot de passe** : interactif uniquement (jamais stocké)
- **Fichiers temporaires** : /dev/shm (RAM), supprimés immédiatement après usage — jamais écrits sur disque
- **Modèle de menace** : protège contre le vol physique de la machine. Ne protège PAS si l'attaquant connaît le mot de passe.
- **Sauvegarde** : gardez une copie des .enc sur un support externe (USB chiffré)
