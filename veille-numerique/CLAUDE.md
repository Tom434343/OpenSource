# CLAUDE.md — VeilleNumerique

## Contexte

VeilleNumerique est un systeme de veille RSS automatise avec analyse Claude IA.
Architecture : conteneurs independants (1 sujet = 1 dossier), pyramide de syntheses temporelles (6 couches).

## Structure du code

- `veille.py` : orchestrateur principal, point d'entree CLI
- `engine/fetcher.py` : fetch RSS via feedparser, deduplication MD5, detection mots-cles alerte
- `engine/analyser.py` : appels Claude API pour 6 couches (jour/semaine/mois/trimestre/annee/cumul)
- `engine/consolidator.py` : stockage/lecture JSON par couche et date
- `engine/mailer.py` : generation emails HTML + envoi SMTP
- `engine/publisher.py` : conversion JSON→Markdown + git push vers GitHub
- `config.env` : variables d'environnement (API key, email, SMTP) — NE JAMAIS COMMITER

## Aider l'utilisateur a configurer

1. **config.env** : copier config.env.example → config.env, remplir ANTHROPIC_API_KEY et config email/SMTP
2. **Creer un conteneur** : `bash new-conteneur.sh <id> "Nom"` puis editer config.json
3. **config.json d'un conteneur** :
   - `sources` : liste de {name, url, lang} — URLs de flux RSS
   - `keywords_alert` : mots-cles qui declenchent des alertes prioritaires
   - `analyse_prompt` : prompt systeme donne a Claude pour orienter l'analyse
   - `source_colors` : couleurs hex pour les badges email (optionnel)
4. **Tester** : `bash run.sh --conteneur <id> --test --no-email`
5. **Crons** : `bash cron-install.sh` installe les crons automatiquement

## Ce qu'il NE FAUT PAS modifier

- La logique de consolidation dans `veille.py` (should_consolidate) — les regles de dates sont correctes
- Le format JSON des syntheses dans `consolidator.py` — le publisher et le mailer en dependent
- Le nommage des fichiers par couche (_date_to_filename) — tout le systeme repose dessus

## Trouver des sources RSS

Si l'utilisateur ne sait pas quelles sources utiliser, aidez-le :
- Suggerer des flux RSS connus dans son domaine
- Verifier que les URLs sont valides (feedparser tolere les erreurs)
- 5-15 sources par conteneur est un bon equilibre
- Les mots-cles alerte doivent etre specifiques (pas "news" ou "update")

## Debugger

- `veille.log` contient toutes les traces d'execution
- `--no-email` affiche les resultats dans le terminal
- `--test` regarde 365 jours en arriere (utile si les sources sont lentes)
- Si 0 articles : verifier les URLs RSS dans config.json (tester dans un navigateur)
- Si erreur Claude : verifier ANTHROPIC_API_KEY dans config.env
- Si erreur email : verifier SMTP host/port/user/pass dans config.env
