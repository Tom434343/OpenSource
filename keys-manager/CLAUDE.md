# CLAUDE.md — Keys Manager

## Contexte

Keys Manager chiffre/dechiffre des cles sensibles (SSH, WireGuard, GnuPG, rclone) avec OpenSSL AES-256-CBC.
Un seul script bash, zero dependance externe (juste openssl + tar).

## Structure

- `keys-manager.sh` : script unique, detection automatique de l'etat (clair/chiffre)
- `keys-manager.desktop` : fichier autostart GNOME (optionnel)

## Aider l'utilisateur a configurer

1. **Adapter les chemins** : editer les variables en haut du script
   - `SSH_KEYS_SUBDIR` : le script detecte l'etat en verifiant si ce dossier existe
   - Si l'utilisateur n'a pas de sous-dossier `restricted/`, changer pour `$SSH_DIR` directement
2. **Retirer les composants inutiles** : si pas de WireGuard → le script l'ignore deja (test -d)
3. **Autostart** : creer le .desktop si l'utilisateur veut le dechiffrement au boot

## Ce qu'il NE FAUT PAS modifier

- L'ordre des operations : toujours verifier le mot de passe AVANT de restaurer
- La suppression des fichiers temporaires dans /tmp
- Le flag `-pbkdf2` (securite de la derivation de cle)

## Attention

- Le meme mot de passe doit etre utilise pour TOUS les .enc (le script verifie sur ssh.enc puis utilise le meme pour les autres)
- Ne JAMAIS supprimer les .enc sans avoir verifie que les cles en clair sont restaurees
- Rappeler a l'utilisateur de sauvegarder ses .enc sur un support externe
