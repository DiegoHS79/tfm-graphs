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

prob = PROVINCIAS[1]

df = pd.read_json(f"data/{prob}_centros_educacion_urls.jsonl", lines=True)
df = df.map(lambda x: x[0] if isinstance(x, list) else x)

df_detalle = pd.read_json("data/centros_educacion_info.jsonl", lines=True)
if df_detalle.empty:
    rest_urls = df.url.to_list()
else:
    list_urls = df_detalle.attr_url.apply(
        lambda x: x[0].replace("%C2%A0", " ").replace("%C2%BA", "º")
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
