import os
from pathlib import Path
import pandas as pd

os.system("clear")

GEO_COM = Path("data/listado-longitud-latitud-municipios-espana.xls")
GEO_MUN = Path("data/coords_municipios.csv")

df_com = pd.read_excel(GEO_COM, sheet_name="Hoja1", header=2)
df_com.to_csv(GEO_MUN, index=False, sep="\t")
