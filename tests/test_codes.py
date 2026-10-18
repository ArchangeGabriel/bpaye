from bpaye.codes import ALL_CODES, load_codes


def test_chaque_code_a_six_chiffres_et_une_categorie():
    assert ALL_CODES
    assert all(len(code) == 6 and code.isdigit() for code in ALL_CODES)
    assert {fiche["cat"] for fiche in ALL_CODES.values()} == {"revenu", "retenue", "patronal", "special"}


def test_les_rubriques_courantes_sont_connues():
    assert (ALL_CODES["101000"]["cat"], ALL_CODES["401301"]["cat"]) == ("revenu", "retenue")


def test_load_codes_relit_le_meme_fichier():
    assert load_codes() == ALL_CODES
