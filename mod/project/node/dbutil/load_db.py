import json
import os.path
import re
import sys
from dataclasses import dataclass, field
from typing import Tuple, Optional, List, Union

if "/www/server/panel/class" not in sys.path:
    sys.path.insert(0, "/www/server/panel/class")

import public
import db

if "/www/server/panel" not in sys.path:
    sys.path.insert(0, "/www/server/panel")


@dataclass
class LoadSite:
    name: str
    site_name: str
    site_type: str
    ps: str = ''
    http_config: dict = field(default_factory=lambda: {
        "proxy_next_upstream": "error timeout http_500 http_502 http_503 http_504",
        "http_alg": "sticky_cookie",
        "proxy_cache_status": False,
        "cache_time": "1d",
        "cache_suffix": "css,js,jpe,jpeg,gif,png,webp,woff,eot,ttf,svg,ico,css.map,js.map",
    })
    tcp_config: dict = field(default_factory=lambda: {
        "proxy_connect_timeout": 8,
        "proxy_timeout": 86400,
        "host": "127.0.0.1",
        "port": 80,
        "type": "tcp"
    })
    created_at: int = 0
    load_id: int = 0
    site_id: int = 0

    @classmethod
    def bind_http_load(cls, data: dict) -> Tuple[Optional["LoadSite"], str]:
        check_msg = cls.base_check(data)
        if check_msg:
            return None, check_msg
        if not data.get('site_name', None):
            return None, 'site_name is required'
        if not public.is_domain(data['site_name']):
            return None, 'site_name is invalid'
        if not isinstance(data.get('http_config', None), dict):
            return None, 'http_config is required'
        else:
            if "proxy_cache_status" not in dict.keys(data['http_config']): #兼容旧版本数据
                data['http_config']["proxy_cache_status"] = False
                data['http_config']["cache_time"] = "1d"
                data['http_config']["cache_suffix"] = "css,js,jpe,jpeg,gif,png,webp,woff,eot,ttf,svg,ico,css.map,js.map"
            for k in ['proxy_next_upstream', 'http_alg', "proxy_cache_status", "cache_time", "cache_suffix"]:
                if k not in dict.keys(data['http_config']):
                    return None, 'http_config.{} is required'.format(k)
            for i in data['http_config']['proxy_next_upstream'].split():
                if i not in ('error', 'timeout') and not re.match(r'^http_\d{3}$', i):
                    return None, 'http_config.proxy_next_upstream is invalid'
            if data['http_config']['http_alg'] not in ('sticky_cookie', 'round_robin', 'least_conn', 'ip_hash'):
                return None, 'http_config.http_alg is invalid'
            if not isinstance(data['http_config']['proxy_cache_status'], bool):
                return None, 'http_config.proxy_cache_status is invalid'
            if not isinstance(data['http_config']['cache_time'], str):
                return None, 'http_config.cache_time is invalid'
            if not re.match(r"^[0-9]+([smhd])$", data['http_config']['cache_time']):
                return None, 'http_config.cache_time is invalid'
            cache_suffix = data['http_config']['cache_suffix']
            cache_suffix_list = []
            for suffix in cache_suffix.split(","):
                tmp_suffix = re.sub(r"\s", "", suffix)
                if not tmp_suffix:
                    continue
                cache_suffix_list.append(tmp_suffix)
            real_cache_suffix = ",".join(cache_suffix_list)
            if not real_cache_suffix:
                real_cache_suffix = "css,js,jpe,jpeg,gif,png,webp,woff,eot,ttf,svg,ico,css.map,js.map"
            data['http_config']['cache_suffix'] = real_cache_suffix

        l = LoadSite(data.get('name'), data.get('site_name'), 'http', data.get('ps', ''),
                     http_config=data.get('http_config'),
                     created_at=data.get('created_at', 0), load_id=data.get('load_id', 0),
                     site_id=data.get('site_id', 0))
        return l, ""

    @classmethod
    def base_check(cls, data) -> str:
        if not data.get('name', None):
            return 'name is required'
        if not re.match(r'^[a-zA-Z0-9][a-zA-Z0-9_]+$', data['name']):
            return '名称只能包含字母、数字、下划线且不能以数字和下划线开头'
        if not len(data['name']) >= 3:
            return '名称长度不能小于3个字符'
        return ""

    @classmethod
    def bind_tcp_load(cls, data: dict) -> Tuple[Optional["LoadSite"], str]:
        check_msg = cls.base_check(data)
        if check_msg:
            return None, check_msg
        if not isinstance(data.get('tcp_config', None), dict):
            return None, 'tcp_config is required'
        else:
            for k in ['proxy_connect_timeout', 'proxy_timeout', 'host', 'port', 'type']:
                if not data['tcp_config'].get(k):
                    return None, 'tcp_config.{} is required'.format(k)
            if data['tcp_config']['type'] not in ('tcp', 'udp'):
                return None, 'tcp_config.type is invalid'
            if not isinstance(data['tcp_config']['port'], int) and not 1 <= data['tcp_config']['port'] <= 65535:
                return None, 'tcp_config.port is invalid'
            if not public.check_ip(data['tcp_config']['host']):
                return None, 'tcp_config.host is invalid'

        l = LoadSite(data.get('name'), data.get('site_name'), 'tcp', ps=data.get('ps', ''),
                     tcp_config=data.get('tcp_config'),
                     created_at=data.get('created_at', 0), load_id=data.get('load_id', 0),
                     site_id=data.get('site_id', 0))
        return l, ""

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "site_name": self.site_name,
            "site_type": self.site_type,
            "ps": self.ps,
            "http_config": self.http_config,
            "tcp_config": self.tcp_config,
            "created_at": self.created_at,
            "load_id": self.load_id,
            "site_id": self.site_id
        }


