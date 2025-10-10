#coding: utf-8
#-------------------------------------------------------------------
# 宝塔Linux面板
#-------------------------------------------------------------------
# Copyright (c) 2015-2018 宝塔软件(http:#bt.cn) All rights reserved.
#-------------------------------------------------------------------
# Author: hwliang <hwl@bt.cn>
# Author: hezhihong <272267659@bt.cn>
#-------------------------------------------------------------------

#------------------------------
# URL重写类
#------------------------------
import os,public,json,re,sys,socket,shutil
os.chdir("/www/server/panel")
class panelRedirect:

    setupPath = '/www/server'
    __redirectfile = "/www/server/panel/data/redirect.conf"
    __firsturl=""

    #匹配目标URL的域名并返回
    def GetToDomain(self,tourl):
        if tourl:
            rep = "https?://([\w\-\.]+)"
            tu = re.search(rep, tourl)
            return tu.group(1)

    #取某个站点下所有域名
    def GetAllDomain(self,sitename):
        domains = []
        id = public.M('sites').where("name=?",(sitename,)).getField('id')
        tmp = public.M('domain').where("pid=?",(id,)).field('name').select()
        for key in tmp:
            domains.append(key["name"])
        return domains

    #检测被重定向域名是否有已经存在配置文件里面
    def __CheckRepeatDomain(self,get,action):
        conf_data = self.__read_config(self.__redirectfile)
        repeat = []
        # for conf in conf_data:
        #     if conf["sitename"] == get.sitename and conf["redirectname"] != get.redirectname:
        #         repeat += list(set(conf["redirectdomain"]).intersection(set(get.redirectdomain)))


        for conf in conf_data:
            if conf["sitename"] == get.sitename:
                if action == "create":
                    if  conf["redirectname"] == get.redirectname:
                        repeat += list(set(conf["redirectdomain"]).intersection(set(get.redirectdomain)))
                else:
                    if conf["redirectname"] != get.redirectname:
                        repeat += list(set(conf["redirectdomain"]).intersection(set(get.redirectdomain)))
        if list(set(repeat)):
            return list(set(repeat))

    #检测被重定向路径是否重复
    def __CheckRepeatPath(self, get):
        conf_data = self.__read_config(self.__redirectfile)
        repeat = []
        for conf in conf_data:
            if conf["sitename"] == get.sitename and get.redirectpath != "":
                if  conf["redirectname"] != get.redirectname and conf["redirectpath"] == get.redirectpath:
                    repeat.append(get.redirectpath)
        if repeat:
            return repeat
    # 检测URL是否可以访问
    def __CheckRedirectUrl(self, domainlist):
        """
        @name 检测URL是否可以访问
        @author: hezhihong
        @param domainlist: 域名列表 
        """
        http_list=[]
        import requests
        for i in domainlist:
            i = i.replace("*.", "")
            https_url = "https://" + i
            http_url = "http://" + i
            try:
                response=requests.get(https_url,timeout=20)
                if response.status_code==200:return https_url
            except:pass
            try:
                response=requests.get(http_url,timeout=20)
                if response.status_code==200:http_list.append(http_url) 
            except:pass
        if http_list:return http_list[0] 
        else:return []
        
    # 计算proxyname md5
    def __calc_md5(self,redirectname):
        import hashlib
        md5 = hashlib.md5()
        md5.update(redirectname.encode('utf-8'))
        return md5.hexdigest()

    # 设置Nginx配置
    def SetRedirectNginx(self,get):
        ng_redirectfile = "%s/panel/vhost/nginx/redirect/%s/*.conf" % (self.setupPath,get.sitename)
        ng_file = self.setupPath + "/panel/vhost/nginx/" + get.sitename + ".conf"
        p_conf = self.__read_config(self.__redirectfile)
        if public.get_webserver() == 'nginx':
            shutil.copyfile(ng_file, '/tmp/ng_file_bk.conf')
        if os.path.exists(ng_file):
            ng_conf = public.readFile(ng_file)
            if not p_conf:
                rep = "#SSL-END(\n|.)*\/redirect\/.*\*.conf;"
                ng_conf = re.sub(rep, '#SSL-END', ng_conf)
                public.writeFile(ng_file, ng_conf)
                return
            sitenamelist = []
            for i in p_conf:
                sitenamelist.append(i["sitename"])

            if get.sitename in sitenamelist:
                rep = "include.*\/redirect\/.*\*.conf;"
                if not re.search(rep,ng_conf):
                    ng_conf = ng_conf.replace("#SSL-END","#SSL-END\n\t#引用重定向规则，注释后配置的重定向代理将无效\n\t" + "include " + ng_redirectfile + ";")
                    public.writeFile(ng_file,ng_conf)

            else:
                rep = "#SSL-END(\n|.)*\/redirect\/.*\*.conf;"
                ng_conf = re.sub(rep,'#SSL-END',ng_conf)
                public.writeFile(ng_file, ng_conf)

    # 设置apache配置
    def SetRedirectApache(self,sitename):
        ap_redirectfile = "%s/panel/vhost/apache/redirect/%s/*.conf" % (self.setupPath,sitename)
        ap_file = self.setupPath + "/panel/vhost/apache/" + sitename + ".conf"
        p_conf = public.readFile(self.__redirectfile)
        if public.get_webserver() == 'apache':
            shutil.copyfile(ap_file, '/tmp/ap_file_bk.conf')
        if os.path.exists(ap_file):
            ap_conf = public.readFile(ap_file)
            if p_conf == "[]":
                rep = "\n*#引用重定向规则，注释后配置的重定向代理将无效\n+\s+IncludeOptiona[\s\w\/\.\*]+"
                ap_conf = re.sub(rep, '', ap_conf)
                public.writeFile(ap_file, ap_conf)
                return
            if sitename in p_conf:
                rep = "#引用重定向(\n|.)+IncludeOptional.*\/redirect\/.*conf"
                rep1 = "combined"
                if not re.search(rep,ap_conf):
                    ap_conf = ap_conf.replace(rep1, rep1 + "\n\t#引用重定向规则，注释后配置的重定向代理将无效" +"\n\tIncludeOptional " + ap_redirectfile)
                    public.writeFile(ap_file,ap_conf)
            else:
                rep = "\n*#引用重定向规则，注释后配置的重定向代理将无效\n+\s+IncludeOptiona[\s\w\/\.\*]+"
                ap_conf = re.sub(rep,'', ap_conf)
                public.writeFile(ap_file, ap_conf)

    # 创建修改配置检测
    def __CheckRedirectStart(self,get,action=""):
        isError = public.checkWebConfig()
        if (isError != True):
            return public.returnMsg(False, '配置文件出错请先排查配置')
        if action == "create":
            #检测名称是否重复
            if sys.version_info.major < 3:
                if len(get.redirectname) < 3 or len(get.redirectname) > 15:
                    return public.returnMsg(False, '名称必须大于3小于15个字符串')
            else:
                if len(get.redirectname.encode("utf-8")) < 3 or len(get.redirectname.encode("utf-8")) > 15:
                    return public.returnMsg(False, '名称必须大于3小于15个字符串')
            if 'errorpage' in get:is_error_page = True 
            else:is_error_page = False
            if self.__CheckRedirect(get.sitename,get.redirectname,is_error_page):
                return public.returnMsg(False, '指定重定向名称已存在')
        #检测目标URL格式
        rep = "http(s)?\:\/\/([a-zA-Z0-9][-a-zA-Z0-9]{0,62}\.)+([a-zA-Z0-9][a-zA-Z0-9]{0,62})+.?"
        if 'tourl' in get and get.tourl and not re.match(rep, get.tourl):
            return public.returnMsg(False, '目标URL格式不对 %s' + get.tourl)

        #非404页面重定向检测项
        if 'errorpage' not in get:
            #检测是否选择域名
            if get.domainorpath == "domain":
                if not json.loads(get.redirectdomain):
                    return public.returnMsg(False, '请选择重定向域名')
            else:
                if not get.redirectpath:
                    return public.returnMsg(False, '请输入重定向路径')
                #repte = "[\?\=\[\]\)\(\*\&\^\%\$\#\@\!\~\`{\}\>\<\,\',\"]+"
                # 检测路径格式
                if "/" not in get.redirectpath:
                    return public.returnMsg(False, "路径格式不正确，格式为/xxx")
                #if re.search(repte, get.redirectpath):
                #    return public.returnMsg(False, "代理目录不能有以下特殊符号 ?,=,[,],),(,*,&,^,%,$,#,@,!,~,`,{,},>,<,\,',\"]")
            #检测域名是否已经存在配置文件
            repeatdomain = self.__CheckRepeatDomain(get,action)
            if repeatdomain:
                return public.returnMsg(False, '重定向域名重复 %s' % (repeatdomain))
            #检测路径是否有存在配置文件
            repeatpath = self.__CheckRepeatPath(get)
            if repeatpath:
                return public.returnMsg(False, '重定向路径重复 %s' % (repeatpath))
            #检测目标URL是否可用
            #if self.__CheckRedirectUrl(get):
            #    return public.returnMsg(False, '目标URL无法访问')

            #检查目标URL的域名和被重定向的域名是否一样
            if get.domainorpath == "domain":
                for d in json.loads(get.redirectdomain):
                    tu = self.GetToDomain(get.tourl)
                    if d == tu:
                        return public.returnMsg(False,'域名 "%s" 和目标域名一致请取消选择' % (d))

            if get.domainorpath == "path":
                domains = self.GetAllDomain(get.sitename)
                rep = "https?://(.*)"
                tu = re.search(rep,get.tourl).group(1)
                for d in domains:
                    ad = "%s%s" % (d,get.redirectpath) #站点域名+重定向路径
                    if tu == ad:
                        return public.returnMsg(False, '"%s" ，目标URL和被重定向路径一致会导致无限重定向！请不要花样作死' % (tu))

        #404页面重定向检测项
        else:
            if 'tourl' not in get and 'topath' not in get:
                return public.returnMsg(False, '首页或自定义页面必须二选一')
            # #网站首页访问检测
            # if 'topath' in get and get.topath == "/":
            #     domainlist=self.GetAllDomain(get.sitename)
            #     self.__firsturl=self.__CheckRedirectUrl(domainlist)
            #     if not self.__firsturl:return public.returnMsg(False, '网站首页无法访问，请检查网站是否正常运行')

    #创建重定向
    def CreateRedirect(self,get):

        if self.__CheckRedirectStart(get,"create"):
            return self.__CheckRedirectStart(get,"create")
        redirectconf = self.__read_config(self.__redirectfile)
        redirectconf.append({
            "sitename":get.sitename,
            "redirectname":get.redirectname,
            "tourl":get.tourl,
            "redirectdomain":json.loads(get.redirectdomain),
            "redirectpath":get.redirectpath,
            "redirecttype":get.redirecttype,
            "type":int(get.type),
            "domainorpath":get.domainorpath,
            "holdpath":int(get.holdpath)
        })
        self.__write_config(self.__redirectfile,redirectconf)
        self.SetRedirectNginx(get)
        self.SetRedirectApache(get.sitename)
        self.SetRedirect(get)
        public.serviceReload()
        return public.returnMsg(True, '创建成功')


    def ModifyRedirect(self,get):
        """
        @name 修改、启用、禁用重定向
        @author hezhihong 
        @param get.sitename 站点名称
        @param get.redirectname 重定向名称
        @param get.tourl 目标URL
        @param get.redirectdomain 重定向域名
        @param get.redirectpath 重定向路径
        @param get.redirecttype 重定向类型
        @param get.type 重定向状态 0禁用 1启用
        @param get.domainorpath 重定向类型 domain 域名重定向 path 路径重定向
        @param get.holdpath 保留路径 0不保留 1保留
        @return json
        """
        # 基本信息检查
        if self.__CheckRedirectStart(get):
            return self.__CheckRedirectStart(get)
        redirectconf = self.__read_config(self.__redirectfile)
        for i in range(len(redirectconf)):
            domainorpath=''
            if 'domainorpath' not in get or not get.domainorpath:domainorpath='domain' if get.tourl else 'path'
            if not domainorpath:domainorpath=get.domainorpath
            if redirectconf[i]["redirectname"] == get.redirectname and redirectconf[i]["sitename"] == get.sitename:
                redirectconf[i]["tourl"] =get.tourl if 'tourl' in get and get.tourl else ""
                redirectconf[i]["redirectdomain"] = "" if 'redirectdomain' not in get else json.loads(get.redirectdomain)
                redirectconf[i]["redirectpath"] ="" if 'redirectpath' not in get else get.redirectpath
                redirectconf[i]["redirecttype"] ='' if 'redirecttype' not in get else get.redirecttype
                redirectconf[i]["type"] = int(get.type)
                redirectconf[i]["domainorpath"] = domainorpath
                redirectconf[i]["topath"] = "" if 'topath' not in get else get.topath
                redirectconf[i]["holdpath"] =999 if 'holdpath' not in get else int(get.holdpath) 
                redirectconf[i]["errorpage"]=1 if 'errorpage' in get and get.errorpage in [1,'1']  else 0
        self.__write_config(self.__redirectfile, redirectconf)
        redirect_path=get.tourl.strip() if 'tourl' in get and get.tourl else get.topath.strip()
        #404页面重定向
        is_del= True if int(get.type) == 0 else False
        if 'errorpage' in get and get.errorpage in [1,'1']:
            web_type=public.get_webserver()
            if web_type == 'nginx':
                self.SetRedirectNginx(get)
                self.unset_nginx_conf(get.sitename)
                self.get_nginx_conf(redirect_path,get.redirecttype,get.sitename,get.redirectname,is_del)
            elif web_type == 'apache' or web_type == 'openlitespeed':
                self.get_apache_conf(redirect_path,get.sitename,get.redirectname,str(get.redirecttype),is_del)
            else:
                return public.returnMsg(False,'未安装web服务器或未知的web服务器')
        #非404页面重定向
        else:
            self.SetRedirect(get)
            self.SetRedirectNginx(get)
            self.SetRedirectApache(get.sitename)
        public.serviceReload()
        print("修改成功")
        return public.returnMsg(True, '修改成功')


    def set_error_redirect(self,get):
        """
        @name 设置404重定向
        @author hezhihong
        @param get.sitename 站点名称
        @param get.redirectname 重定向名称(唯一key标志)
        @param get.tourl 重定向到的url
        @param get.topath 重定向到的路径
        @param get.redirecttype 重定向类型
        @param get.type 重定向状态 0禁用 1启用
        @param get.domainorpath 重定向类型 domain 域名重定向 path 路径重定向
        @param get.holdpath 是否保留原路径 0不保留 1保留
        @param get.errorpage 是否为404重定向 1是 0否
        @return json
        """
        public.set_module_logs('panelRedirect','set_error_redirect')
        check_result = self.__CheckRedirectStart(get,"create")
        if check_result:return check_result
        redirectconf = self.__read_config(self.__redirectfile)
        site_name= get.sitename.strip()
        redirect_path=get.tourl if  'tourl' in get and get.tourl and get.tourl.strip() else get.topath.strip()
        redirectconf.append({
            "sitename":site_name,
            "redirectname":get.redirectname,
            "tourl":get.tourl if 'tourl' in get else '',
            "redirectdomain":"",
            "redirectpath":"",
            "topath": get.topath.strip() if 'topath' in get and get.topath.strip() else "",
            "redirecttype":get.redirecttype,
            "type":int(get.type),
            "domainorpath":'domain' if 'tourl' in get else 'path', 
            "holdpath":999,
            "errorpage":1
        })
        self.__write_config(self.__redirectfile,redirectconf)
        web_type=public.get_webserver()
        if web_type == 'nginx':
            self.SetRedirectNginx(get)
            self.unset_nginx_conf(site_name)
            self.get_nginx_conf(redirect_path,get.redirecttype,site_name,get.redirectname)
        elif web_type == 'apache' or web_type == 'openlitespeed':
            self.SetRedirectApache(get.sitename)
            self.get_apache_conf(redirect_path,site_name,get.redirectname,str(get.redirecttype))
        else:
            return public.returnMsg(False,'未安装web服务器或未知的web服务器')
        public.serviceReload()
        return public.returnMsg(True, '404重定向设置成功')


    def get_nginx_conf(self,redirect_path,redirecttype,site_name,redirectname,is_del=False):
        """
        @name 设置nginx 404重定向
        @author hezhihong
        @param redirect_path 重定向到（路径或地址）
        @param redirecttype 重定向方式（301/302）
        @param site_name 站点名称
        @param redirectname 重定向名称（唯一key标志）
        @param is_del 是否删除
        """
        redirectname_md5 = self.__calc_md5(redirectname)
        file_path= "%s/panel/vhost/nginx/redirect/%s" % (self.setupPath,site_name)
        public.ExecShell("mkdir -p %s" % file_path)
        file_path+= '/%s_%s.conf' % (redirectname_md5, site_name)
        add_str='#REWRITE-START\nerror_page 404 = @notfound;\nlocation @notfound {\n    return '+str(redirecttype)+' '+ redirect_path+'; \n}\n#REWRITE-END'
        if os.path.isfile(file_path):public.ExecShell("rm -f %s" % file_path)
        if not is_del:public.writeFile(file_path,add_str)

    def get_apache_conf(self,redirect_path,site_name,redirectname='',r_type='301',is_del=False):
        """
        @name 设置apache 404重定向
        @author hezhihong
        @param redirect_path 重定向到（路径或地址）
        @param site_name 站点名称
        @param redirectname 重定向名称（唯一key标志）
        @param is_del 是否删除
        @param r_type 重定向方式
        """
        if self.__firsturl:redirect_path=self.__firsturl
        add_type=',R={}]'.format(str(r_type))
        add_str='#REWRITE-START\n<IfModule mod_rewrite.c>\n    RewriteEngine on\n    RewriteCond %\{REQUEST_FILENAME\} !-f\n    RewriteCond %{REQUEST_FILENAME} !-d\n    RewriteRule . '+redirect_path+' [L'+add_type+'\n</IfModule>\n#REWRITE-END'
        redirectname_md5 = self.__calc_md5(redirectname)
        file_path= "%s/panel/vhost/apache/redirect/%s" % (self.setupPath,site_name)
        public.ExecShell("mkdir -p %s" % file_path)
        file_path+= '/%s_%s.conf' % (redirectname_md5, site_name)
        if os.path.isfile(file_path):public.ExecShell("rm -f %s" % file_path)
        if not is_del:public.writeFile(file_path,add_str)
 

    def unset_nginx_conf(self,site_name):
        """
        @name 取消设置nginx 404重定向
        @author hezhihong
        @param site_name 站点名称
        """
        file_path='/www/server/panel/vhost/nginx/{}.conf'.format(site_name)
        hta_path='/www/server/panel/vhost/rewrite/{}.conf'.format(site_name)
        rep_str_one='error_page 404 /404.html'
        rep_str_two='location = /404.html'
        #清理nginx伪静态404配置
        hta_conf=public.readFile(hta_path)
        if hta_conf:
            hta_conf=self.replace_str_to_srt(hta_conf,rep_str_one,'','\n')
            hta_conf=self.replace_str_to_srt(hta_conf,rep_str_two,'','}')
        public.writeFile(hta_path,hta_conf)
        #清理nginx网站配置文件非include方式404配置
        conf=public.readFile(file_path)
        conf=self.replace_str_to_srt(conf,rep_str_one,'','\n')
        conf=self.replace_str_to_srt(conf,rep_str_two,'','}')
        public.writeFile(file_path,conf)


    def replace_str_to_srt(self,conf,str_src,str_d,end_str,is_replace=False):
        """
        @name 替换字符串
        @author hezhihong
        @param conf 配置文件内容
        @param str_src 要替换的字符串
        @param str_d 替换成的字符串
        @param end_str 结束字符串
        @param is_replace 是否替换 
        """
        if conf.strip():
            start_num=conf.find(str_src)
            if start_num !=-1:
                d_conf=conf[start_num:]
                end_num = d_conf.find(end_str)
                if end_num ==-1:end_num=len(conf)
                d_conf=d_conf[:end_num+1]
                if is_replace:conf=conf.replace(d_conf,str_d)
                else:conf=conf.replace(d_conf,'')
        return conf
        


    # 设置重定向
    def SetRedirect(self,get):
        ng_file = self.setupPath + "/panel/vhost/nginx/" + get.sitename + ".conf"
        ap_file = self.setupPath + "/panel/vhost/apache/" + get.sitename + ".conf"
        p_conf = self.__read_config(self.__redirectfile)
        # nginx
        # 构建重定向配置
        if int(get.type) == 1:
            domainstr = """
        if ($host ~ '^%s'){
            return %s %s%s;
        }
"""
            pathstr = """
        rewrite ^%s(.*) %s%s %s;
"""
            rconf = "#REWRITE-START"
            tourl = get.tourl
            # if tourl[-1] == "/":
            #     tourl = tourl[:-1]
            if get.domainorpath == "domain":
                domains = json.loads(get.redirectdomain)
                holdpath = int(get.holdpath)
                if holdpath == 1:
                    for sd in domains:
                        if sd.startswith("*."):
                            sd = r"[\w-.]+\." + sd[2:]
                        rconf += domainstr % (sd,get.redirecttype,tourl,"$request_uri")
                else:
                    for sd in domains:
                        if sd.startswith("*."):
                            sd = r"[\w-.]+\." + sd[2:]
                        rconf += domainstr % (sd,get.redirecttype,tourl,"")
            if get.domainorpath == "path":
                redirectpath = get.redirectpath
                if get.redirecttype == "301":
                    redirecttype = "permanent"
                else:
                    redirecttype = "redirect"
                if int(get.holdpath) == 1 and redirecttype == "permanent":
                    rconf += pathstr % (redirectpath,tourl,"$1",redirecttype)
                elif int(get.holdpath) == 0 and redirecttype == "permanent":
                    rconf += pathstr % (redirectpath, tourl,"",redirecttype)
                elif int(get.holdpath) == 1 and redirecttype == "redirect":
                    rconf += pathstr % (redirectpath,tourl,"$1",redirecttype)
                elif int(get.holdpath) == 0 and redirecttype == "redirect":
                    rconf += pathstr % (redirectpath, tourl,"",redirecttype)
            rconf += "#REWRITE-END"
            nginxrconf = rconf



            # 设置apache重定向

            domainstr = """
	<IfModule mod_rewrite.c>
		RewriteEngine on
		RewriteCond %s{HTTP_HOST} ^%s [NC]
		RewriteRule ^(.*) %s%s [L,R=%s]
	</IfModule>
"""
            pathstr = """
	<IfModule mod_rewrite.c>
		RewriteEngine on
		RewriteRule ^%s(.*) %s%s [L,R=%s]
	</IfModule>
"""
            rconf = "#REWRITE-START"
            if get.domainorpath == "domain":
                domains = json.loads(get.redirectdomain)
                holdpath = int(get.holdpath)
                if holdpath == 1:
                    for sd in domains:
                        if sd.startswith("*."):
                            sd = r"[\w-.]+\." + sd[2:]
                        rconf += domainstr % ("%",sd,tourl,"$1",get.redirecttype)
                else:
                    for sd in domains:
                        if sd.startswith("*."):
                            sd = r"[\w-.]+\." + sd[2:]
                        rconf += domainstr % ("%",sd,tourl,"",get.redirecttype)

            if get.domainorpath == "path":
                holdpath = int(get.holdpath)
                if holdpath == 1:
                    rconf += pathstr % (get.redirectpath,tourl,"$1",get.redirecttype)
                else:
                    rconf += pathstr % (get.redirectpath,tourl,"",get.redirecttype)
            rconf += "#REWRITE-END"
            apacherconf = rconf

            redirectname_md5 = self.__calc_md5(get.redirectname)
            for w in ["nginx","apache"]:
                redirectfile = "%s/panel/vhost/%s/redirect/%s/%s_%s.conf" % (self.setupPath,w,get.sitename,redirectname_md5, get.sitename)
                redirectdir = "%s/panel/vhost/%s/redirect/%s" % (self.setupPath,w,get.sitename)

                if not os.path.exists(redirectdir):
                    public.ExecShell("mkdir -p %s" % redirectdir)
                if w == "nginx":
                    public.writeFile(redirectfile,nginxrconf)
                else:
                    public.writeFile(redirectfile, apacherconf)
            isError = public.checkWebConfig()
            if (isError != True):
                if public.get_webserver() == "nginx":
                    shutil.copyfile('/tmp/ng_file_bk.conf', ng_file)
                else:
                    shutil.copyfile('/tmp/ap_file_bk.conf', ap_file)
                for i in range(len(p_conf) - 1, -1, -1):
                    if get.sitename == p_conf[i]["sitename"] and p_conf[i]["redirectname"]:
                        del(p_conf[i])
                return public.returnMsg(False, 'ERROR: 配置出错<br><a style="color:red;">' + isError.replace("\n",'<br>') + '</a>')

        else:
            redirectname_md5 = self.__calc_md5(get.redirectname)
            redirectfile = "%s/panel/vhost/%s/redirect/%s/%s_%s.conf"
            for w in ["apache","nginx"]:
                rf = redirectfile % (self.setupPath,w ,get.sitename, redirectname_md5, get.sitename)
                if os.path.exists(rf):
                    os.remove(rf)

    def del_redirect_multiple(self,get):
        '''
            @name 批量删除重定向
            @author zhwen<2020-11-21>
            @param site_id 1
            @param redirectnames test,baohu
        '''
        redirectnames = get.redirectnames.split(',')
        del_successfully = []
        del_failed = {}
        get.sitename = public.M('sites').where("id=?", (get.site_id,)).getField('name')
        for redirectname in redirectnames:
            get.redirectname = redirectname
            try:
                get.multiple = 1
                result = self.DeleteRedirect(get,multiple=1)
                if not result['status']:
                    del_failed[redirectname] = result['msg']
                    continue
                del_successfully.append(redirectname)
            except:
                del_failed[redirectname]='删除时出错了，请再试一次'
        public.serviceReload()
        return {'status': True, 'msg': '删除重定向 [ {} ] 成功'.format(','.join(del_successfully)), 'error': del_failed,
                'success': del_successfully}

    def DeleteRedirect(self,get,multiple=None):
        if not hasattr(get, 'redirectname'):
            return public.returnMsg(False, '缺少参数redirectname')
        if not hasattr(get, 'sitename'):
            return public.returnMsg(False, '缺少参数sitename')
        redirectconf = self.__read_config(self.__redirectfile)
        sitename = get.sitename
        redirectname = get.redirectname
        for i in range(len(redirectconf)):
            if redirectconf[i]["sitename"] == sitename and redirectconf[i]["redirectname"] == redirectname:
                proxyname_md5 = self.__calc_md5(redirectconf[i]["redirectname"])
                public.ExecShell("rm -f %s/panel/vhost/nginx/redirect/%s/%s_%s.conf" % (self.setupPath,redirectconf[i]["sitename"],proxyname_md5,redirectconf[i]["sitename"]))
                public.ExecShell("rm -f %s/panel/vhost/apache/redirect/%s/%s_%s.conf" % (self.setupPath,redirectconf[i]["sitename"],proxyname_md5, redirectconf[i]["sitename"]))
                del redirectconf[i]
                self.__write_config(self.__redirectfile,redirectconf)
                self.SetRedirectNginx(get)
                self.SetRedirectApache(get.sitename)
                if not multiple:
                    public.serviceReload()
                return public.returnMsg(True, '删除成功')

    def GetRedirectList(self,get):
        """
        @name 获取重定向列表
        @author hezhihong
        @param  get.sitename 站点名
        @param  get.errorpage 1:404页面重定向 0:非404页面重定向
        @return 重定向列表
        """
        redirectconf = self.__read_config(self.__redirectfile)
        sitename = get.sitename
        redirectlist = []
        for i in redirectconf:
            if i["sitename"] == sitename:
                if 'errorpage' in get and 'errorpage' in i and int(get.errorpage)!=int(i['errorpage']):continue
                if  'errorpage' in i and i['errorpage'] in [1,'1']:i['redirectdomain']=['404页面']
                redirectlist.append(i)
        return redirectlist

    def ClearOldRedirect(self,get):
        for i in ["apache","nginx"]:
            conf_path = "%s/panel/vhost/%s/%s.conf" % (self.setupPath,i,get.sitename)
            old_conf = public.readFile(conf_path)
            rep =""
            if i == "nginx":
                rep += "#301-START\n+[\s\w\:\/\.\;\$]+#301-END"
            if i == "apache":
                rep += "#301-START[\n\<\>\w\.\s\^\*\$\/\[\]\(\)\:\,\=]+#301-END"
            conf = re.sub(rep, "", old_conf)
            public.writeFile(conf_path, conf)
        public.serviceReload()
        return public.returnMsg(False, '旧版本重定向已经清理')

    # 取重定向配置文件
    def GetRedirectFile(self,get):
        import files
        conf = self.__read_config(self.__redirectfile)
        sitename = get.sitename
        redirectname = get.redirectname
        proxyname_md5 = self.__calc_md5(redirectname)
        if get.webserver == 'openlitespeed':
            get.webserver = 'apache'
        get.path = "%s/panel/vhost/%s/redirect/%s/%s_%s.conf" % (self.setupPath, get.webserver, sitename,proxyname_md5,sitename)
        for i in conf:
            if redirectname == i["redirectname"] and sitename == i["sitename"] and i["type"] != 1:
                return public.returnMsg(False, '重定向已暂停')
        f = files.files()
        return f.GetFileBody(get),get.path

    # 保存重定向配置文件
    def SaveRedirectFile(self,get):
        import files
        f = files.files()
        return f.SaveFileBody(get)
        #	return public.returnMsg(True, '保存成功')

    def __CheckRedirect(self,sitename,redirectname,is_error=False):
        conf_data = self.__read_config(self.__redirectfile)
        for i in conf_data:
            if i["sitename"] == sitename:
                if is_error and  "errorpage" in i and i["errorpage"] in [1,'1']:
                    return i
                if i["redirectname"] == redirectname:
                    return i


    # 读配置
    def __read_config(self, path):
        if not os.path.exists(path):
                public.writeFile(path, '[]')
        upBody = public.readFile(path)
        if not upBody: upBody = '[]'
        return json.loads(upBody)

    # 写配置
    def __write_config(self ,path, data):
        return public.writeFile(path, json.dumps(data))


