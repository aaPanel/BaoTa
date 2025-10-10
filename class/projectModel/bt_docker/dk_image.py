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
import os
import public
import docker.errors
import projectModel.bt_docker.dk_public as dp

class main:
    __log_path = '/tmp/dockertmp.log'
    def docker_client(self,url):
        import projectModel.bt_docker.dk_public as dp
        return dp.docker_client(url)

    # 导出
    def save(self,args):
        """
        :param path 要镜像tar要存放的路径
        :param name 包名
        :param id 镜像
        :param
        :param args:
        :return:
        """
        try:
            if "tar" in args.name:
                filename = '{}/{}'.format(args.path,args.name)
            else:
                filename = '{}/{}.tar'.format(args.path, args.name)
            if not os.path.exists(args.path):
                os.makedirs(args.path)
            public.writeFile(filename,"")
            f = open(filename,'wb')
            image = self.docker_client(args.url).images.get(args.id)
            for chunk in image.save(named=True):
                f.write(chunk)
            f.close()
            dp.write_log("镜像 [{}] 导出到 [{}] 成功".format(args.id,filename))
            return public.returnMsg(True, "成功保存到：{}".format(filename))
        except docker.errors.APIError as e:
            if "empty export - not implemented" in str(e):
                return public.returnMsg(False,"不能导出镜像！")
            return public.get_error_info()

    # 导入
    def load(self,args):
        """
        :param path: 需要导入的镜像路径具体到文件名
        :param args:
        :return:
        """
        images = self.docker_client(args.url).images
        with open(args.path,'rb') as f:
            images.load(
                f
            )
        dp.write_log("镜像 [{}] 导入成功!".format(args.path))
        return public.returnMsg(True,"镜像导入成功！{}".format(args.path))

    # 列出所有镜像
    def image_list(self,args):
        """
        :param url
        :param args:
        :return:
        """
        import projectModel.bt_docker.dk_registry as dr
        import projectModel.bt_docker.dk_setup as ds
        data = list()
        client = self.docker_client(args.url)
        docker_setup = ds.main()
        installed = docker_setup.check_docker_program()
        service_status = docker_setup.get_service_status()
        if not client:
            data = {
                "images_list": [],
                "registry_list": [],
                "installed": installed,
                "service_status": service_status
            }
            return public.returnMsg(True,data)
        images = client.images
        image_attr = self.get_image_attr(images)
        registry_list = dr.main().registry_list(args)
        if registry_list['status']:
            registry_list = registry_list['msg']['registry']
        else:
            registry_list = []
        for attr in image_attr:
            if len(attr['RepoTags']) == 1:
                tmp = {
                    "id": attr["Id"],
                    "tags": attr["RepoTags"],
                    "time": attr["Created"],
                    "name": attr['RepoTags'][0],
                    "size": attr["Size"],
                    "detail": attr
                }
                data.append(tmp)
            elif len(attr['RepoTags']) > 1:
                for i in range(len(attr['RepoTags'])):
                    tmp = {
                        "id": attr["Id"],
                        "tags": attr["RepoTags"],
                        "time": attr["Created"],
                        "name": attr['RepoTags'][i],
                        "size": attr["Size"],
                        "detail": attr
                    }
                    data.append(tmp)
            elif not attr['RepoTags']:
                tmp = {
                    "id": attr["Id"],
                    "tags": attr["RepoTags"],
                    "time": attr["Created"],
                    "name": attr["Id"],
                    "size": attr["Size"],
                    "detail": attr
                }
                data.append(tmp)
        data = {
            "images_list":data,
            "registry_list": registry_list,
            "installed": installed,
            "service_status": service_status
        }
        return public.returnMsg(True,data)

    def get_image_attr(self,images):
        image = images.list()
        return [i.attrs for i in image]

    def get_logs(self, args):
        import files
        logs_file = args.logs_file
        return public.returnMsg(True,files.files().GetLastLine(logs_file, 20))

    # 构建镜像
    def build(self,args):
        """
        :param path         dockerfile dir
        :param pull         如果引用的镜像有更新自动拉取
        :param tag          标签 jose:v1
        :param data         在线编辑配置
        :param args:
        :return:
        """
        public.writeFile(self.__log_path,"开始构建镜像！")
        public.writeFile('/tmp/dockertmp.log', "开始构建镜像！")
        if not hasattr(args,"pull"):
            args.pull = False
        if hasattr(args,"data") and args.data:
            args.path = "/tmp/dockerfile"
            public.writeFile(args.path,args.data)
            with open(args.path, 'rb') as f:
                image_obj,generator = self.docker_client(args.url).images.build(
                    pull=True if args.pull == "1" else False,
                    fileobj=f,
                    tag=args.tag,
                    forcerm=True
                )
            os.remove(args.path)
        else:
            if not os.path.exists(args.path):
                return public.returnMsg(True, "请输入正确的DockerFile路径！")
            if not os.path.isdir(args.path):
                args.path = '/'.join(args.path.split('/')[:-1])
            image_obj,generator = self.docker_client(args.url).images.build(
                pull=True if args.pull == "1" else False,
                path=args.path,
                tag=args.tag,
                forcerm=True
            )
        # return args.path
        dp.log_docker(generator,"Docker 构建任务！")
        dp.write_log("构建镜像 [{}] 成功!".format(args.tag))
        return public.returnMsg(True,"构建镜像成功!")

    # 删除镜像
    def remove(self,args):
        """
        :param url
        :param id  镜像id
        :param name 镜像tag
        :force 0/1 强制删除镜像
        :param args:
        :return:
        """
        try:
            self.docker_client(args.url).images.remove(args.name)
            dp.write_log("删除镜像【{}】成功!".format(args.name))
            return public.returnMsg(True,"删除镜像成功!")
        except docker.errors.ImageNotFound as e:
            return public.returnMsg(False,"删除进行失败，镜像可能不存在!")
        except docker.errors.APIError as e:
            if "image is referenced in multiple repositories" in str(e):
                return public.returnMsg(False, "镜像 ID 用在多个镜像中，请强制删除镜像!")
            if "using its referenced image" in str(e):
                return public.returnMsg(False, "镜像正在使用中，请删除容器后再删除镜像!")
            return public.returnMsg(False,"删除镜像失败!<br> {}".format(e))

    # 拉取指定仓库镜像
    def pull_from_some_registry(self,args):
        """
        :param name 仓库名
        :param url
        :param image
        :param args:
        :return:
        """
        import projectModel.bt_docker.dk_registry as br
        r_info = br.main().registry_info(args.name)
        login = br.main().login(args.url,r_info['url'],r_info['username'],r_info['password'])['status']
        if not login:
            return login
        args.username = r_info['username']
        args.password = r_info['password']
        args.registry = r_info['url']
        args.namespace = r_info['namespace']
        return self.pull(args)

    # 推送镜像到指定仓库
    def push(self,args):
        """
        :param id       镜像ID
        :param url      连接docker的url
        :param tag      标签 镜像名+版本号v1
        :param name     仓库名
        :param args:
        :return:
        """
        if "/" in args.tag:
            return public.returnMsg(False,"推送的镜像不能包含 [/] , 请使用以下格式: image:v1 (镜像名:版本)")
        if ":" not in args.tag:
            return public.returnMsg(False,"推送的镜像不能包含 [ : ] , 请使用以下格式: image:v1 (image_name:version_number)")
        public.writeFile(self.__log_path, "开始推镜像!\n")
        import projectModel.bt_docker.dk_registry as br
        r_info = br.main().registry_info(args.name)
        if args.name == "docker official" and r_info['url'] == "docker.io":
            public.writeFile(self.__log_path, "镜像无法推送到 Docker 公共仓库!\n")
            return public.returnMsg(False,"无法推送到 Docker 公共仓库!")
        login = br.main().login(args.url,r_info['url'],r_info['username'],r_info['password'])['status']
        tag = args.tag
        if not login:
            return login
        auth_conf = {"username": r_info['username'],
                     "password": r_info['password'],
                     "registry": r_info['url']
                     }
        # repository       namespace/image
        if ":" not in tag:
            tag = "{}:latest".format(tag)
        repository = r_info['url']
        image = "{}/{}/{}".format(repository,r_info['namespace'],args.tag)
        self.tag(args.url,args.id,image)
        ret = self.docker_client(args.url).images.push(
            repository=image.split(":")[0],
            tag=tag.split(":")[-1],
            auth_config=auth_conf,
            stream=True
        )
        dp.log_docker(ret,"Image push task")
        # 删除自动打标签的镜像
        args.name = image
        self.remove(args)
        dp.write_log("镜像 [{}] 推送成功！".format(image))
        return public.returnMsg(True,"推送成功！{}".format(str(ret)))

    def tag(self,url,image_id,tag):
        """
        为镜像打标签
        :param repository   仓库namespace/images
        :param image_id:          镜像ID
        :param tag:         镜像标签jose:v1
        :return:
        """
        image = tag.split(":")[0]
        tag_ver = tag.split(":")[1]
        self.docker_client(url).images.get(image_id).tag(
            repository=image,
            tag=tag_ver
        )
        return public.returnMsg(True,"设置成功！")

    def pull(self,args):
        """
        :param image
        :param url
        :param registry
        :param username 拉取私有镜像时填写
        :param password 拉取私有镜像时填写
        :param args:
        :return:
        """
        public.writeFile(self.__log_path, "开始推送镜像!")
        import docker.errors
        try:
            if ':' not in args.image:
                args.image = '{}:latest'.format(args.image)
            auth_conf = {"username": args.username,
                         "password": args.password,
                         "registry":args.registry if args.registry else None
                         } if args.username else None
            if not hasattr(args,"tag"):
                args.tag = args.image.split(":")[-1]
            if args.registry != "docker.io":
                args.image = "{}/{}/{}".format(args.registry,args.namespace,args.image)
            ret = dp.docker_client_low(args.url).pull(
                repository=args.image,
                auth_config=auth_conf,
                tag=args.tag,
                stream=True
            )
            dp.log_docker(ret,"镜像拉取任务")
            if ret:
                dp.write_log("镜像拉取 [{}:{}] 成功".format(args.image,args.tag))
                return public.returnMsg(True, '镜像拉取成功.')
            else:
                return public.returnMsg(False, '可能没有这个镜像.')
        except docker.errors.ImageNotFound as e:
            if "pull access denied for" in str(e):
                return public.returnMsg(False,"拉取失败，镜像为私有镜像，需要输入dockerhub的账号密码!")

            return public.returnMsg(False,"拉取失败<br><br>原因: {}".format(e))

        except docker.errors.NotFound as e:
            if "not found: manifest unknown" in str(e):
                return public.returnMsg(False,"镜像拉取失败，仓库中没有这个镜像!")
            return public.returnMsg(False, "Pull failed<br><br>reason:{}".format(e))
        except docker.errors.APIError as e:
            if "invalid tag format" in str(e):
                return public.returnMsg(False,"拉取失败, 镜像格式错误, 如: nginx:v 1!")
            return public.returnMsg(False,"拉取失败!{}".format(e))


    # 拉取镜像
    def pull_high_api(self,args):
        """
        :param image
        :param url
        :param registry
        :param username 拉取私有镜像时填写
        :param password 拉取私有镜像时填写
        :param args:
        :return:
        """
        import docker.errors
        try:
            if ':' not in args.image:
                args.image = '{}:latest'.format(args.image)
            auth_conf = {"username": args.username,
                         "password": args.password,
                         "registry":args.registry if args.registry else None
                         } if args.username else None

            if args.registry != "docker.io":
                args.image = "{}/{}/{}".format(args.registry,args.namespace,args.image)
            ret = self.docker_client(args.url).images.pull(
                repository=args.image,
                auth_config=auth_conf,
            )
            if ret:
                return public.returnMsg(True, '拉取镜像成功.')
            else:
                return public.returnMsg(False, '可能没有这个镜像.')
        except docker.errors.ImageNotFound as e:
            if "pull access denied for" in str(e):
                return public.returnMsg(False,"拉取镜像失败, 这个是私有镜像，请输入账号密码!")
            return public.returnMsg(False,"拉取镜像失败<br><br>原因: {}".format(e))

    def image_for_host(self,args):
        """
        获取镜像大小和获取镜像数量
        :param args:
        :return:
        """
        res = self.image_list(args)
        if not res['status']:
            return res
        num = len(res['msg']['images_list'])
        size = 0
        for i in res['msg']['images_list']:
            size += i['size']
        return public.returnMsg(True,{'num':num,'size':size})