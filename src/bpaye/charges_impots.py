"""Heures supplémentaires : réduction de cotisations (453000) et exonération d'impôt (011200).

Depuis 2019 (loi 2018-1213), les HSA, leur majoration et les heures d'interrogation,
pas les indemnités, ont :

- une réduction de cotisations salariales de 5 % (le taux salarial de la RAFP), dans
  la limite de 20 % du traitement indiciaire brut annuel ; compensée, elle laisse les
  droits RAFP intacts ;
- une exonération d'impôt sous un plafond annuel net, 5 000 € puis 7 500 € (loi
  2022-1158). Le plafond brut réintègre la CSG déductible :
  5 000 / (1 − 98,25 % × 6,8 %) = 5 357,96, arrondi à 5 358 €. Sur ces heures, la CSG
  n'est pas déductible (charges.csg_basculee).

Le net exonéré (011200) se retrouve depuis le bulletin : S = (N + C + R − M) / 0,93319,
N le net avant impôt, C la CSG non déductible, R la CRDS, M le montant imposable.

En 2019, les heures de janvier à mars ont été régularisées en octobre (ligne « Regul
réduction cotis HS montant HS payé ») ; le prélèvement à la source de ces mois les
comptait encore imposables.

Sources : https://www.fonction-publique.gouv.fr/exoneration-des-heures-supplementaires,
https://blog.juliendelmas.fr/?les-heures-supplementaires-desocialisees-et-defiscalisees-pour-les-enseignants-a-partir-de-janvier-2019
"""

import datetime as dt

import bpaye.config as config
from bpaye.classes import Fixe, Ligne
from bpaye.config import BAREME, Bareme
from bpaye.protocoles import BulletinMois
from bpaye.utils import truncate

__all__ = [
    "DEBUT_EXONERATION_HS",
    "FACTEUR_HS_NET",
    "FIN_EXONERATION_TEPA",
    "FIN_REDUCTION_TEPA",
    "ExonerationHS",
    "hs_exa_net",
    "reduc_cotis_hs",
]

# ── REDUC COTIS HS (code 453000) ─────────────────────────────────────────────
# Formule : min(HS_brut, 20 % × TB annuel) × 5 %
# Le 20 % × TB annuel est le plafond annuel ; appliqué ici au bulletin mensuel.
# La valeur est positive (réduction des retenues, augmente le net).


# Ces régimes sont datés par l'heure effectuée ; bpaye prend la date du bulletin.
# - Loi 2012-958, art. 3 : II abroge l'exonération d'impôt (CGI, art. 81 quater) pour les
#   heures effectuées depuis le 1/8/2012 (VIII C), I la réduction de cotisations (CSS,
#   art. L241-17) depuis le 1/9/2012 (VIII A).
#   https://www.legifrance.gouv.fr/jorf/article_jo/JORFARTI000026288968 (lu le 18/10/2026)
# - Loi 2018-1213, art. 2 : II rétablit l'exonération pour les heures réalisées depuis le
#   1/1/2019, III y avance la réduction (loi 2018-1203, art. 7, V).
#   https://www.legifrance.gouv.fr/jorf/id/JORFTEXT000037851899 (lu le 18/10/2026)
# Avant 2012, le régime de la loi 2007-1223 n'est pas relu : MANQUANT, et bpaye refuse ces
# heures plutôt que de leur appliquer celui de 2019.
FIN_EXONERATION_TEPA = dt.date(2012, 8, 1)
FIN_REDUCTION_TEPA = dt.date(2012, 9, 1)
DEBUT_EXONERATION_HS = dt.date(2019, 1, 1)


def _refuse_avant(date: dt.date, fin_tepa: dt.date) -> None:
    if date < fin_tepa:
        raise ValueError(
            f"Heures supplémentaires au {date} : régime de la loi 2007-1223 non vérifié (MANQUANT)"
        )


