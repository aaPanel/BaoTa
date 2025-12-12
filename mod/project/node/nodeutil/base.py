import hashlib
import html
import io
import ipaddress
import json
import os
import re
import shutil
import sys
import threading
import time
import socket
import platform
from uuid import uuid4

import math
import requests
import simple_websocket
import websocket
from werkzeug.datastructures import FileStorage
from datetime import datetime

if "/www/server/panel/class" not in sys.path:
    sys.path.insert(0, "/www/server/panel/class")

import public
from typing import Optional, Tuple, List, Callable, Union, Any, Dict
from .one_panel_api import OnePanelApiClient
from mod.project.node.dbutil import Node, NodeAPPKey

try:
    from BTPanel import cache
except:
    class _Cache:
        def __init__(self):
            self._data = {}

        def get(self, key):
            return self._data.get(key, None)

        def set(self, key, value, timeout):
            self._data[key] = value


    cache = _Cache()


def _get_os_info() -> Tuple[str, str]:
    os_data = public.readFile("/etc/os-release")
    if not os_data:
        return "", ""

    version = ["", ""]
    for line in os_data.split("\n"):
        if line.startswith("NAME="):
            name = line.split("=")[1].replace('"', "").strip()
            name_arr = name.split(" ")
            if len(name_arr) > 1:
                name = name_arr[0]
            version[0] = name
        elif line.startswith("VERSION="):
            ver = line.split("=")[1].replace('"', "").strip()
            ver_arr = ver.split(" ")
            if len(ver_arr) > 1:
                ver = ver_arr[0]
            version[1] = ver

    version = " ".join(version)
    return version, platform.machine()


