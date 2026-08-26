# THESIS.md — Critères de screening deal flow EFI III

> Ce fichier est lu par l'agent à chaque exécution du screening. Toute modification des critères se fait ici, pas dans le code.

---

## 1. Cadre général

- **Fonds** : EFI III (Eurazeo Future Industries III)
- **Ticket** : €10–30M par société
- **Géographie** : ~2/3 Europe (priorité), ~1/3 reste du monde
- **Stade cible** : ouvert, du pré-seed au growth — le filtre de stade se fait par la taille, pas par le label de levée :
  - **Effectif** : 0 à 500 employés
  - **Revenus** : jusqu'à €150M de CA
  - Une société pré-revenus (R&D, deeptech en développement) reste éligible si elle respecte le critère d'effectif et le fit sectoriel.
- **Âge** : sociétés créées il y a **20 ans ou moins**. Au-delà, exclusion automatique (probable acteur mature déjà consolidé, hors profil VC).
- **IRR net cible** : 20%
- **Classification** : SFDR Article 8+ — la société doit avoir un impact climat/durabilité mesurable, pas seulement adjacent

**Filtre d'exclusion immédiat** : toute société sans lien direct avec la transition énergétique, l'industrie décarbonée, la mobilité durable, le bâtiment bas-carbone, les ressources critiques, l'agriculture régénérative ou l'eau est écartée, même si elle est autrement solide (hors thèse fonds).

**Note transverse — logiciel et digitalisation** : le logiciel n'est jamais un secteur en soi dans cette thèse, mais un vecteur transverse. Un éditeur de logiciel n'est retenu **que s'il sert directement un des 5 secteurs cibles** (ex : logiciel de gestion de l'énergie, SaaS de gestion technique du bâtiment, plateforme de digitalisation agricole, logiciel de pilotage de flotte électrique, outil de traçabilité supply chain bas-carbone). Un logiciel générique sans lien sectoriel explicite reste hors scope.

---

## 2. Sous-secteurs et codes NAF cibles (France)

*Codes indicatifs à valider avec vous — un code NAF trop large noie le signal (ex : ingénierie généraliste), donc chaque code ci-dessous doit rester couplé à un filtre de mots-clés sur l'objet social. Les mots-clés logiciel/digitalisation sont désormais intégrés dans chaque secteur plutôt que traités à part.*

### 2.1 Transition énergétique
**Définition élargie** : tous les modèles liés à l'énergie et à l'électricité — batteries, développeurs solaires, pompes à chaleur, réseaux de chaleur, chaleur industrielle, géothermie, nouveaux modèles de fusion nucléaire, nouveaux modèles de fourniture/gestion d'électricité, logiciels de gestion de l'énergie ou de gestion du bâtiment (énergétique).
*(ex. portefeuille : 1KOMMA5°, UrbanChain, PCG Power, Ambos Energy, Sunfire, PowerUs, Sonaura)*

| Code NAF | Libellé | Mots-clés (incl. logiciel/digital) |
|---|---|---|
| 35.11Z | Production d'électricité | solaire, éolien, PPA, autoconsommation, **développeur de projets solaires/éoliens** |
| 35.12Z / 35.13Z / 35.14Z | Transport / Distribution / Commerce d'électricité | réseau, smart grid, agrégation, **logiciel de gestion de l'énergie**, plateforme de fourniture d'électricité |
| 27.20Z | Fabrication de piles et accumulateurs | stockage batterie, BESS, **logiciel de gestion de batterie (BMS)** |
| 28.25Z | Équipements aérauliques et frigorifiques | pompe à chaleur, chauffage, géothermie, réseaux de chaleur |
| 35.30Z | Production et distribution de vapeur et d'air conditionné | chaleur industrielle, réseaux de chaleur urbains |
| 43.22B | Installation thermique et climatisation | rénovation énergétique, PAC, chaleur industrielle |
| 27.11Z / 27.12Z | Moteurs, transformateurs, matériel de distribution électrique | électrification, hardware réseau |
| 20.11Z | Chimie de base | hydrogène vert, électrolyseurs |
| 24.46Z / 20.13B | Élaboration/transformation de matières nucléaires | **fusion nucléaire, nouveaux modèles de production nucléaire** |
| 62.01Z / 58.29C | Programmation, édition de logiciels | **logiciel de gestion énergétique du bâtiment (GTB énergie), plateforme d'optimisation énergétique, SaaS pilotage réseau** |
| 46.69B | Commerce de gros matériel électrique | distribution équipements EnR |

