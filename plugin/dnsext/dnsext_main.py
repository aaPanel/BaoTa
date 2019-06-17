#coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板 x3
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2017 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: 黄文良 <287962566@qq.com>
# +-------------------------------------------------------------------

#+--------------------------------------------------------------------
#|   DNS云解析
#+--------------------------------------------------------------------
import sys;
if sys.version_info[0] == 2:
    reload(sys)
    sys.setdefaultencoding('utf-8')
sys.path.append('/www/server/panel/class/');
import public,json,os,time,binascii,urllib,re;
class dns_main:
    __PDATA = None;
    __APIURL = 'http://www.bt.cn/api/Dns';
    __UPATH = 'data/userInfo.json';
    __userInfo = None;
    def __init__(self):
        pdata = {}
        data = {}
        if os.path.exists(self.__UPATH):
            self.__userInfo = json.loads(public.readFile(self.__UPATH));
            if self.__userInfo:
                pdata['access_key'] = self.__userInfo['access_key'];
                data['secret_key'] = self.__userInfo['secret_key'];
        else:
            pdata['access_key'] = 'test';
            data['secret_key'] = '123456';
        pdata['data'] = data;
        self.__PDATA = pdata;
   
    #发送到服务器
    def send_server(self,action):
        if self.__PDATA['access_key'] == 'test': return public.returnMsg(False,'请先绑定宝塔用户!');
        data = self.__PDATA['data'] 
        self.__PDATA['data'] = self.De_Code(self.__PDATA['data']);
        result = public.httpPost(self.__APIURL + '/' + action,self.__PDATA);
        self.__PDATA['data'] = data
        #public.writeFile('/tmp/1.txt',result)
        return json.loads(result);


    #-----新增 ----------
    #获取IP
    def get_ip(self,get):
        ip = public.GetLocalIp();
        return {'ip':ip, 'msg': 'ok'};

    def get_server(self,get):
        data = public.M('domain').field('id,name').order('id desc').select();
        result = [];
        host = "";
        domain = get.domain
        for d in data: 
            if domain in d['name']: 
                if d['name'] == domain:
                    host = "@"
                else :
                    host = d['name'].rsplit("."+domain)[0];
                result.append(host);
        ip = public.GetLocalIp();
        return {'server': result, 'ip': ip, 'domain': domain, 'data': data};

    def auto_dns(self, get):
        ip = public.GetLocalIp();
        domain = get.domain;
        domainId = get.domainId;
        results = []
        hosts = []
        status = True
        data = public.M('domain').field('id,name').order('id desc').select();
        for d in data: 
            if domain in d['name']:
                if domain == d['name']:
                    host = "@"
                else :
                    host = d['name'].rsplit("."+domain)[0];
                self.__PDATA['domainId'] = domainId;
                self.__PDATA['type'] = "A";
                self.__PDATA['viewId'] = "0";
                self.__PDATA['host'] = host;
                self.__PDATA['value'] = ip;
                self.__PDATA['ttl'] = 600;
                self.__PDATA['mx'] = 0;
                self.__PDATA['remark'] = "";
                result = self.send_server('AddRecord');
                status = status & result['status']
                results.append(host + "&nbsp;&nbsp;" + result['msg'] + "<br />")
        return {'results': results, 'status': status}


    #-----新增 END ----------

   
    #获取域名列表
    def get_domains(self,get):
        if not hasattr(get,'p'): get.p = '1';
        query = ''
        if hasattr(get,'query'): query = '&query='+get.query;
        data =  self.send_server('GetDomainList?limit=10&tojs=Domains.DomainListRequest&p='+get.p+query);
        return data;
    
    #创建域名
    def create_domain(self,get):
        self.__PDATA['domain'] = get.domain;
        return self.send_server('CreateDomain');
    
    #删除域名
    def remove_domain(self,get):
        self.__PDATA['domain'] = get.domain;
        return self.send_server('RemoveDomain');
    
    #锁定域名
    def lock_domain(self,get):
        self.__PDATA['domain'] = get.domain;
        return self.send_server('LockDomain');
    
    #解锁域名
    def unlock_domain(self,get):
        self.__PDATA['domain'] = get.domain;
        return self.send_server('UnlockDomain');
    
    #暂停域名
    def pause_domain(self,get):
        self.__PDATA['domain'] = get.domain;
        return self.send_server('PauseDomain');
    
    #启用域名
    def start_domain(self,get):
        self.__PDATA['domain'] = get.domain;
        return self.send_server('StartDomain');
    
    #修改域名备注
    def set_domain_ps(self,get):
        self.__PDATA['domain'] = get.domain;
        self.__PDATA['ps'] = get.ps;
        return self.send_server('SetDomainPs');
    
    #获取域名默认NS信息
    def get_domain_ns(self,get):
        self.__PDATA['domain'] = get.domain;
        return self.send_server('GetDomainNs');
    
    #获取域名操作日志
    def get_domain_logs(self,get):
        self.__PDATA['domainId'] = get.domainId;
        if not hasattr(get,'p'): get.p = '1';
        data =  self.send_server('GetDomainLog?limit=10&tojs=Domains.LogsListRequest&p='+get.p);
        return data;
    
    #获取实时QPS
    def get_qps_hour(self,get):
        self.__PDATA['domainId'] = get.domainId;
        data = self.send_server('GetQpsHour');
        return sorted(data.items(),key=lambda item:item[0]);
    
    #获取天 QPS
    def get_qps_day(self,get):
        self.__PDATA['domainId'] = get.domainId;
        data = self.send_server('GetQpsDay');
        return sorted(data.items(),key=lambda item:item[0]);
    
    #获取月 QPS
    def get_qps_year(self,get):
        self.__PDATA['domainId'] = get.domainId;
        data = self.send_server('GetQpsYear');
        return sorted(data.items(),key=lambda item:item[0]);
    
    #获取记录列表
    def get_record_list(self,get):
        self.__PDATA['domainId'] = get.domainId;
        if not hasattr(get,'p'): get.p = '1';
        query = ''
        if hasattr(get,'query'): query = '&query='+get.query;
        data =  self.send_server('GetRecordList?limit=10&tojs=Domains.AnalysisListRequest&p='+get.p + query);
        return data;
    
    #添加解析记录
    def create_record(self,get):
        self.__PDATA['domainId'] = get.domainId;
        self.__PDATA['type'] = get.type;
        self.__PDATA['viewId'] = get.viewId;
        self.__PDATA['host'] = get.host;
        self.__PDATA['value'] = get.value;
        self.__PDATA['ttl'] = get.ttl;
        self.__PDATA['mx'] = get.mx;
        self.__PDATA['remark'] = get.remark;
        return self.send_server('AddRecord');
    
    #添加高级解析记录
    def create_senior_record(self,get):
        self.__PDATA['domainId'] = get.domainId;
        self.__PDATA['type'] = get.type;
        self.__PDATA['viewId'] = get.viewId;
        self.__PDATA['host'] = get.host;
        self.__PDATA['value'] = get.value;
        self.__PDATA['ttl'] = get.ttl;
        self.__PDATA['mx'] = get.mx;
        self.__PDATA['remark'] = get.remark;
        self.__PDATA['ispId'] = get.ispId;
        self.__PDATA['areaId'] = get.areaId;
        return self.send_server('AddSeniorRecord');
    
    
    #删除解析记录
    def remove_record(self,get):
        self.__PDATA['domainId'] = get.domainId;
        self.__PDATA['recordId'] = get.recordId;
        return self.send_server('RemoveRecord');
    
    #暂停记录
    def pause_record(self,get):
        self.__PDATA['domainId'] = get.domainId;
        self.__PDATA['recordId'] = get.recordId;
        return self.send_server('PauseRecord');
    
    #启用记录
    def start_record(self,get):
        self.__PDATA['domainId'] = get.domainId;
        self.__PDATA['recordId'] = get.recordId;
        return self.send_server('StartRecord');
    
    #编辑记录
    def modify_record(self,get):
        self.__PDATA['domainId'] = get.domainId;
        self.__PDATA['recordId'] = get.recordId;
        if hasattr(get,'type'): self.__PDATA['type'] = get.type;
        if hasattr(get,'viewId'): self.__PDATA['viewId'] = get.viewId;
        if hasattr(get,'host'): self.__PDATA['host'] = get.host;
        if hasattr(get,'value'): self.__PDATA['value'] = get.value;
        if hasattr(get,'ttl'): self.__PDATA['ttl'] = get.ttl;
        if hasattr(get,'mx'): self.__PDATA['mx'] = get.mx;
        if hasattr(get,'remark'): self.__PDATA['remark'] = get.remark;
        return self.send_server('ModifyRecord');
    
    #编辑高级记录
    def modify_senior_record(self,get):
        self.__PDATA['domainId'] = get.domainId;
        self.__PDATA['recordId'] = get.recordId;
        if hasattr(get,'type'): self.__PDATA['type'] = get.type;
        if hasattr(get,'viewId'): self.__PDATA['viewId'] = get.viewId;
        if hasattr(get,'host'): self.__PDATA['host'] = get.host;
        if hasattr(get,'value'): self.__PDATA['value'] = get.value;
        if hasattr(get,'ttl'): self.__PDATA['ttl'] = get.ttl;
        if hasattr(get,'mx'): self.__PDATA['mx'] = get.mx;
        if hasattr(get,'remark'): self.__PDATA['remark'] = get.remark;
        if hasattr(get,'ispId'): self.__PDATA['ispId'] = get.ispId;
        if hasattr(get,'areaId'): self.__PDATA['areaId'] = get.areaId;
        return self.send_server('SeniormodifyRecord');
    
    #获取whois信息
    def get_domain_ns(self,get):
        try:
            import whois
            data = whois.whois(get.domain.strip())
            if not data: return public.returnMsg(False,'获取NS信息失败!');
            result = [];
            for d in data['name_servers']: result.append(d.strip().lower());
            return result
        except:
            return ['ns1.dns.com','ns2.dns.com'];
    
    #获取服务套餐列表
    def get_server_list(self,get):
        return self.send_server('GetServerList');
    
    #获取默认区域线路ID列表
    def get_areaview_list(self,get):
        return self.send_server('AreaviewList');
        
    #获取默认ISP线路ID列表
    def get_ispview_list(self,get):
        return self.send_server('IspviewList');
    
    #通过IP获取线路
    def get_ip_dist(self,get):
        return self.send_server('IpDist');
    
    #服务套餐NS查询
    def get_service_list(self,get):
        return self.send_server('GetServiceList');
    
    #加密数据
    def De_Code(self,data):
        if sys.version_info[0] == 2:
            pdata = urllib.urlencode(data);
        else:
            #import urllib.parse
            pdata = urllib.parse.urlencode(data);
            if type(pdata) == str: pdata = pdata.encode('utf-8')
        return binascii.hexlify(pdata);
    
    #解密数据
    def En_Code(self,data):
        if sys.version_info[0] == 2:
            result = urllib.unquote(binascii.unhexlify(data));
        else:
            #import urllib.parse
            if type(data) == str: data = data.encode('utf-8')
            tmp = binascii.unhexlify(data)
            if type(tmp) != str: tmp = tmp.decode('utf-8')
            result = urllib.parse.unquote(tmp)

        if type(result) != str: result = result.decode('utf-8')
        return json.loads(result);

    #获取域名标识
    def get_domainid(self,domain):
        get = dict_obj()
        get.query = domain
        data = self.get_domains(get)
        if len(data['data']) < 1: return False
        for dm in data['data']:
            if dm['domain'] == domain: return dm['domainId']
        return False

    #获取解析记录标识
    def get_recordid(self,domainId,key):
        get = dict_obj()
        get.domainId = domainId
        get.query = key
        data = self.get_record_list(get)
        if len(data['data']) < 1: return False
        for dm in data['data']:
            if dm['record_host'] == key: return dm['recordId']
        return False

    #匹配域名标识
    def get_domainid_byfull(self,fulldomain):
        domainItem = fulldomain.split('.')
        domainPx = ""
        domainId = False
        exts  = ['com.cn','org.cn','gov.cn','net.cn','com','cn','top']
        for dm in domainItem:
            domainPx += dm + '.'
            domain = fulldomain.replace(domainPx,'')
            if domain in exts: break
            if domain.find('.') == -1: break
            self.__init__()
            domainId = self.get_domainid(domain)
            if domainId: break
        return domainId,domainPx[:-1]

    #添加TXT记录
    def add_txt(self,fulldomain,value):
        get = dict_obj()
        domainId,key = self.get_domainid_byfull(fulldomain)
        if not domainId: return str(False)
        get.domainId = domainId
        get.type='TXT'
        get.viewId= ''
        get.host = key
        get.value = value
        get.ttl = '600'
        get.mx = '' 
        get.remark = u'申请SSL自动验证TXT记录'
        self.__init__()
        result = self.create_record(get)
        return str(result['status'])

    #删除TXT记录
    def remove_txt(self,fulldomain):
        get = dict_obj()
        get.domainId,key = self.get_domainid_byfull(fulldomain)
        if not get.domainId: return str(False)
        self.__init__()
        get.recordId = self.get_recordid(get.domainId,key)
        if not get.recordId: return str(False)
        self.__init__()
        result = self.remove_record(get)
        return str(result['status'])



class dict_obj:
    def __contains__(self, key):
        return getattr(self,key,None)
    def __setitem__(self, key, value): setattr(self,key,value)
    def __getitem__(self, key): return getattr(self,key,None)
    def __delitem__(self,key): delattr(self,key)
    def __delattr__(self, key): delattr(self,key)
    def get_items(self): return self


if __name__ == '__main__':
    os.chdir('/www/server/panel')
    q = dns_main()
    if sys.argv[1] == 'add_txt':
        print(q.add_txt(sys.argv[2],sys.argv[3]))
    elif sys.argv[1] == 'remove_txt':
        print(q.remove_txt(sys.argv[2]))
    else:
        print('args error')
