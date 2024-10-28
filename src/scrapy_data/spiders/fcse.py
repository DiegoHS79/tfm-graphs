import os
import re
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup
from scrapy.crawler import CrawlerProcess
from scrapy.item import Field
from scrapy.item import Item
from scrapy.spiders import CrawlSpider, Spider, Rule
from scrapy.selector import Selector
from scrapy.linkextractors import LinkExtractor
from scrapy.loader import ItemLoader
from itemloaders.processors import MapCompose

from utils import get_user_agent

os.system("clear")

headers = {"user-agent": get_user_agent()}

# Puestos de la GC
PUESTOS_GC = Path("data/puestos_gc.csv")
PUESTOS_GC_V2 = Path("data/puestos_gc_final.csv")

COMISARIAS_PN = Path("data/comisarias.jsonl")
COMISARIAS_PN_CSV = Path("data/comisarias.csv")

if not PUESTOS_GC_V2.exists():
    # PUESTOS
    url_puestos = "https://www.guardiacivil.es/documentos/contenidos_reutilizables/dependencias_24h_guardia_civil.csv"
    resp = requests.get(url_puestos, headers=headers)
    with open(PUESTOS_GC, "wb") as outfile:
        outfile.write(resp.content)

    df = pd.read_csv(PUESTOS_GC, sep=";", encoding="latin-1")
    df.UNIDAD = df.UNIDAD.apply(lambda x: x.strip())
    df.drop(columns=["Unnamed: 7"], inplace=True)

    df.rename(
        columns={
            "DOMICILIO": "Domicilio",
            "PROVINCIA": "Provincia",
            "LOCALIDAD": "city",
            "CODIGO POSTAL": "cp",
            "TELEFONO": "Teléfono",
        },
        inplace=True,
    )

    # COMANDANCIAS
    url_comand = "https://www.guardiacivil.es/es/servicios/atencionciudadano_1/cartaservicios/direcciones_postales_comandancias.html"
    response = requests.get(url_comand, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    prov = []
    addr = []
    tele = []
    com = soup.select("tbody > tr")
    for i, co in enumerate(com):
        if i == 0:
            cols = [j.text for j in co.select("p > strong")]
        else:
            data = [j.text for j in co.select("p")]
            if len(data) == 0:
                continue
            prov.append(data[0].lower())
            addr.append(data[1].lower())
            tele.append(data[2].lower())

    dfc = pd.DataFrame({cols[0]: prov, cols[1]: addr, cols[2]: tele})
    dfc["cp"] = dfc[cols[1]].apply(
        lambda x: x.split("-")[1].strip().split(" ")[0].strip()
    )
    dfc["city"] = dfc[cols[1]].apply(
        lambda x: x.split("-")[1].strip().split(" ", 1)[1].strip()
    )
    dfc[cols[1]] = dfc[cols[1]].apply(lambda x: x.split("-")[0].strip())

    # UNION
    dff = pd.concat([df, dfc])
    dff.drop(columns=["COMUNIDAD AUTONOMA"], inplace=True)

    dff.to_csv(PUESTOS_GC_V2, index=False, sep="\t")

if not COMISARIAS_PN.exists():

    class Comisarias(Item):
        name = Field()
        telephone = Field()
        address = Field()
        longitude = Field()
        latitude = Field()
        city = Field()
        province = Field()

    class ComisariasSpider(Spider):
        name = "Comisarias (ODAC)"
        start_urls = [
            "https://sede.policia.gob.es/portalCiudadano/_es/dependencias_localizador_accesible.php"
        ]
        custom_settings = {
            "USER_AGENT": get_user_agent(),
            "CONCURRENT_REQUEST": 1,
            "FEEDS": {
                COMISARIAS_PN: {
                    "format": "jsonlines",
                    "overwrite": True,
                    "encoding": "utf-8",
                    "fields": [
                        "name",
                        "telephone",
                        "address",
                        "longitude",
                        "latitude",
                        "servicios",
                        "city",
                        "province",
                    ],
                },
            },
        }

        def parse(self, response):
            print("*" * 150)
            print("*" * 150)
            sel = Selector(response)

            if response.status == 200:
                c_prov = sel.css(
                    'ul[aria-label*="Listado de Oficinas de trámites de Oficina de Denuncias"] > li'
                )
                for com in c_prov:
                    try:
                        prov = com.css("h4::text").get().strip().lower()

                        for co in com.css("ul > li"):
                            item = ItemLoader(Comisarias(), co)
                            item.add_value(
                                "province",
                                prov,
                                MapCompose(lambda x: x.lower().strip()),
                            )

                            name = co.css("h5::text").get()
                            item.add_value(
                                "name", name, MapCompose(lambda x: x.lower().strip())
                            )

                            city = name.replace(
                                "Jefatura Superior de Policía de ", ""
                            ).replace("Comisaría de ", "")
                            item.add_value(
                                "city", city, MapCompose(lambda x: x.lower().strip())
                            )

                            dd = co.css("dd")
                            addr = dd[0].css("dd::text").get()
                            item.add_value(
                                "address",
                                addr,
                                MapCompose(lambda x: x.lower().strip()),
                            )
                            tel = dd[1].css("dd a::text").get()
                            item.add_value(
                                "telephone",
                                tel,
                                MapCompose(lambda x: x.lower().strip()),
                            )

                            coord = dd[-1].css("dd a::attr(href)").get()
                            try:
                                lat, long = re.findall("[+-]?[0-9]+\.[0-9]+", coord)
                            except ValueError as e:
                                print(e)
                                lat, long = "0.0", "0.0"
                            item.add_value(
                                "longitude",
                                long,
                                MapCompose(lambda x: x.strip()),
                            )
                            item.add_value(
                                "latitude", lat, MapCompose(lambda x: x.strip())
                            )

                            yield item.load_item()

                    except Exception as e:
                        print(e)

            print("*" * 150)
            print("*" * 150)

    process = CrawlerProcess()
    process.crawl(ComisariasSpider)
    process.start()

if not COMISARIAS_PN_CSV.exists():
    df = pd.read_json(COMISARIAS_PN, lines=True)
    df = df.map(lambda x: x[0], na_action="ignore")

    df.to_csv(COMISARIAS_PN_CSV, index=False, sep="\t")
