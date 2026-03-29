"""
VeilleNumerique — Publisher GitHub
Convertit les synthèses JSON en Markdown + génère les README index + git push.
"""

import json
import subprocess
from datetime import datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.parent
CONTENEURS_DIR = SCRIPT_DIR / "conteneurs"
PUBLISH_DIR = SCRIPT_DIR / "publication"

COUCHE_INFO = {
    "jour":       {"icon": "📰", "label": "Synthèses quotidiennes",    "desc": "Analyse quotidienne des articles du jour"},
    "semaine":    {"icon": "📊", "label": "Synthèses hebdomadaires",   "desc": "Tendances et fils rouges de la semaine"},
    "mois":       {"icon": "📅", "label": "Synthèses mensuelles",      "desc": "Dynamiques et trajectoires du mois"},
    "trimestre":  {"icon": "📈", "label": "Synthèses trimestrielles",  "desc": "Analyse stratégique du trimestre"},
    "annee":      {"icon": "🏆", "label": "Bilans annuels",            "desc": "Bilan et bascules de l'année"},
    "cumul":      {"icon": "🧠", "label": "Mémoire cumulative",        "desc": "Mémoire progressive mise à jour chaque semaine"},
}

CONTENEUR_ICONS = {
    "libertes-numeriques": "📰",
    "volatilite-marches": "⚡",
    "brics-multipolarite": "🌍",
}

COUCHES_ORDER = ["jour", "semaine", "mois", "trimestre", "annee", "cumul"]


def _load_config(conteneur_path):
    config_file = conteneur_path / "config.json"
    if config_file.exists():
        with open(config_file, encoding="utf-8") as f:
            return json.load(f)
    return {}


def _json_to_markdown(data, config_name=""):
    """Convertit une synthèse JSON en contenu Markdown."""
    date = data.get("date", "?")
    couche = data.get("couche", "?")
    analyse = data.get("analyse", "")
    generated = data.get("generated_at", "")
    meta = data.get("metadata", {})

    info = COUCHE_INFO.get(couche, {"icon": "📄", "label": couche})

    lines = []
    lines.append(f"# {info['icon']} {info['label'].rstrip('s')} — {date}")
    lines.append("")
    lines.append(f"**Conteneur** : {config_name}  ")
    lines.append(f"**Couche** : {couche}  ")
    lines.append(f"**Date** : {date}  ")
    if generated:
        lines.append(f"**Généré le** : {generated}  ")

    if meta:
        lines.append("")
        lines.append("## Métadonnées")
        lines.append("")
        if meta.get("articles_count"):
            lines.append(f"- **Articles** : {meta['articles_count']}")
        if meta.get("alert_count"):
            lines.append(f"- **Alertes** : {meta['alert_count']}")
        if meta.get("sources"):
            sources_str = ", ".join(meta["sources"]) if isinstance(meta["sources"], list) else str(meta["sources"])
            lines.append(f"- **Sources** : {sources_str}")
        if meta.get("periode"):
            lines.append(f"- **Période** : {meta['periode']}")
        if meta.get("jours_count"):
            lines.append(f"- **Jours analysés** : {meta['jours_count']}")
        if meta.get("semaines_count"):
            lines.append(f"- **Semaines analysées** : {meta['semaines_count']}")
        if meta.get("mois_count"):
            lines.append(f"- **Mois analysés** : {meta['mois_count']}")

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Analyse")
    lines.append("")
    lines.append(analyse)

    # Liste complète des articles (synthèses jour uniquement)
    articles_list = meta.get("articles", []) if meta else []
    if articles_list:
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append(f"## Sources — {len(articles_list)} articles")
        lines.append("")

        # Grouper par source
        by_source = {}
        for a in articles_list:
            src = a.get("source", "?")
            if src not in by_source:
                by_source[src] = []
            by_source[src].append(a)

        for src in sorted(by_source.keys()):
            src_articles = by_source[src]
            alert_count = sum(1 for a in src_articles if a.get("alert"))
            alert_tag = f" — {alert_count} alerte{'s' if alert_count > 1 else ''}" if alert_count else ""
            lines.append(f"### {src} ({len(src_articles)} articles{alert_tag})")
            lines.append("")
            for a in src_articles:
                tag = "🚨" if a.get("alert") else "📰"
                title = a.get("title", "Sans titre")
                link = a.get("link", "")
                date = a.get("date", "")
                date_str = f" · {date}" if date else ""
                if link:
                    lines.append(f"- {tag} [{title}]({link}){date_str}")
                else:
                    lines.append(f"- {tag} {title}{date_str}")
            lines.append("")

    lines.append("---")
    lines.append(f"*VeilleNumerique · {config_name} · Généré automatiquement par Claude AI*")

    return "\n".join(lines)


