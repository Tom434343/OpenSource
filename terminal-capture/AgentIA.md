# AgentIA.md — Terminal Capture

## Contexte

Terminal Capture est un gestionnaire de sessions de votre agent de codage. Il lance votre agent de codage dans un projet, capture la conversation, et génère un journal de projet cumulatif avec analyse automatique.

## Structure

- `lancer-session.sh` : lanceur bash, menu zenity, démarre votre agent de codage, appelle l'exporteur
- `exporter_conversation.py` : lit le JSONL de votre agent de codage, génère Markdown + JOURNAL.md
- `projets.conf` : liste NOM=CHEMIN des projets (créé par l'utilisateur)
- `install.sh` : crée raccourci bureau GNOME

## Aider l'utilisateur à configurer

1. **projets.conf** : copier l'exemple, ajouter ses projets (format NOM=CHEMIN_ABSOLU)
2. **zenity** : installer avec `sudo apt install zenity` si absent
3. **votre agent de codage** : doit être dans le PATH (`which agentia` doit répondre)
4. **Raccourci bureau** : `bash install.sh` crée un .desktop sur le Bureau

## Ce qu'il NE FAUT PAS modifier

- `encode_project_path()` dans l'exporteur — c'est la convention de votre agent de codage pour encoder les chemins
- Le parsing JSONL — le format est imposé par votre agent de codage
- Le chemin `~/.agentia/projects/` — c'est le stockage natif de votre agent de codage

## Analyse automatique (JOURNAL.md)

L'exporteur utilise des regex pour extraire :
- **Corrections** : lignes contenant « corrigé », « fixé », « réparé », « résolu »
- **TODOs** : lignes contenant « TODO », « à faire », « en attente », « manquant »
- **Décisions** : lignes avec « → » ou « -> »
- **Fichiers** : chemins de fichiers détectés dans le texte

C'est du pré-remplissage — l'utilisateur complète ensuite manuellement la section « Notes complémentaires ».
