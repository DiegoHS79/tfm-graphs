import os
import re
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup

from utils import get_user_agent

os.system("clear")

TAXI_URL = "https://parada-taxi.com/paradas-taxi/"  # ?cerrar-compartir=1
headers = {"user-agent": get_user_agent()}
resp = requests.get(TAXI_URL, headers=headers)
soup = BeautifulSoup(resp.text, "html.parser")

urls = soup.select("div.listado-paginas-relacionadas:first-of-type li a")
URLS = {"url": [url.get("href") for url in urls]}

df_orig = pd.DataFrame(URLS)
dff = pd.DataFrame(
    columns=[
        "province",
        # "city",
        # "cp",
        "latitude",
        "longitude",
    ]
)
for URL in df_orig.url.to_list():
    print(URL)
    prov = re.findall("[a-z-]+", URL)[-1].lower()

    headers = {"user-agent": get_user_agent()}
    resp = requests.get(URL, headers=headers)
    soup = BeautifulSoup(resp.text, "html.parser")

    trs = soup.select("table.table-striped tbody tr")
    addrs = []
    # cities = []
    # cps = []
    lats = []
    longs = []
    for tr in trs:
        tds = tr.select("td + td")
        try:
            parada_text = tds[0].select("span")[0].text
        except IndexError as e:
            parada_text = ""
        address = tds[0].text.replace(parada_text, "").lower()
        addrs.append(address)
        # print(address)
        # info = address.split(",")
        # addr = "".join(info[0:-2])
        # addrs.append(addr)
        # print(addr)
        # city = info[-2].strip()
        # cp = re.findall("\d+", city)[0]
        # cps.append(cp)
        # print(cp)
        # cities.append(city.replace(cp, "").strip())
        # print(city)

        direc = tds[1].select("a")[0].get("href")
        coor = re.findall("[+-]?[0-9]+\.[0-9]+", direc)
        if len(coor) == 2:
            lat, long = coor
        elif len(coor) == 4:
            lat, long, _, _ = coor
        lats.append(lat)
        longs.append(long)
        # print(lat, long)
        # print()
        # break

    data = {
        "province": [prov] * len(trs),
        "address": address,
        # "city": cities,
        # "cp": cps,
        "latitude": lats,
        "longitude": longs,
    }

    dff = pd.concat([dff, pd.DataFrame(data)])
    print("*" * 200)

    # break

TAXI_CSV = Path("data/parada_taxi.csv")
dff.to_csv(TAXI_CSV, index=False, sep="\t")
