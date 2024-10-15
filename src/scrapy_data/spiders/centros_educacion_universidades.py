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


class DetallesUniversidad(Item):
    url = Field()
    name = Field()
    type = Field()
    address = Field()
    telephone = Field()
    email = Field()


class UniversidadesSpider(Spider):
    name = "CentrosUniversitarios"
    start_urls = ["https://www.universidades.gob.es/listado-de-universidades/"]

    # ?https://docs.scrapy.org/en/latest/topics/feed-exports.html#feed-export-fields
    custom_settings = {
        "USER_AGENT": get_user_agent(),
        "CONCURRENT_REQUEST": 1,
        "FEEDS": {
            f"data/centros_educacion_universidades.jsonl": {
                "format": "jsonlines",
                "overwrite": True,
                "encoding": "utf-8",
                "fields": [
                    "url",
                    "name",
                    "type",
                    "address",
                    "city",
                    "province",
                    "telephone",
                    "email",
                ],
            },
        },
    }
    # download_delay = 2 + random.random()

    def parse(self, response):
        print("*" * 150)
        print("*" * 150)

        print(f"Status connection: {response.status}")
        print(f"Priginal page: {response.url}", end="\n\n")
        sel = Selector(response)
        univs = sel.css(".elementor-tab-content.elementor-clearfix > ul > li")
        for uni in univs:
            item = ItemLoader(DetallesUniversidad(), uni)
            url = uni.css("a::attr(href)").get()
            item.add_value("url", url)

            name = uni.css("a::text").get()
            item.add_value("name", name)

            detalles = uni.css("ul > li")
            for detalle in detalles:
                text = detalle.css("li::text").get()
                if "Dirección:" in text:
                    item.add_value("address", text.replace("Dirección:", "").strip())
                elif "Teléfono:" in text:
                    item.add_value("telephone", text.replace("Teléfono:", "").strip())
                elif "Tipo:" in text:
                    item.add_value("type", text.replace("Tipo:", "").strip())

            try:
                mail = uni.css("ul > li > a::attr(href)").get()
                mail = mail.replace("mailto:", "").strip()
            except AttributeError as e:
                print(e)
                mail = ""

            item.add_value("email", mail.replace("mailto:", "").strip())

            break

            yield item.load_item()

        print("*" * 150)
        print("*" * 150)


process = CrawlerProcess()
process.crawl(UniversidadesSpider)
process.start()
