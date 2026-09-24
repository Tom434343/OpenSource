# VeilleNumerique

**Author** : Thomas ROUGER ([Digital Consulting & Training](https://www.digitalct.io))

Veille RSS automatisée avec analyse IA et pyramide de synthèses temporelles.

Vous définissez des **conteneurs** (sujets de veille), chacun avec ses sources RSS et mots-clés. Le système fetch les articles, les analyse avec IA, et génère des synthèses à 6 niveaux : jour, semaine, mois, trimestre, année + mémoire cumulative.

## Ce que ça fait

```
Sources RSS → Fetch articles → Analyse IA → Synthèse jour
                                                  → Email HTML
                                                  → Publication GitHub (Markdown)

Dimanche     → Consolide les 7 jours    → Synthèse semaine + cumul
1er du mois  → Consolide les semaines   → Synthèse mois
1er trimestre→ Consolide les mois       → Synthèse trimestre
31 décembre  → Consolide les trimestres → Synthèse année
```

## Prérequis

- Linux (Debian/Ubuntu)
- Python 3.10+
- Une clé API IA (console de votre fournisseur IA)
- Un serveur SMTP pour les emails (Gmail, ProtonMail Bridge, Mailgun...)

## Installation

```bash
# 1. Installer les dépendances
pip install -r requirements.txt

# 2. Configurer l'environnement
cp config.env.example config.env
nano config.env   # Remplir : IA_API_KEY, IA_API_URL, IA_MODEL, email, SMTP

# 3. Créer votre premier conteneur
bash new-conteneur.sh cybersecurite "Cybersécurité"
# → Éditez conteneurs/cybersecurite/config.json (sources RSS, mots-clés, prompt)

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
  "name": "Cybersécurité",
  "id": "cybersecurite",
  "enabled": true,
  "days_back": 1,
  "sources": [
    {"name": "Schneier on Security", "url": "https://www.schneier.com/feed/atom/", "lang": "en"}
  ],
  "keywords_alert": ["zero-day", "ransomware", "CVE-2026"],
  "analyse_prompt": "Tu es un expert en cybersécurité. Analyse de manière factuelle...",
  "email_subject_prefix": "Veille Cyber"
}
```

Un conteneur exemple prêt à l'emploi est fourni dans `exemple-conteneur/`.

## Structure

```
veille-numerique/
├── veille.py               ← Orchestrateur principal
├── engine/
│   ├── fetcher.py          ← Fetch RSS + déduplication MD5
│   ├── analyser.py         ← Analyse IA 6 couches
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
├── new-conteneur.sh        ← Créer un nouveau conteneur
├── cron-install.sh         ← Installer les crons automatiquement
└── requirements.txt
```

## Usage

```bash
# Lancer tous les conteneurs
bash run.sh

# Un seul conteneur
bash run.sh --conteneur cybersecurite

# Mode test (365 jours en arrière, utile au début)
bash run.sh --test

# Sans email (affiche dans le terminal)
bash run.sh --no-email

# Combiner
bash run.sh --conteneur cybersecurite --test --no-email
```

## Publication GitHub (optionnel)

Le module `publisher.py` convertit les synthèses JSON en Markdown et les push sur un dépôt GitHub. Pour l'activer :

1. Créez un dépôt GitHub (public ou privé)
2. Initialisez `publication/` comme un repo git lié à votre dépôt
3. Les synthèses seront auto-publiées après chaque run

## Coût

Le modèle utilisé est `haiku-4-5` (~0.001$/article). Consultez les tarifs de votre fournisseur IA pour estimer votre usage.
