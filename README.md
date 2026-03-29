# OpenSource Tools — Digital Consulting & Training

5 outils Linux autonomes, prets a deployer avec [Claude Code](https://claude.ai/code).

Chaque outil fonctionne independamment. Choisissez celui qui vous interesse, lisez son README, et lancez Claude Code dedans pour le configurer a votre sauce.

## Outils

| Outil | Description | Requis |
|-------|-------------|--------|
| [veille-numerique](./veille-numerique/) | Veille RSS automatisee + analyse IA (Claude) + syntheses pyramidales (jour/semaine/mois/trimestre/annee) | Python 3.10+, cron |
| [keys-manager](./keys-manager/) | Chiffrement/dechiffrement de cles SSH et WireGuard avec OpenSSL AES-256-CBC | OpenSSL, bash |
| [integrity-check](./integrity-check/) | Verification d'integrite systeme : baseline + 15 controles (binaires, ports, SUID, rootkits...) | bash, sha256sum, rkhunter |
| [lynis-fleet](./lynis-fleet/) | Audit de securite Lynis centralise sur plusieurs serveurs en parallele via SSH | Lynis, SSH, bash |
| [terminal-capture](./terminal-capture/) | Gestionnaire de sessions Claude Code avec export Markdown et journal de projet | Python 3, zenity, Claude Code |

## Comment utiliser

```bash
# 1. Cloner le depot
git clone https://github.com/Tom434343/OpenSource.git
cd OpenSource

# 2. Aller dans l'outil qui vous interesse
cd veille-numerique

# 3. Lire le README
less README.md

# 4. Lancer Claude Code pour configurer
claude
> "Configure-moi cet outil pour mon usage"
```

Chaque dossier contient un `CLAUDE.md` que Claude Code lira automatiquement pour comprendre l'outil et vous aider a le configurer.

## Environnement

- **OS** : Linux (Debian/Ubuntu recommande)
- **Windows/Mac** : non supporte (ces outils sont faits pour des serveurs Linux)

## Licence

[MIT](./LICENSE) — Utilisez, modifiez, distribuez librement.

---

*Outils crees par [Digital Consulting & Training](https://www.digitalct.io)*
