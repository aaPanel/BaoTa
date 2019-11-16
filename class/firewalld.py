#!/usr/bin/env python
# coding:utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2017 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: 1249648969@qq.com,
# +-------------------------------------------------------------------
# Firewalld管理类
# ------------------------------
from xml.etree.ElementTree import ElementTree, Element
import os, public

class firewalld:
    __TREE = None
    __ROOT = None
    __CONF_FILE = '/etc/firewalld/zones/public.xml'

    # 初始化配置文件XML对象
    def __init__(self):
        if self.__TREE: return
        self.__TREE = ElementTree()
        self.__TREE.parse(self.__CONF_FILE)
        self.__ROOT = self.__TREE.getroot()


    # 获取端口列表
    def GetAcceptPortList(self):
        mlist = self.__ROOT.getchildren()
        data = []
        for p in mlist:
            if p.tag != 'port': continue
            tmp = p.attrib
            port = p.attrib['port']
            data.append(tmp)
        return data

    # 添加端口放行
    def AddAcceptPort(self, port, pool='tcp'):
        # 检查是否存在
        if self.CheckPortAccept(pool, port): return True
        attr = {"protocol": pool, "port": port}
        Port = Element("port", attr)
        self.__ROOT.append(Port)
        self.Save()
        return True

    # 删除端口放行
    def DelAcceptPort(self, port, pool='tcp'):
        # 检查是否存在
        if not self.CheckPortAccept(pool, port): return True
        mlist = self.__ROOT.getchildren()
        m = False
        for p in mlist:
            if p.tag != 'port': continue
            if p.attrib['port'] == port:
                self.__ROOT.remove(p)
                m = True
        if m:
            self.Save()
            return True
        return False

    # 添加UDP端口放行
    def AddUpdPort(self, port, pool='udp'):
        # 检查是否存在
        if self.CheckPortAccept(pool, port): return True
        attr = {"protocol": pool, "port": port}
        Port = Element("port", attr)
        self.__ROOT.append(Port)
        self.Save()
        return True

    # 删除UDP端口放行
    def DelUdpPort(self, port, pool='udp'):
        # 检查是否存在
        if not self.CheckPortAccept(pool, port): return True
        mlist = self.__ROOT.getchildren()
        m = False
        for p in mlist:
            if p.tag != 'port': continue
            if p.attrib['port'] == port:
                self.__ROOT.remove(p)
                m = True
        if m:
            self.Save()
            return True
        return False

    # 检查端口是否已放行
    def CheckPortAccept(self, pool, port):
        for p in self.GetAcceptPortList():
            if p['port'] == port and p['protocol']==pool: return True
        return False


    # 获取屏蔽IP列表
    def GetDropAddressList(self):
        mlist = self.__ROOT.getchildren()
        data = []
        for ip in mlist:

            if ip.tag != 'rule': continue
            tmp = {}
            ch = ip.getchildren()
            a=None
            for c in ch:
                tmp['type']=None
                if c.tag == 'drop': tmp['type'] = 'drop'
                if c.tag == 'source':

                    tmp['address']=c.attrib['address']
                if tmp['type']:
                    data.append(tmp)
        return data

    # 获取 reject 信息
    def GetrejectLIST(self):
        mlist = self.__ROOT.getchildren()
        data = []
        for ip in mlist:
            #print(ip)
            if ip.tag != 'rule': continue
            tmp = {}
            ch = ip.getchildren()
            a=None
            flag = None
            for c in ch:
                tmp['type']=None
                if c.tag == 'reject': tmp['type'] = 'reject'
                if c.tag == 'source':

                    tmp['address']=c.attrib['address']
                if c.tag =='port':

                    tmp['protocol']=c.attrib['protocol']
                    tmp['port']=c.attrib['port']
                if tmp['type']:
                    data.append(tmp)
        return data

# 获取 accept 信息

    def Getacceptlist(self):
        mlist = self.__ROOT.getchildren()
        data = []
        for ip in mlist:

            if ip.tag != 'rule': continue
            tmp = {}
            ch = ip.getchildren()
            a=None
            flag = None
            for c in ch:
                tmp['type']=None
                if c.tag == 'accept': tmp['type'] = 'accept'
                if c.tag == 'source':

                    tmp['address']=c.attrib['address']
                if c.tag =='port':
                    tmp['protocol']=c.attrib['protocol']
                    tmp['port']=c.attrib['port']
                if tmp['type']:
                    data.append(tmp)
        return data


# 获取所有信息
    def Get_All_Info(self):
        data={}
        data['drop_ip']=self.GetDropAddressList()
        data['reject']=self.GetrejectLIST()
        data['accept']=self.Getacceptlist()
        return data

