# Screening deal flow EFI III — mise en route

Pipeline de sourcing automatisé pour EFI III : découverte via registres publics
(INSEE, INPI), enrichissement (Pappers), veille presse pilotée par l'agent,
qualification et scoring selon les critères de [`THESIS.md`](./THESIS.md).

⚠️ **Ce projet a été construit et testé avec des données simulées dans un
environnement sans accès réseau à l'INSEE/Pappers/INPI.** La logique métier
(filtres d'exclusion, scoring, dédoublonnage, export) est testée et validée
— voir `tests/test_pipeline_smoke.py`. Les appels réseau réels doivent être
faits depuis votre propre environnement Claude Code local, où le réseau
sortant vers ces domaines est disponible.

## 1. Installation

```bash
cd dealflow-screening
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

**Bonne nouvelle : la découverte France ne nécessite plus AUCUNE clé API.**
Le pipeline utilise désormais l'API publique gratuite `recherche-entreprises.api.gouv.fr`
(agrège Sirene/INSEE et le RNE/INPI, 7 requêtes/seconde, aucun compte requis).

Le reste de `.env` est optionnel :

| Clé | Où l'obtenir | Nécessaire ? |
|---|---|---|
| `PAPPERS_API_KEY` | contrat Pappers, clé batch dédiée (différente du connecteur MCP conversationnel) | Non — n'ajoute que le signal "levée de fonds récente" |
| `INPI_API_KEY` | data.inpi.fr, compte développeur gratuit | Non — n'ajoute que le signal "brevet/marque récent" |
| `SERPAPI_API_KEY` | optionnel, mode presse 100% batch sans agent | Non |

⚠️ **Fiabilité des filtres de l'API gratuite** : contrairement à Sirene V3 ou
Pappers, certains filtres avancés de `recherche-entreprises.api.gouv.fr`
(tranche d'effectif, date de création) n'ont pas pu être vérifiés en conditions
réelles au moment de l'écriture. Le pipeline contourne ce risque en récupérant
toutes les sociétés par code NAF puis en appliquant les filtres durs de
THESIS.md **côté client** (`score_and_rank.py`, déjà testé) plutôt que de
compter sur les paramètres de l'API. Avant un usage en volume, vérifiez la
liste à jour des paramètres sur https://recherche-entreprises.api.gouv.fr/docs/.

## 2. Vérifier que tout fonctionne AVANT de brancher les vraies clés

```bash
python3 tests/test_pipeline_smoke.py
```

Ce test utilise des sociétés fictives et ne fait **aucun appel réseau**. S'il
passe, la logique de filtrage/scoring/export est saine — vous pouvez alors
brancher les vraies API en confiance.

## 3. Premier run réel (une fois les clés renseignées)

```bash
python3 scripts/main.py
```

Regardez le CSV produit dans `data/exports/`. **Ce premier run sert de
calibrage** : vérifiez notamment les faux positifs de classification
sectorielle par mot-clé (ex : le mot "carbone", très générique, peut classer
une société dans le mauvais secteur — voir `scripts/score_and_rank.py::keyword_sector_match`).
Affinez `config/naf_codes.yaml` en conséquence avant de passer à l'automatisation.

## 4. Mode interactif vs mode batch — lequel utiliser pour Pappers ?

Vous avez déjà un connecteur **Pappers** actif sur votre compte Claude (MCP).
Deux façons de l'utiliser :

- **Interactif** (dans une conversation Claude, comme celle-ci) : demandez
  directement "enrichis-moi cette liste de SIREN via Pappers" — pratique pour
  une vérification ponctuelle ou un petit lot.
- **Batch** (ce projet, `scripts/fetch_pappers.py`) : pour boucler
  automatiquement sur des dizaines/centaines de sociétés chaque semaine, une
  clé API Pappers classique est préférable — les quotas du connecteur MCP
  sont dimensionnés pour un usage conversationnel, pas pour une boucle batch.

## 5. Volet presse : pourquoi ce n'est pas un script Python

`scripts/search_press.py` ne fait volontairement pas de scraping : il génère
les requêtes, mais l'exécution des recherches et la synthèse des résultats
sont confiées à l'agent Claude Code lui-même (`run_weekly.sh` construit le
prompt et appelle `claude -p`). Raisons :

- Le jugement "cette mention presse correspond-elle vraiment à la thèse
  EFI III" est mieux fait par un LLM qui lit `THESIS.md` que par une règle
  regex.
- Cela évite tout scraping de paywall (Les Échos, La Tribune) — on ne
  récupère que ce que web_search retourne publiquement.

## 6. Automatisation

```bash
crontab -e
# Tous les lundis à 8h :
0 8 * * 1 cd /chemin/absolu/vers/dealflow-screening && ./run_weekly.sh >> logs/run.log 2>&1
```

Ou, si vous préférez tout piloter depuis Claude Code sans cron système,
demandez à l'agent en session interactive de lancer `run_weekly.sh` en fin de
session avec une instruction de rappel pour la semaine suivante.

## 7. Pousser les résultats vers Affinity

Vous avez un connecteur Affinity actif. Une fois le CSV validé, demandez à
Claude Code (en interactif, avec le connecteur Affinity) de créer les
sociétés retenues sur une liste dédiée ("Sourcing EFI III — climat/industrie")
plutôt que de ressaisir à la main.

## 8. Structure du projet

```
dealflow-screening/
├── THESIS.md               # Critères de filtrage — source de vérité métier
├── README.md                # Ce fichier
├── requirements.txt
├── .env.example
├── run_weekly.sh             # Orchestration hebdomadaire (batch + agent)
├── config/
│   ├── naf_codes.yaml         # Codes NAF + mots-clés par sous-secteur EFI III
│   └── sources.yaml           # Paramètres API, seuils, pondérations de scoring
├── scripts/
│   ├── fetch_entreprises_gouv.py # Découverte GRATUITE : recherche-entreprises.api.gouv.fr
│   ├── fetch_inpi.py           # Enrichissement optionnel : brevets/marques récents
│   ├── fetch_pappers.py        # Enrichissement optionnel : signal levée de fonds
│   ├── search_press.py         # Génération des requêtes presse (Mode A/B)
│   ├── score_and_rank.py       # Filtres d'exclusion + scoring (applique THESIS.md)
│   ├── store.py                 # Persistance SQLite + dédoublonnage
│   └── main.py                  # Orchestrateur du pipeline batch
├── tests/
│   └── test_pipeline_smoke.py  # Test end-to-end sans réseau
└── data/
    ├── companies_seen.db        # Créé au premier run
    └── exports/                  # CSV horodatés
```

## 9. Prochaines itérations possibles

- Ajouter un connecteur North Data pour l'Allemagne (voir guide méthodologique
  précédent) une fois un budget/API confirmé.
- Affiner `is_likely_spv()` dans `score_and_rank.py` — c'est une heuristique,
  elle produira des faux positifs/négatifs à surveiller les premières semaines.
- Ajouter un export direct vers Notion (vous avez déjà ce connecteur) en
  parallèle du CSV, si vous préférez un tableau de bord partagé au CSV brut.