### 2.2 Transport & Supply Chain
**Définition élargie** : mobilité électrique, électrification des flottes et des véhicules, mobilité durable sur tout mode (route, fleuve, mer, air), logistique et supply chain.
*(ex. portefeuille : Electra, Vay, Dance, Alt Mobility, Celcius, TransTRACK)*

| Code NAF | Libellé | Mots-clés (incl. logiciel/digital) |
|---|---|---|
| 29.10Z | Construction de véhicules automobiles | véhicule électrique |
| 29.32Z | Autres équipements automobiles | recharge, batteries véhicules |
| 30.11Z | Construction de navires et structures flottantes | **propulsion fluviale/maritime décarbonée, batterie marine** |
| 30.30Z | Construction aéronautique et spatiale | **aviation électrique/hydrogène, e-VTOL** |
| 49.41A / 49.41B | Transports routiers de fret | logistique décarbonée, flotte électrique |
| 50.xx | Transport fluvial et maritime | fret fluvial/maritime bas-carbone |
| 52.10A / 52.10B | Entreposage | chaîne du froid, cold chain |
| 52.29A / 52.29B | Organisation des transports, affrètement | logistique SaaS, **plateforme digitale de supply chain** |
| 62.01Z / 58.29C | Programmation, édition de logiciels | teledriving, autonomie, **logiciel de gestion de flotte (fleet management SaaS), plateforme de recharge, traçabilité logistique** |
| 77.11A / 77.11B | Location de véhicules | leasing EV, électrification de flotte en gestion |

### 2.3 Industrialisation & Solutions industrielles
**Définition élargie** : digitalisation et décarbonation de l'industrie, incluant robotique, économie circulaire, nouveaux matériaux.
*(ex. portefeuille : Materrup)*

| Code NAF | Libellé | Mots-clés (incl. logiciel/digital) |
|---|---|---|
| 23.51Z | Fabrication de ciment | ciment bas-carbone, matériaux biosourcés |
| 20.xx | Industrie chimique | chimie verte, biomatériaux, nouveaux matériaux |
| 24.xx / 25.xx | Métallurgie, fabrication de produits métalliques | recyclage acier, économie circulaire industrielle |
| 28.xx | Fabrication de machines et équipements | efficacité industrielle, décarbonation process, **robotique industrielle** |
| 28.99Z | Fabrication d'autres machines spécialisées | **robotique de production, automatisation** |
| 38.xx | Collecte, traitement des déchets, récupération | économie circulaire, recyclage industriel |
| 62.01Z / 63.11Z | Programmation, traitement de données | **jumeau numérique industriel, logiciel de pilotage de production décarbonée, plateforme d'économie circulaire (marketplace matières)** |

### 2.4 Bâtiment (Built Environment)
**Définition élargie** : construction, gestion, maintenance, opération et rénovation du bâtiment.
*(ex. portefeuille : GA Smart Building, Reneo, Aedifion, Witco, Swapp, Cove)*

| Code NAF | Libellé | Mots-clés (incl. logiciel/digital) |
|---|---|---|
| 41.20A / 41.20B | Construction de bâtiments | construction hors-site, modulaire |
| 43.xx | Travaux de construction spécialisés | isolation, rénovation, étanchéité |
| 71.11Z / 71.12B | Architecture, ingénierie, études techniques | BIM bas-carbone, conception énergétique |
| 81.10Z / 81.2x | Services de maintenance et d'entretien des bâtiments | **opération et maintenance bâtiment, facility management digitalisé** |
| 62.01Z / 58.29C | Programmation, édition de logiciels | proptech, **gestion technique du bâtiment (GTB), SaaS maintenance prédictive, logiciel de conception/rénovation assistée** |
| 68.20B | Location de logements | co-living, habitat partagé |

### 2.5 Ressources critiques, agriculture, eau, biodiversité
**Définition élargie** : minerais et systèmes d'extraction, modèles agricoles (opérationnels ou de digitalisation/intrants), gestion de l'eau, reforestation et biodiversité.
*(ex. portefeuille : NeoFarm, aDryada, BreezoMeter)*

