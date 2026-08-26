"""
fetch_inpi.py — enrichissement optionnel via data.inpi.fr (RNE, brevets, marques).

Rôle : détecter les dépôts de brevets/marques récents d'une société identifiée
par ailleurs — signal précoce de sérieux technologique (THESIS.md §3), en
particulier pour l'Industrialisation et les Ressources critiques.

Auth : compte développeur gratuit sur data.inpi.fr. Placer les identifiants
dans .env sous INPI_API_KEY (ou INPI_USERNAME/INPI_PASSWORD selon le mode
d'auth en vigueur au moment de l'implémentation réelle — à vérifier sur la
doc officielle, l'API INPI a changé de mécanisme d'auth plusieurs fois).

Ce module est entièrement optionnel : le pipeline fonctionne sans.
"""
from __future__ import annotations

import os
from datetime import date, timedelta
from pathlib import Path
from typing import Optional

import requests
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

# NOTE : l'auth data.inpi.fr fonctionne par couple identifiant/mot de passe,
# pas par clé Bearer simple — le mécanisme exact (échange contre un token,
# durée de validité) est décrit dans la doc technique téléchargeable depuis
# votre espace "Mes accès API / SFTP" sur data.inpi.fr. Le code ci-dessous
# suppose un endpoint de login classique — à ajuster si la doc en dit autrement.
BASE_URL_RNE = "https://data.inpi.fr/api/rne"          # TODO vérifier le path exact dans la doc "formalités"
BASE_URL_COMPTES = "https://data.inpi.fr/api/comptes-annuels"  # TODO vérifier le path exact dans la doc "comptes annuels"
LOGIN_URL = "https://data.inpi.fr/login"                # TODO vérifier le endpoint d'auth réel

USERNAME = os.environ.get("INPI_USERNAME")
PASSWORD = os.environ.get("INPI_PASSWORD")
DEFAULT_LOOKBACK_DAYS = 90

_session_token: Optional[str] = None


def is_configured() -> bool:
    return bool(USERNAME and PASSWORD)


def _get_token() -> Optional[str]:
    """Authentification INPI — met en cache le token pour la durée du run.
    TODO : confirmer le format exact de la requête de login dans la doc
    technique (documentation technique API formalités_v4.0.pdf, section
    authentification)."""
    global _session_token
    if _session_token:
        return _session_token
    if not is_configured():
        return None

    resp = requests.post(
        LOGIN_URL,
        json={"username": USERNAME, "password": PASSWORD},
        timeout=30,
    )
    resp.raise_for_status()
    _session_token = resp.json().get("token")
    return _session_token


def get_objet_social(siren: str) -> Optional[str]:
    """
    Récupère la description de l'objet social depuis le RNE (Base RNE,
    formalités). Retourne None si non configuré ou société non trouvée.
    """
    token = _get_token()
    if not token:
        return None

    resp = requests.get(
        f"{BASE_URL_RNE}/{siren}",
        headers={"Authorization": f"Bearer {token}"},
        timeout=30,
    )
    if resp.status_code == 404:
        return None
    resp.raise_for_status()
    data = resp.json()

    # TODO : confirmer le chemin exact du champ dans le JSON retourné —
    # d'après la doc "Activités principales de l'objet social" existe côté
    # attestation d'immatriculation ; le nom du champ peut différer légèrement
    # dans l'API formalités brute (ex: peut être sous "formality" > "content"
    # > "personneMorale" > "identite" > "description" selon les versions).
    return (
        data.get("objet_social")
        or data.get("activitePrincipale", {}).get("description")
    )


def get_comptes_annuels_historique(siren: str, max_years: int = 5) -> list[dict]:
    """
    Récupère l'historique des comptes annuels non confidentiels (CA, résultat)
    pour une société, jusqu'à max_years exercices. Retourne une liste
    [{"annee": 2024, "ca": 1234567.0}, ...] triée du plus récent au plus ancien.
    Retourne [] si non configuré, société non trouvée, ou comptes confidentiels
    (rappel : ~45% des dépôts sont confidentiels, quelle que soit la source).
    """
    token = _get_token()
    if not token:
        return []

    resp = requests.get(
        f"{BASE_URL_COMPTES}/{siren}",
        headers={"Authorization": f"Bearer {token}"},
        params={"limit": max_years},
        timeout=30,
    )
    if resp.status_code == 404:
        return []
    resp.raise_for_status()
    data = resp.json()

    # TODO : confirmer le schéma exact — la doc distingue bilan (actif/passif)
    # et compte de résultat ; le chiffre d'affaires est typiquement une ligne
    # du compte de résultat (poste "FJ" ou équivalent en liasse fiscale).
    historique = []
    for exercice in data.get("comptes", [])[:max_years]:
        historique.append({
            "annee": exercice.get("dateClotureExercice", "")[:4],
            "ca": exercice.get("compteResultat", {}).get("chiffreAffaires"),
            "effectif": exercice.get("effectif"),  # certains dépôts incluent l'effectif moyen
        })
    return sorted(historique, key=lambda x: x["annee"], reverse=True)


def search_recent_filings(
    company_name: str, lookback_days: int = DEFAULT_LOOKBACK_DAYS
) -> list[dict]:
    """
    Recherche les dépôts de brevets et marques récents pour une société,
    par nom (l'API INPI ne recherche pas fiablement par SIREN pour les
    brevets/marques, contrairement au RNE).
    """
    if not is_configured():
        return []

    since = (date.today() - timedelta(days=lookback_days)).isoformat()
    resp = requests.get(
        BASE_URL,
        headers={"Authorization": f"Bearer {API_KEY}"},
        params={"q": company_name, "type": "brevets,marques", "depot_since": since},
        timeout=30,
    )
    if resp.status_code == 404:
        return []
    resp.raise_for_status()
    return resp.json().get("results", [])


def detect_patent_signal(company_name: str, lookback_days: int = DEFAULT_LOOKBACK_DAYS) -> bool:
    """Signal 'patent_recent' pour score_and_rank.py."""
    filings = search_recent_filings(company_name, lookback_days)
    return any(f.get("type") == "brevet" for f in filings)


if __name__ == "__main__":
    if not is_configured():
        print("INPI_API_KEY absent — module inactif (voir .env.example).")
    else:
        print(search_recent_filings("Materrup"))
