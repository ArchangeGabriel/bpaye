"""Colles (heures d'interrogation, code 200207) : déclarées, payées, prévues.

Une colle est déclarée un mois et payée deux mois plus tard, au taux du code sous
lequel le lycée la déclare (hsa.valeur_colle), pas à celui du colleur. Les colles
prévues d'une rentrée (carriere.toml) se répartissent sur les semaines de cours de la
zone de l'établissement (vacances.py) ; celles d'un autre établissement sont payées à
part, sur un autre bulletin.
"""

import datetime as dt
from collections import defaultdict
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol, Self

from bpaye.classes import Ligne
from bpaye.config import BAREME, Bareme
from bpaye.hsa import code_colle, valeur_colle
from bpaye.protocoles import Agent, BulletinMois
from bpaye.utils import decalage_mois
from bpaye.vacances import ZONE_PAR_DEFAUT, semaines_de_cours

__all__ = [
    "MOIS_RELIQUAT",
    "SEMAINES_BUDGET",
    "SEMAINES_COLLES",
    "Colle",
    "Colles",
    "CollesExternes",
    "CollesPrevues",
    "brut_colles_externes",
    "inject_colles_prevues",
    "semaines_de_colles",
]

# Colles de seconde année. Le budget d'une classe compte SEMAINES_BUDGET semaines de
# colles ; SEMAINES_COLLES se passent de fin septembre à fin mars, payées à chaque colleur
# pour ses heures. Le reliquat est rendu en mai/juin, avant les oraux, et revient au seul
# professeur de la classe : il est payé sur ses heures de budget hebdomadaire. La première
# phase fait 19 ou 20 semaines selon l'année, le reliquat 5 ou 6 (6 en 2025-2026) : une
# prévision s'en accommode, elle garde 20 et 5.
SEMAINES_BUDGET = 25
SEMAINES_COLLES = 20
# Le reliquat est déclaré en mai et payé deux mois après, comme les autres colles : il est
# arrivé sur la paie de juillet en 2025 comme en 2026.
MOIS_RELIQUAT = 5


@dataclass(frozen=True, slots=True)
class CollesPrevues:
    """Les colles prévues d'une rentrée, lues dans carriere.toml."""

    debut: dt.date  # première semaine de colles
    fin: dt.date  # au plus tard ; les semaines au-delà de SEMAINES_COLLES ne comptent pas
    heures: dict[int, float] = field(default_factory=dict)  # par semaine, par code de colle
    heures_classe: float = 0.0  # budget hebdomadaire de sa propre classe, pour le reliquat


@dataclass(frozen=True, slots=True)
class CollesExternes:
    """Des colles dans un autre établissement, lues dans carriere.toml. Elles ont leur
    payeur et leur bulletin, à part du salaire, et suivent les vacances de la zone de cet
    établissement : ses semaines de colles ne sont pas celles du lycée d'affectation."""

    zone: str
    debut: dt.date
    fin: dt.date
    heures: dict[int, float] = field(default_factory=dict)  # par semaine, par code déclaré
    etablissement: str = ""  # pour mémoire


def semaines_de_colles(
    debut: dt.date,
    fin: dt.date,
    vacances: list[tuple[str, dt.date, dt.date]] | None = None,
    nombre: int = SEMAINES_COLLES,
    zone: str = ZONE_PAR_DEFAUT,
) -> dict[tuple[int, int], int]:
    """Les ``nombre`` premières semaines de cours à partir du ``debut``, par mois, dans
    la ``zone`` de l'établissement.

    Le calendrier zone C compte 22 semaines de cours entre fin septembre et fin mars
    2025-2026 quand le récapitulatif HIO en paie 20 : les colles ne tombent pas chaque
    semaine de cours. Garder les premières plutôt que d'ôter des semaines au milieu
    décale au plus d'un mois le paiement des dernières, sans en changer le total.
    """
    retenues: dict[tuple[int, int], int] = {}
    reste = nombre
    for mois, semaines in semaines_de_cours(debut, fin, vacances, zone).items():
        if reste <= 0:
            break
        retenues[mois] = min(semaines, reste)
        reste -= retenues[mois]
    return retenues


