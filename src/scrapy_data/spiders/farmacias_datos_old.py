import os
import random
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup
from scrapy.crawler import CrawlerProcess
from scrapy.item import Field
from scrapy.item import Item
from scrapy.spiders import CrawlSpider, Rule
from scrapy.selector import Selector
from scrapy.linkextractors import LinkExtractor
from scrapy.loader import ItemLoader
from itemloaders.processors import MapCompose

from utils import get_user_agent

os.system("clear")

headers = {"user-agent": get_user_agent()}

# A CORUÑA
LOCAL_FARMA_CORUNA_CSV = Path("data/farma_acoruna.csv")
if not LOCAL_FARMA_CORUNA_CSV.exists():
    # ? https://www.cofc.es/farmacia/index
    # descargado directamente de la web en formato raw.
    # Lo guardo en forma de json en farma_acoruna.json
    df_a_coruna = pd.read_json("data/farma_acoruna.json")

    df_a_coruna = df_a_coruna.loc[
        :,
        [
            "nombre",
            "direccion",
            "latitud",
            "longitud",
            "telefono",
            "nombrePoblacion",
        ],
    ]

    df_a_coruna.to_csv(LOCAL_FARMA_CORUNA_CSV, index=False, sep="\t")

# ALICANTE
LOCAL_FARMA_ALI = Path("data/farma_alicante.xlsx")
LOCAL_FARMA_ALI_CSV = Path("data/farma_alicante.csv")
if not LOCAL_FARMA_ALI_CSV.exists():
    download_url = (
        "https://www.cofalicante.com/ficheros/listadofarmacias/Farmacias.xlsx"
    )
    response = requests.get(download_url, headers=headers)
    with open(LOCAL_FARMA_ALI, "wb") as outfile:
        outfile.write(response.content)

    df = pd.read_excel(
        open(LOCAL_FARMA_ALI, "rb"),
        # sheet_name="DIRECTORIO DE HOSPITALES",
    )
    df.to_csv(LOCAL_FARMA_ALI_CSV, index=False, sep="\t")

