import ast
import os
import random
import re
import sys
import time
from pathlib import Path
from pprint import pp
from math import floor, ceil

import numpy as np
import pandas as pd
from pandas import Series

from utils.mongo_db import MongoDBConnect
from utils.geo_coords import get_coordinates

os.system("clear")
pd.options.mode.copy_on_write = True

# LAT y LONG de las comunidades
GEO_COM = Path("data/listado-longitud-latitud-municipios-espana.xls")
GEO_COM_MAX = Path("data/coords_com_max.csv")
GEO_COM_MIN = Path("data/coords_com_min.csv")
if not GEO_COM_MAX.exists() or not GEO_COM_MIN.exists():
    df_com = pd.read_excel(GEO_COM, sheet_name="Hoja1", header=2)
    df_com["Comunidad"] = df_com["Comunidad"].apply(lambda x: x.lower())
    df = df_com.loc[:, ["Comunidad", "Latitud", "Longitud"]]

    df_com_max = df.groupby(["Comunidad"]).max()
    df_com_max.to_csv(GEO_COM_MAX, sep="\t")
    df_com_min = df.groupby(["Comunidad"]).min()
    df_com_min.to_csv(GEO_COM_MIN, sep="\t")
else:
    df_com_max = pd.read_csv(GEO_COM_MAX, sep="\t")
    df_com_max.set_index("Comunidad", inplace=True)
    df_com_min = pd.read_csv(GEO_COM_MIN, sep="\t")
    df_com_min.set_index("Comunidad", inplace=True)


def normalize_data(sf: Series) -> dict:
    com = sf.loc["community"].lower()
    if com == "comunitat valenciana":
        com = "valencia"
    elif com == "cataluña":
        com = "catalunya"
    elif com == "illes balears":
        com = "islas baleares"
    elif com == "comunidad de madrid":
        com = "madrid"
    elif com == "andalucia":
        com = "andalucía"
    elif com == "region de murcia":
        com = "murcia"

    max_coor = df_com_max.loc[[com]].to_dict()
    min_coor = df_com_min.loc[[com]].to_dict()
    lat_edges = (max_coor["Latitud"][com], min_coor["Latitud"][com])
    lon_edges = (max_coor["Longitud"][com], min_coor["Longitud"][com])

    tel = sf.loc["telephone"]
    if "/" in str(tel):
        tel = tel.split("/")[0]

    if tel is not np.nan:
        sf.loc["telephone"] = ast.literal_eval(tel)

    print("-" * 100)
    direction = f"{sf.loc['address']}, {sf.loc['cp']}, {sf.loc['city']}, ({com})"
    print(f"\tdireccion: {direction}")
    resp = get_coordinates(direction, lat_edges=lat_edges, long_edges=lon_edges)

    print(f"INFO - nuevas coordenadas: {resp}")
    sf.loc["latitude"] = resp[0]
    sf.loc["longitude"] = resp[1]

    return sf.to_dict()


CORREOS = Path("../scrapy_data/spiders/data/correos_oficinas.jsonl")
CORREOS_FINAL = Path("data/correos.csv")
if not CORREOS_FINAL.exists():
    df = pd.read_json(CORREOS, lines=True)
    df = df.map(lambda x: x[0], na_action="ignore")
    for i in range(df.shape[0]):
        print(f"{i} - ", end="")
        document = normalize_data(df.iloc[i, :])
        # break
        if i == 0:
            df_final = pd.DataFrame.from_dict(document, orient="index").T
        elif i > 0:
            new_row = pd.DataFrame.from_dict(document, orient="index").T
            df_final = pd.concat([df_final, new_row])

    df_final.to_csv(CORREOS_FINAL, index=False, sep="\t")


if CORREOS_FINAL.exists:
    conn = MongoDBConnect(container_name="mongo-tfm", database="tfm-data")
    col = conn.collection(
        name="correos",
        mode="create",
        # delete=True,
    )
    df_tmp = pd.read_csv(CORREOS_FINAL, sep="\t")
    for j in range(df_tmp.shape[0]):
        document = df_tmp.iloc[j, :].to_dict()
        conn.insert(collection=col, data=document)

    conn.db_manage(list_collections=True)
    conn.close()
