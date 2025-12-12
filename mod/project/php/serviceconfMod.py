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
import re

from mod.base.web_conf import IpRestrict, Referer, NginxGzipMgr, NginxStaticCacheMgr
from mod.base import json_response, list_args
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

    @staticmethod
    def set_nginx_static_cache(get):
        if public.get_webserver() != "nginx":
            return json_response(False, '当前Web服务器非Nginx,不支持设置')

        suffix = list_args(get, 'suffix')
        old_suffix = list_args(get, 'old_suffix')
        time_out = get.get('time_out/s', '')
        site_name = get.get('site_name/s', '')
        suffix = [i for i in suffix if i.strip() and not re.search(r"\s",  i)]
        old_suffix = [i for i in old_suffix if i.strip() and not re.search(r"\s",  i)]
        if not suffix or not site_name:
            return json_response(False, '请填写缓存后缀')
        if not re.match(r"^\d+[smhd]$", time_out):
            return json_response(False, '请填写正确的缓存时间')
        nsc = NginxStaticCacheMgr()
        err = nsc.can_set_cache(site_name)
        if err:
            return json_response(False, err)
        ret = nsc.set_cache(site_name, old_suffix, suffix, time_out)
        if ret:
            return json_response(False, ret)
        return json_response(True, '设置成功')

    @staticmethod
    def remove_nginx_static_cache(get):
        if public.get_webserver() != "nginx":
            return json_response(False, '当前Web服务器非Nginx,不支持设置')
        site_name = get.get('site_name/s', '')
        suffix = list_args(get, 'suffix')
        suffix = [i for i in suffix if i.strip() and not re.search(r"\s",  i)]
        if not suffix or not site_name:
            return json_response(False, '请填写缓存后缀')
        ret = NginxStaticCacheMgr().remove_cache(site_name, suffix)
        if ret:
            return json_response(False, ret)
        return json_response(True, '删除成功')

    @staticmethod
    def get_nginx_static_cache(get):
        if public.get_webserver() != "nginx":
            return json_response(False, '当前Web服务器非Nginx,不支持设置')
        site_name = get.get('site_name/s', '')
        if not site_name:
            return json_response(False, '请填写站点名称')
        ret = NginxStaticCacheMgr().read_cache(site_name)
        return json_response(True, '获取成功', data=ret)

