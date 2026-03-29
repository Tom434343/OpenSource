#!/usr/bin/env python3
"""
VeilleNumerique — Orchestrateur multi-conteneur + pyramide de synthèses
Chaque conteneur = un sujet de veille indépendant avec sa propre pyramide.
Cron : tous les jours à 22h
Usage : python3 veille.py [--test] [--no-email] [--conteneur ID]
"""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Engine modules
from engine.fetcher import fetch_articles
from engine.analyser import (
    analyse_jour, analyse_semaine, analyse_mois,
    analyse_trimestre, analyse_annee, analyse_cumul
)
from engine.consolidator import (
    save_synthese, load_syntheses, load_latest_cumul,
    get_week_range, get_month_range, get_quarter_range
)
from engine.mailer import send_report, send_synthese_report
from engine.publisher import publish_and_push

# ─── CONFIG ──────────────────────────────────────────────────────────────────

SCRIPT_DIR = Path(__file__).parent
CONTENEURS_DIR = SCRIPT_DIR / "conteneurs"
LOG_FILE = SCRIPT_DIR / "veille.log"

# ─── LOGGING ─────────────────────────────────────────────────────────────────

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")

# ─── CONTENEURS ──────────────────────────────────────────────────────────────

def discover_conteneurs(filter_id=None):
    """Découvre tous les conteneurs actifs."""
    conteneurs = []
    if not CONTENEURS_DIR.exists():
        return conteneurs

    for d in sorted(CONTENEURS_DIR.iterdir()):
        config_file = d / "config.json"
        if not config_file.exists():
            continue
        try:
            with open(config_file, encoding="utf-8") as f:
                config = json.load(f)
            if not config.get("enabled", True):
                continue
            if filter_id and config.get("id") != filter_id:
                continue
            conteneurs.append((d, config))
        except (json.JSONDecodeError, KeyError) as e:
            log(f"ERREUR config {d.name}: {e}")

    return conteneurs

# ─── CONSOLIDATION AUTO ──────────────────────────────────────────────────────

def should_consolidate(couche, dt):
    """Détermine si une consolidation doit être lancée pour cette couche à cette date."""
    if couche == "jour":
        return True  # toujours
    elif couche == "semaine":
        return dt.weekday() == 6  # dimanche
    elif couche == "cumul":
        return dt.weekday() == 6  # dimanche (avec la semaine)
    elif couche == "mois":
        return dt.day == 1  # 1er du mois
    elif couche == "trimestre":
        return dt.day == 1 and dt.month in (1, 4, 7, 10)  # 1er du trimestre
    elif couche == "annee":
        return dt.day == 31 and dt.month == 12  # 31 décembre
    return False


def run_consolidation(conteneur_path, config, dt, no_email=False):
    """Exécute toutes les consolidations nécessaires et envoie les emails."""
    consolidations_done = []

    # ── SEMAINE (dimanche → synthèse des 7 jours)
    if should_consolidate("semaine", dt):
        monday, sunday = get_week_range(dt)
        jours = load_syntheses(conteneur_path, "jour", monday, sunday)
        if jours:
            week_num = dt.strftime("S%W")
            periode = f"{week_num} ({monday.strftime('%d/%m')} → {sunday.strftime('%d/%m/%Y')})"
            log(f"  Consolidation SEMAINE ({len(jours)} jours)...")
            analyse = analyse_semaine(jours, config, log)
            if analyse:
                meta = {"jours_count": len(jours), "periode": f"{monday.strftime('%Y-%m-%d')} → {sunday.strftime('%Y-%m-%d')}"}
                save_synthese(conteneur_path, "semaine", dt, analyse, meta)
                consolidations_done.append("semaine")
                if not no_email:
                    send_synthese_report("semaine", analyse, config, log, periode)

                # ── CUMUL (dimanche → cumul progressif)
                log(f"  Consolidation CUMUL...")
                prev_cumul = load_latest_cumul(conteneur_path)
                prev_text = prev_cumul["analyse"] if prev_cumul else None
                cumul_analyse = analyse_cumul(prev_text, analyse, config, log)
                if cumul_analyse:
                    save_synthese(conteneur_path, "cumul", dt, cumul_analyse)
                    consolidations_done.append("cumul")
                    # Pas d'email pour le cumul (document interne de travail)

    # ── MOIS (1er du mois → synthèse du mois précédent)
    if should_consolidate("mois", dt):
        prev_month_dt = dt - timedelta(days=1)  # dernier jour du mois précédent
        first, last = get_month_range(prev_month_dt)
        semaines = load_syntheses(conteneur_path, "semaine", first, last)
        if semaines:
            mois_label = prev_month_dt.strftime("%B %Y")
            log(f"  Consolidation MOIS ({len(semaines)} semaines)...")
            analyse = analyse_mois(semaines, config, log)
            if analyse:
                meta = {"semaines_count": len(semaines), "mois": prev_month_dt.strftime("%Y-%m")}
                save_synthese(conteneur_path, "mois", prev_month_dt, analyse, meta)
                consolidations_done.append("mois")
                if not no_email:
                    send_synthese_report("mois", analyse, config, log, mois_label)

    # ── TRIMESTRE (1er jan/avr/jul/oct → synthèse du trimestre précédent)
    if should_consolidate("trimestre", dt):
        prev_quarter_dt = dt - timedelta(days=1)
        first, last = get_quarter_range(prev_quarter_dt)
        mois_synth = load_syntheses(conteneur_path, "mois", first, last)
        if mois_synth:
            q = (prev_quarter_dt.month - 1) // 3 + 1
            trim_label = f"Q{q} {prev_quarter_dt.year}"
            log(f"  Consolidation TRIMESTRE ({len(mois_synth)} mois)...")
            analyse = analyse_trimestre(mois_synth, config, log)
            if analyse:
                meta = {"mois_count": len(mois_synth), "trimestre": f"{prev_quarter_dt.year}-Q{q}"}
                save_synthese(conteneur_path, "trimestre", prev_quarter_dt, analyse, meta)
                consolidations_done.append("trimestre")
                if not no_email:
                    send_synthese_report("trimestre", analyse, config, log, trim_label)

    # ── ANNÉE (31 déc → synthèse de l'année)
    if should_consolidate("annee", dt):
        first = dt.replace(month=1, day=1)
        last = dt
        trimestres = load_syntheses(conteneur_path, "trimestre", first, last)
        if trimestres:
            log(f"  Consolidation ANNÉE ({len(trimestres)} trimestres)...")
            analyse = analyse_annee(trimestres, config, log)
            if analyse:
                meta = {"trimestres_count": len(trimestres), "annee": str(dt.year)}
                save_synthese(conteneur_path, "annee", dt, analyse, meta)
                consolidations_done.append("annee")
                if not no_email:
                    send_synthese_report("annee", analyse, config, log, str(dt.year))

    return consolidations_done

