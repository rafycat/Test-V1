"""
fetch_inpi.py — signal "dépôt de brevet/marque récent" via l'API INPI (data.inpi.fr).

Ce signal sert surtout à ENRICHIR une société déjà repérée par ailleurs
(INSEE ou presse), pas à faire de la découverte pure — la recherche INPI
par secteur est moins fine que par NAF.

Auth : compte développeur gratuit sur data.inpi.fr -> jeton dans .env (INPI_API_KEY).

⚠️ Non exécutable dans ce sandbox (domaine non whitelisté) — à lancer depuis
votre environnement Claude Code local.
"""
from __future__ import annotations

import os
import yaml
from datetime import date, timedelta
from pathlib import Path

import requests

CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"
with open(CONFIG_DIR / "sources.yaml", encoding="utf-8") as f:
    CFG = yaml.safe_load(f)["inpi"]

API_KEY = os.environ.get("INPI_API_KEY")


def _headers() -> dict:
    if not API_KEY:
        raise RuntimeError("INPI_API_KEY manquant — voir data.inpi.fr pour un compte développeur.")
    return {"Authorization": f"Bearer {API_KEY}", "Accept": "application/json"}


def fetch_recent_patents(siren: str, lookback_days: int | None = None) -> list[dict]:
    """Dépôts de brevets récents pour une société donnée (par SIREN)."""
    lookback_days = lookback_days or CFG["lookback_days"]
    since = (date.today() - timedelta(days=lookback_days)).isoformat()

    url = f"{CFG['base_url']}/patents/search"
    params = {"applicant_siren": siren, "filed_after": since}
    resp = requests.get(url, headers=_headers(), params=params, timeout=30)
    resp.raise_for_status()
    return resp.json().get("results", [])


def fetch_recent_trademarks(siren: str, lookback_days: int | None = None) -> list[dict]:
    """Dépôts de marques récents — signal plus faible que le brevet mais utile
    pour repérer un lancement produit imminent."""
    lookback_days = lookback_days or CFG["lookback_days"]
    since = (date.today() - timedelta(days=lookback_days)).isoformat()

    url = f"{CFG['base_url']}/trademarks/search"
    params = {"applicant_siren": siren, "filed_after": since}
    resp = requests.get(url, headers=_headers(), params=params, timeout=30)
    resp.raise_for_status()
    return resp.json().get("results", [])


def enrich_with_ip_signals(companies: list[dict]) -> list[dict]:
    """
    Pour une liste de sociétés (avec `id` = SIREN), ajoute has_recent_patent /
    has_recent_trademark. Prévu pour être appelé APRÈS fetch_insee/fetch_pappers,
    pas en découverte primaire.
    """
    enriched = []
    for company in companies:
        siren = company.get("id")
        try:
            patents = fetch_recent_patents(siren) if siren else []
            trademarks = fetch_recent_trademarks(siren) if siren else []
        except requests.HTTPError:
            patents, trademarks = [], []
        company = dict(company)
        company["has_recent_patent"] = bool(patents)
        company["has_recent_trademark"] = bool(trademarks)
        enriched.append(company)
    return enriched


if __name__ == "__main__":
    # Exemple d'appel unitaire (nécessite INPI_API_KEY et un vrai SIREN)
    example_siren = os.environ.get("EXAMPLE_SIREN", "000000000")
    print(fetch_recent_patents(example_siren))