@dataclass
class HttpNode:
    node_id: int
    node_site_name: str
    port: int
    location: str = "/"
    path: str = "/"
    node_status: str = "online"  # online, backup, down
    weight: int = 1
    max_fail: int = 3
    fail_timeout: int = 600
    ps: str = ""
    created_at: int = 0
    node_site_id: int = 0
    id: int = 0
    load_id: int = 0

    @classmethod
    def bind(cls, data: dict) -> Tuple[Optional["HttpNode"], str]:
        if not isinstance(data.get('node_site_name', None), str):
            return None, 'node_site_name is required'
        if not public.is_domain(data['node_site_name']) and not public.check_ip(data['node_site_name']):
            return None, 'node_site_name is invalid'
        if not isinstance(data.get('port', None), int):
            return None, 'port is required'
        if not 1 <= data['port'] <= 65535:
            return None, 'port is invalid'
        if not isinstance(data.get('node_id', None), int):
            return None, 'node_id is required'
        if not isinstance(data.get('node_status', None), str):
            return None, 'node_status is required'
        if not data['node_status'] in ('online', 'backup', 'down'):
            return None, 'node_status is invalid'

        n = HttpNode(data.get('node_id'), data.get('node_site_name'), data.get('port'), "/",
                     data.get('path', "/"), data.get('node_status', "online"), data.get('weight', 1),
                     data.get('max_fail', 3), data.get('fail_timeout', 600), data.get('ps', ''),
                     data.get('created_at', 0), data.get('node_site_id', 0), data.get('id', 0),
                     data.get('load_id', 0)
                     )
        return n, ""

    def to_dict(self) -> dict:
        return {
            "node_id": self.node_id,
            "node_site_name": self.node_site_name,
            "port": self.port,
            "location": self.location,
            "path": self.path,
            "node_status": self.node_status,
            "weight": self.weight,
            "max_fail": self.max_fail,
            "fail_timeout": self.fail_timeout,
            "ps": self.ps,
            "created_at": self.created_at,
            "node_site_id": self.node_site_id,
            "id": self.id,
            "load_id": self.load_id
        }


