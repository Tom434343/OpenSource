#!/usr/bin/env python3
"""
exporter_conversation.py
Terminal Capture v3

Lit la conversation Claude Code (stockee en JSONL dans ~/.claude/projects/)
et genere :
  1. conversation_YYYYMMDD_HHMMSS.md  -> transcription complete
  2. JOURNAL.md                        -> entree pre-remplie par analyse automatique (dev/ops)
"""

import sys
import os
import re
import json
import argparse
from datetime import datetime
from pathlib import Path


# -- Encodage du chemin (identique a Claude Code) --------------------------

def encode_project_path(directory: str) -> str:
    return directory.replace("/", "-").replace(" ", "-")


# -- Recherche du fichier JSONL de la session ------------------------------

def trouver_conversation(projet_dir: str, start_epoch: int):
    encoded = encode_project_path(projet_dir)
    projects_dir = Path.home() / ".claude" / "projects" / encoded

    if not projects_dir.exists():
        return None

    jsonl_files = list(projects_dir.glob("*.jsonl"))
    if not jsonl_files:
        return None

    candidates = [f for f in jsonl_files if f.stat().st_mtime >= (start_epoch - 10)]
    if not candidates:
        candidates = jsonl_files

    return max(candidates, key=lambda f: f.stat().st_mtime)


# -- Lecture du JSONL ------------------------------------------------------

def lire_messages(jsonl_path):
    messages = []
    with open(jsonl_path, "r", encoding="utf-8") as f:
        for ligne in f:
            ligne = ligne.strip()
            if not ligne:
                continue
            try:
                messages.append(json.loads(ligne))
            except json.JSONDecodeError:
                continue
    return messages


# -- Formatage du contenu d'un message ------------------------------------

def extraire_texte(content) -> str:
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parties = []
        for bloc in content:
            if not isinstance(bloc, dict):
                continue
            if bloc.get("type") == "text":
                texte = bloc.get("text", "").strip()
                if texte:
                    parties.append(texte)
            elif bloc.get("type") == "tool_use":
                parties.append(f"*[Action : {bloc.get('name', 'outil')}]*")
        return "\n".join(parties)
    return ""


# -- Conversion JSONL -> Markdown ------------------------------------------

def convertir_en_markdown(messages, projet_nom: str, session_date: str) -> str:
    lignes = [
        f"# Conversation Claude Code — {projet_nom}",
        "",
        f"**Date** : {session_date}",
        "",
        "---",
        "",
    ]
    nb_echanges = 0

    for msg in messages:
        type_msg = msg.get("type", "")
        if type_msg == "user":
            texte = extraire_texte(msg.get("message", {}).get("content", ""))
            if texte:
                lignes += ["## Vous", "", texte, ""]
                nb_echanges += 1
        elif type_msg == "assistant":
            texte = extraire_texte(msg.get("message", {}).get("content", []))
            if texte:
                lignes += ["## Claude", "", texte, ""]
                nb_echanges += 1

    if nb_echanges == 0:
        lignes.append("*Aucun echange enregistre dans cette session.*")

    return "\n".join(lignes)


# -- Analyse automatique de la conversation (dev/ops) ---------------------

def analyser_conversation(markdown: str) -> dict:
    """
    Extrait les points cles depuis les sections Claude de la conversation.
    Adapte dev/ops : corrections, TODO, decisions techniques, fichiers modifies.
    """

    def clean(line: str) -> str:
        line = re.sub(r'\*\*([^*]+)\*\*', r'\1', line)
        line = re.sub(r'\*([^*]+)\*', r'\1', line)
        line = re.sub(r'`([^`]+)`', r'\1', line)
        line = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', line)
        line = re.sub(r'#+\s*', '', line)
        line = re.sub(r'\|', ' ', line)
        line = re.sub(r'\s+', ' ', line)
        return line.strip()

    def is_table_separator(line: str) -> bool:
        return bool(re.match(r'^\|[-\s|:]+\|$', line.strip()))

    def dedup(lst):
        seen, result = set(), []
        for item in lst:
            key = item.lower()[:60]
            if key not in seen:
                seen.add(key)
                result.append(item)
        return result

    def to_bullets(lst, max_items: int = 8):
        return dedup(lst)[:max_items]

    # Extraire uniquement le texte des blocs Claude
    claude_blocks = re.findall(
        r'## Claude\n\n(.*?)(?=\n## (?:Vous|Claude)|$)',
        markdown, re.DOTALL
    )
    claude_text = "\n".join(claude_blocks)

    corrections = []
    todos = []
    decisions = []
    fichiers = []

    for line in claude_text.split("\n"):
        stripped = line.strip()

        if not stripped:
            continue
        if is_table_separator(stripped):
            continue
        if stripped.startswith("*[Action"):
            continue

        cleaned = clean(stripped)
        if not cleaned or len(cleaned) < 5:
            continue

        # -- Corrections / Bugs fixes --
        if re.search(r'(\u2705|corrig[eé]|fix[eé]|r[eé]par[eé]|r[eé]solu)', stripped, re.I):
            corrections.append(cleaned[:120])

        # -- TODO / En attente --
        if re.search(r'(\u274C|TODO|[aà] faire|en attente|reste [aà]|manquant|pas encore)', stripped, re.I):
            todos.append(cleaned[:120])

        # -- Decisions techniques (lignes avec ->) --
        if "\u2192" in stripped or "->" in stripped:
            item = re.sub(r'^.*?(\u2192|->)\s*', '', cleaned).strip().strip("*").strip()
            if item and len(item) > 5:
                decisions.append(item[:120])

        # -- Fichiers modifies (chemins de fichiers) --
        # Pattern : /chemin/vers/fichier ou fichier.ext
        file_matches = re.findall(r'(?:^|\s)(/[a-zA-Z0-9_./-]+\.[a-zA-Z0-9]+)', stripped)
        for f in file_matches:
            if len(f) > 5:
                fichiers.append(f)

        file_matches2 = re.findall(r'(?:^|\s)([a-zA-Z0-9_-]+\.[a-zA-Z]{1,10})\b', stripped)
        for f in file_matches2:
            if len(f) > 3 and f not in ("e.g.", "i.e.", "etc.", "ex.", "vs."):
                fichiers.append(f)

    return {
        "corrections": to_bullets(corrections, 8),
        "todos": to_bullets(todos, 8),
        "decisions": to_bullets(decisions, 6),
        "fichiers": to_bullets(fichiers, 10),
    }


