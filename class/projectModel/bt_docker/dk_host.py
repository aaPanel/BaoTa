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
import public
import projectModel.bt_docker.dk_public as dp

class main:

    # 获取docker主机列表
    def get_list(self,args=None):
        info = dp.sql("hosts").select()
        for i in info:
            if dp.docker_client(i['url']):
                i['status'] = True
            else:
                i['status'] = False
        return info

    # 添加docker主机
    def add(self,args):
        """
        :param url      连接主机的url
        :param remark   主机备注
        :return:
        """
        import time
        host_lists = self.get_list()
        for h in host_lists:
            if h['url'] == args.url:
                return public.returnMsg(False,"该主机已存在！")
        # 测试连接
        if not dp.docker_client(args.url):
            return public.returnMsg(False,"连接服务器失败，请检查docker是否已经启动！")
        pdata = {
            "url": args.url,
            "remark": public.xsssec(args.remark),
            "time": int(time.time())
        }
        dp.write_log("添加主机 [{}] 成功！".format(args.url))
        dp.sql('hosts').insert(pdata)
        return public.returnMsg(True,"添加docker主机成功！")

    def delete(self,args):
        """
        :param id      连接主机id
        :return:
        """
        data = dp.sql('hosts').where('id=?',args(args.id,)).find()
        dp.sql('hosts').delete(id=args.id)
        dp.write_log("删除主机 [{}] 成功！".format(data['url']))
        return public.returnMsg(True,"删除主机成功！")