def publish_syntheses(log_fn):
    """Génère tous les fichiers Markdown + README index dans publication/."""
    PUBLISH_DIR.mkdir(parents=True, exist_ok=True)

    conteneurs_data = []

    for conteneur_dir in sorted(CONTENEURS_DIR.iterdir()):
        config = _load_config(conteneur_dir)
        if not config.get("enabled", True):
            continue

        cid = config.get("id", conteneur_dir.name)
        cname = config.get("name", cid)
        icon = CONTENEUR_ICONS.get(cid, "📄")

        pub_conteneur = PUBLISH_DIR / cid
        conteneur_stats = {}

        for couche in COUCHES_ORDER:
            src_dir = conteneur_dir / "syntheses" / couche
            if not src_dir.exists():
                continue

            pub_couche = pub_conteneur / couche
            pub_couche.mkdir(parents=True, exist_ok=True)

            files = sorted(src_dir.glob("*.json"))
            md_files = []

            for json_file in files:
                try:
                    with open(json_file, encoding="utf-8") as f:
                        data = json.load(f)

                    md_content = _json_to_markdown(data, cname)
                    md_file = pub_couche / (json_file.stem + ".md")
                    with open(md_file, "w", encoding="utf-8") as f:
                        f.write(md_content)

                    md_files.append({
                        "name": json_file.stem,
                        "date": data.get("date", json_file.stem),
                        "articles": data.get("metadata", {}).get("articles_count", ""),
                        "path": f"{couche}/{json_file.stem}.md",
                    })
                except (json.JSONDecodeError, KeyError):
                    continue

            conteneur_stats[couche] = md_files

            # README par couche
            if md_files:
                info = COUCHE_INFO[couche]
                couche_readme = [f"# {info['icon']} {info['label']} — {cname}\n"]
                couche_readme.append(f"{info['desc']}\n")
                couche_readme.append(f"| Date | Lien |")
                couche_readme.append(f"|------|------|")
                for mf in reversed(md_files):
                    extra = f" ({mf['articles']} articles)" if mf.get("articles") else ""
                    couche_readme.append(f"| {mf['date']} | [{mf['name']}.md]({mf['name']}.md){extra} |")
                couche_readme.append(f"\n---\n[← Retour {cname}](../README.md) · [← Index principal](../../README.md)")

                with open(pub_couche / "README.md", "w", encoding="utf-8") as f:
                    f.write("\n".join(couche_readme))

        # README par conteneur
        conteneur_readme = [f"# {icon} {cname}\n"]
        conteneur_readme.append(f"**ID** : `{cid}`\n")

        prompt = config.get("analyse_prompt", "")
        if prompt:
            first_line = prompt.split("\n")[0][:200]
            conteneur_readme.append(f"> {first_line}\n")

        conteneur_readme.append("## Synthèses disponibles\n")
        conteneur_readme.append("| Couche | Fichiers | Dernière |")
        conteneur_readme.append("|--------|:--------:|----------|")

        for couche in COUCHES_ORDER:
            info = COUCHE_INFO[couche]
            files = conteneur_stats.get(couche, [])
            count = len(files)
            last = files[-1]["date"] if files else "—"
            if count > 0:
                conteneur_readme.append(f"| {info['icon']} [{info['label']}]({couche}/README.md) | **{count}** | {last} |")
            else:
                conteneur_readme.append(f"| {info['icon']} {info['label']} | 0 | — |")

        sources = config.get("sources", [])
        if sources:
            conteneur_readme.append("\n## Sources\n")
            conteneur_readme.append("| Source | Langue |")
            conteneur_readme.append("|--------|--------|")
            for s in sources:
                conteneur_readme.append(f"| {s['name']} | {s.get('lang', '?')} |")

        conteneur_readme.append(f"\n---\n[← Index principal](../README.md)")

        with open(pub_conteneur / "README.md", "w", encoding="utf-8") as f:
            f.write("\n".join(conteneur_readme))

        conteneurs_data.append({
            "id": cid,
            "name": cname,
            "icon": icon,
            "stats": conteneur_stats,
        })

    # README principal
    now = datetime.now().strftime("%d/%m/%Y %H:%M")
    main_readme = [
        "# 🔍 VeilleNumerique\n",
        "Plateforme de veille RSS multi-sujets avec pyramide de synthèses IA.",
        "Chaque conteneur est un sujet de veille indépendant avec ses propres sources",
        "et sa propre pyramide de synthèses temporelles (jour → semaine → mois → trimestre → année + cumul).\n",
        f"**Dernière mise à jour** : {now}\n",
        "---\n",
        "## Conteneurs\n",
    ]

    for c in conteneurs_data:
        total = sum(len(files) for files in c["stats"].values())
        main_readme.append(f"### {c['icon']} [{c['name']}]({c['id']}/README.md)\n")

        main_readme.append("| Couche | Fichiers | Dernière |")
        main_readme.append("|--------|:--------:|----------|")
        for couche in COUCHES_ORDER:
            info = COUCHE_INFO[couche]
            files = c["stats"].get(couche, [])
            count = len(files)
            last = files[-1]["date"] if files else "—"
            if count > 0:
                main_readme.append(f"| {info['icon']} [{info['label']}]({c['id']}/{couche}/README.md) | **{count}** | {last} |")
            else:
                main_readme.append(f"| {info['icon']} {info['label']} | 0 | — |")
        main_readme.append("")

    # Stats globales
    total_all = sum(
        sum(len(files) for files in c["stats"].values())
        for c in conteneurs_data
    )
    main_readme.append("---\n")
    main_readme.append("## Statistiques globales\n")
    main_readme.append(f"- **Conteneurs actifs** : {len(conteneurs_data)}")
    main_readme.append(f"- **Total synthèses** : {total_all}")
    main_readme.append(f"- **Modèle IA** : Claude Haiku 4.5")
    main_readme.append(f"- **Mise à jour** : automatique (cron quotidien)\n")

    main_readme.append("## Pyramide de synthèses\n")
    main_readme.append("```")
    main_readme.append("                    ┌─────────┐")
    main_readme.append("                    │ ANNUELLE│  1/an")
    main_readme.append("                    └────┬────┘")
    main_readme.append("                 ┌───────┴───────┐")
    main_readme.append("                 │  TRIMESTRIELLE │  4/an")
    main_readme.append("                 └───────┬───────┘")
    main_readme.append("              ┌──────────┴──────────┐")
    main_readme.append("              │      MENSUELLE      │  12/an")
    main_readme.append("              └──────────┬──────────┘")
    main_readme.append("           ┌─────────────┴─────────────┐")
    main_readme.append("           │       HEBDOMADAIRE        │  52/an")
    main_readme.append("           └─────────────┬─────────────┘")
    main_readme.append("        ┌────────────────┴────────────────┐")
    main_readme.append("        │           QUOTIDIENNE           │  365/an")
    main_readme.append("        └─────────────────────────────────┘")
    main_readme.append("        + CUMUL PROGRESSIF (mémoire longue)")
    main_readme.append("```\n")
    main_readme.append("---\n")
    main_readme.append("*VeilleNumerique · VeilleNumerique · Généré automatiquement par Claude AI*")

    with open(PUBLISH_DIR / "README.md", "w", encoding="utf-8") as f:
        f.write("\n".join(main_readme))

    log_fn(f"  Publication : {total_all} synthèses Markdown générées dans publication/")
    return total_all


def git_push(log_fn):
    """Commit et push les changements dans publication/."""
    try:
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        subprocess.run(
            ["git", "add", "."],
            cwd=str(PUBLISH_DIR), capture_output=True, text=True
        )

        # Vérifier s'il y a des changements
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=str(PUBLISH_DIR), capture_output=True, text=True
        )
        if not result.stdout.strip():
            log_fn("  Git : aucun changement à publier")
            return True

        subprocess.run(
            ["git", "commit", "-m", f"Veille {now} — mise à jour automatique"],
            cwd=str(PUBLISH_DIR), capture_output=True, text=True
        )

        result = subprocess.run(
            ["git", "push"],
            cwd=str(PUBLISH_DIR), capture_output=True, text=True
        )
        if result.returncode == 0:
            log_fn(f"  Git : push OK")
            return True
        else:
            log_fn(f"  Git : ERREUR push — {result.stderr}")
            return False
    except Exception as e:
        log_fn(f"  Git : ERREUR — {e}")
        return False


def publish_and_push(log_fn):
    """Pipeline complet : génère le Markdown + commit + push."""
    total = publish_syntheses(log_fn)
    if total > 0:
        git_push(log_fn)
    return total
