"""Obligations réglementaires de service (ORS) : le maximum hebdomadaire d'un enseignant.

Elles fixent le taux des HSA (hsa.py) et, en CPGE, le code des colles de sa propre classe.

Hors CPGE, l'ORS est celle du corps : décret 2014-940, art. 2 I, depuis le 1/9/2015
(avant : décret 50-581, art. 1, « agrégés : quinze heures ; non agrégés : dix-huit
heures »). https://www.legifrance.gouv.fr/loda/id/JORFTEXT000029390906/2026-10-17/
Professeurs des écoles : décret 2008-775, art. 1 (24 heures).

En CPGE, elle dépend de la classe et de son effectif : plus de 35 élèves, de 20 à 35,
moins de 20. Décret 50-581, art. 6 (mathématiques, sciences physiques, sciences
naturelles) et art. 7 (philosophie, lettres, histoire-géographie, langues), modifiés par
le décret 2014-941 ; les chaires supérieures y sont soumises (décret 68-503, art. 6).
https://www.legifrance.gouv.fr/loda/id/LEGITEXT000006060582/2026-10-17/
Les règles des services partagés entre plusieurs classes ne sont pas modélisées : donner
alors l'ORS de la rentrée dans carriere.toml (``ors``).
"""

__all__ = [
    "CORPS_SANS_ORS",
    "ORS",
    "ORS_CORPS",
    "ORS_CPGE",
    "calc_ors",
    "calc_ors_single",
    "classe_effectif",
]

# Par type de classe : (plus de 35, de 20 à 35, moins de 20 élèves).
ORS_CPGE: dict[str, tuple[int, int, int]] = {
    # art. 6 : mathématiques spéciales et préparation ENS sciences expérimentales
    "sciences-2": (8, 9, 10),
    # art. 6 : mathématiques supérieures et classes assimilées
    "sciences-1": (9, 10, 11),
    # art. 6 : autres classes préparatoires
    "autres": (11, 12, 13),
    # art. 7 : première supérieure
    "lettres-2": (8, 9, 10),
    # art. 7 : lettres supérieures et classes assimilées
    "lettres-1": (9, 10, 11),
}

# L'ancienne table par année (1re, 2e), celle des classes scientifiques.
ORS = [list(ORS_CPGE["sciences-1"]), list(ORS_CPGE["sciences-2"])]

# Les CPE et les PsyEN n'enseignent pas : pas d'obligation de service d'enseignement
# (décret 2014-940, art. 1 : « personnels enseignants »), donc ni HSA ni colles.
CORPS_SANS_ORS = frozenset({"CPE", "PsyEN"})

# Second degré : décret 2014-940, art. 2 I. Premier degré : « un service d'enseignement de
# vingt-quatre heures hebdomadaires » (décret 2008-775, art. 1, version depuis le 1/4/2017,
# https://www.legifrance.gouv.fr/loda/id/JORFTEXT000019278548/2026-10-17/) ; un PE en SEGPA,
# EREA ou ULIS doit 21 h (décret 2014-940, art. 2 I) : le donner dans carriere.toml (``ors``).
ORS_CORPS: dict[str, int] = {
    "Agrégé": 15,
    "Certifié": 18,
    "PLP": 18,
    "PEPS": 20,
    "PE": 24,
}


def classe_effectif(n: int) -> int:
    if n > 35:
        return 0
    if 20 <= n <= 35:
        return 1
    return 2


def calc_ors_single(effectif: int, annee: int, type_classe: str = "sciences") -> int:
    """L'ORS en CPGE pour une classe de ``annee`` (1 ou 2), de ``type_classe``
    (« sciences », « lettres » ou « autres ») et d'``effectif`` élèves."""
    cle = "autres" if type_classe == "autres" else f"{type_classe}-{annee}"
    return ORS_CPGE[cle][classe_effectif(effectif)]


def calc_ors(*args: int | tuple[int, int], type_classe: str = "sciences") -> int:
    """calc_ors((23, 2), (19, 1)) ou calc_ors(23, 2)"""
    assert len(args) >= 2
    if type(args[0]) is tuple:
        # liste de tuple
        couples = [arg for arg in args if isinstance(arg, tuple)]
        assert len(couples) == len(args), "calc_ors : des couples (effectif, année), ou un seul"
        e = max([e for e, a in couples])
        a = max([a for e, a in couples])
        return calc_ors_single(e, a, type_classe)
    if type(args[0]) is int:
        effectif, annee = args
        assert isinstance(effectif, int) and isinstance(annee, int), "calc_ors(effectif, année)"
        return calc_ors_single(effectif, annee, type_classe=type_classe)
    raise ValueError
