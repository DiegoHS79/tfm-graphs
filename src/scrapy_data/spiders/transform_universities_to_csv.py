import os

import pandas as pd

os.system("clear")

df = pd.read_json("data/centros_educacion_universidades.jsonl", lines=True)
df = df.map(lambda x: x[0], na_action="ignore")
# dup = ~df2.duplicated()
# df = df[dup]
# extract value
# print(df.columns)
# for col in df.columns:
#     if col in ["attr_type_description", "attr_cursos"]:
#         continue

#     print(col)
#     df[col] = df[col].apply(lambda x: None if isinstance(x, float) else x[0])

# for t in df["attr_mail"]:
#     print(type(t))

df.to_csv("data/centros_educacion_universidades.csv", index=False, sep="\t")
