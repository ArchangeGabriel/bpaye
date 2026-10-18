import datetime as dt

import pytest

from bpaye.fonctionnaire import Fonctionnaire
from bpaye.gipa import montant_gipa

CARRIERE = """
[depart]
nom        = "Agent Fictif"
grille     = "GRILLE_CERTCN"
corps      = "Certifié"
echelon    = {echelon}
anciennete = 0.0
date       = 2018-09-01

[[detachements]]
date    = 2018-09-01
detache = false
"""


def _agent(tmp_path, echelon):
    chemin = tmp_path / "carriere.toml"
    chemin.write_text(CARRIERE.format(echelon=echelon), encoding="utf-8")
    return Fonctionnaire().load_carriere(chemin)


def test_gipa_2023_au_dernier_echelon_rend_l_inflation(tmp_path):
    fonc = _agent(tmp_path, 11)  # dernier échelon de la classe normale : pas d'avancement
    debut, fin = dt.date(2018, 12, 31), dt.date(2022, 12, 31)
    im_debut, im_fin = (fonc.grille.value(d).indice(fonc.echelon(d)) for d in (debut, fin))
    # Arrêté du 11/08/2023 : inflation 8,19 %, point moyen 56,2323 puis 57,2164 (décret 2008-539, art. 3).
    attendu = round(im_debut * 56.2323 * 1.0819 - im_fin * 57.2164, 2)
    assert attendu > 0
    assert montant_gipa(fonc, 2023) == attendu


def test_gipa_d_une_annee_absente_refusee(tmp_path):
    with pytest.raises(ValueError, match="2030"):
        montant_gipa(_agent(tmp_path, 11), 2030)
