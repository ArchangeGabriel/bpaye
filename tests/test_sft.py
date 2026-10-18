import datetime as dt

import pytest

from bpaye.sft import valeur_sft

JANVIER_2025 = dt.date(2025, 1, 31)
POINT_2025 = 59.0734 / 12


@pytest.mark.parametrize(
    ("enfants", "traitement", "attendu"),
    [
        (0, 3000.0, 0.0),
        (1, 3000.0, 2.29),
        # Plafond : traitement de l'IB 879, IM 722 en 2025 (décret 85-1148, art. 10 bis).
        (2, 4500.0, round(10.67 + 0.03 * int(722 * POINT_2025 * 100) / 100, 2)),
        # Plancher : traitement de l'IB 524, IM 454.
        (2, 1500.0, round(10.67 + 0.03 * int(454 * POINT_2025 * 100) / 100, 2)),
        (4, 3000.0, round(15.24 + 4.57 + (0.08 + 0.06) * 3000.0, 2)),
    ],
)
def test_sft_selon_les_enfants_entre_plancher_et_plafond(enfants, traitement, attendu):
    assert valeur_sft(enfants, traitement, JANVIER_2025) == attendu


def test_sft_plafond_suit_le_bareme_de_2024():
    # IB 879 : IM 717 en 2023, 722 en 2024.
    assert valeur_sft(2, 9000.0, dt.date(2023, 12, 31)) < valeur_sft(2, 9000.0, dt.date(2024, 1, 31))
