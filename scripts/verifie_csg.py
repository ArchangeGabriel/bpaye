#!/usr/bin/env python3
"""Vérifie sur des bulletins réels la règle de calcul de la CSG et de la CRDS (docs/csg.md).

L'assiette de chaque bulletin se reconstitue à partir de ses propres lignes, rappels (_R)
compris : les revenus soumis, moins le transfert prime-point, plus la part employeur de la
complémentaire santé (720580). La CRDS, que l'exonération des heures supplémentaires ne
touche pas, valide cette assiette : un bulletin où elle ne tombe pas juste est écarté et
signalé. Les heures supplémentaires exonérées se cumulent dans l'ordre de l'année civile,
sous le plafond de taux.toml ; leur CSG déductible passe en non déductible.

Sont comparées au bulletin : la CSG non déductible et la CSG déductible que calcule bpaye
(charges.csg_nonded, charges.csg, charges.crds), et, pour les mois sans heures exonérées,
deux règles simples de la CSG déductible (troncature et arrondi unique de 6,8 % du total).

Rien n'est écrit : les montants, personnels, ne s'affichent qu'à l'écran.

Usage, bpaye[pdf] installé :
    python scripts/verifie_csg.py DOSSIER_DES_BULLETINS agent.toml
"""

import datetime as dt
import math
import sys
import tomllib
from collections import defaultdict
from pathlib import Path

from bpaye.charges import _appliquer_abattement_csg, crds, csg, csg_nonded
from bpaye.charges_impots import _plafond_hs_exo
from bpaye.pdf import extract_bulletin, extract_sirets
from bpaye.utils import last_day_month

# Les lignes « à payer » soumises à la CSG ; les remboursements de frais (200039, 200041)
# n'y entrent pas.
REVENUS = ["101000", "102000", "104000", "200364", "200597", "202209", "202321", "202326", "202354"]
HEURES_SUP = ["200205", "200207", "200215", "200497", "200576"]
TPP, MGEN_EMPLOYEUR = "604970", "720580"


def arrondi(x: float) -> float:
    """Au centime, la moitié vers le haut, comme une paie."""
    return math.floor(x * 100 + 0.5 + 1e-9) / 100


def tronque(x: float) -> float:
    return math.floor(x * 100 + 1e-9) / 100


def main() -> None:
    dossier, agent = Path(sys.argv[1]), Path(sys.argv[2])
    with Path(agent).open("rb") as f:
        siret = tomllib.load(f).get("siret")  # facultatif : sans lui, tous les bulletins
    bulletins = []
    for chemin in sorted(dossier.glob("20*_BP_*.pdf")):
        if siret is None or siret in extract_sirets(chemin):
            d = extract_bulletin(chemin)
            if "401301" in d:
                bulletins.append((chemin.name[:7], d))

    cumul_exonere: dict[int, float] = defaultdict(float)
    regle_ok, ecartes = 0, []
    simples, n_simples = {"troncature": 0, "arrondi unique": 0, "deux arrondis": 0}, 0
    print(f"{'mois':8} {'HS exo.':>8} {'CSG ND calcul/bulletin':>25} {'CSG déd. calcul/bulletin':>25}")
    for mois, d in bulletins:
        annee, m = map(int, mois.split("_"))
        date = last_day_month(dt.date(annee, m, 1))

        def lu(code: str, d: dict = d) -> float:
            return d.get(code, 0.0) + d.get(code + "_R", 0.0)

        heures_sup = sum(lu(c) for c in HEURES_SUP)
        exonere = max(0.0, min(heures_sup, _plafond_hs_exo(date) - cumul_exonere[annee]))
        cumul_exonere[annee] += exonere
        brut = sum(lu(c) for c in REVENUS) + heures_sup - lu(TPP)
        mgen = d.get(MGEN_EMPLOYEUR, 0.0)
        if abs(-crds(brut, date, mgen, exonere).valeur - lu("401501")) > 0.001:
            ecartes.append(mois)
            continue
        nd = round(-csg_nonded(brut, date, mgen, exonere).valeur, 2)
        ded = round(-csg(brut, date, mgen, exonere).valeur, 2)
        regle_ok += abs(nd - lu("401201")) < 0.001 and abs(ded - lu("401301")) < 0.001
        salaire = _appliquer_abattement_csg(brut, date)

        def marque(calcul: float, reel: float) -> str:
            return f"{calcul:11.2f} {'✓' if abs(calcul - reel) < 0.001 else '✗'} {reel:11.2f}"

        print(f"{mois:8} {exonere:8.2f} {marque(nd, lu('401201'))} {marque(ded, lu('401301'))}")
        if exonere == 0:
            n_simples += 1
            total = salaire + mgen
            for regle, valeur in (
                ("troncature", tronque(0.068 * total)),
                ("arrondi unique", arrondi(0.068 * total)),
                ("deux arrondis", ded),
            ):
                simples[regle] += abs(valeur - lu("401301")) < 0.001
    retenus = len(bulletins) - len(ecartes)
    print(f"\n{retenus} bulletins à assiette reconstituée ; règle de bpaye juste sur {regle_ok}/{retenus}")
    print(
        f"CSG déductible des {n_simples} mois sans heures exonérées : "
        + ", ".join(f"{r} {n}/{n_simples}" for r, n in simples.items())
    )
    if ecartes:
        print(f"écartés, assiette non reconstituée (CRDS) : {', '.join(ecartes)}")


if __name__ == "__main__":
    main()
