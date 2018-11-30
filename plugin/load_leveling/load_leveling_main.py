#coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: 黄文良 <287962566@qq.com>
# +-------------------------------------------------------------------

import sys
sys.path.append('/www/server/panel/class');
import json,os,time,public,re

#+--------------------------------------------------------------------
#|   宝塔负载均衡
#+--------------------------------------------------------------------
class load_leveling_main:
    __nodes         = None;
    __loadLevelings = None;
    __confPath      = 'plugin/load_leveling/config.json';
    __emailPath     = 'plugin/load_leveling/email.json';
    __heartbeat     = 'plugin/load_leveling/heartbeat.json';
    __nginxConf     = 'vhost/nginx/';
    
    def __init__(self):
        
        pass;
    
    def get_loadleveling_list(self,get):
        if public.ExecShell('nginx -V 2>&1|grep /www/server/nginx/src/nginx-sticky-module')[0] == '': return public.returnMsg(False,'当前nginx不支持sticky插件,请重装nginx!');
        if not os.path.exists('/www/server/nginx/sbin/nginx'): return public.returnMsg(False,'本插件基于nginx，请先安装!');
        return self.__read_config();
    
    def cerate_loadleveling(self,get):
        upName = get.upname;
        if self.__get_leveling_info(upName): return public.returnMsg(False,'指定负载均衡已存在!');
        upExpires = int(get.upexpires);
        session_type = get.session_type;
        ps = get.ps;
        tmpNodes = json.loads(get.upnodes);
        domains = json.loads(get.domains);
        mainDomain = domains[0].split(':')[0]
        result = self.create_site(get);
        if 'status' in result: return result;
        site_id = result['id'];
        levelingInfo = {'name':upName,'pool':'http','site':mainDomain,'site_id': site_id,'ps':ps,'session_type':session_type,'expires':upExpires,'cookie_name':'bt_route','secure':False,'httponly':True,'time':int(time.time()),'nodes':tmpNodes}
        
        data = self.__read_config();
        data.append(levelingInfo);
        self.__write_config(data);
        self.__write_to_conf(upName);
        import panelSite
        s = panelSite.panelSite()
        
        get.name = mainDomain
        get.proxyUrl = 'http://' + upName;
        get.toDomain = '$host';
        get.sub1 = '';
        get.sub2 = '';
        get.type = '1';
        result = s.SetProxy(get);
        public.WriteLog('负载均衡','添加负载均衡['+upName+']' + str(result));
        return public.returnMsg(True,'添加成功!');
    
    #创建关联站点
    def create_site(self,get):
        domains = json.loads(get.domains);
        mainDomain = domains[0].split(':')
        if len(mainDomain) == 1: mainDomain.append('80');
        del(domains[0])
        get.webname = json.dumps({'domain': mainDomain[0],'domainlist':domains,'count':len(domains)});
        get.port = mainDomain[1]
        get.ftp = 'false';
        get.sql = 'false';
        get.version = '54';
        get.ps = '负载均衡['+get.upname+']的绑定站点';
        get.path = public.M('config').where("id=?",('1',)).getField('sites_path') + '/' + mainDomain[0];
        import panelSite
        s = panelSite.panelSite()
        result = s.AddSite(get);
        if 'status' in result: return result;
        result['id'] = public.M('sites').where('name=?',(mainDomain[0],)).getField('id');
        self.set_ssl_check(mainDomain[0])
        return result;
    
    #设置SSL验证目录过滤
    def set_ssl_check(self,siteName):
        rewriteConf = '''#一键申请SSL证书验证目录相关设置
location ~ \.well-known{
    allow all;
}'''
        public.writeFile('vhost/rewrite/' + siteName + '.conf',rewriteConf)
    
    #删除负载均衡
    def remove_loadleveling(self,get):
        upName = get.upname;
        upFile = self.__nginxConf + 'leveling_' + upName + '.conf';
        if os.path.exists(upFile): os.remove(upFile)
        data = self.__read_config()
        levelingList = []
        for d in data:
            if d['name'] == upName:
                if 'site_id' in d:
                    get.id = d['site_id'];
                    get.webname = d['site'];
                    import panelSite;
                    panelSite.panelSite().DeleteSite(get);
                continue;
            levelingList.append(d);
        self.__write_config(levelingList);
        public.WriteLog('负载均衡','删除负载均衡['+upName+']');
        return public.returnMsg(True,'删除成功!');
    
    #修改备注
    def modify_ps(self,get):
        upName = get.upname;
        data = self.__read_config();
        for i in range(len(data)):
            if data[i]['name'] != upName: continue;
            data[i]['ps'] = get.ps;
        self.__write_config(data);
        return public.returnMsg(True,'修改成功!');
    
    #修改cookie配置
    def modify_sticky_conf(self,get):
        upName = get.upname;
        expires = int(get.upexpires);
        cookie_name = get.cookie_name;
        session_type = get.session_type;
        secure = False
        if get.secure == '1': secure = True;
        httponly = False
        if get.httponly == '1': httponly = True;
        data = self.__read_config();
        for i in range(len(data)):
            if data[i]['name'] != upName: continue;
            data[i]['session_type'] = session_type;
            data[i]['expires'] = expires;
            data[i]['cookie_name'] = cookie_name;
            data[i]['secure'] = secure;
            data[i]['httponly'] = httponly;
        self.__write_config(data);
        self.__write_to_conf(upName);
        public.WriteLog('负载均衡','修改负载均衡配置['+upName+']');
        return public.returnMsg(True,'cookie设置成功!');
    
    #解析配置文件
    def encode_loadleveling_conf(self,upName):
        upFile = self.__nginxConf + 'leveling_' + upName + '.conf';
        upBody = public.readFile(upFile)
        levelingInfo = {}
        tmp = re.search('upstream\s+([^ .]+)\s*{',upBody)
        if not tmp: return False
        levelingInfo['name'] = tmp.groups()[0]
        
        ip_hash = upBody.find('#ip_hash')
        sticky = upBody.find('#sticky')
        if ip_hash != -1:
            levelingInfo['mode'] = 'ip_hash';
        elif sticky != -1:
            levelingInfo['mode'] = 'sticky';
        else:
            levelingInfo['mode'] = 'off';
        
        tmp = re.search('expires\s+(.+)h',upBody)
        if not tmp: return False
        levelingInfo['expires'] = tmp.groups()[0]
        
        httponly = False
        if upBody.find('httponly') != -1: httponly = True
        levelingInfo['httponly'] = httponly
        
        tmpNodes = re.findall('server.+',upBody)
        levelingInfo['nodes'] = []
        for node in tmpNodes:
            node = node.replace(';','')
            nodeTmp = node.split()
            serTmp = nodeTmp[1].split(':')
            tmp = {}
            tmp['server'] = serTmp[0];
            tmp['port'] = 80;
            if len(serTmp) > 1: tmp['port'] = int(serTmp[1])
            tmp['weight'] = 1;
            tmp['state'] = 1;
            if node.find('weight') != -1: 
                tmp['weight'] = int(nodeTmp[-1].split('=')[1])
            elif nodeTmp[-1] == 'down': 
                tmp['state'] = 0;
            elif nodeTmp[-1] == 'backup':
                tmp['state'] = 2;
            levelingInfo['nodes'].append(tmp);
        return levelingInfo;
    
    
    #hash-ip/sticky/off
    def set_session_type(self,get):
        session_type = get.session_type;
        upName = get.upname;
        data = self.__read_config();
        for i in range(len(data)):
            if data[i]['name'] != upName: continue;
            data[i]['session_type'] = get.session_type;
        self.__write_config(data);
        self.__write_to_conf(upName);
        public.WriteLog('负载均衡','修改负载均衡['+upName+']的会话模式为[' + session_type + ']');
        return public.returnMsg(True,'负载均衡模式设置成功!');
    
    #添加节点
    def add_node(self,get):
        upName = get.upname;
        node = {}
        node['server'] = get.server;
        node['port'] = int(get.port)
        node['state'] = int(get.state)
        node['weight'] = int(get.weight)
        node['max_fails'] = int(get.max_fails)
        node['fail_timeout'] = int(get.fail_timeout)
        node['addtime'] = int(get.addtime)
        data = self.__read_config()
        for i in range(len(data)):
            if data[i]['name'] != upName: continue;
            for n in  data[i]['nodes']:
                if n['server'] == node['server'] and n['port'] == node['port']: return public.returnMsg(False,'指定节点已存在!');
            data[i]['nodes'].append(node);
        self.__write_config(data);
        self.__write_to_conf(upName);
        public.WriteLog('负载均衡','添加节点['+node['server'] + ':' + str(node['port']) + ']到负载均衡['+upName+']');
        return public.returnMsg(True,'节点添加成功!');
            
    #删除节点
    def remove_node(self,get):
        upName = get.upname;
        data = self.__read_config();
        for i in range(len(data)):
            if data[i]['name'] != upName: continue;
            nodes = []
            for n in  data[i]['nodes']:
                if n['server'] == get['server'] and n['port'] == int(get['port']): continue;
                nodes.append(n);
            data[i]['nodes'] = nodes;
        self.__write_config(data);
        self.__write_to_conf(upName);
        public.WriteLog('负载均衡','从负载均衡['+upName+']删除节点['+get['server'] + ':' + get['port'] + ']');
        return public.returnMsg(True,'节点删除成功!');
    
    #修改节点状态
    def modify_node_state(self,get):
        upName = get.upname;
        data = self.__read_config();
        get.port  = int(get.port);
        for i in range(len(data)):
            if data[i]['name'] != upName: continue;
            for n in  range(len(data[i]['nodes'])):
                if data[i]['nodes'][n]['server'] != get.server or data[i]['nodes'][n]['port'] != get.port: continue;
                data[i]['nodes'][n]['state'] = int(get.state)
        self.__write_config(data);
        self.__write_to_conf(upName);
        public.WriteLog('负载均衡','修改负载均衡['+upName+']下的节点['+get['server'] + ':' + get['port'] + ']状态 => ' + get.state);
        return public.returnMsg(True,'节点状态修改成功!');
    
    #修改节点权重
    def modify_node(self,get):
        upName = get.upname;
        data = self.__read_config();
        
        for i in range(len(data)):
            if data[i]['name'] != upName: continue;
            for n in  range(len(data[i]['nodes'])):
                if data[i]['nodes'][n]['server'] != get['server'] or data[i]['nodes'][n]['port'] != int(get['port']): continue;
                data[i]['nodes'][n]['weight'] = int(get['weight']);
                data[i]['nodes'][n]['state'] = int(get['state']);
                data[i]['nodes'][n]['max_fails'] = int(get['max_fails']);
                data[i]['nodes'][n]['fail_timeout'] = int(get['fail_timeout']);
                    
        self.__write_config(data);
        self.__write_to_conf(upName);
        public.WriteLog('负载均衡','修改负载均衡['+upName+']下的节点配置:' + get.server + ':' + get.port);
        return public.returnMsg(True,'节点配置已修改!');
    
    #取指定节点列表
    def get_node_list(self,get):
        upName = get.upname
        levelingInfo = self.__get_leveling_info(upName)
        heartbeat = self.get_heartbeat_conf(None);
        for i in range(len(levelingInfo['nodes'])):
            url = 'http://' + levelingInfo['nodes'][i]['server'].strip() + ':' + str(levelingInfo['nodes'][i]['port']) + heartbeat['path'];
            levelingInfo['nodes'][i]['check'] = self.__http_get(url);
            levelingInfo['nodes'][i]['url'] = url;
        return levelingInfo['nodes'];
    
    #取所有节点列表
    def get_node_list_all(self,get):
        data = self.__read_config()
        nodeList = []
        for d in data:
            for n in d['nodes']:
                n['leveling'] = d['name'];
                nodeList.append(n);
        return nodeList
    
    #获取邮箱列表
    def get_email_list(self,get):
        if not os.path.exists(self.__emailPath): public.writeFile(self.__emailPath,'[]');
        emails = public.readFile(self.__emailPath);
        data = {}
        data['emails'] = json.loads(emails);
        data['heartbeat'] = self.get_heartbeat_conf(get);
        return data;
    
    #添加邮箱地址
    def add_email(self,get):
        emails = self.get_email_list(get)['emails'];
        if len(emails) > 2: return public.returnMsg(False,'最多添加3个收件地址!');
        if get.email in emails: return public.returnMsg(False,'指定收件地址已存在!');
        emails.append(get.email)
        public.WriteLog('负载均衡','添加收件地址[' + get.email + ']');
        self.__write_mail_conf(emails);
        return public.returnMsg(True,'添加成功');
    
    #删除邮箱地址
    def remove_email(self,get):
        emails = self.get_email_list(get)['emails'];
        data = []
        for email in emails:
            if email == get.email: continue;
            data.append(email);
        public.WriteLog('负载均衡','删除收件地址[' + get.email + ']');
        self.__write_mail_conf(data);
        return public.returnMsg(True,'删除成功');
        
    #获取日志
    def get_logs(self,get):
        import page
        page = page.Page();
        count = public.M('logs').where('type=?',(u'负载均衡',)).count();
        limit = 12;
        info = {}
        info['count'] = count
        info['row']   = limit
        info['p'] = 1
        if hasattr(get,'p'):
            info['p']    = int(get['p'])
        info['uri']      = get
        info['return_js'] = ''
        if hasattr(get,'tojs'):
            info['return_js']   = get.tojs
        
        data = {}
        
        #获取分页数据
        data['page'] = page.GetPage(info,'1,2,3,4,5,8');
        data['data'] = public.M('logs').where('type=?',(u'负载均衡',)).order('id desc').limit(bytes(page.SHIFT)+','+bytes(page.ROW)).field('log,addtime').select();
        return data;
    
    #写邮箱配置
    def __write_mail_conf(self,data):
        return public.writeFile(self.__emailPath,json.dumps(data));
    
    def get_leveling_info(self,get):
        return self.__get_leveling_info(get.upname);
    
    #取指定负载均衡信息
    def __get_leveling_info(self,upName):
        data = self.__read_config()
        for d in data:
            if d['name'] == upName: return d;
        return None
    
    #获取心跳包设置
    def get_heartbeat_conf(self,get):
        if not os.path.exists(self.__heartbeat): public.writeFile(self.__heartbeat,'{"path":"/","time":30,"warning":3,"last_time":'+str(time.time())+'}');
        upBody = public.readFile(self.__heartbeat);
        data = json.loads(upBody);
        data['open'] = id = public.M('crontab').where('name=?',(u'负载均衡节点心跳检测任务',)).getField('id');
        return data;
    
    #修改心跳包设置
    def modify_heartbeat_conf(self,get):
        heartbeat = self.get_heartbeat_conf(get);
        heartbeat['path'] = get.hpath;
        heartbeat['time'] = int(get.htime);
        heartbeat['warning'] = get.hwarning;
        public.writeFile(self.__heartbeat,json.dumps(heartbeat));
        
        id = public.M('crontab').where('name=?',(u'负载均衡节点心跳检测任务',)).getField('id');
        import crontab
        if id: crontab.crontab().DelCrontab({'id':id})
        data = {}
        data['name'] = '负载均衡节点心跳检测任务'
        data['type'] = 'minute-n'
        data['where1'] = get.htime
        data['sBody'] = 'python /www/server/panel/plugin/load_leveling/load_leveling_main.py'
        data['backupTo'] = 'localhost'
        data['sType'] = 'toShell'
        data['hour'] = ''
        data['minute'] = ''
        data['week'] = ''
        data['sName'] = ''
        data['urladdress'] = ''
        data['save'] = ''
        crontab.crontab().AddCrontab(data)
        public.WriteLog('负载均衡','修改心跳包检测配置');
        return public.returnMsg(True,'设置成功!');
    
    #关闭心跳包
    def heartbeat_off(self,get):
        id = public.M('crontab').where('name=?',(u'负载均衡节点心跳检测任务',)).getField('id');
        import crontab
        if id: crontab.crontab().DelCrontab({'id':id})
        return public.returnMsg(True,'已关闭任务');
    
    #读配置
    def __read_config(self):
        if not os.path.exists(self.__confPath): public.writeFile(self.__confPath,'[]');
        upBody = public.readFile(self.__confPath);
        return json.loads(upBody);
    
    #写配置
    def __write_config(self,data):
        return public.writeFile(self.__confPath,json.dumps(data));
    
    #将规则写到配置文件
    def __write_to_conf(self,upName):
        levelingInfo = self.__get_leveling_info(upName)
        upFile = self.__nginxConf + 'leveling_' + upName + '.conf';
        httponly = ''
        if levelingInfo['httponly']: httponly = ' httponly';
        
        secure = ''
        if levelingInfo['secure']: secure = ' secure';
        
        modes = {'ip_hash':['ip_hash','#sticky'],'sticky':['#ip_hash','sticky'],'off':['#ip_hash','#sticky']};
        ip_hash = modes[levelingInfo['session_type']][0]
        sticky = modes[levelingInfo['session_type']][1]
        
        upNodes = '';
        for node in levelingInfo['nodes']:
            states = ['down','weight=' + str(node['weight']),'backup']
            upNodes += '    server ' + node['server'].strip() + ':' + str(node['port']) + ' max_fails=' + str(node['max_fails']) + ' fail_timeout=' + str(node['fail_timeout']) + 's ' +  states[node['state']]+";\n";
        
        upBody = '''upstream %s {
    %s;
%s
    %s name=%s expires=%sh%s%s;
}''' % (upName,ip_hash,upNodes,sticky,levelingInfo['cookie_name'],levelingInfo['expires'],httponly,secure)
        public.writeFile(upFile,upBody)
        public.serviceReload();
        return True
    
    #检查节点是否存在
    def __check_node_exists(self,name,node,port):
        data = self.__read_config();
        for d in data:
            if d['name'] != name: continue
            for n in d['nodes']:
                if n['server'] != node:continue;
                if n['port'] == port: return True
        return False;
    
    
    #检测节点
    def _check_node(self):
        data = self.__read_config()
        emails = self.get_email_list(None)['emails'];
        heartbeat = self.get_heartbeat_conf(None);
        warningUrl = 'http://www.bt.cn/api/index/sendWarningMessage'
        successUrl = 'http://www.bt.cn/api/index/sendSuccessMessage'
        for i in range(len(data)):
            for n in range(len(data[i]['nodes'])):
                node = data[i]['nodes'][n];
                nerror = True
                if 'error' in node:  nerror = node['error'];
                urlstr = 'http://' + node['server'].strip() + ':' + str(node['port']) + heartbeat['path'];
                status = self.__http_get(urlstr)
                nodestr = node['server'] + ':' + str(node['port']);
                data[i]['nodes'][n]['error'] = status
                if not status: 
                    self.__send_mail(warningUrl, emails, nodestr, data[i]['name']);
                if status and not nerror: 
                    self.__send_mail(successUrl, emails, nodestr, data[i]['name']);
        self.__write_config(data)
                
    def __send_mail(self,url,emails,node,name):
        for email in emails:
            if not email: continue;
            print(public.httpGet(url+'?email='+email+'&node='+node+'&name='+name));
    
    #发送检测请求
    def __http_get(self,url):
        try:
            if sys.version_info[0] == 2:
                import urllib2;
                rec = urllib2.urlopen(url,timeout=3)
            else:
                import urllib.request
                rec = urllib.request.urlopen(url,timeout=3)
            status = [200,301,302,404,403]
            if rec.getcode() in status: return True
            return False
        except:
            return False

if __name__ == '__main__':
    p = load_leveling_main();
    p._check_node();
                
                
                
    