@dataclass
class TcpNode:
    node_id: int
    host: str
    port: int
    id: int = 0
    load_id: int = 0
    node_status: str = "online"  # online, backup, down
    weight: int = 1
    max_fail: int = 3
    fail_timeout: int = 600
    ps: str = ""
    created_at: int = 0

    @classmethod
    def bind(cls, data: dict) -> Tuple[Optional["TcpNode"], str]:
        if not isinstance(data.get('node_status', None), str):
            return None, 'node_status is required'
        if not data['node_status'] in ('online', 'backup', 'down'):
            return None, 'node_status is invalid'
        if not isinstance(data.get('host', None), str):
            return None, 'host is required'
        if not isinstance(data.get('node_id', None), int):
            return None, 'node_id is required'
        if not isinstance(data.get('port', None), int):
            return None, 'port is required'
        if not 1 <= data['port'] <= 65535:
            return None, 'port is invalid'
        n = TcpNode(data.get('node_id'), data.get('host'), data.get('port'), data.get('id', 0), data.get('load_id', 0),
                    data.get('node_status', "online"), data.get('weight', 1), data.get('max_fail', 3),
                    data.get('fail_timeout', 600), data.get('ps', ''), data.get('created_at', 0))
        return n, ""

    def to_dict(self) -> dict:
        return {
            "node_id": self.node_id,
            "host": self.host,
            "port": self.port,
            "id": self.id,
            "load_id": self.load_id,
            "node_status": self.node_status,
            "weight": self.weight,
            "max_fail": self.max_fail,
            "fail_timeout": self.fail_timeout,
            "ps": self.ps,
            "created_at": self.created_at
        }


