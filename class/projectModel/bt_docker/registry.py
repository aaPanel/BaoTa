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
import projectModel.bt_docker.public as dp

class registry:

    def docker_client(self,url):
        import projectModel.bt_docker.public as dp
        return dp.docker_client(url)

    def add(self,args):
        """
        添加仓库
        :param registry 仓库URL docker.io
        :param name
        :parma username
        :parma password
        :param args:
        :return:
        """
        # 验证登录
        if not args.registry:
            args.registry = "docker.io"
        res = self.login(args.url,args.registry,args.username,args.password)
        if not res['status']:
            return res
        r_list = self.registry_list()['msg']
        for r in r_list:
            if r['name'] == args.name:
                return public.returnMsg(False,"名称已经存在！<br><br>名称: {}".format(args.name))
            if r['username'] == args.username and args.registry == r['url']:
                return public.returnMsg(False,"该仓库信息已经存在！")
        pdata = {
            "name": args.name,
            "url": args.registry,
            "username": args.username,
            "password": args.password
        }
        dp.sql("registry").insert(pdata)
        return public.returnMsg(True,"添加成功！")

    def remove(self, args):
        """
        删除某个仓库
        :param name
        :param rags:
        :return:
        """
        dp.sql("registry").where("name=?",(args.name,)).delete()
        return public.returnMsg(True,"删除成功！")

    def registry_list(self):
        """
        获取仓库列表
        :return:
        """
        return public.returnMsg(True,dp.sql("registry").select())

    def registry_info(self,name):
        return dp.sql("registry").where("name=?",(name,)).find()

    def login(self, url, registry, username, password):
        """
        仓库登录测试
        :param args:
        :return:
        """
        import docker.errors
        try:
            res = self.docker_client(url).login(
                registry=registry,
                username=username,
                password=password,
                reauth=False
            )
            return public.returnMsg(True,str(res))
        except docker.errors.APIError as e:
            if "unauthorized: incorrect username or password" in str(e):
                return public.returnMsg(False,"登录测试失败！<br><br>原因: 账号密码错误！{}".format(e))
            return public.returnMsg(False,"登录测试失败！<br><br>原因: {}".format(e))