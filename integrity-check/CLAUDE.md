# CLAUDE.md — Integrity Check

## Contexte

Outil de verification d'integrite systeme Linux. Deux scripts : baseline.sh (reference) + integrity-check.sh (verification).
13 controles automatiques couvrant cles SSH, binaires, comptes, sudoers, crontabs, ports, rootkits.

## Structure

- `baseline.sh` : cree les fichiers de reference dans `baseline/`
- `integrity-check.sh` : compare l'etat actuel avec la baseline
- `install.sh` : installe service systemd boot + cron quotidien
- `baseline/` : dossier genere contenant les empreintes de reference

## Aider l'utilisateur a configurer

1. **Premiere utilisation** : `bash baseline.sh` sur une machine propre, puis `bash integrity-check.sh`
2. **IGNORE_NETS** : si l'utilisateur a un VPN (WireGuard, OpenVPN), ajouter le subnet dans cette variable
3. **rkhunter** : installer avec `sudo apt install rkhunter` pour le controle 13
4. **Faux positifs** : adapter le filtre `grep -v` dans la section rkhunter selon le systeme
5. **Cron** : `sudo bash install.sh` pour automatiser au boot + quotidien 08h00

## Ce qu'il NE FAUT PAS modifier

- L'ordre des controles (numerotes 1-13)
- La structure de baseline/ (les noms de fichiers sont references dans integrity-check.sh)
- Le code de sortie (`exit $CRITICALS`) — utilise par systemd et les scripts appelants

## Detection des cles SSH

La baseline detecte automatiquement les cles privees en cherchant les fichiers commencant par "-----BEGIN" dans ~/.ssh/ et ses sous-dossiers. Pas besoin de lister les noms de cles manuellement.