| Code NAF | Libellé | Mots-clés (incl. logiciel/digital) |
|---|---|---|
| 08.xx / 07.xx | Industries extractives, extraction de minerais | minéraux critiques, **systèmes/technologies d'extraction** |
| 01.xx | Agriculture, production animale, sylviculture | agroécologie, agriculture régénérative, ferme verticale, exploitation agricole opérationnelle |
| 20.15Z | Fabrication de produits azotés et d'engrais | **intrants agricoles innovants, biostimulants** |
| 36.00Z | Captage, traitement, distribution d'eau | gestion de l'eau, dessalement |
| 37.00Z | Collecte et traitement des eaux usées | traitement eaux usées |
| 39.00Z | Dépollution, gestion des déchets | dépollution, séquestration carbone |
| 02.xx | Sylviculture et exploitation forestière | **reforestation, gestion forestière** |
| 62.01Z / 63.11Z | Programmation, traitement de données | **plateforme de digitalisation agricole, agritech data, monitoring biodiversité par satellite/capteurs, MRV carbone** |

**⚠️ À valider avec vous** : ces listes sont un point de départ. Je recommande un premier run de calibrage où l'on regarde les faux positifs générés par secteur avant de figer les codes définitifs.

---

## 3. Signaux positifs (scoring)

Chaque société repérée reçoit un score composite. Barème indicatif à ajuster :

| Signal | Poids | Source |
|---|---|---|
| Levée de fonds < 18 mois | Fort | Presse, Pappers (dépôts d'augmentation de capital) |
| Croissance d'effectifs marquée sur 12 mois | Fort | INSEE Sirene (évolution tranche d'effectif) |
| Dépôt de brevet récent | Moyen-Fort | INPI |
| Mention dans un classement sectoriel (French Tech Green20, Katapult, etc.) | Moyen | Presse |
| Clients B2B nommés / partenariats industriels | Moyen | Site société, presse |
| Présence dans un accélérateur/incubateur climat reconnu | Faible-Moyen | Presse, site accélérateur |
| Fondateur avec parcours precedent notable (exit, corporate reconnu) | Faible-Moyen | LinkedIn, presse |

## 4. Signaux d'exclusion

- **Âge > 20 ans** : exclusion automatique, quel que soit le dynamisme apparent.
- **Effectif > 500** ou **revenus > €150M** : hors profil taille, exclusion automatique.
- **SPV mono-actif** : société ad hoc portant un seul actif/projet (ex : une SPV dédiée à une seule centrale solaire, un seul immeuble) — exclusion, car ce n'est pas une plateforme/entreprise scalable.
  - **Distinction importante** : un **développeur de projets** (société qui développe, structure et opère un portefeuille de projets — ex : plusieurs centrales solaires, plusieurs réseaux de chaleur) **n'est PAS exclu**, même si son modèle s'appuie sur des SPV par projet en aval. Le filtre porte sur la société mère/opérante, pas sur ses véhicules de financement projet.
- Activité principale hors thèse malgré un code NAF proche (ex : bureau d'études généraliste sans mention climat/énergie/industrie dans l'objet social, logiciel générique sans lien sectoriel)
- Effectif stagnant ou en déclin marqué sans autre signal positif (levée, brevet, contrat)
- Hors zone géographique prioritaire sans argument fort de qualité

---

## 5. Pondération géographique

- **Priorité 1** : France, Allemagne, UK, Benelux, pays nordiques
- **Priorité 2** : reste Europe (Espagne, Italie, Europe centrale)
- **Priorité 3** : hors Europe — uniquement si signal exceptionnel (aligné sur le tiers rest-of-world du fonds)

---

## 6. Format de sortie attendu

Pour chaque société qualifiée, l'agent produit :

```
[Nom société] — [Sous-secteur EFI III] — [Pays]
Score : X/10
Stade estimé : [pré-seed/seed/Series A/B/C]
Signal déclencheur : [ex: "Levée €12M annoncée le [date], NAF 35.11Z"]
Résumé activité (2 lignes)
Fit EFI III : [1 phrase — pourquoi/pourquoi pas]
Source(s) : [liens]
```

---

## 7. Points ouverts à trancher ensemble

1. Faut-il pondérer différemment les 5 sous-secteurs (ex : priorité renforcée sur Bâtiment ou Ressources critiques, moins denses dans votre portefeuille actuel) ?
2. Fréquence du run : hebdomadaire ou bi-mensuelle ?
3. Faut-il exclure explicitement les niches déjà bien couvertes par votre portefeuille actuel (ex : encore un acteur EV charging France) ou au contraire les prioriser pour du bolt-on ?
4. Avec l'élargissement du critère de stade (0-500 employés, jusqu'à €150M de CA), le volume de sociétés remontées par le screening va mécaniquement augmenter — voulez-vous un score minimum de coupure pour ne recevoir que le top X par run, ou préférez-vous voir l'exhaustif et trier vous-même ?
