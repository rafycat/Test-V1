"""
fetch_insee_historique.py — historique de la tranche d'effectif salarié via
l'API Sirene V3 (INSEE), gratuite avec un compte sur portail-api.insee.fr.

Contrairement à recherche-entreprises.api.gouv.fr (qui ne renvoie que la
tranche d'effectif la PLUS RÉCENTE), l'API Sirene V3 expose l'historique
complet des périodes d'une unité légale via `periodesUniteLegale`, ce qui
permet de reconstruire une courbe de croissance d'effectif approximative
(par tranche, pas en valeur exacte — c'est aussi une limite chez Pappers,
qui s'appuie sur la même source Sirene pour cette donnée).
"""
from __future__ import annotations

import os
import time
from typing import Optional

import requests

TOKEN_URL = "https://api.insee.fr/token"
SIRENE_BASE_URL = "https://api.insee.fr/entreprises/sirene/V3.11/siren"

CLIENT_ID = os.environ.get("INSEE_CLIENT_ID")
CLIENT_SECRET = os.environ.get("INSEE_CLIENT_SECRET")

_token_cache: dict = {"value": None, "expires_at": 0}

# Table de conversion tranche Sirene -> effectif médian approximatif
# (identique à celle de fetch_entreprises_gouv.py, gardée cohérente ici)
TRANCHE_EFFECTIF_MIDPOINT = {
    "NN": 0, "00": 0, "01": 1, "02": 4, "03": 7,
    "11": 15, "12": 35, "21": 75, "22": 150,
    "31": 225, "32": 375, "41": 750, "42": 1500,
    "51": 3500, "52": 7500, "53": 15000,
}


def is_configured() -> bool:
    return bool(CLIENT_ID and CLIENT_SECRET)


def _get_token() -> Optional[str]:
    if _token_cache["value"] and time.time() < _token_cache["expires_at"]:
        return _token_cache["value"]
    if not is_configured():
        return None

    resp = requests.post(
        TOKEN_URL,
        data={"grant_type": "client_credentials"},
        auth=(CLIENT_ID, CLIENT_SECRET),
        timeout=30,
    )
    resp.raise_for_status()
    payload = resp.json()
    _token_cache["value"] = payload["access_token"]
    _token_cache["expires_at"] = time.time() + payload.get("expires_in", 3600) - 60
    return _token_cache["value"]


def get_effectif_historique(siren: str) -> list[dict]:
    """
    Retourne l'historique des tranches d'effectif d'une unité légale :
    [{"date_debut": "2022-01-01", "tranche": "21", "effectif_approx": 75}, ...]
    trié du plus ancien au plus récent. Liste vide si non configuré ou
    société non trouvée.
    """
    token = _get_token()
    if not token:
        return []

    resp = requests.get(
        f"{SIRENE_BASE_URL}/{siren}",
        headers={"Authorization": f"Bearer {token}"},
        timeout=30,
    )
    if resp.status_code == 404:
        return []
    resp.raise_for_status()
    data = resp.json()

    periodes = data.get("uniteLegale", {}).get("periodesUniteLegale", [])
    historique = []
    for periode in periodes:
        tranche = periode.get("trancheEffectifsUniteLegale")
        if not tranche:
            continue
        historique.append({
            "date_debut": periode.get("dateDebut"),
            "tranche": tranche,
            "effectif_approx": TRANCHE_EFFECTIF_MIDPOINT.get(tranche),
        })

    return sorted(historique, key=lambda x: x["date_debut"] or "")


def compute_growth_ratio(historique: list[dict]) -> Optional[float]:
    """
    Ratio simple effectif le plus récent / effectif le plus ancien connu.
    None si historique insuffisant (< 2 points avec effectif non-nul).
    """
    points = [h["effectif_approx"] for h in historique if h["effectif_approx"]]
    if len(points) < 2 or points[0] == 0:
        return None
    return round(points[-1] / points[0], 2)


if __name__ == "__main__":
    if not is_configured():
        print("INSEE_CLIENT_ID/SECRET absents — module inactif (voir .env.example).")
    else:
        hist = get_effectif_historique("403052111")
        print(hist)
        print("Ratio de croissance:", compute_growth_ratio(hist))
