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
from scrapy.spiders import CrawlSpider, Spider, Rule
from scrapy.selector import Selector
from scrapy.linkextractors import LinkExtractor
from scrapy.loader import ItemLoader
from itemloaders.processors import MapCompose

from utils import get_user_agent

os.system("clear")

EMPRESAS_MUNICIPIO_CSV = Path("data/empresas_municipios_urls.csv")
if 0:
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

EMPRESAS_JSON = Path("data/empresas_urls.jsonl")
if 0:

    class DetallesEmpresa(Item):
        url = Field()
        city = Field()
        province = Field()

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
                    "fields": ["url", "city", "province"],
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
                callback="parse_urls",
            ),
        )

        def parse_urls(self, response):
            print("*" * 150)
            print("*" * 150)
            sel = Selector(response)

            trs = sel.css("div#listaEmpresas > table tbody > tr")
            for tr in trs:
                item = ItemLoader(DetallesEmpresa(), tr)
                url = tr.css("a::attr(href)").get()
                item.add_value("url", url)

                tds = tr.css("td")
                city = tds[1].css("td span::text").get()
                item.add_value("city", city)

                prov = tds[2].css("td span::text").get()
                item.add_value("province", prov)

                yield item.load_item()

    process = CrawlerProcess()
    process.crawl(EmpresasSpider)
    process.start()


def read_large_json(file_name: Path, chunk: int = 100000):
    for chunk in pd.read_json(file_name, lines=True, chunksize=chunk):
        yield chunk


# creamos los chunks para poder trabajar mejor
if 0:
    for i, df_urls in enumerate(read_large_json(EMPRESAS_JSON)):
        EMPRESAS_CSV = Path(f"data/empresas/empresas_{i}.csv")
        print(EMPRESAS_CSV)
        df_urls = df_urls.map(lambda x: x[0], na_action="ignore")
        df_urls.to_csv(EMPRESAS_CSV, index=False, sep="\t")


class DetallesEmpresa2(Item):
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


df_prox = pd.read_csv("utils/proxies.csv", sep=",")
proxies = df_prox.ip.apply(lambda x: x + ":") + df_prox.port.astype("str")


if 1:
    for i in range(43):
        if i in [0, 1, 2, 3]:
            continue
        EMPRESAS_CSV = Path(f"data/empresas/empresas_{i}.csv")
        df_urls = pd.read_csv(EMPRESAS_CSV, sep="\t")
        EMPRESAS_INFO = Path(f"data/empresas/empresas_{i}.jsonl")

        class EmpresasSpider2(Spider):
            name = "Empresas"
            custom_settings = {
                "USER_AGENT": get_user_agent(),
                "COOKIES_ENABLED": False,
                # "RETRY_TIMES": 3,
                # "RETRY_HTTP_CODES": [500, 503, 504, 400, 403, 404, 408],
                "CONCURRENT_REQUEST": 1,
                # "DOWNLOADER_MIDDLEWARES": {
                #     "rotating_proxies.middlewares.RotatingProxyMiddleware": 610,
                #     "rotating_proxies.middlewares.BanDetectionMiddleware": 620,
                # },
                # "ROTATING_PROXY_LIST": proxies.to_list(),
                "FEEDS": {
                    EMPRESAS_INFO: {
                        "format": "jsonlines",
                        "overwrite": False,
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
                "DOWNLOAD_DELAY": 3,
                # "RANDOMIZE_DOWNLOAD_DELAY": True,
                # "AUTOTHROTTLE_ENABLED": True,
                # "ROBOTSTXT_OBEY": True,  # obedecer la reglas de robots de la p'agina destino
            }
            # download_delay = 3 + random.random()
            allowed_domains = ["axesor.es"]

            def __init__(self, urls, **kwargs):
                self.start_urls = urls
                super().__init__(**kwargs)

            def parse(self, response):
                print("*" * 150)
                print("*" * 150)
                item = ItemLoader(DetallesEmpresa2(), response)
                item.add_value("url", response.url)
                sel = Selector(response)

                nombre = sel.css(
                    "table#tablaInformacionGeneral tbody tr h3::text"
                ).get()
                item.add_value(
                    "name",
                    nombre,
                    MapCompose(lambda x: x.replace("\n", "").strip().lower()),
                )

                direc = sel.css(
                    "table#tablaInformacionGeneral tbody tr td#Direccion + td span > span"
                )
                if len(direc) == 0:
                    direc = sel.css(
                        "table#tablaInformacionGeneral tbody tr td#Direccion + td span"
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
                            MapCompose(
                                lambda x: x.replace("\n", "").strip(" ,").lower()
                            ),
                        )
                    elif i == 2:
                        item.add_value(
                            "city",
                            anot.css("span::text").get(),
                            MapCompose(
                                lambda x: x.replace("\n", "").strip(" ,").lower()
                            ),
                        )
                    elif i == 3:
                        item.add_value(
                            "province",
                            anot.css("span::text").get(),
                            MapCompose(
                                lambda x: x.replace("\n", "").strip(" ,").lower()
                            ),
                        )

                tel = sel.css(
                    "table#tablaInformacionGeneral tbody tr td#Telefono + td::text"
                ).get()
                item.add_value(
                    "telephone",
                    tel,
                    MapCompose(lambda x: x.replace("&nbsp", "").strip().lower()),
                )

                trs = sel.css("table#tablaInformacionGeneral tbody tr")
                for tr in trs:
                    save_cif = False
                    save_forma = False
                    save_cnae = False
                    save_sic = False
                    for j, td in enumerate(tr.css("td")):
                        text = td.css("td::text").get()
                        if text is None:
                            text = td.css("td span::text").get()
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
                                MapCompose(
                                    lambda x: x.replace("\n", "").strip().lower()
                                ),
                            )
                            save_cnae = False
                        elif save_sic and j == 1:
                            item.add_value(
                                "sic",
                                text,
                                MapCompose(
                                    lambda x: x.replace("\n", "").strip().lower()
                                ),
                            )
                            save_sic = False

                yield item.load_item()

        if not EMPRESAS_INFO.exists():
            urls_rest = df_urls.url.apply(lambda x: f"https:{x}").to_list()

        else:
            # cambiar el numero del archivo al que corresponda
            # for df_def in pd.read_json(EMPRESAS_INFO, lines=True):

            urls_all = set(df_urls.url.apply(lambda x: f"https:{x}").to_list())
            print(f"todos: {len(urls_all)}")
            # print(urls_all)
            df_def = pd.read_json(EMPRESAS_INFO, lines=True)
            urls_def = set(df_def.url.apply(lambda x: x[0]).to_list())
            print(f"hay: {len(urls_def)}")
            # print(urls_def)
            urls_rest = list(set(urls_all).difference(set(urls_def)))
            print(f"quedan: {len(urls_rest)}")

        process = CrawlerProcess()
        process.crawl(EmpresasSpider2, urls=urls_rest)
        process.start()

        break
