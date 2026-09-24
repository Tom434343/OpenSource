# AgentIA.md — Lynis Fleet

## Contexte

Lynis Fleet lance des audits Lynis en parallèle sur plusieurs serveurs Linux via SSH.
Un script bash unique + un fichier de config (servers.conf).

## Structure

- `lynis-fleet.sh` : orchestrateur principal, lance les audits en parallèle, consolide
- `servers.conf` : liste des serveurs (NOM|USER@IP|CLE_SSH)
- `reports/` : rapports JSON générés (un par exécution)

## Aider l'utilisateur à configurer

1. **servers.conf** : copier servers.conf.example, ajouter ses serveurs
   - Format : `NOM|USER@IP|CLE_SSH`
   - Ligne vide pour le serveur local : `LOCAL||`
2. **Prérequis par serveur** :
   - Lynis installé : `sudo apt install lynis`
   - SSH avec clé publique (pas de mot de passe)
   - sudo sans mot de passe pour l'user deploy : `echo "deploy ALL=(ALL) NOPASSWD: ALL" | sudo tee /etc/sudoers.d/deploy`
3. **Tester** : `ssh -i CLE user@ip "sudo lynis --version"` doit répondre

## Ce qu'il NE FAUT PAS modifier

- Le parsing des suggestions Lynis (format `suggestion[]=ID|description|...|`)
- Le mécanisme parallèle avec `wait` (1 SSH par serveur = safe Fail2Ban)
- Le format JSON du rapport (peut être consommé par d'autres outils)

## Quick Wins

Le concept clé : les suggestions présentes sur TOUS les serveurs sont les "Quick Wins" — une seule correction appliquée partout améliore le score de toute la flotte. Le script les affiche en premier.
