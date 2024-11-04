import os

os.system("clear")

from utils.mongo_db import MongoDBConnect

conn = MongoDBConnect(container_name="mongo-tfm", database="tfm-data")

col = conn.collection(
    name="education",
    # mode="create",
    # delete=True,
)

# listar
conn.query(collection=col)
# print(len(data))

# conn.db_manage(list_collections=True)
conn.close()
