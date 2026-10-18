import datetime as dt

import pytest

from bpaye.vacances import annee_scolaire, en_vacances, semaines_de_cours


def test_semaines_de_cours_2025_2026_par_mois():
    assert semaines_de_cours(dt.date(2025, 9, 22), dt.date(2026, 4, 10)) == {
        (2025, 9): 2,
        (2025, 10): 2,  # Toussaint : les 20 et 27 octobre
        (2025, 11): 4,
        (2025, 12): 3,  # Noël : le 22 et le 29 décembre
        (2026, 1): 4,
        (2026, 2): 3,  # hiver : le 23 février
        (2026, 3): 4,  # le 2 mars, encore en vacances
        (2026, 4): 1,
    }


def test_pont_de_l_ascension_ne_retire_pas_la_semaine():
    assert semaines_de_cours(dt.date(2026, 5, 11), dt.date(2026, 5, 22)) == {(2026, 5): 2}


def test_la_semaine_du_debut_compte():
    assert semaines_de_cours(dt.date(2025, 9, 25), dt.date(2025, 9, 26)) == {(2025, 9): 1}


@pytest.mark.parametrize(
    ("jour", "attendu"),
    [(dt.date(2025, 10, 18), True), (dt.date(2025, 11, 3), False), (dt.date(2025, 10, 17), False)],
)
def test_vacances_du_premier_jour_a_la_veille_de_la_reprise(jour, attendu):
    assert en_vacances(jour) is attendu


def test_zone_b_n_a_pas_les_memes_semaines_en_fevrier():
    # Hiver 2027 : du 6 au 22 février en zone C, du 20 février au 8 mars en zone B.
    fevrier = (dt.date(2027, 2, 1), dt.date(2027, 3, 12))
    assert semaines_de_cours(*fevrier, zone="C") == {(2027, 2): 2, (2027, 3): 2}
    assert semaines_de_cours(*fevrier, zone="B") == {(2027, 2): 3, (2027, 3): 1}


def test_zone_inconnue_refusee():
    with pytest.raises(ValueError, match="'D'"):
        semaines_de_cours(dt.date(2025, 9, 1), dt.date(2025, 10, 1), zone="D")


def test_annee_inconnue_refusee():
    with pytest.raises(ValueError, match="2040-2041"):
        semaines_de_cours(dt.date(2040, 9, 1), dt.date(2041, 4, 1))


def test_annee_scolaire_va_de_septembre_a_aout():
    assert (annee_scolaire(dt.date(2025, 9, 1)), annee_scolaire(dt.date(2026, 8, 31))) == (
        "2025-2026",
        "2025-2026",
    )
