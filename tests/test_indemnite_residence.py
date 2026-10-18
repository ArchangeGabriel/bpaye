import datetime as dt

import pytest

from bpaye.indemnite_residence import calc_indemnite_residence
from bpaye.point import valeur_point

JOUR = dt.date(2025, 1, 31)


@pytest.mark.parametrize(("zone", "taux"), [(1, 0.03), (2, 0.01), (3, 0.0)])
def test_indemnite_de_residence_selon_la_zone(zone, taux):
    assert calc_indemnite_residence(zone, 3000.0, valeur_point(JOUR), JOUR) == pytest.approx(3000.0 * taux)


def test_petit_traitement_releve_au_plancher():
    point = valeur_point(JOUR)
    assert calc_indemnite_residence(1, 100.0, point, JOUR) > 0.03 * 100.0
