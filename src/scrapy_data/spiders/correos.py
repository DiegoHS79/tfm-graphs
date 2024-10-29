import os
import re
import time
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import NoSuchElementException
from scrapy.crawler import CrawlerProcess
from scrapy.item import Field
from scrapy.item import Item
from scrapy.spiders import Spider
from scrapy.selector import Selector
from scrapy.loader import ItemLoader
from itemloaders.processors import MapCompose

from utils import get_user_agent

os.system("clear")

OFIS_URL_FILE = Path("data/correos_urls.csv")

if not OFIS_URL_FILE.exists():
    headers = {"user-agent": get_user_agent()}
    url_ofis = "https://www.correosoficinas.es/"
    resp = requests.get(url_ofis, headers=headers)
    soup = BeautifulSoup(resp.text, "html.parser")

    urls = soup.select("table tr > td > a")
    URLS = {"url": [url.get("href") for url in urls]}

    df = pd.DataFrame(URLS)
    df.to_csv(OFIS_URL_FILE, index=False, sep="\t")
else:
    df = pd.read_csv(OFIS_URL_FILE, sep="\t")

URLS = df.url.to_list()
# URLS = ["https://correosoficinas.es/localidad/madrid"]

URLS_OFI = []
ALL_OFIS_URLS = Path("data/correos_ofis_urls.csv")
if not ALL_OFIS_URLS.exists():
    print(len(URLS_OFI))
    for URL in URLS:
        print(URL)
        opts = Options()
        opts.add_argument(f"user-agent={get_user_agent()}")
        opts.add_argument("--disable-search-engine-choice-screen")
        opts.add_argument("--no-sandbox")

        user_home_dir = os.path.expanduser("~")
        chrome_binary_path = os.path.join(user_home_dir, "chrome-linux64", "chrome")
        chromedriver_path = os.path.join(
            user_home_dir, "chromedriver-linux64", "chromedriver"
        )

        opts.binary_location = chrome_binary_path
        with webdriver.Chrome(
            service=Service(chromedriver_path), options=opts
        ) as driver:

            driver.get(URL)
            wait = WebDriverWait(driver, 10)

            counter = 1
            while True:
                try:
                    next_link = driver.find_element(
                        By.CSS_SELECTOR, f"li > span[data-pageurl='{counter}']"
                    ).click()
                    time.sleep(5.0)
                    # https://www.selenium.dev/selenium/docs/api/py/webdriver_support/selenium.webdriver.support.expected_conditions.html
                    links = WebDriverWait(driver, 10).until(
                        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "h3 > a"))
                    )

                    # links = driver.find_elements(By.CSS_SELECTOR, "h3 > a")
                    for tag_a in links:
                        URLS_OFI.append(tag_a.get_attribute("href"))

                    print(len(URLS_OFI))
                    counter += 1
                except NoSuchElementException as e:
                    print(
                        "No more pagination numbers found, continue to the next URL/n"
                    )
                    break
        # break

    df = pd.DataFrame({"url": URLS_OFI})
    df.to_csv(ALL_OFIS_URLS, index=False, sep="\t")
else:
    df = pd.read_csv(ALL_OFIS_URLS, sep="\t")


CORREOS_JSON = Path("data/correos_oficinas.jsonl")


class DetallesOficinas(Item):
    url = Field()
    name = Field()
    address = Field()
    cp = Field()
    city = Field()
    community = Field()
    telephone = Field()


class OficinasSpider(Spider):
    name = "Oficinas Correos"
    custom_settings = {
        "USER_AGENT": get_user_agent(),
        "COOKIES_ENABLED": True,
        "CONCURRENT_REQUEST": 1,
        "FEEDS": {
            CORREOS_JSON: {
                "format": "jsonlines",
                "overwrite": True,
                "encoding": "utf-8",
                "fields": [
                    "url",
                    "name",
                    "address",
                    "cp",
                    "city",
                    "community",
                    "telephone",
                ],
            },
        },
        "DOWNLOAD_DELAY": 3,
    }
    allowed_domains = ["correosoficinas.es"]

    def __init__(self, urls, **kwargs):
        self.start_urls = urls
        super().__init__(**kwargs)

    def parse(self, response):
        print("*" * 150)
        print("*" * 150)
        item = ItemLoader(DetallesOficinas(), response)
        item.add_value("url", response.url)
        sel = Selector(response)

        name = sel.css("div h1::text").get()
        item.add_value(
            "name",
            name,
            MapCompose(lambda x: x.replace("\n", "").strip().lower()),
        )

        addr = sel.css("div h1 + p::text").get()
        data = addr.split(",")

        cp = re.findall("\d+", addr)[-1]
        item.add_value("cp", cp, MapCompose(lambda x: x.strip().lower()))
        city = data[-1]
        item.add_value("city", city, MapCompose(lambda x: x.strip().lower()))

        item.add_value(
            "address",
            " ".join(data),
            MapCompose(lambda x: x.replace(cp, "").replace(city, "").strip(" ,")),
        )

        ps = sel.css("div.post-detail-content > p")
        for p in ps:
            data = p.css("p::text").get()
            if p.css("p strong::text").get() == "Comunidad autónoma":
                item.add_value(
                    "community", data, MapCompose(lambda x: x.strip(" :").lower())
                )
            elif p.css("p strong::text").get() == "Teléfono":
                item.add_value(
                    "telephone", data, MapCompose(lambda x: x.strip(" :").lower())
                )

        yield item.load_item()


process = CrawlerProcess()
process.crawl(OficinasSpider, urls=df.url.to_list())
process.start()
