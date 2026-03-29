"""
VeilleNumerique — Moteur RSS générique
Lit le config.json d'un conteneur, fetch les articles, gère le seen_articles.
"""

import feedparser
import json
import hashlib
from datetime import datetime, timezone, timedelta
from pathlib import Path


def _article_id(entry):
    return hashlib.md5((entry.get("link", "") + entry.get("title", "")).encode()).hexdigest()


def _load_seen(conteneur_path):
    seen_file = conteneur_path / "seen_articles.json"
    if seen_file.exists():
        with open(seen_file) as f:
            return set(json.load(f))
    return set()


def _save_seen(conteneur_path, seen):
    seen_file = conteneur_path / "seen_articles.json"
    with open(seen_file, "w") as f:
        json.dump(list(seen), f)


def fetch_articles(conteneur_path, config, log_fn, test_mode=False):
    """
    Fetch les articles RSS pour un conteneur donné.

    Args:
        conteneur_path: Path vers le dossier du conteneur
        config: dict chargé depuis config.json
        log_fn: fonction de log(msg)
        test_mode: si True, regarde 365 jours en arrière

    Returns:
        list[dict] — articles avec {source, title, link, summary, date, alert}
    """
    seen = _load_seen(conteneur_path)
    days_back = config.get("days_back", 1)
    cutoff = datetime.now(timezone.utc) - timedelta(days=days_back if not test_mode else 365)
    keywords = [kw.lower() for kw in config.get("keywords_alert", [])]

    new_articles = []
    new_ids = set()

    for source in config.get("sources", []):
        log_fn(f"  [{config['id']}] Fetching {source['name']}...")
        try:
            feed = feedparser.parse(source["url"])
            count = 0
            for entry in feed.entries[:20]:
                aid = _article_id(entry)
                if aid in seen:
                    continue

                pub = entry.get("published_parsed") or entry.get("updated_parsed")
                if pub:
                    pub_dt = datetime(*pub[:6], tzinfo=timezone.utc)
                    if pub_dt < cutoff:
                        continue

                title_lower = entry.get("title", "").lower()
                summary_lower = entry.get("summary", "").lower()
                text = title_lower + " " + summary_lower
                is_alert = any(kw in text for kw in keywords)

                new_articles.append({
                    "source": source["name"],
                    "title": entry.get("title", "Sans titre"),
                    "link": entry.get("link", ""),
                    "summary": entry.get("summary", "")[:500],
                    "date": entry.get("published", ""),
                    "alert": is_alert,
                })
                new_ids.add(aid)
                count += 1

            log_fn(f"    → {count} nouveaux articles")
        except Exception as e:
            log_fn(f"    ERREUR {source['name']}: {e}")

    seen.update(new_ids)
    _save_seen(conteneur_path, seen)

    log_fn(f"  [{config['id']}] Total : {len(new_articles)} nouveaux articles")
    return new_articles
