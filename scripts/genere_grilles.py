"""Génère src/bpaye/grilles.toml à partir des relevés vérifiés de docs/verification.

Les relevés (indices bruts, barème IB → IM, hors-échelle, durées d'échelon) ont été lus
sur Légifrance le 17 octobre 2026, chaque valeur avec sa source. grilles.toml en garde
une copie réduite, et la source de chaque entrée : ce script fait le passage, pour que
la donnée de bpaye ne s'écarte jamais du relevé.

    python scripts/genere_grilles.py [docs/verification] [src/bpaye/grilles.toml]
"""

import re
import sys
import tomllib
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]

# Durée d'un chevron hors échelle : 1 an, arrêté interministériel du 29/8/1957, art. 2 (« après
# un an de perception effective »), non publié sur Légifrance : cité par le Conseil d'État,
# 7/6/2006, n° 271892, https://www.legifrance.gouv.fr/ceta/id/CETATEXT000008239991
CHEVRON = 1.0
SANS_AVANCEMENT = -1

# Nom de la grille dans bpaye → (clé des relevés, corps, classe, cn_echelons).
GRILLES = {
    "GRILLE_AGCN": ("AGREGE_CN", "Agrégé", "CN", None),
    "GRILLE_AGHC": ("AGREGE_HC", "Agrégé", "HC", None),
    "GRILLE_AGCE": ("AGREGE_CE", "Agrégé", "CE", None),
    "GRILLE_CERTCN": ("CERTIFIE_CN", "Certifié", "CN", None),
    "GRILLE_CERTHC": ("CERTIFIE_HC", "Certifié", "HC", None),
    "GRILLE_CERTCE": ("CERTIFIE_CE", "Certifié", "CE", None),
    "GRILLE_CHSUP": ("CHAIRE_SUP", "Chaire Supérieure", "", 5),
}

# Pour chaque grille, les entrées de durées retenues (rang dans le relevé), et ce qui suit
# l'entrée dans le groupe hors échelle : durées des chevrons, et commentaire.
DUREES = {
    "GRILLE_AGCN": [(0, [], ""), (1, [], "")],
    "GRILLE_AGHC": [(0, [CHEVRON, CHEVRON], "chevrons HEA"), (1, [CHEVRON, CHEVRON], "chevrons HEA")],
    "GRILLE_AGCE": [(0, None, "HEA : 3 ans en trois chevrons d'un an, puis HEB")],
    "GRILLE_CERTCN": [(0, [], ""), (1, [], "")],
    "GRILLE_CERTHC": [(0, [], ""), (1, [], ""), (2, [], "")],
    "GRILLE_CERTCE": [
        (0, [SANS_AVANCEMENT, CHEVRON, CHEVRON], "échelon spécial HEA au choix"),
        (1, [CHEVRON, CHEVRON], "5e échelon HEA"),
    ],
    "GRILLE_CHSUP": [
        (0, [CHEVRON, CHEVRON], "chevrons HEA"),
        (1, [CHEVRON, CHEVRON], "6e sans avancement au-delà de HEA III"),
        (2, [CHEVRON, CHEVRON, SANS_AVANCEMENT, CHEVRON, CHEVRON], "HEB échelon spécial au choix"),
        (
            3,
            [CHEVRON, CHEVRON, 1.5, CHEVRON, CHEVRON],
            "HEA : 3 ans 6 mois en trois chevrons, HEA III 1 an 6 mois ; HEB à l'ancienneté",
        ),
    ],
}

ENTETE = """# Grilles indiciaires (grille.py les compose date par date).
#
# Généré par scripts/genere_grilles.py depuis docs/verification, relevés sur Légifrance le
# 17 octobre 2026 ; chaque entrée cite sa source :
# - [[bareme]] : correspondance indice brut → indice majoré, décret 82-1105 (barème A),
#   limitée aux indices bruts des grilles ci-dessous. De 2007 à 2021, la correspondance des
#   IB 340 à 1015 est la même dans toutes les versions ; la version du 1/5/2008 n'est
#   publiée sur Légifrance que jusqu'à l'IB 536 : grille.py prend alors la version
#   précédente pour les IB au-delà. Les barèmes du 1/7/2005, 1/7/2006 et 1/11/2006 sont lus
#   sur les fac-similés du JO (« tableau non reproduit » sur Légifrance).
# - [[hors_echelle]] : indices majorés des chevrons HEA et HEB, montants annuels du décret
#   85-1148, art. 6, divisés par la valeur annuelle du point (entiers à 0,0005 près).
# - pour chaque grille : ses indices bruts (statuts et décrets d'échelonnement indiciaire),
#   et ses durées d'échelon (statuts particuliers). « HEA » et « HEB » occupent chacun trois
#   positions, une par chevron. Durée d'un chevron : 1 an (arrêté du 29/8/1957, art. 2, cité
#   par le Conseil d'État, 7/6/2006, n° 271892 ; l'arrêté lui-même n'est pas publié en ligne).
#   -1 : pas d'avancement automatique (échelon spécial au choix, ou dernier échelon).
#
# Ce qui manque : les chaires supérieures avant le 1/9/2010 (arrêté du 20/10/1977, ni sur
# Légifrance ni en fac-similé trouvé). Les PsyEN ont les indices bruts des certifiés depuis
# le 1/9/2017 (décret 2017-145, puis décret 2017-789, art. 11-1).
"""


def url(source: str) -> str:
    m = re.search(r"https://\S+", source)
    return m.group(0).rstrip(" ;,)") if m else ""


