import base64
import json
import os.path
import re
import time
import sys
from urllib.parse import urlparse
from dataclasses import dataclass, field
from typing import Tuple, Optional, List, Union, Dict

if "/www/server/panel/class" not in sys.path:
    sys.path.insert(0, "/www/server/panel/class")

import public
import db

if "/www/server/panel" not in sys.path:
    sys.path.insert(0, "/www/server/panel")


@dataclass
class NodeAPPKey:
    origin: str
    request_token: str
    app_key: str
    app_token: str

    def to_string(self)->str:
        data = "|".join((self.origin, self.request_token, self.app_key, self.app_token))
        return base64.b64encode(data.encode()).decode("utf-8")


@dataclass
class Node:
    remarks: str
    id: int = 0
    address: str = ""
    category_id: int = 0
    api_key: str = ""
    create_time: int = 0
    server_ip: str = ""
    status: int = 1
    error: dict = field(default_factory=dict)
    error_num: int = 0
    app_key: str = ""
    ssh_conf: dict = field(default_factory=dict)
    lpver: str = ""

    @classmethod
    def from_dict(cls, data: dict) -> Tuple[Optional["Node"], str]:
        if not isinstance(data.get('remarks', None), str):
            return None, 'remarks is required'
        if not data["remarks"].strip():
            return None, 'remarks is required'
        data["remarks"] = data["remarks"].strip()

        api_key = data.get('api_key', '')
        app_key = data.get('app_key', '')
        ssh_conf: dict = data.get('ssh_conf', {})
        if not api_key and not app_key and not ssh_conf:
            return None, 'api_key or app_key or ssh_conf is required'

        if app_key:
            app = cls.parse_app_key(app_key)
            if not app:
                return None, 'app_key格式错误'
            data["address"] = app.origin
            url = urlparse(data["address"], allow_fragments=False)
            if not url.scheme or not url.netloc:
                return None, 'address is invalid'

        if api_key:
            if not isinstance(data.get('address', None), str):
                return None, 'address is required'
            url = urlparse(data["address"], allow_fragments=False)
            if not url.scheme or not url.netloc:
                return None, 'address is invalid'

        if ssh_conf:
            for key in ("host", "port"):
                if key not in ssh_conf:
                    return None, 'ssh_conf is invalid'
            if "username" not in ssh_conf:
                ssh_conf["username"] = "root"
            if "password" not in ssh_conf:
                ssh_conf["password"] = ""
            if "pkey" not in ssh_conf:
                ssh_conf["pkey"] = ""
            if "pkey_passwd" not in ssh_conf:
                ssh_conf["pkey_passwd"] = ""

        if ssh_conf and not data.get("address", None):
            data["address"] = ssh_conf["host"]

        n = Node(
            data["remarks"], id=data.get('id', 0), address=data.get("address"), category_id=int(data.get('category_id', 0)),
            api_key=api_key, create_time=data.get('create_time', 0), server_ip=data.get('server_ip', ''),
            status=data.get('status', 1), error=data.get('error', {}), error_num=data.get('error_num', 0),
            app_key=app_key, ssh_conf=ssh_conf, lpver=data.get('lpver', '')
        )
        return n, ''

    def to_dict(self) -> dict:
        return {
            "remarks": self.remarks,
            "id": self.id,
            "address": self.address,
            "category_id": self.category_id,
            "api_key": self.api_key,
            "create_time": self.create_time,
            "server_ip": self.server_ip,
            "status": self.status,
            "error": self.error,
            "error_num": self.error_num,
            "app_key": self.app_key,
            "ssh_conf": self.ssh_conf,
            "lpver": self.lpver
        }

    def parse_server_ip(self):
        import socket
        from urllib.parse import urlparse
        if not self.address.startswith("http"):
            host = self.address  # 仅 ssh时 address本身就是host
        else:
            host = urlparse(self.address).hostname
        if isinstance(host, str) and public.check_ip(host):
            return host
        try:
            ip_address = socket.gethostbyname(host)
            return ip_address
        except socket.gaierror as e:
            public.print_log(f"Error: {e}")
            return ""

    @staticmethod
    def parse_app_key(app_key: str) -> Optional[NodeAPPKey]:
        try:
            data = base64.b64decode(app_key).decode("utf-8")
            origin, request_token, app_key, app_token = data.split("|")
            origin_arr = origin.split(":")
            if len(origin_arr) > 3:
                origin = ":".join(origin_arr[:3])
            return NodeAPPKey(origin, request_token, app_key, app_token)
        except:
            return None


