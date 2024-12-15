import ast
from pathlib import Path

import geopandas as gpd
import pandas as pd

# GASOLINERAS -----------------------------------------------------------------------
gaso = pd.read_csv(Path("data/gasolineras.csv"), sep="\t")
gaso.latitud = gaso.latitud.apply(lambda x: ast.literal_eval(x.replace(",", ".")))
gaso.longitud = gaso.longitud.apply(lambda x: ast.literal_eval(x.replace(",", ".")))
gaso.rename(
    columns={"latitud": "latitude", "longitud": "longitude", "provincia": "province"},
    inplace=True,
)

gaso_canar = gaso[
    gaso.province.apply(lambda x: x in ["santa cruz de tenerife", "palmas (las)"])
]
gaso_penin = gaso[
    ~gaso.province.apply(lambda x: x in ["santa cruz de tenerife", "palmas (las)"])
]

# ELECTROLINERAS -----------------------------------------------------------------------
elec = pd.read_csv(Path("data/electrolineras.csv"), sep="\t")
elec.loc[:, "province"] = elec.province.apply(lambda x: x.lower())
elec.loc[:, "province"] = elec.province.apply(
    lambda x: "alicante" if x == "alicante/alacant" else x
)
elec.loc[:, "province"] = elec.province.apply(
    lambda x: "castellón / castelló" if x == "castellón/castelló" else x
)
elec.loc[:, "province"] = elec.province.apply(
    lambda x: "rioja (la)" if x == "rioja, la" else x
)
elec.loc[:, "province"] = elec.province.apply(
    lambda x: "valencia / valència" if x == "valencia/valència" else x
)
elec.loc[:, "province"] = elec.province.apply(
    lambda x: "balears (illes)" if x == "balears, illes" else x
)
elec.loc[:, "province"] = elec.province.apply(
    lambda x: "coruña (a)" if x == "coruña, a" else x
)

elec_canar = elec[
    elec.province.apply(lambda x: x in ["Santa Cruz de Tenerife", "Palmas, Las"])
]
elec_canar.loc[:, "province"] = elec_canar.province.apply(
    lambda x: "palmas (las)" if x == "Palmas, Las" else x.lower()
)


elec_penin = elec[
    ~elec.province.apply(lambda x: x in ["Santa Cruz de Tenerife", "Palmas, Las"])
]


# AREAS -----------------------------------------------------------------------------
ccaa_shp = "SHP_REGCAN95/recintos_provinciales_inspire_canarias_regcan95/recintos_provinciales_inspire_canarias_regcan95.shp"
areas_canarias = gpd.read_file(ccaa_shp, encoding="utf-8")
areas_canarias.NAMEUNIT = areas_canarias.NAMEUNIT.apply(lambda x: x.lower())
areas_canarias.loc[0, "NAMEUNIT"] = "palmas (las)"

ccaa_shp_2 = "SHP_ETRS89/recintos_provinciales_inspire_peninbal_etrs89/recintos_provinciales_inspire_peninbal_etrs89.shp"
areas_espania = gpd.read_file(ccaa_shp_2, encoding="utf-8")
areas_espania.NAMEUNIT = areas_espania.NAMEUNIT.apply(lambda x: x.lower())
areas_espania.loc[2, "NAMEUNIT"] = "alicante"
areas_espania.loc[6, "NAMEUNIT"] = "balears (illes)"
areas_espania.loc[11, "NAMEUNIT"] = "castellón / castelló"
areas_espania.loc[14, "NAMEUNIT"] = "coruña (a)"
areas_espania.loc[25, "NAMEUNIT"] = "rioja (la)"
areas_espania.loc[43, "NAMEUNIT"] = "valencia / valència"
