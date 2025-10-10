import os.path
import shutil
import traceback
from uuid import uuid4

import requests
import time
import hashlib
import json
from typing import Optional, List, Any, Tuple, Dict


class OnePanelApiClient:
    def __init__(self, panel_address, api_key, ver: str = "v2", timeout: int = 20):
        """
        初始化 OnePanel API 客户端

        Args:
            panel_address (str): 1Panel 的访问地址 (例如: "http://your_server_ip:4004")
            api_key (str): 您的 1Panel API Key
        """
        self.panel_address = panel_address
        self.api_key = api_key
        self.ver = ver
        self.timeout = timeout
        self._call_err: Optional[Exception] = None

    def _generate_token(self):
        """生成 1Panel API token 和时间戳"""
        timestamp = str(int(time.time()))
        sign_string = f"1panel{self.api_key}{timestamp}"
        md5_hash = hashlib.md5(sign_string.encode()).hexdigest()
        return md5_hash, timestamp

    def _call_api(self, method, endpoint, json_data=None):
        """发送 API 请求"""
        token, timestamp = self._generate_token()
        headers = {
            "1Panel-Token": token,
            "1Panel-Timestamp": timestamp,
            "Content-Type": "application/json"
        }
        url = "{}{}".format(self.panel_address, endpoint)

        # print(f"Calling API: {method} {url}")
        try:
            response = requests.request(method, url, headers=headers, json=json_data, timeout=self.timeout)
            response.raise_for_status()  # 检查 HTTP 错误 (例如 4xx 或 5xx)
            print(f"API Response Status: {response.status_code}")
            return response.json()
        except requests.exceptions.RequestException as e:
            self._call_err = e
            print(f"API 调用失败: {e}")
            return None
        except Exception as e:
            self._call_err = e
            print(f"API 调用失败: {e}")
            return None

    def add_website(self, site_name: str, port: int, **kwargs):
        """
        添加网站
        """
        endpoint = "/api/{}/websites".format(self.ver)
        return self._call_api("POST", endpoint, json_data={
            "primaryDomain": site_name,
            "type": "static",
            "alias": site_name,
            "remark": kwargs.get("ps") if kwargs.get("ps", None) else "宝塔面板负载均衡站点",
            "appType": "installed",
            "webSiteGroupId": 1,
            "otherDomains": "",
            "proxy": "",
            "appinstall": {
                "appId": 0,
                "name": "",
                "appDetailId": 0,
                "params": {},
                "version": "",
                "appkey": "",
                "advanced": False,
                "cpuQuota": 0,
                "memoryLimit": 0,
                "memoryUnit": "MB",
                "containerName": "",
                "allowPort": False
            },
            "IPV6": False,
            "enableFtp": False,
            "ftpUser": "",
            "ftpPassword": "",
            "proxyType": "tcp",
            "port": 9000,
            "proxyProtocol": "http://",
            "proxyAddress": "",
            "runtimeType": "php",
            "taskID": str(uuid4()),
            "createDb": False,
            "dbName": "",
            "dbPassword": "",
            "dbFormat": "utf8mb4",
            "dbUser": "",
            "dbType": "mysql",
            "dbHost": "",
            "enableSSL": False,
            "domains": [
                {
                    "domain": site_name,
                    "port": port,
                    "ssl": False
                }
            ],
            "siteDir": ""
        })

    def check_site_create(self, site_name: str) -> Optional[int]:
        endpoint = "/api/{}/websites/search".format(self.ver)
        res_data = self._call_api("POST", endpoint, json_data={
            "name": site_name,
            "page": 1,
            "pageSize": 10,
            "orderBy": "favorite",
            "order": "descending",
            "websiteGroupId": 0,
            "type": "static"
        })

        if res_data is not None and "data" in res_data and isinstance(res_data["data"], dict):
            for item in res_data["data"].get("items", {}):
                if item["alias"] == site_name:
                    return item["id"]
        return None

    def get_websites(self):
        """
        获取所有网站信息

        Returns:
            dict: API 返回结果 (网站列表)，失败返回 None
        """
        # 示例接口路径，请根据您的 Swagger 文档修改
        endpoint = "/api/{}/websites/list".format(self.ver)
        return self._call_api("GET", endpoint)

    def add_website_domain(self, website_id: int, new_domain: str, port: int):
        """
        设置网站域名
        """
        # 示例接口路径和参数，请根据您的 Swagger 文档修改
        endpoint = "/api/{}/websites/domains".format(self.ver)
        return self._call_api("POST", endpoint, json_data={
            "websiteID": website_id,
            "domains": [
                {
                    "domain": new_domain,
                    "port": port,
                    "ssl": False
                }
            ],
            "domainStr": ""
        })

    def website_domains(self, website_id: int):
        """
        获取网站域名列表
        """
        endpoint = "/api/{}/websites/domains/{website_id}".format(self.ver, website_id=website_id)
        return self._call_api("GET", endpoint)

    def list_file_test(self):
        endpoint = "/api/{}/files/search".format(self.ver)
        return self._call_api("POST", endpoint, json_data={
            "containSub": False,
            "dir": True,
            "expand": True,
            "isDetail": True,
            "page": 0,
            "pageSize": 0,
            "path": "/",
            "search": "",
            "showHidden": True,
            "sortBy": "",
            "sortOrder": ""
        })

    def list_file(self, path: str) -> Tuple[List[Dict], str]:
        endpoint = "/api/{}/files/search".format(self.ver)
        res = self._call_api("POST", endpoint, json_data={
            "containSub": False,
            "expand": True,
            "isDetail": True,
            "page": 1,
            "pageSize": 1000,
            "path": path,
            "search": "",
            "showHidden": True,
            "sortBy": "name",
            "sortOrder": "ascending"
        })
        if res is None:
            return [], "获取文件列表失败"
        if res["code"] != 200:
            return [], res["message"]
        if res["data"]["itemTotal"] > 1000:
            return [], "目录文件数量超过1000,请压缩后再操作"
        elif res["data"]["itemTotal"] == 0:
            return [], ""
        return [] if res["data"]["items"] is None else res["data"]["items"], ""

    def files_search(self, path: str, page: int, page_size: int, search: str):
        endpoint = "/api/{}/files/search".format(self.ver)
        res = self._call_api("POST", endpoint, json_data={
            "containSub": False,
            "expand": True,
            "isDetail": True,
            "page": page,
            "pageSize": page_size,
            "path": path,
            "search": search,
            "showHidden": True,
            "sortBy": "name",
            "sortOrder": "ascending"
        })
        if res is None:
            return {}, "获取文件列表失败"
        elif res["code"] != 200:
            return {}, res["message"]
        return res["data"], ""

    def test_ver(self) -> bool:
        self.ver = "v2"
        self._call_err = None
        res_data = self.list_file_test()
        if res_data is None and isinstance(self._call_err, json.JSONDecodeError):
            self.ver = "v1"
            res_data = self.list_file_test()
            if isinstance(res_data, dict):
                return True
        elif isinstance(res_data, dict):
            return True
        return False

    def system_status(self):
        endpoint = "/api/{}/dashboard/current".format(self.ver)
        if self.ver == "v1":
            return self._call_api("POST", endpoint, json_data={
                "scope": "basic",
                "ioOption": "all",
                "netOption": "all"
            })
        else:
            return self._call_api("GET", endpoint + "/all/all")

    def open_port(self, port: int, protocol: str):
        endpoint = "/api/{}/hosts/firewall/port".format(self.ver)
        return self._call_api("POST", endpoint, json_data={
            "protocol": protocol,
            "source": "anyWhere",
            "strategy": "accept",
            "port": str(port),
            "description": "aaaa",
            "operation": "add",
            "address": ""
        })

    def ws_shell(self, work_dir: str, cmd: str) -> Optional[str]:
        import websocket
        import base64
        import threading
        from urllib.parse import urlencode, urlparse
        if self.ver != "v2":
            return None
        try:
            pre_command = "PS1="" && stty -echo && clear && cd {}".format(work_dir, cmd)
            p = {
                "cols": 80,
                "rows": 24,
                "command": pre_command,
                "operateNode": "local"
            }
            token, timestamp = self._generate_token()
            u = urlparse(self.panel_address)
            url = ("{}://{}/api/{}/hosts/terminal?{}".format
                   ("ws" if u.scheme == "http" else "wss", u.netloc, self.ver, urlencode(p)))
            ws = websocket.WebSocket()
            ws.connect(url, header={"1Panel-Token": token, "1Panel-Timestamp": timestamp, })
            if not cmd.endswith("\n"):
                cmd += "\n"
            ws.send(json.dumps({"type": "cmd", "data": base64.b64encode(cmd.encode("utf-8")).decode("utf-8")}))
            res_str = ""

            wait = False

            def close_timeout():
                time.sleep(5)
                if wait:
                    ws.close()

            threading.Thread(target=close_timeout).start()

            while True:
                wait = True
                result = ws.recv()
                wait = False
                if result == "":
                    break
                res_data = json.loads(result)
                if res_data["type"] == "cmd":
                    res_str += base64.b64decode(res_data["data"]).decode("utf-8")

            if pre_command in res_str:
                res_str = res_str[res_str.index(pre_command) + len(pre_command):]

            res_str = res_str.strip()
            real_data = []
            for line in res_str.split("\r\n"):
                if line[0] == '\x1b':
                    continue
                real_data.append(line)

            real_data = "\n".join(real_data)
            with open("test.txt", "w") as f:
                f.write(real_data)
            return real_data
        except Exception as e:
            print("错误：{}".format(str(e)))
            traceback.print_exc()
        return None

    def chunkupload(self,
                    upload_name: str,
                    target_path: str,
                    chunk: Any, chunk_index: int, chunk_count: int) -> Tuple[str, Optional[dict]]:
        token, timestamp = self._generate_token()
        header = {"User-Agent": "Bt-Panel/Node Manager", "1Panel-Token": token, "1Panel-Timestamp": timestamp}
        files = {'chunk': ("chunk", chunk, 'application/octet-stream')}
        data = {
            'path': target_path,
            'filename': upload_name,
            'chunkIndex': chunk_index,
            'chunkCount': chunk_count,
        }
        url = "{}/api/{}/files/chunkupload".format(self.panel_address, self.ver)
        try:
            resp = requests.post(url, data=data, files=files, headers=header, verify=False, timeout=self.timeout)
            if not resp.status_code == 200:
                return "上传文件响应状态码错误，请检查节点地址和api是否正确，目前状态码为{},返回信息为:{}".format(
                    resp.status_code, resp.text), None

            return "", None if len(resp.text) < 3 else json.loads(resp.text)
        except Exception as e:
            return "上传文件文件：{}失败，错误信息为:{}".format(upload_name, str(e)), None

    def upload(self, filename: str, target_path: str, upload_name: str) -> str:
        token, timestamp = self._generate_token()
        header = {"User-Agent": "Bt-Panel/Node Manager", "1Panel-Token": token, "1Panel-Timestamp": timestamp}
        try:
            with open(filename, 'rb') as f:
                file_data = f.read()
        except Exception as e:
            return "文件{}打开失败，请检查文件权限，错误信息为:{}".format(filename, str(e))

        files = {'file': (upload_name, file_data, 'application/octet-stream')}
        data = {
            'path': target_path,
            'overwrite': True
        }
        url = "{}/api/{}/files/upload".format(self.panel_address, self.ver)
        try:
            resp = requests.post(url, data=data, files=files, headers=header, verify=False, timeout=self.timeout)
            if not resp.status_code == 200:
                return "上传文件响应状态码错误，请检查节点地址和api是否正确，目前状态码为{},返回信息为:{}".format(
                    resp.status_code, resp.text)
            if not resp.json()["code"] == 200:
                return "上传文件失败，错误信息为:{}".format(resp.json()["message"])
            return ""
        except Exception as e:
            return "上传文件文件：{}失败，错误信息为:{}".format(filename, str(e))

    def files_exits(self, paths: List[str]) -> Optional[dict]:
        endpoint = "/api/{}/files/batch/check".format(self.ver)
        return self._call_api("POST", endpoint, json_data={
            "paths": paths,
        })

    def download_file(self, filename: str, target_path: str, download_name: str, **kwargs) -> str:
        data = self.files_exits([filename])
        file_size: Optional[int] = None
        if not isinstance(data, dict):
            return "请求文件：{}的状态失败".format(filename)
        for i in data["data"]:
            if i["path"] == filename:
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

        call_log = lambda *args, **keyword_args: None
        if "call_log" in kwargs and callable(kwargs["call_log"]):
            call_log = kwargs["call_log"]
        try:
            for i in range(0, file_size, 1024 * 1024 * 5):
                start = i
                end = min(i + 1024 * 1024 * 5 - 1, file_size - 1)
                url = "{}/api/{}/files/chunkdownload".format(self.panel_address, self.ver)
                data = {
                    'path': filename,
                    'name': os.path.basename(filename),
                }
                token, timestamp = self._generate_token()
                header = {"User-Agent": "Bt-Panel/Node Manager", "1Panel-Token": token, "1Panel-Timestamp": timestamp}
                header.update({"Range": "bytes={}-{}".format(start, end)})
                resp = requests.post(url, json=data, headers=header, verify=False, stream=True, timeout=self.timeout)
                if resp.status_code != 206:
                    return "下载文件响应状态码错误，请检查节点地址和api是否正确，目前状态码为{},返回信息响应头是:{}".format(
                        resp.status_code, resp.headers)
                fb.write(resp.content)
                call_log(end // file_size, "文件下载：{} -> {}, 已下载大小：{}".format(filename, target_path, end))
                fb.flush()
            if fb.tell() != file_size:
                print(fb.tell(), file_size)
                return "下载文件{}失败，错误信息为:{}".format(filename, "文件大小不一致")
            else:
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

    def dir_walk(self, path: str) -> Tuple[List[dict], str]:
        dirs = [path]
        res = []
        count = 0
        empty_dir = []
        while dirs:
            dir_path = dirs.pop(0)
            try:
                files, err = self.list_file(dir_path)
            except Exception as e:
                return [], str(e)
            if err:
                return [], err
            if not files:
                empty_dir.append(dir_path)
            for i in files:
                if i["isDir"]:
                    dirs.append(i["path"])
                else:
                    res.append({
                        "path": i["path"],
                        "size": i["size"],
                        "is_dir": 0
                    })
                    count += 1
                    if count > 1000:
                        return [], "目录文件数量超过1000,请压缩后再操作"

        return [{"path": i, "size": 0, "is_dir": 1} for i in empty_dir] + res, ""

    def remove_file(self, path: str, is_dir: bool) -> str:
        return self._call_api("POST", "/api/{}/files/del".format(self.ver), json_data={
            "isDir": is_dir,
            "path": path,
            "forceDelete": False
        })

    def download_proxy(self, filename: str):
        try:
            url = "{}/api/{}/files/download".format(self.panel_address, self.ver)
            token, timestamp = self._generate_token()
            header = {"User-Agent": "Bt-Panel/Node Manager", "1Panel-Token": token, "1Panel-Timestamp": timestamp}
            resp = requests.get(url, params={
                "operateNode": "local",
                "path": filename
            }, headers=header, stream=True, verify=False, timeout=self.timeout)
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
            return "下载文件：{}失败，错误信息为:{}".format(filename, traceback.format_exc())

    def dir_size(self, path: str):
        return self._call_api("POST", "/api/{}/files/size".format(self.ver), json_data={
            "path": path
        })

    def get_sshd_config(self) -> Optional[dict]:
        res = self._call_api("POST", "/api/{}/hosts/ssh/search".format(self.ver))
        if res is None:
            return None
        if res["code"] == 200:
            return res.get("data", {})
        return None

    def create_dir(self, path: str):
        return self._call_api("POST", "/api/{}/files".format(self.ver), {
            "content": "",
            "isDir": True,
            "isLink": False,
            "isSymlink": False,
            "linkPath": "",
            "mode": 0,
            "path": path,
            "sub": False
        })

    def restart_panel(self):
        return self._call_api("POST", "/api/{}/dashboard/system/restart/{}".format(self.ver, "1panel"))

    def server_reboot(self):
        return self._call_api("POST", "/api/{}/dashboard/system/restart/{}".format(self.ver, "system"))

    def get_file_body(self, path: str) -> Tuple[Optional[dict], str]:
        res = self._call_api("POST", "/api/{}/files/content".format(self.ver), json_data={
            "path": path,
            "expand":True,
            "isDetail": False,
            "page":1,
            "pageSize":100
        })
        if res is None:
            return None, "获取文件内容失败"
        if res["code"] == 200:
            return res.get("data", {}), ""
        return None, res.get("message")