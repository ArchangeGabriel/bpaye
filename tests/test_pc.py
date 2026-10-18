import datetime as dt

import pytest

from bpaye.pc import pension_civile


@pytest.mark.parametrize(
    ("jour", "taux"),
    [
        (dt.date(2011, 6, 30), 0.0812),  # décret 2010-1749, version de 2011
        (dt.date(2012, 11, 30), 0.0849),  # décret 2012-847 : de novembre à décembre 2012
        (dt.date(2025, 1, 31), 0.1110),  # depuis 2020
    ],
)
def test_pension_civile_au_taux_de_l_annee(jour, taux):
    ligne = pension_civile(3000.0, jour)
    assert (ligne.valeur, ligne.code) == (-round(3000.0 * taux, 2), 101050)


def test_pension_civile_avant_2011_refusee():
    with pytest.raises(ValueError, match="MANQUANT"):
        pension_civile(3000.0, dt.date(2010, 6, 30))
