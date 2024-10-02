import json
import os
import random
import requests
from datetime import date, datetime
from pathlib import Path
from typing import Any

BASE_FILE_PATH = "data/user_agents.json"
DATE_FORMAT = "%d-%m-%Y"


def _user_agents_from_source() -> None:
    print("Downloading latest user agents from original source.")

    download_url = "https://jnrbsn.github.io/user-agents/user-agents.json"
    response = requests.get(download_url, timeout=5)
    response.raise_for_status()
    user_agents = response.json()

    info = {
        "update_date": date.today().strftime(DATE_FORMAT),
        "user_agents": user_agents,
    }

    with open(BASE_FILE_PATH, "w") as outfile:
        outfile.write(json.dumps(info, indent=4))


def _load_json_file() -> tuple[Any]:
    with open(BASE_FILE_PATH, "r") as openfile:
        json_object = json.load(openfile)
        updated_date = json_object["update_date"]
        user_agents = json_object["user_agents"]

    return updated_date, user_agents


def get_user_agents() -> str:
    if Path(BASE_FILE_PATH).exists():
        updated_date, user_agents = _load_json_file()

    substract = date.today() - datetime.strptime(updated_date, DATE_FORMAT).date()
    if substract.days >= 7:
        _user_agents_from_source()
        updated_date, user_agents = _load_json_file()

    return random.choice(user_agents)


if "__main__" == __name__:
    os.system("clear")

    user_agent = get_user_agents()
    print(user_agent)
