"""
VeilleNumerique — Consolidator
Stockage et lecture des synthèses JSON par couche.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path


COUCHES = ["jour", "semaine", "mois", "trimestre", "annee", "cumul"]


def _syntheses_dir(conteneur_path, couche):
    return conteneur_path / "syntheses" / couche


def _date_to_filename(couche, dt):
    """Génère le nom de fichier selon la couche et la date."""
    if couche == "jour":
        return dt.strftime("%Y-%m-%d") + ".json"
    elif couche == "semaine":
        return dt.strftime("%Y-W%W") + ".json"
    elif couche == "mois":
        return dt.strftime("%Y-%m") + ".json"
    elif couche == "trimestre":
        q = (dt.month - 1) // 3 + 1
        return f"{dt.year}-Q{q}.json"
    elif couche == "annee":
        return f"{dt.year}.json"
    elif couche == "cumul":
        return "cumul-" + dt.strftime("%Y-W%W") + ".json"
    return dt.strftime("%Y-%m-%d") + ".json"


def save_synthese(conteneur_path, couche, dt, analyse, metadata=None):
    """
    Sauvegarde une synthèse dans le dossier approprié.

    Args:
        conteneur_path: Path vers le conteneur
        couche: "jour", "semaine", "mois", "trimestre", "annee", "cumul"
        dt: datetime de la synthèse
        analyse: texte de l'analyse Claude
        metadata: dict optionnel {articles_count, sources, keywords_found, ...}

    Returns:
        Path du fichier créé
    """
    directory = _syntheses_dir(conteneur_path, couche)
    directory.mkdir(parents=True, exist_ok=True)

    filename = _date_to_filename(couche, dt)
    filepath = directory / filename

    data = {
        "date": dt.strftime("%Y-%m-%d"),
        "couche": couche,
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "analyse": analyse,
    }
    if metadata:
        data["metadata"] = metadata

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return filepath


def load_synthese(conteneur_path, couche, dt):
    """Charge une synthèse spécifique. Retourne None si inexistante."""
    directory = _syntheses_dir(conteneur_path, couche)
    filename = _date_to_filename(couche, dt)
    filepath = directory / filename

    if not filepath.exists():
        return None

    with open(filepath, encoding="utf-8") as f:
        return json.load(f)


def load_syntheses(conteneur_path, couche, date_debut, date_fin):
    """
    Charge toutes les synthèses d'une couche entre deux dates.

    Returns:
        list[dict] triée par date
    """
    directory = _syntheses_dir(conteneur_path, couche)
    if not directory.exists():
        return []

    results = []
    for filepath in sorted(directory.glob("*.json")):
        try:
            with open(filepath, encoding="utf-8") as f:
                data = json.load(f)
            synth_date = datetime.strptime(data["date"], "%Y-%m-%d")
            if date_debut <= synth_date <= date_fin:
                results.append(data)
        except (json.JSONDecodeError, KeyError, ValueError):
            continue

    return sorted(results, key=lambda x: x["date"])


def load_all_syntheses(conteneur_path, couche):
    """Charge toutes les synthèses d'une couche."""
    directory = _syntheses_dir(conteneur_path, couche)
    if not directory.exists():
        return []

    results = []
    for filepath in sorted(directory.glob("*.json")):
        try:
            with open(filepath, encoding="utf-8") as f:
                results.append(json.load(f))
        except (json.JSONDecodeError, KeyError):
            continue

    return sorted(results, key=lambda x: x.get("date", ""))


def load_latest_cumul(conteneur_path):
    """Charge le cumul le plus récent. Retourne None si aucun."""
    directory = _syntheses_dir(conteneur_path, "cumul")
    if not directory.exists():
        return None

    files = sorted(directory.glob("cumul-*.json"))
    if not files:
        return None

    with open(files[-1], encoding="utf-8") as f:
        return json.load(f)


def get_week_range(dt):
    """Retourne (lundi, dimanche) de la semaine contenant dt."""
    monday = dt - timedelta(days=dt.weekday())
    sunday = monday + timedelta(days=6)
    return monday, sunday


def get_month_range(dt):
    """Retourne (premier jour, dernier jour) du mois contenant dt."""
    first = dt.replace(day=1)
    if dt.month == 12:
        last = dt.replace(day=31)
    else:
        last = dt.replace(month=dt.month + 1, day=1) - timedelta(days=1)
    return first, last


def get_quarter_range(dt):
    """Retourne (premier jour, dernier jour) du trimestre contenant dt."""
    q = (dt.month - 1) // 3
    first = dt.replace(month=q * 3 + 1, day=1)
    if q == 3:
        last = dt.replace(month=12, day=31)
    else:
        last = dt.replace(month=(q + 1) * 3 + 1, day=1) - timedelta(days=1)
    return first, last
