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

class image:

    def docker_client(self,url):
        import projectModel.bt_docker.public as dp
        return dp.docker_client(url)

    # 导出
    def save(self,args):
        """
        :param path 要镜像tar要存放的路径
        :param name 包名
        :param
        :param args:
        :return:
        """
        filename = "{}/{}.tar".format(args.path,args.name)
        if not os.path.exists(args.path):
            os.makedirs(args.path)
        public.writeFile(filename,"")
        f = open(filename,'wb')
        image = self.docker_client(args.url).images.get(args.id)
        for chunk in image.save():
            f.write(chunk)
        f.close()
        return public.returnMsg(True,"成功保存到: {}".format(filename))

    # 导入
    def load(self,args):
        """
        :path 需要导入的镜像路径
        :param args:
        :return:
        """
        images = self.docker_client(args.url).images
        with open(args.path,'rb') as f:
            images.load(
                f
            )
        return public.returnMsg(True,"导入成功！")

    # 列出所有镜像
    def image_list(self,args):
        """
        :param url
        :param args:
        :return:
        """
        images = self.docker_client(args.url).images
        return public.returnMsg(True,self.get_image_attr(images))

    def get_image_attr(self,images):
        image = images.list()
        return [i.attrs for i in image]

    # 构建镜像
    def build(self,args):
        """
        :param path         dockerfile
        :param pull         如果引用的镜像有更新自动拉取
        :param tag          标签
        :param args:
        :return:
        """
        self.docker_client(args.url).images.build(
            pull=True if args.pull=="1" else False,
            path=args.path,
            tag=args.tag
        )
        return public.returnMsg(True,"构造成功！")

    # 获取服务器容器数量
    def get_container_count(self):
        self.docker_client()

    # 删除镜像
    def remove(self,args):
        import docker.errors
        """
        :param url
        :param id  镜像id
        :param args:
        :return:
        """
        try:
            self.docker_client(args.url).images.remove(args.id)
            return public.returnMsg(True,"镜像删除成功！")
        except docker.errors.ImageNotFound as e:
            return public.returnMsg(True,"删除镜像失败，可能是镜像不存在！")

    # 拉取指定仓库镜像
    def pull_from_some_registry(self,args):
        """
        :param name 仓库名
        :param url
        :param image
        :param args:
        :return:
        """
        import projectModel.bt_docker.registry as br
        r_info = br.registry().registry_info(args.name)
        login = br.registry().login(args.url,r_info['url'],r_info['username'],r_info['password'])['status']
        if not login:
            return login
        args.username = r_info['username']
        args.password = r_info['password']
        args.registry = r_info['url']
        return self.pull(args)

    # 推送镜像到指定仓库
    def push(self,args):
        """
        :param id       镜像ID
        :param url      连接docker的url
        :param tag      标签 v1
        :param name     仓库名
        :param args:
        :return:
        """
        import projectModel.bt_docker.registry as br
        r_info = br.registry().registry_info(args.name)
        login = br.registry().login(args.url,r_info['url'],r_info['username'],r_info['password'])['status']
        if not login:
            return login
        auth_conf = {"username": r_info['username'],
                     "password": r_info['password'],
                     "registry": r_info['url']
                     }
        # args.repository       namespace/image
        args.repository = "{}/{}".format(r_info['url'],args.repository) if r_info['url'] != "docker.io" else args.repository
        self.tag(args.url,args.id,args.repository,args.tag)
        ret = self.docker_client(args.url).images.push(
            repository=args.repository,
            tag=args.tag if args.tag else "latest",
            auth_config=auth_conf,
        )
        return ret

    def tag(self,url,image_id,repository,tag):
        """
        为镜像打标签
        :param repository   namespace/images
        :param id:
        :param tag:         v1
        :return:
        """
        self.docker_client(url).images.get(image_id).tag(
            repository=repository,
            tag=tag
        )
        return public.returnMsg(True,"设置成功")

    # 拉取镜像
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
        import docker.errors
        try:
            if ':' not in args.image:
                args.image = '{}:latest'.format(args.image)
            auth_conf = {"username": args.username,
                         "password": args.password,
                         "registry":args.registry if args.registry else None
                         } if args.username else None


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
                return public.returnMsg(False,"拉取失败，该镜像为私有镜像需要输入dockerhub的账号密码！")
            return public.returnMsg(False,"拉取失败<br><br>原因: {}".format(e))