class ServerNode:
    is_local = False

    def __init__(self, origin: str, api_key: str, app_key: str, remarks: str = "", timeout: int = 20):
        self.origin = origin
        self.api_key = api_key
        self.app_key: Optional[NodeAPPKey] = Node.parse_app_key(app_key)
        self.remarks = remarks
        self.timeout = timeout

    @property
    def node_server_ip(self):
        from urllib.parse import urlparse
        host = urlparse(self.origin).hostname
        try:
            if isinstance(host, str) and ipaddress.ip_address(host):
                return host
        except:
            pass
        try:
            ip_address = socket.gethostbyname(host)
            return ip_address
        except socket.gaierror as e:
            print(f"Error: {e}")
            return host

    def app_bind(self) -> Optional[str]:
        if self.app_key is None:
            return "app秘钥解析失败，请重新确认秘钥信息"
        version, arch = _get_os_info()
        public.print_log(self.app_key.app_token)
        pdata = {
            "bind_token": self.app_key.app_token,
            "client_brand": "BT-Panel",
            "client_model": "Linux" if not version else "Linux {} {}".format(version, arch)
        }
        header = {
            'Content-Type': 'application/x-www-form-urlencoded',
            "User-Agent": "Bt-Panel/Node Manager"
        }
        bind_url = self.app_key.origin + "/check_bind"
        try:
            res = requests.post(bind_url, data=pdata, headers=header, verify=False, timeout=self.timeout)
            if res.status_code != 200:
                return "绑定请求失败，返回状态码：%s,响应信息为：%s" % (res.status_code, res.text)
            res_str = res.text.strip()
            if res_str == "0":
                return "绑定失败，请检查您的密钥是否正确"
            elif res_str == "1":
                return None
            else:
                return "绑定失败，错误信息为：{}".format(json.loads(res_str))
        except Exception as e:
            return "网络连接失败，无法请求到目标服务器"

    def app_bind_status(self) -> Optional[str]:
        if self.app_key is None:
            return "app秘钥解析失败，请重新确认秘钥信息"
        pdata = {"bind_token": self.app_key.app_token}
        header = {
            'Content-Type': 'application/x-www-form-urlencoded',
            "User-Agent": "Bt-Panel/Node Manager"
        }
        bind_url = self.app_key.origin + "/get_app_bind_status"
        try:
            resp = requests.post(bind_url, data=pdata, headers=header, verify=False, timeout=self.timeout)
            if not resp.status_code == 200:
                return "获取绑定状态响应状态码错误，请检查节点地址和api是否正确，目前状态码为{},返回信息为:{}".format(
                    resp.status_code, resp.text)
            res_str = resp.text.strip()
            if res_str == "0":
                return "您的设备未绑定，请尝试重新绑定"
            elif res_str == "1":
                return None
            else:
                return "请求绑定状态失败，错误信息为：{}".format(json.loads(res_str))
        except Exception as e:
            return "获取绑定状态失败，请检查节点app秘钥是否正确，错误信息为:{}".format(str(e))

    @classmethod
    def new_by_id(cls, node_id: int) -> Optional[Union['ServerNode', 'LocalNode', 'LPanelNode']]:
        data = public.M("node").where("id = ?", (node_id,)).find()
        if not data or not isinstance(data, dict):
            return None
        return cls.new_by_data(data)

    @classmethod
    def new_by_data(cls, node_data: dict):
        if node_data["api_key"] == "local" and node_data["app_key"] == "local":
            return LocalNode()

        if node_data['lpver']:
            lp = LPanelNode(
                address=node_data['address'],
                api_key=node_data['api_key'],
                lpver=node_data['lpver'],
                timeout=node_data.get('timeout', 20)
            )
            lp.remarks = node_data['remarks']
            return lp
        if not node_data["api_key"] and not node_data["app_key"]:
            return None

        return cls(
            origin=node_data['address'],
            api_key=node_data['api_key'],
            app_key=node_data['app_key'],
            remarks=node_data['remarks'],
            timeout=node_data.get('timeout', 20)
        )

    def show_name(self) -> str:
        if self.remarks:
            return "{}({})".format(self.remarks, self.origin)
        return self.origin

    @staticmethod
    def _get_node_ip(node_id: int) -> str:
        data = public.M("node").where("id = ?", (node_id,)).find()
        if not data or not isinstance(data, dict):
            return ""
        if data['address'].startswith("http"):
            from urllib.parse import urlparse
            host = urlparse(data['address']).hostname
        else:
            host = data['address']
        try:
            if isinstance(host, str) and ipaddress.ip_address(host):
                return host
        except:
            pass
        try:
            ip_address = socket.gethostbyname(host)
            return ip_address
        except socket.gaierror as e:
            print(f"Error: {e}")
            return ""

    @classmethod
    def get_node_ip(cls, node_id: int) -> Optional[str]:
        if public.M('node').where("id=? AND app_key = 'local' AND api_key = 'local'", (node_id,)).count() > 0:
            return "127.0.0.1"
        cache_key = "mod_node_server_ip_{}".format(node_id)
        c_ip = cache.get(cache_key)
        if c_ip:
            return c_ip
        else:
            ip = cls._get_node_ip(node_id)
            if ip:
                cache.set(cache_key, ip, 86400)
                return ip
            return None

    @classmethod
    def check_api_key(cls, node: Node) -> str:
        if not LPanelNode.check_api_key(node):  # 如果1panel检查可以连接上，则标记为1panel并直接返回
            return ""

        node = cls(node.address, node.api_key, node.app_key)
        data, err = node._request("/system", "GetSystemTotal")
        if err:
            return err
        if isinstance(data, dict) and "version" in data:
            return ""
        return "验证错误：%s" % str(data)

    def test_conn(self) -> str:
        data, err = self._request("/system", "GetSystemTotal")
        if err:
            return err
        if isinstance(data, dict) and "version" in data:
            return ""
        return "验证错误：%s" % str(data)

    def version(self) -> Optional[str]:
        data, err = self._request("/system", "GetSystemTotal")
        if err:
            return None
        if isinstance(data, dict) and "version" in data:
            return data["version"]
        return None

    def get_net_work(self) -> Tuple[Optional[dict], str]:
        data, err = self._request("/system", "GetNetWork")
        if err:
            return None, err
        if isinstance(data, dict) and "cpu" in data and "mem" in data:
            return data, ""
        return None, "数据格式错误: %s" % str(data)

    def get_tmp_token(self) -> Tuple[str, str]:
        data, err = self._request("/config", "get_tmp_token")
        if err:
            return "", err
        if isinstance(data, dict) and "status" in data:
            if data["status"] and "msg" in data:
                return data["msg"], ""
            return "", data.get("msg", str(data))
        return "", "数据格式错误: %s" % str(data)

    def get_bt_params(self, other_data: dict = None) -> Dict:
        now = int(time.time() * 1000)
        other_data = other_data or {}
        if self.app_key:
            md5_panel_key = hashlib.md5(self.app_key.request_token.encode()).hexdigest()
            request_token = hashlib.md5("{}{}".format(now, md5_panel_key).encode()).hexdigest()
            other_data["request_token"] = request_token
            other_data["request_time"] = str(now)
            form_data = json.dumps(other_data)
            return {
                "client_bind_token": self.app_key.app_token,
                "form_data": public.aes_encrypt(form_data, self.app_key.app_key)
            }
        else:
            md5_panel_key = hashlib.md5(self.api_key.encode()).hexdigest()
            request_token = hashlib.md5("{}{}".format(now, md5_panel_key).encode()).hexdigest()
            other_data["request_token"] = request_token
            other_data["request_time"] = str(now)
            return other_data

    def _request(self, path: str, action: str, pdata: dict = None) -> Tuple[Optional[any], str]:
        url = "{}{}".format(self.origin, path)
        pdata = pdata or {}
        bt_p = self.get_bt_params({"action": action, **pdata})
        header = {
            'Content-Type': 'application/x-www-form-urlencoded',
            "User-Agent": "Bt-Panel/Node Manager"
        }
        try:
            resp = requests.post(url, data=bt_p, headers=header, verify=False, timeout=self.timeout)
            if not resp.status_code == 200:
                return None, "响应状态码错误，请检查节点地址和api是否正确，目前响应状态码为{}".format(
                    resp.status_code)
            if self.app_key:
                real_data = public.aes_decrypt(resp.text, self.app_key.app_key)
                return json.loads(real_data), ""
            return resp.json(), ""
        except Exception as e:
            # public.print_error()
            # return None, "请求节点失败，请检查节点地址和api是否正确，错误信息为:{}".format(str(e))
            if self.remarks:
                return None, "请求节点【{}】失败，请检查节点地址和api是否正确".format(self.remarks)
            return None, "请求节点失败，请检查节点地址和api是否正确"

    def get_file_body(self, path: str) -> Tuple[Optional[str], str]:
        data, err = self._request("/files", "GetFileBody", pdata={"path": path})
        if err:
            return None, err
        if not isinstance(data, dict):
            if isinstance(data, dict) and "msg" in data:
                return None, data["msg"]
            return None, "数据格式错误"
        return data["data"], ""

    def php_site_list(self) -> Tuple[Optional[List[dict]], str]:
        data, err = self._request("/mod/node/node/php_site_list", "", pdata={
            "type": -1,
            "p": 1,
            "limit": 1000,
            "table": "sites",
            "search": "",
        })
        if err:
            return None, err

        if not isinstance(data, list):
            if isinstance(data, dict) and "msg" in data:
                return None, data["msg"]
            return None, "数据格式错误"

        return data, ""

    def create_php_site(self, site_name: str, port: int, **kwargs) -> Tuple[Optional[int], str]:
        path = "/www/wwwroot/{}".format(site_name)
        if port not in (80, 443):
            path = "/www/wwwroot/{}_{}".format(site_name, port)
        webname = {
            "domain": site_name if port in (80, 443) else "{}:{}".format(site_name, port),
            "domainlist": [],
            "count": 0
        }
        data, err = self._request("/site", "AddSite", pdata={
            "path": path,
            "ftp": "false",
            "type": "PHP",
            "type_id": "0",
            "ps": "{}【负载均衡节点】".format(site_name),
            "port": str(port),
            "version": "00",
            "sql": "false",
            "webname": json.dumps(webname)
        })

        if err:
            return None, err
        if not isinstance(data, dict):
            return None, "数据格式错误"

        if isinstance(data, dict) and "msg" in data and not data.get("status", True):
            return None, data["msg"]

        site_id = data.get("siteId", None)
        if not isinstance(site_id, int):
            return None, "数据解析错误"
        return site_id, ""

    def set_firewall_open(self, port: int, protocol: str = "tcp") -> Tuple[bool, str]:
        data, err = self._request("/firewall/com/set_port_rule", "", pdata={
            "protocol": "udp" if protocol == "udp" else "tcp",
            "port": str(port),
            "choose": "all",
            "types": "accept",
            "chain": "INPUT",
            "operation": "add",
            "strategy": "accept",
        })
        if err:
            return False, err

        if isinstance(data, dict) and "msg" in data:
            msg = data["msg"]
            if "端口{}已存在".format(port) in msg:
                return True, ""
            elif "设置成功" in msg:
                return True, ""
        return False, "设置失败"

    def add_domain(self, site_id: int, site_name: str, domain: str, port: int) -> Tuple[bool, str]:
        data, err = self._request("/site", "AddDomain", pdata={
            "domain": "{}:{}".format(domain, port),
            "webname": site_name,
            "id": str(site_id)
        })
        if err:
            return False, err

        if isinstance(data, dict) and "domains" in data:
            for d in data["domains"]:
                if d["name"] == domain:
                    if "绑定过了" in d["msg"]:
                        return True, ""
                    elif "添加成功" in d["msg"]:
                        return True, ""
        return False, "添加失败,目标机返回信息为:{}".format(
            data.get("msg", str(data)) if isinstance(data, dict) else str(data))

    def has_domain(self, site_id: int, domain: str) -> bool:
        data, err = self._request("/data", "getData", pdata={
            "table": "domain",
            "list": "True",
            "search": str(site_id)
        })
        if err:
            return False
        if not isinstance(data, list):
            return False
        for d in data:
            if d["name"] == domain:
                return True
        return False

    # mode -> cover: 覆盖，ignore: 跳过，rename:重命名
    def upload_file(self, filename: str, target_path: str, mode: str = "cover",
                    call_log: Callable[[int, str], None] = None) -> str:
        if not os.path.isfile(filename):
            return "文件:{}不存在".format(filename)

        target_file = os.path.join(target_path, os.path.basename(filename))
        exits, err = self.target_file_exits(target_file)
        if err:
            return err
        if exits and mode == "ignore":
            call_log(0, "文件上传:{} -> {},目标文件已存在,跳过上传".format(filename, target_file))
            return ""
        if exits and mode == "rename":
            upload_name = "{}_{}".format(os.path.basename(filename), public.md5(filename))
            call_log(0, "文件上传:{} -> {},目标文件已存在,将重命名为{}".format(filename, target_file, upload_name))
        else:
            upload_name = os.path.basename(filename)

        if os.path.getsize(filename) > 1024 * 1024 * 5:
            return self._upload_big_file(filename, target_path, upload_name, call_log)
        else:
            return self._upload_little_file(filename, target_path, upload_name, call_log)

    def target_file_exits(self, target_file: str) -> Tuple[bool, str]:
        data, err = self._request("/files", "upload_files_exists", pdata={
            "files": target_file,
        })
        if err:
            return False, err
        if not isinstance(data, list):
            return False, "数据格式错误: %s" % str(data)
        for f in data:
            if f["filename"] == target_file and f["exists"]:
                return True, ""
        return False, ""

    def upload_check(self, target_file_list: List[str]) -> Tuple[List[dict], str]:
        data, err = self._request("/files", "upload_files_exists", pdata={
            "files": "\n".join(target_file_list),
        })
        if err:
            return [], err
        if not isinstance(data, list):
            if isinstance(data, dict):
                return [], data.get("msg", "数据格式错误")
            return [], "数据格式错误: %s" % str(data)
        return data, ""

    def _upload_big_file(self, filename: str, target_path: str, upload_name: str,
                         call_log: Callable[[int, str], None] = None) -> str:
        url = "{}/files".format(self.origin)
        bt_p = self.get_bt_params({"action": "upload"})
        header = {"User-Agent": "Bt-Panel/Node Manager"}
        try:
            fb = open(filename, 'rb')
        except Exception as e:
            public.print_error()
            return "文件{}打开失败，请检查文件权限，错误信息为:{}".format(filename, str(e))

        file_size = os.path.getsize(filename)
        for i in range(0, file_size, 1024 * 1024 * 5):
            file_data = fb.read(1024 * 1024 * 5)
            files = {'blob': ('blob', file_data, 'application/octet-stream')}
            data = {
                'f_path': target_path,
                'f_name': upload_name,
                'f_size': file_size,
                'f_start': i,
            }
            data.update(bt_p)
            try:
                resp = requests.post(url, data=data, files=files, headers=header, verify=False, timeout=self.timeout)
                if not resp.status_code == 200:
                    return "上传文件响应状态码错误，请检查节点地址和api是否正确，目前状态码为{},返回信息为:{}".format(
                        resp.status_code, resp.text)
                resp_text = resp.text
                resp_json = {}
                if self.app_key:
                    resp_text = public.aes_decrypt(resp_text, self.app_key.app_key).strip()
                    if not resp_text.isdecimal():
                        resp_json = json.loads(resp_text)
                else:
                    resp_json = resp.json()

                if resp_text.isdecimal():
                    up_p = int(resp_text)
                    if up_p != i + len(file_data):
                        return "上传文件失败，文件块大小不一致"
                    else:
                        call_log(up_p * 100 // file_size, "文件上传:{} -> {},已上传大小为:{}".format(
                            filename, upload_name, public.to_size(up_p)))
                elif "status" in resp_json:
                    if not resp_json["status"]:
                        return "上传文件失败，错误信息为:{}".format(resp_json["msg"])
                    else:
                        call_log(100, "文件上传:{} -> {},上传成功".format(filename, upload_name))
                        return ""
                else:
                    return "上传文件失败，响应信息为:{}".format(resp_text)
            except Exception as e:
                public.print_error()
                return "上传文件文件：{}失败，错误信息为:{}".format(filename, str(e))
        return ""

    def _upload_little_file(self, filename: str, target_path: str, upload_name: str,
                            call_log: Callable[[int, str], None] = None) -> str:
        url = "{}/files".format(self.origin)
        bt_p = self.get_bt_params({"action": "upload"})
        header = {"User-Agent": "Bt-Panel/Node Manager"}
        try:
            with open(filename, 'rb') as f:
                file_data = f.read()
        except Exception as e:
            public.print_error()
            return "文件{}打开失败，请检查文件权限，错误信息为:{}".format(filename, str(e))

        file_size = os.path.getsize(filename)
        files = {'blob': ('blob', file_data, 'application/octet-stream')}
        data = {
            'f_path': target_path,
            'f_name': upload_name,
            'f_size': file_size,
            'f_start': 0
        }
        data.update(bt_p)
        try:
            resp = requests.post(url, data=data, files=files, headers=header, verify=False, timeout=self.timeout)
            if not resp.status_code == 200:
                return "上传文件响应状态码错误，请检查节点地址和api是否正确，目前状态码为{},返回信息为:{}".format(
                    resp.status_code, resp.text)
            resp_json = {}
            if self.app_key:
                resp_text = public.aes_decrypt(resp.text, self.app_key.app_key).strip()
                if not resp_text.isdecimal():
                    resp_json = json.loads(resp_text)
            else:
                resp_json = resp.json()
            if not resp_json["status"]:
                return "上传文件失败，错误信息为:{}".format(resp.json()["msg"])
            return ""
        except Exception as e:
            public.print_error()
            return "上传文件文件：{}失败，错误信息为:{}".format(filename, str(e))

    def upload_proxy(self):
        try:
            from BTPanel import request
            f_name = request.form.get('f_name')
            f_path = request.form.get('f_path')
            f_size = request.form.get('f_size')
            f_start = request.form.get('f_start')
            blob_file: FileStorage = request.files.getlist('blob')[0]
            url = "{}/files".format(self.origin)
            bt_p = self.get_bt_params({"action": "upload"})
            header = {"User-Agent": "Bt-Panel/Node Manager"}
            files = {'blob': ('blob', blob_file.stream, 'application/octet-stream')}
            data = {
                'f_path': f_path,
                'f_name': f_name,
                'f_size': f_size,
                'f_start': f_start
            }
            data.update(bt_p)
            resp = requests.post(url, data=data, files=files, headers=header, verify=False, timeout=self.timeout)
            if not resp.status_code == 200:
                return "上传文件响应状态码错误，请检查节点地址和api是否正确，目前状态码为{},返回信息为:{}".format(
                    resp.status_code, resp.text)
            resp_text = resp.text
            resp_json = {}
            if self.app_key:
                resp_text = public.aes_decrypt(resp_text, self.app_key.app_key).strip()
                if not resp_text.isdecimal():
                    resp_json = json.loads(resp_text)
            else:
                resp_json = resp.json()
            if resp_text.isdecimal():
                return int(resp_text)
            elif "status" in resp_json:
                return resp_json
            else:
                return {"status": False, "msg": "上传文件失败，响应信息为:{}".format(resp_text)}
        except Exception as e:
            public.print_error()
            return {"status": False, "msg": "上传文件失败，错误信息为:{}".format(str(e))}

    def remove_file(self, filename: str, is_dir: bool) -> dict:
        action = "DeleteDir" if is_dir else "DeleteFile"
        data, err = self._request("/files", action, pdata={
            "path": filename,
        })
        if err:
            return {"status": False, "msg": "删除文件失败，错误信息为:{}".format(err)}

        if isinstance(data, dict):
            return data
        return {"status": False, "msg": "删除文件失败，响应信息为:{}".format(data)}

    def create_dir(self, path: str) -> Tuple[Optional[Dict], str]:
        data, err = self._request("/files", action="CreateDir", pdata={
            "path": path,
        })
        if err:
            return None, "创建目录失败，错误信息为:{}".format(err)
        if isinstance(data, dict):
            return data, ""
        return None, "创建目录失败，响应信息为:{}".format(data)

    def dir_walk(self, path: str) -> Tuple[List[dict], str]:
        data, err = self._request("/mod/node/file_transfer/dir_walk", "", pdata={
            "path": path,
        })
        if err:
            return [], err

        if not isinstance(data, list):
            if isinstance(data, dict) and "msg" in data:
                return [], data["msg"]
            return [], "数据格式错误: %s" + str(data)

        return data, ""

    def filetransfer_version_check(self) -> str:
        ver = self.version()
        if not ver:
            return "节点{}连接错误".format(self.show_name())

        try:
            ver_list = [int(i) for i in ver.split(".")]
            if self.app_key:  # todo: 版本号检测
                if ver_list[0] > 11 or (ver_list[0] == 11 and ver_list[1] >= 1):
                    return "节点{}版本低于【11.1.0】，无法使用app链接，请升级节点版本".format(self.show_name())

            if ver_list[0] > 10 or (ver_list[0] == 10 and ver_list[2] >= 1):
                return ""
            elif ver_list[0] == 9 and ver_list[1] >= 7:
                return ""
            return "请将面板版本升级到【10.0.1】及以上再使用"
        except:
            pass
        return "请将面板版本升级到【10.0.1】及以上再使用"


    def node_create_filetransfer_task(self, source_node: dict,
                                      target_node: dict,
                                      source_path_list: List[dict],
                                      target_path: str,
                                      created_by: str,
                                      default_mode: str = "cover") -> dict:
        data, err = self._request("/mod/node/file_transfer/node_create_filetransfer_task", "", pdata={
            "source_node": json.dumps(source_node),
            "target_node": json.dumps(target_node),
            "source_path_list": json.dumps(source_path_list),
            "target_path": target_path,
            "created_by": created_by,
            "default_mode": default_mode,
        })
        if err:
            return {"status": False, "msg": "创建文件传输任务失败，错误信息为:{}".format(err)}
        if isinstance(data, dict):
            return data
        else:
            return {"status": False, "msg": "创建文件传输任务失败，响应信息为:{}".format(data)}

    def file_list(self, path: str, p: int, row: int, search: str) -> Tuple[Dict, str]:
        data, err = self._request("/files", "GetDirNew", pdata={
            "path": path,
            "p": p,
            "showRow": row,
            "search": search,
        })
        if err:
            return {}, err
        if not isinstance(data, dict):
            return {}, "数据格式错误: %s" + str(data)
        return data, ""

    def get_transfer_status(self, task_id: int) -> dict:
        data, err = self._request("/mod/node/file_transfer/get_transfer_status", "", pdata={
            "task_id": task_id,
        })
        if err:
            return {"status": False, "msg": "获取文件传输任务状态失败，错误信息为:{}".format(err)}
        if isinstance(data, dict):
            return data
        return {"status": False, "msg": "获取文件传输任务状态失败，响应信息为:{}".format(data)}

    def proxy_transfer_status(self, task_id: int, ws: simple_websocket.Server):
        err = self._proxy_websocket(
            call_data={
                "mod_name": "node",
                "sub_mod_name": "file_transfer",
                "def_name": "node_proxy_transfer_status",
                "callback": "node_proxy_transfer_status",
                "data": {
                    "task_id": task_id,
                }
            },
            uri="ws_modsoc",
            call_back=ws.send
        )
        if err:
            ws.send(json.dumps({
                "type": "error",
                "msg": "获取文件传输任务状态失败，错误信息为:{}".format(err)
            }))

    def _proxy_websocket(self, call_data: dict, uri: str, call_back: Callable[[Any],None]) -> str:
        from urllib.parse import urlencode, urlparse
        from ssl import CERT_NONE
        try:
            bt_p = self.get_bt_params()
            header = {"User-Agent": "Bt-Panel/Node Manager"}
            u = urlparse(self.origin)
            url = (
                "{}://{}/{}?{}".format(
                    "ws" if u.scheme == "http" else "wss",
                    u.netloc, uri, urlencode(bt_p)
                )
            )
            ws_req = websocket.WebSocket(sslopt={"cert_reqs": CERT_NONE}) # 忽略证书
            ws_req.connect(url, header=header)
            ws_req.send("{}") # 跳过x-http-tokn 验证
            ws_req.send(json.dumps(call_data))  # 发送调用数据

            while True:
                data = ws_req.recv()
                if data == "{}":
                    break
                if data:
                    call_back(data)
                else:
                    break
            ws_req.close()
            return ""
        except Exception as e:
            return str(e)

    def proxy_transferfile_status(self, task_id: int, call_back: Callable[[Any],None]) -> str:
        return self._proxy_websocket(
            call_data={
                "mod_name": "node",
                "sub_mod_name": "executor",
                "def_name": "node_proxy_transferfile_status",
                "callback": "node_proxy_transferfile_status",
                "data": {
                    "task_id": task_id,
                }
            },
            uri="ws_modsoc",
            call_back=call_back
        )

    def node_create_transfer_task(self, transfer_task_data:dict) -> dict:
        data, err = self._request(
            "/mod/node/executor/node_create_transfer_task", "", pdata={
                "transfer_task_data": json.dumps(transfer_task_data),
            }
        )
        if err:
            return {"status": False, "msg": "创建文件传输任务失败，错误信息为:{}".format(err)}
        if isinstance(data, dict):
            return data
        else:
            return {"status": False, "msg": "创建文件传输任务失败，响应信息为:{}".format(data)}

    def node_transferfile_status_history(self, transfer_task_id: int, only_error=True):
        data, err = self._request(
            "/mod/node/executor/node_transferfile_status_history", "", pdata={
                "task_id": transfer_task_id,
                "only_error": 1 if only_error else 0
            }
        )
        if err:
            return {"status": False, "msg": "创建文件传输任务失败，错误信息为:{}".format(err)}
        if isinstance(data, dict):
            return data
        else:
            return {"status": False, "msg": "创建文件传输任务失败，响应信息为:{}".format(data)}

    def download_proxy(self, filename: str):
        url = "{}/download".format(self.origin)
        bt_p = self.get_bt_params()
        header = {"User-Agent": "Bt-Panel/Node Manager"}
        try:
            resp = requests.get(url, params={"filename": filename}, data=bt_p, headers=header, stream=True, verify=False, timeout=self.timeout)
            if not resp.status_code == 200:
                return "下载文件响应状态码错误，请检查节点地址和api是否正确，目前状态码为{},返回信息为:{}".format(
                    resp.status_code, resp.text)

            from flask import send_file, stream_with_context, Response
            filename = os.path.basename(filename)
            if resp.headers.get("Content-Disposition", "").find("filename=") != -1:
                filename = resp.headers.get("Content-Disposition", "").split("filename=")[1]

            def generate():
                for chunk in resp.iter_content(chunk_size=1024 * 1024 * 5):
                    if chunk:
                        yield chunk

            # 设置响应头
            headers = {
                'Content-Type': resp.headers.get('Content-Type', 'application/octet-stream'),
                'Content-Disposition': 'attachment; filename="{}"'.format(filename),
                'Content-Length': resp.headers.get('Content-Length', ''),
                'Accept-Ranges': 'bytes'
            }

            # 使用 stream_with_context 确保请求上下文在生成器运行时保持活跃
            return Response(
                stream_with_context(generate()),
                headers=headers,
                direct_passthrough=True
            )
        except Exception as e:
            public.print_error()
            return "下载文件：{}失败，错误信息为:{}".format(filename, str(e))

    def download_file(self, filename: str, target_path: str, mode: str,
                      call_log: Callable[[int, str], None] = None) -> str:
        target_file = os.path.join(target_path, os.path.basename(filename))
        exits = os.path.exists(target_file)
        if exits and mode == "ignore":
            call_log(0, "文件下载:{} -> {},目标文件已存在,跳过下载".format(filename, target_file))
            return ""
        if exits and mode == "rename":
            download_name = "{}_{}".format(os.path.basename(filename), public.md5(filename))
            call_log(0, "文件下载:{} -> {},目标文件已存在,将重命名为{}".format(filename, target_file, download_name))
        else:
            download_name = os.path.basename(filename)

        return self._download_file(filename, target_path, download_name, call_log)

    def _download_file(self, filename: str, target_path: str, download_name: str,
                       call_log: Callable[[int, str], None] = None) -> str:
        data, err = self.upload_check([filename])
        if err:
            return "请求文件：{}的状态失败，错误信息为:{}".format(filename, err)
        file_size: Optional[int] = None
        for i in data:
            if i["filename"] == filename and i["isfile"] == True:
                file_size = i["size"]
                break

        if file_size is None:
            return "文件{}不存在, 跳过下载".format(filename)
        try:
            if not os.path.isdir(target_path):
                os.makedirs(target_path)
        except  Exception as e:
            return "创建文件夹{}失败，请检查文件夹权限，错误信息为:{}".format(target_path, str(e))

        if file_size == 0:
            fp = open(os.path.join(target_path, download_name), "w")
            fp.close()
            return ""

        tmp_file = os.path.join(target_path, "{}.{}".format(download_name, uuid4().hex))
        try:
            if not os.path.exists(target_path):
                os.makedirs(target_path)
            fb = open(tmp_file, 'wb')
        except  Exception as e:
            return "创建临时文件{}失败，请检查文件夹权限，错误信息为:{}".format(tmp_file, str(e))

        url = "{}/download".format(self.origin)
        bt_p = self.get_bt_params()
        header = {"User-Agent": "Bt-Panel/Node Manager"}
        try:
            resp = requests.get(url, params={"filename": filename}, data=bt_p, headers=header, stream=True, verify=False, timeout=self.timeout)
            if not resp.status_code == 200:
                return "下载文件响应状态码错误，请检查节点地址和api是否正确，目前状态码为{},返回信息为:{}".format(
                    resp.status_code, resp.text)

            now_size = 0
            for chunk in resp.iter_content(chunk_size=1024 * 1024 * 3):
                if chunk:
                    now_size += len(chunk)
                    fb.write(chunk)
                    fb.flush()
                    call_log(now_size * 100 // file_size,
                             "下载文件{}, 已下载: {}".format(filename, public.to_size(now_size)))
            if fb.tell() != file_size:
                return "下载文件{}失败，文件大小检查错误".format(filename)
            fb.close()
            shutil.move(tmp_file, os.path.join(target_path, download_name))
            return ""
        except Exception as e:
            return "下载文件{}失败，错误信息为:{}".format(filename, str(e))
        finally:
            if not fb.closed:
                fb.close()
            if os.path.exists(tmp_file):
                os.remove(tmp_file)

    def dir_size(self, path: str) -> Tuple[Optional[int], str]:
        data, err = self._request("/files", "get_path_size", pdata={
            "path": path,
        })
        if err:
            return None, err
        if isinstance(data, dict) and "size" in data:
            return data["size"], ""
        return None, "获取目录大小失败，响应信息为:{}".format(data)

    def get_sshd_port(self) -> Optional[int]:
        data, err = self._request("/safe/ssh/GetSshInfo", "", pdata={})
        if err:
            return None
        if isinstance(data, dict) and "port" in data:
            return int(data["port"])
        return None

    def restart_bt_panel(self) -> Dict[str, Any]:
        res, err = self._request("/system", "ReWeb", pdata={})
        if err:
            return {"status": False, "msg": err}
        return {"status": True, "msg": "重启成功"}

    def server_reboot(self):
        res, err = self._request("/system", "ServiceAdmin", pdata={
            "name": "nginx",
            "type": "stop",
        })
        if err:
            return {"status": False, "msg": err}
        if not res["status"]:
            return {"status": False, "msg": "nginx停止失败, 无法继续执行重启服务器：" + res["msg"]}

        res, err = self._request("/system", "ServiceAdmin", pdata={
            "name": "mysqld",
            "type": "stop",
        })
        if err:
            return {"status": False, "msg": err}
        if not res["status"]:
            return {"status": False, "msg": "mysql服务停止失败, 无法继续执行重启服务器：" + res["msg"]}

        res, _ = self._request("/system", "RestartServer", pdata={})
        if not res["status"]:
            return {"status": False, "msg": "重启服务器失败：" + res["msg"]}

        from mod.project.node.dbutil import ServerMonitorRepo
        repo = ServerMonitorRepo()
        repo.set_wait_reboot(self.node_server_ip, True)

        def wait_for_reboot():
            # wait 等待服务器重启成功， 超时时间默认为 10 分钟
            wait_for = time.time() + 600
            time.sleep(3)
            while time.time() < wait_for:
                if self.test_conn() == "":  # 无错误时表示重启成功
                    repo.set_wait_reboot(self.node_server_ip, False)
                    from mod.project.node.dbutil import ServerNodeDB
                    node_data = ServerNodeDB().find_node(api_key=self.api_key, app_key=self.app_key.to_string())
                    if node_data:
                        monitor_node_once(node_data)
                    return {"status": True, "msg": "重启服务器成功"}
                time.sleep(3)
                public.print_log("等待服务器重启中... {}".format(wait_for - time.time()))
            repo.set_wait_reboot(self.node_server_ip, False)
            return {"status": False, "msg": "重启服务器失败, 已超过10分钟未能检测到服务器信息"}

        t = threading.Thread(target=wait_for_reboot, daemon=True)
        t.start()

        return {"status": True, "msg": "重启服务器已开始，请赖心等待重启成功"}

    def read_ssh_key(self) -> Tuple[Optional[str], str]:
        data, err = self._request("/ssh_security", "get_key", pdata={})
        if err:
            return None, err
        if not isinstance(data, dict) or "status" not in data:
            return None, "获取SSH密钥失败，请检查节点地址和api是否正确"
        if not data["status"]:
            return None, data["msg"]
        return data["msg"], ""

    def get_dir(self, path: str, search: str, disk: str):
        data, err = self._request("/files", "GetDir", pdata={
            "path": path, "disk": disk, "search": search
        })
        if err:
            return {"status": False, "msg": err}
        if not isinstance(data, dict):
            return {"status": False, "msg": "获取目录失败，请检查节点地址和api是否正确"}
        return data

    def upload_dir_check(self, target_file: str) -> str:
        data, err = self._request("/files", "upload_files_exists", pdata={"files": target_file})
        if err:
            return err
        if not isinstance(data, list):
            return "数据格式错误: %s" % str(data)
        for f in data:
            if f["filename"] == target_file and f["exists"]:
                if f["isfile"]:
                    return "该名称路径不是目录"
                else:
                    return ""
        return ""


