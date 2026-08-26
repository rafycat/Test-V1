"""
main.py — orchestrateur du pipeline de screening.

Déroulé :
1. Découverte  : INSEE (créations récentes par NAF cible)
2. Enrichissement : Pappers (financials, dirigeants, signal levée)
                     + INPI (signal brevet/marque)
3. Qualification : score_and_rank.qualify() — filtres durs + scoring
4. Persistance  : store.py — dédoublonnage, on ne ressort que le NOUVEAU
5. Export       : CSV horodaté dans data/exports/

Le volet presse (search_press.py) n'est PAS appelé ici : en Mode A, c'est
l'agent Claude Code qui pilote la recherche presse en interactif (voir
README.md et run_weekly.sh) et vient enrichir les résultats de ce script.

Usage :
    python3 scripts/main.py

Pré-requis : variables d'environnement INSEE_API_KEY, PAPPERS_API_KEY,
(INPI_API_KEY optionnel) — voir .env.example.
"""
from __future__ import annotations

import csv
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import store
import score_and_rank
import fetch_entreprises_gouv
import fetch_pappers

EXPORTS_DIR = Path(__file__).resolve().parent.parent / "data" / "exports"


def run() -> list[dict]:
    conn = store.get_connection()
    new_or_updated = []

    print("→ Découverte via l'API publique Recherche d'Entreprises (gratuite, sans clé)...")
    candidates = fetch_entreprises_gouv.run_all_sectors()
    print(f"  {len(candidates)} sociétés candidates brutes (avant filtres THESIS.md)")

    pappers_available = bool(os.environ.get("PAPPERS_API_KEY"))
    if not pappers_available:
        print("  ℹ PAPPERS_API_KEY absent — enrichissement Pappers ignoré. "
              "Le CA et l'effectif viennent déjà de l'API gratuite ; seul le "
              "signal 'levée de fonds récente' (basé sur les augmentations de "
              "capital publiées au greffe) ne sera pas disponible ce run.")

    for candidate in candidates:
        siren = candidate.get("id")
        detected_signals = []

        if pappers_available:
            try:
                pappers_data = fetch_pappers.enrich_company(siren)
                enriched = fetch_pappers.to_common_schema(pappers_data)
                candidate.update({k: v for k, v in enriched.items() if v is not None})
                if fetch_pappers.has_recent_capital_increase(pappers_data):
                    detected_signals.append("recent_funding")
            except Exception as e:  # noqa: BLE001 — on continue le run même si une société échoue
                print(f"  ⚠ enrichissement Pappers échoué pour {siren}: {e}")

        qualified = score_and_rank.qualify(candidate, detected_signals)

        if not qualified["passed"]:
            continue

        is_new = store.upsert_company(conn, qualified)
        for sig in detected_signals:
            store.add_signal(conn, qualified["id"], sig, detail="", source="pipeline")

        if is_new:
            new_or_updated.append(qualified)

    print(f"→ {len(new_or_updated)} nouvelles sociétés qualifiées ce run")
    conn.close()
    return new_or_updated


def export_csv(companies: list[dict]) -> Path:
    EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M")
    out_path = EXPORTS_DIR / f"screening_{timestamp}.csv"

    fieldnames = [
        "id", "name", "country", "sector_guess", "naf_code", "creation_date",
        "employees", "revenue_eur", "score", "geo_priority",
        "detected_signals", "exclusion_reason",
    ]
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for c in companies:
            row = dict(c)
            row["detected_signals"] = ", ".join(c.get("detected_signals", []))
            writer.writerow(row)

    print(f"→ Export : {out_path}")
    return out_path


if __name__ == "__main__":
    results = run()
    if results:
        export_csv(results)
    else:
        print("Aucune nouvelle société qualifiée ce run.")
