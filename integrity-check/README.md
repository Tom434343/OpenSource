# Integrity Check

Verification d'integrite systeme Linux : baseline + 13 controles automatiques.

Cree une empreinte de reference de votre systeme (baseline), puis verifie quotidiennement que rien n'a ete modifie sans autorisation : cles SSH, binaires, comptes utilisateurs, sudoers, crontabs, ports, SUID, rootkits...

## Les 13 controles

| # | Controle | Methode | Niveau |
|---|----------|---------|--------|
| 1 | Cles SSH privees | SHA256 hash + permissions | CRITIQUE si modifie |
| 2 | Comptes systeme | /etc/passwd diff | CRITIQUE si nouveau compte |
| 3 | Sudoers | SHA256 hash | CRITIQUE si modifie |
| 4 | Crontabs | SHA256 hash + diff | WARNING si modifie |
| 5 | Fichiers SUID/SGID | Liste comparative | CRITIQUE si nouveau |
| 6 | Binaires systeme | SHA256 de 2000+ binaires | CRITIQUE si modifie |
| 7 | Modifications /etc | find -mtime -7 | WARNING si >20 fichiers |
| 8 | Ports en ecoute | ss -tlnp comparative | WARNING si nouveau port |
| 9 | Connexions sortantes | ss -tnp | INFO |
| 10 | Packages recents | dpkg.log 7 jours | INFO |
| 11 | Processus suspects | regex mineurs/backdoors | CRITIQUE si detecte |
| 12 | Espace disque | df -h | WARNING >80%, CRITIQUE >90% |
| 13 | Rootkits (rkhunter) | scan complet | CRITIQUE si warning reel |

## Prerequis

- Linux (Debian/Ubuntu)
- sudo
- Optionnel : `rkhunter` (`sudo apt install rkhunter`)

## Installation

```bash
# 1. Creer la baseline (machine propre !)
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

Apres tout changement volontaire du systeme :
- Nouvelle cle SSH
- Nouveau package installe
- Modification sudoers
- Nouveau service/port

```bash
bash baseline.sh
```

## Structure

```
integrity-check/
├── baseline.sh           ← Cree la reference (a lancer 1 fois)
├── integrity-check.sh    ← Verifie l'integrite (quotidien)
├── install.sh            ← Installe service boot + cron
├── baseline/             ← Fichiers de reference (generes)
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

- **Reseaux ignores** : editez `IGNORE_NETS` dans integrity-check.sh pour ignorer vos subnets VPN
- **Faux positifs rkhunter** : ajoutez des patterns dans le filtre `grep -v` de la section rkhunter
