"""Largeurs et formats de l'affichage texte des bulletins (Bulletin.__str__)."""

__all__ = [
    "LIB_FORMAT",
    "LIB_WIDTH",
    "MOIS",
    "MT_FORMAT",
    "MT_WIDTH",
    "WIDTH",
]

# Les mois en français, sans dépendre de la locale du système (strftime("%B")).
MOIS = (
    "janvier",
    "février",
    "mars",
    "avril",
    "mai",
    "juin",
    "juillet",
    "août",
    "septembre",
    "octobre",
    "novembre",
    "décembre",
)

WIDTH = 80
LIB_WIDTH = 50
LIB_FORMAT = "{:" + str(LIB_WIDTH) + "}"
MT_WIDTH = 10
MT_FORMAT = "{:> 8.2f}€"
