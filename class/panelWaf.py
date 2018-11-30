#!/usr/bin/python
#coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2017 宝塔软件(http:#bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: 黄文良 <287962566@qq.com>
# +-------------------------------------------------------------------

import re,json,sys,public,os
class panelWaf:
    __ConfigFile = '/www/server/nginx/waf/config.lua'
    __WafConfigPath = '/www/server/panel/vhost/wafconf'  
    #获取配置项
    def GetConfig(self,get):
        data = {}
        try:
            conf = public.readFile(self.__ConfigFile);
            configs = ["attacklog","UrlDeny","Redirect","CookieMatch","postMatch","whiteModule","CCDeny","CCrate"];
            #遍历单一配置
            for key in configs:
                rep = key + "\s*=\s*\"([\w\/]+)\"\s*\n"
                data[key] = re.search(rep,conf).groups()[0]
            #遍历列表
            configs = ["black_fileExt","ipWhitelist","ipBlocklist"];
            for key in configs:
                rep = key + "\s*=\s*(.+)\n";
                data[key] = json.loads(re.search(rep,conf).groups()[0].replace("{","[").replace("}","]"));
            
            get.name = 'whiteurl';
            data['uriWhite'] = self.GetWafConf(get);
        except:
            pass;
        data['status'] = self.GetStatus();
        return  data;
    
    #取状态
    def GetStatus(self):
        path = "/www/server/nginx/conf/nginx.conf";
        if not os.path.exists(path): return public.returnMsg(False,'WAF_NOT_NGINX');
        conf = public.readFile(path);
        status = 1;
        if conf.find("#include luawaf.conf;") != -1: status = 0;
        if conf.find("luawaf.conf;") == -1: status = -1;
        return status;
    
    #更新规则
    def updateWaf(self,get):
        names = ['args','cookie','post','url','user-agent'];
        furl = 'http://download.bt.cn/install/waf/wafconf'
        fpath = '/www/server/panel/vhost/wafconf'
        for name in names:
            public.downloadFile(furl + '/' + name,fpath + '/' + name);
        public.serviceReload();
        return public.returnMsg(True,'WAF_UPDATE')
    
    #设置状态
    def SetStatus(self,get):
        path = "/www/server/nginx/conf/nginx.conf";
        if not os.path.exists(path): return public.returnMsg(False,'WAF_NOT_NGINX');
        conf = public.readFile(path);
        status = self.GetStatus()
        if status == -1: return public.returnMsg(False,'WAF_NOT_NGINX_VERSION');
        if status == 0:
            conf = conf.replace('#include luawaf.conf;',"include luawaf.conf;");
        else:
            conf = conf.replace('include luawaf.conf;',"#include luawaf.conf;");
        
        public.writeFile(path,conf);
        public.serviceReload();
        return public.returnMsg(True,"SET_SUCCESS");
            
        
    
    #设置配置项
    def SetConfigString(self,get):
        conf = public.readFile(self.__ConfigFile);
        rep = get.name + "\s*=\s*\"[\w\/]+\"\s*\n"
        conf = re.sub(rep,get.name + '="' + get.value.strip() + '"\n',conf)
        public.writeFile(self.__ConfigFile,conf);
        public.serviceReload();
        return public.returnMsg(True,"SET_SUCCESS");
    
    #设置配置项列表
    def SetConfigList(self,get):
        conf = public.readFile(self.__ConfigFile);
        rep = get.name + "\s*=\s*(.+)\n";
        keyList = json.loads(re.search(rep,conf).groups()[0].replace("{","[").replace("}","]"));
        if get.name != 'black_fileExt':
            rep2 = "\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}";
            if not re.search(rep2,get.value): return public.returnMsg(False,"WAF_CONF_ERR");
        if get.act == 'del':
            if not get.value in keyList: return public.returnMsg(False,"WAF_CONF_NOT_EXISTS");
            tmp = []
            for t in keyList:
                if t == get.value: continue;
                tmp.append(t);
            keyList = tmp;
        else:
            if get.value in keyList:return public.returnMsg(False,"WAF_CONF_EXISTS");
            keyList.append(get.value.strip());
        keyStr = json.dumps(keyList).replace("[","{").replace("]","}");
        conf = re.sub(rep,get.name + "=" + keyStr + "\n",conf);
        public.writeFile(self.__ConfigFile,conf);
        public.serviceReload();
        return public.returnMsg(True,"SUCCESS");
        
    #获取指定规则列表
    def GetWafConf(self,get):
        path = self.__WafConfigPath + '/' + get.name;
        if not os.path.exists(path): return public.returnMsg(False,"WAF_CONF_NOT_EXISTS");
        data = public.readFile(path).split("\n")
        return data;
    
    #设置指定规则列表
    def SetWafConf(self,get):
        path = self.__WafConfigPath + '/' + get.name;
        if not os.path.exists(path): return public.returnMsg(False,"WAF_CONF_NOT_EXISTS");
        data = public.readFile(path).split("\n")
        if get.act == "del":
            if not get.value in data: return public.returnMsg(False,"WAF_CONF_NOT_EXISTS");
            tmp = []
            for t in data:
                if get.value == t: continue;
                tmp.append(t);
            data = tmp;
        else:
            if get.value in data: return public.returnMsg(False,"WAF_CONF_EXISTS");
            data.append(get.value);
        conf = ""
        
        for v in data:
            conf += v + "\n";
            
        public.writeFile(path,conf[:-1]);
        public.serviceReload();
        return public.returnMsg(True,"SUCCESS");
    
    #取日志
                
    

if __name__ == "__main__":
    if len(sys.argv) > 1:
        p = panelWaf();
        if sys.argv[1] == 'add' or sys.argv[1] == 'del':
            print p.SetConfigList(sys.argv[2],sys.argv[3],sys.argv[1]);
        else:
            print p.SetConfigString(sys.argv[1],sys.argv[2]);
    print GetConfig();