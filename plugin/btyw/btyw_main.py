#!/usr/bin/python
#coding: utf-8
#-----------------------------
# 宝塔Linux面板网站备份工具 - ALIOSS
#-----------------------------
import sys,os
if sys.version_info[0] == 2:
    reload(sys)
    sys.setdefaultencoding('utf-8')
sys.path.append("class/")
import public
from BTPanel import session

class btyw_main:
    def GetIndex(self,get):
        try:
            if 'btyw' in session: return False;
            result = public.httpGet('http://www.bt.cn/lib/btyw.html');
            public.writeFile('plugin/btyw/index.html',result);
            session['btyw'] = True;
            return True;
        except:
            return False;