import ast
import os
import random
import re
import time
from math import floor, ceil
from pathlib import Path
from pprint import pp

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
    prov = sf.loc["province"].lower()
    if prov == "bizkaia":
        prov = "vizcaya"
    elif prov == "rioja, la":
        prov = "la rioja"
    elif prov == "gipuzkoa":
        prov = "guipúzcoa"
    elif prov == "coruña, a":
        prov = "a coruña"
    elif prov == "palmas, las":
        prov = "las palmas"
    elif prov == "valència/valencia":
        prov = "valencia/valència"
    elif prov == "alacant/alicante":
        prov = "alicante/alacant"
    elif prov == "castelló/castellón":
        prov = "castellón/castelló"
    elif prov == "araba/álava":
        prov = "álava"

    max_coor = df_max.loc[[prov]].to_dict()
    min_coor = df_min.loc[[prov]].to_dict()
    lat_edges = (max_coor["Latitud"][prov], min_coor["Latitud"][prov])
    lon_edges = (max_coor["Longitud"][prov], min_coor["Longitud"][prov])

    for ind in sf.index:
        if ind in [
            "telefono",
            "fax",
        ] and isinstance(sf.loc[ind], float):
            continue

        if ind in ["telefono", "fax"]:
            number = re.findall("\d+", sf.loc[ind].strip())[0]
            sf.loc[ind] = ast.literal_eval(number)
        elif ind == "cp":
            sf.loc[ind] = f"{sf.loc[ind]}"
            if len(sf.loc[ind]) == 4:
                sf.loc[ind] = "0" + sf.loc[ind]

    print("-" * 100)
    print("INFO - calculando coordenadas geofráficas.")
    print(
        f"\tdireccion: {', '.join([sf.loc['address'], sf.loc['name'], sf.loc['cp'], sf.loc['province']])}"
    )
    direccion = ", ".join(
        [sf.loc["address"], sf.loc["name"], sf.loc["cp"], sf.loc["province"]]
    )
    resp = get_coordinates(direccion, lat_edges=lat_edges, long_edges=lon_edges)

    print(f"INFO - nuevas coordenadas: {resp}")

    sf.loc["latitude"] = resp[0]
    sf.loc["longitude"] = resp[1]

    time.sleep(1.5 + random.random())

    # print(sf.to_dict())

    return sf.to_dict()


AYUNTAMIENTOS = Path("../scrapy_data/spiders/data/ayuntamientos_detalle.csv")
AYUNTAMIENTOS_FINAL = Path("data/ayuntamientos_final.csv")
if not AYUNTAMIENTOS_FINAL.exists():
    df = pd.read_csv(AYUNTAMIENTOS, sep="\t")
    for i in range(df.shape[0]):
        print(f"{i} - ", end="")
        document = normalize_data(df.iloc[i, :])
        if i == 0:
            df_final = pd.DataFrame.from_dict(document, orient="index").T
        elif i > 0:
            new_row = pd.DataFrame.from_dict(document, orient="index").T
            df_final = pd.concat([df_final, new_row])

    df_final.to_csv(AYUNTAMIENTOS_FINAL, index=False, sep="\t")

if AYUNTAMIENTOS_FINAL.exists():
    conn = MongoDBConnect(container_name="mongo-tfm", database="tfm-data")
    col = conn.collection(
        name="ayuntamientos",
        mode="create",
        # delete=True,
    )
    df_tmp = pd.read_csv(AYUNTAMIENTOS_FINAL, sep="\t")
    for j in range(df_tmp.shape[0]):
        print(j)
        document = df_tmp.iloc[j, :].to_dict()
        # print(document)
        # break
        conn.insert(collection=col, data=document)

    conn.db_manage(list_collections=True)
    conn.close()