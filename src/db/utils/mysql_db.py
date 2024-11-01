import os

import pymysql as ps

# from celta_mali.utils.exceptions import TableSQLError

os.system("clear")

# https://dev.mysql.com/doc/connector-python/en/connector-python-examples.html


class MySQLConnect:

    def __init__(
        self,
        host_name: str = "127.0.0.1",
        port: str = "3306",
        user: str = "user",
        password: str = "password",
        database_name: str = "db",
    ) -> None:

        self.host_name = host_name
        self.port = port
        self.user = user
        self.password = password
        self.database_name = database_name
        # self.query = query

    def __connect(self) -> None:
        self.db = ps.connect(
            host=self.host_name,
            user=self.user,
            password=self.password,
            database=self.database_name,
        )
        # prepare a cursor object using cursor() method
        self.cursor = self.db.cursor()

    # def __execute_query(self) -> None:
    #     res = self.cursor.execute(self.query)
    #     # if the query was executed with success, 'res' returns 0

    #     self.cursor.close()

    def __disconnect(self) -> None:
        self.db.close()

    def query(self, query: str) -> None:
        # Abre conexion con la base de datos
        self.__connect()

        # Ejecutar la query
        self.cursor.execute(query)

        # cierra la conexion
        self.__disconnect()

    # def create_table(
    #     self, table_name: str, query: str, if_exist: Literal["remove", "exit"] = "exit"
    # ) -> None:
    #     self.query = query

    #     if "CREATE TABLE" not in self.query:
    #         raise TableSQLError(keyword="CREATE TABLE")
    #     # Abre conexion con la base de datos
    #     self.__connect()

    #     # check if table exist
    #     res = self.cursor.execute(f"SHOW TABLES LIKE '{table_name}';")
    #     if res and if_exist == "exit":
    #         raise TableSQLError(message=f"Table {table_name} already exist.")
    #     elif res and if_exist == "replace":
    #         self.cursor.execute(
    #             f"""
    #             DROP TABLE {table_name};
    #         """
    #         )
    #         print(f"INFO: Table {table_name} was removed correctly")

    #     self.__execute_query()

    #     # cierra la conexion
    #     self.__disconnect()

    # def add_rows(self, table_name: str, query: str):
    #     self.query = query

    #     if "INSERT INTO" not in self.query or "VALUES" not in self.query:
    #         raise TableSQLError(keyword="INSERT INTO")
    #     # Abre conexion con la base de datos
    #     self.__connect()
    #     self.__execute_query()
    #     self.db.commit()
    #     self.__disconnect()
