"""
Test fumée du pipeline : vérifie que store -> score_and_rank -> export_csv
s'enchaînent correctement, SANS appeler aucune API externe (INSEE/Pappers/INPI
ne sont pas joignables depuis cet environnement de test).

Lancer : python3 tests/test_pipeline_smoke.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import store
import score_and_rank
import main as pipeline_main
from fetch_entreprises_gouv import _normalize, TRANCHE_EFFECTIF_MIDPOINT

# Échantillon réel récupéré le 2026-08-24 sur recherche-entreprises.api.gouv.fr
# (démontre que le connecteur gratuit sans clé fonctionne et que le parsing est correct)
REAL_API_SAMPLE = {
    "siren": "403052111", "nom_complet": "BOULANGERIES PAUL",
    "activite_principale": "10.71A", "date_creation": "1995-12-07",
    "nature_juridique": "5710", "tranche_effectif_salarie": "41",
    "finances": {"2023": {"ca": 75869141, "resultat_net": -5022746}},
}


def test_connecteur_gratuit_normalisation():
    normalized = _normalize(REAL_API_SAMPLE, sector_key="test")
    assert normalized["id"] == "403052111"
    assert normalized["employees"] == TRANCHE_EFFECTIF_MIDPOINT["41"]
    assert normalized["revenue_eur"] == 75869141
    # Société de 1995 -> doit être rejetée par le filtre d'âge THESIS.md
    qualified = score_and_rank.qualify(normalized, detected_signals=["recent_funding"])
    assert not qualified["passed"]
    assert "âge" in qualified["exclusion_reason"]
    print("✅ Connecteur gratuit (recherche-entreprises.api.gouv.fr) : normalisation + filtre âge OK")


MOCK_CANDIDATES = [
    dict(
        id="111111111", name="HeatNet Développement", country="FR",
        creation_date="2020-06-01", employees=60, revenue_eur=12_000_000,
        legal_form="SAS",
        activity_description="Développeur de réseaux de chaleur urbains bas-carbone",
    ),
    dict(
        id="222222222", name="Ferme Verticale du Nord", country="FR",
        creation_date="2022-01-01", employees=15, revenue_eur=1_500_000,
        legal_form="SAS",
        activity_description="Exploitation d'une ferme verticale agroécologique",
    ),
    dict(
        id="333333333", name="Centrale Solaire de Vezins", country="FR",
        creation_date="2021-01-01", employees=1, revenue_eur=300_000,
        legal_form="SAS",
        activity_description="Exploitation d'une centrale solaire",
    ),
    dict(
        id="444444444", name="Cabinet Conseil Généraliste", country="FR",
        creation_date="2019-01-01", employees=20, revenue_eur=3_000_000,
        legal_form="SAS",
        activity_description="Conseil en stratégie tous secteurs",
    ),
]


def run_smoke_test():
    # Nettoie la DB de test pour un run reproductible
    if store.DB_PATH.exists():
        store.DB_PATH.unlink()

    conn = store.get_connection()
    qualified_results = []

    for c in MOCK_CANDIDATES:
        q = score_and_rank.qualify(c, detected_signals=["recent_funding", "headcount_growth"])
        print(f"{c['name']:32s} passed={q['passed']!s:5} reason={q.get('exclusion_reason')}")
        if q["passed"]:
            store.upsert_company(conn, q)
            qualified_results.append(q)

    assert any(r["name"] == "HeatNet Développement" for r in qualified_results), \
        "Le développeur de projets aurait dû passer"
    assert not any(r["name"] == "Centrale Solaire de Vezins" for r in qualified_results), \
        "La SPV mono-actif n'aurait pas dû passer"
    assert not any(r["name"] == "Cabinet Conseil Généraliste" for r in qualified_results), \
        "Une activité hors thèse n'aurait pas dû passer"

    out_path = pipeline_main.export_csv(qualified_results)
    assert out_path.exists()
    print(f"\n✅ Test fumée OK — export : {out_path}")


if __name__ == "__main__":
    test_connecteur_gratuit_normalisation()
    run_smoke_test()
