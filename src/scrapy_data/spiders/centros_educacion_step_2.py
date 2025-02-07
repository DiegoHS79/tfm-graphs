import io
import os
import random
import re
import requests
import sys
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

from utils import get_user_agent, manage_catpcha

os.system("clear")

PROVINCIAS = [
    "a-coruna",  # 0
    "albacete",  # 1
    "alicante",  # 2
    "almeria",  # 3
    "arabaalava",  # 4
    "asturias",  # 5
    "avila",  # 6
    "badajoz",  # 7
    "barcelona",  # 8
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
    "madrid",  # 32
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
    "valencia",  # 48
    "valladolid",  # 49
    "zamora",  # 50
    "zaragoza",  # 51
]

prob = PROVINCIAS[51]

df = pd.read_json(f"data/{prob}_centros_educacion_urls.jsonl", lines=True)
df = df.map(lambda x: x[0] if isinstance(x, list) else x)

df_detalle = pd.read_json("data/centros_educacion_info.jsonl", lines=True)
if df_detalle.empty:
    rest_urls = df.url.to_list()
else:
    list_urls = df_detalle.attr_url.apply(
        lambda x: x[0]
        .replace("%C2%A0", " ")
        .replace("%C2%BA", "º")
        .replace("%C2%B7", "·")
        .replace("%C3%8C", "Ì")
        .replace("%C3%8F", "Ï")
        .replace("%C3%80", "À")
        .replace("%C3%84", "Ä")
        .replace("%C3%87", "Ç")
        .replace("%C3%88", "È")
        .replace("%C3%92", "Ò")
        .replace("%C3%94", "Ô")
        .replace("%C3%96", "Ö")
        .replace("%C3%99", "Ù")
        .replace("%C3%B2", "ò")
        .replace("%C3%A0", "à")
        .replace("%C3%A7", "ç")
        .replace("%C3%A8", "è")
        .replace("%C3%AF", "ï")
        .replace("%7", "|")
        .replace("%60", "`")
    ).to_list()

    all_urls = df.url.to_list()

    rest_urls = set(all_urls).difference(set(list_urls))

    print(f"Hay recogidos: {len(list_urls)}, quedan {len(rest_urls)}")


# url = "https://proxylist.geonode.com/api/proxy-list?limit=500&page=1&sort_by=lastChecked&sort_type=desc"
# response = requests.get(url)

# df2 = pd.read_json(io.StringIO(response.content.decode("utf-8")))
# PROXIES = []
# for dat in df2.data:
#     connection = dict(dat)
#     PROXIES.append(f"{connection['ip']}:{connection['port']}")


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


class CentroEducacionSpider(Spider):
    name = "CentrosEducacionScrap"
    start_urls = list(rest_urls)

    # ?https://docs.scrapy.org/en/latest/topics/feed-exports.html#feed-export-fields
    custom_settings = {
        "USER_AGENT": get_user_agent(),
        # numero de paginas a descargar.
        # "CLOSESPIDER_PAGECOUNT": 20,
        # profundidad de las reglas.
        # "DEPTH_LIMIT": 1,
        "FEEDS": {
            "data/centros_educacion_info.jsonl": {
                "format": "jsonlines",
                "overwrite": False,
                "encoding": "utf-8",
                "fields": [
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
            },
        },
        # numero de paginas que se pueden visitar a la vez.
        "CONCURRENT_REQUEST": 1,
    }
    download_delay = 2 + random.random()

    # def start_requests(self):
    #     for url in self.start_urls:
    #         proxy = random.choice(PROXIES)

    #         yield scrapy.Request(url, meta={"proxy": f"http://{proxy}"})

    def parse(self, response):
        print("*" * 150)
        print("*" * 150)

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
        try:
            lat, long = re.findall("[+-]?[0-9]+\.[0-9]+", lat_long)
        except Exception as e:
            print(e)
            lat, long = "0.0", "0.0"
        item.add_value("latitude", lat)
        item.add_value("longitude", long)

        web = description.css("p a::attr(href)").get()
        item.add_value("attr_webpage", web)

        yield item.load_item()

        print("*" * 150)
        print("*" * 150)


process = CrawlerProcess()
process.crawl(CentroEducacionSpider)
process.start()
