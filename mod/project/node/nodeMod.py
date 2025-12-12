import json
import os.path
import threading
import traceback
import public
from mod.base import json_response
from mod.base.ssh_executor import test_ssh_config
from mod.project.node.nodeutil import ServerNode, LocalNode, monitor_node_once_with_timeout
from mod.project.node.dbutil import Node, ServerNodeDB, ServerMonitorRepo
from mod.project.node.task_flow import flow_useful_version


class main():
    def __init__(self):
        self.tip_file = public.get_panel_path() + "/data/mod_node_used.pl"
        self.show_mode_file = public.get_panel_path() + "/data/mod_node_show_mode.pl"

    def add_node(self, get):
        """
        增加节点
        :param get: address节点地址 api_key节点API Key remarks节点备注 category_id节点分类ID
        :return:
        """
        ssh_conf = get.get('ssh_conf', "{}")
        try:
            get.ssh_conf = json.loads(ssh_conf)
        except Exception:
            return json_response(False, msg="ssh_conf数据格式错误")
        n, err = Node.from_dict(get)
        if not n:
            return json_response(False, msg=err)
        public.set_module_logs("nodes_node_adds_9", "add_node")
        if n.app_key or n.api_key:
            err = ServerNode.check_api_key(n)
            if err:
                return json_response(False, msg=err)
        else:
            # ssh 节点，不用处理
            pass

        n.server_ip = n.parse_server_ip()
        err = ServerNodeDB().create_node(n)
        if err:
            return json_response(False, msg=err)
        node = ServerNodeDB().get_node_by_id(n.id)
        if node:
            monitor_node_once_with_timeout(node)
        return json_response(True, msg="节点添加成功")

    @staticmethod
    def bind_app(get):
        n, err = Node.from_dict(get)
        if not n:
            return json_response(False, msg=err)
        if not n.app_key:
            return json_response(False, msg="请指定要绑定的app秘钥")
        srv = ServerNode("", "", n.app_key)
        res = srv.app_bind()
        if res:
            return json_response(False, msg=res)
        else:
            return json_response(True, msg="绑定请求已发出")

    @staticmethod
    def bind_app_status(get):
        n, err = Node.from_dict(get)
        if not n:
            return json_response(False, msg=err)
        if not n.app_key:
            return json_response(False, msg="请指定要绑定的app秘钥")
        srv = ServerNode("", "", n.app_key)
        res = srv.app_bind_status()
        if res:
            return json_response(False, msg=res)
        else:
            return json_response(True, msg="绑定成功")


    def del_node(self, get):
        """
        删除节点
        :param get: ids节点ID
        :return:
        """
        node_ids = get.get('ids', "")
        if not node_ids:
            return public.returnMsg(False, "节点ID不能为空,至少为一个")
        try:
            node_ids = json.loads(node_ids)
            if not isinstance(node_ids, list) and isinstance(node_ids, int):
                node_ids = [node_ids]
        except Exception:
            return public.returnMsg(False, "传入的节点ID数据格式错误")

        srv_db = ServerNodeDB()
        for node_id in node_ids:
            if srv_db.is_local_node(node_id):
                continue
            err = srv_db.delete_node(node_id)
            if err:
                return json_response(False, msg=err)
        return json_response(True, msg="节点删除成功")

    def update_node(self, get):
        """
        更新节点
        :param get: id节点ID address节点地址 api_key节点API Key remarks节点备注 category_id节点分类ID
        :return:
        """
        node_id = get.get('id/d', 0)
        ssh_conf = get.get('ssh_conf', "{}")
        try:
            get.ssh_conf = json.loads(ssh_conf)
        except Exception:
            return json_response(False, msg="ssh_conf数据格式错误")
        if not node_id:
            return json_response(False, "节点ID不能为空")
        n, err = Node.from_dict(get)
        if not n:
            return json_response(False, msg=err)
        if n.app_key or n.api_key:
            err = ServerNode.check_api_key(n)
            if err:
                return json_response(False, msg=err)

        n.server_ip = n.parse_server_ip()
        srv_db = ServerNodeDB()
        err = srv_db.update_node(n, with_out_fields=["id", "status", "error", "error_num"])
        if err:
            return json_response(False, msg=err)
        node = ServerNodeDB().get_node_by_id(n.id)
        if node:
            monitor_node_once_with_timeout(node)
        return json_response(True, "节点更新成功")

    def default_show_mode(self) -> str:
        if not os.path.exists(self.show_mode_file):
            return "list"
        show_mode = public.readFile(self.show_mode_file)
        if not show_mode:
            return "list"
        if show_mode not in ["list", "block"]:
            return "list"
        return show_mode

    def set_show_mode(self, mode_name: str):
        if mode_name not in ["list", "block"]:
            return False
        if mode_name == "block":
            public.set_module_logs("node_show_block", "node_show_block")
        public.writeFile(self.show_mode_file, mode_name)
        return True

    def get_node_list(self, get):
        """
        获取节点列表
        :param get: p页码 limit每页数量 search搜索关键字 category_id分类ID
        :return:
        """
        page_num = max(int(get.get('p/d', 1)), 1)
        limit = max(int(get.get('limit/d', 10)), 10)
        search = get.get('search', "").strip()
        category_id = get.get('category_id/d', -1)
        refresh = get.get('refresh/s', "")
        show_mode = get.get('show_mode/s', "")
        if not show_mode or show_mode not in ["list", "block"]:
            show_mode = self.default_show_mode()
        else:
            if not self.set_show_mode(show_mode):
                show_mode = self.default_show_mode()

        if show_mode == "block": # 返回所有数据
            page_num = 1
            limit = 9999999

        srv_db = ServerNodeDB()
        data, err = srv_db.get_node_list(search, category_id, (page_num - 1) * limit, limit)
        if err:
            return json_response(False, msg=err)

        if refresh and refresh == "1":
            th_list = []
            for node in data:
                th = threading.Thread(target=monitor_node_once_with_timeout, args=(node,5))
                th.start()
                th_list.append(th)

            for th in th_list:
                th.join()

        for node in data:
            if isinstance(node["ssh_conf"], str):
                node["ssh_conf"] = json.loads(node["ssh_conf"])
            if isinstance(node["error"], str):
                node["error"] = json.loads(node["error"])
            if node["app_key"] == "local" and node["api_key"] == "local":
                node["address"] = public.getPanelAddr()
            if node["lpver"] and not node["remarks"].endswith(" | 1Panel"):
                node["remarks"] = node["remarks"] + " | 1Panel"
            node_data = self.get_node_data(node)
            node['data'] = node_data
        count = srv_db.node_count(search, category_id)
        page = public.get_page(count, page_num, limit)
        page["data"] = data
        page["show_mode"] = show_mode
        return page

    @staticmethod
    def get_node_data(node: dict):
        if node["app_key"] == "local" and node["api_key"] == "local":
            data = ServerMonitorRepo.get_local_server_status()
        else:
            srv_m = ServerMonitorRepo()
            if srv_m.is_reboot_wait(node["server_ip"]):
                return {'status': 4, 'msg': "服务器重启中..."}
            data = srv_m.get_server_status(node['id'])
        if data:
            cpu_data = data.get('cpu', {})
            memory_data = data.get('mem', {})
            if cpu_data and memory_data:
                return {
                    'status': 0,
                    'cpu': cpu_data[0],
                    'cpu_usage': cpu_data[1],
                    'memory': round(float(memory_data['memRealUsed']) / float(memory_data['memTotal']) * 100, 2),
                    'mem_usage': memory_data['memRealUsed'],
                    'memNewTotal': memory_data.get('memNewTotal', "") or public.to_size(
                        memory_data['memTotal'] * 1024 * 1024)
                }
        return {'status': 2, 'msg': "获取节点数据失败"}

    def add_category(self, get):
        """
        添加分类
        :param get:
        :return:
        """
        name = get.get('name', "").strip()
        srv_db = ServerNodeDB()
        if not name:
            return json_response(False, "分类名称不能为空")
        if srv_db.category_exites(name):
            return json_response(False, "分类名称已存在")
        err = srv_db.create_category(name)
        if err:
            return json_response(False, err)
        return json_response(True, "分类添加成功")

    def del_category(self, get):
        """
        删除分类
        :param get:
        :return:
        """
        category_id = get.get('id/d', 0)
        if not category_id:
            return json_response(False, "分类ID不能为空")
        srv_db = ServerNodeDB()
        if srv_db.category_exites(category_id):
            srv_db.delete_category(category_id)

        return json_response(True, "分类删除成功")

    def bind_node_to_category(self, get):
        """
        绑定节点到分类  可以批量绑定
        :param get: 如果传入单个node_id则是绑定单个，如果是传入列表则批量绑定
        :return:
        """
        node_ids = get.get('ids', "")
        category_id = get.get('category_id/d', 0)
        try:
            node_ids = json.loads(node_ids)
            if not isinstance(node_ids, list) and isinstance(node_ids, int):
                node_ids = [node_ids]
        except Exception:
            return json_response(False, "节点ID格式错误")

        if not node_ids:
            return json_response(False, "节点ID不能为空,至少为一")

        if category_id < 0:
            return json_response(False, "分类ID不能为空")

        srv_db = ServerNodeDB()
        err = srv_db.bind_category_to_node(node_ids, category_id)
        if err:
            return json_response(False, err)
        return json_response(True, "节点分组修改成功")

    def get_category_list(self, get):
        """
        获取分类列表
        :param get:
        :return:
        """
        try:
            categorys = public.M('category').select()
            return public.returnMsg(True, categorys)
        except Exception:
            public.print_log(traceback.print_exc())
            return json_response(False, "数据查询失败")

    @staticmethod
    def get_panel_url(get):
        """
        获取目标面板的访问url
        :param get: address节点地址 api_key节点API Key
        :return:
        """
        node_id = get.get('node_id/d', 0)
        if not node_id:
            return json_response(False, "node_id不能为空")
        srv = ServerNode.new_by_id(node_id)
        if not srv:
            return json_response(False, "node_id不存在")
        token, err = srv.get_tmp_token()
        if err:
            return public.returnResult(False, err)
        target_panel_url = srv.origin + "/login?tmp_token=" + token
        return json_response(True, data={'target_panel_url': target_panel_url})

    @classmethod
    def get_all_node(cls, get):
        """
        @route /mod/node/node/get_all_node
        @param query: str
        @return: [
            {
                "node_id": int,
                "remarks": str,
                "ip": str,
            }
        ]
        """
        query_type = get.get('node_type/s', "api")
        field_str = "id,remarks,server_ip,address,app_key,api_key,lpver,category_id,error_num,ssh_conf"
        if query_type == "api":
            data = public.M('node').where("app_key != '' or api_key != ''", ()).field(field_str).select()
        elif query_type == "ssh":
            data = public.M('node').field(field_str).where("ssh_conf != '{}'", ()).select()
        elif query_type == "file_src":
            data = public.M('node').field(field_str).where(
                "(app_key != '' or api_key != '') and lpver = ''", ()).select()
        else:  # all 除本机之外的节点
            data = public.M('node').where("api_key != 'local'", ()).field(field_str).select()

        srv_cache = ServerMonitorRepo()
        for i in data:
            i["has_ssh"] = bool(json.loads(i["ssh_conf"]))
            i.pop("ssh_conf")
            i["is_local"] = (i["app_key"] == "local" and i["api_key"] == "local")
            i.pop("app_key")
            i.pop("api_key")
            if i["server_ip"] == "":
                server_ip = ServerNode.get_node_ip(i['id'])
                if server_ip:
                    i["server_ip"] = server_ip
            if i["lpver"] and not i["remarks"].endswith(" | 1Panel"):
                i["remarks"] = i["remarks"] + " | 1Panel"

            tmp_data = srv_cache.get_server_status(i['id'])
            tmp_data = tmp_data or {}
            if query_type == "file_src":
                if not tmp_data and not i["is_local"]:
                    i["version"] = ""
                    i["useful_version"] = True
                    continue
                if not i["is_local"] or not flow_useful_version(tmp_data.get('version', "")):
                    continue
            else:
                if not tmp_data:
                    i["version"] = ""
                    i["useful_version"] = True
                    continue
            i['version'] = tmp_data.get('version', "")
            i['useful_version'] = cls._useful_version(i['version'])

        return json_response(True, "获取成功", data)

    @staticmethod
    def _useful_version(ver: str):
        try:
            if ver == "1Panel":
                return True
            ver_list = [int(i) for i in ver.split(".")]
            if ver_list[0] >= 10:
                return True
            elif ver_list[0] == 9 and ver_list[1] >= 7:
                return True
        except:
            pass
        return False

    @staticmethod
    def get_node_sites(get):
        """
        @route /mod/node/node/get_node_sites
        @param node_id: int
        @param query: str
        @return: [
            {
                "node_id": int,
                "site_id": int,
                "site_name": str,
                "site_port": int
            }
        ]
        """
        node_id = get.get('node_id/d', 0)
        if not node_id:
            return json_response(False, "node_id不能为空")
        srv = ServerNode.new_by_id(node_id)
        if not srv:
            return json_response(False, "node_id不存在")
        data_list, err = srv.php_site_list()
        if err:
            return json_response(False, err)
        return json_response(True, "获取成功", data_list)

    @staticmethod
    def php_site_list(get):
        """
        @route /mod/node/node/php_site_list
        @return: [
            {
                "site_id": int,
                "site_name": str,
                "ports": []int,
                "domains": []str,
                "ssl":bool
            }
        ]
        """
        return LocalNode().php_site_list()[0]

    def node_used_status(self, get):
        if os.path.exists(self.tip_file):
            return json_response(True, "已使用")
        return json_response(False, "未使用")

    def set_used_status(self, get):
        if os.path.exists(self.tip_file):
            os.remove(self.tip_file)
        else:
            public.set_module_logs("nodes_installed_9", "set_used_status")
            public.writeFile(self.tip_file, "True")
        return json_response(True, "设置成功")


    @staticmethod
    def remove_ssh_conf(get):
        node_id = get.get("node_id/d", 0)
        ServerNodeDB().remove_node_ssh_conf(node_id)
        return json_response(True, "删除成功")

    @staticmethod
    def set_ssh_conf(get):
        """设置ssh配置信息"""
        host = get.get("host/s", "")
        port = get.get("port/d", 22)
        username = get.get("username/s", "root")
        password = get.get("password/s", "")
        pkey = get.get("pkey/s", "")
        pkey_passwd = get.get("pkey_passwd/s", "")
        node_id = get.get("node_id/d", 0)
        test_case = get.get("test_case/d", 0)

        if not node_id and not test_case:
            return json_response(False, "节点不存在")

        if not host and node_id:
            host = ServerNode.get_node_ip(node_id)
        if not username:
            username = "root"
        if not host or not username or not port:
            return json_response(False, "主机IP、主机端口、用户名称不能为空")
        if not password and not pkey:
            return json_response(False, "密码或密钥不能为空")

        res = test_ssh_config(host, port, username, password, pkey, pkey_passwd)
        if res:
            return json_response(False, res)
        if test_case:
            return json_response(True, "测试成功")
        ServerNodeDB().set_node_ssh_conf(node_id, {
            "host": host,
            "port": port,
            "username": username,
            "password": password,
            "pkey": pkey,
            "pkey_passwd": pkey_passwd
        })
        return json_response(True, "设置成功")

    @staticmethod
    def get_sshd_port(get):
        node_id = get.get("node_id/d", 0)
        srv = ServerNode.new_by_id(node_id)
        if not srv:
            return json_response(False, "节点不存在")

        port = srv.get_sshd_port()
        if not port:
            port = 22
        return json_response(True, "获取成功", data={"port": port})


    @staticmethod
    def restart_bt_panel(get):
        node_id = get.get("node_id/d", 0)
        srv = ServerNode.new_by_id(node_id)
        if not srv:
            return json_response(False, "节点不存在")
        if srv.is_local:
            return json_response(False, "本地节点不支持此操作")
        ret = srv.restart_bt_panel()
        return json_response(ret.get("status"), ret.get("msg"))


    @staticmethod
    def server_reboot(get):
        node_id = get.get("node_id/d", 0)
        srv = ServerNode.new_by_id(node_id)
        if not srv:
            return json_response(False, "节点不存在")
        if srv.is_local:
            return json_response(False, "本地节点不支持此操作")
        repo = ServerMonitorRepo()
        if repo.is_reboot_wait(srv.node_server_ip):
            return json_response(False, "节点正在重启中，请稍后再试")
        ret = srv.server_reboot()
        return json_response(ret.get("status"), ret.get("msg"))