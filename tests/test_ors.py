import pytest

from bpaye.ors import calc_ors, classe_effectif


@pytest.mark.parametrize(("effectif", "rang"), [(36, 0), (35, 1), (20, 1), (19, 2)])
def test_classe_effectif_aux_seuils_de_35_et_20_eleves(effectif, rang):
    assert classe_effectif(effectif) == rang


@pytest.mark.parametrize(
    ("effectif", "annee", "type_classe", "ors"),
    [
        (40, 2, "sciences", 8),  # décret 50-581, art. 6 : mathématiques spéciales, plus de 35
        (30, 1, "sciences", 10),  # mathématiques supérieures, de 20 à 35
        (15, 2, "lettres", 10),  # art. 7 : première supérieure, moins de 20
    ],
)
def test_ors_en_cpge_selon_la_classe_et_son_effectif(effectif, annee, type_classe, ors):
    assert calc_ors(effectif, annee, type_classe=type_classe) == ors


def test_ors_d_une_troisieme_annee_refusee():
    with pytest.raises(ValueError, match="1 ou 2"):
        calc_ors(30, 3)
