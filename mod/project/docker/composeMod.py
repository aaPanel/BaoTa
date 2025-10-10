# coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author: wzz <wzz@bt.cn>
# -------------------------------------------------------------------
# ------------------------------
# docker模型 - docker compose
# ------------------------------
import json
import os
import sys
import time

if "/www/server/panel/class" not in sys.path:
    sys.path.insert(0, "/www/server/panel/class")
import public

os.chdir("/www/server/panel")

if "/www/server/panel" not in sys.path:
    sys.path.insert(0, "/www/server/panel")
from mod.project.docker.docker_compose.base import Compose


# 2024/6/25 下午2:16 检查相同传参的装饰器
def check_file(func):
    '''
        @name 检查相同传参的装饰器
        @author wzz <2024/6/25 下午2:30>
        @param get.path : 传docker-compose.yaml的绝对路劲;
                get.def_name : 传需要使用的函数名，如get_log
        @return dict{"status":True/False,"msg":"提示信息"}
    '''

    def wrapper(self, get, *args, **kwargs):
        try:
            get.path = get.get("path/s", None)
            if get.path is None:
                get._ws.send(json.dumps(self.wsResult(False, "path参数不能为空", code=1)))
                return

            if not os.path.exists(get.path):
                get._ws.send(
                    json.dumps(self.wsResult(False, "[{}] 文件不存在".format(get.path), code=2)))
                return

            func(self, get, *args, **kwargs)

            if get.def_name in ("create", "up", "update", "start", "stop", "restart","rebuild"):
                get._ws.send(
                    json.dumps(self.wsResult(True, " {}完成，如日志无异常再关闭此窗口！\r\n".format(get.option), data=-1, code=-1)))
        except Exception as e:
            return

    return wrapper


