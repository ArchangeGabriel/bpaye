"""Temps partiel : la fraction de rémunération et la retenue pour pension.

Un fonctionnaire à temps partiel perçoit « une fraction du traitement, de l'indemnité de
résidence ainsi que des primes et indemnités de toute nature », égale au rapport entre son
service et le service à temps complet ; à 80 % et 90 %, six septièmes et trente-deux
trente-cinquièmes (code général de la fonction publique, art. L612-5, depuis le
1/3/2022 ; avant, ordonnance 82-296, art. 6). Un enseignant dont la quotité est aménagée
entre 80 et 90 % perçoit (quotité × 4/7 + 40) %, « avec un chiffre après la virgule »
(décret 82-624, art. 1) ; au second degré, le service se compte en heures entières, d'où
une quotité = heures / ORS (code de l'éducation, R911-7).
https://www.legifrance.gouv.fr/codes/section_lc/LEGITEXT000044416551/LEGISCTA000044423499/2026-10-17/
https://www.legifrance.gouv.fr/loda/id/LEGITEXT000006063839/2026-10-17/

Retenue pour pension : sur le traitement perçu ; ou, si l'agent a choisi de surcotiser
(code des pensions, L11 bis), sur le traitement d'un temps plein au taux de l'art. D5 :
taux salarial × quotité travaillée + 80 % × (taux salarial + taux employeur CNRACL) ×
quotité non travaillée (depuis le 1/1/2024, décret 2024-49) ; ceux qui avaient choisi la
surcotisation avant restent à 11,10 % × quotité travaillée + 33,40 % × quotité non
travaillée (décret 2024-49, art. 5). Les taux d'avant 2024 ne sont pas lus.
https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000049064677/2026-10-17/

Ce qu'aucun texte lu ne règle, et que bpaye suppose : la fraction arrondie (et non
tronquée) à un chiffre après la virgule ; la prime d'attractivité, les indemnités REP et
l'ISOE réduites selon la règle générale de L612-5, faute de clause propre ; le montant
réduit arrondi au centime.
"""

import datetime as dt

from bpaye.config import BAREME, Bareme

__all__ = [
    "SURCOTISATION_ANTERIEURE",
    "fraction_remuneration",
    "reduit",
    "taux_surcotisation",
]

# Le choix de surcotiser fait avant le 1/2/2024 (décret 2024-49, art. 5).
SURCOTISATION_ANTERIEURE = "anterieure"


def fraction_remuneration(quotite: float) -> float:
    """La fraction de la rémunération d'un temps plein que perçoit un agent dont le service
    vaut ``quotite`` (1.0 à temps plein)."""
    if quotite >= 1.0:
        return 1.0
    if abs(quotite - 0.8) < 1e-9:
        return 6 / 7
    if abs(quotite - 0.9) < 1e-9:
        return 32 / 35
    if 0.8 < quotite < 0.9:
        return round(quotite * 100 * 4 / 7 + 40, 1) / 100
    return quotite


def reduit(montant: float, fraction: float) -> float:
    """``montant`` ramené à la ``fraction`` de rémunération, au centime ; inchangé à temps
    plein."""
    return montant if fraction >= 1.0 else round(montant * fraction, 2)


def taux_surcotisation(
    quotite: float, date: dt.date, option: bool | str = True, bareme: Bareme = BAREME
) -> float:
    """Le taux de la retenue pour pension d'un agent qui surcotise, appliqué au traitement
    d'un temps plein. ``option`` : True (choix fait depuis 2024) ou SURCOTISATION_ANTERIEURE."""
    travaille, non_travaille = quotite, 1.0 - quotite
    if option == SURCOTISATION_ANTERIEURE:
        return 0.1110 * travaille + 0.3340 * non_travaille
    if date < dt.date(2024, 1, 1):
        raise ValueError(f"taux de surcotisation avant 2024 non vérifié ({date})")
    salarial = bareme.load("pc").value(date)
    employeur = bareme.load("surcotisation.cnracl_employeur").value(date)
    return salarial * travaille + 0.80 * (salarial + employeur) * non_travaille
