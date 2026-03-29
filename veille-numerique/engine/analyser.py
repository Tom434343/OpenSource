"""
VeilleNumerique — Analyse Claude multi-couche
Chaque couche a son propre prompt adapté à la granularité temporelle.
"""

import anthropic
import os

MODEL = "claude-haiku-4-5-20251001"
MAX_TOKENS = 2000


def _call_claude(prompt, log_fn):
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        log_fn("ERREUR: ANTHROPIC_API_KEY non définie")
        return None
    try:
        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            messages=[{"role": "user", "content": prompt}]
        )
        return message.content[0].text
    except Exception as e:
        log_fn(f"ERREUR Claude API: {e}")
        return None


# ─── COUCHE JOUR ─────────────────────────────────────────────────────────────

def analyse_jour(articles, config, log_fn):
    if not articles:
        return "Aucun nouvel article aujourd'hui."

    alert_articles = [a for a in articles if a["alert"]]
    other_articles = [a for a in articles if not a["alert"]]
    source_names = ", ".join(sorted(set(a["source"] for a in articles)))
    base_prompt = config.get("analyse_prompt", "Analyse les articles suivants.")

    content = f"""{base_prompt}

Voici {len(articles)} nouveaux articles collectés aujourd'hui depuis : {source_names}.
ARTICLES PRIORITAIRES (mots-clés alerte) : {len(alert_articles)}
AUTRES ARTICLES : {len(other_articles)}

--- ARTICLES ---
"""
    for a in articles[:30]:
        tag = "🚨 ALERTE" if a["alert"] else "📰"
        content += f"""
{tag} [{a['source']}] {a['title']}
URL: {a['link']}
Résumé: {a['summary'][:300]}
---"""

    content += """

Produis une synthèse quotidienne structurée en français :

1. **ALERTES CRITIQUES** (si applicable) : mesures législatives imminentes, votes prévus, nouvelles menaces concrètes
2. **FAITS DU JOUR** : 2-4 points clés factuels
3. **SIGNAUX FAIBLES** : éléments qui pourraient devenir importants
4. **MOTS-CLÉS** : 5-10 tags pour indexation

Sois direct, factuel. Maximum 400 mots."""

    log_fn(f"  Analyse JOUR — {len(articles)} articles...")
    return _call_claude(content, log_fn)


# ─── COUCHE SEMAINE ──────────────────────────────────────────────────────────

def analyse_semaine(syntheses_jour, config, log_fn):
    if not syntheses_jour:
        return "Aucune synthèse quotidienne cette semaine."

    base_prompt = config.get("analyse_prompt", "")
    jours_txt = ""
    for s in syntheses_jour:
        jours_txt += f"\n--- {s['date']} ---\n{s['analyse']}\n"

    content = f"""{base_prompt}

Tu reçois les synthèses quotidiennes de la semaine ({len(syntheses_jour)} jours).
Ton rôle : identifier les TENDANCES et FILS ROUGES qui traversent la semaine.

{jours_txt}

Produis une synthèse hebdomadaire en français :

1. **TENDANCES DE LA SEMAINE** : 2-3 mouvements de fond identifiés à travers les jours
2. **ÉVÉNEMENTS MARQUANTS** : les 3-5 faits les plus importants de la semaine
3. **LIENS ENTRE LES SUJETS** : connexions non évidentes entre événements de jours différents
4. **ÉVOLUTION** : ce qui a changé entre le début et la fin de la semaine
5. **À SURVEILLER** : ce qui pourrait devenir important la semaine prochaine
6. **MOTS-CLÉS** : 10-15 tags pour indexation

Maximum 600 mots."""

    log_fn(f"  Analyse SEMAINE — {len(syntheses_jour)} jours...")
    return _call_claude(content, log_fn)


# ─── COUCHE MOIS ─────────────────────────────────────────────────────────────

def analyse_mois(syntheses_semaine, config, log_fn):
    if not syntheses_semaine:
        return "Aucune synthèse hebdomadaire ce mois."

    base_prompt = config.get("analyse_prompt", "")
    semaines_txt = ""
    for s in syntheses_semaine:
        semaines_txt += f"\n--- Semaine {s['date']} ---\n{s['analyse']}\n"

    content = f"""{base_prompt}

Tu reçois les synthèses hebdomadaires du mois ({len(syntheses_semaine)} semaines).
Ton rôle : dégager les DYNAMIQUES MENSUELLES, les inflexions et les trajectoires.

{semaines_txt}

Produis une synthèse mensuelle en français :

1. **DYNAMIQUES DU MOIS** : 2-3 grandes tendances qui se dégagent sur le mois entier
2. **FAITS STRUCTURANTS** : les 3-5 événements qui changent la donne ce mois
3. **TRAJECTOIRES** : ce qui accélère, ce qui ralentit, ce qui émerge
4. **ACTEURS CLÉS** : institutions, personnalités, entreprises les plus actives ce mois
5. **COMPARAISON** : comment ce mois se distingue du précédent (si contexte disponible)
6. **PERSPECTIVES** : anticipations pour le mois suivant
7. **MOTS-CLÉS** : 15-20 tags

Maximum 800 mots."""

    log_fn(f"  Analyse MOIS — {len(syntheses_semaine)} semaines...")
    return _call_claude(content, log_fn)


