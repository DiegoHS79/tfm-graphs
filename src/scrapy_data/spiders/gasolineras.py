import ast
import json
import os
import re
from pathlib import Path

import pandas as pd
import requests

# from bs4 import BeautifulSoup

from utils import get_user_agent

os.system("clear")

GP_FILE = Path("data/gasolineras_v0.csv")
if not GP_FILE.exists():
    GASO_URL = "https://sedeaplicaciones.minetur.gob.es/ServiciosRESTCarburantes/PreciosCarburantes/EstacionesTerrestres/"
    resp = requests.get(GASO_URL, headers={"user-agent": get_user_agent()})

    df = pd.read_json(resp.text)
    df.to_csv(GP_FILE, index=False, sep="\t")
else:
    df = pd.read_csv(GP_FILE, sep="\t")

for i, row in enumerate(df.ListaEESSPrecio):
    rep = re.findall(", 'remisión'.+", row.lower())[0]
    row = row.lower().replace(rep, "}").replace("'", '"').replace("\\", "")

    rep2 = re.findall('(?<="dirección": ")(.*)(?=", "horario")', row)[0]
    rep2_r = rep2.replace('"', "'")
    row = row.replace(rep2, rep2_r)

    rep3 = re.findall('(?<="localidad": ")(.*)(?=", "longitud)', row)[0]
    rep3_r = rep3.replace('"', "'")
    row = row.replace(rep3, rep3_r)

    rep4 = re.findall('(?<="municipio": ")(.*)(?=", "precio biodiesel)', row)[0]
    rep4_r = rep4.replace('"', "'")
    row = row.replace(rep4, rep4_r)

    row = json.loads(row)

    df = pd.DataFrame((k, v) for k, v in row.items()).T
    df.columns = df.iloc[0]
    df.drop(df.index[0], inplace=True)

    if i == 0:
        dff = df.copy()
    else:
        dff = pd.concat([dff, df])

    dff.drop(
        columns=[
            "precio biodiesel",
            "precio bioetanol",
            "precio gas natural comprimido",
            "precio gas natural licuado",
            "precio gases licuados del petróleo",
            "precio gasoleo a",
            "precio gasoleo b",
            "precio gasoleo premium",
            "precio gasolina 95 e10",
            "precio gasolina 95 e5",
            "precio gasolina 95 e5 premium",
            "precio gasolina 98 e10",
            "precio gasolina 98 e5",
            "precio hidrogeno",
        ],
        axis=1,
        inplace=True,
    )

dff.to_csv(Path("data/gasolineras_v1.csv"), index=False, sep="\t")
