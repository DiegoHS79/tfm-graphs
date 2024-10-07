import random
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from .user_agents import get_user_agent


def manage_catpcha(url: str, catpcha_css: str, button_css: str):
    opts = Options()
    opts.add_argument(f"user-agent={get_user_agent()}")
    opts.add_argument("--headless")
    opts.add_argument("--no-sandbox")
    # Agregar a todos sus scripts de selenium para que no aparezca la ventana de seleccionar navegador por defecto: (desde agosto 2024)
    opts.add_argument("--disable-search-engine-choice-screen")
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=opts,
    )

    # Para interactuar con los elementos dentro de un iframe tengo que realizar
    # un cambio de contexto hacia el iframe
    driver.switch_to.frame(driver.find_element(By.CSS_SELECTOR, "iframe"))
    driver.get(url)

    time.sleep(random.uniform(8, 10))

    captcha = driver.find_element(By.CSS_SELECTOR, catpcha_css)
    captcha.click()

    # input es solo si tenemos alg'un boton de submit o algo por el estilo
    input()

    # Una vez resuelto el captcha, devolvemos el driver al contexto de la pagina principal
    # Es decir, salimos del iframe
    driver.switch_to.default_content()
    submit_button = driver.find_element(By.CSS_SELECTOR, button_css)
    submit_button.click()
