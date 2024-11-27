import ast
import os
import random
import re
import sys
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
    # print(sf)
    prov = sf.loc[prov_name].lower()
    # if prov == "balears, illes":
    #     prov = "illes balears"
    # elif prov == "coruña, a":
    #     prov = "a coruña"
    # elif prov == "castellón":
    #     prov = "castellón/castelló"
    if prov == "alava":
        prov = "álava"
    elif prov == "alicante":
        prov = "alicante/alacant"
    elif prov == "caceres":
        prov = "cáceres"
    elif prov == "cadiz":
        prov = "cádiz"
    elif prov == "guipuzcoa":
        prov = "guipúzcoa"
    elif prov == "valencia":
        prov = "valencia/valència"

    max_coor = df_max.loc[[prov]].to_dict()
    min_coor = df_min.loc[[prov]].to_dict()
    lat_edges = (max_coor["Latitud"][prov], min_coor["Latitud"][prov])
    lon_edges = (max_coor["Longitud"][prov], min_coor["Longitud"][prov])

    if "address" in sf.index:
        if isinstance(sf.loc["address"], str):
            direccion = sf.loc["address"].lower()
        else:
            direccion = ""
    else:
        direccion = ""

    try:
        cp = str(int(sf.loc["cp"])).zfill(5)
    except ValueError as e:
        cp = ""

    direccion = ", ".join([direccion, sf.loc["city"], cp, prov])

    print("-" * 100)
    print("INFO - calculando coordenadas geofráficas.")
    print(f"\tdireccion: {direccion}")
    resp = get_coordinates(direccion, lat_edges=lat_edges, long_edges=lon_edges)
    if resp is None:
        print("\t\nIntroduce las coordenadas manualmente")
        user_lat = input("\t\tLatitud: ")
        user_long = input("\t\tLongitud: ")
        sf.loc["latitude"] = user_lat
        sf.loc["longitude"] = user_long
        print()
    else:
        print(f"INFO - nuevas coordenadas: {resp}")

        sf.loc["latitude"] = resp[0]
        sf.loc["longitude"] = resp[1]

    time.sleep(1.5 + random.random())

    return sf.to_dict()


def save_csv(df: pd.DataFrame, file_name: str) -> None:
    print("INFO - Guardada copia temporal de 'sanidad_primaria.csv'")
    df.to_csv(file_name, index=False, sep="\t")


EMPRESAS_PARCIAL = Path("data/empresas_parcial.csv")
for i in range(43):
    if i in [0]:
        continue
    EMPRESAS_FINAL = Path(f"data/empresas_{i}.csv")
    if not EMPRESAS_FINAL.exists():
        EMPRESAS = Path(f"../scrapy_data/spiders/data/empresas/empresas_{i}.jsonl")
        if not EMPRESAS_PARCIAL.exists():
            df = pd.read_json(EMPRESAS, lines=True)
            df = df.map(lambda x: x[0], na_action="ignore")
            df.drop_duplicates(inplace=True)

        else:
            df0 = pd.read_json(EMPRESAS, lines=True)
            df0 = df0.map(lambda x: x[0], na_action="ignore")
            df0.drop_duplicates(inplace=True)
            all_ccn = set(df0.loc[:, "cif"].to_list())
            print(f"total: {len(all_ccn)}")

            df1 = pd.read_csv(EMPRESAS_PARCIAL, sep="\t")
            par_ccn = df1.loc[:, "cif"].to_list()
            print(f"hay: {len(par_ccn)}")

            res_ccn = urls_rest = list(all_ccn.difference(set(par_ccn)))
            print(f"quedan: {len(res_ccn)}")

            df = df0[~df0.loc[:, "cif"].isin(par_ccn)]

        for i in range(df.shape[0]):
            print(f"{i} - ", end="")
            document = normalize_data(df.iloc[i, :], "province")
            # break
            if i == 0 and not EMPRESAS_PARCIAL.exists():
                df_final = pd.DataFrame.from_dict(document, orient="index").T
            elif i == 0 and EMPRESAS_PARCIAL.exists():
                new_row = pd.DataFrame.from_dict(document, orient="index").T
                df_final = pd.concat([df1, new_row])
            elif i > 0:
                new_row = pd.DataFrame.from_dict(document, orient="index").T
                df_final = pd.concat([df_final, new_row])

            if i % 10 == 0 and i != 0:
                save_csv(df_final, EMPRESAS_PARCIAL)

        save_csv(df_final, EMPRESAS_FINAL)
        # break

    EMPRESAS_PARCIAL.unlink()

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
