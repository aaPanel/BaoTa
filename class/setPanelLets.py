#coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: 邹浩文 <627622230@qq.com>
# +-------------------------------------------------------------------
import os
os.chdir("/www/server/panel")
import public,db,panelSSL,json


class setPanelLets:
    __vhost_cert_path = "/www/server/panel/vhost/ssl/"
    __panel_cert_path = "/www/server/panel/ssl/"
    __tmp_key = ""
    __tmp_cert = ""
    def __init__(self):
        pass

    # 保存面板证书
    def __save_panel_cert(self,cert,key):
        keyPath = 'ssl/privateKey.pem'
        certPath = 'ssl/certificate.pem'
        checkCert = '/tmp/cert.pl'
        public.writeFile(checkCert,cert)
        if key:
            public.writeFile(keyPath,key)
        if cert:
            public.writeFile(certPath,cert)
        if not public.CheckCert(checkCert): return public.returnMsg(False,'证书错误,请检查!')
        public.writeFile('ssl/input.pl','True')
        return public.returnMsg(True,'证书已保存!')

    # 检查是否存在站点aapanel主机名站点
    def __check_host_name(self, domain):
        sql = db.Sql()
        path = sql.table('sites').where('name=?', (domain,)).getField('path')
        return path

    # 创建证书使用的站点
    def __create_site_of_panel_lets(self,get):
        import panelSite
        ps = panelSite.panelSite()
        get.webname = json.dumps({"domain":get.domain,"domainlist":[],"count":0})
        get.ps = "用于面板Let's Encrypt 证书申请和续签，请勿删除"
        get.path = "/www/wwwroot/panel_ssl_site"
        get.ftp = "false"
        get.sql = "false"
        get.codeing = "utf8"
        get.type = "PHP"
        get.version = "00"
        get.type_id = "0"
        get.port = "80"
        psa = ps.AddSite(get)
        if "status" in psa.keys():
            return psa

    # 申请面板域名证书
    def __create_lets(self,get):
        import panelSite
        ps = panelSite.panelSite()
        get.siteName = get.domain
        get.updateOf = "1"
        get.domains = json.dumps([get.domain])
        get.force = "true"
        psc = ps.CreateLet(get)
        if "False" in psc.values():
            return psc

    # 检查证书夹是否存在可用证书
    def __check_cert_dir(self,get):
        pssl = panelSSL.panelSSL()
        gcl = pssl.GetCertList(get)
        for i in gcl:
            if get.domain in i.values():
                return i

    # 读取可用站点证书
    def __read_site_cert(self,domain_cert):
        self.__tmp_key = public.readFile("{path}{domain}/{key}".format(path=self.__vhost_cert_path,domain=domain_cert["subject"],key="privkey.pem"))
        self.__tmp_cert = public.readFile(
            "{path}{domain}/{cert}".format(path=self.__vhost_cert_path, domain=domain_cert["subject"],
                                           cert="fullchain.pem"))
        public.writeFile("/tmp/2",str(self.__tmp_cert))

    # 检查面板证书是否存在
    def __check_panel_cert(self):
        key = public.readFile(self.__panel_cert_path+"privateKey.pem")
        cert = public.readFile(self.__panel_cert_path+"certificate.pem")
        if key and cert:
            return {"key":key,"cert":cert}

    # 写面板证书
    def __write_panel_cert(self):
        public.writeFile(self.__panel_cert_path + "privateKey.pem", self.__tmp_key)
        public.writeFile(self.__panel_cert_path + "certificate.pem", self.__tmp_cert)

    # 记录证书源
    def __save_cert_source(self,domain,email):
        public.writeFile(self.__panel_cert_path+"lets.info",json.dumps({"domain":domain,"cert_type":"2","email":email}))

    # 获取证书源
    def get_cert_source(self):
        data = public.readFile(self.__panel_cert_path+"lets.info")
        if not data:
            return {"cert_type":"","email":"","domain":""}
        return json.loads(data)

    # 检查面板是否绑定域名
    def __check_panel_domain(self):
        domain = public.readFile("/www/server/panel/data/domain.conf")
        if not domain:
            return False
        return domain

    # 复制证书
    def copy_cert(self,domain_cert):
        self.__read_site_cert(domain_cert)
        panel_cert_data = self.__check_panel_cert()
        if not panel_cert_data:
            self.__write_panel_cert()
            return True
        else:
            if panel_cert_data["key"] == self.__tmp_key and panel_cert_data["cert"] == self.__tmp_cert:
                pass
            else:
                self.__write_panel_cert()
                return True

    # 设置lets证书
    def set_lets(self,get):
        """
        传入参数
        get.domain  面板域名
        get.email   管理员email
        """
        create_site = ""
        domain = self.__check_panel_domain()
        get.domain = domain
        if not domain:
            return public.returnMsg(False, '需要为面板绑定域名后才能申请 Let\'s Encrypt 证书')
        if not self.__check_host_name(domain):
            create_site = self.__create_site_of_panel_lets(get)
        domain_cert = self.__check_cert_dir(get)
        if domain_cert:
            self.copy_cert(domain_cert)
            public.writeFile("/www/server/panel/data/ssl.pl", "True")
            public.writeFile("/www/server/panel/data/reload.pl","1")
            self.__save_cert_source(domain,get.email)
            return public.returnMsg(True, '面板lets https设置成功')
        if not create_site:
            create_lets = self.__create_lets(get)
            if not create_lets:
                domain_cert = self.__check_cert_dir(get)
                self.copy_cert(domain_cert)
                public.writeFile("/www/server/panel/data/ssl.pl", "True")
                public.writeFile("/www/server/panel/data/reload.pl", "1")
                self.__save_cert_source(domain, get.email)
                return  public.returnMsg(True, '面板lets https设置成功')
            else:
                return create_lets
        else:
            return create_site
