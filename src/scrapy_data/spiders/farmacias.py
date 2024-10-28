import os
import random
import re
import sys
from pathlib import Path

import pandas as pd
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

PROVINCIAS = [
    "coruna",
    "alicante",
    "albacete",
    "almeria",
    "alava",
    "asturias",
    "avila",
    "badajoz",
    "baleares",
    "barcelona",
    "bizkaia",
    "burgos",
    "caceres",
    "cadiz",
    "cantabria",
    "castellon",
    "ceuta",
    "ciudad-real",
    "cordoba",
    "cuenca",
    "girona",
    "granada",
    "guadalajara",
    "gipuzkoa",
    "huelva",
    "huesca",
    "jaen",
    "la-rioja",
    "las-palmas",
    "leon",
    "lleida",
    "lugo",
    "madrid",
    "malaga",
    "melilla",
    "murcia",
    "navarra",
    "ourense",
    "palencia",
    "pontevedra",
    "salamanca",
    "segovia",
    "sevilla",
    "soria",
    "tenerife",
    "tarragona",
    "teruel",
    "toledo",
    "valencia",
    "valladolid",
    "zamora",
    "zaragoza",
]

URLS_CENTROS = []
for prob in PROVINCIAS:
    URLS_CENTROS.append(f"https://www.farmacias.es/{prob}/")

LOCAL_FARMA = Path("data/farmacias.jsonl")
LOCAL_FARMA_DET = Path("data/farmacias_detalles.jsonl")
LOCAL_FARMA_CSV = Path("data/farmacias.csv")
LOCAL_FARMA_DET_2 = Path("data/farmacias_detalles_v2.jsonl")

if not LOCAL_FARMA.exists():

    class DetallesCentro(Item):
        name = Field()
        url = Field()

    class FarmaciasSpider(CrawlSpider):
        name = "Farmacias"
        # start_urls = [URLS_CENTROS[0]]
        start_urls = URLS_CENTROS
        custom_settings = {
            "USER_AGENT": get_user_agent(),
            "CONCURRENT_REQUEST": 1,
            "FEEDS": {
                LOCAL_FARMA: {
                    "format": "jsonlines",
                    "overwrite": True,
                    "encoding": "utf-8",
                    "fields": ["name", "url"],
                },
            },
        }
        download_delay = 1 + random.random()
        rules = (
            # Regla para Paginacion
            Rule(
                LinkExtractor(allow=r"\/[a-z-]+\/\d+"),
                follow=True,
                callback="parse_horizontal",
            ),
        )

        def parse_horizontal(self, response):
            print("*" * 150)
            print("*" * 150)
            sel = Selector(response)
            farmas = sel.css("div.fichas > div > div.ficha")

            for farma in farmas:
                item = ItemLoader(DetallesCentro(), farma)
                # print(farma)
                name = farma.css("a::attr(title)").get()
                # print(name)
                item.add_value("name", name.strip())

                url = farma.css("h3.card-title a::attr(href)").get()
                item.add_value("url", url.strip())

                yield item.load_item()
            print("*" * 150)
            print("*" * 150)

    process = CrawlerProcess()
    process.crawl(FarmaciasSpider)
    process.start()


