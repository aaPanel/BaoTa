#coding: utf-8
#-------------------------------------------------------------------
# 宝塔Linux面板
#-------------------------------------------------------------------
# Copyright (c) 2015-2016 宝塔软件(http:#bt.cn) All rights reserved.
#-------------------------------------------------------------------
# Author: hwliang <hwl@bt.cn>
#-------------------------------------------------------------------

#------------------------------
# SSL接口
#------------------------------
import public,os,sys,binascii,urllib,json,time,datetime
from BTPanel import cache,session
class panelSSL:
    __APIURL = 'http://www.bt.cn/api/Auth'
    __UPATH = 'data/userInfo.json'
    __userInfo = None
    __PDATA = None
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
        pdata = {}
        pdata['data'] = self.De_Code(data)
        try:
            rtmp = public.httpPost(self.__APIURL+'/GetToken',pdata)
            result = json.loads(rtmp)
            result['data'] = self.En_Code(result['data'])
            if result['data']: public.writeFile(self.__UPATH,json.dumps(result['data']))
            del(result['data'])
            session['focre_cloud'] = True
            return result
        except Exception as ex:
            return public.returnMsg(False,'连接服务器失败!<br>' + str(rtmp))
    
    #删除Token
    def DelToken(self,get):
        public.ExecShell("rm -f " + self.__UPATH)
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
    
    #获取订单列表
    def GetOrderList(self,get):
        if hasattr(get,'siteName'):
            path =   '/etc/letsencrypt/live/'+ get.siteName + '/partnerOrderId'
            if os.path.exists(path):
                self.__PDATA['data']['partnerOrderId'] = public.readFile(path)
            else:
                path = '/www/server/panel/vhost/cert/' + get.siteName + '/partnerOrderId'
                if os.path.exists(path):
                    self.__PDATA['data']['partnerOrderId'] = public.readFile(path)

        self.__PDATA['data'] = self.De_Code(self.__PDATA['data'])
        rs = public.httpPost(self.__APIURL + '/GetSSLList',self.__PDATA)
        try:
            result = json.loads(rs)
        except: return public.returnMsg(False,'获取失败，请稍候重试!')

        result['data'] = self.En_Code(result['data'])
        for i in range(len(result['data'])):
            result['data'][i]['endtime'] =   self.add_months(result['data'][i]['createTime'],result['data'][i]['validityPeriod'])
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
        
        if get.domain[:4] == 'www.':
            if not public.M('domain').where('name=?',(get.domain[4:],)).count():
                return public.returnMsg(False,"申请[%s]证书需要验证[%s]请将[%s]绑定并解析到站点!" % (get.domain,get.domain[4:],get.domain[4:]))

        runPath = self.GetRunPath(get)
        if runPath != False and runPath != '/': get.path +=  runPath
        authfile = get.path + '/.well-known/pki-validation/fileauth.txt'
        if not self.CheckDomain(get):
            if not os.path.exists(authfile): return public.returnMsg(False,'无法创建['+authfile+']')
        
        action = 'GetDVSSL'
        if hasattr(get,'partnerOrderId'):
            self.__PDATA['data']['partnerOrderId'] = get.partnerOrderId
            action = 'ReDVSSL'
        
        self.__PDATA['data']['domain'] = get.domain
        self.__PDATA['data'] = self.De_Code(self.__PDATA['data'])
        result = public.httpPost(self.__APIURL + '/' + action,self.__PDATA)
        try:
            result = json.loads(result)
        except: return result
        result['data'] = self.En_Code(result['data'])
        if hasattr(result['data'],'authValue'):
            public.writeFile(authfile,result['data']['authValue'])
        
        return result
    
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
            epass = public.GetRandomString(32)
            spath = get.path + '/.well-known/pki-validation'
            if not os.path.exists(spath): public.ExecShell("mkdir -p '" + spath + "'")
            public.writeFile(spath + '/fileauth.txt',epass)
            result = public.httpGet('http://' + get.domain + '/.well-known/pki-validation/fileauth.txt')
            if result == epass: return True
            return False
        except:
            return False
    
    #确认域名
    def Completed(self,get):
        self.__PDATA['data']['partnerOrderId'] = get.partnerOrderId
        self.__PDATA['data'] = self.De_Code(self.__PDATA['data'])
        if hasattr(get,'siteName'):
            get.path = public.M('sites').where('name=?',(get.siteName,)).getField('path')
            runPath = self.GetRunPath(get)
            if runPath != False and runPath != '/': get.path +=  runPath
            tmp = public.httpPost(self.__APIURL + '/SyncOrder',self.__PDATA)
            try:
                sslInfo = json.loads(tmp)
            except:
                return public.returnMsg(False,tmp)

            sslInfo['data'] = self.En_Code(sslInfo['data'])
            try:
                spath = get.path + '/.well-known/pki-validation'
                if not os.path.exists(spath): public.ExecShell("mkdir -p '" + spath + "'")
                public.writeFile(spath + '/fileauth.txt',sslInfo['data']['authValue'])
            except:
                return public.returnMsg(False,'SSL_CHECK_WRITE_ERR')
        try:
            result = json.loads(public.httpPost(self.__APIURL + '/Completed',self.__PDATA))
        except:
            result = public.returnMsg(True,'检测中..')
        n = 0
        my_ok = False
        while True:
            if n > 5: break
            time.sleep(5)
            rRet = json.loads(public.httpPost(self.__APIURL + '/SyncOrder',self.__PDATA))
            n +=1
            rRet['data'] = self.En_Code(rRet['data'])
            try:
                if rRet['data']['stateCode'] == 'COMPLETED': 
                    my_ok = True
                    break
            except: return public.get_error_info()
        if not my_ok: return result
        return rRet
    
    #同步指定订单
    def SyncOrder(self,get):
        self.__PDATA['data']['partnerOrderId'] = get.partnerOrderId
        self.__PDATA['data'] = self.De_Code(self.__PDATA['data'])
        result = json.loads(public.httpPost(self.__APIURL + '/SyncOrder',self.__PDATA))
        result['data'] = self.En_Code(result['data'])
        return result
    
    #获取证书
    def GetSSLInfo(self,get):
        self.__PDATA['data']['partnerOrderId'] = get.partnerOrderId
        self.__PDATA['data'] = self.De_Code(self.__PDATA['data'])
        time.sleep(3)
        result = json.loads(public.httpPost(self.__APIURL + '/GetSSLInfo',self.__PDATA))
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
                
                public.writeFile(keypath,result['data']['privateKey'])
                public.writeFile(csrpath,result['data']['cert']+result['data']['certCa'])
                public.writeFile(pidpath,get.partnerOrderId)
                import panelSite
                panelSite.panelSite().SetSSLConf(get)
                public.serviceReload()
                return public.returnMsg(True,'SET_SUCCESS')
            except:
                return public.returnMsg(False,'SET_ERROR')
        result['data'] = self.En_Code(result['data'])
        return result
    
    #部署证书夹证书
    def SetCertToSite(self,get):
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
            
            public.writeFile(keypath,result['privkey'])
            public.writeFile(csrpath,result['fullchain'])
            import panelSite
            panelSite.panelSite().SetSSLConf(get)
            public.serviceReload()
            return public.returnMsg(True,'SET_SUCCESS')
        except Exception as ex:
            return public.returnMsg(False,'SET_ERROR,' + public.get_error_info())
    
    #获取证书列表
    def GetCertList(self,get):
        try:
            vpath = '/www/server/panel/vhost/ssl'
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
            if not certInfo: return public.returnMsg(False,'证书解析失败!')
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
        vpath = os.path.join('/www/server/panel/vhost/ssl' , get.certName.replace("*.",''))
        if not os.path.exists(vpath): return public.returnMsg(False,'证书不存在!')
        data = {}
        data['privkey'] = public.readFile(vpath + '/privkey.pem')
        data['fullchain'] = public.readFile(vpath + '/fullchain.pem')
        return data
    
    #获取证书名称
    def GetCertName(self,get):            
        try:
            openssl = '/usr/local/openssl/bin/openssl'
            if not os.path.exists(openssl): openssl = 'openssl'
            result = public.ExecShell(openssl + " x509 -in "+get.certPath+" -noout -subject -enddate -startdate -issuer")
            tmp = result[0].split("\n")
            data = {}
            data['subject'] = tmp[0].split('=')[-1]
            data['notAfter'] = self.strfToTime(tmp[1].split('=')[1])
            data['notBefore'] = self.strfToTime(tmp[2].split('=')[1])
            if tmp[3].find('O=') == -1:
                data['issuer'] = tmp[3].split('CN=')[-1]
            else:
                data['issuer'] = tmp[3].split('O=')[-1].split(',')[0]
            if data['issuer'].find('/') != -1: data['issuer'] = data['issuer'].split('/')[0]
            result = public.ExecShell(openssl + " x509 -in "+get.certPath+" -noout -text|grep DNS")
            data['dns'] = result[0].replace('DNS:','').replace(' ','').strip().split(',')
            return data
        except:
            print(public.get_error_info())
            return None
    
    #转换时间
    def strfToTime(self,sdate):
        import time
        return time.strftime('%Y-%m-%d',time.strptime(sdate,'%b %d %H:%M:%S %Y %Z'))
        
    
    #获取产品列表
    def GetSSLProduct(self,get):
        self.__PDATA['data'] = self.De_Code(self.__PDATA['data'])
        result = json.loads(public.httpPost(self.__APIURL + '/GetSSLProduct',self.__PDATA))
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
