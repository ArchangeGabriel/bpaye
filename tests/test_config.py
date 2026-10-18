import datetime as dt

from bpaye.config import BAREME, Bareme
from bpaye.point import calc_traitement_brut

HAUSSE = """
[point]
type  = "Fixe"
unite = "annuel"
values = [
  { date = 2023-07-01, valeur = 59.0734 },
  { date = 2027-01-01, valeur = 60.0 },
]
"""


def test_bareme_surcharge_une_section_et_garde_les_autres(tmp_path):
    fichier = tmp_path / "hausse.toml"
    fichier.write_text(HAUSSE, encoding="utf-8")
    bareme = Bareme.depuis_fichiers(fichier)
    janvier = dt.date(2027, 1, 31)
    assert calc_traitement_brut(500, janvier, bareme) == 2500.0
    assert calc_traitement_brut(500, janvier) == calc_traitement_brut(500, janvier, BAREME) < 2500.0
    assert bareme.get("pc") == BAREME.get("pc")


def test_bareme_table_construite_une_fois():
    assert BAREME.load("csg.deductible") is BAREME.load("csg.deductible")
