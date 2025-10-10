# coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2015-2017 宝塔软件(http:#bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author: baozi <baozi@bt.cn>
# -------------------------------------------------------------------
# 服务配置模块
# ------------------------------

from mod.base.web_conf import IpRestrict, Referer, NginxGzipMgr
from mod.base import json_response
import public


class main(IpRestrict, Referer):   # 继承并使用同ip黑白名单限制
    def __init__(self):
        IpRestrict.__init__(self, config_prefix="")
        Referer.__init__(self, config_prefix="")

    @staticmethod
    def set_nginx_gzip(get):
        if public.get_webserver() != "nginx":
            return json_response(False, '当前Web服务器非Nginx,不支持设置')
        site_name = get.get('site_name/s', '')
        if not site_name:
            return json_response(False, '请指定站点名称')
        args = NginxGzipMgr.check_gzip_args(get)
        if isinstance(args, str):
            return json_response(False, args)
        ret = NginxGzipMgr().set_gzip(site_name, **args)
        if ret:
            return json_response(False, ret)

        return json_response(True, '设置成功')

    @staticmethod
    def remove_nginx_gzip(get):
        if public.get_webserver() != "nginx":
            return json_response(False, '当前Web服务器非Nginx,不支持设置')
        site_name = get.get('site_name/s', '')
        ret = NginxGzipMgr().remove_gzip(site_name)
        if ret:
            return json_response(False, ret)
        return json_response(True, '关闭成功')

    @staticmethod
    def get_nginx_gzip(get):
        if public.get_webserver() != "nginx":
            return json_response(False, '当前Web服务器非Nginx,不支持设置')
        site_name = get.get('site_name/s', '')
        ret, err = NginxGzipMgr().read_gzip(site_name)
        if err:
            return json_response(False, err)
        return json_response(True, '获取成功', data=ret)
