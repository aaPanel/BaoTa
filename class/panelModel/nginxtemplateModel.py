# coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author: baozi <baozi@bt.cn>
# -------------------------------------------------------------------
# 网站nginx配置模板
# ------------------------------
import os
import re
import time

import public


class main:
    _template_dir = "{}/data/nginx_template".format(public.get_panel_path())
    _use_template = "{}/data/use_nginx_template.pl".format(public.get_panel_path())

    def __init__(self):
        if not os.path.exists(self._template_dir):
            os.makedirs(self._template_dir)

        # if not os.path.exists(self._template_json):
        #     public.writeFile(self._template_json, "[]")

    @staticmethod
    def get_default_template(get):
        return """server
{{
    listen {listen_port};{listen_ipv6}
    server_name {site_name};
    index index.php index.html index.htm default.php default.htm default.html;
    root {site_path};
    #CERT-APPLY-CHECK--START
    # 用于SSL证书申请时的文件验证相关配置 -- 请勿删除
    include /www/server/panel/vhost/nginx/well-known/{site_name}.conf;
    #CERT-APPLY-CHECK--END

    #SSL-START %s
    #error_page 404/404.html;
    #SSL-END

    #ERROR-PAGE-START  %s
    {error_page_line}
    #error_page 502 /502.html;
    #ERROR-PAGE-END

    #PHP-INFO-START  %s
    include enable-php-{php_version}.conf;
    #PHP-INFO-END

    #REWRITE-START %s
    include {setup_path}/panel/vhost/rewrite/{site_name}.conf;
    #REWRITE-END

    #禁止访问的文件或目录
    location ~ ^/(\.user.ini|\.htaccess|\.git|\.env|\.svn|\.project|LICENSE|README.md)
    {{
        return 404;
    }}

    #一键申请SSL证书验证目录相关设置
    location ~ \.well-known{{
        allow all;
    }}

    #禁止在证书验证目录放入敏感文件
    if ( $uri ~ "^/\.well-known/.*\.(php|jsp|py|js|css|lua|ts|go|zip|tar\.gz|rar|7z|sql|bak)$" ) {{
        return 403;
    }}

    location ~ .*\\.(gif|jpg|jpeg|png|bmp|swf)$
    {{
        expires      30d;
        error_log /dev/null;
        access_log /dev/null;
    }}

    location ~ .*\\.(js|css)?$
    {{
        expires      12h;
        error_log /dev/null;
        access_log /dev/null;
    }}
    access_log  {log_path}/{site_name}.log;
    error_log  {log_path}/{site_name}.error.log;
}}""" % (public.getMsg('NGINX_CONF_MSG1'),
         public.getMsg('NGINX_CONF_MSG2'),
         public.getMsg('NGINX_CONF_MSG3'),
         public.getMsg('NGINX_CONF_MSG4')
         )

    def save_template(self, get):
        try:
            name = get.template_name.strip()
            template_body = get.template_body
        except AttributeError:
            return public.returnMsg(False, "参数错误")

        # for i in os.listdir(self._template_dir):
        #     if i == name:
        #         return public.returnMsg(False, "该名称的配置模板已经存在")

        if public.checkWebConfig() is not True:
            return public.returnMsg(False, "当前nginx配置文件存在错误，无法判断您的模板是否可以生效，请先解决这个配置问题")

        # 检测项目(listen server_name root )
        rep_list = (
            (
                re.compile(r"listen +\{listen_port};\{listen_ipv6}"),
                "不能删除监听端口相关的配置"
            ),
            (
                re.compile(r"server_name +\{site_name};"),
                "不能删除域名绑定相关的配置"
            ),
            (
                re.compile(r"root +\{site_path};"),
                "不能删除网站根目录相关的配置"
            )
        )

        for r, msg in rep_list:
            if not r.search(template_body):
                return public.returnMsg(False, msg)
        test_name = "tmp.test-{}.com".format(int(time.time()))
        test_dir = "/www/wwwroot/tmp_{}".format(int(time.time()))
        default_test = {
            "listen_port": "80",
            "listen_ipv6": "",
            "site_path": test_dir,
            "php_version": "00",
            "setup_path": "/www/server",
            "log_path": "/www/wwwlogs",
            "site_name": test_name,
            "error_page_line": "#error_page 404 /404.html;",
        }

        if not os.path.exists(test_dir):
            os.makedirs(test_dir)

        test_nginx_conf = "{}/vhost/nginx/0.test_{}.conf".format(public.get_panel_path(), int(time.time()))
        test_well_known = "/www/server/panel/vhost/nginx/well-known/{}.conf".format(test_name)
        test_rewrite = "/www/server/panel/vhost/rewrite/{}.conf".format(test_name)
        try:
            public.writeFile(test_nginx_conf, template_body.format(**default_test))
            public.writeFile(test_well_known, "")
            public.writeFile(test_rewrite, "")
        except:
            os.rmdir(test_dir)
            return public.returnMsg(False, "模板无法格式化，不能进行保存")

        is_error = public.checkWebConfig()

        os.remove(test_nginx_conf)
        os.remove(test_well_known)
        os.remove(test_rewrite)
        os.rmdir(test_dir)
        if is_error is not True:
            return public.returnMsg(False, "尝试使用该模板创建网站失败，请检测，模板是否存在问题")

        public.writeFile(self._template_dir + "/" + name, template_body)
        return public.returnMsg(True, "保存成功")

    def get_template(self, get):
        try:
            name = get.template_name.strip()
        except AttributeError:
            return public.returnMsg(False, "参数错误")

        file_name = None
        for i in os.listdir(self._template_dir):
            if i == name:
                file_name = "{}/{}".format(self._template_dir, i)
                if not os.path.isfile(file_name):
                    return public.returnMsg(False, "指定的模板不存在")

        if file_name is None:
            return public.returnMsg(False, "指定的模板不存在")

        return public.readFile(file_name)

    def remove_template(self, get):
        try:
            name = get.template_name.strip()
        except AttributeError:
            return public.returnMsg(False, "参数错误")
        if not os.path.isfile(self._template_dir + "/" + name):
            return public.returnMsg(False, "模板不存在")

        os.remove(self._template_dir + "/" + name)

        return public.returnMsg(True, "删除完成")

    def get_template_list(self, get=None):
        used = public.readFile(self._use_template)
        res = []
        not_default = False
        for i in os.listdir(self._template_dir):
            file_name = os.path.join(self._template_dir, i)
            if os.path.isfile(file_name):
                use = i == used
                if use:
                    not_default = True
                res.append({
                    "name": i,
                    "file_path": file_name,
                    "use": use,
                    "time": int(os.path.getmtime(file_name))
                })

        res.insert(0, {
            "name": "官方默认模板",
            "file_path": "",
            "time": 0,
            "use": False if not_default else True
        })

        return res

    def set_use_template(self, get):
        try:
            name = get.template_name.strip()
        except AttributeError:
            return public.returnMsg(False, "参数错误")
        if not os.path.isfile(self._template_dir + "/" + name):
            return public.returnMsg(False, "模板不存在")

        public.writeFile(self._use_template, name)

        return public.returnMsg(True, "修改完成")

    def set_default_template(self, get):
        public.writeFile(self._use_template, "")
        return public.returnMsg(True, "修改完成")
