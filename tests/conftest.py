import pytest

CARRIERE = """
[depart]
nom        = "Agent Fictif"
grille     = "GRILLE_AGCN"
echelon    = 3
anciennete = 0.0
date       = 2019-09-01

[[detachements]]
date    = 2019-09-01
detache = false

[[rentrees]]
year     = 2024
annee    = 2
effectif = 40
hsa_vs   = 6

[[rentrees]]
year         = 2025
annee        = 2
effectif     = 40
hsa_vs       = 6
colles       = { 161 = 4.0 }
colles_debut = 2025-09-22
colles_fin   = 2026-04-10
"""

AGENT = """
siret = "19750000000000"

[ir]
type = "Taux"
values = [{ date = 2019-01-01, valeur = 0.05 }]

[[enfants]]
date   = 2019-01-01
nombre = 0

[[residence]]
date = 2019-09-01
zone = 1

[[fmd]]
date   = 2019-01-01
niveau = 1

[[transport]]
date              = 2019-09-01
abonnement_annuel = 1000
"""


@pytest.fixture
def configuration(tmp_path):
    carriere, agent = tmp_path / "carriere.toml", tmp_path / "agent.toml"
    carriere.write_text(CARRIERE, encoding="utf-8")
    agent.write_text(AGENT, encoding="utf-8")
    return carriere, agent


def _ecrit_faux_bulletin(chemin):
    """Un bulletin PAY18E fictif, écrit comme les vrais : Courier-Bold 9 pt, code et libellé
    à gauche, « € » puis le montant à droite, version à la verticale, pied en bas."""
    from reportlab_layout import PDFMaker

    hauteur = 842
    with PDFMaker(str(chemin)) as doc:
        c = doc.canvas
        c.setFont("Helvetica", 6)
        for i, lettre in enumerate("PAY18E-V4.2-29"):
            c.drawString(570, hauteur - 300 - 7 * i, lettre)
        lignes = [
            ("101000", "TRAITEMENT BRUT", "3000,00"),
            ("200205", "HEURES ANNEES ENSEIGNT", "300,00"),
            ("200205", "HEURES ANNEES ENSEIGNT    RAPPEL ANNEE C", "50,00"),
        ]
        for rang, (code, libelle, montant) in enumerate(lignes):
            y = hauteur - 142 - 9 * rang
            c.setFont("Courier-Bold", 9)
            c.drawString(16.4, y, code)
            c.drawString(53.0, y, libelle)
            c.setFont("Helvetica", 8)
            c.drawString(361.4, y, "€")
            c.setFont("Courier-Bold", 9)
            c.drawString(385.4, y, montant)
        c.setFont("Courier-Bold", 9)
        for x, y, texte in [
            (380, 212, "3350,00"),
            (450, 212, "1000,00"),
            (520, 212, "2000,00"),
            (420, 194, "2350,00"),  # net à payer : 3 350 − 1 000 de retenues
            (120, 126, "2600,00"),
        ]:
            c.drawString(x, y, texte)


@pytest.fixture
def faux_bulletin_pdf():
    """Écrit un bulletin PAY18E fictif au chemin donné (il faut reportlab_layout)."""
    return _ecrit_faux_bulletin