# -- Generation de l'entree JOURNAL.md ------------------------------------

def generer_entree_journal(
    projet_nom: str,
    conv_filename: str,
    session_date: str,
    analyse: dict,
) -> str:

    def section(titre: str, items, fallback: str = "- *a completer*") -> str:
        if items:
            bullets = "\n".join(f"- {item}" for item in items)
            return f"### {titre}\n\n{bullets}"
        return f"### {titre}\n\n{fallback}"

    blocs = [
        "\n---\n",
        f"## Session du {session_date}\n",
        f"**Projet** : {projet_nom}  ",
        f"**Transcription** : [{conv_filename}]({conv_filename})\n",
        section("Corrections / Bugs fixes", analyse["corrections"]),
        "",
        section("TODO / En attente", analyse["todos"]),
        "",
        section("Decisions techniques", analyse["decisions"]),
        "",
        section("Fichiers modifies", analyse["fichiers"]),
        "",
        "### Notes complementaires\n\n*a completer*\n",
    ]

    return "\n".join(blocs)


# -- Mise a jour du JOURNAL.md --------------------------------------------

def mettre_a_jour_journal(journal_path, entree: str, projet_nom: str):
    journal_path = Path(journal_path)
    journal_path.parent.mkdir(parents=True, exist_ok=True)

    if not journal_path.exists():
        journal_path.write_text(
            f"# JOURNAL — {projet_nom}\n" + entree, encoding="utf-8"
        )
        return

    contenu = journal_path.read_text(encoding="utf-8")
    lignes = contenu.split("\n", 1)
    if len(lignes) == 2:
        journal_path.write_text(
            lignes[0] + "\n" + entree + lignes[1], encoding="utf-8"
        )
    else:
        journal_path.write_text(contenu + entree, encoding="utf-8")


# -- Point d'entree -------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Export conversation Claude Code -> Markdown + JOURNAL.md"
    )
    parser.add_argument("--projet", required=True, help="Nom du projet")
    parser.add_argument("--projet-dir", required=True, help="Chemin du projet")
    parser.add_argument("--output", required=True, help="Fichier de sortie .md")
    parser.add_argument("--start-epoch", type=int, default=0, help="Timestamp debut session")
    args = parser.parse_args()

    session_date = datetime.now().strftime("%d/%m/%Y a %H:%M")
    conv_filename = os.path.basename(args.output)

    # 1. Trouver le fichier JSONL
    jsonl_path = trouver_conversation(args.projet_dir, args.start_epoch)
    if not jsonl_path:
        print(f"Attention : aucune conversation trouvee pour {args.projet_dir}")
        sys.exit(0)
    print(f"Conversation trouvee : {jsonl_path.name}")

    # 2. Lire et convertir en markdown
    messages = lire_messages(jsonl_path)
    markdown = convertir_en_markdown(messages, args.projet, session_date)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(markdown, encoding="utf-8")
    print(f"Transcription ecrite : {args.output}")

    # 3. Analyser la conversation pour pre-remplir le journal
    analyse = analyser_conversation(markdown)

    # 4. Generer et inserer l'entree dans JOURNAL.md
    entree = generer_entree_journal(args.projet, conv_filename, session_date, analyse)
    journal_path = output_path.parent / "JOURNAL.md"
    mettre_a_jour_journal(journal_path, entree, args.projet)
    print(f"Journal mis a jour : {journal_path}")


if __name__ == "__main__":
    main()