class ServerNodeDB:
    _DB_FILE = public.get_panel_path() + "/data/db/node.db"
    _DB_INIT_FILE = os.path.dirname(__file__) + "/node.sql"

    def __init__(self):
        sql = db.Sql()
        sql._Sql__DB_FILE = self._DB_FILE
        self.db = sql

    def init_db(self):
        sql_data = public.readFile(self._DB_INIT_FILE)
        import sqlite3
        conn = sqlite3.connect(self._DB_FILE)
        cur = conn.cursor()
        cur.executescript(sql_data)
        cur.execute("PRAGMA table_info(node)")
        existing_cols = [row[1] for row in cur.fetchall()]
        if "ssh_test" in existing_cols:
            print("字段 ssh_test 已存在")
        else:
            cur.execute("ALTER TABLE node ADD COLUMN ssh_test INTEGER DEFAULT (0)")
        conn.commit()
        conn.close()

    def close(self):
        self.db.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_trackback):
        self.close()

    def __del__(self):
        self.close()

    def is_local_node(self, node_id: int):
        return self.db.table('node').where("id=? AND app_key = 'local' AND api_key = 'local'", (node_id,)).count() > 0

    def get_local_node(self):
        data = self.db.table('node').where("app_key = 'local' AND api_key = 'local'", ()).find()
        if isinstance(data, dict):
            return data
        return {
            "id": 0,
            "address": "",
            "category_id": 0,
            "remarks": "本机节点",
            "api_key": "local",
            "create_time": time.strftime('%Y-%m-%d %H:%M:%S'),
            "server_ip": "127.0.0.1",
            "status": 0,
            "error": 0,
            "error_num": 0,
            "app_key": "local",
            "ssh_conf": "{}",
            "lpver": "",
        }

    def create_node(self, node: Node) -> str:
        node_data = node.to_dict()
        node_data.pop("id")
        node_data["create_time"] = time.strftime('%Y-%m-%d %H:%M:%S')
        node_data.pop("error")
        node_data["status"] = 1
        node_data["ssh_conf"] = json.dumps(node_data["ssh_conf"])

        if node.category_id > 0 and not self.category_exites(node.category_id):
            return "分类不存在"

        if self.db.table('node').where('remarks=?', (node.remarks,)).count() > 0:
            return "该名称的节点已存在"
        try:
            node_id = self.db.table('node').insert(node_data)
            if isinstance(node_id, int):
                node.id = node_id
                return ""
            elif isinstance(node_id, str):
                return node_id
            else:
                return str(node_id)
        except Exception as e:
            return str(e)

    def update_node(self, node: Node, with_out_fields: List[str] = Node) -> str:
        if self.is_local_node(node.id):
            return "不能修改本机节点"
        if not self.node_id_exites(node.id):
            return "节点不存在"
        node_data = node.to_dict()
        node_data.pop("create_time")
        node_data.pop("id")
        node_data["ssh_conf"] = json.dumps(node_data["ssh_conf"])
        node_data["error"] = json.dumps(node_data["error"])
        if with_out_fields and isinstance(with_out_fields, list):
            for f in with_out_fields:
                if f in node_data:
                    node_data.pop(f)

        if node.category_id > 0 and not self.category_exites(node.category_id):
            node.category_id = 0
            node_data["category_id"] = 0
        try:
            res = self.db.table('node').where('id=?', (node.id,)).update(node_data)
            if isinstance(res, str):
                return res
        except Exception as e:
            return str(e)

        return ""

    def set_node_ssh_conf(self, node_id: int, ssh_conf: dict, ssh_test: int=0):
        pdata = {"ssh_conf": json.dumps(ssh_conf)}
        if ssh_test:
            pdata["ssh_test"] = 1
        self.db.table('node').where('id=?', (node_id,)).update(pdata)
        return

    def remove_node_ssh_conf(self, node_id: int):
        self.db.table('node').where('id=?', (node_id,)).update({"ssh_conf": "{}"})
        return

    def delete_node(self, node_id: int) -> str:
        if self.is_local_node(node_id):
            return "不能删除本机节点"
        if not self.node_id_exites(node_id):
            return "节点不存在"
        try:
            res = self.db.table('node').where('id=?', (node_id,)).delete()
            if isinstance(res, str):
                return res
        except Exception as e:
            return str(e)
        return ""

    def find_node(self, api_key:str = "", app_key: str = "") -> Optional[dict]:
        res =  self.db.table('node').where('api_key=?', (api_key, app_key)).find()
        if isinstance(res, dict):
            return res
        else:
            return None

    def get_node_list(self,
                      search: str = "",
                      category_id: int = -1,
                      offset: int = 0,
                      limit: int = 10) -> Tuple[List[Dict], str]:
        try:
            args = []
            query_str = ""
            if search:
                query_str += "remarks like ?"
                args.append('%{}%'.format(search))
            if category_id >= 0:
                if query_str:
                    query_str += " and category_id=?"
                else:
                    query_str += "category_id=?"
                args.append(category_id)
            if query_str:
                data_list = self.db.table('node').where(query_str, args).order('id desc').limit(limit, offset).select()
            else:
                data_list = self.db.table('node').order('id desc').limit(limit, offset).select()
            if self.db.ERR_INFO:
                return [], self.db.ERR_INFO
            if not isinstance(data_list, list):
                return [], str(data_list)
            return data_list, ""
        except Exception as e:
            return [], str(e)

    def query_node_list(self, *args) -> List[Dict]:
        return self.db.table('node').where(*args).select()

    def category_exites(self, category_id: int) -> bool:
        return self.db.table('category').where('id=?', (category_id,)).count() > 0

    def node_id_exites(self, node_id: int) -> bool:
        return self.db.table('node').where('id=?', (node_id,)).count() > 0

    def category_map(self) -> Dict:
        default_data = {0: "默认分类"}
        data_list = self.db.table('category').field('id,name').select()
        if isinstance(data_list, list):
            for data in data_list:
                default_data[data["id"]] = data["name"]
        return default_data

    def node_map(self) -> Dict:
        default_data = {}
        data_list = self.db.table('node').field('id,remarks').select()
        if isinstance(data_list, list):
            for data in data_list:
                default_data[data["id"]] = data["remarks"]
        return default_data

    def create_category(self, name: str) -> str:
        if self.db.table('category').where('name=?', (name,)).count() > 0:
            return "该名称的分类已存在"
        try:
            res = self.db.table('category').insert({"name": name, "create_time": time.strftime('%Y-%m-%d %H:%M:%S')})
            if isinstance(res, str):
                return res
        except Exception as e:
            return str(e)
        return ""

    def delete_category(self, category_id: int):
        self.db.table('node').where('category_id=?', (category_id,)).update({"category_id": 0})
        self.db.table('category').where('id=?', (category_id,)).delete()

    def bind_category_to_node(self, node_id: List[int], category_id: int) -> str:
        if not node_id:
            return "节点ID不能为空"
        if category_id > 0 and not self.category_exites(category_id):
            return "分类不存在"

        try:
            err = self.db.table('node').where(
                'id in ({})'.format(",".join(["?"]*len(node_id))), (*node_id,)
            ).update({"category_id": category_id})
            if isinstance(err, str):
                return err

        except Exception as e:
            return str(e)
        return ""

    def node_count(self, search, category_id) -> int:
        try:
            args = []
            query_str = ""
            if search:
                query_str += "remarks like ?"
                args.append('%{}%'.format(search))
            if category_id >= 0:
                if query_str:
                    query_str += " and category_id=?"
                else:
                    query_str += "category_id=?"
                args.append(category_id)
            if query_str:
                count = self.db.table('node').where(query_str, args).order('id desc').count()
            else:
                count = self.db.table('node').order('id desc').count()
            return count
        except:
            return 0

    def get_node_by_id(self, node_id: int) -> Optional[Dict]:
        try:
            data = self.db.table('node').where('id=?', (node_id,)).find()
            if self.db.ERR_INFO:
                return None
            if not isinstance(data, dict):
                return None
            return data
        except:
            return None