def monitor_all_node_status():
    all_nodes = public.M("node").select()
    if not isinstance(all_nodes, list) or not all_nodes:
        return

    import threading

    threads = []
    for tmp_node_data in all_nodes:
        t = threading.Thread(target=monitor_node_once, args=(tmp_node_data,))
        t.start()
        threads.append(t)

    # 等待所有线程完成（可选）
    for t in threads:
        t.join()


def monitor_node_once(node_data: dict):
    from mod.project.node.dbutil import Node, ServerNodeDB, ServerMonitorRepo
    from mod.project.node.nodeutil.ssh_wrap import SSHApi
    from mod.base.ssh_executor import test_ssh_config
    try:
        if node_data["app_key"] == "local" and node_data["api_key"] == "local":
            return
        node_data["error"] = json.loads(node_data["error"])
        node_data["ssh_conf"] = json.loads(node_data["ssh_conf"])
        node, err = Node.from_dict(node_data)
        if err:
            public.print_log("节点数据解析错误:{}".format(err))
            return

        if node_data["lpver"]:
            srv = LPanelNode(node.address, node.api_key, node.lpver)
        elif node.api_key or node.app_key:
            srv = ServerNode(node.address, node.api_key, node.app_key)
        else:
            srv =SSHApi(**node_data["ssh_conf"])

        data, err = srv.get_net_work()
        if err:
            node.error_num += 1
            node.error = {
                "msg": err,
                "time": int(time.time())
            }
            if node.error_num >= 2:
                node.status = 0
                ServerMonitorRepo().remove_cache(node.id)

            ServerNodeDB().update_node(node)

        else:
            if node.error_num > 0:
                node.error_num = 0
                node.error = {}
                node.status = 1
                ServerNodeDB().update_node(node)

        if data:
            repo = ServerMonitorRepo()
            repo.save_server_status(node.id, data)
            if repo.is_reboot_wait(node.server_ip):
                repo.set_wait_reboot(node.server_ip, False)
        if not node_data["ssh_test"] and not node_data["ssh_conf"] and not isinstance(srv, SSHApi):
            ssh_key, err = srv.read_ssh_key()
            if err:
                public.print_log("获取SSH密钥失败:{}".format(err))
                return
            port = srv.get_sshd_port()
            if not port:
                public.print_log("获取SSH服务端口失败")
                return

            conf = {
                "host": srv.node_server_ip,
                "pkey": ssh_key,
                "port": port,
                "username": "root",
                "password": "",
                "pkey_passwd": "",
            }
            err = test_ssh_config(**conf)
            if err:
                public.print_log("SSH密钥测试失败:{}".format(err))
                ServerNodeDB().set_node_ssh_conf(node.id, {}, ssh_test=1)
                return
            else:
                ServerNodeDB().set_node_ssh_conf(node.id, conf, ssh_test=1)

    except Exception as e:
        if public.is_debug():
            public.print_error()


