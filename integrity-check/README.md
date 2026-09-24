# Integrity Check

**Author** : Thomas ROUGER ([Digital Consulting & Training](https://www.digitalct.io))

Vérification d'intégrité système Linux : baseline + 13 contrôles automatiques.

Crée une empreinte de référence de votre système (baseline), puis vérifie quotidiennement que rien n'a été modifié sans autorisation : clés SSH, binaires, comptes utilisateurs, sudoers, crontabs, ports, SUID, rootkits...

## Les 13 contrôles

| # | Contrôle | Méthode | Niveau |
|---|----------|---------|--------|
| 1 | Clés SSH privées | SHA256 hash + permissions | CRITIQUE si modifié |
| 2 | Comptes système | /etc/passwd diff | CRITIQUE si nouveau compte |
| 3 | Sudoers | SHA256 hash | CRITIQUE si modifié |
| 4 | Crontabs | SHA256 hash + diff | WARNING si modifié |
| 5 | Fichiers SUID/SGID | Liste comparative | CRITIQUE si nouveau |
| 6 | Binaires système | SHA256 de 2000+ binaires | CRITIQUE si modifié |
| 7 | Modifications /etc | find -mtime -7 | WARNING si >20 fichiers |
| 8 | Ports en écoute | ss -tlnp comparative | WARNING si nouveau port |
| 9 | Connexions sortantes | ss -tnp | INFO |
| 10 | Packages récents | dpkg.log 7 jours | INFO |
| 11 | Processus suspects | regex mineurs/backdoors | CRITIQUE si détecté |
| 12 | Espace disque | df -h | WARNING >80%, CRITIQUE >90% |
| 13 | Rootkits (rkhunter) | scan complet | CRITIQUE si warning réel |

## Prérequis

- Linux (Debian/Ubuntu)
- sudo
- Optionnel : `rkhunter` (`sudo apt install rkhunter`)

## Installation

```bash
# 1. Créer la baseline (machine propre !)
bash baseline.sh

# 2. Lancer un premier check
bash integrity-check.sh

# 3. (Optionnel) Installer le service boot + cron quotidien
sudo bash install.sh
```

## Usage

```bash
# Check manuel
bash integrity-check.sh

# Les logs sont dans ~/logs/security/
ls ~/logs/security/integrity-*.log
```

## Quand relancer la baseline ?

Après tout changement volontaire du système :
- Nouvelle clé SSH
- Nouveau package installé
- Modification sudoers
- Nouveau service/port

```bash
bash baseline.sh
```

## Structure

```
integrity-check/
├── baseline.sh           ← Crée la référence (à lancer 1 fois)
├── integrity-check.sh    ← Vérifie l'intégrité (quotidien)
├── install.sh            ← Installe service boot + cron
├── baseline/             ← Fichiers de référence (générés)
│   ├── ssh-keys.sha256
│   ├── passwd.baseline
│   ├── sudoers.sha256
│   ├── crontabs.baseline
│   ├── suid-files.txt
│   ├── binaries.sha256
│   └── listening-ports.baseline
└── README.md
```

## Personnalisation

- **Réseaux ignorés** : éditez `IGNORE_NETS` dans integrity-check.sh pour ignorer vos subnets VPN
- **Faux positifs rkhunter** : ajoutez des patterns dans le filtre `grep -v` de la section rkhunter
