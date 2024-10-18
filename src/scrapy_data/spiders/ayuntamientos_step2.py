import os
import random
import re
import sys
import time
from pathlib import Path

from itemloaders.processors import MapCompose
import pandas as pd
import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy.item import Field
from scrapy.item import Item
from scrapy.spiders import Spider
from scrapy.selector import Selector
from scrapy.loader import ItemLoader

from utils import get_user_agent

os.system("clear")

df = pd.read_json("data/ayuntamientos.jsonl", lines=True)
df = df.map(lambda x: x[0] if isinstance(x, list) else x)
df = df[df.town.apply(lambda x: True if "ayuntamiento de" in x.lower() else False)]
all_urls = set(df.url)
print(len(all_urls))

df2 = pd.read_json("data/ayuntamientos_detalle.jsonl", lines=True)
df2 = df2.map(lambda x: x[0] if isinstance(x, list) else x)
extracted_urls = set(df2.url)
print(len(extracted_urls))

rest_urls = all_urls.difference(extracted_urls)
print(len(rest_urls))


class DetallesAyuntamiento(Item):
    url = Field()
    name = Field()
    province = Field()
    address = Field()
    cp = Field()
    email = Field()
    web = Field()
    telefono = Field()
    fax = Field()


class AyuntamientosSpider(Spider):
    name = "CentrosEducacion"

    # ?https://docs.scrapy.org/en/latest/topics/feed-exports.html#feed-export-fields
    custom_settings = {
        "USER_AGENT": get_user_agent(),
        # numero de paginas a descargar.
        # "CLOSESPIDER_PAGECOUNT": 20,
        # profundidad de las reglas.
        # "DEPTH_LIMIT": 1,
        "FEEDS": {
            f"data/ayuntamientos_detalle.jsonl": {
                "format": "jsonlines",
                "overwrite": False,
                "encoding": "utf-8",
                "fields": [
                    "name",
                    "province",
                    "address",
                    "cp",
                    "email",
                    "web",
                    "telefono",
                    "fax",
                    "url",
                ],
            },
        },
        "CONCURRENT_REQUEST": 1,  # numero de paginas que se pueden visitar a la vez.
        "RETRY_TIMES": 3,
    }
    download_delay = 2 + random.random()

    def __init__(self, **kwargs):
        self.start_urls = list(rest_urls)
        # self.start_urls = list(rest_urls)[0]
        # self.start_urls = [df.url.to_list()[4]]
        # self.start_urls = [
        #     "https://administracion.gob.es/pagFront/espanaAdmon/directorioOrganigramas/fichaUnidadOrganica.htm?idUnidOrganica=25533&origenUO=quienEsQuien&quienEsQuien=true&nJerOriginal=0&volver=quienEsQuien&desOrganismo=&idNivAdmin=3&idCCAA=0&idProv=&numPagAct=1"
        # ]
        super().__init__(**kwargs)

    def parse(self, response):
        print("*" * 150)
        print("*" * 150)
        # try:
        #     if sel.css("#MainContent_EnviarLink").get():
        #         input()
        #         time.sleep(random.uniform(8, 10))
        # except Exception as e:
        #     print(e)

        item = ItemLoader(DetallesAyuntamiento(), response)
        item.add_value("url", response.url)
        sel = Selector(response)
        name = sel.css("h1::text").get().lower()
        item.add_value("name", name.replace("ayuntamiento de", "").strip())

        direc = sel.css(".ppg-map__info--text::text").getall()
        if len(direc) == 0:
            item.add_value("address", "Unknown")
            item.add_value("cp", "Unknown")
            item.add_value("province", "Unknown")
        else:
            item.add_value("address", direc[0])

            cp = re.findall("[0-9]+", direc[1])[0]
            item.add_value("cp", cp)

            # regex = "\([a-zA-ZÁÉÍÓÚáéíóúñÑè]+,? ?\/?[a-zA-Zó]+?\)"
            regex = "\(.*?\)"
            prov = re.findall(regex, direc[1])[0].strip("()")
            item.add_value("province", prov)

            li_list = sel.css("ul.ppg-map__list > li")
            for li in li_list:
                content_1 = li.css("li::text").get()
                content_2 = li.css("li a::text").get()
                if "Ver Oficinas asociadas" in [content_1, content_2]:
                    continue
                elif content_1:
                    if content_1.startswith("Email:"):
                        email = li.css("li::text").get()
                        item.add_value("email", email.replace("Email:", "").strip())
                    elif content_1.startswith("Teléfono:"):
                        tel = li.css("li::text").get()
                        item.add_value("telefono", tel.replace("Teléfono:", "").strip())
                    elif content_1.startswith("Fax:"):
                        fax = li.css("li::text").get()
                        item.add_value("fax", fax.replace("Fax:", "").strip())
                elif content_2:
                    item.add_value("web", li.css("a::text").get())

        yield item.load_item()
        print("*" * 150)
        print("*" * 150)


if __name__ == "__main__":
    process = CrawlerProcess()
    process.crawl(AyuntamientosSpider)
    process.start()
