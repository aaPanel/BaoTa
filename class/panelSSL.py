#coding: utf-8
#-------------------------------------------------------------------
# 宝塔Linux面板
#-------------------------------------------------------------------
# Copyright (c) 2015-2016 宝塔软件(http:#bt.cn) All rights reserved.
#-------------------------------------------------------------------
# Author: hwliang <hwl@bt.cn>
#-------------------------------------------------------------------
from hashlib import md5

#------------------------------
# SSL接口
#------------------------------
from panelAuth import panelAuth
import public,os,sys,binascii,urllib,json,time,datetime,re
from ssl_manage import SSLManger
try:
    from BTPanel import cache,session
except:
    pass

class panelSSL:
    __APIURL = public.GetConfigValue('home') + '/api/Auth'
    __APIURL2 = public.GetConfigValue('home') + '/api/Cert'
    __APIURL3 = public.GetConfigValue('home') + '/api/v2'
    __API = public.GetConfigValue('home') + '/api'
    __BINDURL = 'https://api.bt.cn/Auth/GetAuthToken'
    __CODEURL = 'https://api.bt.cn/Auth/GetBindCode'
    __UPATH = 'data/userInfo.json'
    __userInfo = None
    __PDATA = None
    _check_url = None
    __request_url = None
    __WECHAT_AUTH_URL = 'https://www.bt.cn/api/v2/wx_auth_panel/auth_url' # 微信授权接口
    __WECHAT_CHECK_USER_URL = 'https://www.bt.cn/api/v2/wx_auth_panel/auth_login' # 微信绑定接口
    #构造方法
    def __init__(self):
        pdata = {}
        data = {}
        if os.path.exists(self.__UPATH):
            my_tmp = public.readFile(self.__UPATH)
            if my_tmp:
                try:
                    self.__userInfo = json.loads(my_tmp)
                except:
                    self.__userInfo = {}
            else:
                self.__userInfo = {}
            try:
                if self.__userInfo:
                    pdata['access_key'] = self.__userInfo['access_key']
                    data['secret_key'] = self.__userInfo['secret_key']
            except:
                self.__userInfo = {}
                pdata['access_key'] = 'test'
                data['secret_key'] = '123456'
        else:
            pdata['access_key'] = 'test'
            data['secret_key'] = '123456'
        pdata['data'] = data
        self.__PDATA = pdata

    #获取Token
    def GetToken(self,get):
        rtmp = ""
        data = {}
        data['username'] = get.username
        data['password'] = public.md5(get.password)
        data['serverid'] = panelAuth().get_serverid()
        pdata = {}
        pdata['data'] = self.De_Code(data)
        try:

            result = self.request_post(self.__BINDURL,pdata)
            if not 'data' in result: return result

            result['data'] = self.En_Code(result['data'])
            if result['data']:
                result['data']['serverid'] = data['serverid']
                public.writeFile(self.__UPATH,json.dumps(result['data']))
                public.flush_plugin_list()
            del(result['data'])
            session['focre_cloud'] = True
            return result
        except Exception as ex:
            # bind = 'data/bind.pl'
            # if os.path.exists(bind): os.remove(bind)
            # return public.returnMsg(False,'连接服务器失败!<br>' + str(ex))
            raise public.error_conn_cloud(str(ex))

    #删除Token
    def DelToken(self,get):
        if os.path.exists(self.__UPATH):
            try:
                os.remove(self.__UPATH)
                public.flush_plugin_list()
            except Exception as e:
                return public.returnMsg(False,"删除失败：" + str(e))
        session['focre_cloud'] = True
        return public.returnMsg(True,"SSL_BTUSER_UN")

    #获取用户信息
    def GetUserInfo(self,get):
        result = {}
        if self.__userInfo:
            userTmp = {}
            userTmp['username'] = self.__userInfo['username'][0:3]+'****'+self.__userInfo['username'][-4:]
            result['status'] = True
            result['msg'] = public.getMsg('SSL_GET_SUCCESS')
            result['data'] = userTmp
        else:
            userTmp = {}
            userTmp['username'] = public.getMsg('SSL_NOT_BTUSER')
            result['status'] = False
            result['msg'] = public.getMsg('SSL_NOT_BTUSER')
            result['data'] = userTmp
        return result

    #获取产品列表
    def get_product_list(self,get):
        p_type = 'dv'
        if 'p_type' in get: p_type = get.p_type
        result = self.request('get_product_list?p_type={}'.format(p_type))
        return result

    def get_product_list_v2(self,get):
        p_type = 'dv'
        if 'p_type' in get: p_type = get.p_type


        result = self.request('get_product_list_v3?p_type={}'.format(p_type))
        return result

    def get_cert_oid(self,get):
        """
        @name 获取已部署证书订单oid
        """
        oid = 0
        if 'siteName' in get:
            sfile = '{}/vhost/cert/{}/certOrderId'.format(public.get_panel_path(),get.siteName)
            if os.path.exists(sfile):
                try:
                    oid = int(public.readFile(sfile).strip())
                except:pass
        return oid

    def get_cert_sort(self,get,result):
        """
        @name 重新排序商用证书订单
        @return 1、已部署证书，2、待提交证书 ，3、待完善资料，4、即将到期，5、已过期
        """
        if type(result) == list:
            oid = self.get_cert_oid(get)
            for val in result:
                val['endDay'] = 0
                val['ssl_state'] = 0
                val['sort'] = 0

                #有CA订单号
                if val['certId']:
                    if val['endDate']:
                        #已完成的订单
                        day = int((val['endDate'] - time.time()) / 86400)
                        if val['endDate'] < time.time() or day < 30:
                            if day > 0:
                                val['sort'] = 395 - day
                            else:
                                val['sort'] = day - 365
                        else:
                            val['sort'] = day
                        val['endDay'] = day
                    else:
                        #带验证订单
                        if val['domainName']:
                            val['sort'] = -2
                else:
                    if not val['domainName']:
                        #待完善资料
                        val['sort'] = -3
                    else:
                        #待提交证书
                        val['sort'] = -1

                if val['oid'] == oid:
                    val['sort'] = 2000
                    val['ssl_state'] = 1
            if len(result):
                result.sort(key = lambda item: (item['sort']),reverse=True)
        return result

    # TODO 修改接口后重构
    #获取商业证书订单列表
    def get_order_list(self,get):
        result = self.request('get_bt_ssl_list')
        return self.get_cert_sort(get,result)

    def soft_release(self, get):
        self.__PDATA['data']['oid'] = get.oid
        result = self.request('soft_release')
        return result

    def batch_soft_release(self, get):
        oids = get.oid.split(',')
        finish_list = []
        for oid in oids:
            finish = {'oid': oid}
            self.__PDATA['data']['oid'] = oid
            try:
                finish.update(self.request('soft_release'))
            except:
                finish.update({'status':False,'msg':'请求失败'})
            finish_list.append(finish)
        return {'status': True, 'msg': "删除成功", 'finish_list': finish_list}

    #获指定商业证书订单
    def get_order_find(self,get):
        self.__PDATA['data']= {}
        self.__PDATA['data']['oid'] = get.oid
        result = self.request('get_order_find')
        return result

    #下载证书
    def download_cert(self,get):
        self.__PDATA['data']['oid'] = get.oid
        result = self.request('download_cert')
        if not result.get('data'):
            self.__PDATA['data'] = json.loads(self.__PDATA['data'])
            result = self.request_v2("cert_ssl/compat_download")
            return result['res']
        return result

    #部署指定商业证书
    def set_cert(self,get):
        if not hasattr(get,'siteName'):
                return public.returnMsg(False,'缺少参数siteName')
        siteName = get.siteName
        reload = get.get("reload",0)
        certInfo = self.get_order_find(get)

        if ("years" in certInfo and certInfo["years"] > 1) and ("cert_ssl_type" in certInfo and certInfo["cert_ssl_type"] == 1):
            get.status = 1
            self.set_auto_renew_cert(get)  # 宝塔证书且签发时设置自动续签任务
        path = '/www/server/panel/vhost/cert/' + siteName
        if not os.path.exists(path):
            public.ExecShell('mkdir -p ' + path)
        csrpath = path+"/fullchain.pem"
        keypath = path+"/privkey.pem"
        pidpath = path+"/certOrderId"

        other_file = path + '/partnerOrderId'
        if os.path.exists(other_file): os.remove(other_file)
        other_file = path + '/README'
        if os.path.exists(other_file): os.remove(other_file)

        public.writeFile(keypath,certInfo['privateKey'])
        public.writeFile(csrpath,certInfo['certificate']+"\n"+certInfo['caCertificate'])
        public.writeFile(pidpath,get.oid)
        import panelSite
        panelSite.panelSite().SetSSLConf(get)
        if reload == 0:
            public.serviceReload()
        get.csr = certInfo['certificate']+"\n"+certInfo['caCertificate']
        self.set_exclude_hash(get)
        return public.returnMsg(True,'SET_SUCCESS')

    #生成商业证书支付订单
    def apply_order_pay(self,args):
        self.__PDATA['data'] = json.loads(args.pdata)
        result = self.check_ssl_caa(self.__PDATA['data']['domains'])
        if result: return result
        result = self.request('apply_cert_order')
        return result

    def check_ssl_caa(self,domains,clist = ['sectigo.com','digicert.com','comodoca.com']):
        '''
            @name 检查CAA记录是否正确
            @param domains 域名列表
            @param clist 正确的记录值关键词
            @return bool
        '''
        try:
            data = {}
            for domain in domains:
                root,zone = public.get_root_domain(domain)
                for d in [domain,root,'_acme-challenge.{}'.format(root),'_acme-challenge.{}'.format(domain)]:
                    ret = public.query_dns(d,'CAA')
                    if not ret: continue

                    slist = []
                    for val in ret:
                        if val['value'] in clist:
                            return False

                        slist.append(val)

                    if len(slist) > 0:
                        data[d] = slist
            if data:
                result = {}
                result['status'] = False
                result['msg'] = 'error:域名的DNS解析中存在CAA记录，请删除后重新申请'
                result['data'] = json.dumps(data)
                result['caa_list'] = data
                return result
        except : pass
        return False

    # TODO 修改接口后重构
    #检查商业证书支付状态
    def get_pay_status(self,args):
        self.__PDATA['data']['oid'] = args.oid
        self.__PDATA['data']['pid'] = args.pid
        result = self.request('get_pay_status')
        return result

    #提交商业证书订单到CA
    def apply_order(self,args):
        self.__PDATA['data']['oid'] = args.oid
        result = self.request('apply_cert')
        if result['status'] == True:
            self.__PDATA['data'] = {}
            result['verify_info'] = self.get_verify_info(args)
        return result

    #获取商业证书验证信息
    def get_verify_info(self,args):
        self.__PDATA['data']['oid'] = args.oid
        verify_info = self.request('get_verify_info')
        is_file_verify = 'fileName' in verify_info
        verify_info['paths'] = []
        verify_info['hosts'] = []
        for domain in verify_info['domains']:
            if is_file_verify:
                siteRunPath = self.get_domain_run_path(domain)
                if not siteRunPath:
                    # if domain[:4] == 'www.': domain = domain[:4]
                    verify_info['paths'].append(verify_info['path'].replace('example.com',domain))
                    continue
                verify_path = siteRunPath + '/.well-known/pki-validation'
                if not os.path.exists(verify_path):
                    os.makedirs(verify_path)
                verify_file = verify_path + '/' + verify_info['fileName']
                if os.path.exists(verify_file): continue
                public.writeFile(verify_file,verify_info['content'])
            else:
                original_domain = domain
                # if domain[:4] == 'www.': domain = domain[:4]
                verify_info['hosts'].append(verify_info['host'] + '.' + domain)
                if 'auth_to' in args:
                    root, zone = public.get_root_domain(domain)
                    res = self.create_dns_record(args['auth_to'], verify_info['host'] + '.' + root,
                                                 verify_info['value'], original_domain)
                    print(res)
        return verify_info

    #处理验证信息
    def set_verify_info(self,args):
        verify_info = self.get_verify_info(args)
        is_file_verify = 'fileName' in verify_info
        verify_info['paths'] = []
        verify_info['hosts'] = []
        for domain in verify_info['domains']:
            if domain[:2] == '*.': domain = domain[2:]
            if is_file_verify:
                siteRunPath = self.get_domain_run_path(domain)
                if not siteRunPath:
                    #if domain[:4] == 'www.': domain = domain[4:]
                    verify_info['paths'].append(verify_info['path'].replace('example.com',domain))
                    continue
                verify_path = siteRunPath + '/.well-known/pki-validation'
                if not os.path.exists(verify_path):
                    os.makedirs(verify_path)
                verify_file = verify_path + '/' + verify_info['fileName']
                if os.path.exists(verify_file): continue
                public.writeFile(verify_file,verify_info['content'])
            else:
                original_domain = domain
                #if domain[:4] == 'www.': domain = domain[4:]
                verify_info['hosts'].append(verify_info['host'] + '.' + domain)

                if 'auth_to' in args:
                    root,zone = public.get_root_domain(domain)
                    self.create_dns_record(args['auth_to'],verify_info['host'] + '.' + root,
                                           verify_info['value'], original_domain)
        return verify_info


    #获取指定域名的PATH
    def get_domain_run_path(self,domain):
        pid = public.M('domain').where('name=?',(domain,)).getField('pid')
        if not pid: return False
        return self.get_site_run_path(pid)


    def get_site_run_path(self,pid):
        '''
            @name 获取网站运行目录
            @author hwliang<2020-08-05>
            @param pid(int) 网站标识
            @return string
        '''
        siteInfo = public.M('sites').where('id=?',(pid,)).find()
        siteName = siteInfo['name']
        sitePath = siteInfo['path']
        webserver_type = public.get_webserver()
        setupPath = '/www/server'
        path = None
        if webserver_type == 'nginx':
            filename = setupPath + '/panel/vhost/nginx/' + siteName + '.conf'
            if os.path.exists(filename):
                conf = public.readFile(filename)
                rep = r'\s*root\s+(.+);'
                tmp1 = re.search(rep,conf)
                if tmp1: path = tmp1.groups()[0]

        elif webserver_type == 'apache':
            filename = setupPath + '/panel/vhost/apache/' + siteName + '.conf'
            if os.path.exists(filename):
                conf = public.readFile(filename)
                rep = r'\s*DocumentRoot\s*"(.+)"\s*\n'
                tmp1 = re.search(rep,conf)
                if tmp1: path = tmp1.groups()[0]
        else:
            filename = setupPath + '/panel/vhost/openlitespeed/' + siteName + '.conf'
            if os.path.exists(filename):
                conf = public.readFile(filename)
                rep = r"vhRoot\s*(.*)"
                path = re.search(rep,conf)
                if not path:
                    path = None
                else:
                    path = path.groups()[0]

        if not path:
            path = sitePath
        return path

    #验证URL是否匹配
    def check_url_txt(self,args,timeout=5):
        url = args.url
        content = args.content

        import http_requests
        res = http_requests.get(url,s_type='curl',timeout=timeout)
        result = res.text
        if not result: return 0

        if result.find('11001') != -1 or result.find('curl: (6)') != -1: return -1
        if result.find('curl: (7)') != -1 or res.status_code in [403,401]: return -5
        if result.find('Not Found') != -1 or result.find('not found') != -1 or res.status_code in [404]:return -2
        if result.find('timed out') != -1:return -3
        if result.find('301') != -1 or result.find('302') != -1 or result.find('Redirecting...') != -1 or res.status_code in [301,302]:return -4
        if result == content:return 1
        return 0

    #更换验证方式
    def again_verify(self,args):
        if "cert_ssl_type" not in args or args.cert_ssl_type == '0':
            self.__PDATA['data']['oid'] = args.oid
            self.__PDATA['data']['dcvMethod'] = args.dcvMethod
            result = self.request('again_verify')
            return result
        else:
            self.__PDATA['data']['oid'] = args.oid
            self.__PDATA['data']['pid'] = args.pid
            if args.dcvMethod in ['HTTP_CSR_HASH','HTTPS_CSR_HASH']:
                verification = 'file'
            else:
                verification = 'dns'
            self.__PDATA['data']['verification'] = verification
            result = self.request_v2('cert_ssl/update_ca_verification')
            if not result['success']: return public.returnMsg(False,result['res'])
            return public.returnMsg(True, result)

    # TODO 修改接口后重构
    #获取商业证书验证结果
    def get_verify_result(self,args):
        self.__PDATA['data']={}
        self.__PDATA['data']['oid'] = args.oid
        self.__PDATA['data']['pid'] = args.pid
        if "cert_ssl_type" not in args or args.cert_ssl_type == '0':
            verify_info = self.request('get_verify_result')
            if verify_info['status'] in ['COMPLETE',False]: return verify_info
            is_file_verify = 'CNAME_CSR_HASH' != verify_info['data']['dcvList'][0]['dcvMethod']
            verify_info['paths'] = []
            verify_info['hosts'] = []
            if not 'application' in verify_info['data'] :
                return public.returnMsg(False,'订单出现问题，请联系人工客服.')
            if verify_info['data']['application']['status'] == 'ongoing':
                return public.returnMsg(False,'订单出现问题，CA正在人工验证，若24小时内依然出现此提示，请联系宝塔')
            for dinfo in verify_info['data']['dcvList']:
                is_https = dinfo['dcvMethod'] == 'HTTPS_CSR_HASH'
                if is_https:
                    is_https = 's'
                else:
                    is_https = ''
                domain = dinfo['domainName']
                if domain[:2] == '*.': domain = domain[2:]
                dinfo['domainName'] = domain
                if is_file_verify:
                    #判断是否是Springboot 项目
                    if public.M('sites').where('id=?',(public.M('domain').where('name=?',(dinfo['domainName'])).getField('pid'),)).getField('project_type') == 'Java' or public.M('sites').where('id=?',(public.M('domain').where('name=?',(dinfo['domainName'])).getField('pid'),)).getField('project_type') == 'Go' or public.M('sites').where('id=?',(public.M('domain').where('name=?',(dinfo['domainName'])).getField('pid'),)).getField('project_type') == 'Other':
                        siteRunPath='/www/wwwroot/java_node_ssl'
                    else:
                        siteRunPath = self.get_domain_run_path(domain)
                    #if domain[:4] == 'www.': domain = domain[4:]
                    status = 0
                    url = 'http'+ is_https +'://'+ domain +'/.well-known/pki-validation/' + verify_info['data']['DCVfileName']
                    get = public.dict_obj()
                    get.url = url
                    get.content = verify_info['data']['DCVfileContent']
                    status = self.check_url_txt(get)
                    verify_info['paths'].append({'url':url,'status':status})
                    if not siteRunPath: continue
                    verify_path = siteRunPath + '/.well-known/pki-validation'
                    if not os.path.exists(verify_path):
                        os.makedirs(verify_path)
                    verify_file = verify_path + '/' + verify_info['data']['DCVfileName']
                    if os.path.exists(verify_file): continue
                    public.writeFile(verify_file,verify_info['data']['DCVfileContent'])
                else:
                    #if domain[:4] == 'www.': domain = domain[4:]
                    domain,subb = public.get_root_domain(domain)
                    dinfo['domainName'] = domain
                    verify_info['hosts'].append(verify_info['data']['DCVdnsHost'] + '.' + domain)
        else:
            verify_info = self.request_v2('cert_ssl/ssl_check')
            if not verify_info['success'] or not verify_info['res'].get('list'): return public.returnMsg(False,verify_info['res'])
            status = "PENDING"
            if verify_info['res']['list'][0]['state'] == 2:
                status = "COMPLETE"

            verify_info['data'] = {}
            verify_info['paths'] = []
            if verify_info['res']['list'][0]['verification'] == 'file':
                verify_info['data']['dcvList'] = []
                for domain in verify_info['res']['list']:
                    verify_info['data']['dcvList'].append({"dcvEmail": "", "dcvMethod": "HTTP_CSR_HASH","domainName": domain['domain']})
                    url = 'http://'+ domain['domain'] + domain['file_name']
                    get = public.dict_obj()
                    get.url = url
                    get.content = domain['value']
                    verify_info['paths'].append({"url": url,"status": self.check_url_txt(get)})

                    # 判断是否是Springboot 项目
                    if public.M('sites').where('id=?',
                                               (public.M('domain').where('name=?', (domain['domain'])).getField(
                                                       'pid'),)).getField('project_type') == 'Java' or public.M(
                        'sites').where('id=?', (public.M(
                        'domain').where('name=?', (domain['domain'])).getField('pid'),)).getField(
                        'project_type') == 'Go' or public.M('sites').where('id=?', (public.M('domain').where('name=?', (
                            domain['domain'])).getField('pid'),)).getField('project_type') == 'Other':
                        siteRunPath = '/www/wwwroot/java_node_ssl'
                    else:
                        siteRunPath = self.get_domain_run_path(domain['domain'])
                    if not siteRunPath: continue
                    if siteRunPath.endswith("/"):
                        siteRunPath = siteRunPath[:-1]
                    verify_file = siteRunPath + domain['file_name']
                    verify_path = os.path.dirname(verify_file)
                    if not os.path.exists(verify_path):
                        os.makedirs(verify_path)
                    if os.path.exists(verify_file): continue
                    public.writeFile(verify_file, domain['value'])

                verify_info['data']['DCVfileName'] = os.path.basename(verify_info['res']['list'][0]['file_name'])
                verify_info['data']['DCVfileContent'] = os.path.basename(verify_info['res']['list'][0]['value'])
                verify_info['data']['DCVfilePath'] = "http://example.com"+verify_info['res']['list'][0]['file_name']
                # url = 'http://'+ verify_info['res']['list'][0]['domain'] + verify_info['res']['list'][0]['file_name']
                # get = public.dict_obj()
                # get.url = url
                # get.content = verify_info['data']['DCVfileContent']
                verify_info['certStatus'] = verify_info['status'] = status
                # verify_info['paths'] = [{"url": url,"status": self.check_url_txt(get)}]
            else:
                verify_info['data']['dcvList'] = []
                for domain in verify_info['res']['list']:
                    verify_info['data']['dcvList'].append({"dcvEmail": "", "dcvMethod": "CNAME_CSR_HASH","domainName": domain['domain']})
                verify_info['data']['DCVdnsHost'] = os.path.basename(verify_info['res']['list'][0]['file_name'].split('.')[0])
                verify_info['data']['DCVdnsType'] = "CNAME"
                verify_info['data']['DCVdnsValue'] = os.path.basename(verify_info['res']['list'][0]['value'])
                verify_info['certStatus'] = verify_info['status'] = status

        return verify_info

    def get_order_details(self,args):
        """
        @name 获取商业证书订单详情
        @param args: oid 订单ID
        @return: 订单详情
        """
        self.__PDATA['data'] = {}
        self.__PDATA['data']['oid'] = args.oid
        self.__PDATA['data']['pid'] = args.pid
        result = self.request_v2('cert_ssl/get_cert_info')

        if not result['success']:
            return public.returnMsg(False,result['res'])

        if "check" in result["res"] and isinstance(result["res"]["check"],list):
            result["res"]["verifyInfo"] = {
                "DCVdnsHost":result["res"]["check"][0]["file_name"].split('.')[0],
                "DCVdnsType":result["res"]["check"][0]["verification"],
                "DCVdnsValue":result["res"]["check"][0]["value"]
            }

        result["res"]["renewal_text"] = ""
        result["res"]["purchase_date"] = ""
        result["res"]["cycle_text"] = ""
        result["res"]["remaining_text"] = ""

        try:
            # 当前时间（UTC+8）
            current_time = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8)))

            # 将 beginDate 和 endDate 从时间戳转换为 datetime (UTC)
            begin_date = datetime.datetime.fromtimestamp(result["res"]['addtime'], tz=datetime.timezone.utc)
            end_date = datetime.datetime.fromtimestamp(result["res"]['endDate'], tz=datetime.timezone.utc)

            # 转换为 UTC+8
            begin_date = begin_date.astimezone(datetime.timezone(datetime.timedelta(hours=8)))
            end_date = end_date.astimezone(datetime.timezone(datetime.timedelta(hours=8)))

            # 1. 格式化购买时间为 "xx年xx月xx日"
            purchase_date = begin_date.strftime("%Y年%m月%d日")

            # 2. 计算当前签发周期（第几年）
            cycle_years = result["res"]['years']
            time_diff = current_time - begin_date
            days_diff = time_diff.total_seconds() / (60 * 60 * 24)
            current_cycle = min(int(days_diff // 365) + 1, cycle_years)
            cycle_text = "第{}年".format(current_cycle)

            # 3. 计算当前周期剩余时间（天数）
            remaining_days = (end_date - current_time).days
            remaining_text = "{}天".format(remaining_days)

            # 4. 计算下一次自动续签时间（endDate 前 30 天）
            crontabs = public.M('crontab').where("name like '%自动续签多年宝塔证书%'", ()).get()

            if len(crontabs) > 0:
                crontabs = crontabs[0]
                task_runtime = '{}时{}分'.format(crontabs['where_hour'],crontabs['where_minute'])
                renewal_date = end_date - datetime.timedelta(days=30)
                days_to_renewal = (renewal_date - current_time).days
                renewal_text = "{}天后{}".format(days_to_renewal,task_runtime)
                result["res"]["renewal_text"] = renewal_text
            result["res"]["purchase_date"] = purchase_date
            result["res"]["cycle_text"] = cycle_text
            result["res"]["remaining_text"] = remaining_text
        except Exception as e:
            pass
        return result

    def set_auto_renew_cert(self,args):
        from crontab import crontab
        status = args.status
        public.print_log("set_auto_renew_cert===================")
        if str(status) == "1":
            crontab_malicious = public.M('crontab').where("name like '%自动续签多年宝塔证书%'", ()).get()
            if len(crontab_malicious) > 0:
                return public.returnMsg(True, '任务已存在!')

            public.WriteLog('自动续签多年宝塔证书', '功能开启')

            public.set_module_logs('panelSSL', 'open_auto_renew_cert', 1)

            # 每个用户随机 凌晨0-4小时 之间运行 错开分流
            import random
            run_hour = random.randint(0, 4)
            run_minute = random.randint(0, 59)

            args.name = "[勿删]宝塔自动续签多年宝塔证书任务"
            args.type = "day"
            args.hour = run_hour
            args.minute = run_minute
            args.where1 = "1"
            args.week = "1"
            args.timeType = "sday"
            args.timeSet = "1"
            args.second = ""
            args.sType = "toShell"
            args.sBody = "{panelpath}/pyenv/bin/python3 -u {panelpath}/script/renew_certificate.py".format(panelpath=public.get_panel_path())
            args.sName = ""
            args.backupTo = ""
            args.save = ""
            args.urladdress = ""
            args.save_local = "0"
            args.notice = "0"
            args.notice_channel = ""
            args.datab_name = ""
            args.tables_name = ""
            args.keyword = ""
            args.flock = "1"
            args.stop_site = "0"
            args.version = ""
            args.user = ""
            return crontab().AddCrontab(args)
        else:
            res = public.M('crontab').where("name like '%自动续签多年宝塔证书%'", ()).get()
            if len(res) > 0:
                for crontask in res:
                    args.id = crontask["id"]
                    crontab().DelCrontab(args)
            return public.returnMsg(True, '自动续签任务已关闭!')

    #取消订单
    def cancel_cert_order(self,args):
        self.__PDATA['data']['oid'] = args.oid
        result = self.request('cancel_cert_order')
        return result


    #生成商业证书支付订单
    def apply_cert_order_pay(self,args):
        pdata = json.loads(args.pdata)
        self.__PDATA['data'] = pdata
        result = self.request('apply_cert_order_pay')
        return result

    #获取证书管理员信息
    def get_cert_admin(self,get):
        result = self.request('get_cert_admin')
        return result

    def ApplyDVSSL(self,get):

        """
        申请证书
        """
        public.set_module_logs('TrustAsiaCA', 'ApplyDVSSL', 1)

        if not 'orgName' in get: return public.returnMsg(False,'确实必要参数 orgName')
        if not 'orgPhone' in get: return public.returnMsg(False,'确实必要参数 orgPhone')
        if not 'orgPostalCode' in get: return public.returnMsg(False,'确实必要参数 orgPostalCode')
        if not 'orgRegion' in get: return public.returnMsg(False,'确实必要参数 orgRegion')
        if not 'orgCity' in get: return public.returnMsg(False,'确实必要参数 orgCity')
        if not 'orgAddress' in get: return public.returnMsg(False,'确实必要参数 orgAddress')
        if not 'orgDivision' in get: return public.returnMsg(False,'确实必要参数 orgDivision')

        get.id = public.M('domain').where('name=?',(get.domain,)).getField('pid');
        get.path = public.M('sites').where('id=?', (get.id,)).getField('path');

        if not hasattr(get,'siteName'):
            get.siteName = public.M('sites').where('id=?',(get.id,)).getField('name');

        #当申请二级域名为www时，检测主域名是否绑定到同一网站
        if get.domain[:4] == 'www.':
            if not public.M('domain').where('name=? AND pid=?',(get.domain[4:],get.id)).count():
                return public.returnMsg(False,"申请[%s]证书需要验证[%s]请将[%s]绑定并解析到站点!" % (get.domain,get.domain[4:],get.domain[4:]))
        #判断是否是Java项目
        if public.M('sites').where('id=?',(get.id,)).getField('project_type') == 'Java' or public.M('sites').where('id=?',(get.id,)).getField('project_type') == 'Go' or public.M('sites').where('id=?',(get.id,)).getField('project_type') == 'Other':
            get.path='/www/wwwroot/java_node_ssl/'
            runPath=''
        #判断是否是Node项目
        elif public.M('sites').where('id=?',(get.id,)).getField('project_type') == 'Node':
            get.path=public.M('sites').where('id=?',(get.id,)).getField('path')
            runPath=''
        #判断是否是python项目
        elif public.M('sites').where(
                'id=?', (get.id, )).getField('project_type') == 'Python':
            get.path = public.M('sites').where('id=?',
                                               (get.id, )).getField('path')
            runPath = ''
        else:
            runPath = self.GetRunPath(get)
        if runPath != False and runPath != '/': get.path +=  runPath
        authfile = get.path + '/.well-known/pki-validation/fileauth.txt'
        if not self.CheckDomain(get):
            if not os.path.exists(authfile):
                return public.returnMsg(False,'无法写入验证文件: {}'.format(authfile))
            else:
                msg = '''无法正确访问验证文件<br><a class="btlink" href="{c_url}" target="_blank">{c_url}</a> <br><br>
                <p></b>可能的原因：</b></p>
                1、未正确解析，或解析未生效 [请正确解析域名，或等待解析生效后重试]<br>
                2、检查是否有设置301/302重定向 [请暂时关闭重定向相关配置]<br>
                3、检查该网站是否已部署HTTPS并设置强制HTTPS [请暂时关闭强制HTTPS功能]<br>'''.format(c_url = self._check_url)
                return public.returnMsg(False,msg)

        action = 'ApplyDVSSL'
        if hasattr(get,'partnerOrderId'):
            self.__PDATA['data']['partnerOrderId'] = get.partnerOrderId
            action = 'ReDVSSL'

        self.__PDATA['data']['domain'] = get.domain
        self.__PDATA['data']['orgPhone'] = get.orgPhone
        self.__PDATA['data']['orgPostalCode'] = get.orgPostalCode
        self.__PDATA['data']['orgRegion'] = get.orgRegion
        self.__PDATA['data']['orgCity'] = get.orgCity
        self.__PDATA['data']['orgAddress'] = get.orgAddress
        self.__PDATA['data']['orgDivision'] = get.orgDivision
        self.__PDATA['data']['orgName'] = get.orgName
        self.__PDATA['data'] = self.De_Code(self.__PDATA['data'])
        try:
            result = self.request_post(self.__APIURL + '/' + action,self.__PDATA)
            if not 'data' in result: return result
        except Exception as ex:
            raise public.error_conn_cloud(str(ex))

        if 'status' in result:
            if not result['status']: return result
        result['data'] = self.En_Code(result['data'])
        try:
            if not 'authPath' in result['data']: result['data']['authPath'] = '/.well-known/pki-validation/'
            authfile = get.path + result['data']['authPath'] + result['data']['authKey']
        except:
            if 'authKey' in result['data']:
                authfile = get.path + '/.well-known/pki-validation/' + result['data']['authKey']
            else:
                return public.returnMsg(False,'获取验证文件失败!')

        if 'authValue' in result['data']:
            public.writeFile(authfile,result['data']['authValue'])
        return result


    def apply_order_byca(self,get):
        """
        @name 测试证书，提交订单
        """

        get.id = public.M('domain').where('name=?',(get.domain,)).getField('pid')
        if hasattr(get,'siteName'):
            get.path = public.M('sites').where('id=?',(get.id,)).getField('path')
        else:
            get.siteName = public.M('sites').where('id=?',(get.id,)).getField('name')

        #当申请二级域名为www时，检测主域名是否绑定到同一网站
        if get.domain[:4] == 'www.':
            if not public.M('domain').where('name=? AND pid=?',(get.domain[4:],get.id)).count():
                return public.returnMsg(False,"申请[%s]证书需要验证[%s]请将[%s]绑定并解析到站点!" % (get.domain,get.domain[4:],get.domain[4:]))
        #判断是否是Java项目
        if public.M('sites').where('id=?',(get.id,)).getField('project_type') == 'Java' or public.M('sites').where('id=?',(get.id,)).getField('project_type') == 'Go' or public.M('sites').where('id=?',(get.id,)).getField('project_type') == 'Other':
            get.path='/www/wwwroot/java_node_ssl/'
            runPath=''
        #判断是否是Node项目
        elif public.M('sites').where('id=?',(get.id,)).getField('project_type') == 'Node':
            get.path=public.M('sites').where('id=?',(get.id,)).getField('path')
            runPath=''
        #判断是否是python项目
        elif public.M('sites').where(
                'id=?', (get.id, )).getField('project_type') == 'Python':
            get.path = public.M('sites').where('id=?',
                                               (get.id, )).getField('path')
            runPath = ''
        else:
            runPath = self.GetRunPath(get)
        if runPath != False and runPath != '/': get.path +=  runPath
        authfile = get.path + '/.well-known/pki-validation/fileauth.txt'
        if not self.CheckDomain(get):
            if not os.path.exists(authfile):
                return public.returnMsg(False,'无法写入验证文件: {}'.format(authfile))
            else:
                msg = '''无法正确访问验证文件<br><a class="btlink" href="{c_url}" target="_blank">{c_url}</a> <br><br>
                <p></b>可能的原因：</b></p>
                1、未正确解析，或解析未生效 [请正确解析域名，或等待解析生效后重试]<br>
                2、检查是否有设置301/302重定向 [请暂时关闭重定向相关配置]<br>
                3、检查该网站是否已部署HTTPS并设置强制HTTPS [请暂时关闭强制HTTPS功能]<br>'''.format(c_url = self._check_url)
                return public.returnMsg(False,msg)

        action = 'apply_order_byca'

        self.__PDATA['data']['ssl_id'] = get.ssl_id
        self.__PDATA['data']['domain'] = get.domain

        self.__PDATA['data'] = self.De_Code(self.__PDATA['data'])

        result = public.httpPost(self.__APIURL + '/' + action,self.__PDATA)
        try:
            result = json.loads(result)
        except: return result
        result['data'] = self.En_Code(result['data'])

        try:
            if 'authValue' in result['data'].keys():
                public.writeFile(authfile,result['data']['authValue'])
        except:
            try:
                public.writeFile(authfile,result['data']['authValue'])
            except:
                return result

        return result

    # TODO 修改接口后重构
    #完善资料CA(先支付接口)
    def apply_order_ca(self,args):
        pdata = json.loads(args.pdata)
        if len(pdata['Administrator']['lastName'])<2:
            return public.returnMsg(False,'请正确填写姓名')
        result = self.check_ssl_caa(pdata['domains'])
        if result:  return result

        if "cert_ssl_type" not in pdata or pdata['cert_ssl_type'] == 0:
            self.__PDATA['data'] = pdata
            result = self.request('apply_cert_ca')
            if result['status'] == True:
                self.__PDATA['data'] = {}
                args['oid'] = pdata['oid']
                if 'auth_to' in pdata:
                    args['auth_to'] = pdata['auth_to']
                result['verify_info'] = self.get_verify_info(args)
            return result
        else:
            data = {}
            data["pid"] = str(pdata["pid"])
            data["oid"] = str(pdata["oid"])
            data["administrator"] = {
                "name": pdata["Administrator"]["lastName"],
                "email": pdata["Administrator"]["email"],
                "zip_code": pdata["Administrator"]["postCode"],
                "country": pdata["Administrator"]["country"],
                "city": pdata["Administrator"]["city"],
                "telephone": pdata["Administrator"]["mobile"],
                "state": pdata["Administrator"]["state"],
            }
            data["verification"] = "file" if pdata["dcvMethod"] == "HTTP_CSR_HASH" else "dns"
            data["verification_type"] = "1"
            data["domains"] = pdata["domains"]
            self.__PDATA['data'] = data

            result = self.request_v2('cert_ssl/submit_ssl_order')
            if not result['success']:
                return public.returnMsg(False,result['res'])
            # 设置验证信息
            try:
                self.__PDATA['data'] = {}
                self.__PDATA['data']['oid'] = pdata["oid"]
                self.__PDATA['data']['pid'] = pdata["pid"]
                verify_info = self.request_v2('cert_ssl/ssl_check')
                for item in verify_info['res']['list']:
                    public.print_log(item)
                    domain = item['domain']
                    if item["verification"] == "file":
                        siteRunPath = self.get_domain_run_path(domain)
                        if not siteRunPath:
                            # if domain[:4] == 'www.': domain = domain[:4]
                            verify_info['paths'].append(verify_info['path'].replace('example.com', domain))
                            continue
                        verify_path = siteRunPath + '/.well-known/pki-validation'
                        if not os.path.exists(verify_path):
                            os.makedirs(verify_path)
                        verify_file = verify_path + '/' + verify_info['file_name']
                        if os.path.exists(verify_file): continue
                        public.writeFile(verify_file, verify_info['value'])
                    else:
                        original_domain = domain

                        if 'auth_to' in pdata:
                            root, zone = public.get_root_domain(domain)
                            res = self.create_dns_record(pdata['auth_to'], item['file_name'] + '.' + root,
                                                         item['value'], original_domain)
                            public.print_log(res)
            except:
                public.print_log(public.get_error_info())

            return public.returnMsg(True,'提交成功')



    #获取订单列表
    def GetOrderList(self,get):

        partnerOrderId = None
        if hasattr(get,'siteName'):
            path =   '/etc/letsencrypt/live/'+ get.siteName + '/partnerOrderId'
            if os.path.exists(path):
                partnerOrderId = public.readFile(path)
            else:
                path = '/www/server/panel/vhost/cert/' + get.siteName + '/partnerOrderId'
                if os.path.exists(path):
                    partnerOrderId = public.readFile(path)

        self.__PDATA['data'] = self.De_Code(self.__PDATA['data'])
        try:
            result = self.request_post(self.__APIURL + '/GetSSLList',self.__PDATA)
            if not 'data' in result: return result
        except Exception as ex:
            raise public.error_conn_cloud(str(ex))

        result['data'] = self.En_Code(result['data'])
        for i in range(len(result['data'])):
            result['data'][i]['endtime'] =   self.add_months(result['data'][i]['createTime'],result['data'][i]['validityPeriod'])
        result['partnerOrderId'] = partnerOrderId
        return result

    #计算日期增加(月)
    def add_months(self,dt,months):
        import calendar
        dt = datetime.datetime.fromtimestamp(dt/1000)
        month = dt.month - 1 + months
        year = dt.year + month // 12
        month = month % 12 + 1

        day = min(dt.day,calendar.monthrange(year,month)[1])
        return (time.mktime(dt.replace(year=year, month=month, day=day).timetuple()) + 86400) * 1000


    #申请证书
    def GetDVSSL(self,get):
        get.id = public.M('domain').where('name=?',(get.domain,)).getField('pid')
        if hasattr(get,'siteName'):
            get.path = public.M('sites').where('id=?',(get.id,)).getField('path')
        else:
            get.siteName = public.M('sites').where('id=?',(get.id,)).getField('name')

        #当申请二级域名为www时，检测主域名是否绑定到同一网站
        if get.domain[:4] == 'www.':
            if not public.M('domain').where('name=? AND pid=?',(get.domain[4:],get.id)).count():
                return public.returnMsg(False,"申请[%s]证书需要验证[%s]请将[%s]绑定并解析到站点!" % (get.domain,get.domain[4:],get.domain[4:]))

        #检测是否开启强制HTTPS
        if not self.CheckForceHTTPS(get.siteName):
            return public.returnMsg(False,'当前网站已开启【强制HTTPS】,请先关闭此功能再申请SSL证书!')

        #获取真实网站运行目录
        runPath = self.GetRunPath(get)
        if runPath != False and runPath != '/': get.path +=  runPath


        #提前模拟测试验证文件值是否正确
        authfile = get.path + '/.well-known/pki-validation/fileauth.txt'
        if not self.CheckDomain(get):
            if not os.path.exists(authfile):
                return public.returnMsg(False,'无法写入验证文件: {}'.format(authfile))
            else:
                msg = '''无法正确访问验证文件<br><a class="btlink" href="{c_url}" target="_blank">{c_url}</a> <br><br>
                <p></b>可能的原因：</b></p>
                1、未正确解析，或解析未生效 [请正确解析域名，或等待解析生效后重试]<br>
                2、检查是否有设置301/302重定向 [请暂时关闭重定向相关配置]<br>
                3、检查该网站是否设置强制HTTPS [请暂时关闭强制HTTPS功能]<br>'''.format(c_url = self._check_url)
                return public.returnMsg(False,msg)

        action = 'GetDVSSL'
        if hasattr(get,'partnerOrderId'):
            self.__PDATA['data']['partnerOrderId'] = get.partnerOrderId
            action = 'ReDVSSL'

        self.__PDATA['data']['domain'] = get.domain
        self.__PDATA['data'] = self.De_Code(self.__PDATA['data'])

        result = self.request_post(self.__APIURL + '/' + action,self.__PDATA)
        if 'data' in result:
            result['data'] = self.En_Code(result['data'])
        try:
            if 'authValue' in result['data'].keys():
                public.writeFile(authfile,result['data']['authValue'])
        except:
            try:
                public.writeFile(authfile,result['data']['authValue'])
            except:
                return result

        return result

    #检测是否强制HTTPS
    def CheckForceHTTPS(self,siteName):
        conf_file = '/www/server/panel/vhost/nginx/{}.conf'.format(siteName)
        if not os.path.exists(conf_file):
            return True

        conf_body = public.readFile(conf_file)
        if not conf_body: return True
        if conf_body.find('HTTP_TO_HTTPS_START') != -1:
            return False
        return True

    #获取运行目录
    def GetRunPath(self,get):
        if hasattr(get,'siteName'):
            get.id = public.M('sites').where('name=?',(get.siteName,)).getField('id')
        else:
            get.id = public.M('sites').where('path=?',(get.path,)).getField('id')
        if not get.id: return False
        import panelSite
        result = panelSite.panelSite().GetSiteRunPath(get)
        return result['runPath']


    #检查域名是否解析
    def CheckDomain(self,get):
        try:

            self._check_url = 'http://127.0.0.1/.well-known/pki-validation/fileauth.txt'
            #创建目录
            spath = get.path + '/.well-known/pki-validation'
            if not os.path.exists(spath):
                os.makedirs(spath,0o755, True)
                #public.ExecShell("mkdir -p '" + spath + "'")

            #生成并写入检测内容
            epass = public.GetRandomString(32)
            public.writeFile(spath + '/fileauth.txt',epass)

            #检测目标域名访问结果
            if get.domain[:4] == 'www.':   #申请二级域名为www时检测主域名
                get.domain = get.domain[4:]

            import http_requests

            result = http_requests.get(self._check_url,s_type='curl',timeout=6,headers={"host":get.domain}).text
            self.__test = result
            if result == epass: return True
            self._check_url = self._check_url.replace('127.0.0.1', get.domain)
            return False
        except:
            self._check_url = self._check_url.replace('127.0.0.1', get.domain)
            return False

    #确认域名
    def Completed(self,get):
        self.__PDATA['data']['partnerOrderId'] = get.partnerOrderId
        self.__PDATA['data'] = self.De_Code(self.__PDATA['data'])
        if hasattr(get,'siteName'):
            site_data = public.M('sites').where('id=?',(public.M('domain').where('name=?',(get.siteName)).getField('pid'),)).find()
            if not site_data: return public.returnMsg(False,'站点不存在')
            get.path = site_data['path']
            get.siteName = site_data['name']
            if public.M('sites').where('id=?',(public.M('domain').where('name=?',(get.siteName)).getField('pid'),)).getField('project_type') == 'Java' or public.M('sites').where('id=?',(public.M('domain').where('name=?',(get.siteName)).getField('pid'),)).getField('project_type') == 'Go' or public.M('sites').where('id=?',(public.M('domain').where('name=?',(get.siteName)).getField('pid'),)).getField('project_type') == 'Other':
                runPath='/www/wwwroot/java_node_ssl'
            else:
                runPath = self.GetRunPath(get)
            if runPath != False and runPath != '/': get.path +=  runPath

            sslInfo = self.request_post(self.__APIURL + '/SyncOrder',self.__PDATA)
            if not 'data' in sslInfo: return sslInfo

            sslInfo['data'] = self.En_Code(sslInfo['data'])
            try:

                if public.M('sites').where('id=?',(public.M('domain').where('name=?',(get.siteName)).getField('pid'),)).getField('project_type') == 'Java' or public.M('sites').where('id=?',(public.M('domain').where('name=?',(get.siteName)).getField('pid'),)).getField('project_type') == 'Go' or public.M('sites').where('id=?',(public.M('domain').where('name=?',(get.siteName)).getField('pid'),)).getField('project_type') == 'Other':
                    spath = '/www/wwwroot/java_node_ssl/.well-known/pki-validation'
                else:
                    spath = get.path + '/.well-known/pki-validation'
                if not os.path.exists(spath): public.ExecShell("mkdir -p '" + spath + "'")
                public.writeFile(spath + '/' + sslInfo['data']['authKey'],sslInfo['data']['authValue'])
            except:
                return public.returnMsg(False,'SSL_CHECK_WRITE_ERR')
        try:
            result = self.request_post(self.__APIURL + '/Completed',self.__PDATA)
            if 'data' in result:
                result['data'] = self.En_Code(result['data'])
        except:
            result = public.returnMsg(True,'检测中..')
        n = 0
        my_ok = False
        while True:
            if n > 5: break
            time.sleep(5)

            rRet  = self.request_post(self.__APIURL + '/SyncOrder',self.__PDATA)
            n +=1

            if 'data' in rRet:
                rRet['data'] = self.En_Code(rRet['data'])
            try:
                if rRet['data']['stateCode'] == 'COMPLETED':
                    my_ok = True
                    break
            except: return public.get_error_info()
        if not my_ok:

            return result
        return rRet

    #同步指定订单
    def SyncOrder(self,get):
        self.__PDATA['data']['partnerOrderId'] = get.partnerOrderId
        self.__PDATA['data'] = self.De_Code(self.__PDATA['data'])

        result = self.request_post(self.__APIURL + '/SyncOrder',self.__PDATA)
        if 'data' in result:
            result['data'] = self.En_Code(result['data'])
        return result

    def GetSSLInfoTo(self, get):
        self.__PDATA['data']['partnerOrderId'] = get.partnerOrderId
        self.__PDATA['data'] = self.De_Code(self.__PDATA['data'])

        result = self.request_post(self.__APIURL + '/GetSSLInfo', self.__PDATA)
        if not 'data' in result: return result
        result['data'] = self.En_Code(result['data'])
        return result['data']

    #获取证书
    def GetSSLInfo(self,get):
        self.__PDATA['data']['partnerOrderId'] = get.partnerOrderId
        self.__PDATA['data'] = self.De_Code(self.__PDATA['data'])
        time.sleep(3)

        result = self.request_post(self.__APIURL + '/GetSSLInfo',self.__PDATA)
        if not 'data' in result: return result

        result['data'] = self.En_Code(result['data'])
        if not 'privateKey' in result['data']: return result

        #写配置到站点
        if hasattr(get,'siteName'):
            try:
                siteName = get.siteName
                path = '/www/server/panel/vhost/cert/' + siteName
                if not os.path.exists(path):
                    public.ExecShell('mkdir -p ' + path)
                csrpath = path+"/fullchain.pem"
                keypath = path+"/privkey.pem"
                pidpath = path+"/partnerOrderId"
                #清理旧的证书链
                public.ExecShell('rm -f ' + keypath)
                public.ExecShell('rm -f ' + csrpath)
                public.ExecShell('rm -rf ' + path + '-00*')
                public.ExecShell('rm -rf /etc/letsencrypt/archive/' + get.siteName)
                public.ExecShell('rm -rf /etc/letsencrypt/archive/' + get.siteName + '-00*')
                public.ExecShell('rm -f /etc/letsencrypt/renewal/'+ get.siteName + '.conf')
                public.ExecShell('rm -f /etc/letsencrypt/renewal/'+ get.siteName + '-00*.conf')
                public.ExecShell('rm -f ' + path + '/README')
                public.ExecShell('rm -f ' + path + '/certOrderId')

                public.writeFile(keypath,result['data']['privateKey'])
                public.writeFile(csrpath,result['data']['cert']+result['data']['certCa'])
                public.writeFile(pidpath,get.partnerOrderId)
                import panelSite
                panelSite.panelSite().SetSSLConf(get)
                public.serviceReload()
                get.csr = result['data']['cert']+result['data']['certCa']
                self.set_exclude_hash(get)
                return public.returnMsg(True,'SET_SUCCESS')
            except:
                return public.returnMsg(False,'SET_ERROR')
        result['data'] = self.En_Code(result['data'])
        return result

    def _hash(self, cert_filename: str = None, certificate: str = None, ignore_errors: bool = False):
        if cert_filename is not None and os.path.isfile(cert_filename):
            certificate = public.readFile(cert_filename)

        if not isinstance(certificate, str) or not certificate.startswith("-----BEGIN"):
            if ignore_errors:
                return None
            raise ValueError("证书格式错误")

        md5_obj = md5()
        md5_obj.update(certificate.encode("utf-8"))
        return md5_obj.hexdigest()

    def get_exclude_hash(self, get):
        path = '{}/data/exclude_hash.json'.format(public.get_panel_path())
        if os.path.exists(path):
            try:
                data = json.loads(public.readFile(path))
                if data['version'] == "2":
                    return data
            except:
                pass

        data = {"version": "2", "exclude_hash": {}}
        try:
            _cert_data = self.get_order_list(get)
            for i in _cert_data:
                if i['orderStatus'] != 'COMPLETE':
                    continue
                try:
                    get.oid = i['oid']
                    self.__init__()
                    certInfo = self.get_order_find(get)
                    data['exclude_hash'].update(
                        {i['oid']: self._hash(certificate=certInfo['certificate'] + "\n" + certInfo['caCertificate'])}
                    )
                except Exception as e:
                    continue
            self.__init__()
            test_cert_data = self.GetOrderList(get)
            for j in test_cert_data['data']:
                if j['stateCode'] != 'COMPLETED':
                    continue
                try:
                    get.partnerOrderId = j['partnerOrderId']
                    self.__init__()
                    certInfo = self.GetSSLInfoTo(get)
                    data['exclude_hash'].update(
                        {j['partnerOrderId']: self._hash(certificate=certInfo['cert'] + certInfo['certCa'])}
                    )
                except Exception as e:
                    continue
        except:
            return data
        public.writeFile(path, json.dumps(data))
        return data

    def set_exclude_hash(self, get):
        try:
            path = '{}/data/exclude_hash.json'.format(public.get_panel_path())
            try:
                data = json.loads(public.readFile(path))
            except:
                data = self.get_exclude_hash(get)
            if 'oid' in get:
                order = get.oid
            elif 'partnerOrderId' in get:
                order = get.partnerOrderId
            data['exclude_hash'].update({order: self._hash(certificate=get.csr)})
            public.writeFile(path, json.dumps(data))
        except:
            pass

    def GetSiteDomain(self,get):
        """
        @name 获取网站域名对应的站点名
        @param cert_list 证书域名列表
        @auther hezhihong
        return 证书域名对应的站点名字典，如证书域名未绑定则为空
        """
        all_site=[]  #所有站点名列表
        cert_list=[] #证书域名列表
        site_list=[] #证书域名列表对应的站点名列表
        all_domain = [] #所有域名列表
        try:
            cert_list=json.loads(get.cert_list)
        except:pass
        result={}
        #取所有站点名和所有站点的绑定域名
        all_sites=public.M('sites').field('name').select()
        for site in all_sites:
            all_site.append(site['name'])
            if not cert_list:continue
            tmp_dict={}
            tmp_dict['name']=site['name']
            pid = public.M('sites').where("name=?",(site['name'],)).getField('id')
            domain_list=public.M('domain').where("pid=?",(pid,)).field('name').select()
            for domain in domain_list:
                all_domain.append(domain['name'])
        #取证书域名所在的所有域名列表
        site_domain=[]#证书域名对应的站点名列表
        if cert_list and all_domain:
            for cert in cert_list:
                d_cert=''
                if re.match("^\*\..*",cert):
                    d_cert=cert.replace('*.','')
                for domain in all_domain:
                    if cert == domain:
                        site_domain.append(domain)
                    else:
                        replace_str=domain.split('.')[0]+'.'
                        if d_cert and d_cert==domain.replace(replace_str,''):
                            site_domain.append(domain)
        #取证书域名对应的站点名
        for site in site_domain:
            site_id=public.M('domain').where("name=?",(site,)).getField('pid')
            site_name=public.M('sites').where("id=?",(site_id,)).getField('name')
            site_list.append(site_name)
        site_list=sorted(set(site_list),key=site_list.index)
        result['all']=all_site
        result['site']=site_list
        return  result


    def SetBatchCertToSite(self,get):
        """
        @name 批量部署证书
        @auther hezhihong
        """
        ssl_list=[]
        if not hasattr(get,'BatchInfo') or not get.BatchInfo:return public.returnMsg(False,'参数错误')
        else:
            ssl_list=json.loads(get.BatchInfo)
        if isinstance(ssl_list, list):
            total_num = len(ssl_list)
            resultinfo = {"total":total_num,"success": 0, "faild": 0,"successList":[],"faildList":[]}
            successList = []
            faildList=[]
            successnum=0
            failnum=0
            for Info in ssl_list:
                set_result={}
                set_result['status']=True
                get.certName =set_result['certName']= Info.get('certName')
                get.siteName =set_result['siteName']= str(Info['siteName'])  # 站点名称必定为字符串
                get.isBatch=True
                if "ssl_hash" in Info:
                    get.ssl_hash=Info['ssl_hash']
                result=self.SetCertToSite(get)
                if not result or (isinstance(result, dict) and not result['status']):
                    set_result['status']=False
                    failnum+=1
                    set_result["error_msg"] = ''
                    if isinstance(result, dict) and 'msg' in result:
                        set_result["error_msg"] = result['msg']
                    faildList.append(set_result)
                else:
                    successnum+=1
                    successList.append(set_result)
                public.writeSpeed('setssl', successnum+failnum, total_num)
            import firewalls
            get.port = '443'
            get.ps = 'HTTPS'
            firewalls.firewalls().AddAcceptPort(get)
            public.serviceReload()
            resultinfo['success']=successnum
            resultinfo['faild']= failnum
            resultinfo['successList']=  successList
            resultinfo['faildList']=  faildList

            if hasattr(get, "set_https_mode") and get.set_https_mode.strip() in (True, 1, "1", "true"):
                import panelSite
                sites_obj = panelSite.panelSite()
                if not sites_obj.get_https_mode():
                    sites_obj.set_https_mode()

        else:return public.returnMsg(False,'参数类型错误')
        return resultinfo

    #部署证书夹证书
    def SetCertToSite(self,get):
        """
        @name 兼容批量部署
        @auther hezhihong
        """

        try:
            result = self.GetCert(get)
            if not 'privkey' in result: return result
            siteName = get.siteName
            path = '/www/server/panel/vhost/cert/' + siteName
            if not os.path.exists(path):
                public.ExecShell('mkdir -p ' + path)
            csrpath = path+"/fullchain.pem"
            keypath = path+"/privkey.pem"

            #清理旧的证书链
            public.ExecShell('rm -f ' + keypath)
            public.ExecShell('rm -f ' + csrpath)
            public.ExecShell('rm -rf ' + path + '-00*')
            public.ExecShell('rm -rf /etc/letsencrypt/archive/' + get.siteName)
            public.ExecShell('rm -rf /etc/letsencrypt/archive/' + get.siteName + '-00*')
            public.ExecShell('rm -f /etc/letsencrypt/renewal/'+ get.siteName + '.conf')
            public.ExecShell('rm -f /etc/letsencrypt/renewal/'+ get.siteName + '-00*.conf')
            public.ExecShell('rm -f ' + path + '/README')
            if os.path.exists(path + '/certOrderId'): os.remove(path + '/certOrderId')

            public.writeFile(keypath,result['privkey'])
            public.writeFile(csrpath,result['fullchain'])
            import panelSite
            return panelSite.panelSite().SetSSLConf(get)
            public.serviceReload()
            return public.returnMsg(True,'SET_SUCCESS')
        except Exception as ex:
            if 'isBatch' in get:return False
            return public.returnMsg(False,'SET_ERROR,' + public.get_error_info())

    #获取证书列表
    def GetCertList(self,get):
        try:
            vpath = '/www/server/panel/vhost/ssl'
            if 'vpath' in get: vpath = get.vpath
            if not os.path.exists(vpath): public.ExecShell("mkdir -p " + vpath)
            data = []
            for d in os.listdir(vpath):
                mpath = vpath + '/' + d + '/info.json'
                if not os.path.exists(mpath): continue
                tmp = public.readFile(mpath)
                if not tmp: continue
                tmp1 = json.loads(tmp)
                data.append(tmp1)
            return data
        except:
            return []

    #删除证书
    def RemoveCert(self,get):
        try:
            vpath = '/www/server/panel/vhost/ssl/' + get.certName.replace("*.",'')
            if not os.path.exists(vpath): return public.returnMsg(False,'证书不存在!')
            public.ExecShell("rm -rf " + vpath)
            return public.returnMsg(True,'证书已删除!')
        except:
            return public.returnMsg(False,'删除失败!')

    #保存证书
    def SaveCert(self,get):
        try:
            certInfo = self.GetCertName(get)
            if not certInfo:
                return public.returnMsg(False, '证书解析失败!')
            SSLManger().save_by_file(get.certPath, get.keyPath)
            vpath = '/www/server/panel/vhost/ssl/' + certInfo['subject']
            vpath=vpath.replace("*.",'')
            if not os.path.exists(vpath):
                public.ExecShell("mkdir -p " + vpath)
            public.writeFile(vpath + '/privkey.pem',public.readFile(get.keyPath))
            public.writeFile(vpath + '/fullchain.pem',public.readFile(get.certPath))
            public.writeFile(vpath + '/info.json',json.dumps(certInfo))
            return public.returnMsg(True,'证书保存成功!')
        except:
            return public.returnMsg(False,'证书保存失败!')

    #读取证书
    def GetCert(self,get):
        if "ssl_hash" in get:
            from ssl_manage import SSLManger
            return SSLManger.get_cert_for_deploy(get.ssl_hash.strip())
        vpath = os.path.join('/www/server/panel/vhost/ssl' , get.certName.replace("*.",''))
        if not os.path.exists(vpath): return public.returnMsg(False,'证书不存在!')
        data = {}
        data['privkey'] = public.readFile(vpath + '/privkey.pem')
        data['fullchain'] = public.readFile(vpath + '/fullchain.pem')
        return data

    #获取证书名称
    def GetCertName(self,get):
        return self.get_cert_init(get.certPath)


    def get_unixtime(self,data,format = "%Y-%m-%d %H:%M:%S"):
        import time
        timeArray = time.strptime(data,format )
        timeStamp = int(time.mktime(timeArray))
        return timeStamp

    # 获取指定证书基本信息
    def get_cert_init(self, pem_file):
        if "/www/server/panel/class" not in sys.path:
            sys.path.insert(0, "/www/server/panel/class")
        import ssl_info
        return ssl_info.ssl_info().load_ssl_info(pem_file)

        # if not os.path.exists(pem_file):
        #     return None
        # try:
        #     import OpenSSL
        #     result = {}
        #     x509 = OpenSSL.crypto.load_certificate(
        #         OpenSSL.crypto.FILETYPE_PEM, public.readFile(pem_file))
        #     # 取产品名称
        #     issuer = x509.get_issuer()
        #     result['issuer'] = ''
        #     if hasattr(issuer, 'CN'):
        #         result['issuer'] = issuer.CN
        #     if not result['issuer']:
        #         is_key = [b'0', '0']
        #         issue_comp = issuer.get_components()
        #         if len(issue_comp) == 1:
        #             is_key = [b'CN', 'CN']
        #         for iss in issue_comp:
        #             if iss[0] in is_key:
        #                 result['issuer'] = iss[1].decode()
        #                 break
        #     if not result['issuer']:
        #         if hasattr(issuer, 'O'):
        #             result['issuer'] = issuer.O
        #     # 取到期时间
        #     result['notAfter'] = self.strf_date(
        #         bytes.decode(x509.get_notAfter())[:-1])
        #     # 取申请时间
        #     result['notBefore'] = self.strf_date(
        #         bytes.decode(x509.get_notBefore())[:-1])
        #     # 取可选名称
        #     result['dns'] = []
        #     for i in range(x509.get_extension_count()):
        #         s_name = x509.get_extension(i)
        #         if s_name.get_short_name() in [b'subjectAltName', 'subjectAltName']:
        #             s_dns = str(s_name).split(',')
        #             for d in s_dns:
        #                 result['dns'].append(d.split(':')[1])
        #     subject = x509.get_subject().get_components()
        #     # 取主要认证名称
        #     if len(subject) == 1:
        #         result['subject'] = subject[0][1].decode()
        #     else:
        #         if not result['dns']:
        #             for sub in subject:
        #                 if sub[0] == b'CN':
        #                     result['subject'] = sub[1].decode()
        #                     break
        #             if 'subject' in result:
        #                 result['dns'].append(result['subject'])
        #         else:
        #             result['subject'] = result['dns'][0]
        #     result['endtime'] = int(int(time.mktime(time.strptime(result['notAfter'], "%Y-%m-%d")) - time.time()) / 86400)
        #     return result
        # except:
        #     return None


    #获取产品列表
    def GetSSLProduct(self,get):
        self.__PDATA['data'] = self.De_Code(self.__PDATA['data'])

        result = self.request_post(self.__APIURL + '/GetSSLProduct',self.__PDATA)
        if 'data' in result:
            result['data'] = self.En_Code(result['data'])
        return result

    #加密数据
    def De_Code(self,data):
        if sys.version_info[0] == 2:
            import urllib
            pdata = urllib.urlencode(data)
            return binascii.hexlify(pdata)
        else:
            import urllib.parse
            pdata = urllib.parse.urlencode(data)
            if type(pdata) == str: pdata = pdata.encode('utf-8')
            return binascii.hexlify(pdata).decode()

    #解密数据
    def En_Code(self,data):
        if sys.version_info[0] == 2:
            import urllib
            result = urllib.unquote(binascii.unhexlify(data))
        else:
            import urllib.parse
            if type(data) == str: data = data.encode('utf-8')
            tmp = binascii.unhexlify(data)
            if type(tmp) != str: tmp = tmp.decode('utf-8')
            result = urllib.parse.unquote(tmp)

        if type(result) != str: result = result.decode('utf-8')
        return json.loads(result)

    # 手动一键续签
    def renew_lets_ssl(self, get):
        if not os.path.exists('vhost/cert/crontab.json'):
            return public.returnMsg(False,'当前没有可以续订的证书!')

        old_list = json.loads(public.ReadFile("vhost/cert/crontab.json"))
        cron_list = old_list
        if hasattr(get, 'siteName'):
            if not get.siteName in old_list:
                return public.returnMsg(False,'当前网站没有可以续订的证书.')
            cron_list = {}
            cron_list[get.siteName] = old_list[get.siteName]

        import panelLets
        lets = panelLets.panelLets()

        result = {}
        result['status'] = True
        result['sucess_list']  = []
        result['err_list'] = []
        for siteName in cron_list:
            data = cron_list[siteName]
            ret = lets.renew_lest_cert(data)
            if ret['status']:
                result['sucess_list'].append(siteName)
            else:
                result['err_list'].append({"siteName":siteName,"msg":ret['msg']})
        return result


    def renew_cert_order(self,args):
        '''
            @name 续签商用证书
            @author cjx
            @version 1.0
        '''
        if not 'pdata' in args:
            return public.returnMsg(False,'pdata参数不能为空!')
        pdata = json.loads(args.pdata)
        pdata['version'] = '2'
        self.__PDATA['data'] = pdata

        result = self.request('renew_cert_order')
        if 'status' in result:
            if result['status'] == True:
                self.__PDATA['data'] = {}
                args['oid'] = result['oid']
                result['verify_info'] = self.get_verify_info(args)
        return result

    def auto_renew_ca(self,args):
        '''
            @name 自动续签商用证书
            @author csj
            @version 1.0
        '''
        self.__PDATA['data'] ={}
        self.__PDATA['data']['oid'] = args.oid
        self.__PDATA['data']['pid'] = args.pid

        result = self.request_v2('cert_test/auto_renew_ca')
        return result

    # 第三方授权登录
    # 1. 腾讯云
    # 2. 阿里云
    # 3. 华为云
    def GetCloudType(self, get):
        """
        通过文件判断获取云服务商类型
        """
        # client  服务商标识 0：宝塔账号，1：腾讯云，2：阿里云
        # login  授权登录方式，0：宝塔账号，1：一键登录，2：授权登录

        service, server_type = public.get_cloud_server_type()

        if service == 'tencent':
            client = 1
            if server_type == 'lighthouse':
                login = 1
            else:
                login = 0
        elif service == 'aliyun':
            client = 2
            login = 1
            if os.path.exists('/home/admin') and not os.path.exists('/root/.swas/machine-info'):
                client = 0
                login = 0
        else:
            client = 0
            login = 0

        return {'client': client, 'login': login}


    def GetAuthUrl(self, get):
        """
        获取授权连接
        """
        dic = {
            1: self.TencentcloudMarketAuth,
            2: None,  # 阿里云不需要获取授权链接
        }
        fun = dic.get(int(get.client))
        if not fun:
            return public.returnMsg(False, '未知客户端类型')
        return fun(get)

    def AuthLogin(self, get):
        """
        授权登录
        """
        dic = {
            1: self.TencentcloudMarketAuthLogin,
            2: self.AliyunAccountLogin,
        }
        fun = dic.get(int(get.client))
        if not fun:
            return public.returnMsg(False, '未知客户端类型')
        return fun(get)

    def TencentcloudMarketAuth(self, get):
        """
        腾讯云-获取授权连接
        """
        try:
            data = {}
            order_no = get.order_no
            uin = get.uin
            # , 'uin': uin
            data['sing'] = self.De_Code({'serverid': panelAuth().get_serverid(), 'order_no': order_no, 'uin': uin})
            # public.print_log(data['sing'])
            data['os'] = 'Linux'
            result = self.request_post(self.__APIURL3 + "/tencent_cloud_market/auth_url", data)
            if not result['success']:
                return public.returnMsg(False, result['res'])
            # public.print_log(result)
            result['data'] = result['res']
            result['status'] = result['success']
            del result['success']
            del result['res']
            return result
        except Exception as ex:
            error = str(ex)
            if error.lower().find('json') >= 0:
                error = '<br>错误：连接宝塔官网异常，请按照以下方法排除问题后重试：<br>解决方法：<a target="_blank" class="btlink" href="https://www.bt.cn/bbs/thread-87257-1-1.html">https://www.bt.cn/bbs/thread-87257-1-1.html</a><br>'
                return public.returnMsg(False, error)
            else:
                return public.returnMsg(False, 6)

    def tencent_no_secret_login(self, get):
        """
        腾讯云一键登录
        @param get:
        @return:
        """
        # 判断授权文件是否存在
        if not os.path.exists('/usr/local/qcloud/lighthouse/.cert/machine-info'):
            return public.returnMsg(False, '激活失败，授权文件不存在')
        # 读取授权文件
        try:
            json_data = json.loads(public.readFile('/usr/local/qcloud/lighthouse/.cert/machine-info'))
            identity = json_data.get('identity')
            signature = json_data.get('signature')
            if not identity or not signature:
                return public.returnMsg(False, '激活失败，授权文件格式错误')
        except:
            return public.returnMsg(False, '激活失败，授权文件读取失败')
        # 登录
        serverid = panelAuth().get_serverid()
        data = {
            'identity': identity,
            'signature': signature,
            'serverid': serverid,
        }

        o_code = public.readFile('data/o.pl')
        if not o_code: o_code = ''
        data['o'] = o_code.strip()

        # 保存当前的IP类型配置
        v4_file = '{}/data/v4.pl'.format(public.get_panel_path())
        original_ip_config = ''
        if os.path.exists(v4_file):
            original_ip_config = public.readFile(v4_file).strip()

        # 强制设置为使用IPv4
        public.writeFile(v4_file, '-4')
        try:
            result = self.request_post(self.__APIURL3 + "/tencent_cloud_auth/no_secret_login", data)
            # 恢复原始IP类型配置
            public.writeFile(v4_file, original_ip_config)

            public.print_log(result)
            if not result['success']:
                return public.returnMsg(False, result['res'])
            if result['res']:
                if result['res']['serverid'] != serverid:  # 保存新的serverid
                    public.writeFile('data/sid.pl', result['res']['serverid'])
                public.writeFile(self.__UPATH, json.dumps(result['res']))
                if os.path.exists('data/bind_path.pl'): os.remove('data/bind_path.pl')
                public.flush_plugin_list()
            del result['res']
            session['focre_cloud'] = True
            result['status'] = result['success']
            del result['success']
            return result

        except Exception as ex:
            # 恢复原始IP类型配置
            public.writeFile(v4_file, original_ip_config)

            error = str(ex)
            if error.lower().find('json') >= 0:
                error = '<br>错误：连接宝塔官网异常，请按照以下方法排除问题后重试：<br>解决方法：<a target="_blank" class="btlink" href="https://www.bt.cn/bbs/thread-87257-1-1.html">https://www.bt.cn/bbs/thread-87257-1-1.html</a><br>'
                return public.returnMsg(False, error)
            else:
                return public.returnMsg(False, 6)


    def TencentcloudMarketAuthLogin(self, get):
        """
        腾讯云-授权登录
        """

        if 'code' not in get:
            return self.tencent_no_secret_login(get)

        data = {}
        serverid = panelAuth().get_serverid()
        data['sing'] = self.De_Code({'serverid': panelAuth().get_serverid()})
        data['signature'] = get.signature
        data['code'] = get.code
        data['state'] = get.state
        data['os'] = 'Linux'

        o_code = public.readFile('data/o.pl')
        if not o_code: o_code = ''
        data['o'] = o_code.strip()

        pdata = {}
        pdata['data'] = self.De_Code(data)
        try:
            result = self.request_post(self.__APIURL3 + "/tencent_cloud_market/auth_login", data)
            if not result['success']:
                return public.returnMsg(False, result['res'])
            if result['res']:
                if result['res']['serverid'] != serverid: # 保存新的serverid
                    public.writeFile('data/sid.pl',result['res']['serverid'])
                public.writeFile(self.__UPATH,json.dumps(result['res']))
                if os.path.exists('data/bind_path.pl'): os.remove('data/bind_path.pl')
                public.flush_plugin_list()
            del result['res']
            session['focre_cloud'] = True
            result['status'] = result['success']
            del result['success']
            return result

        except Exception as ex:
            error = str(ex)
            if error.lower().find('json') >= 0:
                error = '<br>错误：连接宝塔官网异常，请按照以下方法排除问题后重试：<br>解决方法：<a target="_blank" class="btlink" href="https://www.bt.cn/bbs/thread-87257-1-1.html">https://www.bt.cn/bbs/thread-87257-1-1.html</a><br>'
                return public.returnMsg(False, error)
            else:
                return public.returnMsg(False, 6)

    def AliyunAccountLogin(self, get):
        """
        阿里云-授权登录
        """
        # 判断授权文件是否存在
        if not os.path.exists('/root/.swas/machine-info'):
            return self.AliyunAccountLoginV3(get)
        # 读取授权文件
        try:
            json_data = json.loads(public.readFile('/root/.swas/machine-info'))
        except:
            return public.returnMsg(False, '授权文件读取失败!')
        # 登录
        serverid = panelAuth().get_serverid()
        json_data['serverid'] = serverid

        o_code = public.readFile('data/o.pl')
        if not o_code: o_code = ''
        json_data['o'] = o_code.strip()

        try:
            result = self.request_post(self.__APIURL3 + "/aliyun_auth/bt_panel_auth", json_data)
            public.print_log(result)
            if not result['success']:
                return public.returnMsg(False, result['res'])
            if result['res']:
                if result['res']['serverid'] != serverid: # 保存新的serverid
                    public.writeFile('data/sid.pl',result['res']['serverid'])
                public.writeFile(self.__UPATH,json.dumps(result['res']))
                if os.path.exists('data/bind_path.pl'): os.remove('data/bind_path.pl')
                public.flush_plugin_list()
            del result['res']
            session['focre_cloud'] = True
            result['status'] = result['success']
            del result['success']
            return result

        except Exception as ex:
            error = str(ex)
            if error.lower().find('json') >= 0:
                error = '<br>错误：连接宝塔官网异常，请按照以下方法排除问题后重试：<br>解决方法：<a target="_blank" class="btlink" href="https://www.bt.cn/bbs/thread-87257-1-1.html">https://www.bt.cn/bbs/thread-87257-1-1.html</a><br>'
                return public.returnMsg(False, error)
            else:
                return public.returnMsg(False, 6)

    def AliyunAccountLoginV3(self, get):
        """
        阿里云-授权登录-v2
        """
        ipv4 = public.httpGet('http://100.100.100.200/latest/meta-data/eipv4', timeout=(1, 1))
        if not ipv4:
            return public.returnMsg(False, '您的机器不支持一键登录!')
        document = public.httpGet('http://100.100.100.200/latest/dynamic/instance-identity/document', timeout=(1, 1))
        if not document:
            return public.returnMsg(False, '您的机器不支持一键登录!')
        document = json.loads(document)
        document.update({'audience': ipv4})
        signature = public.httpGet('http://100.100.100.200/latest/dynamic/instance-identity/pkcs7?audience="{}"'.format(ipv4), timeout=(1, 1))
        if not signature:
            return public.returnMsg(False, '您的机器不支持一键登录!')

        serverid = panelAuth().get_serverid()
        json_data = {
            "serverid": serverid,
            "identity": json.dumps(document),
            "signature": signature
        }

        o_code = public.readFile('data/o.pl')
        if not o_code: o_code = ''
        json_data['o'] = o_code.strip()

        # 保存当前的IP类型配置
        v4_file = '{}/data/v4.pl'.format(public.get_panel_path())
        original_ip_config = ''
        if os.path.exists(v4_file):
            original_ip_config = public.readFile(v4_file).strip()

        # 强制设置为使用IPv4
        public.writeFile(v4_file, '-4')
        try:
            result = self.request_post(self.__API + "/v2/aliyun_auth/bt_panel_auth_v2", json_data)
            # 恢复原始IP类型配置
            public.writeFile(v4_file, original_ip_config)
            if not result['success']:
                return public.returnMsg(False, result['res'])
            if result['res']:
                if result['res']['serverid'] != serverid:  # 保存新的serverid
                    public.writeFile('data/sid.pl', result['res']['serverid'])
                public.writeFile(self.__UPATH, json.dumps(result['res']))
                if os.path.exists('data/bind_path.pl'): os.remove('data/bind_path.pl')
                public.flush_plugin_list()
            del result['res']
            session['focre_cloud'] = True
            result['status'] = result['success']
            del result['success']
            return result
        except Exception as ex:
            # 恢复原始IP类型配置
            public.writeFile(v4_file, original_ip_config)
            error = str(ex)
            if error.lower().find('json') >= 0:
                error = '<br>错误：连接宝塔官网异常，请按照以下方法排除问题后重试：<br>解决方法：<a target="_blank" class="btlink" href="https://www.bt.cn/bbs/thread-87257-1-1.html">https://www.bt.cn/bbs/thread-87257-1-1.html</a><br>'
                return public.returnMsg(False, error)
            else:
                return public.returnMsg(False, 6)


    def get_mac_address(self):
        import uuid
        mac = uuid.UUID(int=uuid.getnode()).hex[-12:]
        return ":".join([mac[e:e + 2] for e in range(0, 11, 2)])


    def get_suppliers_source(self):
        """
        获取供应商来源
        """
        if os.path.exists("data/install_ltd.pl"):
            public.writeFile('data/o.pl', 'install_ltd')
            return 'install_ltd'
        else:
            o_code = public.readFile('data/o.pl')
            if not o_code: o_code = ''
            return o_code.strip()
            

    def GetAuthToken(self,get):
        """
        登录官网获取Token
        @get.username 官网手机号
        @get.password 官网账号密码
        """

        if not 'username' in get or not 'password' in get:
            return public.returnMsg(False, '请输入账号和密码')

        if not get['username'] or not get['password']:
            return public.returnMsg(False, '请输入账号和密码')

        rtmp = ""
        data = {}
        data['username'] = public.rsa_decrypt(get.username)
        data['password'] = public.md5(public.rsa_decrypt(get.password))
        data['serverid'] = panelAuth().get_serverid()
        data['os'] = 'Linux'
        data['mac'] = self.get_mac_address()
        data['o'] = self.get_suppliers_source()
        if not data['username']:
            try:
                from Crypto.PublicKey import RSA
                from Crypto.Cipher import PKCS1_v1_5 as Cipher_pkcs
            except:
                return public.returnMsg(False, public.get_error_info())

        if 'code' in get: data['code'] = get.code
        if 'token' in get: data['token'] = get.token

        if os.path.exists("data/install_ltd.pl"):
            data['o'] = 'install_ltd'
            public.writeFile('data/o.pl', 'install_ltd')
        else:
            o_code = public.readFile('data/o.pl')
            if not o_code: o_code = ''
            data['o'] = o_code.strip()

        pdata = {}
        pdata['data'] = self.De_Code(data)
        try:

            result = self.request_post(self.__BINDURL,pdata)
            if not 'data' in result: return result

            result['data'] = self.En_Code(result['data'])
            if not result['status']: return result

            if result['data']:
                if result['data']['serverid'] != data['serverid']: # 保存新的serverid
                    public.writeFile('data/sid.pl',result['data']['serverid'])
                public.writeFile(self.__UPATH,json.dumps(result['data']))
                if os.path.exists('data/bind_path.pl'): os.remove('data/bind_path.pl')
                public.flush_plugin_list()
            del(result['data'])
            session['focre_cloud'] = True
            return result
        except Exception as ex:
            error = str(ex)
            if os.path.exists('data/debug.pl'):
                public.debug_log()
            if error.lower().find('json') >= 0:
                error = '<br>错误：连接宝塔官网异常，请按照以下方法排除问题后重试：<br>解决方法：<a target="_blank" class="btlink" href="https://www.bt.cn/bbs/thread-87257-1-1.html">https://www.bt.cn/bbs/thread-87257-1-1.html</a><br>'
                # raise public.PanelError(error)
                return public.returnMsg(False, 6)
            else:
                return public.returnMsg(False, 6)
                # raise public.error_conn_cloud(error)
            # return public.returnMsg(False,'连接服务器失败!<br>{}'.format(rtmp))

    def GetBindCode(self,get):
        """
        获取验证码
        """
        rtmp = ""
        data = {}
        data['username'] = get.username
        data['token'] = get.token
        pdata = {}
        pdata['data'] = self.De_Code(data)
        try:
            result = self.request_post(self.__CODEURL,pdata)
            return result
        except Exception as ex:
            raise public.error_conn_cloud(str(ex))
            # return public.returnMsg(False,'连接服务器失败!<br>' + rtmp)


    def GetWechatAuthUrl(self, get):
        """
        获取微信授权扫码URL地址
        """
        try:
            result = self.request_post(self.__WECHAT_AUTH_URL,{})
            if result['res'] and 'url' in result['res']:
                return public.returnMsg(result['success'], result['res']['url'])
            else:
                return public.returnMsg(result['success'], result['res'])
        except Exception as ex:
            raise public.error_conn_cloud(str(ex))
        
    def SetWechatBindUser(self, get):
        """
        微信绑定，用于绑定微信账号到宝塔账号
        """
        try:
            # 获取参数
            pdata = {}
            pdata['o'] = self.get_suppliers_source() # 供应商来源
            pdata['serverid'] = panelAuth().get_serverid() # 宝塔ID
            pdata['mac'] = self.get_mac_address() # 机器码
            pdata['os'] = 'Linux' # 操作系统
            pdata['code'] = get.code # 微信授权code
            pdata['state'] = get.state # 授权标识
            result = self.request_post(self.__WECHAT_CHECK_USER_URL, pdata)
            if not 'res' in result: return result
            result['res'] = self.En_Code(result['res'])
            if result['res'] and result['success']:
                if result['res']['serverid'] != pdata['serverid']: # 保存新的serverid
                    public.writeFile('data/sid.pl',result['res']['serverid'])
                public.writeFile(self.__UPATH,json.dumps(result['res']))
                public.flush_plugin_list()
            else:
                return public.returnMsg(False, result['res'])
            del(result['res'])
            session['focre_cloud'] = True
            return public.returnMsg(True,'绑定成功')
        except Exception as ex:
            raise public.error_conn_cloud(str(ex))

    # 解析DNSAPI信息
    def get_dnsapi(self, auth_to):
        tmp = auth_to.split('|')
        dns_name = tmp[0]
        key = "None"
        secret = "None"
        if len(tmp) < 3:
            dnsapi_config = json.loads(public.readFile('{}/config/dns_api.json'.format(public.get_panel_path())))
            for dc in dnsapi_config:
                if dc['name'] != dns_name:
                    continue
                if not dc['data']:
                    continue
                key = dc['data'][0]['value']
                secret = dc['data'][1]['value']
        else:
            key = tmp[1]
            secret = tmp[2]
        return dns_name, key, secret

    #获取dnsapi对象
    def get_dns_class(self,auth_to):
        try:
            import panelDnsapi
            dns_name, key, secret = self.get_dnsapi(auth_to)
            dns_class = getattr(panelDnsapi, dns_name)(key, secret)
            dns_class._type = 1
            return dns_class
        except :
            return None

    # 解析域名
    def create_dns_record(self, auth_to, domain, dns_value, original_domain=None):
        # 如果为手动解析
        if auth_to == 'dns':
            return None
        try:
            from sslModel import dataModel
            dataModel.main().add_dns_value_by_domain(domain, dns_value, "CNAME")
            return public.returnMsg(True,'添加成功')
        except Exception as e:
            return public.returnMsg(False, str(e))

    def apply_cert_install_pay(self,args):
        '''
            @name 单独购买人工安装服务
            @param args<dict_obj>{
                'oid'<int> 订单ID
            }
        '''
        if not hasattr(args, "pdata"):
            return public.returnMsg(False,'参数错误')
        try:
            pdata = json.loads(args.pdata)
        except:
            return public.returnMsg(False, '参数格式错误')
        self.__PDATA['data'] = pdata
        result = self.request('apply_cert_install_pay')
        return result

    def check_ssl_method(self,get):
        """
        @name 检测ssl验证方式
        @domain string 域名
        """

        domain = get.domain
        if public.M('sites').where('id=?',(public.M('domain').where('name=?',(domain)).getField('pid'),)).getField('project_type') == 'Java':
            siteRunPath='{}/java_node_ssl'.format(public.M("config").getField("sites_path"))
        else:
            siteRunPath = self.get_domain_run_path(domain)

        if not siteRunPath:
            return public.returnMsg(False,'获取网站路径失败，请检查网站是否存在.')

        verify_path = siteRunPath + '/.well-known/pki-validation'
        if not os.path.exists(verify_path):
            public.rename_parent_file(verify_path)
            try:
                os.makedirs(verify_path)
            except:
                return public.returnMsg(False, '创建验证目录失败，请检测是否写入被拦截.')

        #生成临时文件
        check_val =  public.GetRandomString(16)
        verify_file = '{}/{}.txt'.format(verify_path,check_val)
        public.writeFile(verify_file,check_val)
        if not os.path.exists(verify_file):
            return public.returnMsg(False,'创建验证文件失败，请检测是否写入被拦截.')

        res = {}
        msg = [     '域名【{}】无法正确访问验证文件'.format(domain),
                    '可能的原因',
                    '1、未正确解析，或解析未生效 [请正确解析域名，或等待解析生效后重试]',
                    '2、检查是否有设置301/302重定向 [请暂时关闭重定向相关配置]',
                    '3、检查该网站是否已经开启反向代理 [请暂时关闭反向代理配置]'
                ]

        res['HTTP_CSR_HASH'] = msg
        res['HTTPS_CSR_HASH'] = msg

        #检测HTTP/https访问
        args = public.dict_obj()
        for stype in ['http','https']:
            args.url = '{}://{}/.well-known/pki-validation/{}.txt'.format(stype,domain,check_val)
            args.content = check_val
            if self.check_url_txt(args,2) == 1:
                res['{}_CSR_HASH'.format(stype).upper()] = 1

        #检测caa记录
        result = self.check_ssl_caa([domain])
        if not result:
            res['CNAME_CSR_HASH'] = 1
        else:
            res['CNAME_CSR_HASH'] = json.loads(result['data'])

        try:
            if os.path.exists(verify_file):
                os.remove(verify_file)
        except:pass
        return res

    @staticmethod
    def upload_cert_to_cloud(get):
        ssl_id = None
        ssl_hash = None
        try:
            if "ssl_id" in get:
                ssl_id = int(get.ssl_id)
            if "ssl_hash" in get:
                ssl_hash = get.ssl_hash.strip()
        except (ValueError, AttributeError, KeyError):
            return public.ReturnMsg(False, "参数错误")
        from ssl_manage import SSLManger
        try:
            return SSLManger().upload_cert(ssl_id, ssl_hash)
        except ValueError as e:
            return public.returnMsg(False, str(e))
        except Exception as e:
            return public.returnMsg(False, "操作错误：" + str(e))

    @staticmethod
    def remove_cloud_cert(get):
        ssl_id = None
        ssl_hash = None
        local = False
        force = False
        try:
            if "ssl_id" in get:
                ssl_id = int(get.ssl_id)
            if "ssl_hash" in get:
                ssl_hash = get.ssl_hash.strip()

            if "local" in get and get.local.strip() in ("1", 1, True, "true"):
                local = True
            # if "force" in get and get.force.strip() in ("1", 1, True, "true"):
            #     force = True

        except (ValueError, AttributeError, KeyError):
            return public.ReturnMsg(False, "参数错误")
        import acme_v2
        try:
            return acme_v2.acme_v2().delete_order(public.to_dict_obj({"ssl_hash": ssl_hash, "local": local, "force": force}))
        except ValueError as e:
            return public.returnMsg(False, str(e))
        except Exception as e:
            return public.returnMsg(False, "操作错误：" + str(e))

    # 未使用
    @staticmethod
    def refresh_cert_list(get=None):
        from ssl_manage import SSLManger
        try:
            return SSLManger().get_cert_list(force_refresh=True)
        except ValueError as e:
            return public.returnMsg(False, str(e))
        except Exception as e:
            return public.returnMsg(False, "操作错误：" + str(e))

    @staticmethod
    def get_cert_info(get):
        ssl_id = None
        ssl_hash = None
        try:
            if "ssl_id" in get:
                ssl_id = int(get.ssl_id)
            if "ssl_hash" in get:
                ssl_hash = get.ssl_hash.strip()
        except (ValueError, AttributeError, KeyError):
            return public.ReturnMsg(False, "参数错误")
        from ssl_manage import SSLManger
        try:
            ssl_mager = SSLManger()
            target = ssl_mager.find_ssl_info(ssl_id, ssl_hash)
            if target is None:
                return public.returnMsg(False, "未获取到证书信息")
            target.update(ssl_mager.get_cert_for_deploy(target["hash"]))
            return target
        except ValueError as e:
            return public.returnMsg(False, str(e))
        except Exception as e:
            return public.returnMsg(False, "操作错误：" + str(e))

    @staticmethod
    def get_cert_list(get):
        """
        search_limit 0 -> 所有证书
        search_limit 1 -> 没有过期的证书
        search_limit 2 -> 有效期小于等于15天的证书 但未过期
        search_limit 3 -> 过期的证书
        search_limit 4 -> 过期时间1年以上的证书
        """
        search_name = None
        search_limit = 0
        force_refresh = False
        reverse = False

        try:
            if "search_name" in get:
                search_name = get.search_name.strip()
            if "search_limit" in get:
                search_limit = int(get.search_limit.strip())
            if "force_refresh" in get and get.force_refresh.strip() in ("1", 1, "True", True):
                force_refresh = True
            if "reverse" in get and get.reverse.strip() in ("1", 1, "True", True):
                reverse = True

        except (ValueError, AttributeError, KeyError):
            return public.ReturnMsg(False, "参数错误")

        param = None
        if search_name is not None:
            param = ['subject LIKE ?', ["%{}%".format(search_name)]]

        now = datetime.datetime.now()
        filter_func = lambda x: True
        if search_limit == 1:
            date = now.strftime("%Y-%m-%d")
            filter_func = lambda x: x["not_after"] >= date
        elif search_limit == 2:
            date1 = now.strftime("%Y-%m-%d")
            date2 = (now + datetime.timedelta(days=15)).strftime("%Y-%m-%d")
            filter_func = lambda x:  date1 <= x["not_after"] <= date2
        elif search_limit == 3:
            date = now.strftime("%Y-%m-%d")
            filter_func = lambda x: x["not_after"] < date
        elif search_limit == 4:
            date = (now + datetime.timedelta(days=366)).strftime("%Y-%m-%d")
            filter_func = lambda x: x["not_after"] > date

        from ssl_manage import SSLManger
        try:
            res_list = SSLManger().get_cert_list(param=param, force_refresh=force_refresh)
            res_list = list(filter(filter_func, res_list))
            res_list.sort(key=lambda x: x["not_after"], reverse=reverse)
            return res_list
        except ValueError as e:
            return public.returnMsg(False, str(e))
        except Exception as e:
            return public.returnMsg(False, "操作错误：" + str(e))

    def set_ssl_ps(self, get):
        """设置SSL证书的备份说明"""
        from ssl_manage import SSLManger
        ssl_mager = SSLManger()
        ssl_id = get.get('id')
        ps = get.get('ps', '')
        result, message = SSLManger().update_ssl_ps(ssl_id, ps)
        if result:
            return public.ReturnMsg(True, message)
        else:
            return public.ReturnMsg(False, message)

    def get_ssl_ps(self, get):
        try:
            """获取SSL证书的备份说明"""
            from ssl_manage import SSLManger
            ssl_mager = SSLManger()
            ssl_id = get.get('id')
            result, ps = SSLManger().get_ssl_ps(ssl_id)
            data=[{"ps":ps}]
            if result:
                return public.ReturnMsg(True, data)
            else:
                return public.ReturnMsg(False, data)
        except:
            print(public.get_error_info())



       #发送请求
    def request(self,dname):
        self.__PDATA['data'] = json.dumps(self.__PDATA['data'])

        rquest_url = self.__APIURL2 + '/' + dname
        self.__request_url = public.get_home_node(rquest_url)

        msg = '接口请求失败（{}）'.format(self.__request_url)
        try:

            res = public.httpPost(rquest_url,self.__PDATA)
            if res == False:
                raise public.error_conn_cloud(msg)
        except Exception as ex:
            raise public.error_conn_cloud(str(ex))

        result = public.returnMsg(False, msg)
        try:
            result = json.loads(res)
        except:
            pass
        return result

    def request_v2(self,dname):
        self.__PDATA['data'] = json.dumps(self.__PDATA['data'])

        rquest_url = self.__APIURL3 + '/' + dname
        self.__request_url = public.get_home_node(rquest_url)

        msg = '接口请求失败（{}）'.format(self.__request_url)
        try:
            res = public.httpPost(rquest_url, self.__PDATA)
            if res == False:
                raise public.error_conn_cloud(msg)
        except Exception as ex:
            raise public.error_conn_cloud(str(ex))

        result = public.returnMsg(False, msg)
        try:
            result = json.loads(res.strip())
        except:
            pass
        return result

    """
    @name 统一请求接口
    @param url 返回URL不是www.bt.cn，修改config/config.json的home字段
    """
    def request_post(self,url,params):

        self.__request_url = public.get_home_node(url)
        msg = '接口请求失败（{}）'.format(self.__request_url)
        try:
            res = public.httpPost(url,params)
            if res == False:
                raise public.error_conn_cloud(msg)
        except Exception as ex:
            raise public.error_conn_cloud(str(ex))

        result = public.returnMsg(False,msg)
        try:
            result = json.loads(res.strip())
        except:pass
        return result


    # 转换时间
    def strf_date(self, sdate):
        return time.strftime('%Y-%m-%d', time.strptime(sdate, '%Y%m%d%H%M%S'))

    #转换时间
    def strfToTime(self,sdate):
        import time
        return time.strftime('%Y-%m-%d',time.strptime(sdate,'%b %d %H:%M:%S %Y %Z'))