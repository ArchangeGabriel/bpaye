"""Les extraits de code de README.md et docs/DOC.md, sur l'agente fictive des exemples."""

from pathlib import Path

import pytest

from bpaye import Paye, load_agent
from bpaye.prevision import nets_prevus

EXEMPLE = Path(__file__).resolve().parents[1] / "examples" / "college"


@pytest.fixture
def paye():
    agente = load_agent(EXEMPLE / "agent.toml")
    agente.load_carriere(EXEMPLE / "carriere.toml")
    paye = Paye(agente)
    paye.generate(startyear=2025, startmonth=1, n=12)
    return paye


def test_doc_evenements_hors_carriere(paye):
    net_novembre = paye(2025, 11).net
    paye.retard_paiement((2025, 3), 200205)
    paye.colle((2025, 10), {157: 6.0})
    paye.hse((2025, 11), 3)
    paye.erreur((2025, 4), (2025, 6), 50.0, 200364)
    assert paye(2025, 11).net != net_novembre


def test_doc_selection_et_somme(paye):
    assert paye.select(200364, 2025).somme().calcul == 2550.0
    assert len(paye.select(lambda b: b.net_imposable, 2025)) == 12


def test_doc_prevision():
    mois = nets_prevus(EXEMPLE / "carriere.toml", EXEMPLE / "agent.toml", (2025, 9), 12)
    assert [(m.annee, m.mois) for m in mois][:2] == [(2025, 9), (2025, 10)]
