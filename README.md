# OpenSource Tools — Digital Consulting & Training

5 outils Linux autonomes, prêts à déployer avec votre agent de codage.

Chaque outil fonctionne indépendamment. Choisissez celui qui vous intéresse, lisez son README, et lancez votre agent de codage dedans pour le configurer à votre sauce.

## Outils

| Outil | Description | Requis |
|-------|-------------|--------|
| [veille-numerique](./veille-numerique/) | Veille RSS automatisée + analyse IA + synthèses pyramidales (jour/semaine/mois/trimestre/année) | Python 3.10+, cron |
| [keys-manager](./keys-manager/) | Chiffrement/déchiffrement de clés SSH et WireGuard avec OpenSSL AES-256-CBC | OpenSSL, bash |
| [integrity-check](./integrity-check/) | Vérification d'intégrité système : baseline + 13 contrôles (binaires, ports, SUID, rootkits...) | bash, sha256sum, rkhunter |
| [lynis-fleet](./lynis-fleet/) | Audit de sécurité Lynis centralisé sur plusieurs serveurs en parallèle via SSH | Lynis, SSH, bash |
| [terminal-capture](./terminal-capture/) | Gestionnaire de sessions de votre agent de codage avec export Markdown et journal de projet | Python 3, zenity, votre agent de codage |

## Comment utiliser

```bash
# 1. Cloner le dépôt
git clone https://github.com/Tom434343/OpenSource.git
cd OpenSource

# 2. Aller dans l'outil qui vous intéresse
cd veille-numerique

# 3. Lire le README
less README.md

# 4. Lancer votre agent de codage pour configurer
agentia
> "Analyse le code de ce dossier dans son ensemble. Explique-moi le rôle de cet outil, ses prérequis et ses dépendances, puis guide-moi étape par étape dans sa configuration pour mon environnement. Pose-moi les questions nécessaires avant toute modification, et ne change rien sans mon accord explicite."
```

Chaque dossier contient un `AgentIA.md` que votre agent de codage lira automatiquement pour comprendre l'outil et vous aider à le configurer.

## Environnement

- **OS** : Linux
- **Windows/Mac** : votre agent de codage adaptera les outils à votre système

## Contributors

| Outil | Auteur |
|-------|--------|
| veille-numerique | Thomas ROUGER |
| keys-manager | Thomas ROUGER |
| integrity-check | Thomas ROUGER |
| lynis-fleet | Thomas ROUGER |
| terminal-capture | Céline PASCAUD |

## Licence

[MIT](./LICENSE) — Utilisez, modifiez, distribuez librement.

---

*Outils créés par [Digital Consulting & Training](https://www.digitalct.io)*