# 判断是否存在
    def Chekc_info(self,port,address,pool,type):
        data=self.Get_All_Info()
        if type=='accept':
            for i in data['accept']:
                #print(i['address'], i['protocol'], i['port'])
                if i['address']==address and i['protocol']==pool and i['port']==port:
                    return True
                else:
                    return False
        elif type=='reject':
            for i in data['accept']:
               # print(i['address'], i['protocol'], i['port'])
                if i['address'] == address and i['protocol'] == pool and i['port'] == port:
                    return True
                else:
                    return False
        else:
            return False

    def AddDropAddress(self, address):
        # 检查是否存在
        if self.CheckIpDrop(address): return True
        attr = {"family": 'ipv4'}
        rule = Element("rule", attr)
        attr = {"address": address}
        source = Element("source", attr)
        drop = Element("drop", {})
        rule.append(source)
        rule.append(drop)
        self.__ROOT.append(rule)
        self.Save()
        return 'OK'

    # 删除IP屏蔽
    def DelDropAddress(self, address):
        # 检查是否存在
        if not self.CheckIpDrop(address): return True
        mlist = self.__ROOT.getchildren()
        for ip in mlist:
            if ip.tag != 'rule': continue
            ch = ip.getchildren()
            for c in ch:

                if c.tag != 'source':continue
                if c.attrib['address'] == address:
                    self.__ROOT.remove(ip)
                    self.Save()
                    return True
        return False



# 添加端口放行并且指定IP
    def Add_Port_IP(self, port,address,pool,type):
        if type=='accept':
            # 判断是否存在
            if self.Chekc_info(port,address,pool,type): return True
            attr = {"family": 'ipv4'}
            rule = Element("rule", attr)
            attr = {"address": address}
            source = Element("source", attr)
            attr={'port':str(port),'protocol':pool}
            port_info=Element("port",attr)
            accept = Element("accept", {})
            rule.append(source)
            rule.append(port_info)
            rule.append(accept)
            self.__ROOT.append(rule)
            self.Save()
            return True

        elif type=='reject':
            # 判断是否存在
            if self.Chekc_info(port,address,pool,type):return True
            attr = {"family": 'ipv4'}
            rule = Element("rule", attr)
            attr = {"address": address}
            source = Element("source", attr)
            attr = {'port': str(port), 'protocol': pool}
            port_info = Element("port", attr)
            reject = Element("reject", {})
            rule.append(source)
            rule.append(port_info)
            rule.append(reject)
            self.__ROOT.append(rule)
            self.Save()
            return True
        else:
            return False


# 删除指定端口的=。=
    def Del_Port_IP(self, port,address,pool,type):
        if type=='accept':
            a = None
            for i in self.__ROOT:
                if i.tag == 'rule':
                    tmp = {}
                    for c in i.getchildren():
                        tmp['type'] = None
                        if c.tag == 'accept': tmp['type'] = 'accept'
                        if c.tag == 'source':
                            tmp['address'] = c.attrib['address']
                        if c.tag == 'port':
                            tmp['protocol'] = c.attrib['protocol']
                            tmp['port'] = c.attrib['port']
                        if tmp['type']:
                            if tmp['port'] == port and tmp['address'] == address and tmp['type'] == type and tmp['protocol'] == pool:
                                self.__ROOT.remove(i)
                        self.Save()
            return True

        elif type=='reject':
            for i in self.__ROOT:
                if i.tag == 'rule':
                    tmp = {}
                    for c in i.getchildren():
                        tmp['type'] = None
                        if c.tag == 'reject': tmp['type'] = 'reject'
                        if c.tag == 'source':
                            tmp['address'] = c.attrib['address']
                        if c.tag == 'port':
                            tmp['protocol'] = c.attrib['protocol']
                            tmp['port'] = c.attrib['port']
                        if tmp['type']:
                            if tmp['port'] == port and tmp['address'] == address and tmp['type'] == type and tmp['protocol'] == pool:
                                self.__ROOT.remove(i)
                                self.Save()
            return True

    # 检查IP是否已经屏蔽
    def CheckIpDrop(self, address):
        for ip in self.GetDropAddressList():
            if ip['address'] == address: return True
        return False

    # 取服务状态
    def GetServiceStatus(self):
        import psutil
        for pid in psutil.pids():
            if psutil.Process(pid).name() == 'firewalld': return True
        return False

    # 服务控制
    def FirewalldService(self, type):
        public.ExecShell('systemctl ' + type + ' firewalld.service')
        return public.returnMsg(True, 'SUCCESS')

    # 保存配置
    def Save(self):
        self.format(self.__ROOT)
        self.__TREE.write(self.__CONF_FILE, 'utf-8')
        public.ExecShell('firewall-cmd --reload')

    # 整理配置文件格式
    def format(self, em, level=0):
        i = "\n" + level * "  "
        if len(em):
            if not em.text or not em.text.strip():
                em.text = i + "  "
            for e in em:
                self.format(e, level + 1)
            if not e.tail or not e.tail.strip():
                e.tail = i
        if level and (not em.tail or not em.tail.strip()):
            em.tail = i


