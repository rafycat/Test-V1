"""
fetch_entreprises_gouv.py — découverte de sociétés françaises via l'API
publique "Recherche d'Entreprises" (recherche-entreprises.api.gouv.fr).

Pourquoi cette API plutôt que l'API Sirene INSEE brute :
- 100% gratuite, SANS clé, SANS création de compte
- Agrège Sirene (INSEE) ET le RNE (INPI) — donc un peu plus riche que Sirene seul
- Limite : 7 requêtes/seconde par IP (largement suffisant pour ce pipeline)

⚠️ Cette API ne filtre pas nativement de façon fiable sur l'âge ou l'effectif
exact dans tous les cas (les filtres avancés officiels — tranche_effectif_min,
etc. — n'ont pas pu être vérifiés en conditions réelles au moment de l'écriture
de ce script). Approche retenue : on récupère TOUT ce qui matche le code NAF,
puis on applique les filtres durs de THESIS.md côté client via
`score_and_rank.py`, qui est déjà testé indépendamment. C'est plus lent
(pagination complète par code NAF) mais beaucoup plus fiable.

⚠️ Ce script ne s'exécute PAS dans l'environnement où il a été rédigé (domaine
gouv.fr non accessible depuis ce sandbox) — à lancer depuis votre Claude Code
local ou tout environnement avec accès réseau sortant standard.

Avant un usage en volume, vérifiez la liste à jour des paramètres de filtrage
sur https://recherche-entreprises.api.gouv.fr/docs/ (certains filtres avancés
comme date_creation ou tranche_effectif_salarie peuvent avoir été ajoutés/
renommés depuis la rédaction de ce script).
"""
from __future__ import annotations

import time
import yaml
from pathlib import Path
from typing import Iterator

import requests

BASE_URL = "https://recherche-entreprises.api.gouv.fr/search"
RATE_LIMIT_PER_SEC = 5  # on reste sous la limite officielle de 7/s par prudence
MAX_PAGES_PER_NAF = 3  # garde-fou : évite de tout paginer sur un NAF trop large (temporairement réduit pour le premier test)

# Codes NAF "programmation informatique" / édition de logiciels — couvrent des
# dizaines de milliers de sociétés françaises et l'API gratuite ne renvoie pas
# activite_description pour les filtrer par mot-clé. Exclus du run principal ;
# à traiter plus tard par recherche textuelle dédiée.
GENERIC_SOFTWARE_NAF_CODES = {"6201Z", "5829C", "6311Z"}

CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"
with open(CONFIG_DIR / "naf_codes.yaml", encoding="utf-8") as f:
    NAF_CFG = yaml.safe_load(f)

# Table de conversion tranche d'effectif Sirene -> effectif numérique approximatif
# (voir doc officielle recherche-entreprises / Sirene)
TRANCHE_EFFECTIF_MIDPOINT = {
    "NN": 0, "00": 0, "01": 1, "02": 4, "03": 7,
    "11": 15, "12": 35, "21": 75, "22": 150,
    "31": 225, "32": 375, "41": 750, "42": 1500,
    "51": 3500, "52": 7500, "53": 15000,
}


def _all_target_naf_codes() -> dict[str, list[str]]:
    """Retourne {code_naf: [secteurs]} — plusieurs secteurs de THESIS.md peuvent
    cibler le même code NAF (ex: codes batteries en transition_energetique ET
    transport), donc un simple dict {code: secteur} perdrait les secteurs
    additionnels. Exclut les codes logiciel génériques (GENERIC_SOFTWARE_NAF_CODES)."""
    mapping: dict[str, list[str]] = {}
    for sector_key, sector_cfg in NAF_CFG.items():
        for code in sector_cfg["naf_codes"]:
            naf_code = code.replace(".", "")  # forme interne sans point, pour matcher GENERIC_SOFTWARE_NAF_CODES
            if naf_code in GENERIC_SOFTWARE_NAF_CODES:
                continue
            mapping.setdefault(naf_code, []).append(sector_key)
    return mapping


def _to_dotted_naf(naf_code_no_dot: str) -> str:
    """"3511Z" -> "35.11Z" — l'API attend le paramètre `activite_principale`
    au format pointé (vérifié empiriquement : `code_naf` n'existe pas et
    `activite_principale` sans point est rejeté avec la liste des valeurs
    valides, toutes pointées)."""
    return f"{naf_code_no_dot[:2]}.{naf_code_no_dot[2:]}"


def fetch_by_naf(naf_code_no_dot: str, per_page: int = 25) -> Iterator[dict]:
    """Pagine sur toutes les sociétés d'un code NAF donné (jusqu'à MAX_PAGES_PER_NAF)."""
    page = 1
    while page <= MAX_PAGES_PER_NAF:
        params = {
            "activite_principale": _to_dotted_naf(naf_code_no_dot),
            "page": page,
            "per_page": per_page,
        }
        resp = requests.get(BASE_URL, params=params, timeout=30)
        if resp.status_code == 429:
            time.sleep(2)
            continue
        resp.raise_for_status()
        payload = resp.json()

        for result in payload.get("results", []):
            yield result

        if page >= payload.get("total_pages", 1):
            break
        page += 1
        time.sleep(1 / RATE_LIMIT_PER_SEC)


def _normalize(result: dict, sector_key: str) -> dict:
    """Convertit un enregistrement de l'API vers le schéma commun du pipeline
    (même format que fetch_pappers.to_common_schema, pour rester compatible
    avec store.py et score_and_rank.py)."""
    finances = result.get("finances") or {}
    latest_year = max(finances.keys()) if finances else None
    revenue = finances.get(latest_year, {}).get("ca") if latest_year else None

    tranche = result.get("tranche_effectif_salarie")
    employees = TRANCHE_EFFECTIF_MIDPOINT.get(tranche) if tranche else None

    return {
        "id": result.get("siren"),
        "name": result.get("nom_complet") or result.get("nom_raison_sociale"),
        "country": "FR",
        "sector": sector_key,
        "naf_code": result.get("activite_principale"),
        "creation_date": result.get("date_creation"),
        "legal_form": result.get("nature_juridique"),  # code catégorie juridique INSEE
        "employees": employees,
        "revenue_eur": revenue,
        "activity_description": None,  # le libellé NAF n'est pas renvoyé par cette API ;
                                        # le matching mot-clé se fait donc surtout sur le nom
        "source": "recherche-entreprises.api.gouv.fr",
    }


def run_all_sectors() -> list[dict]:
    results = []
    naf_to_sectors = _all_target_naf_codes()
    total = len(naf_to_sectors)
    for i, (naf_code, sector_keys) in enumerate(naf_to_sectors.items(), start=1):
        print(f"[{i}/{total}] Code NAF {naf_code} ({', '.join(sector_keys)})...")
        try:
            for raw in fetch_by_naf(naf_code):
                for sector_key in sector_keys:
                    results.append(_normalize(raw, sector_key))
        except requests.exceptions.HTTPError as e:
            if e.response is not None and e.response.status_code == 400:
                print(f"  ⚠ Code NAF {naf_code} rejeté par l'API (400, probablement invalide) — "
                      f"ignoré, run poursuivi sur les codes restants : {e}")
                continue
            raise
    return results


if __name__ == "__main__":
    companies = run_all_sectors()
    print(f"{len(companies)} sociétés brutes récupérées (avant filtrage THESIS.md)")
    for c in companies[:10]:
        print(c["id"], c["name"], c["sector"], c["employees"], c["revenue_eur"])
