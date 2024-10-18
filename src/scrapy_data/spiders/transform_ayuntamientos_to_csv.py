import os
from pathlib import Path

import pandas as pd

os.system("clear")

CSV = "data/ayuntamientos_detalle.csv"
if Path(CSV).exists():
    df = pd.read_csv(CSV, sep="\t")
else:
    df = pd.read_json("data/ayuntamientos_detalle.jsonl", lines=True)
    df = df.map(lambda x: x[0], na_action="ignore")

for name in df.name[df.cp == "Unknown"].to_list():
    print(f"### Detalles del ayuntamiento de: {name} ###")
    # print(df.loc[df.name == name])
    prov = input("\tProvincia: ")
    df.loc[df.name == name, ["province"]] = prov.strip()

    addr = input("\tDireccion: ")
    df.loc[df.name == name, ["address"]] = addr.strip()

    cp = input("\tCodigo postal: ")
    df.loc[df.name == name, ["cp"]] = cp.strip()

    mail = input("\tEmail: ")
    df.loc[df.name == name, ["email"]] = mail.strip()

    web = input("\tWEB: ")
    df.loc[df.name == name, ["web"]] = web.strip()

    tel = input("\tTelefono: ")
    df.loc[df.name == name, ["telefono"]] = tel.strip()

    fax = input("\tFax: ")
    df.loc[df.name == name, ["fax"]] = fax.strip()

    df.to_csv(CSV, index=False, sep="\t")