def reduc_cotis_hs(hs_brut: float, tb_annuel: float, date: dt.date) -> Ligne | None:
    """Réduction de cotisations sur heures supplémentaires (code 453000), depuis 2019."""
    _refuse_avant(date, FIN_REDUCTION_TEPA)
    if date < DEBUT_EXONERATION_HS:
        return None
    assiette = min(hs_brut, 0.20 * tb_annuel)
    val = round(assiette * 0.05, 2)
    return Ligne(val, "Réduction cot. heures sup.", code=453000, classe="CHARGE")


# ── HS EXO NETTES (code 011200) ───────────────────────────────────────────────
# Plafond annuel d'exonération IR (temporel, défini dans taux.toml [hs_exo.plafond_brut])
#   Avant août 2022 : 5 000 € nets = 5 358 € bruts
#   Depuis août 2022 : 7 500 € nets = 8 037 € bruts  (loi 2022-1158)
#   Formule : plafond_net / (1 – 98,25 % × 6,8 %) = plafond_brut
# Le facteur 0.93319 = 1 – 98.25% × 6.8% traduit la part CSG déductible non
# applicable sur les HS exonérées.
# Formule de vérification : S (brut) = (N + C + R – M) / 0.93319
#   → 011200 (net) = S × 0.93319 = N + C + R – M

_plafond_hs_exo: Fixe = config.BAREME.load("hs_exo.plafond_brut")  # celui du barème du paquet
FACTEUR_HS_NET = 0.93319  # = 1 – 98,25 % × 6,8 %


def hs_exa_net(hs_brut_annuel: float, date: dt.date | None = None, bareme: Bareme = BAREME) -> float:
    """Montant net mensuel exonéré d'IR sur les heures supplémentaires (011200).

    Applique le plafond annuel brut (temporel) puis le facteur 0.93319.
    Retourne 0.0 si hs_brut_annuel ≤ 0.
    """
    if hs_brut_annuel <= 0:
        return 0.0
    plafond = bareme.load("hs_exo.plafond_brut")(date)
    return truncate(min(hs_brut_annuel, plafond) * FACTEUR_HS_NET, 2)


class ExonerationHS:
    """Les heures supplémentaires exonérées d'impôt, bulletin par bulletin, sous le plafond
    annuel (CGI, art. 81 quater) : 7 500 € nets depuis août 2022, soit 8 037 € bruts.

    Le plafond se consomme dans l'ordre de l'année civile : les bulletins de 2024 à 2026
    exonèrent toutes les heures de janvier, celles de février jusqu'au plafond, plus rien
    ensuite (011200 au centime, cumulé à 7 500 €). Un seul plafond mensuel, comme le faisait
    hs_exa_net, exonérait toute l'année. Partagée par les bulletins d'une Paye, comme la
    RAFP : un bulletin dont l'exonération change fait recalculer les suivants de l'année.
    """

    def __init__(self, bareme: Bareme = BAREME) -> None:
        self._bulletins: list[BulletinMois] = []
        self._plafond = bareme.load("hs_exo.plafond_brut")

    def inscrit(self, bulletin: BulletinMois) -> None:
        self._bulletins.append(bulletin)
        self._bulletins.sort(key=lambda b: b.date)

    def brut_exonere(self, bulletin: BulletinMois) -> float:
        """Le brut d'heures supplémentaires exonéré sur ce bulletin."""
        if bulletin.hs_brut <= 0:
            return 0.0
        _refuse_avant(bulletin.date, FIN_EXONERATION_TEPA)
        if bulletin.date < DEBUT_EXONERATION_HS:
            return 0.0
        plafond = self._plafond(bulletin.date)
        cumul = 0.0
        for b in self._bulletins:
            if b.date.year != bulletin.date.year or b.date > bulletin.date:
                continue
            exonere = max(0.0, min(b.hs_brut, plafond - cumul))
            if b is bulletin:
                return exonere
            cumul += exonere
        return 0.0

    def suivants(self, bulletin: BulletinMois) -> list[BulletinMois]:
        """Les bulletins inscrits après celui-ci, dans la même année civile."""
        return [b for b in self._bulletins if b.date.year == bulletin.date.year and b.date > bulletin.date]