class ServerMonitorRepo:
    _REPO_DIR = public.get_panel_path() + "/data/mod_node_status_cache/"

    def __init__(self):
        if not os.path.exists(self._REPO_DIR):
            os.makedirs(self._REPO_DIR)

    def set_wait_reboot(self, server_ip: str, start: bool):
        wait_file = os.path.join(self._REPO_DIR, "wait_reboot_{}".format(server_ip))
        if start:
            return public.writeFile(wait_file, "wait_reboot")
        else:
            if os.path.exists(wait_file):
                os.remove(wait_file)

    def is_reboot_wait(self, server_ip: str):
        wait_file = os.path.join(self._REPO_DIR, "wait_reboot_{}".format(server_ip))
        # 重器待等待时间超过10分钟认为超时
        return os.path.exists(wait_file) and os.path.getmtime(wait_file) > time.time() - 610

    @staticmethod
    def get_local_server_status():
        from system import system
        return system().GetNetWork(None)

    def get_server_status(self, server_id: int) -> Optional[Dict]:
        cache_file = os.path.join(self._REPO_DIR, "server_{}.json".format(server_id))
        if not os.path.exists(cache_file):
            return None

        mtime = os.path.getmtime(cache_file)
        if time.time() - mtime > 60 * 5:
            os.remove(cache_file)
            return None
        try:
            data = public.readFile(cache_file)
            if isinstance(data, str):
                return json.loads(data)
        except:
            return None

    def save_server_status(self, server_id: int, data: Dict) -> str:
        cache_file = os.path.join(self._REPO_DIR, "server_{}.json".format(server_id))
        try:
            public.writeFile(cache_file, json.dumps(data))
            return ""
        except Exception as e:
            return str(e)

    def remove_cache(self, server_id: int):
        cache_file = os.path.join(self._REPO_DIR, "server_{}.json".format(server_id))
        if os.path.exists(cache_file):
            os.remove(cache_file)