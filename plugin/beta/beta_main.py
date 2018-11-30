#!/usr/bin/python
#coding: utf-8
#-----------------------------
# 宝塔Linux面板内测插件
#-----------------------------
import sys,os
reload(sys)
sys.setdefaultencoding('utf-8')
os.chdir('/www/server/panel');
sys.path.append("class/")
import public,db,time

class beta_main:
    __setupPath = '/www/server/panel/plugin/beta';
    #设置内测
    def SetConfig(self,get):
        data = {}
        data['username'] = get.bbs_name
        data['qq'] = get.qq
        data['email'] = get.email
        result = public.httpPost('https://www.bt.cn/Api/LinuxBeta',data);
        import json;
        data = json.loads(result);
        if data['status']:
            public.writeFile(self.__setupPath + '/config.conf',get.bbs_name + '|' + get.qq + '|' + get.email);
        return data;
    #取内测资格状态
    def GetConfig(self,get):
        try:
            cfile = self.__setupPath + '/config.conf'
            if not os.path.exists(cfile): cfile = 'data/beta.pl'
            return public.readFile(cfile).strip();
        except:
            return 'False';