# ALMERIA
LOCAL_FARMA_ALME = Path("data/farma_almeria.jsonl")
LOCAL_FARMA_ALME_CSV = Path("data/farma_almeria.csv")
if not LOCAL_FARMA_ALME.exists():
    download_url = "https://www.cofalmeria.com/buscador-farmacias"
    response = requests.get(download_url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    farmas = soup.find_all("div", class_="FilaEntidades")
    name = []
    address = []
    telefono = []
    for farma in farmas:
        name.append(farma.find("a").getText().strip())
        info = farma.find_all("dd")
        if len(info) == 1:
            address.append(info[0].getText().strip().replace("\n", ""))
            telefono.append(None)
        elif len(info) == 2:
            addr, tel = info
            address.append(addr.getText().strip().replace("\n", ""))
            telefono.append(tel.getText().strip())
        elif len(info) == 3:
            addr, tel, _ = info
            address.append(addr.getText().strip().replace("\n", ""))
            telefono.append(tel.getText().strip())

    df = pd.DataFrame(
        {
            "name": name,
            "direccion": address,
            "telefono": telefono,
            "provincia": ["Almeria"] * len(name),
        }
    )
    df.to_csv(LOCAL_FARMA_ALME_CSV, index=False, sep="\t")

# ASTURIAS
# ? https://www.farmasturias.org/GESCOF/cms/Farmacias/FarmaciaBuscar.asp?IdMenu=93
LOCAL_FARMA_AST = Path("data/farma_asturias.jsonl")
LOCAL_FARMA_AST_CSV = Path("data/farma_asturias.csv")
if not LOCAL_FARMA_AST.exists():

    class DetallesCentro(Item):
        name = Field()
        city = Field()
        province = Field()
        address = Field()
        telephone = Field()

    class FarmaAsturiasSpider(CrawlSpider):
        name = "FarmaciasAsturias"
        start_urls = [
            "https://www.farmasturias.org/GESCOF/cms/Farmacias/FarmaciaBuscar.asp?IdMenu=93&intPagina=1"
        ]
        custom_settings = {
            "USER_AGENT": get_user_agent(),
            "CONCURRENT_REQUEST": 1,
            "FEEDS": {
                LOCAL_FARMA_AST: {
                    "format": "jsonlines",
                    "overwrite": True,
                    "encoding": "utf-8",
                    "fields": [
                        "name",
                        "city",
                        "province",
                        "address",
                        "telephone",
                    ],
                },
            },
        }
        download_delay = 1 + random.random()
        rules = (
            # Regla para Paginacion
            Rule(
                LinkExtractor(allow=r"&intPagina="),
                follow=True,
                callback="parse_horizontal",
            ),
        )

        def parse_horizontal(self, response):
            print("*" * 150)
            print("*" * 150)
            sel = Selector(response)
            farmas = sel.css("ul.ListadoResultados li")
            for farma in farmas:
                item = ItemLoader(DetallesCentro(), farma)

                spans = farma.css("span")
                for i, span in enumerate(spans):
                    if i == 0:
                        item.add_value("city", span.css("span::text").get().strip())
                    elif i == 1 or i >= 5:
                        continue
                    elif i == 2:
                        item.add_value("name", span.css("span::text").get().strip())
                    elif i == 3:
                        item.add_value(
                            "address",
                            span.css("span::text").get(),
                            MapCompose(lambda x: x.replace("Dirección:", "").strip()),
                        )
                    elif i == 4:
                        item.add_value(
                            "telephone",
                            span.css("span::text").get(),
                            MapCompose(lambda x: x.replace("Teléfono:", "").strip()),
                        )
                item.add_value("province", "Asturias")

                # break

                yield item.load_item()
            print("*" * 150)
            print("*" * 150)

    process = CrawlerProcess()
    process.crawl(FarmaAsturiasSpider)
    process.start()


if not LOCAL_FARMA_AST_CSV.exists():
    df = pd.read_json(LOCAL_FARMA_AST, lines=True)
    df = df.map(lambda x: x[0], na_action="ignore")

    df.drop_duplicates(inplace=True)
    df.to_csv(LOCAL_FARMA_AST_CSV, index=False, sep="\t")


# ALABA
# con selenium!!!!
# ? https://www.cofalava.org/Sec_DF/wf_directoriofarmacialst.aspx?IdMenu=1015


# BALEARES
# ? https://www.cofib.es/es/mapes_cercador.aspx


# HUESCA
# ? https://www.cofhuesca.com/farmacias
# creas un archivo desde el raw de la pagina
LOCAL_FARMA_HUES = Path("data/farma_huesca.html")
LOCAL_FARMA_HUES_CSV = Path("data/farma_huesca.csv")
if not LOCAL_FARMA_HUES_CSV.exists():
    with open(LOCAL_FARMA_HUES, "r") as zara_file:
        farma_hues = zara_file.readlines()

    soup = BeautifulSoup("".join(farma_hues).replace("\n", ""), "html.parser")
    names = []
    minicipios = []
    zonas = []
    direccion = []
    telefono = []
    for tr in soup.find_all("tr"):
        _, name, muni, zona, dire, tel = tr.find_all("td")
        names.append(name.getText().strip())
        minicipios.append(muni.getText().strip())
        zonas.append(zona.getText().strip())
        direccion.append(dire.getText().strip())
        telefono.append(tel.getText().strip())

    df = pd.DataFrame(
        {
            "name": names,
            "city": minicipios,
            "zona": zonas,
            "direccion": direccion,
            "telefono": telefono,
            "provincia": ["Huesca"] * len(names),
        }
    )
    df.to_csv(LOCAL_FARMA_HUES_CSV, index=False, sep="\t")


# TERUEL
# ? https://www.cofteruel.org/ciudadanos/listado-de-farmacias/?gl=0&localidad=&fecha=
LOCAL_FARMA_TER_CSV = Path("data/farma_teruel.csv")
if not LOCAL_FARMA_TER_CSV.exists():
    download_url = "https://www.cofteruel.org/ciudadanos/listado-de-farmacias/?gl=0&localidad=&fecha="
    response = requests.get(download_url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    # farmas = soup.find_all("div.listado_farmacias .category-box li > a")
    cont0 = soup.find_all("div", class_="listado_farmacias")
    cont1 = cont0[0].find_all("li")
    farmas_urls = []
    for cont in cont1:
        a_urls = cont.find_all("a")
        farmas_urls.append(a_urls[1].get("href"))

    names = []
    cities = []
    address = []
    telefono = []
    for url in farmas_urls:
        headers = {"user-agent": get_user_agent()}
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")

        name = soup.find_all("h1", class_="title")[0].getText().strip()
        names.append(name)

        tds = soup.find_all("table", class_="datosfarmacia")[0].find_all("td")
        for i, td in enumerate(tds):
            if i == 0:
                cities.append(td.getText())
            elif i == 1:
                address.append(td.getText())
            elif i == 2:
                telefono.append(td.getText())

    df = pd.DataFrame(
        {
            "name": names,
            "ciudad": cities,
            "direccion": address,
            "telefono": telefono,
            "provincia": ["Teruel"] * len(names),
        }
    )
    df.to_csv(LOCAL_FARMA_TER_CSV, index=False, sep="\t")


# ZARAGOZA
# ? https://cofzaragoza.org/listado-de-farmacias/
# creas un archivo desde el raw de la pagina con solo lo que necesitas <tr>
LOCAL_FARMA_ZAR = Path("data/farma_zaragoza.html")
LOCAL_FARMA_ZAR_CSV = Path("data/farma_zaragoza.csv")
if not LOCAL_FARMA_ZAR_CSV.exists():
    with open(LOCAL_FARMA_ZAR, "r") as zara_file:
        farma_zara = zara_file.readlines()

    soup = BeautifulSoup("".join(farma_zara).replace("\n", ""), "html.parser")
    names = []
    direccion = []
    cps = []
    minicipios = []
    for tr in soup.find_all("tr"):
        name, dire, cp, muni = tr.find_all("td")
        names.append(name.getText().strip())
        direccion.append(dire.getText().strip())
        cps.append(cp.getText().strip())
        minicipios.append(muni.getText().strip())
        # break

    df = pd.DataFrame(
        {
            "name": names,
            "direccion": direccion,
            "cp": cps,
            "city": minicipios,
            "provincia": ["Zaragoza"] * len(names),
        }
    )
    df.to_csv(LOCAL_FARMA_ZAR_CSV, index=False, sep="\t")
