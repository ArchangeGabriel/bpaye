import datetime as dt

import pytest

from bpaye.temps_partiel import SURCOTISATION_ANTERIEURE, fraction_remuneration, reduit, taux_surcotisation


@pytest.mark.parametrize(
    ("quotite", "attendu"),
    [
        (1.0, 1.0),
        (0.5, 0.5),
        (0.8, 6 / 7),
        (0.9, 32 / 35),
        # 15 heures sur 18 : (83,33 × 4/7 + 40) % = 87,6 % (décret 82-624, art. 1).
        (15 / 18, 0.876),
    ],
)
def test_fraction_selon_la_quotite_suit_l612_5(quotite, attendu):
    assert fraction_remuneration(quotite) == pytest.approx(attendu)


def test_reduit_a_temps_plein_inchange():
    assert reduit(123.456, 1.0) == 123.456
    assert reduit(100.0, 6 / 7) == 85.71


def test_surcotisation_depuis_2024_suit_d5():
    # 80 % en 2026 : 11,10 % × 0,8 + 0,80 × (11,10 + 37,65) % × 0,2.
    assert taux_surcotisation(0.8, dt.date(2026, 1, 31)) == pytest.approx(0.0888 + 0.078)


def test_surcotisation_anterieure_garde_ses_taux():
    taux = taux_surcotisation(0.5, dt.date(2026, 1, 31), SURCOTISATION_ANTERIEURE)
    assert taux == pytest.approx(0.5 * 0.1110 + 0.5 * 0.3340)


def test_surcotisation_avant_2024_refusee():
    with pytest.raises(ValueError, match="avant 2024"):
        taux_surcotisation(0.8, dt.date(2023, 6, 30))
