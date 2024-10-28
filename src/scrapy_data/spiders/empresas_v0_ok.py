import os
import random
import time
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup
from scrapy.crawler import CrawlerProcess
from scrapy.item import Field
from scrapy.item import Item
from scrapy.spiders import CrawlSpider, Rule
from scrapy.selector import Selector
from scrapy.linkextractors import LinkExtractor
from scrapy.loader import ItemLoader
from itemloaders.processors import MapCompose

from utils import get_user_agent

os.system("clear")

EMPRESAS_MUNICIPIO_CSV = Path("data/empresas_municipios_urls.csv")
if not EMPRESAS_MUNICIPIO_CSV.exists():
    headers = {"user-agent": get_user_agent()}
    url_puestos = "https://www.axesor.es/directorio-informacion-empresas"
    resp = requests.get(url_puestos, headers=headers)
    soup = BeautifulSoup(resp.text, "html.parser")

    urls = soup.select("table.provincias > tbody td > a")
    URLS = [url.get("href") for url in urls]
    PROVS = [url.text for url in urls]

    df = pd.DataFrame(columns=["municipio", "provincia", "url"])
    for URL, PROV in zip(URLS, PROVS):
        print(URL)

        headers = {"user-agent": get_user_agent()}
        resp = requests.get(f"https:{URL}", headers=headers)
        soup = BeautifulSoup(resp.text, "html.parser")

        m_urls = soup.select("table.provincias > tbody td > a")
        for m_url in m_urls:
            df_tmp = pd.DataFrame(
                {
                    "municipio": [m_url.text],
                    "provincia": [PROV],
                    "url": [f"https:{m_url.get('href')}"],
                }
            )
            df = pd.concat([df, df_tmp])

        time.sleep(0.5 + random.random())

    df.reset_index(drop=True, inplace=True)
    df.to_csv(EMPRESAS_MUNICIPIO_CSV, index=False, sep="\t")
else:
    df = pd.read_csv(EMPRESAS_MUNICIPIO_CSV, sep="\t")

EMP_URLS = df.url.to_list()
EMPRESAS_JSON = "data/empresas.jsonl"
EMPRESAS_CSV = "data/empresas.csv"

if 1:

    class DetallesEmpresa(Item):
        url = Field()
        name = Field()
        address = Field()
        cp = Field()
        city = Field()
        province = Field()
        telephone = Field()
        cif = Field()
        forma = Field()
        # https://www.ine.es/daco/daco42/clasificaciones/cnae09/estructura_cnae2009.xls
        cnae = Field()
        # Standard Industrial Classification
        # https://resources.companieshouse.gov.uk/sic/
        sic = Field()

    class EmpresasSpider(CrawlSpider):
        name = "Empresas"
        start_urls = EMP_URLS
        # start_urls = EMP_URLS[0:1]
        # start_urls = [
        #     "https://www.axesor.es/directorio-informacion-empresas/empresas-de-Badajoz/informacion-empresas-de-Navalvillar-De-Pela/1"
        # ]
        custom_settings = {
            "USER_AGENT": get_user_agent(),
            "CONCURRENT_REQUEST": 1,
            "FEEDS": {
                EMPRESAS_JSON: {
                    "format": "jsonlines",
                    "overwrite": True,
                    "encoding": "utf-8",
                    "fields": [
                        "url",
                        "name",
                        "address",
                        "cp",
                        "city",
                        "province",
                        "telephone",
                        "cif",
                        "forma",
                        "cnae",
                        "sic",
                    ],
                },
            },
        }
        download_delay = 1 + random.random()
        allowed_domains = ["axesor.es"]
        rules = (
            # Regla para Paginacion
            Rule(
                LinkExtractor(allow=r"\/\d+$"),
                follow=True,
            ),
            Rule(
                # https://docs.scrapy.org/en/latest/topics/link-extractors.html#module-scrapy.linkextractors.lxmlhtml
                # LinkExtractor solo busca en tags "a"
                LinkExtractor(
                    allow=r"Empresas\/\d+\/",
                ),
                follow=True,
                callback="parse_individual",
            ),
        )

        def parse_individual(self, response):
            print("*" * 150)
            print("*" * 150)
            item = ItemLoader(DetallesEmpresa(), response)
            item.add_value("url", response.url)
            sel = Selector(response)

            nombre = sel.css("table#tablaInformacionGeneral tbody tr h3::text").get()
            item.add_value(
                "name",
                nombre,
                MapCompose(lambda x: x.replace("\n", "").strip().lower()),
            )

            direc = sel.css(
                "table#tablaInformacionGeneral tbody tr td#Direccion + td span > span"
            )
            for i, anot in enumerate(direc):
                if i == 0:
                    item.add_value(
                        "address",
                        anot.css("span::text").get(),
                        MapCompose(lambda x: x.replace("\n", "").strip().lower()),
                    )
                elif i == 1:
                    item.add_value(
                        "cp",
                        anot.css("span::text").get(),
                        MapCompose(lambda x: x.replace("\n", "").strip(" ,").lower()),
                    )
                elif i == 2:
                    item.add_value(
                        "city",
                        anot.css("span::text").get(),
                        MapCompose(lambda x: x.replace("\n", "").strip(" ,").lower()),
                    )
                elif i == 3:
                    item.add_value(
                        "province",
                        anot.css("span::text").get(),
                        MapCompose(lambda x: x.replace("\n", "").strip(" ,").lower()),
                    )

            tel = sel.css(
                "table#tablaInformacionGeneral tbody tr td#Telefono + td::text"
            ).get()
            item.add_value(
                "telephone",
                tel,
                MapCompose(lambda x: x.replace("&nbsp", "").strip().lower()),
            )

            trs = sel.css("table#tablaInformacionGeneral tbody tr ")
            for tr in trs:
                save_cif = False
                save_forma = False
                save_cnae = False
                save_sic = False
                for j, td in enumerate(tr.css("td")):
                    text = td.css("td::text").get()
                    if text == "CIF:":
                        save_cif = True
                    elif text == "Forma jurídica:":
                        save_forma = True
                    elif text == "CNAE:":
                        save_cnae = True
                    elif text == "SIC:":
                        save_sic = True

                    if save_cif and j == 1:
                        item.add_value(
                            "cif",
                            text,
                            MapCompose(lambda x: x.strip().lower()),
                        )
                        save_cif = False
                    elif save_forma and j == 1:
                        item.add_value(
                            "forma",
                            text,
                            MapCompose(lambda x: x.strip().lower()),
                        )
                        save_forma = False
                    elif save_cnae and j == 1:
                        item.add_value(
                            "cnae",
                            text,
                            MapCompose(lambda x: x.replace("\n", "").strip().lower()),
                        )
                        save_cnae = False
                    elif save_sic and j == 1:
                        item.add_value(
                            "sic",
                            text,
                            MapCompose(lambda x: x.replace("\n", "").strip().lower()),
                        )
                        save_sic = False

            yield item.load_item()

    process = CrawlerProcess()
    process.crawl(EmpresasSpider)
    process.start()
