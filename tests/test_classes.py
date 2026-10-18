import datetime as dt

import pytest

from bpaye.classes import Temporal
from bpaye.config import BAREME


@pytest.mark.parametrize(
    ("section", "jour"),
    [
        ("pc", dt.date(2008, 6, 30)),  # taux d'avant 2011 non relu
        ("transport.plafond", dt.date(2015, 3, 31)),  # plafond d'avant août 2016 non relu
        ("rafp", dt.date(2003, 1, 31)),  # régime créé au 1/1/2005
    ],
)
def test_bareme_avant_sa_premiere_valeur_refuse_de_deviner(section, jour):
    with pytest.raises(ValueError, match="MANQUANT"):
        BAREME.load(section)(jour)


def test_donnee_d_agent_avant_sa_premiere_valeur_prend_celle_ci():
    echelon: Temporal[int] = Temporal()
    echelon.append(dt.date(2010, 9, 1), 3)
    assert echelon(dt.date(2010, 1, 31)) == 3


def test_message_sans_valeur_precedente_nomme_la_date():
    echelon: Temporal[int] = Temporal()
    echelon.append(dt.date(2010, 9, 1), 3)
    with pytest.raises(ValueError, match="2010-09-30"):
        echelon.value_prec(dt.date(2010, 9, 30))


def test_valeur_repetee_se_retrouve_a_sa_derniere_date():
    echelon: Temporal[int] = Temporal()
    for jour, valeur in ((dt.date(2010, 9, 1), 2), (dt.date(2012, 9, 1), 3), (dt.date(2015, 9, 1), 2)):
        echelon.append(jour, valeur)
    assert echelon.value_toindice(2) == 2
    echelon.update_date_fromvalue(2, dt.date(2016, 9, 1))
    assert echelon.values[-1] == (dt.date(2016, 9, 1), 2)
