# Contribuer à bpaye

## La règle des données

Une valeur réglementaire (indice, durée, taux, montant, code) n'entre dans les tables
qu'avec sa source officielle à côté d'elle : texte, article, version lue, adresse
(Légifrance consolidé à la date voulue, Bulletin officiel, nomenclature de la DGFiP). Une
page du ministère ne sert qu'à défaut de texte, et le commentaire le dit. Ce qui n'a pas
été lu dans un texte est marqué « MANQUANT » ou « relevé sur les bulletins », jamais
deviné ni repris d'un blog ou d'un syndicat.

Les relevés sont dans `docs/verification/`. Pour les grilles, on met à jour le relevé,
puis :

```bash
uv run python scripts/genere_grilles.py
```

Une règle d'arrondi ou de calendrier qu'aucun texte ne donne se vérifie sur des
bulletins réels, et se documente (`docs/csg.md`, `docs/mgen.md`) ; jamais de montant
réel dans le dépôt, des exemples fictifs.

## Les modules

```text
src/bpaye/
taux.toml              Taux, montants et barèmes datés, chacun avec sa source
grilles.toml           Indices bruts, barème IB → IM, hors-échelle, durées d'échelon
reclassements.toml     Tableaux de reclassement (PPCR 2017, décret 2023-720)
vacances.toml          Vacances scolaires des zones A, B, C (scripts/maj_vacances.py)
codes.toml             Codes de rubrique du bulletin, chacun avec sa source DGFiP

classes.py             Types de base : Ligne, ListeLignes, Somme, Selection, Taux, Fixe…
paye.py                Bulletin et Paye : génération, événements, sélection
prevision.py           Net prévu mois par mois, par payeur
config.py              Chargement de taux.toml
codes.py               Chargement de codes.toml
utils.py               Dates et arrondis

pdf.py                 Lecture des bulletins PDF (PAY18E), par pdfplumber

grille.py              Grilles composées date par date (indices bruts × barème)
fonctionnaire.py       L'agent (corps, CPGE, ORS…), lecture de carriere.toml
reclassement.py        Reclassements par tables
hsa.py                 Heures supplémentaires (HSA, HSE, colles)
colles.py              Colles : déclarées, payées, prévues, dans un autre établissement
vacances.py            Semaines de cours d'une période, par zone
indemnites.py          IFP, ISOE, ISAE, prime d'attractivité, REP/REP+, transport, PSC…
indemnites_corps.py    Indemnités des CPE, PsyEN, documentalistes, directeurs d'école
indemnite_residence.py Indemnité de résidence
indemnite_comp_csg.py  Indemnité compensatrice de CSG
charges.py             CSG, CRDS, transfert primes-points, prélèvement à la source
charges_impots.py      Heures supplémentaires : réduction de cotisations, exonération
mgen.py                PSC santé (depuis mai 2026)
pc.py                  Pension civile
rafp.py                RAFP
point.py               Valeur du point, traitement brut et NBI
temps_partiel.py       Fraction de rémunération, surcotisation pour pension
gipa.py                Garantie individuelle du pouvoir d'achat
sft.py                 Supplément familial de traitement
ors.py                 Obligations réglementaires de service
format.py              Mise en forme textuelle des bulletins
protocoles.py          L'agent et le bulletin vus par les modules qui ne peuvent pas les importer
```

## Le style

- Python 3.11 au moins, annotations natives (`list[int]`, `X | None`), jamais
  `from __future__ import annotations` ni annotation en chaîne.
- ruff (lignes de 110 caractères, règles `E F I UP B SIM RUF N C4 PTH RET`), mypy sur
  `src`, corps des fonctions compris : toute fonction est annotée, sans `cast`.
- Imports en tête de fichier, absolus (`bpaye.…`), bibliothèque standard d'abord.
- `pathlib.Path` partout ; les tables se lisent depuis `Path(__file__).parent`.
- Chaque module déclare `__all__` ; sa docstring dit le pourquoi (le texte, le cas réel
  qui a fixé la règle), les commentaires aussi.
- Prose en français.
- Tests : pytest, un fichier par module, `test_<scénario>_<résultat attendu>`, agents
  fictifs.