class NodeDB:
    _DB_FILE = public.get_panel_path() + "/data/db/node_load_balance.db"
    _DB_INIT_FILE = os.path.dirname(__file__) + "/load_balancer.sql"

    def __init__(self):
        sql = db.Sql()
        sql._Sql__DB_FILE = self._DB_FILE
        self.db = sql

    def init_db(self):
        sql_data = public.readFile(self._DB_INIT_FILE)
        if not os.path.exists(self._DB_FILE) or os.path.getsize(self._DB_FILE) == 0:
            public.writeFile(self._DB_FILE, "")
            import sqlite3
            conn = sqlite3.connect(self._DB_FILE)
            c = conn.cursor()
            c.executescript(sql_data)
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

    def update_load_key(self, load_id: int, load_data: dict) -> str:
        if not isinstance(load_id, int):
            return "load_id is required"
        if not isinstance(load_data, dict):
            return "load_data is required"
        err = self.db.table("load_sites").where("load_id = ?", load_id).update(load_data)
        if isinstance(err, str):
            return err
        return ""

    def name_exist(self, name: str) -> bool:
        return self.db.table("load_sites").where("name = ?", name).count() > 0

    def load_site_name_exist(self, name: str) -> bool:
        return self.db.table("load_sites").where("site_name = ?", name).count() > 0

    def load_id_exist(self, load_id: int) -> bool:
        return self.db.table("load_sites").where("load_id = ?", load_id).count() > 0

    def loads_count(self, site_type: str, query: str = "") -> int:
        if site_type == "http":
            if not query:
                return self.db.table("load_sites").where("site_type = ?", "http").count()
            return self.db.table("load_sites").where(
                "site_type = ? AND ps like ?", ("http", "%" + query + "%")).count()
        else:
            if not query:
                return self.db.table("load_sites").where("site_type = ?", "tcp").count()
            return self.db.table("load_sites").where(
                "site_type = ? AND ps like ?", ("tcp", "%" + query + "%")).count()

    def loads_list(self, site_type: str, offset: int, limit: int, query: str = ""):
        if site_type == "all":
            if query:
                return self.db.table("load_sites").where("ps like ?", "%" + query + "%").limit(limit, offset).select()
            return self.db.table("load_sites").limit(limit, offset).select()
        if site_type == "http":
            if not query:
                return self.db.table("load_sites").where("site_type = ?", "http").limit(limit, offset).select()
            return self.db.table("load_sites").where(
                "site_type = ? AND ps like ?", ("http", "%" + query + "%")).limit(limit, offset).select()
        else:
            if not query:
                return self.db.table("load_sites").where("site_type = ?", "tcp").limit(limit, offset).select()
            return self.db.table("load_sites").where(
                "site_type = ? AND ps like ?", ("tcp", "%" + query + "%")).limit(limit, offset).select()

    def create_load(self, site_type: str, load: LoadSite, nodes: List[Union[HttpNode, TcpNode]]) -> str:
        load_data = load.to_dict()
        load_data.pop('load_id')
        load_data.pop('created_at')
        load_data["http_config"] = json.dumps(load.http_config)
        load_data["tcp_config"] = json.dumps(load.tcp_config)
        try:
            err = self.db.table("load_sites").insert(load_data)
            if isinstance(err, str):
                return err
            load.load_id = err

            for node in nodes:
                node_data = node.to_dict()
                node_data.pop('id')
                node_data.pop('created_at')
                node_data['load_id'] = load.load_id
                if site_type == "http" and isinstance(node, HttpNode):
                    err = self.db.table("http_nodes").insert(node_data)
                else:
                    err = self.db.table("tcp_nodes").insert(node_data)
                if isinstance(err, str):
                    return err
        except Exception as e:
            return "数据库操作错误:" + str(e)

        return ""

    def update_load(self, site_type: str, load: LoadSite, nodes: List[Union[HttpNode, TcpNode]]) -> str:
        load_data = load.to_dict()
        if not load.load_id:
            return "load_id is required"
        load_data.pop('created_at')
        load_data.pop('load_id')
        load_data["http_config"] = json.dumps(load.http_config)
        load_data["tcp_config"] = json.dumps(load.tcp_config)

        try:
            err = self.db.table("load_sites").where("load_id = ?", load.load_id).update(load_data)
            if isinstance(err, str):
                return err
        except Exception as e:
            return "数据库操作错误:" + str(e)

        old_nodes, err = self.get_nodes(load.load_id, site_type)
        if err:
            return err
        old_nodes_map = {}
        for old_node in old_nodes:
            old_nodes_map[old_node['id']] = old_node

        try:
            for node in nodes:
                node_data = node.to_dict()
                node_data.pop('id')
                node_data.pop('created_at')
                node_data['load_id'] = load.load_id
                if node.id in old_nodes_map:
                    if site_type == "http" and isinstance(node, HttpNode):
                        err = self.db.table("http_nodes").where("id = ?", node.id).update(node_data)
                    else:
                        err = self.db.table("tcp_nodes").where("id = ?", node.id).update(node_data)
                    if isinstance(err, str):
                        return err
                    old_nodes_map.pop(node.id)
                else:
                    if site_type == "http" and isinstance(node, HttpNode):
                        err = self.db.table("http_nodes").insert(node_data)
                    else:
                        err = self.db.table("tcp_nodes").insert(node_data)
                    if isinstance(err, str):
                        return err
            for node_id in old_nodes_map:
                if site_type == "http":
                    err = self.db.table("http_nodes").where("id = ?", node_id).delete()
                else:
                    err = self.db.table("tcp_nodes").where("id = ?", node_id).delete()
                if isinstance(err, str):
                    return err
        except Exception as e:
            return "数据库操作错误:" + str(e)
        return ""

    def get_nodes(self, load_id: int, site_type: str) -> Tuple[List[dict], str]:
        if site_type == "http":
            nodes: List[dict] = self.db.table("http_nodes").where("load_id = ?", load_id).select()
        else:
            nodes: List[dict] = self.db.table("tcp_nodes").where("load_id = ?", load_id).select()
        if isinstance(nodes, str):
            return [], nodes
        if not nodes and self.db.ERR_INFO:
            return [], self.db.ERR_INFO
        return nodes, ""

    def get_load(self, load_id: int) -> Tuple[Optional[dict], str]:
        load_data = self.db.table("load_sites").where("load_id = ?", load_id).find()
        if isinstance(load_data, str):
            return None, load_data
        if self.db.ERR_INFO:
            return None, self.db.ERR_INFO
        if len(load_data) == 0:
            return None, "未查询到该负载配置"
        return load_data, ""

    def delete(self, load_id: int) -> str:
        load_data = self.db.table("load_sites").where("load_id = ?", load_id).find()
        if isinstance(load_data, str):
            return load_data
        if self.db.ERR_INFO:
            return self.db.ERR_INFO
        if len(load_data) == 0:
            return ""

        if load_data["site_type"] == "http":
            err = self.db.table("http_nodes").where("load_id = ?", load_id).delete()
        else:
            err = self.db.table("tcp_nodes").where("load_id = ?", load_id).delete()
        if isinstance(err, str):
            return err
        err = self.db.table("load_sites").where("load_id = ?", load_id).delete()
        if isinstance(err, str):
            return err
        return ""
