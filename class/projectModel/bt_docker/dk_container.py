# coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author: zouhw <zhw@bt.cn>
# -------------------------------------------------------------------
import datetime
import json
import os
import traceback

# ------------------------------
# Docker模型
# ------------------------------
import public
import crontab
import docker.errors
import projectModel.bt_docker.dk_public as dp


class main:

    def __init__(self):
        self.alter_table()
        if public.M('sqlite_master').where('type=? AND name=?', ('table', 'docker_log_split')).count():
            p = crontab.crontab()
            llist = p.GetCrontab(None)
            for i in llist:
                if i['name'] == '[勿删]docker日志切割':
                    return
            args = {
                "name": "[勿删]docker日志切割",
                "type": "minute-n",
                "where1": 5,
                "hour": "",
                "minute": "",
                "week": "",
                "sType": "toShell",
                "sName": "",
                "backupTo": "localhost",
                "save": '',
                "sBody": "btpython /www/server/panel/script/dk_log_split.py",
                "urladdress": "undefined"
            }
            p.AddCrontab(args)

    def alter_table(self):
        if not dp.sql('sqlite_master').where('type=? AND name=? AND sql LIKE ?',
                                             ('table', 'container', '%sid%')).count():
            dp.sql('container').execute("alter TABLE container add container_name VARCHAR DEFAULT ''", ())

    def docker_client(self, url):
        return dp.docker_client(url)

    # 添加容器
    def run(self, args):
        """
        :param name:容器名
        :param image: 镜像
        :param publish_all_ports 暴露所有端口 1/0
        :param ports  暴露某些端口 {'1111/tcp': ('127.0.0.1', 1111)}
        :param command 命令
        :param entrypoint  配置容器启动后执行的命令
        :param environment 环境变量 xxx=xxx 一行一条
        :param auto_remove 当容器进程退出时，在守护进程端启用自动移除容器。 0/1

        :param args:
        :return:
        """
        config_path = "{}/config/name_map.json".format(public.get_panel_path())
        if not os.path.exists(config_path):
            public.writeFile(config_path, json.dumps({}))
        if public.readFile(config_path) == '':
            public.writeFile(config_path, json.dumps({}))
        name_map = json.loads(public.readFile(config_path))
        name_str = 'q18q' + public.GetRandomString(10).lower()
        name_map[name_str] = args.name
        args.name = name_str
        public.writeFile(config_path, json.dumps(name_map))
        if not hasattr(args, 'ports'):
            args.ports = False
        if not hasattr(args, 'volumes'):
            args.volumes = False
        # 检测端口是否已经在使用
        if args.ports:
            for i in args.ports:
                if dp.check_socket(args.ports[i]):
                    return public.returnMsg(False, "服务器端口[{}]已被占用，请更换为其他端口！".format(args.ports[i]))
        if not args.image:
            return public.returnMsg(False, "如果没有选择镜像，请到镜像标签拉取您需要的镜像！")
        if args.restart_policy['Name'] == "always":
            args.restart_policy = {"Name": "always"}
        # return args.restart_policy
        # if
        args.cpu_quota = float(args.cpuset_cpus) * 100000
        # if not args.volumes:
        #     args.volumes = {"/sys/fs/cgroup":{"bind":"/sys/fs/cgroup","mode":"rw"}}
        # else:
        #     if not "/sys/fs/cgroup" in args.volumes:
        #         args.volumes['/sys/fs/cgroup'] = {"bind":"/sys/fs/cgroup","mode":"rw"}
        try:
            if not args.name:
                args.name = "{}-{}".format(args.image, public.GetRandomString(8))
            if int(args.cpu_quota) / 100000 > dp.get_cpu_count():
                return public.returnMsg(False, "CPU 配额已超过可用内核数！")
            mem_limit_byte = dp.byte_conversion(args.mem_limit)
            if mem_limit_byte > dp.get_mem_info():
                return public.returnMsg(False, "内存配额已超过可用数量！")
            res = self.docker_client(args.url).containers.run(
                name=args.name,
                image=args.image,
                detach=True,
                publish_all_ports=True if args.publish_all_ports == "1" else False,
                ports=args.ports if args.ports else None,
                command=args.command,
                auto_remove=True if str(args.auto_remove) == "1" else False,
                environment=dp.set_kv(args.environment),  # "HOME=/value\nHOME11=value1"
                volumes=args.volumes,
                # 一个字典对象 {'服务器路径/home/user1/': {'bind': '容器路径/mnt/vol2', 'mode': 'rw'},'/var/www': {'bind': '/mnt/vol1', 'mode': 'ro'}}
                # cpuset_cpus=args.cpuset_cpus ,#指定容器使用的cpu个数
                cpu_quota=int(args.cpu_quota),
                mem_limit=args.mem_limit,  # b,k,m,g
                restart_policy=args.restart_policy,
                labels=dp.set_kv(args.labels),  # "key=value\nkey1=value1"
                tty=True,
                stdin_open=True,
                privileged=True
            )
            if res:
                pdata = {
                    "cpu_limit": str(args.cpu_quota),
                    "container_name": args.name
                }
                dp.sql('container').insert(pdata)
                public.set_module_logs('docker', 'run_container', 1)
                dp.write_log("创建容器 [{}] 成功！".format(args.name))
                return public.returnMsg(True, "容器创建成功！")
            return public.returnMsg(False, '创建失败！')
        except docker.errors.APIError as e:
            if "container to be able to reuse that name." in str(e):
                return public.returnMsg(False, "容器名称已存在！")
            if "Invalid container name" in str(e):
                return public.returnMsg(False, "容器名称不合法,")
            if "bind: address already in use" in str(e):
                port = ""
                for i in args.ports:
                    if ":{}:".format(args.ports[i]) in str(e):
                        port = args.ports[i]
                args.id = args.name
                self.del_container(args)
                return public.returnMsg(False, "服务器端口 {} 正在使用中！ 请更改其他端口".format(port))
            return public.returnMsg(False, '创建失败! {}'.format(public.get_error_info()))

    # 保存为镜像
    def commit(self, args):
        """
        :param repository       推送到的仓库
        :param tag              镜像标签 jose:v1
        :param message          提交的信息
        :param author           镜像作者
        :param changes
        :param conf dict
        :param path 导出路径
        :param name 导出文件名
        :param args:
        :return:
        """
        if not hasattr(args, 'conf') or not args.conf:
            args.conf = None
        if args.repository == "docker.io":
            args.repository = ""
        container = self.docker_client(args.url).containers.get(args.id)
        container.commit(
            repository=args.repository if args.repository else None,
            tag=args.tag if args.tag else None,
            message=args.message if args.message else None,
            author=args.author if args.author else None,
            # changes=args.changes if args.changes else None,
            conf=args.conf
        )
        if hasattr(args, "path") and args.path:
            args.id = "{}:{}".format(args.name, args.tag)
            import projectModel.bt_docker.dk_image as dk
            return dk.main().save(args)
        dp.write_log("提交容器 [{}] 作为图像 [{}] 成功！".format(container.attrs['Name'], args.tag))
        return public.returnMsg(True, "提交成功！")

    # 容器执行命令
    def docker_shell(self, args):
        """
        :param container_id
        :param args:
        :return:
        """
        try:
            self.docker_client(args.url).containers.get(args.container_id)
            cmd = 'docker container exec -it {} /bin/bash'.format(args.container_id)
            return public.returnMsg(True, cmd)
        except docker.errors.APIError as ex:
            return public.returnMsg(False, '获取容器失败')

    # 导出容器为tar 没有导入方法，目前弃用
    def export(self, args):
        """
        :param path 保存路径
        :param name 包名
        :param args:
        :return:
        """
        from os import path as ospath
        from os import makedirs as makedirs
        try:
            if "tar" in args.name:
                file_name = '{}/{}'.format(args.path, args.name)
            else:
                file_name = '{}/{}.tar'.format(args.path, args.name)
            if not ospath.exists(args.path):
                makedirs(args.path)
            public.writeFile(file_name, '')
            f = open(file_name, 'wb')
            container = self.docker_client(args.url).containers.get(args.id)
            data = container.export()
            for i in data:
                f.write(i)
            f.close()
            return public.returnMsg(True, "成功导出到：{}".format(file_name))
        except:
            return public.returnMsg(False, '操作失败：' + str(public.get_error_info()))

    # 删除容器
    def del_container(self, args):
        """
        :return:
        """
        import projectModel.bt_docker.dk_public as dp
        container = self.docker_client(args.url).containers.get(args.id)
        config_path = "{}/config/name_map.json".format(public.get_panel_path())
        if not os.path.exists(config_path):
            public.writeFile(config_path, json.dumps({}))
        if public.readFile(config_path) == '':
            public.writeFile(config_path, json.dumps({}))
        config_data = json.loads(public.readFile(config_path))
        if container.name in config_data.keys():
            config_data.pop(container.name)
        public.writeFile(config_path, json.dumps(config_data))
        container.remove(force=True)
        dp.sql("cpu_stats").where("container_id=?", (args.id,)).delete()
        dp.sql("io_stats").where("container_id=?", (args.id,)).delete()
        dp.sql("mem_stats").where("container_id=?", (args.id,)).delete()
        dp.sql("net_stats").where("container_id=?", (args.id,)).delete()
        dp.sql("container").where("container_nam=?", (container.attrs['Name'])).delete()
        dp.write_log("删除容器 [{}] 成功！".format(container.attrs['Name']))
        return public.returnMsg(True, "成功删除!")

    # 设置容器状态
    def set_container_status(self, args):
        import time
        container = self.docker_client(args.url).containers.get(args.id)
        if args.act == "start":
            container.start()
        elif args.act == "stop":
            container.stop()
        elif args.act == "pause":
            container.pause()
        elif args.act == "unpause":
            container.unpause()
        elif args.act == "reload":
            container.reload()
        else:
            container.restart()
        time.sleep(1)
        tmp = self.docker_client(args.url).containers.get(args.id)
        return {"name": container.attrs['Name'].replace('/', ''), "status": tmp.attrs['State']['Status']}  # 返回设置后的状态

    # 停止容器
    def stop(self, args):
        """
        :param url
        :param id
        :param args:
        :return:
        """
        try:
            args.act = "stop"
            data = self.set_container_status(args)
            if data['status'] != "exited":
                return public.returnMsg(False, "停止失败!")
            dp.write_log("停止容器 [{}] 成功!".format(data['name']))
            return public.returnMsg(True, "停止成功!")
        except docker.errors.APIError as e:
            if "is already paused" in str(e):
                return public.returnMsg(False, "容器已暂停!")
            if "No such container" in str(e):
                return public.returnMsg(True, "容器已停止并删除，因为容器有停止后自动删除的选项!")
            return public.returnMsg(False, "停止失败!{}".format(e))

    def start(self, args):
        """
        :param url
        :param id
        :param args:
        :return:
        """
        try:
            args.act = "start"
            data = self.set_container_status(args)
            if data['status'] != "running":
                return public.returnMsg(False, "启动失败!")
            dp.write_log("启动容器 [{}] 成功!".format(data['name']))
            return public.returnMsg(True, "启动成功!")
        except docker.errors.APIError as e:
            if "cannot start a paused container, try unpause instead" in str(e):
                return self.unpause(args)

    def pause(self, args):
        """
        Pauses all processes within this container.
        :param url
        :param id
        :param args:
        :return:
        """
        try:
            args.act = "pause"
            data = self.set_container_status(args)
            if data['status'] != "paused":
                return public.returnMsg(False, "容器暂停失败!")
            dp.write_log("暂停容器 [{}] 成功!".format(data['name']))
            return public.returnMsg(True, "容器暂停成功!")
        except docker.errors.APIError as e:
            if "is already paused" in str(e):
                return public.returnMsg(False, "容器已被挂起！")
            if "is not running" in str(e):
                return public.returnMsg(False, "容器未启动，无法暂停!")
            if "is not paused" in str(e):
                return public.returnMsg(False, "容器没有被暂停!")
            return str(e)

    def unpause(self, args):
        """
        unPauses all processes within this container.
        :param url
        :param id
        :param args:
        :return:
        """
        try:
            args.act = "unpause"
            data = self.set_container_status(args)
            if data['status'] != "running":
                return public.returnMsg(False, "启动失败!")
            dp.write_log("取消暂停容器 [{}] 成功!".format(data['name']))
            return public.returnMsg(True, "容器取消暂停成功")
        except docker.errors.APIError as e:
            if "is already paused" in str(e):
                return public.returnMsg(False, "容器已暂停!")
            if "is not running" in str(e):
                return public.returnMsg(False, "容器未启动，无法暂停!")
            if "is not paused" in str(e):
                return public.returnMsg(False, "容器没有被暂停!")
            return str(e)

    def reload(self, args):
        """
        Load this object from the server again and update attrs with the new data.
        :param url
        :param id
        :param args:
        :return:
        """
        args.act = "reload"
        data = self.set_container_status(args)
        if data['status'] != "running":
            return public.returnMsg(False, "启动失败!")
        dp.write_log("重新加载容器 [{}] 成功!".format(data['name']))
        return public.returnMsg(True, "重载容器成功!")

    def restart(self, args):
        """
        Restart this container. Similar to the docker restart command.
        :param url
        :param id
        :param args:
        :return:
        """
        args.act = "restart"
        data = self.set_container_status(args)
        if data['status'] != "running":
            return public.returnMsg(False, "启动失败!")
        dp.write_log("重启容器 [{}] 成功!".format(data['name']))
        return public.returnMsg(True, "容器重启成功!")

    def get_container_ip(self, container_networks):
        data = list()
        for network in container_networks:
            data.append(container_networks[network]['IPAddress'])
        return data

    def get_container_path(self, detail):
        try:
            import os
            if not "GraphDriver" in detail:
                return False
            if "Data" not in detail["GraphDriver"]:
                return False
            if "MergedDir" not in detail["GraphDriver"]["Data"]:
                return False
            path = detail["GraphDriver"]["Data"]["MergedDir"]
            if not os.path.exists(path):
                return ""
            return path
        except:
            return False

    # 获取容器列表所需的外部数据
    def get_other_data_for_container_list(self, args):
        import projectModel.bt_docker.dk_image as di
        import projectModel.bt_docker.dk_volume as dv
        import projectModel.bt_docker.dk_compose as dc
        import projectModel.bt_docker.dk_setup as ds
        # 获取镜像列表
        images = di.main().image_list(args)
        if images['status']:
            images = images['msg']['images_list']
        else:
            images = list()
        # 获取卷列表
        volumes = dv.main().get_volume_list(args)
        if volumes['status']:
            volumes = volumes['msg']['volume']
        else:
            volumes = list()
        # 获取模板列表
        template = dc.main().template_list(args)
        if template['status']:
            template = template['msg']['template']
        else:
            template = list()
        online_cpus = dp.get_cpu_count()
        mem_total = dp.get_mem_info()
        docker_setup = ds.main()
        return {
            "images": images,
            "volumes": volumes,
            "template": template,
            "online_cpus": online_cpus,
            "mem_total": mem_total,
            "installed": docker_setup.check_docker_program(),
            "service_status": docker_setup.get_service_status()
        }

    # 获取容器列表
    def get_list(self, args):
        """
        :param url
        :return:
        """
        # 判断docker是否安装
        import projectModel.bt_docker.dk_setup as ds
        data = self.get_other_data_for_container_list(args)
        if not ds.main().check_docker_program():
            data['container_list'] = list()
            return public.returnMsg(True, data)
        client = self.docker_client(args.url)
        if not client:
            return public.returnMsg(True, data)
        containers = client.containers
        attr_list = self.get_container_attr(containers)
        # data = self.get_other_data_for_container_list(args)
        container_detail = list()
        for attr in attr_list:
            cpu_usage = dp.sql("cpu_stats").where("container_id=?", (attr["Id"],)).select()
            if cpu_usage and isinstance(cpu_usage, list):
                cpu_usage = cpu_usage[-1]['cpu_usage']
            else:
                cpu_usage = "0.0"
            tmp = {
                "id": attr["Id"],
                "name": attr['Name'].replace("/", ""),
                "status": attr["State"]["Status"],
                "image": attr["Config"]["Image"],
                "time": attr["Created"],
                "merged": self.get_container_path(attr),
                "ip": self.get_container_ip(attr["NetworkSettings"]['Networks']),
                "ports": attr["NetworkSettings"]["Ports"],
                "detail": attr,
                "cpu_usage": cpu_usage if attr["State"]["Status"] == "running" else ""
            }
            container_detail.append(tmp)
        if container_detail:
            for i in container_detail:
                i['name'] = self.rename(i['name'])
        data['container_list'] = container_detail
        return public.returnMsg(True, data)

    def rename(self, name: str):
        try:
            if name[:4] != 'q18q':
                return name
            config_path = "{}/config/name_map.json".format(public.get_panel_path())
            config_data = json.loads(public.readFile(config_path))
            name_l = name.split('_')
            if name_l[0] in config_data.keys():
                name_l[0] = config_data[name_l[0]]
            return '_'.join(name_l)
        except:
            return name

    # 获取容器的attr
    def get_container_attr(self, containers):
        c_list = containers.list(all=True)
        return [container_info.attrs for container_info in c_list]

    # 获取容器日志
    def get_logs(self, args):
        """
        :param url
        :param id
        :param args:
        :return:
        """
        try:
            container = self.docker_client(args.url).containers.get(args.id)
            if hasattr(args, 'time_search') and args.time_search != '':
                time_search = json.loads(args.time_search)
                since = int(time_search[0])
                until = int(time_search[1])
                res = container.logs(since=since, until=until).decode()
            else:
                res = container.logs().decode()
            if hasattr(args, 'search') and args.search != '':
                if args.search:
                    res = res.split("\n")
                    res = [i for i in res if args.search in i]
                    res = "\n".join(res)
            return public.returnMsg(True, res)
        except docker.errors.APIError as e:
            if "configured logging driver does not support reading" in str(e):
                return public.returnMsg(False, "容器没有日志文件！")
            print(traceback.format_exc())

    def get_logs_all(self, args):
        try:
            client = self.docker_client(args.url)
            if not client:
                return public.returnMsg(True, 'docker连接失败')
            containers = client.containers
            clist = [i.attrs for i in containers.list(all=True)]
            clist = [{'id': i['Id'], 'name': self.rename(i['Name'][1:]), 'log_path': i['LogPath']} for i in clist]
            for i in clist:
                if os.path.exists(i['log_path']):
                    i['size'] = os.stat(i['log_path']).st_size
                else:
                    i['size'] = 0
                if public.M('sqlite_master').where('type=? AND name=?', ('table', 'docker_log_split')).count():
                    i['split_status'] = True if public.M('docker_log_split').where('pid=?',
                                                                                   (i['id'],)).count() else False
                    data = public.M('docker_log_split').where('pid=?', (i['id'],)).select()
                    if data:
                        i['split_type'] = data[0]['split_type']
                        i['split_size'] = data[0]['split_size']
                        i['split_hour'] = data[0]['split_hour']
                        i['split_minute'] = data[0]['split_minute']
                        i['save'] = data[0]['save']
                    else:
                        i['split_type'] = 'day'
                        i['split_size'] = 10485760
                        i['split_hour'] = 2
                        i['split_minute'] = 0
                        i['save'] = '180'
                else:
                    i['split_status'] = False
                    i['split_type'] = 'day'
                    i['split_size'] = 10485760
                    i['split_hour'] = 2
                    i['split_minute'] = 0
                    i['save'] = '180'
            return clist
        except:
            return public.returnMsg(True, traceback.format_tb())

    def docker_split(self, args):
        try:
            client = self.docker_client(args.url)
            if not client:
                return public.returnMsg(True, 'docker连接失败')
            containers = client.containers
            clist = [i.attrs for i in containers.list(all=True)]
            name = [self.rename(i['Name'][1:]) for i in clist if i['Id'] == args.pid]
            if name:
                name = name[0]
            else:
                name = ''
            if not hasattr(args, 'type'):
                return public.returnMsg(False, '参数错误')
            if not public.M('sqlite_master').where('type=? AND name=?', ('table', 'docker_log_split')).count():
                public.M('docker_log_split').execute('''CREATE TABLE IF NOT EXISTS docker_log_split (
                id      INTEGER      PRIMARY KEY AUTOINCREMENT,
                name    text default '',
                pid    text default '',
                log_path     text default '',
                split_type text default '',
                split_size INTEGER default 0,
                split_hour INTEGER default 2,
                split_minute INTEGER default 0,
                save INTEGER default 180)''', ())
            if args.type == 'add':
                if not (hasattr(args, 'pid') and hasattr(args, 'log_path') and
                        hasattr(args, 'split_type') and hasattr(args, 'split_size') and
                        hasattr(args, 'split_minute') and
                        hasattr(args,'split_hour') and hasattr(args, 'save')):
                    return public.returnMsg(False, '参数错误')
                data = {
                    'name': name,
                    'pid': args.pid,
                    'log_path': args.log_path,
                    'split_type': args.split_type,
                    'split_size': args.split_size,
                    'split_hour': args.split_hour,
                    'split_minute': args.split_minute,
                    'save': args.save
                }
                if public.M('docker_log_split').where('pid=?', (args.pid,)).count():
                    id = public.M('docker_log_split').where('pid=?', (args.pid,)).select()
                    public.M('docker_log_split').delete(id[0]['id'])
                public.M('docker_log_split').insert(data)
                return public.returnMsg(True, "开启成功!")
            elif args.type == 'del':
                id = public.M('docker_log_split').where('pid=?', (args.pid,)).getField('id')
                public.M('docker_log_split').where('id=?', (id,)).delete()
                return public.returnMsg(True, "关闭成功!")
        except:
            return public.returnMsg(False, traceback.format_exc())

    def clear_log(self, args):
        if not hasattr(args, 'log_path'):
            return public.returnMsg(False, '参数错误')
        if not os.path.exists(args.log_path):
            return public.returnMsg(False, '日志文件不存在')
        public.writeFile(args.log_path, '')
        return public.returnMsg(True, "日志清理成功成功!")
