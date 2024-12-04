import ast
from pathlib import Path

import pandas as pd

app_dir = Path(__file__).parent

gaso = pd.read_csv(app_dir / "gasolineras.csv", sep="\t")
gaso.latitud = gaso.latitud.apply(lambda x: ast.literal_eval(x.replace(",", ".")))
gaso.longitud = gaso.longitud.apply(lambda x: ast.literal_eval(x.replace(",", ".")))
elec = pd.read_csv(app_dir / "electrolineras.csv", sep="\t")

# tokyo = pd.read_csv(
#     "https://geographicdata.science/book/_downloads/7fb86b605af15b3c9cbd9bfcbead23e9/tokyo_clean.csv"
# )

if __name__ == "__main__":
    import geopandas as gpd

    # print(gaso.provincia.unique())
    # print(elec.ccaa.unique())
    df = gaso[
        gaso.provincia.apply(
            lambda x: (
                True
                if x in ["alicante", "valencia / valència", "castellón / castelló"]
                else False
            )
        )
    ]
    df2 = elec[elec.ccaa == "Comunitat Valenciana"]

    # df = df[["latitud", "longitud"]]
    # df.rename(columns={"latitud": "latitude", "longitud": "longitude"}, inplace=True)
    # df.loc[:, "surtidor"] = "Gasolineras"

    # df2 = df[["latitude", "longitude"]]
    # df2.loc[:, "surtidor"] = "Electrolineras"

    # df3 = pd.concat([df, df2])

    # print(df3)

    # GEOPANDAS
    print(list(zip(df.longitud, df.latitud)))
    # geometry = gpd.points_from_xy(df.longitud, df.latitud, crs="EPSG:4326")
    # print(geometry)
