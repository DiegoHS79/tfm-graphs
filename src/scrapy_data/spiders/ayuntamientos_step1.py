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
from scrapy.spiders import Spider, Rule
from scrapy.selector import Selector
from scrapy.linkextractors import LinkExtractor
from scrapy.loader import ItemLoader

from utils import get_user_agent

os.system("clear")


class UrlAyuntamientos(Item):
    url = Field()
    town = Field()


class AyuntamientosSpider(Spider):
    name = "CentrosEducacion"

    # ?https://docs.scrapy.org/en/latest/topics/feed-exports.html#feed-export-fields
    custom_settings = {
        "USER_AGENT": get_user_agent(),
        # para los caracteres especiales.
        "FEEDS": {
            f"data/ayuntamientos.jsonl": {
                "format": "jsonlines",
                "overwrite": True,
                "encoding": "utf-8",
                "fields": ["url", "town"],
            },
        },
        "CONCURRENT_REQUEST": 1,  # numero de paginas que se pueden visitar a la vez.
    }
    # scrapy no toma este valor fijo, sino que pone un rango entre 0.5 * download_delay y 1.5 * download_delay
    download_delay = 2 + random.random()
    start_urls = [
        "https://administracion.gob.es/pagFront/espanaAdmon/directorioOrganigramas/fichaUnidadOrganica.htm"
        + "?idUnidOrganica=17190&origenUO=quienEsQuien&nJerOriginal=0&desOrganismo=&idNivAdmin=3&idCCAA=0"
        + "&idProv=&numPagAct=1&volver=quienEsQuien"
    ]

    def parse(self, response):
        print("*" * 150)
        print("*" * 150)
        # try:
        #     if sel.css("#MainContent_EnviarLink").get():
        #         input()
        # except Exception as e:
        #     print(e)

        sel = Selector(response)
        li_list = sel.css(".o-layout .o-unit ul > li.o-list--style")
        for li in li_list:
            item = ItemLoader(UrlAyuntamientos(), response)

            url = "https://administracion.gob.es" + li.css("a::attr(href)").get()
            item.add_value("url", url)

            town = li.css("a::text").get()
            item.add_value("town", town)

            yield item.load_item()

        print("*" * 150)
        print("*" * 150)


if __name__ == "__main__":
    process = CrawlerProcess()
    process.crawl(AyuntamientosSpider)
    process.start()
