# Lynis Fleet

**Author** : Thomas ROUGER ([Digital Consulting & Training](https://www.digitalct.io))

Audit de securite Lynis centralise sur plusieurs serveurs Linux en parallele via SSH.

Lance [Lynis](https://cisofy.com/lynis/) sur tous vos serveurs simultanement (1 connexion SSH par serveur), consolide les scores et identifie les Quick Wins — les corrections qui ameliorent TOUS les serveurs d'un coup.

## Ce que ca fait

```
servers.conf        lynis-fleet.sh        Rapport
┌──────────┐       ┌──────────────┐       ┌──────────────────┐
│ LOCAL     │──────→│              │──────→│ Scores /100      │
│ WEB1     │──SSH──│  Lynis audit │──────→│ Suggestions      │
│ WEB2     │──SSH──│  en parallele│──────→│ Quick Wins       │
│ DB1      │──SSH──│              │──────→│ Rapport JSON     │
└──────────┘       └──────────────┘       └──────────────────┘
                   ~2-3 min total
```

## Prerequis

- **Lynis** installe sur chaque serveur : `sudo apt install lynis`
- **SSH** avec cle publique vers chaque serveur distant
- **sudo** sans mot de passe pour l'utilisateur deploy (Lynis a besoin de root)
- bash 4.0+ (pour les tableaux associatifs)

## Installation

```bash
# 1. Configurer les serveurs
cp servers.conf.example servers.conf
nano servers.conf

# 2. Tester la connexion SSH vers chaque serveur
ssh -i ~/.ssh/id_deploy deploy@10.0.0.2 "sudo lynis --version"

# 3. Lancer l'audit
bash lynis-fleet.sh
```

## Configuration (servers.conf)

Un serveur par ligne, format : `NOM|USER@IP|CLE_SSH`

```bash
# Machine locale (pas de SSH)
LOCAL||

# Serveurs distants
WEB1|deploy@10.0.0.2|~/.ssh/id_deploy
WEB2|deploy@10.0.0.3|~/.ssh/id_deploy
DB1|admin@10.0.0.10|~/.ssh/id_db
```

- Laissez `USER@IP` et `CLE_SSH` vides pour un audit local
- Les commentaires (`#`) sont ignores

## Sortie

### Terminal

```
   SCORES HARDENING
   LOCAL           73/100
   WEB1            87/100
   WEB2            87/100
   DB1             84/100
   MOYENNE         83/100

   SUGGESTIONS (Quick Wins en premier)
   [QUICK WIN - 4 serveurs] PKGS-7346
              Consider purging old/removed packages
              Sur: LOCAL, WEB1, WEB2, DB1
   ...
```

### JSON (reports/lynis_YYYY-MM-DD.json)

```json
{
  "date": "2026-03-29",
  "duration_seconds": 166,
  "summary": {"average_score": 83, "total_suggestions": 38},
  "servers": [{"name": "LOCAL", "score": 73}, ...],
  "suggestions": [{"id": "PKGS-7346", "description": "...", "servers": ["LOCAL", "WEB1"], "count": 4}]
}
```

## Securite

- 1 connexion SSH par serveur = pas de risque Fail2Ban
- SSH en mode BatchMode (pas de prompt interactif)
- Les audits tournent en parallele (background processes)
- Aucune donnee sensible dans le rapport (juste scores + IDs de suggestions Lynis)
- `StrictHostKeyChecking=no` par defaut — acceptable sur reseau interne/VPN. Sur un reseau non fiable, editez le script et remplacez par `StrictHostKeyChecking=accept-new`
