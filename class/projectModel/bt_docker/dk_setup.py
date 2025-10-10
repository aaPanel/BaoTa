# coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author: zouhw <zhw@bt.cn>
# -------------------------------------------------------------------

# ------------------------------
# Docker模型
# ------------------------------

import os
import json
import public
import projectModel.bt_docker.dk_public as dp


class main:
    def get_config(self, args):
        import projectModel.bt_docker.dk_public as dp
        # 获取加速配置
        registry_mirrors = self.get_registry_mirrors(args)
        if not registry_mirrors["status"]:
            return registry_mirrors
        else:
            if not isinstance(registry_mirrors['msg'], list):
                registry_mirrors['msg'] = [registry_mirrors['msg']]
        service_status = self.get_service_status()
        return public.returnMsg(
            True, {
                "registry_mirrors": registry_mirrors['msg'],
                "service_status": service_status,
                "installed": self.check_docker_program(),
                "monitor_status": self.get_monitor_status(),
                "monitor_save_date": dp.docker_conf()['SAVE']
            })

    def set_monitor_save_date(self, args):
        """
        :param save_date: int 例如30 表示 30天
        :param args:
        :return:
        """
        import re
        conf_path = "{}/data/docker.conf".format(public.get_panel_path())
        docker_conf = public.readFile(conf_path)
        try:
            save_date = int(args.save_date)
        except:
            return public.returnMsg(False, "监控保存时间需要为正整数！")
        if save_date > 999:
            return public.returnMsg(False, "监控数据不能保留超过999天！")
        if not docker_conf:
            docker_conf = "SAVE={}".format(save_date)
            public.writeFile(conf_path, docker_conf)
            return public.returnMsg(True, "设置成功！")
        docker_conf = re.sub("SAVE\s*=\s*\d+", "SAVE={}".format(save_date),
                             docker_conf)
        public.writeFile(conf_path, docker_conf)
        dp.write_log("设置监控时间为[{}]天！".format(save_date))
        return public.returnMsg(True, "设置成功！")

    def get_service_status(self):
        import projectModel.bt_docker.dk_public as dp
        sock = '/var/run/docker.pid'
        if os.path.exists(sock):
            try:
                client = dp.docker_client()
                if client:
                    return True
                else:
                    return False
            except:
                return False
        else:
            return False

    # docker服务状态设置
    def docker_service(self, args):
        """
        :param act start/stop/restart
        :param args:
        :return:
        """
        import public
        act_dict = {'start': 'start', 'stop': 'stop', 'restart': 'restart'}
        if args.act not in act_dict:
            return public.returnMsg(False, '没有办法做到这一点！')
        exec_str = 'systemctl {} docker'.format(args.act)
        if args.act == "stop":
            exec_str += "&& systemctl {} docker.socket".format(args.act)
        public.ExecShell(exec_str)
        dp.write_log("将 Docker 服务状态设置为 [{}] 成功".format(act_dict[args.act]))
        return public.returnMsg(True,
                                "将状态设置为 [{}] 成功".format(act_dict[args.act]))

    # 获取加速配置
    def get_registry_mirrors(self, args):
        try:
            if not os.path.exists('/etc/docker/daemon.json'):
                return public.returnMsg(True, [])
            if public.readFile('/etc/docker/daemon.json') == '':
                return public.returnMsg(True, [])
            conf = json.loads(public.readFile('/etc/docker/daemon.json'))
            if "registry-mirrors" not in conf:
                return public.returnMsg(True, [])
            return public.returnMsg(True, conf['registry-mirrors'])
        except:
            return public.returnMsg(
                False, '失败！失败原因：{}'.format(public.get_error_info()))

    # 设置加速配置
    def set_registry_mirrors(self, args):
        """
        :param registry_mirrors_address registry.docker-cn.com\nhub-mirror.c.163.com
        :param args:
        :return:
        """
        import re
        try:
            conf = {}
            if os.path.exists('/etc/docker/daemon.json'):
                conf = json.loads(public.readFile('/etc/docker/daemon.json'))
            if not args.registry_mirrors_address.strip():
                # return public.returnMsg(False, '加速地址不能为空！')
                if 'registry-mirrors' not in conf:
                    return public.returnMsg(True, '设置成功')
                del (conf['registry-mirrors'])
            else:
                registry_mirrors = args.registry_mirrors_address.strip().split(
                    '\n')
                for i in registry_mirrors:
                    if not re.search('https?://', i):
                        return public.returnMsg(
                            False,
                            '加速地址[{}]格式错误<br>参考：https://mirror.ccs.tencentyun.com'
                            .format(i))
                tmp_registry = registry_mirrors
                if isinstance(registry_mirrors, list) and registry_mirrors:
                    tmp_registry = registry_mirrors[0]
                conf['registry-mirrors'] = public.xsssec2(tmp_registry)
                if isinstance(conf['registry-mirrors'], str):
                    conf['registry-mirrors'] = [conf['registry-mirrors']]
            public.writeFile('/etc/docker/daemon.json',
                             json.dumps(conf, indent=2))
            dp.write_log("设置Docker加速成功!")
            return public.returnMsg(True, '设置成功')
        except:
            return public.returnMsg(
                False, '设置失败！失败原因:{}'.format(public.get_error_info()))

    def get_monitor_status(self):
        """
        :return:
        """
        # 进程是否存在
        res = public.process_exists(
            "python",
            cmdline=
            "/www/server/panel/class/projectModel/bt_docker/dk_monitor.py")
        if res:
            return res
        res = public.process_exists(
            "python3",
            cmdline=
            "/www/server/panel/class/projectModel/bt_docker/dk_monitor.py")
        if res:
            return res
        return res

    def set_docker_monitor(self, args):
        """
        开启docker监控获取docker相取资源信息
        :param act: start/stop
        :return:
        """
        import time
        import projectModel.bt_docker.dk_public as dp
        python = "/www/server/panel/pyenv/bin/python"
        if not os.path.exists(python):
            python = "/www/server/panel/pyenv/bin/python3"
        cmd_line = "/www/server/panel/class/projectModel/bt_docker/dk_monitor.py"
        if args.act == "start":
            shell = "nohup {} {} &".format(python, cmd_line)
            public.ExecShell(shell)
            time.sleep(1)
            if self.get_monitor_status():
                dp.write_log("Docker监控启动成功！")
                return public.returnMsg(True, "启动监控成功！")
            return public.returnMsg(False, "启动监控失败！")
        else:
            pid = dp.get_process_id(
                "python",
                "/www/server/panel/class/projectModel/bt_docker/dk_monitor.py")
            if not pid:
                pid = dp.get_process_id(
                    "python3",
                    "/www/server/panel/class/projectModel/bt_docker/dk_monitor.py"
                )
            public.ExecShell("kill -9 {}".format(pid))
            dp.write_log("Docker监控成功停止！")
            return public.returnMsg(True, "Docker监控成功停止！")

    def check_docker_program(self):
        """
        检查docker和docker-compose是否已经安装
        :return:
        """
        docker = "/usr/bin/docker"
        docker_compose = "/usr/bin/docker-compose"
        if not os.path.exists(docker_compose):
            dk_compose_list = ["/usr/libexec/docker/cli-plugins/docker-compose", "/usr/local/docker-compose"]
            for i in dk_compose_list:
                if os.path.exists(i):
                    public.ExecShell("ln -sf {} {}".format(i, docker_compose))
        if not os.path.exists(docker) or not os.path.exists(docker_compose):
            return False
        return True

    def install_docker_program(self, args):
        """
        安装docker和docker-compose
        :param args:
        :return:
        """
        import time
        mmsg = "Install Docker service"
        # Docker_Install_File = "/www/server/panel/install/docker_install.sh"
        # execstr = "wget -O {} http://download.bt.cn/install/0/docker_install.sh -T 5"
        execstr = "/bin/bash /www/server/panel/install/install_soft.sh 0 install docker_install"
        public.M('tasks').add('id,name,type,status,addtime,execstr',
                              (None, mmsg, 'execshell', '0',
                               time.strftime('%Y-%m-%d %H:%M:%S'), execstr))
        public.httpPost(
            public.GetConfigValue('home') + '/api/panel/plugin_total', {
                "pid": "1111111",
                'p_name': "Docker商用模块"
            }, 3)
        return public.returnMsg(True, "安装任务已添加到队列中！")
