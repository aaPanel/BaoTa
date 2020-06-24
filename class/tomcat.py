#!/usr/bin/env python
#coding:utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2017 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: hwliang <hwl@bt.cn>
# +-------------------------------------------------------------------

#------------------------------
# Tomcat管理类
#------------------------------
from xml.etree.ElementTree import ElementTree,Element
import os
class tomcat:
    __TREE = None
    __ENGINE = None
    __ROOT = None
    __CONF_FILE = '/www/server/tomcat/conf/server.xml';
    #打开配置文件
    def __init__(self):
        if self.__TREE: return;
        self.__TREE = ElementTree();
        self.__TREE.parse(self.__CONF_FILE);
        self.__ROOT = self.__TREE.getroot();
        self.__ENGINE = self.__TREE.findall('Service/Engine')[0];
        
    #获取虚拟主机列表
    def GetVhosts(self):        
        Hosts = self.__ENGINE.getchildren();
        data = []
        for host in Hosts:
            if host.tag != 'Host': continue;
            tmp = host.attrib
            ch = host.getchildren();
            tmp['item'] = {}
            for c in ch:
                tmp['item'][c.tag] = c.attrib;
            data.append(tmp);
        return data;

    #添加虚拟主机
    def AddVhost(self,path,domain):
        if self.GetVhost(domain): return False;
        if not os.path.exists(path): return False;
        attr = {"autoDeploy":"true","name":domain,"unpackWARs":"true","xmlNamespaceAware":"false","xmlValidation":"false"}
        Host = Element("Host", attr);
        attr = {"docBase":path,"path":"","reloadable":"true","crossContext":"true",}
        Context = Element("Context", attr);
        Host.append(Context);
        self.__ENGINE.append(Host);
        self.Save();
        return True;
    
    #删除虚拟主机
    def DelVhost(self,name):
        host = self.GetVhost(name);
        if not host: return False
        self.__ENGINE.remove(host);
        self.Save();
        return True;
    
    #获取指定虚拟主机
    def GetVhost(self,name):
        Hosts = self.__ENGINE.getchildren();
        for host in Hosts:
            if host.tag != 'Host': continue;
            if host.attrib['name'] == name:
                return host
        return None;
    
    #修改根目录
    def SetPath(self,name,path):
        if not os.path.exists(path): return False;
        host = self.GetVhost(name);
        if not host: return False
        #host.attrib['appBase'] = path;
        host.getchildren()[0].attrib['docBase'] = path;
        self.Save();
        return True;
    
    #修改虚拟主机属性
    def SetVhost(self,name,key,value):
        host = self.GetVhost(name);
        if not host: return False
        host.attrib[key] = value;
        self.Save();
        return True
    
    #保存配置
    def Save(self):
        self.format(self.__ROOT);
        self.__TREE.write(self.__CONF_FILE,'utf-8');
    
    #整理配置文件格式
    def format(self,em,level = 0):
        i = "\n" + level*"  "
        if len(em):
            if not em.text or not em.text.strip():
                em.text = i + "  "
            for e in em:
                self.format(e, level+1)
            if not e.tail or not e.tail.strip():
                e.tail = i
        if level and (not em.tail or not em.tail.strip()):
            em.tail = i
if __name__ == '__main__':
    tom = tomcat();
    print(tom.DelVhost('w1.hao.com'));
    