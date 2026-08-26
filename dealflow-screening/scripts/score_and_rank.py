"""
score_and_rank.py — applique les filtres d'exclusion et le scoring de THESIS.md
à une liste de sociétés candidates (issues de fetch_insee / fetch_inpi / fetch_pappers).

Ce module ne fait AUCUN appel réseau : il prend des dicts en entrée et renvoie
des dicts enrichis d'un score et d'une décision (retenue / exclue + raison).
"""
from __future__ import annotations

import re
import yaml
from datetime import date
from pathlib import Path
from typing import Optional

CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"

with open(CONFIG_DIR / "sources.yaml", encoding="utf-8") as f:
    SOURCES_CFG = yaml.safe_load(f)

with open(CONFIG_DIR / "naf_codes.yaml", encoding="utf-8") as f:
    NAF_CFG = yaml.safe_load(f)

CRITERIA = SOURCES_CFG["criteria"]
WEIGHTS = SOURCES_CFG["scoring"]["weights"]
MIN_SCORE = SOURCES_CFG["scoring"]["min_score_to_report"]

# Formes juridiques signalant quasi-systématiquement un SPV mono-actif.
SPV_LEGAL_FORMS = {f.upper() for f in SOURCES_CFG["criteria"]["exclude_legal_forms"]}

# Mots-clés dans la raison sociale qui trahissent souvent un véhicule mono-projet
# (ex: "Solaire du Moulin 3 SAS", "Parc Eolien de X") plutôt qu'une société opérante.
SPV_NAME_PATTERNS = [
    re.compile(r"\bparc\s+(éolien|solaire|eolien)\b", re.IGNORECASE),
    re.compile(r"\bcentrale\s+(solaire|photovoltaïque)\b", re.IGNORECASE),
    re.compile(r"\bSPV\b", re.IGNORECASE),
]

# Mots qui, à l'inverse, signalent un développeur de projets (à NE PAS exclure
# même si le nom ressemble à un véhicule projet) — voir THESIS.md §4.
PROJECT_DEVELOPER_HINTS = [
    "développement", "developpement", "developer", "energy", "énergie",
    "power", "renewables", "renouvelables",
]


def compute_age_years(creation_date: Optional[str]) -> Optional[float]:
    if not creation_date:
        return None
    try:
        y, m, d = (creation_date.split("-") + ["01", "01"])[:3]
        created = date(int(y), int(m or 1), int(d or 1))
    except (ValueError, IndexError):
        return None
    delta = date.today() - created
    return delta.days / 365.25


def is_likely_spv(company: dict) -> bool:
    """
    Heuristique : SPV mono-actif si (a) forme juridique typique (ex: SCI)
    OU (b) nom qui matche un pattern mono-projet SANS mention d'un profil
    "développeur" (portefeuille de projets) dans le nom ou l'activité déclarée.
    Reste une heuristique — à valider manuellement sur les cas ambigus.
    """
    legal_form = (company.get("legal_form") or "").upper()
    name = company.get("name", "")
    activity = (company.get("activity_description") or "").lower()

    if legal_form in SPV_LEGAL_FORMS:
        return True

    name_matches_spv = any(p.search(name) for p in SPV_NAME_PATTERNS)
    if not name_matches_spv:
        return False

    looks_like_developer = any(
        hint in name.lower() or hint in activity for hint in PROJECT_DEVELOPER_HINTS
    )
    return not looks_like_developer


def passes_hard_filters(company: dict) -> tuple[bool, Optional[str]]:
    """Filtres d'exclusion durs de THESIS.md §1 et §4. Retourne (ok, raison_si_exclu)."""
    age = compute_age_years(company.get("creation_date"))
    if age is not None and age > CRITERIA["max_age_years"]:
        return False, f"âge {age:.1f} ans > {CRITERIA['max_age_years']} ans"

    employees = company.get("employees")
    if employees is not None and employees > CRITERIA["max_employees"]:
        return False, f"effectif {employees} > {CRITERIA['max_employees']}"

    revenue = company.get("revenue_eur")
    if revenue is not None and revenue > CRITERIA["max_revenue_eur"]:
        return False, f"CA {revenue:,.0f}€ > {CRITERIA['max_revenue_eur']:,.0f}€"

    if is_likely_spv(company):
        return False, "SPV mono-actif présumé (voir heuristique is_likely_spv)"

    return True, None


def keyword_sector_match(company: dict) -> Optional[str]:
    """
    Renvoie le nom de secteur (clé naf_codes.yaml) si l'activité déclarée
    matche au moins un mot-clé sectoriel, sinon None.
    Sert de garde-fou pour les codes NAF larges (ex: 62.01Z, 01.xx).
    """
    text = " ".join(filter(None, [
        company.get("name", ""),
        company.get("activity_description", ""),
    ])).lower()

    for sector_key, sector_cfg in NAF_CFG.items():
        for kw in sector_cfg.get("keywords", []):
            if kw.lower() in text:
                return sector_key
    return None


def score_company(company: dict, detected_signals: list[str]) -> float:
    """
    Score composite basé sur les poids de sources.yaml §scoring.
    `detected_signals` est une liste de clés parmi WEIGHTS (ex: ["recent_funding"]).
    """
    return float(sum(WEIGHTS.get(sig, 0) for sig in detected_signals))


def qualify(company: dict, detected_signals: list[str]) -> dict:
    """
    Pipeline complet de qualification d'une société candidate.
    Renvoie le dict enrichi avec: passed (bool), exclusion_reason (str|None),
    sector_guess (str|None), score (float), geo_priority (int).
    """
    ok, reason = passes_hard_filters(company)
    result = dict(company)

    if not ok:
        result.update(passed=False, exclusion_reason=reason, score=0.0)
        return result

    sector_guess = company.get("sector") or keyword_sector_match(company)
    score = score_company(company, detected_signals)

    country = (company.get("country") or "").upper()
    if country in CRITERIA["geo_priority_1"]:
        geo_priority = 1
    elif country in CRITERIA["geo_priority_2"]:
        geo_priority = 2
    else:
        geo_priority = 3

    passed = sector_guess is not None and score >= MIN_SCORE

    result.update(
        passed=passed,
        exclusion_reason=None if passed else (
            "aucun secteur EFI III détecté" if sector_guess is None
            else f"score {score} < seuil {MIN_SCORE}"
        ),
        sector_guess=sector_guess,
        score=score,
        geo_priority=geo_priority,
        detected_signals=detected_signals,
    )
    return result


if __name__ == "__main__":
    # Auto-test rapide avec quelques cas représentatifs des règles THESIS.md
    samples = [
        dict(
            name="SolarDev Développement SAS", country="FR",
            creation_date="2019-03-01", employees=45, revenue_eur=8_000_000,
            legal_form="SAS",
            activity_description="Développeur de projets solaires photovoltaïques en France",
        ),
        dict(
            name="Parc Solaire de Beaulieu 2", country="FR",
            creation_date="2021-01-01", employees=1, revenue_eur=200_000,
            legal_form="SAS",
            activity_description="Exploitation d'une centrale solaire",
        ),
        dict(
            name="Vieille Chimie SA", country="FR",
            creation_date="1998-01-01", employees=300, revenue_eur=90_000_000,
            legal_form="SA", activity_description="Chimie industrielle hydrogène vert",
        ),
    ]
    for s in samples:
        q = qualify(s, detected_signals=["recent_funding", "headcount_growth"])
        print(f"{s['name']:35s} passed={q['passed']!s:5} reason={q.get('exclusion_reason')}")
