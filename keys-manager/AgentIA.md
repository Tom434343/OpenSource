# AgentIA.md — Keys Manager

## Contexte

Keys Manager chiffre/déchiffre des clés sensibles (SSH, WireGuard, GnuPG, rclone) avec OpenSSL AES-256-CBC.
Un seul script bash, zéro dépendance externe (juste openssl + tar).

## Structure

- `keys-manager.sh` : script unique, détection automatique de l'état (clair/chiffré)
- `keys-manager.desktop` : fichier autostart GNOME (optionnel)

## Aider l'utilisateur à configurer

1. **Adapter les chemins** : éditer les variables en haut du script
   - `SSH_KEYS_SUBDIR` : le script détecte l'état en vérifiant si ce dossier existe
   - Si l'utilisateur n'a pas de sous-dossier `restricted/`, changer pour `$SSH_DIR` directement
2. **Retirer les composants inutiles** : si pas de WireGuard → le script l'ignore déjà (test -d)
3. **Autostart** : créer le .desktop si l'utilisateur veut le déchiffrement au boot

## Ce qu'il NE FAUT PAS modifier

- L'ordre des opérations : toujours vérifier le mot de passe AVANT de restaurer
- La suppression des fichiers temporaires dans /tmp
- Le flag `-pbkdf2` (sécurité de la dérivation de clé)

## Attention

- Le même mot de passe doit être utilisé pour TOUS les .enc (le script vérifie sur ssh.enc puis utilise le même pour les autres)
- Ne JAMAIS supprimer les .enc sans avoir vérifié que les clés en clair sont restaurées
- Rappeler à l'utilisateur de sauvegarder ses .enc sur un support externe
