import pprint
from typing import Literal

from pymongo import MongoClient
from pymongo.synchronous.database import Database
from pymongo.synchronous.collection import Collection


class MongoDBConnect:

    def __init__(
        self,
        database: str,
        container_name: str | None = None,
        host: str = "localhost",
        port: str = "27017",
        user: str = "root",
        password: str = "password",
    ) -> None:
        """_summary_

        Args:
            container_name (str | None, optional): _description_. Defaults to None.
            host (str, optional): _description_. Defaults to "localhost".
            port (str, optional): _description_. Defaults to "27017".
            user (str, optional): _description_. Defaults to "root".
            password (str, optional): _description_. Defaults to "password".
        """
        if container_name:
            uri = f"mongodb://{user}:{password}@{container_name}"
        else:
            uri = f"mongodb://{user}:{password}@{host}:{port}"

        self.client = MongoClient(uri)
        dbs = self.client.list_database_names()
        print(f"Data Bases availables: {', '.join(dbs)}\n")

        self.db = self.client[database]
        self.collection_name = ""

    def __collection_names(self) -> list[str]:
        return self.db.list_collection_names()

    def collection(
        self,
        name: str,
        mode: Literal["get", "create"] = "get",
        delete: bool = False,
    ) -> Collection | None:
        """_summary_

        Args:
            name (str): _description_
            mode (Literal[&quot;get&quot;, &quot;create&quot;], optional): _description_. Defaults to "get".
            delete (bool, optional): _description_. Defaults to False.

        Returns:
            Collection | None: _description_
        """
        self.collection_name = name

        if mode == "create" and name not in self.__collection_names():
            collection = self.db.create_collection(name)
            print(f"INFO - {name} collection created.")
        elif mode == "create" and name in self.__collection_names():
            print(
                f"WARNING - {name} collection already exists. Changing to 'get' mode."
            )
            mode = "get"

        if mode == "get" and name in self.__collection_names():
            collection = self.db[name]
            print(f"INFO - {name} collection loaded.")
        elif mode == "get" and name not in self.__collection_names():
            print(f"ERROR - {name} collection doesn't exist.")
            collection = None

        if delete and isinstance(collection, Collection):

            resp = input(f"\nDo you really want to delete '{name}' collection (y/n)? ")
            if resp.lower() == "y":
                collection.drop()
                print(f"INFO - '{name}' collection deleted.")
            else:
                print("INFO - Aborted deletion!!!!")
                return collection
        else:
            return collection

    def insert(self, collection: Collection, data: dict | list) -> None:
        """_summary_

        Args:
            collection (Collection): _description_
            data (dict | list): _description_
        """
        if isinstance(data, dict):
            collection.insert_one(data)
            text = "One document was"
        elif isinstance(data, list):
            collection.insert_many(data)
            text = f"{len(data)} documents were"

        print(f"INFO - {text} inserted into the '{self.collection_name}' collection.")

    def query(self, collection: Collection, query: str = "all"):
        """_summary_
        https://www.mongodb.com/docs/languages/python/pymongo-driver/current/read/specify-a-query/

        Args:
            collection (Collection): _description_
            query (str, optional): _description_. Defaults to "all".
        """

        if query == "all" and isinstance(collection, Collection):
            print(len(list(collection.find({}))))
            # for c in collection.find({}):
            #     print(c)
        else:
            print(f"WARNING - The operation couldn't be done.")

    def db_manage(self, list_collections: bool = False):
        print()
        if list_collections:
            for name in self.__collection_names():
                count = len(list(self.db[name].find({}).clone()))
                print(f"{name} -> {count} documents")

    def close(self):
        self.client.close()
