"""
enrich_export.py — enrichit un export CSV/XLSX existant du pipeline avec :
  - Description activité (objet social, via INPI RNE)
  - Évolution du CA (historique comptes annuels, via INPI)
  - Croissance effectif (historique tranches, via INSEE Sirene V3)

Usage :
    python3 scripts/enrich_export.py data/exports/screening_20260826_0930.xlsx --top 50 --by ca

--by peut valoir : "ca" (CA actuel décroissant, défaut), "score", ou "first"
(les N premières lignes telles quelles, sans tri).

Nécessite INPI_USERNAME/INPI_PASSWORD et/ou INSEE_CLIENT_ID/INSEE_CLIENT_SECRET
dans .env — voir .env.example. Si un seul des deux est configuré, seules les
colonnes correspondantes sont enrichies (le script ne bloque pas sur l'autre).
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

import fetch_inpi
import fetch_insee_historique as fih


def select_rows(df: pd.DataFrame, top: int, by: str) -> pd.DataFrame:
    if by == "ca":
        return df.sort_values("CA (EUR)", ascending=False, na_position="last").head(top)
    if by == "score":
        return df.sort_values("Score", ascending=False, na_position="last").head(top)
    if by == "first":
        return df.head(top)
    raise ValueError(f"--by inconnu: {by} (attendu: ca, score, first)")


def enrich_row(siren: str) -> dict:
    result = {
        "Description activité": None,
        "CA historique (5 ans)": None,
        "Effectif historique (tranches)": None,
        "Ratio croissance effectif": None,
    }

    if fetch_inpi.is_configured():
        try:
            result["Description activité"] = fetch_inpi.get_objet_social(siren)
        except Exception as e:
            print(f"  [warn] objet social échoué pour {siren}: {e}")

        try:
            historique_ca = fetch_inpi.get_comptes_annuels_historique(siren)
            if historique_ca:
                result["CA historique (5 ans)"] = " | ".join(
                    f"{h['annee']}: {h['ca']:,.0f}€" if h.get("ca") is not None else f"{h['annee']}: n/d"
                    for h in historique_ca
                )
        except Exception as e:
            print(f"  [warn] comptes annuels échoués pour {siren}: {e}")

    if fih.is_configured():
        try:
            historique_eff = fih.get_effectif_historique(siren)
            if historique_eff:
                result["Effectif historique (tranches)"] = " | ".join(
                    f"{h['date_debut'][:4]}: ~{h['effectif_approx']}"
                    for h in historique_eff if h.get("date_debut") and h.get("effectif_approx") is not None
                )
                result["Ratio croissance effectif"] = fih.compute_growth_ratio(historique_eff)
        except Exception as e:
            print(f"  [warn] historique effectif échoué pour {siren}: {e}")

    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input_file", help="Fichier CSV ou XLSX à enrichir")
    parser.add_argument("--top", type=int, default=50, help="Nombre de lignes à enrichir (défaut 50)")
    parser.add_argument("--by", default="ca", choices=["ca", "score", "first"], help="Critère de sélection du top N")
    parser.add_argument("--output", default=None, help="Chemin de sortie (défaut: suffixe _enriched)")
    args = parser.parse_args()

    if not fetch_inpi.is_configured() and not fih.is_configured():
        print("⚠️  Ni INPI ni INSEE configurés dans .env — rien à enrichir. Voir .env.example.")
        sys.exit(1)

    input_path = Path(args.input_file)
    df = pd.read_excel(input_path) if input_path.suffix == ".xlsx" else pd.read_csv(input_path)

    subset = select_rows(df, args.top, args.by).copy()
    print(f"Enrichissement de {len(subset)} société(s) (critère: {args.by})...")

    enriched_columns = {
        "Description activité": [],
        "CA historique (5 ans)": [],
        "Effectif historique (tranches)": [],
        "Ratio croissance effectif": [],
    }

    for i, (_, row) in enumerate(subset.iterrows(), start=1):
        siren = str(row["SIREN"])
        print(f"  [{i}/{len(subset)}] {row['Nom']} ({siren})...")
        data = enrich_row(siren)
        for col in enriched_columns:
            enriched_columns[col].append(data[col])
        time.sleep(0.5)  # prudence sur le rate limit, à ajuster selon les quotas réels

    for col, values in enriched_columns.items():
        subset[col] = values

    output_path = Path(args.output) if args.output else input_path.with_stem(input_path.stem + "_enriched")
    if output_path.suffix != ".xlsx":
        output_path = output_path.with_suffix(".xlsx")
    subset.to_excel(output_path, index=False)
    print(f"\n✅ Export enrichi : {output_path}")


if __name__ == "__main__":
    main()
