import ast
import os
import random
import re
import time
from pathlib import Path
from pprint import pp
from math import floor, ceil

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
    # print("*" * 200)
    # [A-zÀ-ú] // accepts lowercase and uppercase characters
    # [A-zÀ-ÿ] // as above, but including letters with an umlaut (includes [ ] ^ \ × ÷)
    # [A-Za-zÀ-ÿ] // as above but not including [ ] ^ \
    # [A-Za-zÀ-ÖØ-öø-ÿ] // as above, but not including [ ] ^ \ × ÷
    direction = sf.address.lower()
    prov0 = re.findall("\(.*\)", direction)
    if not prov0:
        prov = None
    else:
        prov = prov0[0].strip("()")
    sf.loc["province"] = prov

    city0 = re.findall("[a-zà-ú ]+", direction.split(",")[-1])
    if not city0:
        city = None
    else:
        city = city0[-2].strip()
    sf.loc["city"] = city

    cp0 = re.findall("cp \d+", direction)
    if not cp0:
        cp = None
    else:
        cp = cp0[0].replace("cp ", "")
    sf.loc["cp"] = cp

    if prov == "santander":
        prov = "cantabria"
    elif prov == "alicante":
        prov = "alicante/alacant"
    elif prov == "araba/álava":
        prov = "álava"
    elif prov == "bizkaia":
        prov = "vizcaya"
    elif prov == "castellón":
        prov = "castellón/castelló"
    elif prov == "gipuzkoa":
        prov = "guipúzcoa"
    elif prov == "valencia":
        prov = "valencia/valència"
    elif not prov:
        prov = "zaragoza"

    max_coor = df_max.loc[[prov]].to_dict()
    min_coor = df_min.loc[[prov]].to_dict()
    lat_edges = (max_coor["Latitud"][prov], min_coor["Latitud"][prov])
    lon_edges = (max_coor["Longitud"][prov], min_coor["Longitud"][prov])

    tel = sf.loc["telephone"]
    if "/" in tel:
        tel = tel.split("/")[0]
    sf.loc["telephone"] = ast.literal_eval(tel)

    print("-" * 100)
    print(f"\tdireccion: {sf.loc['address']}")
    resp = get_coordinates(sf.loc["address"], lat_edges=lat_edges, long_edges=lon_edges)

    print(f"INFO - nuevas coordenadas: {resp}")

    sf.loc["latitude"] = resp[0]
    sf.loc["longitude"] = resp[1]

    return sf.to_dict()


UNIVERSIDADES = Path("../scrapy_data/spiders/data/centros_educacion_universidades.csv")
UNIVERSIDADES_FINAL = Path("data/universidades.csv")
if not UNIVERSIDADES_FINAL.exists():
    df = pd.read_csv(UNIVERSIDADES, sep="\t")
    for i in range(df.shape[0]):
        print(f"{i} - ", end="")
        document = normalize_data(df.iloc[i, :])
        # break
        if i == 0:
            df_final = pd.DataFrame.from_dict(document, orient="index").T
        elif i > 0:
            new_row = pd.DataFrame.from_dict(document, orient="index").T
            df_final = pd.concat([df_final, new_row])

    df_final.to_csv(UNIVERSIDADES_FINAL, index=False, sep="\t")


if UNIVERSIDADES_FINAL.exists:
    conn = MongoDBConnect(container_name="mongo-tfm", database="tfm-data")
    col = conn.collection(
        name="unversidades",
        mode="create",
        # delete=True,
    )
    df_tmp = pd.read_csv(UNIVERSIDADES_FINAL, sep="\t")
    for j in range(df_tmp.shape[0]):
        document = df_tmp.iloc[j, :].to_dict()
        conn.insert(collection=col, data=document)

    conn.db_manage(list_collections=True)
    conn.close()
