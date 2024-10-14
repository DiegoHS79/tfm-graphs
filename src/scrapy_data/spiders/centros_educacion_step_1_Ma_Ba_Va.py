import os
import random
import re
import sys
import time
from pathlib import Path

import pandas as pd
from scrapy.crawler import CrawlerProcess
from scrapy.item import Field
from scrapy.item import Item
from scrapy.spiders import Spider
from scrapy.selector import Selector
from scrapy.loader import ItemLoader

from utils import get_user_agent, manage_catpcha

os.system("clear")

# data_centros = Path("data/centros_educacion.json")
# if data_centros.exists():
#     data_centros.unlink()

PROVINCIAS = {
    "barcelona": 318,  # 0
    "madrid": 317,  # 1
    "valencia": 141,  # 2
}
prob = list(PROVINCIAS.keys())[0]

URLS = [
    f"https://guia-{prob}.portaldeeducacion.es/colegios-institutos-centros-y-estudios/{prob}/index.htm"
]
for page in range(2, PROVINCIAS[prob] + 1):
    URLS.append(
        f"https://guia-{prob}.portaldeeducacion.es/colegios-institutos-centros-y-estudios/{prob}/index-{page}.htm"
    )
try:
    df = pd.read_json(f"data/{prob}_centros_educacion_urls.jsonl", lines=True)
    df = df.map(lambda x: x[0] if isinstance(x, list) else x)

    all_urls = df.url_base.unique()

    rest_urls = sorted(set(URLS).difference(set(all_urls)))
except ValueError:
    rest_urls = URLS


class DetallesCentro(Item):
    url = Field()
    city = Field()
    address = Field()
    province = Field()
    centre_name = Field()
    centre_description = Field()
    telephone = Field()
    url_base = Field()


class CentroEducacionSpider(Spider):
    name = "CentrosEducacion"
    start_urls = list(rest_urls)

    # ?https://docs.scrapy.org/en/latest/topics/feed-exports.html#feed-export-fields
    custom_settings = {
        "USER_AGENT": get_user_agent(),
        "CONCURRENT_REQUEST": 1,
        "FEEDS": {
            f"data/{prob}_centros_educacion_urls.jsonl": {
                "format": "jsonlines",
                "overwrite": False,
                "encoding": "utf-8",
                "fields": [
                    "url",
                    "city",
                    "address",
                    "province",
                    "centre_name",
                    "centre_description",
                    "telephone",
                    "url_base",
                ],
            },
        },
    }
    download_delay = 2 + random.random()
    # allowed_domains = []

    # para hacer el scrapy de la URL raiz.
    def parse(self, response):
        print("*" * 150)
        print("*" * 150)

        print(f"Status connection: {response.status}")
        print(f"Priginal page: {response.url}", end="\n\n")
        prov = response.url.split("/")[-2].replace("-", " ")
        sel = Selector(response)
        centros = sel.css(".lista-indice > li")
        for centro in centros:
            item = ItemLoader(DetallesCentro(), centro)
            item.add_value("province", prov)

            url = centro.css("h3 a::attr(href)").get()
            item.add_value("url", url)

            h3 = centro.css("h3 a::text").get()
            if h3:
                try:
                    name, description = h3.split(",", 1)
                except:
                    name = "Unknown"
                    description = h3.strip()
                item.add_value("centre_name", name.strip())
                item.add_value("centre_description", description.strip())

                addr, tel = centro.css("p::text").getall()[1:3]
                item.add_value(
                    "address",
                    addr.replace("\r\n                ", "")
                    .replace("Dirección:", "")
                    .strip(". "),
                )

                city = (
                    addr.strip("\r\n ")
                    .split("\r\n")[1]
                    .strip(". ")
                    .replace(prov, "")
                    .strip()
                )
                item.add_value("city", city)

                item.add_value("telephone", tel.replace("Teléfono:", "").strip("\r\n "))
            else:
                continue

            item.add_value("url_base", response.url)

            yield item.load_item()

        print("*" * 150)
        print("*" * 150)


process = CrawlerProcess()
process.crawl(CentroEducacionSpider)
process.start()
