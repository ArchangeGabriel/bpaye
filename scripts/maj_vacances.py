#!/usr/bin/env python3
"""Régénère vacances.toml d'après le calendrier scolaire officiel, zones A, B et C.

Source : jeu de données « fr-en-calendrier-scolaire » de data.education.gouv.fr. Les
dates d'une zone sont les mêmes dans toutes ses académies de métropole : on en lit une
par zone (ACADEMIES). Les dates y sont des instants UTC du minuit de Paris ; on les
ramène au jour local. « debut » est le premier jour sans cours, « reprise » le jour où
les cours reprennent. L'été retenu est celui des élèves.

Usage : python scripts/maj_vacances.py [première année scolaire, par défaut 2019]
"""

import json
import sys
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

URL = "https://data.education.gouv.fr/api/explore/v2.1/catalog/datasets/fr-en-calendrier-scolaire/records"
PARIS = ZoneInfo("Europe/Paris")
CIBLE = Path(__file__).resolve().parent.parent / "vacances.toml"
ACADEMIES = {"A": "Lyon", "B": "Nantes", "C": "Paris"}
PAGE = 100  # le plafond de l'API par requête


def jour(instant: str) -> str:
    return datetime.fromisoformat(instant).astimezone(PARIS).date().isoformat()


def enregistrements(zone: str, academie: str, premiere: int) -> list[dict]:
    filtre = f'zones="Zone {zone}" and location="{academie}" and start_date >= "{premiere}-08-01"'
    resultats: list[dict] = []
    while True:
        parametres = urllib.parse.urlencode(
            {
                "select": "description,start_date,end_date,annee_scolaire,population",
                "where": filtre,
                "order_by": "start_date",
                "limit": PAGE,
                "offset": len(resultats),
            }
        )
        with urllib.request.urlopen(f"{URL}?{parametres}", timeout=30) as reponse:
            page = json.load(reponse)["results"]
        resultats += page
        if len(page) < PAGE:
            return resultats


def main() -> None:
    premiere = int(sys.argv[1]) if len(sys.argv) > 1 else 2019
    lignes = [
        "# Vacances scolaires des zones A, B et C, d'après le calendrier officiel : jeu",
        "# « fr-en-calendrier-scolaire » de data.education.gouv.fr, lu pour une académie par",
        f"# zone ({', '.join(f'{z} {a}' for z, a in ACADEMIES.items())}). Régénéré par",
        "# scripts/maj_vacances.py. « debut » est le premier jour sans cours, « reprise » le jour",
        "# où les cours reprennent.",
    ]
    total = 0
    for zone, academie in ACADEMIES.items():
        vus = set()
        for e in enregistrements(zone, academie, premiere):
            if e["population"] == "Enseignants" or e["description"].startswith("Début"):
                continue  # l'été des élèves suffit ; un été sans fin connue ne dit rien
            cle = (e["annee_scolaire"], e["description"])
            if cle in vus:
                continue
            vus.add(cle)
            lignes += [
                "",
                "[[vacances]]",
                f'zone = "{zone}"',
                f'annee = "{e["annee_scolaire"]}"',
                f'nom = "{e["description"].removesuffix(" Élèves").strip()}"',
                f"debut = {jour(e['start_date'])}",
                f"reprise = {jour(e['end_date'])}",
            ]
        total += len(vus)
    CIBLE.write_text("\n".join(lignes) + "\n", encoding="utf-8")
    print(f"{total} périodes de vacances écrites dans {CIBLE}")


if __name__ == "__main__":
    main()
