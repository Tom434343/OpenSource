# Terminal Capture

Gestionnaire de sessions Claude Code avec export Markdown et journal de projet automatique.

Selectionnez un projet, Claude Code se lance dedans. A la fin, la conversation est exportee en Markdown et un journal cumulatif est pre-rempli automatiquement.

## Ce que ca fait

```
1. Choix du projet (zenity ou argument CLI)
2. Claude Code se lance dans le dossier du projet
3. Vous travaillez normalement avec Claude Code
4. A la fin : Ctrl+D ou /exit
5. Export automatique :
   → conversation_20260329_143022.md  (transcription complete)
   → JOURNAL.md mis a jour            (analyse automatique)
```

## Prerequis

- Linux avec bureau GNOME (pour zenity)
- Python 3
- [Claude Code](https://claude.ai/code) installe (`claude` dans le PATH)
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

## Sortie generee

Dans `[Projet]/Documentation/Terminal-Capture/` :

```
Terminal-Capture/
├── conversation_20260329_143022.md    ← Transcription session
├── conversation_20260330_091500.md    ← Autre session
└── JOURNAL.md                          ← Journal cumulatif
```

### JOURNAL.md (auto-analyse)

```markdown
## Session du 29/03/2026 a 14:30

### Corrections / Bugs fixes
- Corrige le bug de connexion SMTP
- Fix permissions cles SSH

### TODO / En attente
- Ajouter tests unitaires
- Mettre a jour la documentation

### Decisions techniques
- Migration vers Python 3.13
- Passage a Claude Haiku pour les analyses

### Fichiers modifies
- engine/mailer.py
- config.env.example
```

## Structure

```
terminal-capture/
├── lancer-session.sh           ← Lanceur principal
├── exporter_conversation.py    ← Export JSONL → Markdown + JOURNAL
├── projets.conf                ← Vos projets (a creer)
├── projets.conf.example        ← Template
├── install.sh                  ← Raccourci bureau + wrapper
└── README.md
```

## Comment ca marche

1. Le lanceur lit `projets.conf` et affiche un menu zenity
2. Claude Code est lance dans le dossier du projet selectionne
3. Apres `/exit`, le script trouve le fichier JSONL de la session dans `~/.claude/projects/`
4. L'exporteur lit le JSONL, genere le Markdown, et analyse la conversation avec des regex pour pre-remplir le journal
