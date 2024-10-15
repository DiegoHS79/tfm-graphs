import os
from pathlib import Path

import pandas as pd
import requests

os.system("clear")

# Catálogo de Centros de Atención Primaria del SNS
LOCAL_SNS_PRIMARIA = Path("data/sns_primaria.xlsx")
LOCAL_SNS_PRIMARIA_CSV = Path("data/sns_primaria.csv")
if not LOCAL_SNS_PRIMARIA_CSV.exists():
    # ? https://www.sanidad.gob.es/estadEstudios/estadisticas/sisInfSanSNS/ofertaRecursos/centrosSalud/home.htm
    sns_primaria = "https://www.sanidad.gob.es/estadEstudios/estadisticas/docs/siap/2024_C_Catal_Centros_AP.xlsx"
    resp = requests.get(sns_primaria)
    with open(LOCAL_SNS_PRIMARIA, "wb") as outfile:
        outfile.write(resp.content)

    df = pd.read_excel(
        open(LOCAL_SNS_PRIMARIA, "rb"),
        sheet_name="Catálogo - 2024",
    )
    df.to_csv(LOCAL_SNS_PRIMARIA_CSV, index=False, sep="\t")


# Catálogo de Centros de Atención Urgente Extrahospitalaria
LOCAL_SNS_URGENTE = Path("data/sns_urgente.xlsx")
LOCAL_SNS_URGENTE_CSV = Path("data/sns_urgente.csv")
if not LOCAL_SNS_URGENTE_CSV.exists():
    # ? https://www.sanidad.gob.es/estadEstudios/estadisticas/sisInfSanSNS/ofertaRecursos/centrosSalud/home.htm
    sns_urgente = "https://www.sanidad.gob.es/estadEstudios/estadisticas/docs/siap/2024_C_Catal_disp_urg.xlsx"
    resp = requests.get(sns_urgente)
    with open(LOCAL_SNS_URGENTE, "wb") as outfile:
        outfile.write(resp.content)

    df = pd.read_excel(
        open(LOCAL_SNS_URGENTE, "rb"),
        sheet_name="Catálogo - 2024",
    )
    df.to_csv(LOCAL_SNS_URGENTE_CSV, index=False, sep="\t")

# Catálogo Nacional de Hospitales
LOCAL_SNS_HOSP = Path("data/sns_hospital.xlsx")
LOCAL_SNS_HOSP_CSV = Path("data/sns_hospital.csv")
if not LOCAL_SNS_HOSP_CSV.exists():
    # ? https://www.sanidad.gob.es/estadEstudios/estadisticas/sisInfSanSNS/ofertaRecursos/hospitales/home.htm
    sns_hospitales = "https://www.sanidad.gob.es/estadEstudios/estadisticas/sisInfSanSNS/ofertaRecursos/hospitales/docs/CNH_2024.xlsx"
    resp = requests.get(sns_hospitales)
    with open(LOCAL_SNS_HOSP, "wb") as outfile:
        outfile.write(resp.content)

    df = pd.read_excel(
        open(LOCAL_SNS_HOSP, "rb"),
        sheet_name="DIRECTORIO DE HOSPITALES",
    )
    df.to_csv(LOCAL_SNS_HOSP_CSV, index=False, sep="\t")
