import datetime as dt

import pytest

from bpaye.point import calc_traitement_brut, valeur_point


def test_traitement_d_un_indice_au_centime():
    # IM 480 au 1/10/2008, point annuel de 54,8475 € : 480 × 54,8475 / 12 = 2 193,90 €.
    assert calc_traitement_brut(480, dt.date(2008, 10, 31)) == 2193.90


def test_valeur_du_point_suit_ses_revalorisations():
    assert valeur_point(dt.date(2023, 7, 31)) > valeur_point(dt.date(2023, 6, 30))


def test_point_avant_sa_premiere_valeur_refuse():
    with pytest.raises(ValueError, match="MANQUANT"):
        valeur_point(dt.date(2003, 1, 31))
