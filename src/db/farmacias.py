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
GEO_MAX = Path("data/coords_max.csv")
GEO_MIN = Path("data/coords_min.csv")
if not GEO_MAX.exists() or not GEO_MIN.exists():
    df_com = pd.read_excel(GEO_COM, sheet_name="Hoja1", header=2)
    df_com["Provincia"] = df_com["Provincia"].apply(lambda x: x.lower())
    df = df_com.loc[:, ["Provincia", "Latitud", "Longitud"]]

    df_max = df.groupby(["Provincia"]).max()
    df_max.to_csv(GEO_MAX, sep="\t")
    df_min = df.groupby(["Provincia"]).min()
    df_min.to_csv(GEO_MIN, sep="\t")
else:
    df_max = pd.read_csv(GEO_MAX, sep="\t")
    df_max.set_index("Provincia", inplace=True)
    df_min = pd.read_csv(GEO_MIN, sep="\t")
    df_min.set_index("Provincia", inplace=True)


def normalize_data(sf: Series) -> dict:
    try:
        direction = sf.address.lower()
    except AttributeError as e:
        print(e)
        direction = ""
    prov = sf.loc["province"].lower()

    if prov == "jaen":
        prov = "jaén"
    elif prov == "malaga":
        prov = "málaga"
    elif prov == "leon":
        prov = "león"
    elif prov == "alava":
        prov = "álava"
    elif prov == "caceres":
        prov = "cáceres"
    elif prov == "cordoba":
        prov = "córdoba"
    elif prov == "avila":
        prov = "ávila"
    elif prov == "tenerife":
        prov = "santa cruz de tenerife"
    elif prov == "alacant":
        prov = "alicante/alacant"
    elif prov == "castello":
        prov = "castellón/castelló"
    elif prov == "valencia":
        prov = "valencia/valència"
    elif prov == "balears":
        prov = "illes balears"
    elif prov == "guipuzcoa":
        prov = "guipúzcoa"

    max_coor = df_max.loc[[prov]].to_dict()
    min_coor = df_min.loc[[prov]].to_dict()
    lat_edges = (max_coor["Latitud"][prov], min_coor["Latitud"][prov])
    lon_edges = (max_coor["Longitud"][prov], min_coor["Longitud"][prov])

    tel = sf.loc["telephone"]
    if "/" in str(tel):
        tel = tel.split("/")[0]

    if tel is not np.nan:
        sf.loc["telephone"] = ast.literal_eval(tel.strip().replace(" ", ""))

    print("-" * 100)
    try:
        cp = str(int(sf.loc["cp"])).zfill(5)
    except ValueError as e:
        print(e)
        cp = ""
    direction = f"{direction}, {sf.loc['city']}, {cp}, ({prov})"
    if (
        sf.loc["latitude"] > ceil(lat_edges[0])
        or sf.loc["latitude"] < floor(lat_edges[1])
        or sf.loc["longitude"] > ceil(lon_edges[0])
        or sf.loc["longitude"] < floor(lon_edges[1])
    ):
        print(f"\tdireccion: {direction}")
        resp = get_coordinates(direction, lat_edges=lat_edges, long_edges=lon_edges)

        print(f"INFO - nuevas coordenadas: {resp}")

        sf.loc["latitude"] = resp[0]
        sf.loc["longitude"] = resp[1]

        time.sleep(1.5 + random.random())
    else:
        print("INFO - No hace faltan calcular nuevas coordenadas.")

    return sf.to_dict()


FARMACIAS = Path("../scrapy_data/spiders/data/farmacias.csv")
FARMACIAS_FINAL = Path("data/farmacias.csv")
if not FARMACIAS_FINAL.exists():
    df = pd.read_csv(FARMACIAS, sep="\t")
    for i in range(df.shape[0]):
        print(f"{i} - ", end="")
        document = normalize_data(df.iloc[i, :])
        # break
        if i == 0:
            df_final = pd.DataFrame.from_dict(document, orient="index").T
        elif i > 0:
            new_row = pd.DataFrame.from_dict(document, orient="index").T
            df_final = pd.concat([df_final, new_row])

    df_final.to_csv(FARMACIAS_FINAL, index=False, sep="\t")


if FARMACIAS_FINAL.exists:
    conn = MongoDBConnect(container_name="mongo-tfm", database="tfm-data")
    col = conn.collection(
        name="farmacias",
        mode="create",
        # delete=True,
    )
    df_tmp = pd.read_csv(FARMACIAS_FINAL, sep="\t")
    for j in range(df_tmp.shape[0]):
        document = df_tmp.iloc[j, :].to_dict()
        conn.insert(collection=col, data=document)

    conn.db_manage(list_collections=True)
    conn.close()
