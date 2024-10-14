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

PROVINCIAS = [
    "a-coruna",
    "albacete",
    "alicante",
    "almeria",
    "arabaalava",
    "asturias",
    "avila",
    "badajoz",
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
    "gipuzkoa",
    "girona",
    "granada",
    "guadalajara",
    "huelva",
    "huesca",
    "illes-balears",
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
    "santa-cruz-de-tenerife",
    "segovia",
    "sevilla",
    "soria",
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
    URLS_CENTROS.append(
        f"https://guia-{prob}.portaldeeducacion.es/colegios-institutos-centros-y-estudios/{prob}/index.htm"
    )

# df = pd.read_csv("data/proxies.csv")
# PROXIES = df["IP"].to_list()


class DetallesCentro(Item):
    attr_url = Field()
    attr_name = Field()
    attr_type = Field()
    attr_type_description = Field()
    attr_comedor = Field()
    attr_horario_ampliado = Field()
    attr_transporte = Field()
    attr_multi_lengua = Field()
    attr_telephone = Field()
    attr_fax = Field()
    attr_mail = Field()
    attr_cursos = Field()
    attr_webpage = Field()

    city = Field()
    address = Field()
    province = Field()
    latitude = Field()
    longitude = Field()


class CentroEducacionSpider(CrawlSpider):
    name = "CentrosEducacion"

    # ?https://docs.scrapy.org/en/latest/topics/feed-exports.html#feed-export-fields
    custom_settings = {
        "USER_AGENT": get_user_agent(),
        # numero de paginas a descargar.
        # "CLOSESPIDER_PAGECOUNT": 20,
        # profundidad de las reglas.
        # "DEPTH_LIMIT": 1,
        # para los caracteres especiales.
        "FEED_EXPORT_ENCODING": "utf-8",
        "FEED_EXPORT_FIELDS": [
            "attr_url",
            "attr_name",
            "attr_type",
            "attr_type_description",
            "attr_comedor",
            "attr_horario_ampliado",
            "attr_transporte",
            "attr_multi_lengua",
            "attr_telephone",
            "attr_fax",
            "attr_mail",
            "attr_cursos",
            "attr_webpage",
            "city",
            "address",
            "province",
            "latitude",
            "longitude",
        ],
        "CONCURRENT_REQUEST": 1,  # numero de paginas que se pueden visitar a la vez.
    }
    # scrapy no toma este valor fijo, sino que pone un rango entre 0.5 * download_delay y 1.5 * download_delay
    download_delay = 2 + random.random()
    # allowed_domains = []
    rules = (
        # Regla para Paginacion
        Rule(
            LinkExtractor(allow=r"/index-"),
            follow=True,
            # callback="parse_horizontal",
        ),
        # Regla para Profundidad
        Rule(
            # https://docs.scrapy.org/en/latest/topics/link-extractors.html#module-scrapy.linkextractors.lxmlhtml
            # LinkExtractor solo busca en tags "a"
            LinkExtractor(
                allow=r"\-i[0-9]+\.htm",
                # para buscar en los tags que tu quieras y con los attrs
                # tags=("a", "button")
                # attrs=("href", "data-url")
                # para restringir determinados elementos (tags)
                # restrict_css=(),
            ),
            follow=True,
            callback="parse_individual",
        ),
    )

    def __init__(self, **kwargs):
        self.start_urls = [URLS_CENTROS[0]]
        super().__init__(**kwargs)  # python3

    # def start_requests(self):
    #     for url in self.start_urls:
    #         proxy = random.choice(PROXIES)
    #         yield scrapy.Request(url, meta={"proxy": f"http://{proxy}"})

    def parse_individual(self, response):
        print("*" * 150)
        print("*" * 150)
        print("Ok!!!!! - 3")
        try:
            if sel.css("#MainContent_EnviarLink").get():
                input()
                time.sleep(random.uniform(8, 10))
        except Exception as e:
            print(e)

        item = ItemLoader(DetallesCentro(), response)
        item.add_value("attr_url", response.url)
        sel = Selector(response)
        description = sel.css(".descripcion-escuela")
        # Attributes
        cname = description.css("h2::text").get()
        item.add_value(
            "attr_name",
            cname.replace("Descripción detallada de", "").strip(": ").lower(),
        )

        contents = description.css("p::text").getall()
        education = []
        education_bool = True
        descript = True
        type_descript = []
        centre_bool = False
        for i, content in enumerate(contents):
            content = content.strip("\r\n ").lower()
            content = content.replace("\r\n                           ", " - ")
            if len(content) == 0:
                continue

            if content in ["público", "privado"]:
                item.add_value("attr_type", content)
            elif "comedor" in content:
                item.add_value(
                    "attr_comedor",
                    content.replace("comedor", "").strip(": "),
                    MapCompose(lambda x: False if "no" in x else True),
                )
            elif "horario" in content:
                item.add_value(
                    "attr_horario_ampliado",
                    content.replace("horario ampliado", "").strip(": "),
                    MapCompose(lambda x: False if "no" in x else True),
                )
            elif "transporte" in content:
                item.add_value(
                    "attr_transporte",
                    content.replace("transporte", "").strip(": "),
                    MapCompose(lambda x: False if "no" in x else True),
                )
            elif "plurilingüismo" in content:
                item.add_value(
                    "attr_multi_lengua",
                    content.replace("plurilingüismo", "").strip(": "),
                    MapCompose(lambda x: False if "no" in x else True),
                )
            elif education_bool:
                if "establecimiento" in content:
                    education_bool = False
                else:
                    education.append(content)
            elif descript:
                descript = False
                direction = content.split(",")

                city = direction[-1]
                prov = direction[-2]
                direct = " ".join(direction[:-2])

                item.add_value("city", city.strip(". "))
                item.add_value("province", prov.strip(". "))
                item.add_value("address", direct)
            elif "teléfono" in content:
                item.add_value(
                    "attr_telephone", content.replace("teléfono", "").strip(": ")
                )
            elif "fax" in content:
                item.add_value("attr_fax", content.replace("fax", "").strip(": "))
            elif "@" in content:
                item.add_value("attr_mail", content.split(" ")[-1].strip())
                centre_bool = True
            elif centre_bool:
                if "deseas" in content:
                    centre_bool = False
                else:
                    type_descript.append(content)

        item.add_value("attr_cursos", education)
        item.add_value("attr_type_description", type_descript)

        lat_long = description.css("h4 a::attr(href)").get()
        lat, long = re.findall("[+-]?[0-9]+\.[0-9]+", lat_long)
        item.add_value("latitude", lat)
        item.add_value("longitude", long)

        web = description.css("p a::attr(href)").get()
        item.add_value("attr_webpage", web)

        yield item.load_item()
        print("*" * 150)
        print("*" * 150)


if __name__ == "__main__":
    df = pd.read_json("data/centros_educacion_urls.jsonl", lines=True)
    df = df.map(lambda x: x[0] if isinstance(x, list) else x)
    print(df)
    # process = CrawlerProcess(
    #     {
    #         "FEED_FORMAT": "json",
    #         "FEED_URI": "data/centros_educacion.json",
    #     }
    # )
    # process.crawl(CentroEducacionSpider)
    # process.start()