class main(Compose):

    def __init__(self):
        super(main, self).__init__()

    # 2024/6/25 下午2:41 执行docker-compose命令获取实时输出 
    def exec_cmd(self, get, command):
        '''
            @name 执行docker-compose命令获取实时输出
            @author wzz <2024/6/25 下午2:41>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        if self.def_name is None: self.set_def_name(get.def_name)
        import pty

        try:
            def read_output(fd, ws):
                while True:
                    output = os.read(fd, 1024)
                    if not output:
                        break

                    if hasattr(get, '_ws'):
                        ws.send(json.dumps(self.wsResult(
                            True,
                            output.decode(),
                        )))

            pid, fd = pty.fork()
            if pid == 0:
                os.execvp(command[0], command)
            else:
                read_output(fd, get._ws)
        except:
            if self.def_name in ("get_logs", "get_project_container_logs"):
                if hasattr(get, '_ws'):
                    get._ws.send(json.dumps(self.wsResult(
                        True,
                        "",
                    )))
            return

    # 2024/6/25 下午2:44 更新指定docker-compose里面的镜像
    @check_file
    def update(self, get):
        '''
            @name 更新指定docker-compose里面的镜像
            @param get
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        get.option = "更新"
        if hasattr(get, '_ws'):
            get._ws.send(json.dumps(self.wsResult(
                True,
                "",
            )))
        command = self.set_type(1).set_path(get.path).get_compose_pull()
        self.status_exec_logs(get, command)
        command = self.set_type(1).set_path(get.path).get_compose_up_remove_orphans()
        self.status_exec_logs(get, command)

    # 2024/6/28 下午2:19 重建指定docker-compose项目
    @check_file
    def rebuild(self, get):
        '''
            @name 重建指定docker-compose项目
            @param get
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        get.option = "重建"
        command = self.set_type(1).set_path(get.path).get_compose_down()
        self.exec_logs(get, command)
        command = self.set_type(1).set_path(get.path).get_compose_up_remove_orphans()
        self.exec_logs(get, command)

    # 2024/6/24 下午10:54 停止指定docker-compose项目
    @check_file
    def stop(self, get):
        '''
            @name 停止指定docker-compose项目
            @author wzz <2024/6/24 下午10:54>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        get.option = "停止"
        command = self.set_type(1).set_path(get.path).get_compose_stop()
        self.status_exec_logs(get, command)

    # 2024/6/24 下午10:54 启动指定docker-compose项目
    @check_file
    def start(self, get):
        '''
            @name 启动指定docker-compose项目
        '''
        get.option = "启动"
        command = self.set_type(1).set_path(get.path).get_compose_up_remove_orphans()
        self.status_exec_logs(get, command)

    # 2024/6/24 下午11:23 down指定docker-compose项目
    @check_file
    def down(self, get):
        '''
            @name 停止指定docker-compose项目，并删除容器、网络、镜像等
        '''
        get.option = "停止"
        command = self.set_type(1).set_path(get.path).get_compose_down()
        self.status_exec_logs(get, command)

    # 2024/6/24 下午11:23 部署指定docker-compose项目
    @check_file
    def up(self, get):
        '''
            @name 部署指定docker-compose项目
        '''
        get.option = "添加容器编排"
        command = self.set_type(1).set_path(get.path).get_compose_up_remove_orphans()
        self.status_exec_logs(get, command)

    # 2024/6/24 下午11:23 重启指定docker-compose项目
    @check_file
    def restart(self, get):
        '''
            @name 重启指定docker-compose项目
        '''
        get.option = "重启"
        command = self.set_type(1).set_path(get.path).get_compose_restart()
        # self.exec_logs(get, command)
        self.status_exec_logs(get, command)

    # 2024/6/26 下午4:28 获取docker-compose ls -a --format json
    def ls(self, get):
        '''
            @name 获取docker-compose ls -a --format json
        '''
        get.option = "获取编排列表"
        command = self.get_compose_ls()

        try:
            cmd_result = public.ExecShell(command)[0]
            if "Segmentation fault" in cmd_result:
                return []
            return json.loads(cmd_result)
        except:
            return []

    # 2024/6/26 下午8:38 获取指定compose.yaml的docker-compose ps
    def ps(self, get):
        '''
            @name 获取指定compose.yaml的docker-compose ps
            @author wzz <2024/6/26 下午8:38>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        get.path = get.get("path/s", None)
        if get.path is None:
            get._ws.send(json.dumps(self.wsResult(False, "path参数不能为空", code=1)))
            return self.wsResult(False, "path参数不能为空", code=1)

        if not os.path.exists(get.path):
            get._ws.send(
                json.dumps(self.wsResult(False, "[{}] 文件不存在".format(get.path), code=2)))
            return self.wsResult(False, "[{}] 文件不存在".format(get.path), code=1)

        get.option = "获取指定编排的容器信息"
        command = self.set_path(get.path, rep=True).get_compose_ps()

        try:
            cmd_result = public.ExecShell(command)[0]
            if "Segmentation fault" in cmd_result:
                return []

            if not cmd_result.startswith("["):
                return json.loads("[" + cmd_result.strip().replace("\n", ",") + "]")
            else:
                return json.loads(cmd_result.strip().replace("\n", ","))
        except:
            self.ps_count += 1
            if self.ps_count < 5:
                time.sleep(0.5)
                return self.ps(get)
            return []

    # 2024/6/24 下午10:53 获取指定docker-compose的运行日志
    @check_file
    def get_logs(self, get):
        '''
            @name websocket接口，执行docker-compose命令，返回结果：执行self.get_compose_logs()命令
            @param get
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        #每个compose容器获取10行日志
        self.set_tail("10")
        get.option = "读取日志"

        command = self.set_type(1).set_path(get.path).get_compose_logs()
        self.exec_logs(get, command)

    # 2024/6/26 下午9:24 获取指定compose.yaml的内容
    def get_config(self, get):
        '''
            @name 获取指定compose.yaml的内容
            @author wzz <2024/6/26 下午9:25>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        if self.def_name is None: self.set_def_name(get.def_name)
        get.path = get.get("path/s", None)
        if get.path is None:
            if hasattr(get, '_ws'):
                get._ws.send(json.dumps(self.wsResult(False, "path参数不能为空", code=1)))
            return

        if not os.path.exists(get.path):
            if hasattr(get, '_ws'):
                get._ws.send(
                    json.dumps(self.wsResult(False, "[{}] 文件不存在".format(get.path), code=2)))
            return

        try:
            config_body = public.readFile(get.path)
            # env_path = get.path.replace("docker-compose.yaml", ".env").replace("docker-compose.yml", ".env")
            # 获取文件路径  有些情况不是用标准文件名进行启动容器的
            file_path = os.path.dirname(get.path)
            env_path = os.path.join(file_path, ".env")
            # 判断路径下.env 文件是否存在
            env_body = public.readFile(env_path) if os.path.exists(env_path) else ""

            if hasattr(get, '_ws'):
                get._ws.send(json.dumps(self.wsResult(True, "获取成功", data={
                    "config": config_body if config_body else "",
                    "env": env_body if env_body else "",
                })))
            return
        except:
            if hasattr(get, '_ws'):
                get._ws.send(json.dumps(self.wsResult(False, "获取失败", data={}, code=3)))
            return

    # 2024/6/26 下午9:31 保存指定compose.yaml的内容
    def save_config(self, get):
        '''
            @name 保存指定compose.yaml的内容
            @param get
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        if self.def_name is None: self.set_def_name(get.def_name)
        get.path = get.get("path/s", None)
        get.config = get.get("config/s", None)
        get.env = get.get("env/s", None)
        if get.path is None:
            if hasattr(get, '_ws'):
                get._ws.send(json.dumps(self.wsResult(False, "path参数不能为空", code=1)))
            return

        if not os.path.exists(get.path):
            if hasattr(get, '_ws'):
                get._ws.send(
                    json.dumps(self.wsResult(False, "[{}] 文件不存在".format(get.path), code=2)))
            return

        if public.check_chinese(get.path):
            if hasattr(get, '_ws'):
                get._ws.send(json.dumps(self.wsResult(False, "文件路径不能包含中文！", code=3)))
            return

        if get.config is None:
            if hasattr(get, '_ws'):
                get._ws.send(json.dumps(self.wsResult(False, "config参数不能为空", code=3)))
            return

        if get.env is None:
            if hasattr(get, '_ws'):
                get._ws.send(json.dumps(self.wsResult(False, "env参数不能为空", code=3)))
            return

        try:
            stdout, stderr = self.check_config(get)
            if stderr:
                if hasattr(get, '_ws'):
                    get._ws.send(json.dumps(self.wsResult(
                        False,
                        "保存失败，请检查compose.yaml文件格式是否正确： 【{}】".format(stderr),
                        code=4,
                    )))
                return
            if "Segmentation fault" in stdout:
                if hasattr(get, '_ws'):
                    get._ws.send(json.dumps(self.wsResult(
                        False,
                        "保存失败，docker-compose 版本过低，请升级到最新版！",
                        code=4,
                    )))
                return

            public.writeFile(get.path, get.config)
            env_path = os.path.join(os.path.dirname(get.path), ".env")
            public.writeFile(env_path,get.env)

            # self.up(get)

            if hasattr(get, '_ws'):
                get._ws.send(json.dumps(self.wsResult(
                    True,
                    "保存成功",
                )))

            return
        except:
            if hasattr(get, '_ws'):
                get._ws.send(json.dumps(self.wsResult(
                    False,
                    "保存失败",
                )))
            return

    # 2024/6/27 上午10:25 检查compose内容是否正确
    def check_config(self, get):
        '''
            @name 检查compose内容是否正确
            @author wzz <2024/6/27 上午10:26>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        if not os.path.exists("/tmp/btdk"):
            os.makedirs("/tmp/btdk", 0o755, True)

        tmp_path = "/tmp/btdk/{}".format(os.path.basename(public.GetRandomString(10).lower()))
        public.writeFile(tmp_path, get.config)
        public.writeFile("/tmp/btdk/.env", get.env)
        command = self.set_path(tmp_path, rep=True).get_compose_config()

        stdout, stderr = public.ExecShell(command)
        if "`version` is obsolete" in stderr:
            public.ExecShell("sed -i '/version/d' {}".format(tmp_path))
            get.config = public.readFile(tmp_path)
            return self.check_config(get)

        public.ExecShell("rm -f {}".format(tmp_path))
        return stdout, stderr

    # 2024/6/27 上午10:06 根据内容创建docker-compose编排
    def create(self, get):
        '''
            @name 根据内容创建docker-compose编排
            @author wzz <2024/6/27 上午10:07>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        if self.def_name is None: self.set_def_name(get.def_name)
        get.project_name = get.get("project_name/s", None)
        if get.project_name is None:
            if hasattr(get, '_ws'):
                get._ws.send(json.dumps(self.wsResult(
                    False,
                    "project_name参数不能为空",
                    code=1,
                )))
            return

        get.config = get.get("config/s", None)
        if get.config is None:
            if hasattr(get, '_ws'):
                get._ws.send(json.dumps(self.wsResult(
                    False,
                    "config参数不能为空",
                    code=2,
                )))
            return

        stdout, stderr = self.check_config(get)
        if stderr:
            if hasattr(get, '_ws'):
                get._ws.send(json.dumps(self.wsResult(
                    False,
                    "创建失败，请检查compose.yaml文件格式是否正确：\r\n{}".format(stderr.replace("\n", "\r\n")),
                    code=4,
                )))
            return
        if "Segmentation fault" in stdout:
            if hasattr(get, '_ws'):
                get._ws.send(json.dumps(self.wsResult(
                    False,
                    "创建失败，docker-compose 版本过低，请升级到最新版！",
                    code=4,
                )))
            return
        # 2024/2/20 下午 3:21 如果检测到是中文的compose，则自动转换为英文
        config_path = "{}/config/name_map.json".format(public.get_panel_path())
        try:
            name_map = json.loads(public.readFile(config_path))
            import re
            if re.findall(r"[\u4e00-\u9fa5]", get.project_name):
                name_str = 'bt_compose_' + public.GetRandomString(10).lower()
                name_map[name_str] = get.project_name
                get.project_name = name_str
                public.writeFile(config_path, json.dumps(name_map))
        except:
            pass

        if not os.path.exists(self.compose_project_path): os.makedirs(self.compose_project_path, 0o755, True)
        if not os.path.exists(os.path.join(self.compose_project_path, get.project_name)):
            os.makedirs(os.path.join(self.compose_project_path, get.project_name), 0o755, True)

        get.path = os.path.join(self.compose_project_path, "{}/docker-compose.yaml".format(get.project_name))

        public.writeFile(get.path, get.config)
        public.writeFile(get.path.replace("docker-compose.yaml", ".env").replace("docker-compose.yml", ".env"), get.env)

        get.add_template = get.get("add_template/d", 0)
        template_id = None
        from btdockerModel import dk_public as dp
        if get.add_template == 1:
            get.template_name = get.get("template_name/s", None)
            if get.template_name is None:
                if hasattr(get, '_ws'):
                    get._ws.send(json.dumps(self.wsResult(
                        False,
                        "template_name参数不能为空",
                        code=1,
                    )))
                return

            from btdockerModel import composeModel as cm
            template_list = cm.main().template_list(get)
            for template in template_list:
                if get.template_name == template['name']:
                    if hasattr(get, '_ws'):
                        get._ws.send(json.dumps(self.wsResult(
                            False,
                            "模板名称已存在，请删除模板后再添加！",
                            code=2,
                        )))
                    return

            #添加编排模板 ---------- 可以直接引用composeModel.add_template
            template_path = os.path.join(self.compose_project_path, "{}".format(get.template_name))
            compose_path = os.path.join(template_path,"docker-compose.yaml")
            env_path = os.path.join(template_path,".env")
            pdata = {
                "name": get.template_name,
                "remark": "",
                "path": template_path,
                "add_in_path":1
            }
            template_id = dp.sql("templates").insert(pdata)
            if not os.path.exists(template_path):
                os.makedirs(template_path, 0o755, True)
            public.writeFile(compose_path, get.config)
            public.writeFile(env_path,get.env)

        get.remark = get.get("remark/s", "")
        stacks_info = dp.sql("stacks").where("name=?", (public.xsssec(get.project_name))).find()
        if not stacks_info:
            pdata = {
                "name": public.xsssec(get.project_name),
                "status": "1",
                "path": get.path,
                "template_id": template_id,
                "time": time.time(),
                "remark": public.xsssec(get.remark)
            }
            dp.sql("stacks").insert(pdata)
        else:
            check_status = public.ExecShell("docker-compose ls |grep {}".format(get.path))[0]
            if not check_status:
                dp.sql("stacks").where("name=?", (public.xsssec(get.project_name))).delete()
            else:
                if hasattr(get, '_ws'):
                    get._ws.send(json.dumps(self.wsResult(
                        False,
                        "项目名已经存在，请先删除后再添加!",
                        code=3,
                    )))
                return

        self.up(get)

    # 2024/6/27 上午11:42 删除指定compose.yaml的docker-compose编排
    def delete(self, get):
        '''
            @name 删除指定compose.yaml的docker-compose编排
            @author wzz <2024/6/27 上午11:42>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        if self.def_name is None: self.set_def_name(get.def_name)
        get.project_name = get.get("project_name/s", None)
        if get.project_name is None:
            get._ws.send(json.dumps(self.wsResult(False, "project_name参数不能为空", code=1)))
            return

        get.path = get.get("path/s", None)
        if get.path is None:
            get._ws.send(json.dumps(self.wsResult(False, "path参数不能为空", code=1)))
            return

        from btdockerModel import dk_public as dp
        stacks_info = dp.sql("stacks").where("path=? or name=?", (get.path, get.project_name)).find()
        if stacks_info:
            dp.sql("stacks").where("path=? or name=?", (get.path, get.project_name)).delete()

        if "bt_compose_" in get.path:
            config_path = "{}/config/name_map.json".format(public.get_panel_path())
            name_map = json.loads(public.readFile(config_path))
            bt_compose_name = os.path.dirname(get.path).split("/")[-1]
            if bt_compose_name in name_map:
                name_map.pop(bt_compose_name)
                public.writeFile(config_path, json.dumps(name_map))

        stacks_list = dp.sql("stacks").select()
        compose_list = self.ls(get)
        for i in stacks_list:
            for j in compose_list:
                if i['name'] == j['Name']:
                    break

                if public.md5(i['name']) in j['Name']:
                    break
            else:
                dp.sql("stacks").where("name=?", (i['name'])).delete()

        if not os.path.exists(get.path):
            command = self.set_type(0).set_compose_name(get.project_name).get_compose_delete_for_ps()
        else:
            command = self.set_type(0).set_path(get.path).get_compose_delete()
        stdout, stderr = public.ExecShell(command)
        if "invalid compose project" in stderr:
            command = self.set_type(0).set_compose_name(get.project_name).get_compose_delete_for_ps()
            stdout, stderr = public.ExecShell(command)

        if stderr and "Error" in stderr:
            if hasattr(get, '_ws'):
                get._ws.send(json.dumps(self.wsResult(
                    False,
                    "删除失败，请检查compose.yaml文件格式是否正确：\r\n{}".format(stderr.replace("\n", "\r\n")),
                    data=-1,
                    code=4,
                )))
                return

        if hasattr(get, '_ws'):
            get._ws.send(json.dumps(self.wsResult(
                True,
                "删除容器编排",
                data=-1,
                code=0
            )))

    # 2024/6/27 下午8:39 批量删除指定compose.yaml的docker-compose编排
    def batch_delete(self, get):
        '''
            @name 批量删除指定compose.yaml的docker-compose编排
            @param get
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        if self.def_name is None: self.set_def_name(get.def_name)
        get.project_list = get.get("project_list", None)
        if get.project_list is None or len(get.project_list) == 0:
            return self.wsResult(False, "project_list参数不能为空", code=1)

        config_path = "{}/config/name_map.json".format(public.get_panel_path())
        try:
            name_map = json.loads(public.readFile(config_path))
        except:
            name_map = {}

        for project in get.project_list:
            if not isinstance(project, dict):
                if hasattr(get, '_ws'):
                    get._ws.send(json.dumps(self.wsResult(
                        False,
                        "project_list参数格式错误: {}".format(project),
                        code=1,
                    )))
                continue

            if project["project_name"] is None or project["project_name"] == "":
                get._ws.send(
                    json.dumps(self.wsResult(False, "project_name参数不能为空", code=1)))
                continue

            if project["path"] is None or project["path"] == "":
                get._ws.send(json.dumps(self.wsResult(False, "path参数不能为空", code=1)))
                continue

            from btdockerModel import dk_public as dp
            stacks_info = dp.sql("stacks").where("path=? or name=?", (project["path"], project["project_name"])).find()
            if stacks_info:
                dp.sql("stacks").where("path=? or name=?", (project["path"], project["project_name"])).delete()

            if "bt_compose_" in project["path"]:
                bt_compose_name = os.path.dirname(project["path"]).split("/")[-1]
                if bt_compose_name in name_map:
                    name_map.pop(bt_compose_name)

            if not os.path.exists(project["path"]):
                command = self.set_type(0).set_compose_name(project["project_name"]).get_compose_delete_for_ps()
            else:
                command = self.set_type(0).set_path(project["path"], rep=True).get_compose_delete()

            stdout, stderr = public.ExecShell(command)
            if "Segmentation fault" in stdout:
                if hasattr(get, '_ws'):
                    get._ws.send(json.dumps(self.wsResult(
                        False,
                        "删除失败，docker-compose 版本过低，请升级到最新版！",
                        code=4,
                    )))
                return

            # public.ExecShell("rm -rf {}".format(os.path.dirname(project["path"])))
            if hasattr(get, '_ws'):
                get._ws.send(json.dumps(self.wsResult(
                    True,
                    data={
                        "project_name": project["project_name"],
                        "status": True
                    }
                )))

        public.writeFile(config_path, json.dumps(name_map))
        if hasattr(get, '_ws'):
            get._ws.send(json.dumps(self.wsResult(True, data=-1)))

    # 2024/6/28 下午3:15 根据容器id获取指定容器的日志
    def get_project_container_logs(self, get):
        '''
            @name 根据容器id获取指定容器的日志
            @author wzz <2024/6/28 下午3:16>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        get.container_id = get.get("container_id/s", None)
        if get.container_id is None:
            return public.returnResult(False, "container_id参数不能为空", code=1)

        self.set_tail("200")
        self.set_container_id(get.container_id)
        command = self.get_container_logs()
        stdout, stderr = public.ExecShell(command)
        if "invalid compose project" in stderr:
            return public.returnResult(False, "容器不存在", code=2)

        return public.returnResult(True, stdout.replace("\n", "\r\n"), code=0)

    # 2024/7/18 上午10:13 修改指定项目备注
    def edit_remark(self, get):
        '''
            @name 修改指定项目备注
        '''
        get.name = get.get("name", None)
        get.remark = get.get("remark", "")
        if get.name is None:
            return public.returnResult(False, "缺少参数name!", code=2)
        old_remark = ""

        from btdockerModel import dk_public as dp
        stacks_info = dp.sql("stacks").where("name=?", (public.xsssec(get.name))).find()
        if not stacks_info:
            get.path = get.get("path", None)
            if get.path is None:
                return public.returnResult(False, "缺少参数path!", code=2)

            pdata = {
                "name": public.xsssec(get.name),
                "status": "1",
                "path": get.path,
                "template_id": None,
                "time": time.time(),
                "remark": public.xsssec(get.remark)
            }
            dp.sql("stacks").insert(pdata)
        else:
            old_remark = stacks_info['remark']
            dp.sql("stacks").where("name=?", (public.xsssec(get.name))).update({"remark": public.xsssec(get.remark)})

        dp.write_log("项目 [{}] 的备注修改成功 [{}] --> [{}]!".format(
            get.name,
            old_remark,
            public.xsssec(get.remark)))
        return public.returnResult(True, "修改成功!")
