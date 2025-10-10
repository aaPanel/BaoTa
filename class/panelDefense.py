#coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: hwliang
# +-------------------------------------------------------------------

# +-------------------------------------------------------------------
# | 面板防御模块
# +-------------------------------------------------------------------
import public

class bot_safe:
    '''
        @name 机器防御模块
    '''

    def is_spider_bot(self,user_agent):
        '''
            @name 检查是否为搜索引擎爬虫
            @auth hwliang
            @param user_agent <str> User-Agent
            @return <bool> True/False
        '''
        spider_uas = ["bot","spider"]
        for spider_ua in spider_uas:
            if spider_ua in user_agent: return True
        return False


    def is_scanner(self,user_agent):
        '''
            @name 检查是否为扫描器
            @auth hwliang
            @param user_agent <str> User-Agent
            @return <bool> True/False
        '''
        scanner_uas = ["wpscan","httrack","antsword","harvest","audit","dirbuster","pangolin","nmap","sqln","hydra","parser","libwww","bbbike","sqlmap","w3af","owasp","nikto","fimap","havij","zmeu","babykrokodil","netsparker","httperf"," sf/"]
        for scanner_ua in scanner_uas:
            if scanner_ua in user_agent: return True
        return False


    def is_scripter(self,user_agent):
        '''
            @name 检查是否为脚本工具
            @auth hwliang
            @param user_agent <str> User-Agent
            @return <bool> True/False
        '''
        scripter_uas = ["curl","requests","python","php","c#","urllib","wget","winhttp","webzip","fetchurl","node-superagent","java/","feeddemon","jullo","indy library","alexa toolbar","asktbfxtv","ahrefsbot","crawldaddy","java","feedly","apache-httpasyncclient","universalfeedparser","apachebench","microsoft url control","zmeu","jaunty","yyspider","digext","httpclient","heritrix","easouspider","ezooms","flightdeckreports"]
        for scripter_ua in scripter_uas:
            if scripter_ua in user_agent: return True
        return False

    def spider(self,user_agent,ip):
        '''
            @name 爬虫防御
            @auth hwliang
            @param user_agent <str> User-Agent
            @param ip <str> 客户端IP地址
            @return <bool> True/False
        '''
        # 检查参数
        if not user_agent or not ip: return False

        # ua长度小于24位的拒绝
        ua_len = len(user_agent)
        if ua_len < 24 or ua_len > 350: return False

        # 放行局域网IP
        if public.is_local_ip(ip): return True

        user_agent = user_agent.lower()

        # 检查是否为搜索引擎爬虫
        if self.is_spider_bot(user_agent): return False

        # 检查是否为扫描器
        if self.is_scanner(user_agent): return False

        # 检查是否为脚本工具
        if self.is_scripter(user_agent): return False

        return True
