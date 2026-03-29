# VeilleNumerique

Veille RSS automatisee avec analyse IA (Claude) et pyramide de syntheses temporelles.

Vous definissez des **conteneurs** (sujets de veille), chacun avec ses sources RSS et mots-cles. Le systeme fetch les articles, les analyse avec Claude, et genere des syntheses a 6 niveaux : jour, semaine, mois, trimestre, annee + memoire cumulative.

## Ce que ca fait

```
Sources RSS → Fetch articles → Analyse Claude IA → Synthese jour
                                                  → Email HTML
                                                  → Publication GitHub (Markdown)

Dimanche     → Consolide les 7 jours    → Synthese semaine + cumul
1er du mois  → Consolide les semaines   → Synthese mois
1er trimestre→ Consolide les mois       → Synthese trimestre
31 decembre  → Consolide les trimestres → Synthese annee
```

## Prerequis

- Linux (Debian/Ubuntu)
- Python 3.10+
- Une cle API Anthropic ([console.anthropic.com](https://console.anthropic.com/))
- Un serveur SMTP pour les emails (Gmail, ProtonMail Bridge, Mailgun...)

## Installation

```bash
# 1. Installer les dependances
pip install -r requirements.txt

# 2. Configurer l'environnement
cp config.env.example config.env
nano config.env   # Remplir : ANTHROPIC_API_KEY, email, SMTP

# 3. Creer votre premier conteneur
bash new-conteneur.sh cybersecurite "Cybersecurite"
# → Editez conteneurs/cybersecurite/config.json (sources RSS, mots-cles, prompt)

# 4. Tester (sans email)
bash run.sh --conteneur cybersecurite --test --no-email

# 5. Tester avec email
bash run.sh --conteneur cybersecurite --test

# 6. Installer les crons
bash cron-install.sh
```

## Configuration d'un conteneur

Chaque conteneur est un dossier dans `conteneurs/` avec un `config.json` :

```json
{
  "name": "Cybersecurite",
  "id": "cybersecurite",
  "enabled": true,
  "days_back": 1,
  "sources": [
    {"name": "Schneier on Security", "url": "https://www.schneier.com/feed/atom/", "lang": "en"}
  ],
  "keywords_alert": ["zero-day", "ransomware", "CVE-2026"],
  "analyse_prompt": "Tu es un expert en cybersecurite. Analyse de maniere factuelle...",
  "email_subject_prefix": "Veille Cyber"
}
```

Un conteneur exemple pret a l'emploi est fourni dans `exemple-conteneur/`.

## Structure

```
veille-numerique/
├── veille.py               ← Orchestrateur principal
├── engine/
│   ├── fetcher.py          ← Fetch RSS + deduplication MD5
│   ├── analyser.py         ← Analyse Claude 6 couches
│   ├── consolidator.py     ← Stockage JSON par couche
│   ├── mailer.py           ← Emails HTML
│   └── publisher.py        ← Publication GitHub Markdown
├── conteneurs/             ← Vos sujets de veille (1 dossier = 1 sujet)
│   └── cybersecurite/
│       ├── config.json
│       ├── seen_articles.json
│       └── syntheses/
│           ├── jour/       ← 2026-03-29.json
│           ├── semaine/    ← 2026-W13.json
│           ├── mois/       ← 2026-03.json
│           ├── trimestre/  ← 2026-Q1.json
│           ├── annee/      ← 2026.json
│           └── cumul/      ← cumul-2026-W13.json
├── config.env.example      ← Template variables d'environnement
├── run.sh                  ← Lanceur (source config.env + python)
├── new-conteneur.sh        ← Creer un nouveau conteneur
├── cron-install.sh         ← Installer les crons automatiquement
└── requirements.txt
```

## Usage

```bash
# Lancer tous les conteneurs
bash run.sh

# Un seul conteneur
bash run.sh --conteneur cybersecurite

# Mode test (365 jours en arriere, utile au debut)
bash run.sh --test

# Sans email (affiche dans le terminal)
bash run.sh --no-email

# Combiner
bash run.sh --conteneur cybersecurite --test --no-email
```

## Publication GitHub (optionnel)

Le module `publisher.py` convertit les syntheses JSON en Markdown et les push sur un depot GitHub. Pour l'activer :

1. Creez un depot GitHub (public ou prive)
2. Initialisez `publication/` comme un repo git lie a votre depot
3. Les syntheses seront auto-publiees apres chaque run

## Cout

Le modele utilise est `claude-haiku-4-5` (~0.001$/article). Consultez les [tarifs Anthropic](https://www.anthropic.com/pricing) pour estimer votre usage.
