#!/usr/bin/env python3
"""
Indemnité compensatrice de la hausse de la CSG (202209).

https://www.service-public.fr/particuliers/vosdroits/F34473

Son montant est propre à chaque agent (décret 2017-1889, art. 2) : pour un agent en poste
avant 2018, (rémunération brute de 2017 × 1,6702 % − contribution de solidarité − cotisation
maladie − contribution chômage de 2017) × 1,1053 ; pour un agent nommé depuis, 0,76 % de sa
première rémunération mensuelle brute d'un mois complet ; l'assiette : les éléments soumis à
la CSG. Chaque 1er janvier, il suit l'évolution de cette rémunération d'une année sur
l'autre, changement de quotité et congé maladie neutralisés (art. 5, version depuis le
1/1/2021 ; en 2019 et 2020, seulement à la hausse).
https://www.legifrance.gouv.fr/loda/id/JORFTEXT000036342240/2026-10-17/

bpaye ne refait pas ce calcul, qui demande la rémunération de 2017 ou du premier mois :
agent.toml donne le montant ([ic_csg], relevé sur les bulletins), et taux.toml n'en garde
qu'une valeur par défaut, pour l'agent qui ne le renseigne pas.
"""

import datetime as dt

import bpaye.config as config
from bpaye.classes import Ligne
from bpaye.config import BAREME, Bareme
from bpaye.fonctionnaire import Fonctionnaire

__all__ = [
    "DEBUT_IC_CSG",
    "grille",
    "indemnite_comp_csg",
]

grille = config.BAREME.load("indemnite_comp_csg")  # valeur par défaut du barème du paquet


# Décret 2017-1889 : l'indemnité compense la hausse de la CSG du 1/1/2018 ; rien avant.
DEBUT_IC_CSG = dt.date(2018, 1, 1)


def indemnite_comp_csg(
    date: dt.date, fonctionnaire: Fonctionnaire | None = None, bareme: Bareme = BAREME
) -> Ligne | None:
    if date < DEBUT_IC_CSG:
        return None
    propre = getattr(fonctionnaire, "ic_csg", None)
    montant = propre(date) if propre is not None else bareme.load("indemnite_comp_csg")(date)
    return Ligne(montant, "Indemnité compensatrice CSG", code=202209, classe="INDEM")