if 0:
    df_all = pd.read_json(LOCAL_FARMA, lines=True)
    df_all = df_all.map(lambda x: x[0], na_action="ignore")

    if not LOCAL_FARMA_DET.exists():
        urls_rest = df_all.url.apply(lambda x: f"https://www.farmacias.es{x}").to_list()
    else:
        df_def = pd.read_json(LOCAL_FARMA_DET, lines=True)

        urls_all = set(
            df_all.url.apply(lambda x: f"https://www.farmacias.es{x}").to_list()
        )
        print(f"todos: {len(urls_all)}")
        urls_def = set(df_def.url.apply(lambda x: x[0]).to_list())
        print(f"hay: {len(urls_def)}")
        urls_rest = list(set(urls_all).difference(set(urls_def)))
        print(f"quedan: {len(urls_rest)}")

    print(urls_rest)

    class DetallesCentro2(Item):
        name = Field()
        url = Field()
        telephone = Field()
        address = Field()
        longitude = Field()
        latitude = Field()
        servicios = Field()
        web = Field()

    class FarmaciasSpider2(Spider):
        name = "Farmacias"
        # start_urls = [
        #     "https://www.farmacias.es/albacete/albacete/hermanas-buendia-sanchez-c-b--4386"
        # ]
        start_urls = sorted(urls_rest)
        custom_settings = {
            "USER_AGENT": get_user_agent(),
            "CONCURRENT_REQUEST": 1,
            "FEEDS": {
                LOCAL_FARMA_DET: {
                    "format": "jsonlines",
                    "overwrite": False,
                    "encoding": "utf-8",
                    "fields": [
                        "name",
                        "url",
                        "telephone",
                        "address",
                        "longitude",
                        "latitude",
                        "servicios",
                        "web",
                    ],
                },
            },
        }
        download_delay = 1 + random.random()

        def parse(self, response):
            print("*" * 150)
            print("*" * 150)
            sel = Selector(response)
            item = ItemLoader(DetallesCentro2(), response)

            item.add_value("url", response.url)

            name = sel.css("h1.title::text").get()
            item.add_value("name", name, MapCompose(lambda x: x.strip()))

            tel = sel.css("div.botonerafijada a::attr(content)").get()
            item.add_value("telephone", tel, MapCompose(lambda x: x.strip()))

            addr = sel.css("div + h4.panel-title a meta::attr(content)").get()
            item.add_value(
                "address",
                addr,
                MapCompose(
                    lambda x: x.strip(),
                ),
            )

            href = sel.css("div + h4.panel-title a::attr(href)").get()
            try:
                lat, long = re.findall("[+-]?[0-9]+\.[0-9]+", href)
            except ValueError as e:
                print(e)
                lat, long = "0.0", "0.0"
            item.add_value("longitude", long, MapCompose(lambda x: x.strip()))
            item.add_value("latitude", lat, MapCompose(lambda x: x.strip()))

            servi = sel.css("div.servicios")
            if len(servi) > 0:
                for ser in servi:
                    if ser.css("h4::text").get().lower() == "servicios":
                        servicios = ser.css("span").getall()
                        item.add_value(
                            "servicios",
                            ",".join(servicios.css("span::text").get()),
                            MapCompose(lambda x: x.strip()),
                        )
                    elif ser.css("h4::text").get().lower() == "web":
                        web = ser.css("a::attr(href)").get()
                        item.add_value("web", web, MapCompose(lambda x: x.strip()))
            else:
                item.add_value("servicios", None)
                item.add_value("web", None)

            yield item.load_item()
            print("*" * 150)
            print("*" * 150)

    process = CrawlerProcess()
    process.crawl(FarmaciasSpider2)
    process.start()