# ─── COUCHE TRIMESTRE ────────────────────────────────────────────────────────

def analyse_trimestre(syntheses_mois, config, log_fn):
    if not syntheses_mois:
        return "Aucune synthèse mensuelle ce trimestre."

    base_prompt = config.get("analyse_prompt", "")
    mois_txt = ""
    for s in syntheses_mois:
        mois_txt += f"\n--- {s['date']} ---\n{s['analyse']}\n"

    content = f"""{base_prompt}

Tu reçois les synthèses mensuelles du trimestre ({len(syntheses_mois)} mois).
Ton rôle : analyse STRATÉGIQUE — grandes manœuvres, rapports de force, inflexions majeures.

{mois_txt}

Produis une analyse trimestrielle en français :

1. **MOUVEMENTS DE FOND** : les 2-3 grandes dynamiques qui redéfinissent le paysage ce trimestre
2. **CHRONOLOGIE CLÉS** : timeline des événements structurants
3. **RAPPORT DE FORCES** : qui gagne du terrain, qui en perd (institutions, lobbies, société civile)
4. **INFLEXIONS** : ce qui a basculé ce trimestre par rapport au précédent
5. **RISQUES ÉMERGENTS** : menaces qui montent et ne sont pas encore dans le radar médiatique
6. **SCÉNARIOS** : 2-3 scénarios possibles pour le trimestre suivant
7. **MOTS-CLÉS** : 20-25 tags

Maximum 1000 mots."""

    log_fn(f"  Analyse TRIMESTRE — {len(syntheses_mois)} mois...")
    return _call_claude(content, log_fn)


# ─── COUCHE ANNÉE ────────────────────────────────────────────────────────────

def analyse_annee(syntheses_trimestre, config, log_fn):
    if not syntheses_trimestre:
        return "Aucune synthèse trimestrielle cette année."

    base_prompt = config.get("analyse_prompt", "")
    trim_txt = ""
    for s in syntheses_trimestre:
        trim_txt += f"\n--- {s['date']} ---\n{s['analyse']}\n"

    content = f"""{base_prompt}

Tu reçois les synthèses trimestrielles de l'année ({len(syntheses_trimestre)} trimestres).
Ton rôle : BILAN ANNUEL — transformations profondes, bascules historiques, vision long terme.

{trim_txt}

Produis un bilan annuel en français :

1. **TRANSFORMATIONS DE L'ANNÉE** : les 3-5 changements majeurs qui marqueront l'histoire
2. **CHRONOLOGIE ANNUELLE** : les dates clés de l'année
3. **BASCULES** : ce qui était vrai en janvier et ne l'est plus en décembre
4. **CARTE DES FORCES** : état des lieux des acteurs et de leurs positions
5. **CE QUI A SURPRIS** : événements inattendus qui ont changé la donne
6. **TENDANCES LONGUES** : ce qui se dessine pour les 2-3 prochaines années
7. **RECOMMANDATIONS** : ce qu'un citoyen/professionnel devrait savoir et surveiller
8. **MOTS-CLÉS** : 30+ tags

Maximum 1500 mots."""

    log_fn(f"  Analyse ANNÉE — {len(syntheses_trimestre)} trimestres...")
    return _call_claude(content, log_fn)


# ─── COUCHE CUMUL (mémoire progressive) ──────────────────────────────────────

def analyse_cumul(cumul_precedent, synthese_semaine, config, log_fn):
    base_prompt = config.get("analyse_prompt", "")

    cumul_txt = cumul_precedent or "(Première semaine — pas de cumul précédent)"

    content = f"""{base_prompt}

Tu es la MÉMOIRE CUMULATIVE de cette veille. Tu reçois :
1. Le cumul précédent (tout ce qui a été observé jusqu'ici)
2. La synthèse de la nouvelle semaine

CUMUL PRÉCÉDENT :
{cumul_txt}

NOUVELLE SEMAINE :
{synthese_semaine}

Ton rôle : METTRE À JOUR le cumul en intégrant les nouvelles informations.

Produis le nouveau cumul en français :

1. **NARRATIF GLOBAL** : résumé de tout ce qui s'est passé depuis le début (mis à jour)
2. **FILS ROUGES** : les sujets récurrents semaine après semaine (avec première et dernière apparition)
3. **SIGNAUX QUI MONTENT** : sujets dont la fréquence ou l'intensité augmente
4. **SIGNAUX QUI DESCENDENT** : sujets qui sortent du radar
5. **NOUVEAUTÉS** : ce qui apparaît pour la première fois cette semaine
6. **TIMELINE CONDENSÉE** : les 10-20 dates les plus importantes depuis le début
7. **MOTS-CLÉS CUMULÉS** : tous les tags importants depuis le début

IMPORTANT : ce document sera relu la semaine prochaine comme base. Il doit être auto-suffisant et complet.
Maximum 1200 mots."""

    log_fn(f"  Analyse CUMUL...")
    return _call_claude(content, log_fn)
