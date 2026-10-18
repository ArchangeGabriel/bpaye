import datetime as dt

import pytest

from bpaye import load_agent
from bpaye.indemnite_comp_csg import indemnite_comp_csg


def _agent(configuration):
    carriere, agent = configuration
    fonc = load_agent(agent)
    fonc.load_carriere(carriere)
    return fonc


def test_montant_declare_par_l_agent(configuration):
    assert indemnite_comp_csg(dt.date(2025, 1, 31), _agent(configuration)).valeur == 57.55


def test_rien_avant_2018(configuration):
    assert indemnite_comp_csg(dt.date(2017, 12, 31), _agent(configuration)) is None


def test_sans_montant_declare_refuse():
    with pytest.raises(ValueError, match="MANQUANT"):
        indemnite_comp_csg(dt.date(2025, 1, 31))