def monitor_node_once_with_timeout(node_data: dict, timeout: int = 5):
    if node_data["app_key"] == "local" and node_data["api_key"] == "local":
        return
    from mod.project.node.dbutil import Node, ServerNodeDB, ServerMonitorRepo
    from mod.project.node.nodeutil.ssh_wrap import SSHApi
    try:
        node_data["error"] = json.loads(node_data["error"])
        node_data["ssh_conf"] = json.loads(node_data["ssh_conf"])
        node, err = Node.from_dict(node_data)
        if err:
            public.print_log("节点数据解析错误:{}".format(err))
            return

        if node_data["app_key"] or node_data["api_key"]:
            node_data["timeout"] = timeout
            srv = ServerNode.new_by_data(node_data)
            node_data.pop("timeout")
        elif node_data["ssh_conf"]:
            srv = SSHApi(**node_data["ssh_conf"], timeout=timeout)
        else:
            return

        data, err = srv.get_net_work()
        if err:
            node.error_num += 1
            node.error = {
                "msg": err,
                "time": int(time.time())
            }
            if node.error_num >= 2:
                node.status = 0
                ServerMonitorRepo().remove_cache(node.id)

            ServerNodeDB().update_node(node)

        elif node.error_num > 0:
            node.error_num = 0
            node.error = {}
            node.status = 1
            ServerNodeDB().update_node(node)

        if data:
            repo = ServerMonitorRepo()
            repo.save_server_status(node.id, data)
            if repo.is_reboot_wait(node.server_ip):
                repo.set_wait_reboot(node.server_ip, False)
    except Exception as e:
        if public.is_debug():
            public.print_error()