def court(source: str, n: int = 150) -> str:
    texte = " ".join(source.split())
    return texte if len(texte) <= n else texte[:n].rsplit(" ", 1)[0] + " […]"


def chaine(texte: str) -> str:
    return '"' + texte.replace("\\", "\\\\").replace('"', '\\"') + '"'


def source(entree: dict, n: int = 150) -> str:
    return chaine(f"{court(entree['source'], n)} {url(entree['source'])}")


def bonifie(anciennete: list[float]) -> list[float]:
    """PPCR : les 6e et 8e échelons peuvent être bonifiés d'un an."""
    choix = list(anciennete)
    choix[5] -= 1
    choix[7] -= 1
    return choix


# Indices bruts lus hors des grilles : plancher et plafond du supplément familial de
# traitement (décret 85-1148, art. 10 bis).
IB_HORS_GRILLES = {524, 879}


def indices_utilises(indices: dict) -> set[int]:
    utilises = set(IB_HORS_GRILLES)
    for cle, *_ in GRILLES.values():
        for entree in indices.get(cle, []):
            if isinstance(entree.get("ib"), list):
                utilises |= {ib for ib in entree["ib"] if isinstance(ib, int)}
    return utilises


def bloc_bareme(bareme: dict, utilises: set[int]) -> list[str]:
    lignes = []
    for version in bareme["bareme"]:
        table = {int(ib): im for ib, im in version["ib_im"].items()}
        valeurs = ", ".join(f'"{ib}" = {table[ib]}' for ib in sorted(utilises) if ib in table)
        lignes.append(f"\n[[bareme]]\ndate = {version['date']}\nsource = {source(version, 110)}\n")
        lignes.append(f"ib_im = {{ {valeurs} }}\n")
    for he in bareme["hors_echelle"]:
        if he.get("im_HEA"):
            lignes.append(
                f"\n[[hors_echelle]]\ndate = {he['date']}\nHEA = {he['im_HEA']}\nHEB = {he['im_HEB']}\n"
                f"source = {source(he, 110)}\n"
            )
    return lignes


def durees_par_position(nom: str, entree: dict, suite: list[float] | None) -> list[float]:
    anciennete = list(entree["anciennete"])
    if suite is None:  # classe exceptionnelle des agrégés : 2,5 ans au 1er, puis chevrons
        return [anciennete[0]] + [CHEVRON] * 5
    # Les durées lues vont jusqu'à l'entrée dans le groupe hors échelle ; au-delà, celles des
    # chevrons (le 6e échelon des chaires supérieures de 2023, HEA, est décompté en chevrons).
    return anciennete[: 5 if nom == "GRILLE_CHSUP" else len(anciennete)] + suite


def bloc_grille(nom: str, indices: dict, durees: dict) -> list[str]:
    cle, corps, classe, cn = GRILLES[nom]
    lignes = [f"\n# {'─' * 88}\n[{nom}]\ncorps = {chaine(corps)}\nclasse = {chaine(classe)}\n"]
    if cn:
        lignes.append(f"cn_echelons = {cn}  # HSA : moyenne des échelons 1 à 5 (décret 50-1253, art. 2)\n")
    for entree in indices[cle]:
        if not isinstance(entree.get("ib"), list):
            lignes.append(f"# {entree['date']} : MANQUANT — {court(entree['source'], 200)}\n")
            continue
        ib = ", ".join(chaine(b) if isinstance(b, str) else str(b) for b in entree["ib"])
        lignes.append(
            f"\n[[{nom}.indices]]\ndate = {entree['date']}\nib = [{ib}]\nsource = {source(entree)}\n"
        )
    for rang, suite, note in DUREES[nom]:
        entree = durees[cle][rang]
        lignes.append(
            f"\n[[{nom}.durees]]\ndate = {entree['date']}\n"
            f"anciennete = {durees_par_position(nom, entree, suite)}\n"
        )
        for cle_choix in ("choix", "grandchoix"):
            if cle_choix in entree:
                lignes.append(f"{cle_choix} = {list(entree[cle_choix]) + (suite or [])}\n")
        if "acceleration" in entree and len(entree["anciennete"]) == 10:
            lignes.append(f"choix = {bonifie(entree['anciennete'])}  # 6e et 8e bonifiés d'un an\n")
        lignes.append(f"source = {source(entree)}\n")
        corps_lus = ", ".join(map(str, entree.get("corps", [])))
        if corps_lus:
            lignes.append(f"corps_verifies = {chaine(court(corps_lus, 200))}\n")
        if note:
            lignes.append(f"# {note}\n")
    return lignes


def main(releves: Path, sortie: Path) -> None:
    with (releves / "indices_bruts.toml").open("rb") as f:
        indices = tomllib.load(f)
    with (releves / "bareme.toml").open("rb") as f:
        bareme = tomllib.load(f)
    with (releves / "durees_reclassements.toml").open("rb") as f:
        durees = tomllib.load(f)["durees"]
    lignes = [ENTETE, *bloc_bareme(bareme, indices_utilises(indices))]
    for nom in GRILLES:
        lignes += bloc_grille(nom, indices, durees)
    sortie.write_text("".join(lignes), encoding="utf-8")
    print("écrit", sortie)


if __name__ == "__main__":
    arguments = sys.argv[1:]
    releves = Path(arguments[0]) if arguments else RACINE / "docs" / "verification"
    sortie = Path(arguments[1]) if len(arguments) > 1 else RACINE / "src" / "bpaye" / "grilles.toml"
    main(releves, sortie)
