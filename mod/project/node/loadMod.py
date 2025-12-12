import json
import os
import re
from typing import List

import simple_websocket
from mod.base import json_response
from mod.project.node.dbutil import LoadSite, HttpNode, NodeDB, TcpNode, ServerNodeDB
from mod.project.node.loadutil import load_check, config_generator
from mod.project.node.loadutil.nginx_utils import NginxUtils
from mod.project.node.loadutil.log_analyze import get_log_analyze, get_log_file
from mod.project.node.nodeutil import ServerNode

import public


class main():
    def __init__(self):
        pass

    def create_http_load(self, get):
        """
        @route /ws_modsoc/node/load/create_http_load
        @param name str
        @param site_name str
        @param ps str
        @param http_config.proxy_next_upstream str
        @param http_config.http_alg str
        @param nodes.[].node_site str
        @param nodes.[].port int
        @param nodes.[].path str
        @param nodes.[].node_status str
        @param nodes.[].weight int
        @param nodes.[].node_id int
        @param nodes.[].max_conns int
        @param nodes.[].max_fail int
        @param nodes.[].fail_timeout int
        @param nodes.[].ps str
        @return ws {
            "type": str,
		    "data": str
        }
        """
        ws: simple_websocket.Server = getattr(get, '_ws', None)
        if not ws:
            return json_response(False, "请使用 WebSocket 连接")
        if not NginxUtils.nginx_exists():
            ws.send(json.dumps({"type": "error", "data": "该功能依赖nginx，请先安装nginx服务"}))
            return
        name = get.get("name", "")
        if not name:
            name = public.GetRandomString(8)
            get.name = name
        public.set_module_logs("nodes_create_http_load_9", "create_http_load")
        load, err = LoadSite.bind_http_load(get)
        if err:
            ws.send(json.dumps({"type": "error", "data": "解析参数错误:%s" % err}))
            return

        nodes: List[HttpNode] = []
        for node_data in get.get("nodes", []):
            node, err = HttpNode.bind(node_data)
            if err:
                ws.send(json.dumps({"type": "error", "data": "解析节点%s参数错误:%s" % (node_data.get("node_site_name"), err)}))
                return
            nodes.append(node)

        if len(nodes) == 0:
            ws.send(json.dumps({"type": "error", "data": "节点不能为空"}))
            return
        node_db = NodeDB()
        if node_db.name_exist(load.name):
            ws.send(json.dumps({"type": "error", "data": "名称已存在"}))
            return
        if node_db.load_site_name_exist(load.site_name):
            ws.send(json.dumps({"type": "error", "data": "站点已存在"}))
            return
        log_call = lambda x: ws.send(json.dumps({"type": "log", "data": x}))
        log_call("开始检查负载配置...")
        err = load_check.check_http_load_data(load, log_call)
        if err:
            ws.send(json.dumps({"type": "error", "data": err}))
            return

        for n in nodes:
            err = load_check.check_http_node(n, load.site_name, log_call)
            if err:
                ws.send(json.dumps({"type": "error", "data": err}))
                return

        log_call("开始生成配置文件...")
        cgr = config_generator.NginxConfigGenerator()
        err = cgr.save_configs(load, nodes)
        if err:
            ws.send(json.dumps({"type": "error", "data": "生成配置文件失败:%s" % err}))
            return

        err = node_db.create_load("http", load, nodes)
        if err:
            ws.send(json.dumps({"type": "error", "data": "保存数据失败:%s" % err}))
            return
        ws.send(json.dumps({"type": "end", "data": "数据保存成功"}))
        # return json_response(True, "负载配置创建成功")
        return

    def modify_http_load(self, get):
        """
        @route /ws_modsoc/node/load/modify_http_load
        @param name str
        @param load_id int
        @param site_name str
        @param ps str
        @param http_config.proxy_next_upstream str
        @param http_config.http_alg str
        @param nodes.[].node_site str
        @param nodes.[].node_site_id int
        @param nodes.[].id int
        @param nodes.[].port int
        @param nodes.[].path str
        @param nodes.[].node_status str
        @param nodes.[].weight int
        @param nodes.[].node_id int
        @param nodes.[].max_conns int
        @param nodes.[].max_fail int
        @param nodes.[].fail_timeout int
        @param nodes.[].ps str
        @return ws {
            "type": str,
		    "data": str
        }
        """

        ws: simple_websocket.Server = getattr(get, '_ws', None)
        if not ws:
            return json_response(False, "请使用 WebSocket 连接")

        if get.get("load_id/d", 0) < 0:
            ws.send(json.dumps({"type": "error", "data": "负载ID不能为空"}))
            return

        load, err = LoadSite.bind_http_load(get)
        if err:
            ws.send(json.dumps({"type": "error", "data": "解析参数错误:%s" % err}))
            return

        if len(get.get("nodes", [])) <= 0:
            ws.send(json.dumps({"type": "error", "data": "负载ID不能为空"}))
            return

        nodes: List[HttpNode] = []
        for node_data in get.get("nodes", []):
            node, err = HttpNode.bind(node_data)
            if err:
                ws.send(json.dumps({"type": "error", "data": "解析参数错误:%s" % err}))
                return
            nodes.append(node)

        if not nodes:
            ws.send(json.dumps({"type": "error", "data": "节点不能为空"}))
            return

        node_db = NodeDB()
        if not node_db.load_id_exist(load.load_id):
            ws.send(json.dumps({"type": "error", "data": "未找到该负载配置"}))
            return

        log_call = lambda x: ws.send(json.dumps({"type": "log", "data": x}))
        err = load_check.check_http_load_data(load, log_call)
        if err:
            ws.send(json.dumps({"type": "error", "data": err}))
            return

        for n in nodes:
            err = load_check.check_http_node(n, load.site_name, log_call)
            if err:
                ws.send(json.dumps({"type": "error", "data": err}))
                return

        log_call("生成配置文件...")
        cgr = config_generator.NginxConfigGenerator()
        err = cgr.save_configs(load, nodes)
        if err:
            ws.send(json.dumps({"type": "error", "data": "生成配置文件失败:%s" % err}))
            return

        err = node_db.update_load("http", load, nodes)
        if err:
            ws.send(json.dumps({"type": "error", "data": "保存数据失败:%s" % err}))
            return
        ws.send(json.dumps({"type": "success", "data": "数据保存成功"}))
        return json_response(True, "负载配置创建成功")

    def check_http_node(self, get):
        """
        @route /ws_modsoc/node/load/check_http_node
        @param node_site str
        @param node_site_id int
        @param port int
        @param path str
        @param node_status str
        @param weight int
        @param max_conns int
        @param max_fail int
        @param fail_timeout int
        @param ps str
        @return ws {
            "type": str,
            "data": str
        }
        """
        ws: simple_websocket.Server = getattr(get, '_ws', None)
        if not ws:
            return json_response(False, "请使用 WebSocket 连接")
        node, err = HttpNode.bind(get)
        if err:
            ws.send(json.dumps({"type": "error", "data": "解析参数错误:%s" % err}))
            return

        log_call = lambda x: ws.send(json.dumps({"type": "log", "data": x}))
        err = load_check.check_http_node(node, "", log_call)
        if err:
            ws.send(json.dumps({"type": "error", "data": err}))
            return
        ws.send(json.dumps({"type": "end", "data": "测试连接成功"}))
        return json_response(True, "测试连接成功")

    def remove_http_load(self, get):
        """
        @route /mod/node/load/delete_http_load
        @param load_id int
        @param {
            "type": str,
		    "data": str
        }
        """

        load_id = get.get("load_id/d", 0)
        if load_id <= 0:
            return json_response(False, "负载ID不能为空")
        node_db = NodeDB()
        load, err = node_db.get_load(load_id)
        if err:
            return json_response(False, "未找到该负载配置")
        load["http_config"] = json.loads(load["http_config"])
        load["tcp_config"] = json.loads(load["tcp_config"])
        load, err = LoadSite.bind_http_load(load)
        if err:
            return json_response(False, "解析参数错误:%s" % err)
        err = node_db.delete(load_id)
        if err:
            return json_response(False, "删除失败:%s" % err)
        cgr = config_generator.NginxConfigGenerator()

        cgr.delete_node_conf(load)

        return json_response(True, "删除成功")

    def multi_remove_http_load(self, get):
        load_ids = get.get("load_ids/s", '')
        try:
            load_ids = json.loads(load_ids)
            load_ids = [int(i) for i in load_ids]
        except:
            return json_response(False, "参数格式错误")
        node_db = NodeDB()
        for load_id in load_ids:
            if load_id <= 0:
                continue
            load, err = node_db.get_load(load_id)
            if err:
                return json_response(False, "未找到该负载配置")
            load["http_config"] = json.loads(load["http_config"])
            load["tcp_config"] = json.loads(load["tcp_config"])
            load, err = LoadSite.bind_http_load(load)
            if err:
                return json_response(False, "解析参数错误:%s" % err)
            err = node_db.delete(load_id)
            if err:
                return json_response(False, "删除失败:%s" % err)
            cgr = config_generator.NginxConfigGenerator()

            cgr.delete_node_conf(load, mutil=True)

        NginxUtils.reload_nginx()
        return json_response(True, "删除成功")

    def http_load_list(self, get):
        """
        @route /mod/node/load/http_load_list
        @param page int
        @param page_size int
        @return {
            "page": str,
            "data": [
                {
                    "load_id": int,
                    "name": str,
                    "site_id": int,
                    "site_name": str,
                    "ps": str,
                    "http_config": {
                        "proxy_next_upstream": str,
                        "http_alg": str
                    },
                    "created_at": int,
                    "request": int,
                    "error": int,
                    "qps": int,
                    "upstream_time": int,
                    "last_request_time": str,
                    "nodes": [
                        {
                            "id": int,
                            "request": int,
                            "error": int,
                            "qps": int,
                            "upstream_time":  int,
                            "last_request": str,
                            "load_id": int,
                            "node_site": str,
                            "node_site_id": int,
                            "port": int,
                            "path": str,
                            "node_status": str,
                            "weight": int,
                            "max_fail": int,
                            "node_id": int,
                            "max_conns": int,
                            "ps": str,
                            "created_at": int,
                            "fail_timeout": int
                        }
                    ]
                }
            ]
        }
        """
        node_db = NodeDB()
        srv_db = ServerNodeDB()
        node_name_map = srv_db.node_map()
        page = max(get.get("page/d", 1), 1)
        page_size = max(get.get("page_size/d", 10), 1)
        search = get.get('search/s', "").strip()
        count = node_db.loads_count("http", search)
        loads = node_db.loads_list("http", (page - 1) * page_size, page_size, search)
        err = ""
        for load in loads:
            la = get_log_analyze("http", load["site_name"], interval=60)
            load["nodes"], tmp_err = node_db.get_nodes(load["load_id"], load["site_type"])
            if tmp_err:
                err = tmp_err
                continue
            la.analyze_logs()
            day_status = la.get_today_stats()
            load.update(day_status.get("total"))
            load["http_config"] = json.loads(load["http_config"])
            load["tcp_config"] = json.loads(load["tcp_config"])
            load["error_codes"] = [int(i[5:]) for i in load["http_config"]["proxy_next_upstream"].split() if i.startswith("http_")]
            for node in load["nodes"]:
                node_ip = ServerNode.get_node_ip(node["node_id"])
                tmp_status = day_status.get("nodes", {}).get(str(node_ip) + ":" + str(node["port"]))
                if not tmp_status:
                    tmp_status = {'requests': 0, 'errors': 0, 'max_response_time': 0,
                                  'max_upstream_time': 0, 'last_update': 0, 'qps': 0}
                node.update(tmp_status)
                node["node_remarks"] = node_name_map.get(node["node_id"], "-")
        data = public.get_page(count,page,page_size)
        data["data"] = loads
        data["err_info"] = err
        return data

    def log(self, get):
        """
        @route /mod/node/load/log
        @param load_id int
        @param date str
        @return {
            "time": str,
            "client_ip": str,
            "method": str,
            "node": str,
            "upstream_time": int,
            "bytes_sent": int,
            "body_sent": int,
            "status": int,
            "uri": str
        }
        """

        load_id = get.get("load_id/d", 0)
        date = get.get("date", "")
        position = get.get("position/d", -1)
        limit = get.get("limit/d", 16)
        if not load_id:
            return json_response(False, "参数错误")
        node_db = NodeDB()
        load, err = node_db.get_load(load_id)
        if err:
            return json_response(False, "未找到该负载配置")
        la = get_log_analyze("http", load["site_name"], date=date, interval=60)
        last_position, data_list = la.get_log(position, limit)
        return json_response(True, "获取成功", data={
            "last_position": last_position,
            "logs": data_list
        })

    def export_log(self, get):
        """
        @route /mod/node/load/export_log
        @param load_id int
        @param date str
        @return {
            "status": bool,
            "filename": str
        }
        """

        load_id = get.get("load_id/d", 0)
        date = get.get("date", "")
        if not load_id:
            return json_response(False, "参数错误")
        node_db = NodeDB()
        load, err = node_db.get_load(load_id)
        if err:
            return json_response(False, "未找到该负载配置")

        la = get_log_file("http", load["site_name"], date=date)
        if not os.path.exists(la):
            return json_response(False, "未找到该日志文件")
        return {
            "status": True,
            "filename": la
        }

    def set_http_load(self, get):
        """
         @route /mod/node/load/set_http_load
         @param load_id int
         @param http_codes []int
         @return {
             "status": bool,
             "msg" str
         }
        """

        load_id = get.get("load_id/d", 0)
        http_codes = get.get("http_codes/s", "[]")
        node_db = NodeDB()
        load, err = node_db.get_load(load_id)
        if err:
            return json_response(False, "未找到该负载配置")
        if not http_codes:
            return json_response(False, "参数错误")
        try:
            http_codes = json.loads(http_codes)
        except:
            return json_response(False, "参数错误")

        code_data = ["error", "timeout"]
        for i in http_codes:
            status_code = int(i)
            if status_code > 600 or status_code < 100:
                return json_response(False, "状态码错误")
            code_data.append("http_{}".format(status_code))
        load["http_config"] = json.loads(load["http_config"])
        load["http_config"]["proxy_next_upstream"] = " ".join(code_data)
        err = node_db.update_load_key(load_id, {
            "http_config": json.dumps(load["http_config"])
        })
        if err:
            return json_response(False, err)

        crg = config_generator.NginxConfigGenerator()
        err = crg.set_http_proxy_next_upstream(load["site_name"], load["http_config"]["proxy_next_upstream"])
        if err:
            return json_response(False, err)
        return json_response(True, "设置成功")

    def set_http_cache(self, get):
        """
         @route /mod/node/load/set_http_cache
         @param load_id int
         @param proxy_cache_status int
         @param cache_time str
         @param cache_suffix str
         @return {
             "status": bool,
             "msg" str
         }
        """

        load_id = get.get("load_id/d", 0)
        proxy_cache_status = bool(get.get("proxy_cache_status/d", 0))
        cache_time = get.get("cache_time/s", "1d")
        cache_suffix = get.get("cache_suffix/s", "")
        if not re.match(r"^[0-9]+([smhd])$", cache_time):
            return json_response(False, "缓存时间格式错误")
        cache_suffix_list = []
        for suffix in cache_suffix.split(","):
            tmp_suffix = re.sub(r"\s", "", suffix)
            if tmp_suffix:
                cache_suffix_list.append(tmp_suffix)
        real_cache_suffix = ",".join(cache_suffix_list)
        if not real_cache_suffix:
            real_cache_suffix = "css,js,jpe,jpeg,gif,png,webp,woff,eot,ttf,svg,ico,css.map,js.map"

        node_db = NodeDB()
        load, err = node_db.get_load(load_id)
        if err:
            return json_response(False, "未找到该负载配置")

        load["http_config"] = json.loads(load["http_config"])
        load["http_config"]["proxy_cache_status"] = proxy_cache_status
        load["http_config"]["cache_time"] = cache_time
        load["http_config"]["cache_suffix"] = real_cache_suffix
        err = node_db.update_load_key(load_id, {
            "http_config": json.dumps(load["http_config"])
        })
        if err:
            return json_response(False, err)

        public.print_log(load)
        load, err = LoadSite.bind_http_load(load)
        if err:
            return json_response(False, err)
        node_datas, err= node_db.get_nodes(load_id,"http")
        if err:
            return json_response(False, err)
        nodes = []
        for node in node_datas:
            node, _ = HttpNode.bind(node)
            if node is None: continue
            nodes.append(node)

        crg = config_generator.NginxConfigGenerator()
        err = crg.set_http_proxy_cache(load.site_name, load,  nodes)
        if err:
            return json_response(False, err)
        return json_response(True, "设置成功")

    def create_tcp_load(self, get):
        """
        @route /ws_modsoc/node/load/create_tcp_load
        @param name str
        @param site_name str
        @param ps str
        @param tcp_config.proxy_connect_timeout int
        @param tcp_config.proxy_timeout int
        @param tcp_config.host str
        @param tcp_config.port int
        @param tcp_config.type str
        @param nodes.[].host str
        @param nodes.[].port int
        @param nodes.[].node_status str
        @param nodes.[].weight int
        @param nodes.[].node_id int
        @param nodes.[].max_fail int
        @param nodes.[].fail_timeout int
        @param nodes.[].ps str
        @return ws {
            "type": str,
		    "data": str
        }
        """
        ws: simple_websocket.Server = getattr(get, '_ws', None)
        if not ws:
            return json_response(False, "请使用 WebSocket 连接")
        public.set_module_logs("node_create_tcp_load_9", "create_tcp_load")
        if not NginxUtils.nginx_exists():
            ws.send(json.dumps({"type": "error", "data": "该功能依赖nginx，请先安装nginx服务"}))
            return
        name = get.get("name", "")
        if not name:
            name = public.GetRandomString(8)
            get.name = name
        load, err = LoadSite.bind_tcp_load(get)
        if err:
            ws.send(json.dumps({"type": "error", "data": "解析参数错误:%s" % err}))
            return

        nodes: List[TcpNode] = []
        for node_data in get.get("nodes", []):
            node, err = TcpNode.bind(node_data)
            if err:
                ws.send(json.dumps({"type": "error", "data": "解析参数错误:%s" % err}))
                return
            nodes.append(node)

        if len(nodes) == 0:
            ws.send(json.dumps({"type": "error", "data": "节点不能为空"}))
            return
        node_db = NodeDB()
        if node_db.name_exist(load.name):
            ws.send(json.dumps({"type": "error", "data": "名称已存在"}))
            return
        log_call = lambda x: ws.send(json.dumps({"type": "log", "data": x}))
        log_call("开始检查负载配置...")
        err = load_check.check_tcp_load_data(load, log_call)
        if err:
            ws.send(json.dumps({"type": "error", "data": err}))
            return
        for n in nodes:
            if load.tcp_config["type"] == "tcp":
                err = load_check.check_tcp_node(n, log_call)
                if err:
                    ws.send(json.dumps({"type": "error", "data": err}))
                    return

        log_call("开始生成配置文件...")
        cgr = config_generator.NginxConfigGenerator()
        err = cgr.save_configs(load, nodes)
        if err:
            ws.send(json.dumps({"type": "error", "data": "生成配置文件失败:%s" % err}))
            return

        err = node_db.create_load("tcp", load, nodes)
        if err:
            ws.send(json.dumps({"type": "error", "data": "保存数据失败:%s" % err}))
            return json_response(False, "保存数据失败:%s" % err)
        ws.send(json.dumps({"type": "end", "data": "数据保存成功"}))
        return json_response(True, "负载配置创建成功")

    def modify_tcp_load(self, get):
        """
        @route /ws_modsoc/node/load/modify_http_load
        @param name str
        @param load_id int
        @param site_name str
        @param ps str
        @param http_config.proxy_next_upstream str
        @param http_config.http_alg str
        @param nodes.[].node_site str
        @param nodes.[].node_site_id int
        @param nodes.[].id int
        @param nodes.[].port int
        @param nodes.[].path str
        @param nodes.[].node_status str
        @param nodes.[].weight int
        @param nodes.[].node_id int
        @param nodes.[].max_conns int
        @param nodes.[].max_fail int
        @param nodes.[].fail_timeout int
        @param nodes.[].ps str
        @return ws {
            "type": str,
		    "data": str
        }
        """

        ws: simple_websocket.Server = getattr(get, '_ws', None)
        if not ws:
            return json_response(False, "请使用 WebSocket 连接")

        if get.get("load_id/d", 0) < 0:
            ws.send(json.dumps({"type": "error", "data": "负载ID不能为空"}))
            return

        load, err = LoadSite.bind_tcp_load(get)
        if err:
            ws.send(json.dumps({"type": "error", "data": "解析参数错误:%s" % err}))
            return

        if len(get.get("nodes", [])) <= 0:
            ws.send(json.dumps({"type": "error", "data": "负载ID不能为空"}))
            return

        nodes: List[TcpNode] = []
        for node_data in get.get("nodes", []):
            node, err = TcpNode.bind(node_data)
            if err:
                ws.send(json.dumps({"type": "error", "data": "解析参数错误:%s" % err}))
                return
            nodes.append(node)

        if not nodes:
            ws.send(json.dumps({"type": "error", "data": "节点不能为空"}))
            return

        node_db = NodeDB()
        if not node_db.load_id_exist(load.load_id):
            ws.send(json.dumps({"type": "error", "data": "未找到该负载配置"}))
            return

        log_call = lambda x: ws.send(json.dumps({"type": "log", "data": x}))
        err = load_check.check_tcp_load_data(load, log_call)
        if err:
            ws.send(json.dumps({"type": "error", "data": err}))
            return
        for n in nodes:
            if load.tcp_config["type"] == "tcp":
                err = load_check.check_tcp_node(n, log_call)
                if err:
                    ws.send(json.dumps({"type": "error", "data": err}))
                    return

        log_call("生成配置文件...")
        cgr = config_generator.NginxConfigGenerator()
        err = cgr.save_configs(load, nodes)
        if err:
            ws.send(json.dumps({"type": "error", "data": "生成配置文件失败:%s" % err}))
            return

        err = node_db.update_load("tcp", load, nodes)
        if err:
            ws.send(json.dumps({"type": "error", "data": "保存数据失败:%s" % err}))
            return
        ws.send(json.dumps({"type": "success", "data": "数据保存成功"}))
        return json_response(True, "负载配置更新成功")

    def check_tcp_node(self, get):
        """
        @route /ws_modsoc/node/load/check_tcp_node
        @param type str
        @param host str
        @param port int
        @param node_status str
        @param weight int
        @param max_fail int
        @param fail_timeout int
        @param ps str
        @return ws {
            "type": str,
            "data": str
        }
        """
        ws: simple_websocket.Server = getattr(get, '_ws', None)
        if not ws:
            return json_response(False, "请使用 WebSocket 连接")
        node, err = TcpNode.bind(get)
        if err:
            ws.send(json.dumps({"type": "error", "data": "解析参数错误:%s" % err}))
            return

        log_call = lambda x: ws.send(json.dumps({"type": "log", "data": x}))
        err = load_check.check_tcp_node(node, log_call)
        if err:
            ws.send(json.dumps({"type": "error", "data": err}))
            return
        ws.send(json.dumps({"type": "end", "data": "测试连接成功"}))
        return json_response(True, "测试连接成功")

    def remove_tcp_load(self, get):
        """
        @route /mod/node/load/delete_http_load
        @param load_id int
        @param {
            "type": str,
		    "data": str
        }
        """

        load_id = get.get("load_id/d", 0)
        if load_id <= 0:
            return json_response(False, "负载ID不能为空")
        node_db = NodeDB()
        load, err = node_db.get_load(load_id)
        if err:
            return json_response(False, "未找到该负载配置")
        load["http_config"] = json.loads(load["http_config"])
        load["tcp_config"] = json.loads(load["tcp_config"])
        load, err = LoadSite.bind_tcp_load(load)
        if err:
            return json_response(False, "解析参数错误:%s" % err)
        err = node_db.delete(load_id)
        if err:
            return json_response(False, "删除失败:%s" % err)
        cgr = config_generator.NginxConfigGenerator()

        cgr.delete_node_conf(load)

        return json_response(True, "删除成功")

    def multi_remove_tcp_load(self, get):
        load_ids = get.get("load_ids/s", '')
        try:
            load_ids = json.loads(load_ids)
            load_ids = [int(i) for i in load_ids]
        except:
            return json_response(False, "参数格式错误")

        node_db = NodeDB()
        for load_id in load_ids:
            load, err = node_db.get_load(load_id)
            if err:
                return json_response(False, "未找到该负载配置")
            load["http_config"] = json.loads(load["http_config"])
            load["tcp_config"] = json.loads(load["tcp_config"])
            load, err = LoadSite.bind_tcp_load(load)
            if err:
                return json_response(False, "解析参数错误:%s" % err)
            err = node_db.delete(load_id)
            if err:
                return json_response(False, "删除失败:%s" % err)
            cgr = config_generator.NginxConfigGenerator()

            cgr.delete_node_conf(load, mutil=True)

        NginxUtils.reload_nginx()
        return json_response(True, "删除成功")


    def tcp_load_list(self, get):
        """
        @route /mod/node/load/http_load_list
        @param page int
        @param page_size int
        @return {
            "page": str,
            "data": [
                {
                    "load_id": int,
                    "name": str,
                    "site_id": int,
                    "site_name": str,
                    "ps": str,
                    "http_config": {
                        "proxy_next_upstream": str,
                        "http_alg": str
                    },
                    "created_at": int,
                    "request": int,
                    "error": int,
                    "qps": int,
                    "upstream_time": int,
                    "last_request_time": str,
                    "nodes": [
                        {
                            "id": int,
                            "request": int,
                            "error": int,
                            "qps": int,
                            "upstream_time":  int,
                            "last_request": str,
                            "load_id": int,
                            "node_site": str,
                            "node_site_id": int,
                            "port": int,
                            "path": str,
                            "node_status": str,
                            "weight": int,
                            "max_fail": int,
                            "node_id": int,
                            "max_conns": int,
                            "ps": str,
                            "created_at": int,
                            "fail_timeout": int
                        }
                    ]
                }
            ]
        }
        """
        node_db = NodeDB()
        page = max(get.get("page/d", 1), 1)
        page_size = max(get.get("page_size/d", 10), 1)
        search = get.get('search/s', "").strip()
        count = node_db.loads_count("tcp", search)
        loads = node_db.loads_list("tcp", (page - 1) * page_size, page_size, search)
        err = ""
        for load in loads:
            la = get_log_analyze("tcp", load["name"], interval=60)
            load["nodes"], tmp_err = node_db.get_nodes(load["load_id"], load["site_type"])
            if tmp_err:
                err = tmp_err
                continue
            la.analyze_logs()
            day_status = la.get_today_stats()
            load.update(day_status.get("total"))
            load["http_config"] = json.loads(load["http_config"])
            load["tcp_config"] = json.loads(load["tcp_config"])
            for node in load["nodes"]:
                tmp_status = day_status["nodes"].get(node["host"] + ":" + str(node["port"]))
                if not tmp_status:
                    tmp_status = {'requests': 0, 'errors': 0, 'max_response_time': 0,
                                  'max_upstream_time': 0, 'last_update': 0, 'qps': 0}
                node.update(tmp_status)
        data = public.get_page(count,page,page_size)
        data["data"] = loads
        data["err_info"] = err
        return data

    def tcp_log(self, get):
        """
        @route /mod/node/load/log
        @param load_id int
        @param date str
        @return {
            "time": str,
            "client_ip": str,
            "method": str,
            "node": str,
            "upstream_time": int,
            "bytes_sent": int,
            "body_sent": int,
            "status": int,
            "uri": str
        }
        """

        load_id = get.get("load_id/d", 0)
        date = get.get("date", "")
        position = get.get("position/d", -1)
        limit = get.get("limit/d", 16)
        if not load_id:
            return json_response(False, "参数错误")
        node_db = NodeDB()
        load, err = node_db.get_load(load_id)
        if err:
            return json_response(False, "未找到该负载配置")
        la = get_log_analyze("tcp", load["name"], date=date, interval=60)
        last_position, data_list = la.get_log(position, limit)
        return json_response(True, "获取成功", data={
            "last_position": last_position,
            "logs": data_list
        })

    def export_tcp_log(self, get):
        """
        @route /mod/node/load/export_log
        @param load_id int
        @param date str
        @return {
            "status": bool,
            "filename": str
        }
        """

        load_id = get.get("load_id/d", 0)
        date = get.get("date", "")
        if not load_id:
            return json_response(False, "参数错误")
        node_db = NodeDB()
        load, err = node_db.get_load(load_id)
        if err:
            return json_response(False, "未找到该负载配置")

        la = get_log_file("tcp", load["name"], date=date)
        return {
            "status": True,
            "filename": la
        }