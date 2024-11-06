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
    # print(sf)
    prov = sf.loc["province"]
    if prov == "alicante":
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

    max_coor = df_max.loc[[prov]].to_dict()
    min_coor = df_min.loc[[prov]].to_dict()
    lat_edges = (max_coor["Latitud"][prov], min_coor["Latitud"][prov])
    lon_edges = (max_coor["Longitud"][prov], min_coor["Longitud"][prov])

    retake_coords = False
    take_count = 0
    for ind in sf.index:
        if ind in [
            "attr_type_description",
            "attr_cursos",
            "attr_telephone",
            "attr_fax",
        ] and isinstance(sf.loc[ind], float):
            continue
        if ind in ["attr_type_description", "attr_cursos"]:
            sf.loc[ind] = eval(sf.loc[ind].replace("\\xa0", ""))
        elif ind in ["attr_telephone", "attr_fax"] and len(sf.loc[ind].strip()) > 8:
            number = re.findall("\d+", sf.loc[ind].strip())[0]
            sf.loc[ind] = ast.literal_eval(number)
        elif ind == "latitude":
            lat = sf.loc[ind]
            if lat > ceil(lat_edges[0]) or lat < floor(lat_edges[1]):
                retake_coords = True
                take_count += 1
        elif ind == "longitude":
            lon = sf.loc[ind]
            if (
                lon > ceil(lon_edges[0]) or lon < floor(lon_edges[1])
            ) and take_count == 0:
                retake_coords = True

        if retake_coords:
            print("-" * 100)
            print(
                f"INFO - coordenadas incorrectas: ({sf.loc['latitude']}, {sf.loc['longitude']})"
            )
            print(
                f"\tdireccion: {', '.join([sf.loc['address'], sf.loc['city'], sf.loc['province']])}"
            )
            direccion = ", ".join(
                [sf.loc["address"], sf.loc["city"], sf.loc["province"]]
            )
            resp = get_coordinates(direccion, lat_edges=lat_edges, long_edges=lon_edges)

            print(f"INFO - nuevas coordenadas: {resp}")

            time.sleep(1.5 + random.random())

            retake_coords = False

    return sf.to_dict()

    # print()
    # for ind in sf.index:
    #     print(ind, sf.loc[ind], type(sf.loc[ind]), sep=" : ")


CENTROS = Path("../scrapy_data/spiders/data/centros_educacion_info_final.csv")
CENTROS_FINAL = Path("data/centros_educacion.csv")
if not CENTROS_FINAL.exists():
    df = pd.read_csv(CENTROS, sep="\t")
    for i in range(df.shape[0]):
        # document = df.iloc[i, :].to_dict()
        print(f"{i} - ", end="")
        document = normalize_data(df.iloc[i, :])
        if i == 0:
            df_final = pd.DataFrame.from_dict(document, orient="index").T
        elif i > 0:
            new_row = pd.DataFrame.from_dict(document, orient="index").T
            df_final = pd.concat([df_final, new_row])

    df_final.to_csv(CENTROS_FINAL, index=False, sep="\t")


if CENTROS_FINAL.exists:
    conn = MongoDBConnect(container_name="mongo-tfm", database="tfm-data")
    col = conn.collection(
        name="education",
        mode="create",
        # delete=True,
    )
    df_tmp = pd.read_csv(CENTROS, sep="\t")
    for j in range(df_tmp.shape[0]):
        document = df_tmp.iloc[i, :].to_dict()
        conn.insert(collection=col, data=document)

    conn.db_manage(list_collections=True)
    conn.close()
