#coding: utf-8
#-------------------------------------------------------------------
# 宝塔Linux面板
#-------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
#-------------------------------------------------------------------
# Author: zouhw <zhw@bt.cn>
#-------------------------------------------------------------------

#------------------------------
# Docker模型
#------------------------------
import public
import json

class contianer:

    def docker_client(self,url):
        import projectModel.bt_docker.public as dp
        return dp.docker_client(url)

    # 添加容器
    def run(self,args):
        """
        :param name:容器名
        :param image: 镜像
        :param auto_pull 如果没有镜像，自动拉取镜像，匿名拉取一天最多100次
        :param publish_all_ports 暴露所有端口 1/0
        :param ports  暴露某些端口 {'1111/tcp': ('127.0.0.1', 1111)}
        :param command 命令
        :param entrypoint  配置容器启动后执行的命令
        :param environment 环境变量 xxx=xxx 一行一条
        :param auto_remove 当容器进程退出时，在守护进程端启用自动移除容器。 0/1

        :param args:
        :return:
        """
        try:
            if not args.name:
                args.name = "{}-{}".format(args.image,public.GetRandomString(8))
            res = self.docker_client(args.url).containers.run(
                name=args.name,
                image=args.image,
                detach=True,
                publish_all_ports=True if args.publish_all_ports == "1" else False,
                ports=json.loads(args.ports) if args.ports else None,
                command=args.command,
                auto_remove=True if args.auto_remove == "1" else False,
                environment=[i.strip() for i in args.environment.split('\n')] if args.environment else None

            )
            if res:
                return public.returnMsg(True,"容器创建成功！")
            return public.returnMsg(False, '创建失败!')
        except:
            return public.returnMsg(False, '创建失败! {}'.format(public.get_error_info()))

    # 保存为镜像
    def commit(self,args):
        """
        :param repository 推送到的仓库
        :param tag
        :param message
        :param author
        :param changes
        :param conf dict
        :param args:
        :return:
        """
        container = self.docker_client(args.url).containers.get(args.id)
        container.commit(
            repository=args.repository if args.repository else None,
            tag=args.tag if args.tag else None,
            message=args.message if args.message else None,
            author=args.author if args.author else None,
            changes=args.changes if args.changes else None,
            conf=args.conf if args.conf else None
        )
        return public.returnMsg(True,"提交成功！")

    # 导出容器为tar
    def export(self,args):
        """
        :param path 保存路径
        :param name 包名
        :param args:
        :return:
        """
        from os import path as ospath
        from os import makedirs as makedirs
        try:
            file_name = '{}/{}.tar'.format(args.path,args.name)
            if not ospath.exists(args.path):
                makedirs(args.path)
            public.writeFile(file_name,'')
            f = open(file_name, 'wb')
            container = self.docker_client(args.url).containers.get(args.id)
            data = container.export()
            for i in data:
                f.write(i)
            f.close()
            return public.returnMsg(True, "成功导出到: {}".format(file_name))
        except:
            return public.returnMsg(False, '操作失败: ' + str(public.get_error_info()))

    # 删除容器
    def del_container(self,args):
        """
        :return:
        """
        container = self.docker_client(args.url).containers.get(args.id)
        container.remove(force=True)
        return public.returnMsg(True,"删除成功！")

    # 停止容器
    def stop(self,args):
        """
        :param url
        :param id
        :param args:
        :return:
        """
        container = self.docker_client(args.url).containers.get(args.id)
        return container.stop()

    def start(self,args):
        """
        :param url
        :param id
        :param args:
        :return:
        """
        container = self.docker_client(args.url).containers.get(args.id)
        return container.start()

    def pause(self,args):
        """
        Pauses all processes within this container.
        :param url
        :param id
        :param args:
        :return:
        """
        container = self.docker_client(args.url).containers.get(args.id)
        return container.pause()

    def reload(self,args):
        """
        Load this object from the server again and update attrs with the new data.
        :param url
        :param id
        :param args:
        :return:
        """
        container = self.docker_client(args.url).containers.get(args.id)
        return container.reload()

    def restart(self,args):
        """
        Restart this container. Similar to the docker restart command.
        :param url
        :param id
        :param args:
        :return:
        """
        container = self.docker_client(args.url).containers.get(args.id)
        return container.restart()

    # 获取容器列表
    def get_list(self,args):
        """
        :param url
        :return:
        """
        import time
        start = time.time()
        containers = self.docker_client(args.url).containers
        attr_list = self.get_container_attr(containers)
        stop = time.time()
        # print(stop - start)
        return public.returnMsg(True,attr_list)

    # 获取容器的attr
    def get_container_attr(self,containers):
        c_list = containers.list(all=True)
        return [container_info.attrs for container_info in c_list]

    # 获取容器日志
    def get_logs(self,args):
        """
        :param url
        :param id
        :param args:
        :return:
        """
        container = self.docker_client(args.url).containers.get(args.id)
        return container.logs().decode()



    # 登录容器


    # 获取容器配置文件