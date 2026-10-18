import subprocess
import sys

import pytest

from bpaye.fonctionnaire import Fonctionnaire
from bpaye.prevision import nets_prevus


def test_import_sans_pdfplumber():
    # Dans un interpréteur neuf : les autres tests importent pdfplumber.
    code = "import sys, bpaye.prevision; assert 'pdfplumber' not in sys.modules"
    subprocess.run([sys.executable, "-c", code], check=True)


def test_colles_prevues_lues_dans_carriere(configuration):
    prevues = Fonctionnaire().load_carriere(configuration[0]).colles_prevues[2025]
    assert (prevues.debut.month, prevues.fin.month, prevues.heures) == (9, 4, {161: 4.0})


def test_colles_payees_deux_mois_apres_selon_les_semaines(configuration):
    nets = {(n.annee, n.mois): n for n in nets_prevus(*configuration, (2025, 9), 12)}
    # Novembre paie septembre (2 semaines), janvier paie novembre (4 semaines).
    assert nets[(2025, 10)].colles == 0
    assert nets[(2026, 1)].colles == pytest.approx(2 * nets[(2025, 11)].colles, abs=0.02)
    assert nets[(2026, 1)].net > nets[(2025, 9)].net


def test_colles_externes_versees_a_part_du_bulletin_principal(configuration):
    carriere, agent = configuration
    sans = {(n.annee, n.mois): n for n in nets_prevus(carriere, agent, (2025, 9), 12)}
    carriere.write_text(
        carriere.read_text(encoding="utf-8")
        + '\n[[rentrees.colles_externes]]\nzone = "B"\ncolles = { 6 = 1.0 }\n'
        + "colles_debut = 2025-09-22\ncolles_fin = 2026-04-10\n"
    )
    avec = {(n.annee, n.mois): n for n in nets_prevus(carriere, agent, (2025, 9), 12)}
    assert all(avec[m].net == sans[m].net for m in sans)
    assert sans[(2026, 1)].net_colles_externes == 0
    assert avec[(2026, 1)].net_colles_externes > 0  # novembre, 4 semaines
    assert avec[(2025, 10)].net_colles_externes == 0


def test_code_de_colle_inconnu_refuse(configuration):
    carriere = configuration[0]
    carriere.write_text(carriere.read_text(encoding="utf-8").replace("161 = 4.0", "999 = 4.0"))
    with pytest.raises(ValueError, match="999"):
        Fonctionnaire().load_carriere(carriere)