# Nueva APPROX
if 0:
    URLS = [
        f"https://www.farmacias.es/coruna/ortigueira/farmacia-fraga-{i}"
        for i in range(30, 27250)
    ]
    # LOCAL_FARMA_DET_2.unlink()

    # df_all = pd.read_json(LOCAL_FARMA_DET, lines=True)
    # df_all = df_all.map(lambda x: x[0], na_action="ignore")

    if not LOCAL_FARMA_DET_2.exists():
        urls_rest = URLS
    else:
        df_def = pd.read_json(LOCAL_FARMA_DET_2, lines=True)

        urls_all = set(URLS)
        print(f"todos: {len(URLS)}")
        urls_def = set(df_def.url.apply(lambda x: x[0]).to_list())
        print(f"hay: {len(urls_def)}")
        urls_rest = list(set(urls_all).difference(set(urls_def)))
        print(f"quedan: {len(urls_rest)}")

    class DetallesCentro2(Item):
        name = Field()
        url = Field()
        telephone = Field()
        address = Field()
        longitude = Field()
        latitude = Field()
        servicios = Field()
        web = Field()
        city = Field()
        province = Field()
        cp = Field()

    class FarmaciasSpider2(Spider):
        name = "Farmacias"
        # start_urls = [
        #     "https://www.farmacias.es/albacete/albacete/hermanas-buendia-sanchez-c-b--4386"
        # ]
        # start_urls = sorted(urls_rest[0:10])
        start_urls = sorted(urls_rest)
        # start_urls = URLS[0:1]
        custom_settings = {
            "USER_AGENT": get_user_agent(),
            "CONCURRENT_REQUEST": 1,
            "FEEDS": {
                LOCAL_FARMA_DET_2: {
                    "format": "jsonlines",
                    "overwrite": False,
                    "encoding": "utf-8",
                    "fields": [
                        "name",
                        "url",
                        "telephone",
                        "address",
                        "longitude",
                        "latitude",
                        "servicios",
                        "web",
                        "city",
                        "province",
                        "cp",
                    ],
                },
            },
        }
        # download_delay = 1 + random.random()

        def parse(self, response):
            print("*" * 150)
            print("*" * 150)
            sel = Selector(response)
            item = ItemLoader(DetallesCentro2(), response)

            if response.status == 200:
                item.add_value("url", response.url)
                name = sel.css("h1.title::text").get()
                if name:
                    item.add_value("name", name, MapCompose(lambda x: x.strip()))

                    tel = sel.css("div.botonerafijada a::attr(content)").get()
                    item.add_value("telephone", tel, MapCompose(lambda x: x.strip()))

                    addrs = sel.css("div + h4.panel-title a meta")
                    for addr in addrs:
                        var = addr.css("meta::attr(content)").get()
                        tipo = addr.css("meta::attr(itemprop)").get()
                        if tipo == "streetAddress":
                            item_var = "address"
                        elif tipo == "addressLocality":
                            item_var = "city"
                        elif tipo == "addressRegion":
                            item_var = "province"
                        elif tipo == "postalCode":
                            item_var = "cp"

                        item.add_value(
                            item_var,
                            var,
                            MapCompose(
                                lambda x: x.strip(),
                            ),
                        )

                    href = sel.css("div + h4.panel-title a::attr(href)").get()
                    try:
                        lat, long = re.findall("[+-]?[0-9]+\.[0-9]+", href)
                    except ValueError as e:
                        print(e)
                        lat, long = "0.0", "0.0"
                    item.add_value("longitude", long, MapCompose(lambda x: x.strip()))
                    item.add_value("latitude", lat, MapCompose(lambda x: x.strip()))

                    servi = sel.css("div.servicios")
                    if len(servi) > 0:
                        for ser in servi:
                            if ser.css("h4::text").get().lower() == "servicios":
                                continue
                                # servicios = ser.css("span").getall()
                                # item.add_value(
                                #     "servicios",
                                #     ",".join(servicios.css("span::text").get()),
                                #     MapCompose(lambda x: x.strip()),
                                # )
                            elif ser.css("h4::text").get().lower() == "web":
                                web = ser.css("a::attr(href)").get()
                                item.add_value(
                                    "web", web, MapCompose(lambda x: x.strip())
                                )
                    else:
                        item.add_value("servicios", None)
                        item.add_value("web", None)

                yield item.load_item()
            print("*" * 150)
            print("*" * 150)

    process = CrawlerProcess()
    process.crawl(FarmaciasSpider2)
    process.start()

if not LOCAL_FARMA_CSV.exists():
    df = pd.read_json(LOCAL_FARMA_DET_2, lines=True)
    df = df.map(lambda x: x[0], na_action="ignore")
    df = df[~df.name.isna()]

    df.to_csv(LOCAL_FARMA_CSV, index=False, sep="\t")