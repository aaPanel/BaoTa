#coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2020 宝塔软件(https://www.bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: 沐落 <cjx@bt.cn>
# | Author: lx
# +-------------------------------------------------------------------
import sys,os,time,psutil,re
panelPath = "/www/server/panel"
os.chdir(panelPath)
sys.path.insert(0, "class/")
import public,time,panelPush,public

try:
    from BTPanel import cache
except :
    from cachelib import SimpleCache
    cache = SimpleCache()

class panel_push:

    __push = None
    pids = None
    def __init__(self):
        self.__push = panelPush.panelPush()

    #-----------------------------------------------------------start 添加推送 ------------------------------------------------------
    def get_version_info(self,get):
        """
        获取版本信息
        """
        data = {}
        data['ps'] = ''
        data['version'] = '1.2'
        data['date'] = '2022-09-20'
        data['author'] = '宝塔'
        data['help'] = 'http://www.bt.cn/bbs'
        return data

    #名取PID
    def getPid(self,pname):
        try:
            if not self.pids: self.pids = psutil.pids()
            for pid in self.pids:
                if psutil.Process(pid).name() == pname: return True
            return False
        except: return True

    #检测指定进程是否存活
    def checkProcess(self,pid):
        try:
            if not self.pids: self.pids = psutil.pids()
            if int(pid) in self.pids: return True
            return False
        except:
            return False

    #检查是否启动
    def check_run(self,name):
        if name == "php-fpm":
            status = False
            base_path = "/www/server/php"
            if not os.path.exists(base_path):
                return status
            for p in os.listdir(base_path):
                pid_file = os.path.join(base_path, p, "var/run/php-fpm.pid")
                if os.path.exists(pid_file):
                    php_pid = int(public.readFile(pid_file))
                    status = self.checkProcess(php_pid)
                    if status:
                        return status
            return status
        elif name == 'nginx':
            status = False
            if os.path.exists('/etc/init.d/nginx'):
                pidf = '/www/server/nginx/logs/nginx.pid'
                if os.path.exists(pidf):
                    try:
                        pid = public.readFile(pidf)
                        status = self.checkProcess(pid)
                    except:
                        pass
            return status
        elif name == 'apache':
            status = False
            if os.path.exists('/etc/init.d/httpd'):
                pidf = '/www/server/apache/logs/httpd.pid'
                if os.path.exists(pidf):
                    pid = public.readFile(pidf)
                    status = self.checkProcess(pid)
            return status
        elif name == 'mysql':
            res = public.ExecShell("service mysqld status")
            if res and not re.search("not\s+running", res[0]):
                return True
            return False
        elif name == 'tomcat':
            status = False
            if os.path.exists('/www/server/tomcat/logs/catalina-daemon.pid'):
                if self.getPid('jsvc'): status = True
            if not status:
                if self.getPid('java'): status = True
            return status
        elif name == 'pure-ftpd':
            pidf = '/var/run/pure-ftpd.pid'
            status = False
            if os.path.exists(pidf):
                pid = public.readFile(pidf)
                status = self.checkProcess(pid)
            return status
        elif name == 'redis':
            status = False
            pidf = '/www/server/redis/redis.pid'
            if os.path.exists(pidf):
                pid = public.readFile(pidf)
                status = self.checkProcess(pid)
            return status
        elif name == 'memcached':
            status = False
            pidf = '/var/run/memcached.pid'
            if os.path.exists(pidf):
                pid = public.readFile(pidf)
                status = self.checkProcess(pid)
            return status
        return True

    def get_server_status(self, server_name):
        status = self.check_run(server_name)
        if status:
            return 1
        return 0

    """
    @获取推送模块配置
    """
    def get_module_config(self,get):

        data = []

        item = self.__push.format_push_data(push = ["mail",'dingding','weixin',"feishu"],project = 'ssl',type = 'ssl')
        item['cycle'] = 30
        item['title'] = 'SSL到期提醒'
        data.append(item)

        item = self.__push.format_push_data(push = ["mail",'dingding','weixin',"feishu"],project = 'endtime',type = 'endtime')
        item['cycle'] = 5
        item['title'] = '专业版/企业版到期提醒'
        item['helps'] = ['']
        data.append(item)

        services = ['nginx','apache',"pure-ftpd",'mysql','php-fpm','memcached','redis']
        channels = ['mail', 'dingding','weixin','sms',"feishu"]
        for x in services:
            item = {}
            item['project'] = x
            item['title'] = '{}服务停止通知'.format(x)

            if x == 'other':
                item['title'] = '自定义服务停止通知'
            else:
                ser_name = self.__get_service_name(x)
                if self.get_server_status(ser_name) == -1: continue

            item['type'] = 'services'
            item['keys'] = []
            item['interval'] = 300
            for x in ['stop']:
               item['keys'].append({'key':x,'val':'停止'})

            item['push'] = channels
            item['helps'] = ['部分服务停止可能会造成业务中断.','短信推送需提前购买，如需购买请联系[<a href="http://q.url.cn/CDfQPS?_type=wpa&amp;qidian=true" target="_blank" class="btlink">宝塔客服</a>]']
            data.append(item)
        import json
        public.writeFile('data/push/config/panel_push.json',json.dumps(data))
        return data

    def get_push_cycle(self,data):
        """
        @获取执行周期
        """
        result = {}
        for skey in data:
            result[skey] = data[skey]

            m_cycle =[]
            m_type = data[skey]['type']
            if m_type in ['endtime','ssl']:
                m_cycle.append('剩余{}天时，每天1次'.format(data[skey]['cycle']))
            elif m_type in ['services']:
                m_cycle.append('服务停止时，每{}秒1次'.format(data[skey]['interval']))
            if len(m_cycle) > 0:
                result[skey]['m_cycle'] = ''.join(m_cycle)
        return result

    #-----------------------------------------------------------end 添加推送 ------------------------------------------------------
    """
    @获取服务真实名称
    """
    def __get_service_name(self,name):
        slist = {"FTP服务端":'pure-ftpd'}
        if name in slist: name = slist[name]

        return name
    """
    @获取推送栏目
    """
    def get_total(self):
        return True;

    def get_push_data(self,data,total):
        if data['type'] == 'services':
            ser_name =  data['project']
            ser_name = self.__get_service_name(ser_name)

            status = self.get_server_status(ser_name)
            if status > 0:
                return public.returnMsg(False,"状态正常，跳过.")
            else:
                if status == 0:
                    return self.__get_service_result(data)
                return public.returnMsg(False,"服务未安装，跳过.")

        elif data['type'] in ['ssl']:

            if time.time() < data['index'] + 86400:
                return public.returnMsg(False,"一天推送一次，跳过.")

            import panelSSL
            ssl = panelSSL.panelSSL()
            clist = []
            for x in ssl.GetCertList(None):
                timeArray = time.strptime(x['notAfter'], "%Y-%m-%d")
                endtime = time.mktime(timeArray)
                day = int((endtime - time.time()) / 86400)
                if day > data['cycle']: continue
                clist.append(x)

            return self.__get_ssl_result(data,clist)

        elif data['type'] in ['endtime']:
            if time.time() < data['index'] + 86400:
                return public.returnMsg(False,"一天推送一次，跳过.")

            from pluginAuth import Plugin
            softs = Plugin(False).get_plugin_list(True)
            if softs['pro'] == 0: return public.returnMsg(False,"永久专业版，跳过.")

            if softs['ltd'] == -2 and softs['pro'] == -2:
                pass
            else:
                pro_data = {}
                if softs['ltd'] > 0:
                    pro_data['endtime'] = softs['ltd']
                    pro_data['name'] = "Linux企业版"
                    pro_data['affect'] = '全部企业版插件'
                elif softs['pro'] > 0:
                    pro_data['endtime'] = softs['pro']
                    pro_data['name'] = "Linux专业版"
                    pro_data['affect'] = '全部专业版插件'

                pro_data['day'] = int((pro_data['endtime'] - time.time()) / 86400)

                if pro_data['day'] <= data['cycle']:
                    return self.__get_ltd_result(data,pro_data)

        return public.returnMsg(False,"未达到阈值，跳过.")

    """
    @企业版到期提醒
    """
    def __get_ltd_result(self,data,pro_data):
        result = {'index':time.time()}

        for m_module in data['module'].split(','):
            result[m_module] = self.__push.format_msg_data()
            newline = ""
            if m_module in ['dingding','weixin',"feishu","mail"]:
                if m_module in ["mail"]:
                    newline="<br/>"
                    result[m_module]["title"] = "宝塔面板业务到期提醒"
                else:
                    newline = "\n\n"
                result[m_module]['msg'] = "".join((
                    "#### 宝塔面板业务到期提醒"+newline,
                    ">服务器 ："+ public.GetLocalIp() + newline,
                    ">剩余天数："+ str(pro_data['day'] + 1) +" 天"+newline,
                    ">到期产品："+ pro_data['name'] +newline,
                    ">到期时间："+ public.format_date(times =pro_data['endtime']) +newline,
                    ">影响业务："+ pro_data['affect'] +newline,
                    ">通知时间：" + public.format_date() + newline))
        return result

    """
    @ssl到期返回
    """
    def __get_ssl_result(self,data,clist):
        if len(clist) == 0:
            return public.returnMsg(False,"未找到到期证书，跳过.")

        result = {'index':time.time() }
        for m_module in data['module'].split(','):

            result[m_module] = self.__push.format_msg_data()
            newline = ""
            if m_module in ['dingding','weixin',"feishu","mail"]:
                if m_module in ["mail"]:
                    newline="<br/>"
                    result[m_module]["title"] = "宝塔面板SSL到期提醒"
                else:
                    newline = "\n\n"

                p_msg = "";
                for x in clist: p_msg+= "  到期：{}  域名：{}".format(x['notAfter'],x['subject']) + newline

                result[m_module]['msg'] ="".join((
                    "#### 宝塔面板SSL到期提醒" + newline,
                    ">服务器 ："+ public.GetLocalIp() +newline,
                    ">检测时间：" + public.format_date() +newline,
                    ">即将到期："+ str(len(clist)) +" 张"+newline,
                    p_msg))
        return result

    """
    @服务停止返回
    """
    def __get_service_result(self,data):

        s_idx = int(time.time())
        if s_idx < data['index'] + data['interval']:
            return public.returnMsg(False,"未达到间隔时间，跳过.")

        result = {'index':s_idx}

        for m_module in data['module'].split(','):
            result[m_module] = self.__push.format_msg_data()
            newline = ""
            if m_module in ['dingding','weixin',"feishu","mail"]:
                if m_module in ["mail"]:
                    newline="<br/>"
                    result[m_module]["title"] = "堡塔服务停止告警"
                else:
                    newline = "\n\n"
                result[m_module]['msg'] = "".join((
                    "#### 堡塔服务停止告警" + newline,
                    ">服务器 ："+ public.GetLocalIp() +newline + " ",
                    ">服务类型："+ data["project"] +newline + " ",
                    ">服务状态：已停止"+newline+" ",
                    ">检测时间："+ public.format_date()))
            elif m_module in ['sms']:
                result[m_module]['sm_type'] = 'servcies'
                result[m_module]['sm_args'] = { 'name':'{}'.format(public.GetConfigValue('title')), 'product':data["project"],'product1':data["project"]}
        return result