class Colle:
    def __init__(
        self,
        date: dt.date,
        code: int,
        heures: float | None = None,
        comm: str = "",
        payee: bool = False,
        troppercue: bool = False,
        bareme: Bareme = BAREME,
    ) -> None:
        """Une colle représente un nombre d'heure pour un code de hsa.CODE à une date donnée
        autant donner des commentaires pour les différencier
        (on les retrouve par le couple (date,code,comm,heures))
        Le taux est celui du code (hsa.valeur_colle), pas de la grille du colleur.
        """
        self.date = date
        self.date_paiement: dt.date | None = None
        self.code = code
        self.valeur_heure = valeur_colle(code, date, bareme)
        self.heures = heures
        self.comm = comm
        self.payee = payee
        self.troppercue = troppercue

    def __eq__(self, colle: object) -> bool:
        assert isinstance(colle, Colle), f"une Colle ne se compare qu'à une Colle : {colle!r}"
        return (
            colle.date == self.date
            and colle.comm == self.comm
            and colle.code == self.code
            and colle.heures == self.heures
        )

    def __str__(self) -> str:
        return (
            str(self.date)
            + " : "
            + self.commentaire
            + (f" payée le {self.date_paiement}" if self.payee else "")
            + (" trop perçue" if self.troppercue else "")
        )

    def __repr__(self) -> str:
        return str(self)

    def fmt_csv(self, delimiter: str = ";") -> str:
        dp = self.date_paiement.strftime("%d/%m/%Y") if self.date_paiement is not None else ""
        champs = [
            self.date.strftime("%d/%m/%Y"),
            str(int(self.troppercue)),
            str(self.heures).replace(".", ","),
            str(self.code),
            str(self.total).replace(".", ","),
            dp,
        ]
        return delimiter.join(champs) + "\n"

    @property
    def total(self) -> float:
        assert self.heures is not None, f"colle sans heures : {self.code} au {self.date}"
        return round(self.valeur_heure * self.heures, 2)

    @property
    def commentaire(self) -> str:
        return f"{self.heures}h[{self.code}] {self.comm}"

    def paiement(self, date: dt.date) -> Ligne:
        self.payee = True
        self.date_paiement = date
        return Ligne(self.total, f"H. Interr. HSI Colles {self.commentaire}", code=200207, classe="INDEM")

    def paiement_dupercu(self, date: dt.date) -> Ligne:
        self.payee = True
        self.troppercue = False
        self.date_paiement = date
        return Ligne(
            -self.total, f"H. Interr. HSI Colles  Trop-perçu {self.commentaire}", code=200207, classe="INDEM"
        )


class Colles:
    def __init__(self, liste: list[Colle] | None = None, bareme: Bareme = BAREME) -> None:
        self.bareme = bareme
        if liste is None:
            self.colles: list[Colle] = []  # Liste d'heures (par code) à différentes dates
        else:
            self.colles = liste

    def append(self, year: int, mois: int, dico: dict[int, float], comm: str = "") -> list[Colle]:
        date = dt.date(year, mois, 1)
        nouvelles: list[Colle] = []
        for code, heures in dico.items():
            c = Colle(date, code, heures, comm, bareme=self.bareme)
            self.colles.append(c)
            nouvelles.append(c)
        return nouvelles

    def sort(self) -> None:
        self.colles.sort(key=lambda c: c.date)

    def paye(
        self, year: int, mois: int, dico: dict[int, float], comm: str, bulletin: BulletinMois
    ) -> list[Colle]:
        date = dt.date(year, mois, 1)
        nouvelles: list[Colle] = []
        for code, heures in dico.items():
            c = Colle(date, code, heures, comm=comm + " (origine ?)", troppercue=True, bareme=self.bareme)
            self.colles.append(c)
            bulletin.append(c.paiement(bulletin.date), recalc=True)
            nouvelles.append(c)
        return nouvelles

    def __getitem__(self, i: int) -> Colle:
        return self.colles[i]

    def __iter__(self) -> Iterator[Colle]:
        return iter(self.colles)

    def __str__(self) -> str:
        self.sort()
        return "\n".join([str(c) for c in self])

    def __repr__(self) -> str:
        return str(self)

    def sum(self) -> float:
        return sum([c.total for c in self])

    def non_payees(self) -> Self:
        return type(self)([c for c in self if not c.payee])

    def trop_percues(self) -> Self:
        return type(self)([c for c in self if c.troppercue])

    @classmethod
    def paiement(cls, bulletin: BulletinMois, colle: Colle | list[Colle]) -> None:
        if type(colle) is list:
            for c in colle:
                Colles.paiement(bulletin, c)
        else:
            assert type(colle) is Colle
            bulletin.append(colle.paiement(bulletin.date), recalc=True)

    def paiement_all(self, bulletin: BulletinMois) -> None:
        for c in self:
            bulletin.append(c.paiement(bulletin.date), recalc=True)

    def export_colles(self, filename: str | Path, delimiter: str = ";") -> None:
        with Path(filename).open("w") as f:
            for c in self:
                f.write(c.fmt_csv(delimiter))


