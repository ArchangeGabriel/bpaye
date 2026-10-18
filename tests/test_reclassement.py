import datetime as dt

import pytest

import bpaye.reclassement as reclassement
from bpaye.fonctionnaire import Fonctionnaire, echelon_d_accueil
from bpaye.reclassement import Correspondance, Reclassement, anciennete_au, reclasse

JOUR = dt.date(2017, 9, 1)

DEPART_AVANT_PPCR = """
[depart]
nom        = "Agent Fictif"
grille     = "GRILLE_AGCN"
echelon    = 7
anciennete = 0.0
date       = 2015-03-08
"""


@pytest.fixture
def tableau(monkeypatch):
    """Un tableau fictif pour GRILLE_AGCN au 1er septembre 2017 : 7 → 7 ancienneté
    conservée, 6 → 6 sans ancienneté, 5 → 5 conservée et majorée de 3 mois."""
    table = {
        7: Correspondance(7, 7),
        6: Correspondance(6, 6, anciennete="neant"),
        5: Correspondance(5, 5, majoration=0.25),
    }
    monkeypatch.setitem(reclassement.RECLASSEMENTS, "GRILLE_AGCN", [Reclassement(JOUR, "fictif", table)])


def _agent(tmp_path, echelon=7, depart="2015-03-08"):
    carriere = tmp_path / "carriere.toml"
    texte = DEPART_AVANT_PPCR.replace("echelon    = 7", f"echelon    = {echelon}")
    carriere.write_text(texte.replace("2015-03-08", depart), encoding="utf-8")
    return Fonctionnaire().load_carriere(carriere)


def test_reclassement_anciennete_conservee_meme_echelon(tableau, tmp_path):
    fonc = _agent(tmp_path)
    avant = anciennete_au(fonc, JOUR)
    reclasse(fonc, JOUR)
    assert fonc.echelon(JOUR) == 7
    assert fonc.anciennete(JOUR) == pytest.approx(avant)


def test_reclassement_sans_anciennete_repart_de_zero(tableau, tmp_path):
    fonc = _agent(tmp_path, echelon=6, depart="2016-03-08")
    reclasse(fonc, JOUR)
    assert (fonc.echelon(JOUR), fonc.anciennete(JOUR)) == (6, 0.0)


def test_reclassement_anciennete_majoree(tableau, tmp_path):
    fonc = _agent(tmp_path, echelon=5, depart="2017-03-01")
    reclasse(fonc, JOUR)
    assert fonc.anciennete(JOUR) == pytest.approx((JOUR - dt.date(2017, 3, 1)).days / 365 + 0.25)


def test_reclassement_anciennete_au_dela_de_la_duree_passe_au_suivant(tableau, tmp_path):
    # Au 7e depuis mars 2014 (le 8e venait en septembre 2017) : plus que les 3 ans du
    # 7e échelon PPCR.
    fonc = _agent(tmp_path, depart="2014-03-08")
    reclasse(fonc, JOUR)
    assert (fonc.echelon(JOUR), fonc.anciennete(JOUR)) == (8, 0.0)


def test_reclassement_sans_tableau_refuse(tmp_path, monkeypatch):
    monkeypatch.setitem(reclassement.RECLASSEMENTS, "GRILLE_AGCN", [])
    fonc = _agent(tmp_path)
    with pytest.raises(ValueError, match="pas de tableau"):
        reclasse(fonc, JOUR)


def test_reclassement_echelon_hors_tableau_refuse(tableau, tmp_path):
    fonc = _agent(tmp_path, echelon=3, depart="2017-03-01")
    with pytest.raises(ValueError, match="pas dans le tableau"):
        reclasse(fonc, JOUR)


@pytest.mark.parametrize(("indice", "attendu"), [(800, 4), (801, 5), (100, 1), (2000, 11)])
def test_echelon_d_accueil_indice_egal_ou_immediatement_superieur(indice, attendu):
    from bpaye.grille import GRILLE_CHSUP

    assert echelon_d_accueil(GRILLE_CHSUP.value(dt.date(2023, 9, 1)), indice) == attendu
