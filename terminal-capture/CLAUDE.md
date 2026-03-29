# CLAUDE.md — Terminal Capture

## Contexte

Terminal Capture est un gestionnaire de sessions Claude Code. Il lance Claude Code dans un projet, capture la conversation, et genere un journal de projet cumulatif avec analyse automatique.

## Structure

- `lancer-session.sh` : lanceur bash, menu zenity, demarre Claude Code, appelle l'exporteur
- `exporter_conversation.py` : lit le JSONL Claude Code, genere Markdown + JOURNAL.md
- `projets.conf` : liste NOM=CHEMIN des projets (cree par l'utilisateur)
- `install.sh` : cree raccourci bureau GNOME

## Aider l'utilisateur a configurer

1. **projets.conf** : copier l'exemple, ajouter ses projets (format NOM=CHEMIN_ABSOLU)
2. **zenity** : installer avec `sudo apt install zenity` si absent
3. **Claude Code** : doit etre dans le PATH (`which claude` doit repondre)
4. **Raccourci bureau** : `bash install.sh` cree un .desktop sur le Bureau

## Ce qu'il NE FAUT PAS modifier

- `encode_project_path()` dans l'exporteur — c'est la convention de Claude Code pour encoder les chemins
- Le parsing JSONL — le format est impose par Claude Code
- Le chemin `~/.claude/projects/` — c'est le stockage natif de Claude Code

## Analyse automatique (JOURNAL.md)

L'exporteur utilise des regex pour extraire :
- **Corrections** : lignes contenant "corrige", "fixe", "repare", "resolu"
- **TODOs** : lignes contenant "TODO", "a faire", "en attente", "manquant"
- **Decisions** : lignes avec "→" ou "->"
- **Fichiers** : chemins de fichiers detectes dans le texte

C'est du pre-remplissage — l'utilisateur complete ensuite manuellement la section "Notes complementaires".
