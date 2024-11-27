import ast
import os
import random
import re
import time
from math import floor, ceil
from pathlib import Path
from pprint import pp

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


def normalize_data(sf: Series, prov_name: str) -> dict:
    prov = sf.loc[prov_name].lower()
    if prov == "balears, illes":
        prov = "illes balears"
    elif prov == "bizkaia":
        prov = "vizcaya"
    elif prov == "rioja, la":
        prov = "la rioja"
    elif prov == "gipuzkoa":
        prov = "guipúzcoa"
    elif prov == "coruña, a":
        prov = "a coruña"
    elif prov == "palmas, las":
        prov = "las palmas"
    elif prov == "valencia":
        prov = "valencia/valència"
    elif prov == "alicante":
        prov = "alicante/alacant"
    elif prov == "castellón":
        prov = "castellón/castelló"
    elif prov == "araba/álava":
        prov = "álava"

    max_coor = df_max.loc[[prov]].to_dict()
    min_coor = df_min.loc[[prov]].to_dict()
    lat_edges = (max_coor["Latitud"][prov], min_coor["Latitud"][prov])
    lon_edges = (max_coor["Longitud"][prov], min_coor["Longitud"][prov])

    if "Dirección" in sf.index:
        direccion = sf.loc["Dirección"].lower()
    elif "DIRECCION" in sf.index:
        direccion = sf.loc["DIRECCION"].lower()

    if "Código Postal" in sf.index:
        try:
            cp = str(int(sf.loc["Código Postal"])).zfill(5)
        except ValueError as e:
            cp = None
    elif "CP" in sf.index:
        cp = str(int(sf.loc["CP"])).zfill(5)

    if "Municipio" in sf.index:
        direccion = ", ".join([direccion, sf.loc["Municipio"], cp, prov])
    elif "MUNICIPIO" in sf.index:
        direccion = ", ".join([direccion, sf.loc["MUNICIPIO"], cp, prov])

    print("-" * 100)
    print("INFO - calculando coordenadas geofráficas.")
    print(f"\tdireccion: {direccion}")
    resp = get_coordinates(direccion, lat_edges=lat_edges, long_edges=lon_edges)

    print(f"INFO - nuevas coordenadas: {resp}")

    sf.loc["latitude"] = resp[0]
    sf.loc["longitude"] = resp[1]

    time.sleep(1.5 + random.random())

    return sf.to_dict()


def save_csv(df: pd.DataFrame, file_name: str) -> None:
    print("INFO - Guardada copia temporal de 'sanidad_primaria.csv'")
    # df_final.to_csv(SANIDAD_HOSP_FINAL, index=False, sep="\t")
    df.to_csv(file_name, index=False, sep="\t")


SANIDAD_HOSP = Path("../scrapy_data/spiders/data/sns_hospital.csv")
SANIDAD_HOSP_FINAL = Path("data/sanidad_hospital.csv")
if not SANIDAD_HOSP_FINAL.exists():
    df = pd.read_csv(SANIDAD_HOSP, sep="\t")
    for i in range(df.shape[0]):
        print(f"{i} - ", end="")
        document = normalize_data(df.iloc[i, :], "Provincia")
        # break
        if i == 0:
            df_final = pd.DataFrame.from_dict(document, orient="index").T
        elif i > 0:
            new_row = pd.DataFrame.from_dict(document, orient="index").T
            df_final = pd.concat([df_final, new_row])

    save_csv(df_final, SANIDAD_HOSP_FINAL)

    # df_final.to_csv(SANIDAD_HOSP_FINAL, index=False, sep="\t")

# if SANIDAD_HOSP_FINAL.exists():
#     conn = MongoDBConnect(container_name="mongo-tfm", database="tfm-data")
#     col = conn.collection(
#         name="ayuntamientos",
#         mode="create",
#         # delete=True,
#     )
#     df_tmp = pd.read_csv(SANIDAD_HOSP_FINAL, sep="\t")
#     for j in range(df_tmp.shape[0]):
#         print(j)
#         document = df_tmp.iloc[j, :].to_dict()
#         # print(document)
#         # break
#         conn.insert(collection=col, data=document)

#     conn.db_manage(list_collections=True)
#     conn.close()


SANIDAD_PRIM = Path("../scrapy_data/spiders/data/sns_primaria.csv")
SANIDAD_PRIM_FINAL = Path("data/sanidad_primaria.csv")
SANIDAD_PRIM_PARCIAL = Path("data/sanidad_primaria_parcial.csv")
if not SANIDAD_PRIM_FINAL.exists():
    if not SANIDAD_PRIM_PARCIAL.exists():
        df = pd.read_csv(SANIDAD_PRIM, sep="\t")
    else:
        df0 = pd.read_csv(SANIDAD_PRIM, sep="\t")
        all_ccn = set(df0.loc[:, "IDCENTRO"].to_list())
        print(f"total: {len(all_ccn)}")
        df1 = pd.read_csv(SANIDAD_PRIM_PARCIAL, sep="\t")
        par_ccn = df1.loc[:, "IDCENTRO"].to_list()
        print(f"hay: {len(par_ccn)}")
        res_ccn = urls_rest = list(all_ccn.difference(set(par_ccn)))
        print(f"quedan: {len(res_ccn)}")

        df = df0[~df0.loc[:, "IDCENTRO"].isin(par_ccn)]

    for i in range(df.shape[0]):
        print(f"{i} - ", end="")
        document = normalize_data(df.iloc[i, :], "SIAP_PROVINCIAS.NOMBRE")
        # break
        if i == 0 and not SANIDAD_PRIM_PARCIAL.exists():
            df_final = pd.DataFrame.from_dict(document, orient="index").T
        elif i == 0 and SANIDAD_PRIM_PARCIAL.exists():
            new_row = pd.DataFrame.from_dict(document, orient="index").T
            df_final = pd.concat([df1, new_row])
        elif i > 0:
            new_row = pd.DataFrame.from_dict(document, orient="index").T
            df_final = pd.concat([df_final, new_row])

        if i % 500 == 0 and i != 0:
            save_csv(df_final, SANIDAD_PRIM_PARCIAL)
            # break

    save_csv(df_final, SANIDAD_PRIM_FINAL)
    SANIDAD_PRIM_PARCIAL.unlink()

# SANIDAD_URGE = Path("../scrapy_data/spiders/data/sns_urgente.csv")
# SANIDAD_URGE_FINAL = Path("data/sanidad_urgente.csv")
# if not SANIDAD_URGE_FINAL.exists():
#     df = pd.read_csv(SANIDAD_URGE, sep="\t")
#     for i in range(df.shape[0]):
#         print(f"{i} - ", end="")
#         document = normalize_data(df.iloc[i, :])
#         break
#         if i == 0:
#             df_final = pd.DataFrame.from_dict(document, orient="index").T
#         elif i > 0:
#             new_row = pd.DataFrame.from_dict(document, orient="index").T
#             df_final = pd.concat([df_final, new_row])

#     df_final.to_csv(SANIDAD_URGE_FINAL, index=False, sep="\t")
