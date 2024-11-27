from pathlib import Path

import pandas as pd

app_dir = Path(__file__).parent
# df = pd.read_csv(app_dir / "penguins.csv")

gaso = pd.read_csv(app_dir / "gasolineras.csv", sep="\t")
elec = pd.read_csv(app_dir / "electrolineras.csv", sep="\t")

# tokyo = pd.read_csv(
#     "https://geographicdata.science/book/_downloads/7fb86b605af15b3c9cbd9bfcbead23e9/tokyo_clean.csv"
# )

if __name__ == "__main__":
    print(gaso.provincia.unique())
    print(elec.ccaa.unique())
