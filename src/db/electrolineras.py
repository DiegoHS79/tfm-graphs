import os

import pandas as pd
from bs4 import BeautifulSoup


os.system("clear")

with open("data/electrolineras.xml", "r") as f:
    data = f.read()

soup = BeautifulSoup(data, "xml")

# info para el data frame
# columns = ["id", "name"]

electrolineras = soup.find_all("energyInfrastructureSite")
all_electro = []
for electro in electrolineras:
    elec_data = {}
    elec_data.update({"id": electro.get("id")})

    name1 = electro.find("fac:name")
    name2 = name1.find("com:value")
    elec_data.update({"name": name2.text})

    location = electro.find("fac:locationReference")
    loc_desc = location.find_all("locx:addressLine")
    for loc in loc_desc:
        value = loc.find("com:value").text
        if "Direc" in value:
            elec_data.update({"address": value.replace("Dirección: ", "")})
        elif "Muni" in value:
            elec_data.update({"city": value.replace("Municipio: ", "")})
        elif "Prov" in value:
            elec_data.update({"province": value.replace("Provincia: ", "")})
        elif "Comu" in value:
            elec_data.update({"ccaa": value.replace("Comunidad Autónoma: ", "")})

    elec_data.update({"latitude": location.find("loc:latitude").text})
    elec_data.update({"longitude": location.find("loc:longitude").text})

    all_electro.append(elec_data)

    # break

df = pd.DataFrame.from_dict(all_electro)
df.to_csv("data/electrolineras.csv", index=False, sep="\t")
