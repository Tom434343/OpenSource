# Terminal Capture

**Author** : Céline PASCAUD ([Digital Consulting & Training](https://www.digitalct.io))

Gestionnaire de sessions de votre agent de codage avec export Markdown et journal de projet automatique.

Sélectionnez un projet, votre agent de codage se lance dedans. À la fin, la conversation est exportée en Markdown et un journal cumulatif est pré-rempli automatiquement.

## Ce que ça fait

```
1. Choix du projet (zenity ou argument CLI)
2. Votre agent de codage se lance dans le dossier du projet
3. Vous travaillez normalement avec votre agent de codage
4. À la fin : Ctrl+D ou /exit
5. Export automatique :
   → conversation_20260329_143022.md  (transcription complète)
   → JOURNAL.md mis à jour            (analyse automatique)
```

## Prérequis

- Linux avec bureau GNOME (pour zenity)
- Python 3
- votre agent de codage installé (`agentia` dans le PATH)
- zenity (`sudo apt install zenity`)

## Installation

```bash
# 1. Configurer vos projets
cp projets.conf.example projets.conf
nano projets.conf

# 2. Installer le raccourci bureau
bash install.sh

# 3. (Ou lancer directement)
bash lancer-session.sh
bash lancer-session.sh MonProjet  # sans menu
```

## Configuration (projets.conf)

```bash
# Format : NOM=CHEMIN_ABSOLU
MonSite=/home/user/mon-site
API=/home/user/mon-api
Scripts=/home/user/scripts
```

## Sortie générée

Dans `[Projet]/Documentation/Terminal-Capture/` :

```
Terminal-Capture/
├── conversation_20260329_143022.md    ← Transcription session
├── conversation_20260330_091500.md    ← Autre session
└── JOURNAL.md                          ← Journal cumulatif
```

### JOURNAL.md (auto-analyse)

```markdown
## Session du 29/03/2026 à 14:30

### Corrections / Bugs fixes
- Corrigé le bug de connexion SMTP
- Fix permissions clés SSH

### TODO / En attente
- Ajouter tests unitaires
- Mettre à jour la documentation

### Décisions techniques
- Migration vers Python 3.13
- Passage à Haiku pour les analyses

### Fichiers modifiés
- engine/mailer.py
- config.env.example
```

## Structure

```
terminal-capture/
├── lancer-session.sh           ← Lanceur principal
├── exporter_conversation.py    ← Export JSONL → Markdown + JOURNAL
├── projets.conf                ← Vos projets (à créer)
├── projets.conf.example        ← Template
├── install.sh                  ← Raccourci bureau + wrapper
└── README.md
```

## Comment ça marche

1. Le lanceur lit `projets.conf` et affiche un menu zenity
2. Votre agent de codage est lancé dans le dossier du projet sélectionné
3. Après `/exit`, le script trouve le fichier JSONL de la session dans `~/.agentia/projects/`
4. L'exporteur lit le JSONL, génère le Markdown, et analyse la conversation avec des regex pour pré-remplir le journal
