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
import os
import json
import projectModel.bt_docker.dk_public as dp

class main:

    def docker_client(self,url):
        return dp.docker_client(url)

    def add(self,args):
        """
        添加仓库
        :param registry 仓库URL docker.io
        :param name
        :parma username
        :parma password
        :param namespace 仓库命名空间
        :param remark 备注
        :param args:
        :return:
        """
        # 验证登录
        if not args.registry:
            args.registry = "docker.io"
        res = self.login(args.url,args.registry,args.username,args.password)
        if not res['status']:
            return res
        r_list = self.registry_list("get")['msg']['registry']
        for r in r_list:
            if r['name'] == args.name:
                return public.returnMsg(False,"名字已经存在！ <br><br>名称：{}".format(args.name))
            if r['username'] == args.username and args.registry == r['url']:
                return public.returnMsg(False,"仓库信息已存在！")
        pdata = {
            "name": args.name,
            "url": args.registry,
            "namespace": args.namespace,
            "username": args.username,
            "password": args.password,
            "remark": public.xsssec(args.remark)
        }
        dp.sql("registry").insert(pdata)
        dp.write_log("添加仓库 [{}] [{}] 成功！".format(args.name,args.registry))
        return public.returnMsg(True,"添加成功！")

    def edit(self,args):
        """
        添加仓库
        :param registry 仓库URL docker.io
        :param id 仓库id
        :parma username
        :parma password
        :param namespace
        :param remark
        :param args:
        :return:
        """
        # 验证登录
        if str(args.id) == "1":
            return public.returnMsg(False,"【Docker官方仓库】不可编辑！")
        if not args.registry:
            args.registry = "docker.io"
        res = self.login(args.url,args.registry,args.username,args.password)
        if not res['status']:
            return res
        res = dp.sql("registry").where("id=?",(args.id,)).find()
        if not res:
            return public.returnMsg(False,"找不到此仓库")
        pdata = {
            "name": args.name,
            "url": args.registry,
            "username": args.username,
            "password": args.password,
            "namespace": args.namespace,
            "remark": args.remark
        }
        dp.sql("registry").where("id=?",(args.id,)).update(pdata)
        dp.write_log("编辑仓库 [{}][{}] 成功！".format(args.name, args.registry))
        return public.returnMsg(True,"编辑成功!")

    def remove(self, args):
        """
        删除某个仓库
        :param id
        :param rags:
        :return:
        """
        if str(args.id) == "1":
            return public.returnMsg(False,"【Docker官方仓库】无法删除！")
        data = dp.sql("registry").where("id=?",(args.id)).find()
        dp.sql("registry").where("id=?",(args.id,)).delete()
        dp.write_log("删除存储库 [{}][{}] 成功！".format(data['name'],data['url']))
        return public.returnMsg(True,"成功删除！")

    def registry_list(self,args):
        """
        获取仓库列表
        :return:
        """
        import projectModel.bt_docker.dk_setup as ds
        res = dp.sql("registry").select()
        if not isinstance(res,list):
            res = []
        docker_setup = ds.main()
        data = {
            "registry": res,
            "installed": docker_setup.check_docker_program(),
            "service_status": docker_setup.get_service_status()
        }
        return public.returnMsg(True,data)

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
                return public.returnMsg(False,"登录测试失败！ <br><br>原因：账号密码错误！ {}".format(e))
            return public.returnMsg(False,"登录测试失败！ <br><br>原因：{}".format(e))