# ─── MAIN ────────────────────────────────────────────────────────────────────

def main():
    test_mode = "--test" in sys.argv
    no_email = "--no-email" in sys.argv
    filter_id = None
    for i, arg in enumerate(sys.argv):
        if arg == "--conteneur" and i + 1 < len(sys.argv):
            filter_id = sys.argv[i + 1]

    now = datetime.now()

    log("=" * 60)
    log(f"VeilleNumerique démarré {'[TEST]' if test_mode else ''} {'[NO-EMAIL]' if no_email else ''}")

    conteneurs = discover_conteneurs(filter_id)
    if not conteneurs:
        log("Aucun conteneur actif trouvé.")
        return

    log(f"{len(conteneurs)} conteneur(s) actif(s)")

    for conteneur_path, config in conteneurs:
        cid = config.get("id", conteneur_path.name)
        log(f"\n{'─' * 40}")
        log(f"Conteneur : {config.get('name', cid)} [{cid}]")

        # 1. Fetch articles
        articles = fetch_articles(conteneur_path, config, log, test_mode)

        if not articles and not test_mode:
            log(f"  Aucun nouvel article — pas de synthèse jour.")
        else:
            # 2. Analyse jour
            analyse = analyse_jour(articles, config, log)

            # 3. Sauvegarder synthèse jour
            if analyse:
                meta = {
                    "articles_count": len(articles),
                    "alert_count": len([a for a in articles if a.get("alert")]),
                    "sources": list(set(a["source"] for a in articles)),
                    "articles": [
                        {
                            "source": a["source"],
                            "title": a["title"],
                            "link": a["link"],
                            "date": a.get("date", ""),
                            "alert": a.get("alert", False),
                        }
                        for a in articles
                    ],
                }
                filepath = save_synthese(conteneur_path, "jour", now, analyse, meta)
                log(f"  Synthèse JOUR sauvegardée → {filepath.name}")

            # 4. Email
            if no_email:
                print(f"\n{'=' * 60}")
                print(f"[{cid}] {analyse or 'Pas d analyse'}")
                print("=" * 60)
                for a in articles:
                    alert = "🚨" if a.get("alert") else "📰"
                    print(f"{alert} [{a['source']}] {a['title']}")
            else:
                send_report(articles, analyse, config, log)

        # 5. Consolidations automatiques + emails par couche
        consolidations = run_consolidation(conteneur_path, config, now, no_email)
        if consolidations:
            log(f"  Consolidations effectuées : {', '.join(consolidations)}")

    # 6. Publication GitHub
    if not no_email:
        log(f"\n{'─' * 40}")
        log("Publication GitHub...")
        publish_and_push(log)

    log(f"\n{'=' * 60}")
    log("VeilleNumerique terminé.")


if __name__ == "__main__":
    main()
