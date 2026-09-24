# AgentIA.md — VeilleNumerique

## Contexte

VeilleNumerique est un système de veille RSS automatisé avec analyse IA.
Architecture : conteneurs indépendants (1 sujet = 1 dossier), pyramide de synthèses temporelles (6 couches).

## Structure du code

- `veille.py` : orchestrateur principal, point d'entrée CLI
- `engine/fetcher.py` : fetch RSS via feedparser, déduplication MD5, détection mots-clés alerte
- `engine/analyser.py` : appels API IA pour 6 couches (jour/semaine/mois/trimestre/année/cumul)
- `engine/consolidator.py` : stockage/lecture JSON par couche et date
- `engine/mailer.py` : génération emails HTML + envoi SMTP
- `engine/publisher.py` : conversion JSON→Markdown + git push vers GitHub
- `config.env` : variables d'environnement (API key, email, SMTP) — NE JAMAIS COMMITTER

## Aider l'utilisateur à configurer

1. **config.env** : copier config.env.example → config.env, remplir IA_API_KEY, IA_API_URL, IA_MODEL et config email/SMTP
2. **Créer un conteneur** : `bash new-conteneur.sh <id> "Nom"` puis éditer config.json
3. **config.json d'un conteneur** :
   - `sources` : liste de {name, url, lang} — URLs de flux RSS
   - `keywords_alert` : mots-clés qui déclenchent des alertes prioritaires
   - `analyse_prompt` : prompt système donné à l'IA pour orienter l'analyse
   - `source_colors` : couleurs hex pour les badges email (optionnel)
4. **Tester** : `bash run.sh --conteneur <id> --test --no-email`
5. **Crons** : `bash cron-install.sh` installe les crons automatiquement

## Ce qu'il NE FAUT PAS modifier

- La logique de consolidation dans `veille.py` (should_consolidate) — les règles de dates sont correctes
- Le format JSON des synthèses dans `consolidator.py` — le publisher et le mailer en dépendent
- Le nommage des fichiers par couche (_date_to_filename) — tout le système repose dessus

## Trouver des sources RSS

Si l'utilisateur ne sait pas quelles sources utiliser, aidez-le :
- Suggérer des flux RSS connus dans son domaine
- Vérifier que les URLs sont valides (feedparser tolère les erreurs)
- 5-15 sources par conteneur est un bon équilibre
- Les mots-clés alerte doivent être spécifiques (pas "news" ou "update")

## Debugger

- `veille.log` contient toutes les traces d'exécution
- `--no-email` affiche les résultats dans le terminal
- `--test` regarde 365 jours en arrière (utile si les sources sont lentes)
- Si 0 articles : vérifier les URLs RSS dans config.json (tester dans un navigateur)
- Si erreur IA : vérifier IA_API_KEY, IA_API_URL et IA_MODEL dans config.env
- Si erreur email : vérifier SMTP host/port/user/pass dans config.env
