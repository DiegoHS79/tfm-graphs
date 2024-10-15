import os

import pandas as pd

os.system("clear")

df = pd.read_json("data/centros_educacion_universidades.jsonl", lines=True)
df = df.map(lambda x: x[0], na_action="ignore")

df.to_csv("data/centros_educacion_universidades.csv", index=False, sep="\t")
