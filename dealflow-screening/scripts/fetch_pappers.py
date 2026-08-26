"""
fetch_pappers.py — enrichissement via l'API Pappers (financials, dirigeants,
augmentations de capital récentes = proxy de levée de fonds).

Deux modes d'usage possibles :

1. Depuis une session Claude Code INTERACTIVE : le connecteur MCP Pappers déjà
   actif sur le compte peut être appelé directement par l'agent, sans ce script
   (voir README.md §"Mode interactif vs mode batch").

2. En exécution BATCH (cron, ce script) : utiliser l'API REST Pappers classique
   avec une clé dédiée (PAPPERS_API_KEY dans .env), car les quotas du connecteur
   MCP sont pensés pour un usage conversationnel, pas pour boucler sur des
   centaines de sociétés.

⚠️ Non exécutable dans ce sandbox (api.pappers.fr non whitelisté) — à lancer
depuis votre environnement Claude Code local.
"""
from __future__ import annotations

import os
import yaml
from pathlib import Path

import requests

CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"
with open(CONFIG_DIR / "sources.yaml", encoding="utf-8") as f:
    CFG = yaml.safe_load(f)["pappers"]

API_KEY = os.environ.get("PAPPERS_API_KEY")


def _params(**extra) -> dict:
    if not API_KEY:
        raise RuntimeError("PAPPERS_API_KEY manquant — voir votre contrat Pappers pour une clé batch.")
    return {"api_token": API_KEY, **extra}


def enrich_company(siren: str) -> dict:
    """Récupère la fiche complète Pappers pour un SIREN : financials, dirigeants,
    forme juridique, capital social, dernière augmentation de capital."""
    url = f"{CFG['base_url']}/entreprise"
    resp = requests.get(url, params=_params(siren=siren), timeout=30)
    resp.raise_for_status()
    return resp.json()


def has_recent_capital_increase(pappers_data: dict, lookback_days: int = 365) -> bool:
    """
    Proxy de "levée de fonds récente" : une augmentation de capital publiée
    au greffe dans la fenêtre récente. Imparfait (ne capture pas les levées
    en obligations convertibles/BSA-AIR sans augmentation de capital immédiate)
    mais c'est le signal le plus fiable et systématique disponible via Pappers.
    """
    from datetime import date, timedelta
    since = date.today() - timedelta(days=lookback_days)
    for event in pappers_data.get("publications_bodacc", []):
        if event.get("type_avis", "").lower().startswith("modification") and event.get("date_parution"):
            try:
                event_date = date.fromisoformat(event["date_parution"])
            except ValueError:
                continue
            if event_date >= since:
                return True
    return False


def to_common_schema(pappers_data: dict) -> dict:
    """Convertit une fiche Pappers en schéma commun du pipeline (voir store.py)."""
    finances = (pappers_data.get("finances") or [{}])
    last_finance = finances[0] if finances else {}
    return {
        "id": pappers_data.get("siren"),
        "name": pappers_data.get("nom_entreprise") or pappers_data.get("denomination"),
        "country": "FR",
        "legal_form": pappers_data.get("forme_juridique"),
        "creation_date": pappers_data.get("date_creation"),
        "employees": pappers_data.get("effectif"),
        "revenue_eur": last_finance.get("chiffre_affaires"),
        "activity_description": pappers_data.get("libelle_code_naf") or pappers_data.get("objet_social"),
        "naf_code": pappers_data.get("code_naf"),
        "source": "pappers",
    }


if __name__ == "__main__":
    example_siren = os.environ.get("EXAMPLE_SIREN", "000000000")
    data = enrich_company(example_siren)
    print(to_common_schema(data))
    print("Levée récente probable :", has_recent_capital_increase(data))
