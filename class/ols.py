# coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http:#bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author: zhwwen <zhw@bt.cn>
# -------------------------------------------------------------------
#
# ------------------------------
# OLS管理模块
# ------------------------------
import public,re,json,os

class ols:
    _main_conf_path = '/usr/local/lsws/conf/httpd_config.conf'
    _detail_conf_path = '/www/server/panel/vhost/openlitespeed/detail/{}.conf'

    def get_value(self,get):
        """
        :param get:
        get.sitename
        :return:
        """
        keys = ["enableGzipCompress","gzipCompressLevel","rollingSize","maxConnections","maxSSLConnections","connTimeout","maxKeepAliveReq"]
        conf = public.readFile(self._main_conf_path)
        data = {}
        for k in keys:
            rep = '{}\s+(\w+)'.format(k)
            tmp = re.search(rep,conf)
            if tmp:
                data[k] = tmp.groups(1)
            else:
                data[k] = ''
        return data

    def set_value(self,get):
        """
        :param get:
        get.array
        :return:
        """
        conf = public.readFile(self._main_conf_path)
        data = json.loads(get.array)
        for k in data:
            rep = '{}\s+(\w+)'.format(k)
            tmp = re.search(rep,conf)
            if tmp:
                conf = re.sub('{}.*'.format(k),'{} {}'.format(k,data[k]),conf)
            else:
                conf = conf + '\n{} {}'.format(k,data[k])
        public.writeFile(self._main_conf_path,conf)
        public.serviceReload()
        return public.returnMsg(True,"设置成功！")

    # 获取站点静态文件缓存配置
    def get_static_cache(self,get):
        data = {}
        sitename = public.M('sites').where("id=?", (get.id,)).getField('name')
        conf = public.readFile(self._detail_conf_path.format(sitename))
        rep = 'expiresByType\s+(.*)'
        tmp = re.search(rep,conf)

        if tmp:
            tmp = tmp.groups(1)[0].split(',')
            for i in tmp:
                if 'image' in i:
                    rep = 'image\/\*=A(\d+)'
                    data['image'] = re.search(rep,conf).groups(1)[0]
                    print(data['image'])
                if 'css' in i:
                    rep = 'css=A(\d+)'
                    data['css'] = re.search(rep, conf).groups(1)[0]
                if 'javascript' in i:
                    rep = 'javascript=A(\d+)'
                    data['javascript'] = re.search(rep, conf).groups(1)[0]
                if 'font' in i:
                    rep = 'font.*=A(\d+)'
                    data['font'] = re.search(rep, conf).groups(1)[0]
        return data

    def set_static_cache(self,get):
        """
        :param get:
        get.values
        get.id
        :return:
        """
        try:
            sitename = public.M('sites').where("id=?", (get.id,)).getField('name')
            conf = public.readFile(self._detail_conf_path.format(sitename))
            print(self._detail_conf_path.format(sitename))
            values = json.loads(get.values)
            for k in values:
                rep = '{}/[\*\w+=]=A\d+'.format(k)
                old_cache = re.search(rep,conf)
                if not old_cache:
                    continue
                old_cache = old_cache.group()
                new_cache = re.sub('\d+',values[k],old_cache)
                conf = conf.replace(old_cache,new_cache)
            public.writeFile(self._detail_conf_path.format(sitename),conf)
            public.serviceReload()
            return public.returnMsg(True,'设置成功！')
        except Exception as e:
            return e

    def get_private_cache_conf(self,id):
        sitepath = public.M('sites').where("id=?", (id,)).getField('path')
        # 获取动态缓存配置
        file = "{}/.htaccess".format(sitepath)
        conf = ''
        if os.path.exists(file):
            conf = public.readFile(file)
        return conf,file

    def get_private_cache(self,get):
        """
        :param get:
        get.id
        :return:
        """
        conf = self.get_private_cache_conf(get.id)[0]
        rep = '#*BTLSCACHE(.|\n)+BTLSCACHE_END.*'
        tmp = re.search(rep,conf)
        data = {}
        if tmp:
            # 获取排除文件
            tmp = tmp.group()
            rep = '#\s*excluding.*\n.*\((.*)\)'
            tmp = re.search(rep,tmp)
            if tmp:
                data['exclude_file'] = [i+'.php' for i in tmp.groups(1)[0].split('|')]
            print(data)
            # 获取缓存时间
            rep = 'max-age=(\d+)'
            tmp = re.search(rep,conf)
            if tmp:
                data['maxage'] = tmp.groups(1)[0]
        return data

    def get_private_cache_status(self,get):
        conf = self.get_private_cache_conf(get.id)[0]
        if 'BTLSCACHE_BEGIN' not in conf:
            return False
        return True

    def switch_private_cache(self,get):
        """
        get.id
        :param get:
        :return:
        """
        conf = self.get_private_cache_conf(get.id)[0]
        file = self.get_private_cache_conf(get.id)[1]
        if 'BTLSCACHE_BEGIN' not in conf:
            confstr = """#######################BTLSCACHE_BEGIN#######################

<IfModule LiteSpeed>
RewriteEngine on
CacheLookup on
# for those not met above condition, enable private cache.
RewriteCond %{REQUEST_METHOD} ^HEAD|GET$
## select which pages to serve from private cache
RewriteCond %{HTTP_COOKIE} !page_contain_cachetoken=yes
# with other condition
RewriteCond %{QUERY_STRING} !s=[a-fA-F0-9]{32}
# excluding certain URLs
RewriteCond %{REQUEST_URI} !/(login|register|usercp|private|profile|cron|image)\.php$
# private cache for however long set in cache policy for php pages only
RewriteRule (.*\.php)?$ - [E=Cache-Control:max-age=120]
RewriteRule (.*\.php)?$ - [E=Cache-Control:private]
</IfModule>

#######################BTLSCACHE_END#######################
"""
            with open(file, "r+") as f:
                f.seek(0)
                f.write(confstr)
                f.write(conf)
                f.close()
            public.serviceReload()
            return public.returnMsg(True,'开启成功！')
        else:
            bt_conf_rep = '#.*BTLSCACHE_BEGIN(.|\n)+BTLSCACHE_END#*\n'
            conf = re.sub(bt_conf_rep,'',conf)
            print(conf)
            public.writeFile(file,conf)
            public.serviceReload()
            return public.returnMsg(True,'关闭成功！')

    def set_private_cache(self,get):
        """
        get.exclude_file
        get.max_age
        :param get:
        :return:
        """
        conf = self.get_private_cache_conf(get.id)[0]
        file_name = self.get_private_cache_conf(get.id)[1]
        bt_conf_rep = '#.*BTLSCACHE_BEGIN(.|\n)+BTLSCACHE_END#*\n'
        bt_conf = re.search(bt_conf_rep, conf)
        if bt_conf:
            bt_conf = bt_conf.group()
            exclude_files = []
            for file in get.exclude_file.split('\n'):
                exclude_files.append(file.split('.')[0])
            exclude_file = "|".join(exclude_files)
            old_exc_rep = 'RewriteCond\s+\%\{REQUEST_URI\}\s+\!/\(.*\)\\\.php\$'
            new_exc = 'RewriteCond %{REQUEST_URI} !/(' + exclude_file + ')\.php$'
            bt_conf = re.sub(old_exc_rep,new_exc,bt_conf)
            old_max_age_rep = 'max-age=\d+'
            new_max_age = 'max-age={}'.format(int(get.max_age))
            bt_conf = re.sub(old_max_age_rep,new_max_age,bt_conf)
            conf = re.sub(bt_conf_rep,bt_conf,conf)
            public.writeFile(file_name,conf)
        public.serviceReload()
        return public.returnMsg(True,'设置成功！')

    def _get_site_domain(self):
        site = []
        site_list = public.M("sites").field("id,name").select()
        for i in site_list:
            domain_list = public.M("domain").where("pid=?", (i["id"],)).field("name").select()
            l = []
            for domain in domain_list:
                l.append(domain["name"])
            # site[i["name"]] = l
            site.append({'sitename':i["name"],'domainlist':l})
        return site

    def _get_need_create_site(self):
        siteinfo = self._get_site_domain()
        data = []
        for s in siteinfo:
            path = '/www/server/panel/vhost/openlitespeed/{}.conf'.format(s['sitename'])
            if not os.path.exists(path):
                data.append(s)
        return data

    def _get_siteconf_info(self):
        siteinfo = self._get_need_create_site()
        phpv_reg = r'enable-php-(\w+)\.conf'
        rundir_reg = r'root\s+(.*);'
        for s in siteinfo:
            path = '/www/server/panel/vhost/nginx/{}.conf'.format(s['sitename'])
            conf = public.readFile(path)
            ap_path = '/www/server/panel/vhost/apache/{}.conf'.format(s['sitename'])
            ap_conf = public.readFile(ap_path)
            tmp = re.search('ServerName\s+SSL\.(.*)',ap_conf)
            s['phpv'] = re.search(phpv_reg,conf).groups(1)[0]
            s['rundir']  = re.search(rundir_reg.format(s),conf).groups(1)[0]
            s['ssl_domain'] =tmp.groups(1)[0] if tmp else None
            s['port'] = re.search('listen\s+(\d+);',conf).groups(1)[0]
        return siteinfo

    def _make_args(self):
        # 获取没有ols配置的域名

        # 获取php版本和执行目录和是否开启ssl
        siteinfo = self._get_siteconf_info()
        return siteinfo

    def init_ols(self,get):
        # 构造需要传入的参数
        import panelSite
        ps = panelSite.panelSite()
        siteinfo = self._make_args()
        for s in siteinfo:
            # 创建配置文件
            get.port = s['port']
            get.webname = {'domain':s['sitename'],'domainlist':s['domainlist']}
            ps.openlitespeed_add_site(get,siteinfo)
            # 处理证书
            if s['ssl_domain']:
                get.first_domain = s['ssl_domain']
                ps.set_ols_ssl(get,s['ssl_domain'])
