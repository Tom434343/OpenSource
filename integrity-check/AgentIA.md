# AgentIA.md — Integrity Check

## Contexte

Outil de vérification d'intégrité système Linux. Deux scripts : baseline.sh (référence) + integrity-check.sh (vérification).
13 contrôles automatiques couvrant clés SSH, binaires, comptes, sudoers, crontabs, ports, rootkits.

## Structure

- `baseline.sh` : crée les fichiers de référence dans `baseline/`
- `integrity-check.sh` : compare l'état actuel avec la baseline
- `install.sh` : installe service systemd boot + cron quotidien
- `baseline/` : dossier généré contenant les empreintes de référence

## Aider l'utilisateur à configurer

1. **Première utilisation** : `bash baseline.sh` sur une machine propre, puis `bash integrity-check.sh`
2. **IGNORE_NETS** : si l'utilisateur a un VPN (WireGuard, OpenVPN), ajouter le subnet dans cette variable
3. **rkhunter** : installer avec `sudo apt install rkhunter` pour le contrôle 13
4. **Faux positifs** : adapter le filtre `grep -v` dans la section rkhunter selon le système
5. **Cron** : `sudo bash install.sh` pour automatiser au boot + quotidien 08h00

## Ce qu'il NE FAUT PAS modifier

- L'ordre des contrôles (numérotés 1-13)
- La structure de baseline/ (les noms de fichiers sont référencés dans integrity-check.sh)
- Le code de sortie (`exit $CRITICALS`) — utilisé par systemd et les scripts appelants

## Détection des clés SSH

La baseline détecte automatiquement les clés privées en cherchant les fichiers commençant par "-----BEGIN" dans ~/.ssh/ et ses sous-dossiers. Pas besoin de lister les noms de clés manuellement.
