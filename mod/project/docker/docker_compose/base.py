# coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author: wzz <wzz@bt.cn>
# -------------------------------------------------------------------
# ------------------------------
# docker模型 - docker compose 基类
# ------------------------------
import sys
from typing import List

if "/www/server/panel/class" not in sys.path:
    sys.path.insert(0, "/www/server/panel/class")

import public


class Compose():

    def __init__(self):
        self.cmd = 'docker-compose'
        self.path = None
        self.tail = "100"
        self.type = 0
        self.compose_name = None
        self.compose_project_path = "{}/data/compose".format(public.get_panel_path())
        self.grep_version = 'grep -v "\`version\` is obsolete"'
        self.def_name = None
        self.container_id = None
        self.ps_count = 0

    def set_container_id(self, container_id: str) -> 'Compose':
        self.container_id = container_id
        return self

    def get_cmd(self) -> str:
        return self.cmd

    def set_cmd(self, cmd: str) -> 'Compose':
        self.cmd = cmd
        return self

    def set_path(self, path: str, rep: bool = False) -> 'Compose':
        if rep:
            self.path = path.replace("\'", "\\'").replace("\"", "\\\"").replace(" ", "\\ ").replace("|", "\\|")
        else:
            self.path = path
        return self

    def set_tail(self, tail: str) -> 'Compose':
        self.tail = tail
        return self

    def set_type(self, type: int) -> 'Compose':
        self.type = type
        return self

    def set_compose_name(self, compose_name: str) -> 'Compose':
        self.compose_name = compose_name
        return self

    def set_def_name(self, def_name: str) -> 'Compose':
        self.def_name = def_name
        return self

    def get_compose_up(self) -> List[str] or str:
        return self.cmd + ' -f {} up -d| {}'.format(self.path, self.grep_version)

    def get_compose_up_remove_orphans(self) -> List[str] or str:
        if self.type == 0:
            return self.cmd + ' -f {} up -d --remove-orphans'.format(self.path)
        else:
            return [self.cmd, '-f', self.path, 'up', '-d', '--remove-orphans']

    def get_compose_down(self) -> List[str] or str:
        if self.type == 0:
            return self.cmd + ' -f {} down'.format(self.path)
        else:
            return [self.cmd, '-f', self.path, 'down']

    def kill_compose(self) -> List[str] or str:
        if self.type == 0:
            return self.cmd + ' -f {} kill'.format(self.path)
        else:
            return [self.cmd, '-f', self.path, 'kill']

    def rm_compose(self) -> List[str] or str:
        if self.type == 0:
            return self.cmd + ' -f {} rm -f'.format(self.path)
        else:
            return [self.cmd, '-f', self.path, 'rm', '-f']

    def get_compose_delete(self) -> List[str] or str:
        if self.type == 0:
            return self.cmd + ' -f {} down --volumes --remove-orphans'.format(self.path)
        else:
            return [self.cmd, '-f', self.path, 'down', '--volumes', '--remove-orphans']

    def get_compose_delete_for_ps(self) -> List[str] or str:
        if self.type == 0:
            return self.cmd + ' -p {} down --volumes --remove-orphans'.format(self.compose_name)
        else:
            return [self.cmd, '-p', self.compose_name, 'down', '--volumes', '--remove-orphans']

    def get_compose_restart(self) -> List[str] or str:
        if self.type == 0:
            return self.cmd + ' -f {} restart'.format(self.path)
        else:
            return [self.cmd, '-f', self.path, 'restart']

    def get_compose_stop(self) -> List[str] or str:
        if self.type == 0:
            return self.cmd + ' -f {} stop'.format(self.path)
        else:
            return [self.cmd, '-f', self.path, 'stop']

    def get_compose_start(self) -> List[str] or str:
        if self.type == 0:
            return self.cmd + ' -f {} start'.format(self.path)
        else:
            return [self.cmd, '-f', self.path, 'start']

    def get_compose_pull(self) -> List[str] or str:
        if self.type == 0:
            return self.cmd + ' -f {} pull'.format(self.path)
        else:
            return [self.cmd, '-f', self.path, 'pull']

    def get_compose_logs(self) -> List[str] or str:
        if self.type == 0:
            return self.cmd + ' -f {} logs -f --tail {}'.format(self.path, self.tail)
        else:
            return [self.cmd, '-f', self.path, 'logs', '-f', '--tail', self.tail]

    def get_tail_compose_log(self) -> List[str] or str:
        if self.type == 0:
            return self.cmd + ' -f {} logs --tail {}'.format(self.path, self.tail)
        else:
            return [self.cmd, '-f', self.path, 'logs', '--tail', self.tail]

    def get_compose_ls(self) -> List[str] or str:
        return self.cmd + ' ls -a --format json| {}'.format(self.grep_version)

    def get_compose_ps(self) -> List[str] or str:
        return self.cmd + ' -f {} ps -a --format json| {}'.format(self.path, self.grep_version)

    def get_compose_config(self) -> List[str] or str:
        return self.cmd + ' -f {} config| {}'.format(self.path, self.grep_version)

    def get_container_logs(self) -> List[str] or str:
        # return ['docker', 'logs', '-f', self.container_id]
        return "docker logs {} --tail {} 2>&1".format(self.container_id, self.tail)

    def wsResult(self, status: bool = True, msg: str = "", data: any = None, timestamp: int = None, code: int = 0,
                 args: any = None):
        rs = public.returnResult(status, msg, data, timestamp, code, args)
        rs["def_name"] = self.def_name
        return rs

    # 2024/8/1 下午3:29 构造分页数据
    def get_page(self, data, get):
        get.row = get.get("row", 20)
        # get.row = 20000
        get.p = get.get("p", 1)
        import page
        page = page.Page()
        info = {'count': len(data), 'row': int(get.row), 'p': int(get.p), 'uri': {}, 'return_js': ''}

        result = {'page': page.GetPage(info)}
        n = 0
        result['data'] = []
        for i in range(info['count']):
            if n >= page.ROW: break
            if i < page.SHIFT: continue
            n += 1
            result['data'].append(data[i])
        return result

    # 2024/7/29 下午4:22 检查web服务是否正常
    def check_web_status(self):
        '''
            @name 检查web服务是否正常
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        from mod.base.web_conf import util
        webserver = util.webserver()
        if webserver != "nginx" or webserver is None:
            return public.returnResult(status=False, msg="仅支持Nginx创建网站，请到宝塔软件商店安装Nginx!")

        from panelSite import panelSite
        site_obj = panelSite()
        site_obj.check_default()

        wc_err = public.checkWebConfig()
        if not wc_err:
            return public.returnResult(
                status=False,
                msg='ERROR: 检测到配置文件有错误,请先排除后再操作<br><br><a style="color:red;">' +
                    wc_err.replace("\n", '<br>') + '</a>'
            )

        return public.returnResult(True)

    def pageResult(self, status: bool = True,
                   msg: str = "",
                   data: any = None,
                   timestamp: int = None,
                   code: int = 0,
                   args: any = None,
                   page: any = None,
                   cpu: any = None,
                   mem: any = None):
        rs = public.returnResult(status, msg, data, timestamp, code, args)
        if not self.def_name is None:
            rs["def_name"] = self.def_name
        if not cpu is None:
            rs["maximum_cpu"] = cpu
        if not mem is None:
            rs["maximum_memory"] = mem
        if not page is None:
            rs["page"] = page
        return rs

    # 2024/6/25 下午2:40 获取日志类型的websocket返回值
    def exec_logs(self, get, command, cwd=None):
        '''
            @name 获取日志类型的websocket返回值
            @author wzz <2024/6/25 下午2:41>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        import json
        if self.def_name is None: self.set_def_name(get.def_name)
        from subprocess import Popen, PIPE, STDOUT

        p = Popen(command, stdout=PIPE, stderr=STDOUT, cwd=cwd)

        while True:
            if p.poll() is not None:
                break

            line = p.stdout.readline()  # 非阻塞读取
            if line:
                try:
                    if hasattr(get, '_ws'):
                        get._ws.send(json.dumps(self.wsResult(
                            True,
                            "{}".format(line.decode('utf-8').rstrip()),
                        )))
                except:
                    continue
            else:
                break

    # 2024/6/25 下午2:40 获取日志类型的websocket返回值
    def status_exec_logs(self, get, command, cwd=None):
        '''
            @name 获取日志类型的websocket返回值
            @author wzz <2024/6/25 下午2:41>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        import json
        if self.def_name is None: self.set_def_name(get.def_name)
        from subprocess import Popen, PIPE, STDOUT

        p = Popen(command, stdout=PIPE, stderr=STDOUT, cwd=cwd)

        while True:
            if p.poll() is not None:
                break

            line = p.stdout.readline()  # 非阻塞读取
            if line:
                try:
                    if hasattr(get, '_ws'):
                        get._ws.send(json.dumps(self.wsResult(
                            True,
                            "{}\r\n".format(line.decode('utf-8').rstrip()),
                        )))
                except:
                    continue
            else:
                break
