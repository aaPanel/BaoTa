#coding: utf-8
#-------------------------------------------------------------------
# 宝塔Linux面板
#-------------------------------------------------------------------
# Copyright (c) 2015-2018 宝塔软件(http:#bt.cn) All rights reserved.
#-------------------------------------------------------------------
# Author: hwliang <hwl@bt.cn>
#-------------------------------------------------------------------

#------------------------------
# URL重写类
#------------------------------
import os,public,json,re,sys,socket,shutil
os.chdir("/www/server/panel")
class panelRedirect:

    setupPath = '/www/server'
    __redirectfile = "/www/server/panel/data/redirect.conf"

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
    def __CheckRedirectUrl(self, get):
        sk = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sk.settimeout(0.5)
        rep = "(https?)://([\w\.]+):?([\d]+)?"
        h = re.search(rep, get.tourl).group(1)
        d = re.search(rep, get.tourl).group(2)
        try:
            p = re.search(rep, get.tourl).group(3)
        except:
            p = ""
        try:
            if p:
                sk.connect((d, int(p)))
            else:
                if h == "http":
                    sk.connect((d, 80))
                else:
                    sk.connect((d, 443))
        except:
            return public.returnMsg(False, "目标URL无法访问")
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
            if self.__CheckRedirect(get.sitename,get.redirectname):
                return public.returnMsg(False, '指定重定向名称已存在')
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
        #检测目标URL格式
        rep = "http(s)?\:\/\/([a-zA-Z0-9][-a-zA-Z0-9]{0,62}\.)+([a-zA-Z0-9][a-zA-Z0-9]{0,62})+.?"
        if not re.match(rep, get.tourl):
            return public.returnMsg(False, '目标URL格式不对 %s' + get.tourl)
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
                        rconf += domainstr % (sd,get.redirecttype,tourl,"$request_uri")
                else:
                    for sd in domains:
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
                        rconf += domainstr % ("%",sd,tourl,"$1",get.redirecttype)
                else:
                    for sd in domains:
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

    def ModifyRedirect(self,get):
        # 基本信息检查
        if self.__CheckRedirectStart(get):
            return self.__CheckRedirectStart(get)
        redirectconf = self.__read_config(self.__redirectfile)
        for i in range(len(redirectconf)):
            if redirectconf[i]["redirectname"] == get.redirectname and redirectconf[i]["sitename"] == get.sitename:
                redirectconf[i]["tourl"] = get.tourl
                redirectconf[i]["redirectdomain"] = json.loads(get.redirectdomain)
                redirectconf[i]["redirectpath"] = get.redirectpath
                redirectconf[i]["redirecttype"] = get.redirecttype
                redirectconf[i]["type"] = int(get.type)
                redirectconf[i]["domainorpath"] = get.domainorpath
                redirectconf[i]["holdpath"] = int(get.holdpath)
        self.__write_config(self.__redirectfile, redirectconf)
        self.SetRedirect(get)
        self.SetRedirectNginx(get)
        self.SetRedirectApache(get.sitename)
        public.serviceReload()
        print("修改成功")
        return public.returnMsg(True, '修改成功')

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
        redirectconf = self.__read_config(self.__redirectfile)
        sitename = get.sitename
        # conf_path = "%s/panel/vhost/nginx/%s.conf" % (self.setupPath, get.sitename)
        # old_conf = public.readFile(conf_path)
        # rep = "#301-START\n+[\s\w\:\/\.\;\$\(\)\'\^\~\{\}]+#301-END"
        # url_rep = "return\s(\d+)\s(https?\:\/\/[\w\.]+)"
        # host_rep = "\$host\s~\s'\^(.*)'"
        # if re.search(rep, old_conf):
        #     # 构造代理配置
        #     get.host = ""
        #     if re.search(host_rep, old_conf):
        #         get.host += str(re.search(host_rep, old_conf).group(1))
        #     get.redirecttype = str(re.search(url_rep, old_conf).group(1))
        #     get.tourl = str(re.search(url_rep, old_conf).group(2))

        #     get.redirectpath = ""
        #     if get.host:
        #         get.domainorpath = "domain"
        #         get.redirectdomain = "[\"%s\"]" % get.host
        #     else:
        #         get.domainorpath = "path"
        #         get.redirectpath = "/"
        #         get.redirectdomain = "[]"
        #     get.sitename = sitename
        #     get.redirectname = '旧重定向'
        #     get.type = 1
        #     get.holdpath = 1

        #     # 备份并替换老虚拟主机配置文件
        #     if not os.path.exists(conf_path + "_bak"):
        #         public.ExecShell("cp %s %s_bak" % (conf_path, conf_path))
        #     conf = re.sub(rep, "", old_conf)
        #     public.writeFile(conf_path, conf)
        #     self.CreateRedirect(get)
        #     # 取消老重定向
        #     import panelSite
        #     ps = panelSite.panelSite()
        #     get.type=0
        #     get.siteName = sitename
        #     get.srcDomain = ''
        #     get.toDomain = ''
        #     ps.Set301Status(get)
            # 写入代理配置
            #proxypath = "%s/panel/vhost/%s/proxy/%s/%s_%s.conf" % (
            #self.setupPath, w, get.sitename, proxyname_md5, get.sitename)
            # proxycontent = str(re.search(rep, old_conf).group(1))
            # public.writeFile(proxypath, proxycontent)

            #public.serviceReload()
        # redirectconf = self.__read_config(self.__redirectfile)
        redirectlist = []
        for i in redirectconf:
            if i["sitename"] == sitename:
                redirectlist.append(i)
        print(redirectlist)
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

    def __CheckRedirect(self,sitename,redirectname):
        conf_data = self.__read_config(self.__redirectfile)
        for i in conf_data:
            if i["sitename"] == sitename:
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