class LocalNode(ServerNode):
    is_local = True

    def __init__(self):
        super().__init__("", "", "")

    def create_php_site(self, site_name: str, port: int = 80, **kwargs) -> Tuple[Optional[int], str]:
        path = "/www/wwwroot/{}".format(site_name)
        webname = {
            "domain": site_name if port in (80, 443) else "{}:{}".format(site_name, port),
            "domainlist": [],
            "count": 0
        }
        pdata = {
            "path": path,
            "ftp": "false",
            "type": "PHP",
            "type_id": "0",
            "ps": kwargs.get("ps") if kwargs.get("ps", None) else "{}【负载均衡站点】".format(site_name),
            "port": str(port),
            "version": "00",
            "sql": "false",
            "webname": json.dumps(webname)
        }

        if "/www/server/panel/class" not in sys.path:
            sys.path.insert(0, "/www/server/panel/class")

        from panelSite import panelSite

        res = panelSite().AddSite(public.to_dict_obj(pdata))

        if "siteId" in res:
            return res["siteId"], ""
        if "status" in res and not res["status"]:
            return 0, res.get("msg", "未知错误")
        return 0, "未知错误"

    @staticmethod
    def site_proxy_list(site_name: str) -> List[dict]:
        from mod.base.web_conf.proxy import RealProxy
        data = RealProxy(config_prefix="").get_proxy_list(public.to_dict_obj({
            "sitename": site_name
        }))
        if isinstance(data, list) and data:
            return data

        from panelSite import panelSite

        data = panelSite().GetProxyList(public.to_dict_obj({
            "sitename": site_name
        }))
        if isinstance(data, list) and data:
            return data
        return []

    def show_name(self) -> str:
        return "本机节点"

    def php_site_list(self) -> Tuple[List[dict], str]:
        from mod.base.web_conf.ssl import RealSSLManger
        ssl_m = RealSSLManger()

        all_sites = public.M("sites").where("project_type=? and status = 1", "PHP").select()
        res = []
        for i in all_sites:
            domain = public.M("domain").where("pid=?", i["id"]).select()
            domains = list(set([x["name"] for x in domain]))
            port = list(set([int(x["port"]) for x in domain]))
            ssl = ssl_m.get_site_ssl_info(i["name"]) is not None
            if ssl and 443 not in port:
                port.append(443)
            res.append({
                "site_id": i["id"],
                "site_name": i["name"],
                "ports": port,
                "domains": domains,
                "ssl": ssl
            })

        return res, ""

    def add_domain(self, site_id: int, site_name: str, domain: str, port: int) -> Tuple[bool, str]:
        from panelSite import panelSite
        res = panelSite().AddDomain(public.to_dict_obj({
            "domain": "{}:{}".format(domain, port),
            "webname": site_name,
            "id": str(site_id)
        }))
        if isinstance(res, dict) and res.get("status", False):
            return True, ""
        return False, res.get("msg", "未知错误")

    def has_domain(self, site_id: int, domain: str):
        return public.M("domain").where("pid=? and name=?", site_id, domain).count() > 0

    def dir_walk(self, path: str) -> Tuple[List[dict], str]:
        if not os.path.isdir(path):
            return [], "{} 不是一个目录".format(path)
        res_file = []
        count = 0
        empty_dir = []
        for root, dirs, files in os.walk(path):
            if not files:
                empty_dir.append(root)
            for f in files:
                if count > 1000:
                    return [], "目录文件数量超过1000,请压缩后再操作"
                count += 1
                try:
                    res_file.append({
                        "path": os.path.join(root, f),
                        "size": os.path.getsize(os.path.join(root, f)),
                        "is_dir": 0
                    })
                except:
                    pass
        return [{"path": d, "size": 0, "is_dir": 1} for d in empty_dir] + res_file, ""

    def remove_file(self, filename: str, is_dir: bool) -> dict:
        from files import files
        if is_dir:
            return files().DeleteDir(public.to_dict_obj({"path": filename}))
        else:
            return files().DeleteFile(public.to_dict_obj({"path": filename}))

    def file_list(self, path: str, p: int, row: int, search: str) -> Tuple[Dict, str]:
        from files import files
        return files().GetDirNew(public.to_dict_obj({
            "path": path,
            "p": p,
            "showRow": row,
            "search": search
        })), ""

    def upload_proxy(self):
        from files import files
        return files().upload(args=public.to_dict_obj({}))

    def upload_check(self, target_file_list: List[str]) -> Tuple[List[dict], str]:
        from files import files
        return files().upload_files_exists(args=public.to_dict_obj({
            "files": "\n".join(target_file_list),
        })), ""

    def dir_size(self, path: str) -> Tuple[Optional[int], str]:
        return public.get_path_size(path), ""

    def get_sshd_port(self) -> Optional[int]:
        return public.get_sshd_port()

    def create_dir(self, path: str) -> Tuple[Optional[Dict], str]:
        from files import files
        return files().CreateDir(public.to_dict_obj({"path": path})), ""

    def get_file_body(self, path: str) -> Tuple[Optional[str], str]:
        res = public.readFile(path)
        if isinstance(res, str):
            return res, ""
        return None, "读取文件失败"

    def read_ssh_key(self) -> Tuple[Optional[str], str]:
        from ssh_security import ssh_security
        data = ssh_security().get_key(None)
        if data["status"]:
            return data["msg"], ""
        return None, data["msg"]

    def get_dir(self, path: str, search: str, disk: str):
        from files import files
        return files().GetDir(public.to_dict_obj({"path": path, "search":search, "disk": disk}))


