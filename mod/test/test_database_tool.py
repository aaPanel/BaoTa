import os
import sys
from unittest import TestCase

if "/www/server/panel" not in sys.path:
    sys.path.insert(0, "/www/server/panel")


from mod.base.database_tool import add_database


class TestDataBaseTool(TestCase):

    def test_create_data_base(self):
        mysql_data = {
            "server_id": 0,
            "database_name": "aaa",
            "db_user": "eee",
            "password": "ffff",
            "dataAccess": "ip",
            "address": "127.0.0.1",
            "codeing": "utf8mb4",
            "ps": "",
            "listen_ip": "0.0.0.0/0",
            "host": "",
        }
        print(add_database(db_type="mysql", data=mysql_data))

        pgsql_data = {
            "server_id": 0,
            "database_name": "aaa",
            "db_user": "eee",
            "password": "ffff",
            "ps": "",
            "listen_ip": "0.0.0.0/0",
        }
        print(add_database(db_type="pgsql", data=pgsql_data))

        mgo_data = {
            "server_id": 0,
            "database_name": "aaa",
            "ps": "",
        }
        print(add_database(db_type="mongodb", data=mgo_data))

    def runTest(self):
        self.test_create_data_base()


if __name__ == '__main__':
    import unittest
    s = unittest.TestSuite()
    s.addTest(TestDataBaseTool())
    unittest.TextTestRunner().run(s)
