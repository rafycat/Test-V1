#!/usr/bin/env bash
# run_weekly.sh — orchestration complète du screening hebdomadaire.
#
# Deux étapes :
#   1. Pipeline batch pur Python (INSEE + Pappers + INPI + scoring + export CSV)
#   2. Volet presse piloté par Claude Code lui-même, qui sait faire du web_search
#      et raisonner sur les résultats — moins mécanique, donc confié à l'agent
#      plutôt qu'à du code batch rigide.
#
# Usage :
#   ./run_weekly.sh                  → exécution complète (batch + agent)
#   ./run_weekly.sh --batch-only      → étape 1 seule, sans appeler Claude Code
#
# Pour la planification :
#   crontab -e
#   0 8 * * 1 cd /chemin/vers/dealflow-screening && ./run_weekly.sh >> logs/run.log 2>&1

set -euo pipefail
cd "$(dirname "$0")"

if [ -f .env ]; then
  set -a
  source .env
  set +a
fi

echo "=== Screening deal flow EFI III — $(date -Iseconds) ==="

echo ""
echo "--- Étape 1/2 : pipeline batch (INSEE + Pappers + INPI) ---"
python3 scripts/main.py

if [ "${1:-}" = "--batch-only" ]; then
  echo "Mode --batch-only : volet presse ignoré."
  exit 0
fi

echo ""
echo "--- Étape 2/2 : volet presse (agent Claude Code) ---"

LATEST_CSV=$(ls -t data/exports/screening_*.csv 2>/dev/null | head -1 || true)

PROMPT="Exécute le screening presse hebdomadaire deal flow EFI III.

1. Lis config/naf_codes.yaml pour la liste des mots-clés sectoriels.
2. Pour chaque secteur, lance 2-3 recherches web_search ciblées sur les levées
   de fonds européennes récentes (derniers 7 jours) croisant ces mots-clés.
   Priorise les sources listées dans config/sources.yaml (press.target_outlets),
   en particulier sifted.eu et eu-startups.com qui couvrent bien le climat/deeptech
   européen sans paywall.
3. Pour chaque société repérée dans la presse, applique les filtres de THESIS.md :
   âge ≤ 20 ans, effectif ≤ 500, CA ≤ 150M€, pas de SPV mono-actif.
4. Croise avec le CSV du run batch de ce jour (${LATEST_CSV:-aucun}) pour éviter
   les doublons.
5. Produis un résumé au format défini dans THESIS.md §6 (Nom / Secteur / Pays /
   Score / Signal déclencheur / Résumé / Fit EFI III / Sources), trié par score
   décroissant, pour les sociétés NON déjà présentes dans le CSV batch.

Respecte les règles de copyright habituelles : pas de citation de plus de
15 mots par source, une seule citation par source."

if command -v claude >/dev/null 2>&1; then
  echo "→ Appel de Claude Code en mode headless..."
  claude -p "$PROMPT" | tee "data/exports/press_summary_$(date +%Y%m%d).md"
else
  echo "⚠ CLI 'claude' introuvable dans le PATH de cet environnement."
  echo "  Copiez le prompt ci-dessous dans une session Claude Code interactive :"
  echo "---"
  echo "$PROMPT"
  echo "---"
fi
