"""
search_press.py — veille presse pour la détection de levées de fonds et de
mentions sectorielles.

IMPORTANT — ce module n'est PAS un scraper. Deux modes d'usage :

Mode A (recommandé) — session Claude Code interactive :
    L'agent Claude Code dispose nativement d'un outil web_search. Il n'a PAS
    besoin de ce script pour chercher : il suffit de lui donner les requêtes
    générées par `build_queries()` ci-dessous, et de lui demander d'exécuter
    chaque requête via son outil web_search intégré, puis de structurer les
    résultats. C'est l'usage prévu pour un run hebdomadaire piloté par un
    prompt (voir run_weekly.sh).

Mode B — exécution 100% batch sans agent (ex: appelé depuis un cron externe
    sans passer par `claude -p`) :
    Nécessite une clé API de recherche tierce (SerpAPI, Google CSE...) posée
    dans .env. Fonction `serpapi_search()` fournie à titre d'exemple.

Dans les deux cas : on ne récupère QUE les snippets publics retournés par le
moteur de recherche, jamais le contenu intégral d'un article sous paywall.
"""
from __future__ import annotations

import os
import yaml
from pathlib import Path

import requests

CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"
with open(CONFIG_DIR / "sources.yaml", encoding="utf-8") as f:
    CFG = yaml.safe_load(f)["press"]

with open(CONFIG_DIR / "naf_codes.yaml", encoding="utf-8") as f:
    NAF_CFG = yaml.safe_load(f)


def build_queries() -> list[str]:
    """
    Génère les requêtes de veille, une par secteur, en combinant un signal
    de levée avec les mots-clés sectoriels les plus discriminants.
    Ces requêtes sont faites pour être passées telles quelles à un outil
    web_search (court, 3-6 mots idéalement — ici on reste volontairement
    un peu plus long car destiné à une recherche presse ciblée).
    """
    queries = []
    for sector_key, sector_cfg in NAF_CFG.items():
        top_keywords = sector_cfg["keywords"][:3]  # les plus discriminants seulement
        for kw in top_keywords:
            queries.append(f'levée de fonds "{kw}" Europe {_this_month_label()}')
    return queries


def _this_month_label() -> str:
    from datetime import date
    return date.today().strftime("%B %Y")


def serpapi_search(query: str) -> list[dict]:
    """Mode B — nécessite SERPAPI_API_KEY dans .env et press.serpapi_enabled: true
    dans sources.yaml. Retourne une liste de {title, snippet, link, source}."""
    if not CFG.get("serpapi_enabled"):
        raise RuntimeError(
            "serpapi_enabled=false dans config/sources.yaml — soit activez-le "
            "avec une clé SERPAPI_API_KEY, soit utilisez le Mode A (agent Claude Code)."
        )
    api_key = os.environ.get("SERPAPI_API_KEY")
    if not api_key:
        raise RuntimeError("SERPAPI_API_KEY manquant dans .env")

    resp = requests.get(
        "https://serpapi.com/search",
        params={"q": query, "api_key": api_key, "hl": "fr", "num": 10},
        timeout=30,
    )
    resp.raise_for_status()
    results = resp.json().get("organic_results", [])
    return [
        {
            "title": r.get("title"),
            "snippet": r.get("snippet"),
            "link": r.get("link"),
            "source": r.get("source"),
        }
        for r in results
    ]


def filter_target_outlets(results: list[dict]) -> list[dict]:
    """Ne garde que les résultats provenant des médias listés dans sources.yaml
    (§press.target_outlets), pour prioriser la qualité de la source."""
    outlets = CFG["target_outlets"]
    return [r for r in results if any(o in (r.get("link") or "") for o in outlets)]


if __name__ == "__main__":
    for q in build_queries():
        print(q)
