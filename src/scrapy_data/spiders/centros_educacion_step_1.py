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
from scrapy.spiders import CrawlSpider, Rule
from scrapy.selector import Selector
from scrapy.linkextractors import LinkExtractor
from scrapy.loader import ItemLoader

from utils import get_user_agent, manage_catpcha

os.system("clear")

# data_centros = Path("data/centros_educacion.json")
# if data_centros.exists():
#     data_centros.unlink()

PROVINCIAS = [
    "a-coruna",  # 0
    "albacete",  # 1
    "alicante",  # 2
    "almeria",  # 3
    "arabaalava",  # 4
    "asturias",  # 5
    "avila",  # 6
    "badajoz",  # 7
    "barcelona",  # 8 - 318
    "bizkaia",  # 9
    "burgos",  # 10
    "caceres",  # 11
    "cadiz",  # 12
    "cantabria",  # 13
    "castellon",  # 14
    "ceuta",  # 15
    "ciudad-real",  # 16
    "cordoba",  # 17
    "cuenca",  # 18
    "gipuzkoa",  # 19
    "girona",  # 20
    "granada",  # 21
    "guadalajara",  # 22
    "huelva",  # 23
    "huesca",  # 24
    "illes-balears",  # 25
    "jaen",  # 26
    "la-rioja",  # 27
    "las-palmas",  # 28
    "leon",  # 29
    "lleida",  # 30
    "lugo",  # 31
    "madrid",  # 32 - 317
    "malaga",  # 33
    "melilla",  # 34
    "murcia",  # 35
    "navarra",  # 36
    "ourense",  # 37
    "palencia",  # 38
    "pontevedra",  # 39
    "salamanca",  # 40
    "santa-cruz-de-tenerife",  # 41
    "segovia",  # 42
    "sevilla",  # 43
    "soria",  # 44
    "tarragona",  # 45
    "teruel",  # 46
    "toledo",  # 47
    "valencia",  # 48 - 141
    "valladolid",  # 49
    "zamora",  # 50
    "zaragoza",  # 51
]

# URLS_CENTROS = []
# for prob in PROVINCIAS:
#     URLS_CENTROS.append(
#         f"https://guia-{prob}.portaldeeducacion.es/colegios-institutos-centros-y-estudios/{prob}/index.htm"
#     )

prob = PROVINCIAS[48]


class DetallesCentro(Item):
    url = Field()
    city = Field()
    address = Field()
    province = Field()
    centre_name = Field()
    centre_description = Field()
    telephone = Field()


class CentroEducacionSpider(CrawlSpider):
    name = "CentrosEducacion"
    start_urls = [
        f"https://guia-{prob}.portaldeeducacion.es/colegios-institutos-centros-y-estudios/{prob}/index.htm"
    ]

    # ?https://docs.scrapy.org/en/latest/topics/feed-exports.html#feed-export-fields
    custom_settings = {
        "USER_AGENT": get_user_agent(),
        "CONCURRENT_REQUEST": 1,
        "FEEDS": {
            f"data/{prob}_centros_educacion_urls.jsonl": {
                "format": "jsonlines",
                "overwrite": True,
                "encoding": "utf-8",
                "fields": [
                    "url",
                    "city",
                    "address",
                    "province",
                    "centre_name",
                    "centre_description",
                    "telephone",
                ],
            },
        },
    }
    download_delay = 2 + random.random()
    # allowed_domains = []
    rules = (
        # Regla para Paginacion
        Rule(
            LinkExtractor(allow=r"/index-"),
            follow=True,
            callback="parse_horizontal",
        ),
    )

    # para hacer el scrapy de la URL raiz.
    def parse_horizontal(self, response):
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

            yield item.load_item()

        print("*" * 150)
        print("*" * 150)


process = CrawlerProcess()
process.crawl(CentroEducacionSpider)
process.start()