class LPanelNode(ServerNode):
    _TIME_REGEXP = re.compile(r":\d{2}(?P<err>\.\d{6,})[+-]\d{2}:\d{2}")

    def __init__(self, address: str, api_key: str, lpver: str = "v2", timeout: int = 20):
        super().__init__(address, api_key, "",  timeout=timeout)
        self.ver = lpver
        self.lpc = OnePanelApiClient(address, api_key, lpver, self.timeout)

    @classmethod
    def check_api_key(cls, node: Node) -> str:
        public.print_log(node.address, node.api_key)
        lpc = OnePanelApiClient(node.address, node.api_key)
        if lpc.test_ver():
            node.lpver = lpc.ver
            return ""
        return "1Panel节点测试连接失败"

    def test_conn(self) -> str:
        if self.lpc.test_ver():
            return ""
        return "1Panel节点测试连接失败"

    def get_net_work(self) -> Tuple[Optional[dict], str]:
        """{
    "code": 200,
    "message": "",
    "data": {
        "path": "/",
        "name": "/",
        "user": "root",
        "group": "root",
        "uid": "0",
        "gid": "0",
        "extension": "",
        "content": "",
        "size": 4096,
        "isDir": true,
        "isSymlink": false,
        "isHidden": false,
        "linkPath": "",
        "type": "",
        "mode": "0555",
        "mimeType": "",
        "updateTime": "0001-01-01T00:00:00Z",
        "modTime": "2023-12-16T18:21:10.369198018+08:00",
        "items": [],
        "itemTotal": 22,
        "favoriteID": 0,
        "isDetail": true
    }
}
API Response Status: 200
{
    "code": 200,
    "message": "",
    "data": {
        "uptime": 8060394,
        "timeSinceUptime": "2025-03-05 10:02:04",
        "procs": 173,
        "load1": 1.05,
        "load5": 1.05,
        "load15": 1.05,
        "loadUsagePercent": 17.5,
        "cpuPercent": [
            100,
            0,
            0,
            0
        ],
        "cpuUsedPercent": 25.000000232830644,
        "cpuUsed": 1.0000000093132257,
        "cpuTotal": 4,
        "memoryTotal": 1038336000,
        "memoryAvailable": 298635264,
        "memoryUsed": 572526592,
        "memoryUsedPercent": 55.13885601577909,
        "swapMemoryTotal": 4160745472,
        "swapMemoryAvailable": 3816017920,
        "swapMemoryUsed": 344727552,
        "swapMemoryUsedPercent": 8.285235285836778,
        "ioReadBytes": 0,
        "ioWriteBytes": 0,
        "ioCount": 0,
        "ioReadTime": 0,
        "ioWriteTime": 0,
        "diskData": [
            {
                "path": "/",
                "type": "xfs",
                "device": "/dev/mapper/centos-root",
                "total": 37688381440,
                "free": 9805086720,
                "used": 27883294720,
                "usedPercent": 73.98379461954417,
                "inodesTotal": 18411520,
                "inodesUsed": 729745,
                "inodesFree": 17681775,
                "inodesUsedPercent": 3.963523924151836
            },
            {
                "path": "/www/monitor_data",
                "type": "ext4",
                "device": "/dev/vdb1",
                "total": 10432565248,
                "free": 8118497280,
                "used": 1760526336,
                "usedPercent": 17.82085360286682,
                "inodesTotal": 655360,
                "inodesUsed": 10029,
                "inodesFree": 645331,
                "inodesUsedPercent": 1.530303955078125
            }
        ],
        "netBytesSent": 0,
        "netBytesRecv": 0,
        "gpuData": null,
        "xpuData": null,
        "shotTime": "2025-06-06T17:01:59.156659566+08:00"
    }
}"""
        try:
            data = self.lpc.system_status()
            system_data = data.get("data", {})
            return {
                "cpu": [round(system_data["cpuUsedPercent"], 2), system_data["cpuTotal"]],
                "mem": {
                    "memRealUsed": system_data["memoryUsed"] / 1024 / 1024,
                    "memTotal": system_data["memoryTotal"] / 1024 / 1024,
                    "memNewTotal": public.to_size(system_data["memoryTotal"])
                },
                "version": "1Panel"
            }, ""

        except Exception as e:
            public.print_error()
            return None, str(e)

    def get_tmp_token(self) -> Tuple[Optional[str], str]:
        return None, "1Panel不支持api临时访问"

    def php_site_list(self) -> Tuple[List[dict], str]:
        """{
          "code": 200,
          "message": "",
          "data": [
            {
              "id": 2,
              "createdAt": "2025-06-06T14:49:00.687860227+08:00",
              "updatedAt": "2025-06-06T14:49:00.687860227+08:00",
              "protocol": "HTTP",
              "primaryDomain": "www.halotest.com",
              "type": "deployment",
              "alias": "www.halotest.com",
              "remark": "",
              "status": "Running",
              "httpConfig": "",
              "expireDate": "9999-12-31T00:00:00Z",
              "proxy": "127.0.0.1:8090",
              "proxyType": "",
              "errorLog": true,
              "accessLog": true,
              "defaultServer": false,
              "IPV6": false,
              "rewrite": "",
              "webSiteGroupId": 1,
              "webSiteSSLId": 0,
              "runtimeID": 0,
              "appInstallId": 5,
              "ftpId": 0,
              "parentWebsiteID": 0,
              "user": "",
              "group": "",
              "dbType": "",
              "dbID": 0,
              "favorite": false,
              "domains": [
                {
                  "id": 2,
                  "createdAt": "2025-06-06T14:49:00.69011631+08:00",
                  "updatedAt": "2025-06-06T14:49:00.69011631+08:00",
                  "websiteId": 2,
                  "domain": "www.halotest.com",
                  "ssl": false,
                  "port": 7080
                },
                {
                  "id": 3,
                  "createdAt": "2025-06-06T14:51:47.932141706+08:00",
                  "updatedAt": "2025-06-06T14:51:47.932141706+08:00",
                  "websiteId": 2,
                  "domain": "qwww.com",
                  "ssl": false,
                  "port": 7080
                }
              ],
              "webSiteSSL": {
                "id": 0,
                "createdAt": "0001-01-01T00:00:00Z",
                "updatedAt": "0001-01-01T00:00:00Z",
                "primaryDomain": "",
                "privateKey": "",
                "pem": "",
                "domains": "",
                "certURL": "",
                "type": "",
                "provider": "",
                "organization": "",
                "dnsAccountId": 0,
                "acmeAccountId": 0,
                "caId": 0,
                "autoRenew": false,
                "expireDate": "0001-01-01T00:00:00Z",
                "startDate": "0001-01-01T00:00:00Z",
                "status": "",
                "message": "",
                "keyType": "",
                "pushDir": false,
                "dir": "",
                "description": "",
                "skipDNS": false,
                "nameserver1": "",
                "nameserver2": "",
                "disableCNAME": false,
                "execShell": false,
                "shell": "",
                "acmeAccount": {
                  "id": 0,
                  "createdAt": "0001-01-01T00:00:00Z",
                  "updatedAt": "0001-01-01T00:00:00Z",
                  "email": "",
                  "url": "",
                  "type": "",
                  "eabKid": "",
                  "eabHmacKey": "",
                  "keyType": "",
                  "useProxy": false,
                  "caDirURL": ""
                },
                "dnsAccount": {
                  "id": 0,
                  "createdAt": "0001-01-01T00:00:00Z",
                  "updatedAt": "0001-01-01T00:00:00Z",
                  "name": "",
                  "type": ""
                },
                "websites": null
              },
              "errorLogPath": "",
              "accessLogPath": "",
              "sitePath": "",
              "appName": "",
              "runtimeName": "",
              "runtimeType": "",
              "siteDir": ""
            }
          ]
        }"""
        try:
            data = self.lpc.get_websites()
            res = []
            for i in data["data"]:
                res.append({
                    "site_id": i["id"],
                    "site_name": i["alias"],
                    "ports": list(set([i["port"] for i in i["domains"]])),
                    "domains": list(set([i["domain"] for i in i["domains"]])),
                    "ssl": any(i["ssl"] for i in i["domains"])
                })
            return res, ""
        except Exception as e:
            return [], str(e)

    def create_php_site(self, site_name: str, port: int, **kwargs) -> Tuple[Optional[int], str]:
        try:
            dat = self.lpc.add_website(site_name, port, **kwargs)
            public.print_log(dat)
            if dat["code"] == 200:
                time.sleep(0.5)
                site_id = self.lpc.check_site_create(site_name)
                if isinstance(site_id, int):
                    return site_id, ""
                return None, "网站创建失败"
            return None, dat["message"]
        except Exception as e:
            return None, str(e)

    def set_firewall_open(self, port: int, protocol: str = "tcp") -> Tuple[bool, str]:
        try:
            dat = self.lpc.open_port(port, protocol)
            if dat["code"] == 200:
                return True, ""
            return False, dat["message"]
        except Exception as e:
            return False, str(e)

    def add_domain(self, site_id: int, site_name: str, domain: str, port: int) -> Tuple[bool, str]:
        try:
            dat = self.lpc.add_website_domain(site_id, domain, port)
            if dat["code"] == 200:
                return True, ""
            return False, dat["message"]
        except Exception as e:
            return False, str(e)

    def has_domain(self, site_id: int, domain: str) -> bool:
        try:
            dat = self.lpc.website_domains(site_id)
            if dat["code"] == 200:
                for i in dat["data"]:
                    if i["domain"] == domain:
                        return True
                return False
            return False
        except Exception as e:
            return False

    def target_file_exits(self, target_file: str) -> Tuple[bool, str]:
        data = self.lpc.files_exits([target_file])
        if not isinstance(data, dict):
            return False, "请求文件：{}的状态失败".format(target_file)
        for i in data["data"]:
            if i["path"] == target_file:
                return True, ""
        return False, ""

    def upload_dir_check(self, target_dir: str) -> str:
        data = self.lpc.files_exits([target_dir])
        if not isinstance(data, dict):
            return "请求文件：{}的状态失败".format(target_dir)
        for i in data["data"]:
            if i["path"] == target_dir:
                if not i.get("isDir", True):
                    return "该名称路径不是目录"
                return ""
        return ""

    def _upload_big_file(self, filename: str, target_path: str, upload_name: str,
                         call_log: Callable[[int, str], None] = None) -> str:
        try:
            fb = open(filename, 'rb')
        except Exception as e:
            public.print_error()
            return "文件{}打开失败，请检查文件权限，错误信息为:{}".format(filename, str(e))

        file_size = os.path.getsize(filename)
        count = math.ceil(file_size / (1024 * 1024 * 5))
        idx = 0
        for i in range(0, file_size, 1024 * 1024 * 5):
            file_data = fb.read(1024 * 1024 * 5)
            err, data = self.lpc.chunkupload(upload_name, target_path, file_data, idx, count)
            idx += 1
            if err:
                return "上传文件{}失败，错误信息为:{}".format(filename, str(err))
            if data:
                call_log(100, "文件上传:{} -> {},上传成功".format(filename, upload_name))
            else:
                up_d = (i + len(file_data)) // file_size
                call_log(up_d, "文件上传:{} -> {},已上传大小为:{}".format(
                    filename, upload_name, public.to_size(i + len(file_data))))
        return ""

    def _upload_little_file(self, filename: str, target_path: str, upload_name: str,
                            call_log: Callable[[int, str], None] = None) -> str:
        return self.lpc.upload(filename, target_path, upload_name)

    def download_file(self, filename: str, target_path: str, mode: str,
                      call_log: Callable[[int, str], None] = None) -> str:
        target_file = os.path.join(target_path, os.path.basename(filename))
        exits = os.path.exists(target_file)
        if exits and mode == "ignore":
            call_log(0, "文件下载:{} -> {},目标文件已存在,跳过下载".format(filename, target_file))
            return ""
        if exits and mode == "rename":
            download_name = "{}_{}".format(os.path.basename(filename), public.md5(filename))
            call_log(0, "文件下载:{} -> {},目标文件已存在,将重命名为{}".format(filename, target_file, download_name))
        else:
            download_name = os.path.basename(filename)

        return self.lpc.download_file(filename, target_path, download_name, call_log=call_log)

    def dir_walk(self, path: str) -> Tuple[List[dict], str]:
        return self.lpc.dir_walk(path)

    def upload_proxy(self):
        try:
            from BTPanel import request, cache
            f_name = request.form.get('f_name')
            f_path = request.form.get('f_path')
            f_size = request.form.get('f_size')
            f_start = request.form.get('f_start')
            cache_key = "upload_file_{}_{}_{}".format(f_name, f_path, f_size)
            num = cache.get(cache_key)
            if num is None:
                num = 0
                cache.set(cache_key, num, 86400)
            else:
                num = int(num)
                cache.set(cache_key, num + 1, 86400)
            blob_file: FileStorage = request.files.getlist('blob')[0]
            file_data = blob_file.read()
            next_size = int(f_start) + len(file_data)
            if next_size == int(f_size):
                chunk_num = num + 1
            else:
                chunk_num = num + 2
            err, data = self.lpc.chunkupload(f_name, f_path, file_data, num, chunk_num)
            if err:
                return {"status": False, "msg": "上传文件失败，错误信息为:{}".format(str(err))}
            elif data is None:
                return str(next_size)
            elif isinstance(data, dict) and data["code"] == 200:
                return {"status": True, "msg": "上传成功"}
            return {"status": False, "msg": "上传文件失败，错误信息为:{}".format(data["message"])}
        except Exception as e:
            public.print_error()
            return {"status": False, "msg": "上传文件失败，错误信息为:{}".format(str(e))}

    def remove_file(self, filename: str, is_dir: bool) -> dict:
        try:
            res = self.lpc.remove_file(filename, is_dir)
            if isinstance(res, dict):
                return {"status": res["code"] == 200, "msg": res["message"]}
            return {"status": False, "msg": "删除文件失败，请求远程失败"}
        except Exception as e:
            return {"status": False, "msg": "删除文件失败，错误信息为:{}".format(str(e))}

    def file_list(self, path: str, p: int, row: int, search: str) -> Tuple[Dict, str]:
        try:
            res, err = self.lpc.files_search(path, p, row, search)
            if err:
                return {}, "获取文件列表失败，错误信息为:{}".format(err)
            count = res["itemTotal"]
            path = res["path"]
            dirs = []
            files = []
            sub_items = [] if res["items"] is None else res["items"]
            for i in sub_items:
                # res = self._TIME_REGEXP.findall(i["modTime"])
                # public.print_log(res)
                mt_str = self._TIME_REGEXP.sub(lambda x: x.group().replace(x.group("err"), ""), i["modTime"])
                for f_str in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S.%f%z"):
                    try:
                        mt = datetime.strptime(mt_str, f_str)
                        break
                    except:
                        pass
                        # public.print_log(i["modTime"], mt_str)
                        # public.print_error()
                else:
                    continue

                if i["isDir"]:
                    dirs.append({
                        "nm": html.unescape(i["name"]),
                        "sz": i["size"],
                        "mt": int(mt.timestamp()),
                        "acc": i["mode"][1:],
                        "user": i["user"],
                        "lnk": "" if not i["linkPath"] else " -> " + i["linkPath"],
                        "durl": "",
                        "cmp": 0,
                        "fav": "0",
                        "rmk": "",
                        "top": 0,
                        "sn": i["name"]
                    })
                else:
                    files.append({
                        "nm": html.unescape(i["name"]),
                        "sz": i["size"],
                        "mt": int(mt.timestamp()),
                        "acc": i["mode"][1:],
                        "user": i["user"],
                        "lnk": "" if not i["linkPath"] else " -> " + i["linkPath"],
                        "durl": "",
                        "cmp": 0,
                        "fav": "0",
                        "rmk": "",
                        "top": 0,
                        "sn": i["name"]
                    })

            return {
                "path": path,
                "page": public.get_page(count, p, row)["page"],
                "dir": dirs,
                "files": files
            }, ""
        except Exception as e:
            return {}, "获取文件列表失败，错误信息为:{}".format(str(e))

    def download_proxy(self, filename: str):
        return self.lpc.download_proxy(filename)

    def upload_check(self, target_file_list: List[str]) -> Tuple[List[dict], str]:
        try:
            res = self.lpc.files_exits(target_file_list)
            if res is None:
                return [], "请求远程1Panel失败"
            data = res.get("data", [])
            res_data = []
            for i in data:
                try:
                    mt = datetime.strptime(i["modTime"], "%Y-%m-%dT%H:%M:%S%z")
                except:
                    try:
                        mt = datetime.strptime(i["modTime"], "%Y-%m-%dT%H:%M:%S.%f%z")
                    except:
                        continue
                res_data.append({
                    'filename': i["path"],
                    'exists': True,
                    'size': i["size"],
                    'mtime': int(mt.timestamp()),
                    'isfile': False
                })

            return res_data, ""
        except Exception as e:
            return [], "请求远程1Panel失败，错误信息为:{}".format(str(e))

    def dir_size(self, path: str) -> Tuple[Optional[int], str]:
        try:
            res = self.lpc.dir_size(path)
            if res is None:
                return None, "请求远程1Panel失败"
            if not isinstance(res, dict):
                return None, "请求远程1Panel失败, 响应数据：%s" % str(res)
            return res["data"].get("size", 0), ""
        except Exception as e:
            return None, "请求远程1Panel失败: %s" % str(e)

    def get_sshd_port(self) -> Optional[int]:
        try:
            data = self.lpc.get_sshd_config()
            return int(data["port"]) if data else None
        except:
            return None

    def create_dir(self, path: str) -> Tuple[Optional[Dict], str]:
        try:
            data = self.lpc.create_dir(path)
            if not data:
                return None, "创建目录失败, 1Panel节点连接失败"
            status = data["code"] == 200
            return {"status": status, "msg": data["message"] if not status else "创建成功"}, ""
        except Exception as e:
            return None, "请求远程1Panel节点失败： %s" % str(e)

    def restart_bt_panel(self) -> Dict[str, Any]:
        self.lpc.restart_panel()
        return {"status": True, "msg": "重启成功"}

    def server_reboot(self) -> Dict[str, Any]:
        self.lpc.server_reboot()

        from mod.project.node.dbutil import ServerMonitorRepo
        repo = ServerMonitorRepo()
        repo.set_wait_reboot(self.node_server_ip, True)

        def wait_for_reboot():
            # wait 等待服务器重启成功， 超时时间默认为 10 分钟
            wait_for = time.time() + 600
            time.sleep(3)
            while time.time() < wait_for:
                if self.test_conn() == "":  # 无错误时表示重启成功
                    repo.set_wait_reboot(self.node_server_ip, False)
                    from mod.project.node.dbutil import ServerNodeDB
                    node_data = ServerNodeDB().find_node(api_key=self.api_key, app_key=self.app_key.to_string())
                    if node_data:
                        monitor_node_once(node_data)
                    return {"status": True, "msg": "重启服务器成功"}
                time.sleep(3)
                public.print_log("等待服务器重启中... {}".format(wait_for - time.time()))
            repo.set_wait_reboot(self.node_server_ip, False)
            return {"status": False, "msg": "重启服务器失败, 已超过10分钟未能检测到服务器信息"}

        t = threading.Thread(target=wait_for_reboot, daemon=True)
        t.start()

        return {"status": True, "msg": "重启服务器已开始，请赖心等待重启成功"}

    def get_file_body(self, path: str) -> Tuple[Optional[str], str]:
        data_dict, err = self.lpc.get_file_body(path)
        if err != "":
            return None, err
        return data_dict["content"], ""

    def read_ssh_key(self) -> Tuple[Optional[str], str]:
        key, err = self.lpc.get_file_body("/root/.ssh/id_ed25519_1panel")
        if err:
            return None, "读取SSH密钥失败, 错误信息为: %s" % err
        return key, ""