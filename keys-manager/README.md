# Keys Manager

**Author** : Thomas ROUGER ([Digital Consulting & Training](https://www.digitalct.io))

Chiffrement/dechiffrement de cles sensibles (SSH, WireGuard, GnuPG, rclone) avec OpenSSL AES-256-CBC.

Protection contre le vol physique : quand la machine est eteinte ou verrouillee, les cles sont chiffrees sur le disque. Au demarrage, un mot de passe les dechiffre et demarre WireGuard.

## Ce que ca fait

```
BOOT (dechiffrement) :
  ssh.enc       → ~/.ssh/           (cles SSH restaurees)
  wireguard.enc → /etc/wireguard/   (config WG restauree + wg-quick up)
  gnupg.enc     → ~/.gnupg/         (optionnel)
  rclone.enc    → ~/.config/rclone/ (optionnel)

SHUTDOWN (chiffrement) :
  ~/.ssh/           → ssh.enc       (chiffre AES-256-CBC)
  /etc/wireguard/   → wireguard.enc (wg-quick down + chiffre)
  ~/.gnupg/         → gnupg.enc     (optionnel)
  ~/.config/rclone/ → rclone.enc    (optionnel)
  + suppression des fichiers en clair
```

## Prerequis

- Linux
- OpenSSL (`apt install openssl`)
- WireGuard (`apt install wireguard`) si vous l'utilisez
- sudo (pour /etc/wireguard)

## Installation

```bash
# 1. Copier le script
cp keys-manager.sh ~/keys-manager.sh
chmod +x ~/keys-manager.sh

# 2. Premier chiffrement (vos cles doivent etre en place)
bash ~/keys-manager.sh
# → Choisir "o" pour chiffrer, entrer un mot de passe

# 3. (Optionnel) Autostart au login — fichier .desktop
cp keys-manager.desktop ~/.config/autostart/
```

## Usage

```bash
# Lancer le gestionnaire
bash keys-manager.sh

# Le script detecte automatiquement l'etat :
#   Cles chiffrees → demande le mot de passe → dechiffre
#   Cles en clair  → demande confirmation   → chiffre
```

## Configuration

Editez les variables en haut du script pour adapter a votre setup :

```bash
# Fichiers chiffres
SSH_ENC="$HOME/ssh.enc"
WG_ENC="$HOME/wireguard.enc"

# Dossiers en clair
SSH_DIR="$HOME/.ssh"
WG_DIR="/etc/wireguard"

# Sous-dossier pour detecter l'etat (doit contenir les cles privees)
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

## Securite

- **Algorithme** : AES-256-CBC avec derivation PBKDF2
- **Mot de passe** : interactif uniquement (jamais stocke)
- **Fichiers temporaires** : /dev/shm (RAM), supprimes immediatement apres usage — jamais ecrits sur disque
- **Modele de menace** : protege contre le vol physique de la machine. Ne protege PAS si l'attaquant connait le mot de passe.
- **Sauvegarde** : gardez une copie des .enc sur un support externe (USB chiffre)