class AgentColles(Agent, Protocol):
    """Ce que inject_colles_prevues lit de l'agent, en plus de sa carrière."""

    @property
    def colles_prevues(self) -> dict[int, CollesPrevues]: ...

    @property
    def zone_vacances(self) -> str: ...


class PayeColles(Protocol):
    """Ce que inject_colles_prevues demande de la Paye, que paye.py importe d'ici : un
    import en retour ferait un cycle (voir protocoles.py)."""

    @property
    def fonctionnaire(self) -> AgentColles: ...

    def __call__(self, year: int, mois: int) -> BulletinMois | None: ...

    def colle(
        self,
        original_date: tuple[int, int],
        codesheures: dict[int, float],
        decalage: int = 2,
        payee: bool = True,
        paiement_date: tuple[int, int] | None = None,
        comm: str = "",
    ) -> list[Colle]: ...


def inject_colles_prevues(
    paye: PayeColles,
    year: int,
    decalage: int = 2,
    vacances: list[tuple[str, dt.date, dt.date]] | None = None,
) -> list[Colle]:
    """Injecte dans P les colles prévues de la rentrée ``year`` (carriere.toml).

    Chaque mois, les heures hebdomadaires de chaque code sont multipliées par les
    semaines de colles du mois (semaines_de_colles) ; elles sont déclarées ce mois-là et
    payées ``decalage`` mois après. Si la rentrée donne le budget hebdomadaire de sa
    classe, le reliquat (SEMAINES_BUDGET − SEMAINES_COLLES semaines) est déclaré en mai,
    au code de la classe : celui de l'ORS de la rentrée, dans le corps du moment. Un mois
    dont le bulletin de paiement n'est pas généré est laissé de côté. Renvoie les colles
    injectées.
    """
    prevues = paye.fonctionnaire.colles_prevues.get(year)
    if prevues is None:
        return []
    declarations = [
        (mois, {code: h * semaines for code, h in prevues.heures.items()}, f"{semaines} sem.")
        for mois, semaines in semaines_de_colles(
            prevues.debut, prevues.fin, vacances, zone=paye.fonctionnaire.zone_vacances
        ).items()
    ]
    if prevues.heures_classe:
        rentree = dt.date(year, 9, 1)
        code = code_colle(paye.fonctionnaire.ors(rentree), paye.fonctionnaire.grille.value(rentree).corps)
        reliquat = SEMAINES_BUDGET - SEMAINES_COLLES
        declarations.append(
            (
                (year + 1, MOIS_RELIQUAT),
                {code: prevues.heures_classe * reliquat},
                f"reliquat de la classe, {reliquat} sem.",
            )
        )
    injectees: list[Colle] = []
    for (y, m), codesheures, detail in declarations:
        if not codesheures or paye(*decalage_mois(y, m, decalage)) is None:
            continue
        injectees += paye.colle(
            original_date=(y, m),
            codesheures=codesheures,
            decalage=decalage,
            comm=f"prévision, {detail}",
        )
    return injectees


def brut_colles_externes(
    externes: CollesExternes,
    decalage: int = 2,
    vacances: list[tuple[str, dt.date, dt.date]] | None = None,
    bareme: Bareme = BAREME,
) -> dict[tuple[int, int], float]:
    """Le brut que l'autre établissement paie chaque mois (année, mois du paiement) :
    ses 20 semaines de colles dans sa zone, déclarées chaque mois, payées ``decalage``
    mois après, au taux du code déclaré."""
    brut: dict[tuple[int, int], float] = defaultdict(float)
    semaines_par_mois = semaines_de_colles(externes.debut, externes.fin, vacances, zone=externes.zone)
    for (y, m), semaines in semaines_par_mois.items():
        paiement = decalage_mois(y, m, decalage)
        for code, heures in externes.heures.items():
            brut[paiement] += Colle(dt.date(y, m, 1), code, heures * semaines, bareme=bareme).total
    return {mois: round(montant, 2) for mois, montant in sorted(brut.items())}
