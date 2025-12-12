# coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2014-2099 宝塔软件(http://bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author: wzz <wzz@bt.cn>
# -------------------------------------------------------------------
import json
import re
import time
import os

# ------------------------------
# 系统防火墙模型 - 业务接口类
# ------------------------------
import public
from firewallModel.firewallBase import Base
from firewallModel.iptablesServices import IptablesServices


class main(Base):

    def __init__(self):
        super().__init__()
        self.iptables = IptablesServices()

    # 2024/3/14 下午 12:01 获取防火墙状态信息
    def get_firewall_info(self, get):
        """
        @name 获取防火墙统计
        """
        cache_key = "firewall_info"
        from BTPanel import cache
        data = cache.get(cache_key)
        if data: return data

        data = {}
        data['port'] = len(self.firewall.list_port())
        data['ip'] = len(self.iptables.list_address())+len(self.firewall.list_address())
        data['trans'] = len(self.iptables.list_port_forward())
        data['country'] = public.M('firewall_country').count()
        data['banned'] = public.M('firewall_malicious_ip').count()
        data['type'] = "firewalld" if self._isFirewalld else "ufw" if self._isUfw else "iptables"
        if not "m_time_file" in self.__dict__:
            self.m_time_file = "/www/server/panel/data/firewall/geoip_mtime.pl"
        m_time = public.readFile(self.m_time_file)
        data['update_time'] = public.format_date(times=int(m_time) if m_time else int(time.time()))

        isPing = True
        try:
            file = '/etc/sysctl.conf'
            conf = public.readFile(file)
            rep = r"#*net\.ipv4\.icmp_echo_ignore_all\s*=\s*([0-9]+)"
            tmp = re.search(rep, conf).groups(0)[0]
            if tmp == '1': isPing = False
        except:
            isPing = True

        data['ping'] = isPing

        cache.set(cache_key, data, 3600)
        return data

    # 2024/3/26 下午 3:40 获取防火墙状态
    def get_status(self, get):
        '''
            @name 获取防火墙状态
            @author wzz <2024/3/26 下午 3:40>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        firewall_status = self.get_firewall_status()
        firewall_init_status = self.check_iptables_env(firewall_status)
        return {"status": firewall_status, "init_status": firewall_init_status}

    def clean_cache(self,get):
        '''
            @name 强制清除防火墙缓存
            @author csj
        '''
        from BTPanel import cache
        cache_keys = ["firewall_info","port_rules_list","ip_rules_list","port_forward_list"]
        for cache_key in cache_keys:
            cache.delete(cache_key)

        return public.returnMsg(True, '清除缓存成功')

    def check_iptables_env(self,firewall_status):
        if firewall_status:
            if not os.path.exists('/etc/systemd/system/BT-FirewallServices.service'):
                #判断 数据库是否有数据 如果没数据直接初始化(新安装面板场景)
                if public.M('firewall_country').count() == 0 and \
                    public.M('firewall_ip').count() == 0 and \
                    public.M('firewall_malicious_ip').count() == 0 and \
                    public.M('firewall_forward').count() == 0 :
                    
                    exec_shell = '('
                    if not os.path.exists('/usr/sbin/ipset'):
                        exec_shell = exec_shell + '{} install ipset -y;'.format(public.get_sys_install_bin())
                    exec_shell = exec_shell + 'sh {panel_path}/script/init_firewall.sh)'.format(panel_path=public.get_panel_path())
                    public.ExecShell(exec_shell)
                    return {'status': True, 'msg': '已安装.'}
                return {'status': False, 'msg': '防火墙未初始化.'}
            elif public.ExecShell("iptables -C INPUT -j IN_BT")[1] != '':         #丢失iptable链 需要重新创建
                exec_shell = 'sh {}/script/init_firewall.sh'.format(public.get_panel_path())
                public.ExecShell(exec_shell)
                return {'status': True, 'msg': '已安装.'}
            else:
                return {'status': True, 'msg': '已安装.'}
        else:
            return {'status': True, 'msg': '防火墙未开启.'}

    def update_bt_firewall(self,get):
        if not os.path.exists('/etc/systemd/system/BT-FirewallServices.service'):
            panel_path = public.get_panel_path()
            exec_shell = '('
            if not os.path.exists('/usr/sbin/ipset'):
                exec_shell = exec_shell + '{} install ipset -y;'.format(public.get_sys_install_bin())
            exec_shell = exec_shell + 'sh {panel_path}/script/init_firewall.sh;btpython -u {panel_path}/script/upgrade_firewall.py )'.format(panel_path=panel_path)

            import panelTask
            task_obj = panelTask.bt_task()
            task_id = task_obj.create_task('防火墙初始化任务', 0, exec_shell)
            public.print_log(f"防火墙初始化任务已创建，任务ID：{task_id}")
            return {'status': True, 'msg': '防火墙初始化任务已创建.', 'task_id': task_id}
        else:
            return {'status': False, 'msg': '已安装.'}

    # 2024/3/26 下午 3:42 设置防火墙状态
    def set_status(self, get):
        '''
            @name 设置防火墙状态
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        get.status = get.get('status/s', '1')
        if get.status not in ['0', '1']:
            return public.returnMsg(False, '参数错误')

        if get.status == '1':
            start_status = self.firewall.start()
            if not start_status["status"]:
                public.WriteLog("系统防火墙", "启动防火墙失败")
                return start_status

            get.reload = 0
            default_ports = ["SSH", "80", "443", "39000-40000", "21","PanelPort"]
            close_ports  = get.get('ports', '').split(",")

            for port in default_ports:
                if port not in close_ports:
                    if port == "PanelPort":
                        _panel_port_file = '/www/server/panel/data/port.pl'
                        port = public.readFile(_panel_port_file).strip(" ").strip("\n")
                    elif port == "SSH":
                        cmd = "cat /etc/ssh/sshd_config |grep -E '^Port'|awk '{print $2}'|awk 'NR == 1'"
                        ssh_port = public.ExecShell(cmd)[0].strip(" ").strip("\n")
                        if ssh_port != "": port = ssh_port
                    get.port = port
                    self.set_port_rule(get)
            self.firewall.reload()
            public.WriteLog("系统防火墙", "启动防火墙")
            return start_status
        else:
            public.WriteLog("系统防火墙", "停止防火墙")
            return self.firewall.stop()

    # 2024/5/13 下午3:50 检查指定端口是否已经存在，如果存在则返回False，否则返回True
    def check_port_exist(self, get):
        '''
            @name 检查指定端口是否已经存在，如果存在则返回False，否则返回True
            @author wzz <2024/5/13 下午3:51>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        port_rules_list = self.port_rules_list(get)
        for item in port_rules_list['data']:
            if item["Port"] == get.port and item["Address"] == get.address and item["Protocol"] == get.protocol and \
                    item["Strategy"] == get.strategy and item["Chain"] == get.chain:
                return False

        return True

    # 2024/5/13 下午4:13 检查指定ip规则是否已经存在，如果存在则返回False，否则返回True
    def check_ip_exist(self, get):
        '''
            @name 检查指定ip规则是否已经存在，如果存在则返回False，否则返回True
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        ip_rules_list = self.ip_rules_list(get)
        for item in ip_rules_list["data"]:
            if item["Address"] == get.address and item["Strategy"] == get.strategy and item["Chain"] == get.chain:
                return False

        return True

    # 2024/5/13 下午4:17 检查指定端口转发规则是否已经存在，如果存在则返回False，否则返回True
    def check_forward_exist(self, get):
        '''
            @name 检查指定端口转发规则是否已经存在，如果存在则返回False，否则返回True
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        forward_rules_list = self.port_forward_list(get)
        for item in forward_rules_list["data"]:
            if item["S_Port"] == get.S_Port and item["T_Address"] == get.T_Address and item["T_Port"] == get.T_Port and item["Protocol"].upper() == get.protocol.upper():
                return False

        return True

    # 2024/3/26 下午 6:09 从数据库中获取端口规则列表
    def get_port_db(self, get):
        '''
            @name 从数据库中获取端口规则列表
            @author wzz <2024/3/26 下午 6:13>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        try:
            where = '1=1'
            sql = public.M('firewall_new')
            data = sql.where(where, ()).select()

            domain_sql = public.M('firewall_domain')
            domain_data = domain_sql.where(where, ()).select()
            for i in range(len(data)):
                if not "ports" in data[i]:
                    data[i]['status'] = -1
                    continue

                if "brief" in data[i]:
                    data[i]['brief'] = public.xssdecode(data[i]['brief'])

                if not "chain" in data[i]:
                    data[i]['chain'] = "INPUT"
                if "chain" in data[i] and data[i]['chain'] == "":
                    data[i]['chain'] = "INPUT"

                for j in range(len(domain_data)):
                    if "domain" in domain_data[j] and data[i]['address'] in domain_data[j]['domain']:
                        data[i]['domain'] = domain_data[j]['domain']
                        break

            return data
        except Exception as e:
            return []

    # 2024/3/26 下午 11:53 从数据库中获取ip规则列表
    def get_ip_db(self, get):
        '''
            @name 从数据库中获取ip规则列表
            @author wzz <2024/3/26 下午 11:53>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        try:
            where = '1=1'
            sql = public.M('firewall_ip')

            ip_data = sql.where(where, ()).select()
            ip_dict = {}
            for i_data in ip_data:
                if "brief" in i_data:
                    i_data['brief'] = public.xssdecode(i_data['brief'])
                if not "chain" in i_data:
                    i_data['chain'] = "INPUT"
                if "chain" in i_data and i_data['chain'] == "":
                    i_data['chain'] = "INPUT"

                if not ip_dict.get(i_data['address'],None):
                    ip_dict[i_data['address']]=[]
                ip_dict[i_data['address']].append(i_data)

            return ip_dict
        except Exception as e:
            return {}

    # 2024/3/26 下午 11:58 从数据库中获取端口转发规则列表
    def get_forward_db(self, get):
        '''
            @name 从数据库中获取端口转发规则列表
            @author wzz <2024/3/26 下午 11:58>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        try:
            where = '1=1'
            sql = public.M('firewall_forward')

            if hasattr(get, 'query'):
                where = " S_Address like '%{search}%' or S_Port like '%{search}%' or T_Address like '%{search}%' or T_Port like '%{search}%'".format(
                    search=get.query
                )
            res = sql.where(where, ()).select()
            if type(res) != list:
                return []
            return res
        except Exception as e:
            return []

    # 2024/3/26 下午 10:46 构造端口规则返回数据
    def structure_port_return_data(self, list_port, rule_db, get):
        '''
            @name 构造返回数据
            @author wzz <2024/3/26 下午 10:47>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        cache_key = "port_rules_list"
        from BTPanel import cache
        data = cache.get(cache_key)
        if data:
            new_list = []
            sort_data = data
            for j in range(len(sort_data)):
                if get.query != "":
                    if get.query in sort_data[j]['Port'] or get.query in sort_data[j]['brief'] or get.query in \
                            sort_data[j]['Address']:
                        new_list.append(sort_data[j])
                elif "Chain" not in sort_data[j]:
                    new_list.append(sort_data[j])
                elif get.chain != "ALL" and sort_data[j]['Chain'] == get.chain:
                    new_list.append(sort_data[j])

            if len(new_list) > 0 or get.query != "" or get.chain != "ALL":
                sort_data = sorted(new_list, key=lambda x: x['addtime'], reverse=True)
        else:
            new_list = []
            for j in range(len(list_port)):
                list_port[j]['id'] = 0
                list_port[j]['sid'] = 0
                list_port[j]['brief'] = ""
                list_port[j]['domain'] = ""
                if (list_port[j]['Port'].find(":") != -1 or list_port[j]['Port'].find("-") != -1 or
                        list_port[j]['Port'].find("/") != -1 or list_port[j]['Port'].find(".") != -1):
                    list_port[j]['status'] = 1
                else:
                    try:
                        if not ":" in list_port[j]['Port'] or not "-" in list_port[j]['Port']:
                            list_port[j]['status'] = self.CheckPort(int(list_port[j]['Port']), list_port[j]['Protocol'])
                        else:
                            list_port[j]['status'] = -1
                    except:
                        list_port[j]['status'] = -1

                if "Chain" in list_port[j] and list_port[j]['Chain'] == "OUTPUT":
                    list_port[j]['status'] = -1

                list_port[j]['addtime'] = "--"

                list_port[j]['Port'] = list_port[j]['Port'].replace(":", "-")
                for i in range(len(rule_db)):
                    if (rule_db[i]['ports'] == list_port[j]['Port'] and
                            rule_db[i]['protocol'] == list_port[j]['Protocol'] and
                            rule_db[i]['address'].lower() == list_port[j]['Address'].lower() and
                            rule_db[i]['types'] == list_port[j]['Strategy'] and
                            rule_db[i]['chain'] == list_port[j]['Chain']):
                        list_port[j]['id'] = rule_db[i]['id']
                        list_port[j]['sid'] = rule_db[i]['sid']
                        list_port[j]['brief'] = rule_db[i]['brief']
                        list_port[j]['addtime'] = rule_db[i]['addtime']

                        if "domain" in rule_db[i]:
                            list_port[j]['domain'] = rule_db[i]['domain']

                        break

                if get.query != "":
                    if get.query in list_port[j]['Port'] or get.query in list_port[j]['brief'] or get.query in \
                            list_port[j]['Address']:
                        new_list.append(list_port[j])

            if len(new_list) > 0 or get.query != "":
                sort_data = sorted(new_list, key=lambda x: x['addtime'], reverse=True)
            else:
                sort_data = sorted(list_port, key=lambda x: x['addtime'], reverse=True)

            if get.query == "":
                cache.set(cache_key, sort_data, 86400)
        if get.export == "1":
            get.row = len(sort_data)
        return self.return_page(sort_data, get)

    # 2024/3/27 上午 12:01 构造ip规则返回数据
    def structure_ip_return_data(self, get):
        '''
            @name 构造ip规则返回数据
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''

        cache_key = "ip_rules_list"
        from BTPanel import cache
        data = cache.get(cache_key)

        if not data: #未缓存 处理逻辑
            rule_db = self.get_ip_db(get)
            if get.chain == "INPUT":
                list_ip = self.iptables.list_address(["INPUT"])  # 托管的IP规则
                system_list_address = self.firewall.list_input_address()  # 系统防火墙的IP规则 ufw firewall 为了考虑用户手动添加的规则
                list_ip += system_list_address  # 拼接
            elif get.chain == "OUTPUT":
                list_ip = self.iptables.list_address(["OUTPUT"])
                system_list_address = self.firewall.list_output_address()
                list_ip += system_list_address
            else:
                list_ip = self.iptables.list_address(["INPUT", "OUTPUT"])
                system_list_address = self.firewall.list_address()
                list_ip += system_list_address

            new_list = []
            for j in range(len(list_ip)):
                import random
                list_ip[j]['id'] = random.randint(-100, -1)
                list_ip[j]['sid'] = 0
                list_ip[j]['brief'] = ""
                list_ip[j]['domain'] = ""
                list_ip[j]['addtime'] = "--"
                list_ip[j]["expiry_date"] = ''
                 #BT-Services托管的IP规则

                if "Timeout" in list_ip[j]:
                    # BT-Services托管的IP规则
                    if int(list_ip[j]["Timeout"]) > 0:
                        from datetime import datetime
                        timeout = int(time.time()) + int(list_ip[j]['Timeout'])
                        timeout_str = datetime.fromtimestamp(timeout).strftime('%Y-%m-%d %H:%M:%S')
                        list_ip[j]["expiry_date"] = timeout_str
                    list_ip[j]["stype"] = '1'
                else:
                    #系统防火墙的IP规则
                    list_ip[j]["stype"] = '0'

                for ip_rule in rule_db.get(list_ip[j]['Address'], []):
                    if (ip_rule['address'] == list_ip[j]['Address'] and
                            ip_rule['types'] == list_ip[j]['Strategy'] and
                            ip_rule['chain'] == list_ip[j]['Chain']):
                        list_ip[j]['id'] = ip_rule['id']
                        list_ip[j]['sid'] = ip_rule['sid']
                        list_ip[j]['brief'] = ip_rule['brief']
                        list_ip[j]['addtime'] = ip_rule['addtime']

                        if "domain" in ip_rule:
                            list_ip[j]['domain'] = ip_rule['domain']
                        break
                if get.query != "":
                    if get.query in list_ip[j]['brief'] or get.query in list_ip[j]['Address']:
                        new_list.append(list_ip[j])

            if len(new_list) > 0 or get.query != "":
                sort_data =  sorted(new_list, key=lambda x: x['addtime'], reverse=True)
            else:
                sort_data = sorted(list_ip, key=lambda x: x['addtime'], reverse=True)

            if get.query == "":
                cache.set(cache_key, sort_data, 86400)
        else:   #缓存流程
            new_list = []
            sort_data = data
            for j in range(len(sort_data)):
                if get.query != "":
                    if get.query in sort_data[j]['Address'] or get.query in sort_data[j]['brief']:
                        new_list.append(sort_data[j])
                elif get.chain != "ALL" and sort_data[j]['Chain'] == get.chain:
                    new_list.append(sort_data[j])

            if len(new_list) > 0 or get.query != "" or get.chain != "ALL":
                sort_data = sorted(new_list, key=lambda x: x['addtime'], reverse=True)

        from mod.project.ssh.base import SSHbase
        if get.export == "1":
            get.row = len(sort_data)
        page_data = self.return_page(sort_data, get)
        page_data["data"] = SSHbase.return_area(page_data["data"], "Address")
        return page_data

    # 2024/3/27 上午 12:11 构造端口转发规则返回数据
    def structure_forward_return_data(self, list_forward, rule_db, get):
        '''
            @name 构造端口转发规则返回数据
            @author wzz <2024/3/27 上午 12:11>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        cache_key = "port_forward_list"
        from BTPanel import cache
        data = cache.get(cache_key)
        if data:
            new_list = []
            sort_data = data
            for j in range(len(sort_data)):
                if get.query != "":
                    if get.query in sort_data[j]['S_Address'] or get.query in sort_data[j]['S_Port'] or get.query in \
                            sort_data[j]['T_Address'] or get.query in sort_data[j]['T_Port'] or get.query in \
                            sort_data[j]['brief']:
                        new_list.append(sort_data[j])

            if len(new_list) > 0 or get.query != "":
                sort_data = sorted(new_list, key=lambda x: x['addtime'], reverse=True)
        else:
            new_list = []
            for j in range(len(list_forward)):
                list_forward[j]['id'] = 0
                list_forward[j]['brief'] = ""
                list_forward[j]['addtime'] = "--"

                for i in range(len(rule_db)):
                    if (rule_db[i]['T_Address'] == list_forward[j]['T_Address'] and
                            rule_db[i]['S_Port'] == list_forward[j]['S_Port'] and
                            rule_db[i]['T_Port'] == list_forward[j]['T_Port'] and
                            rule_db[i]['Protocol'].upper() == list_forward[j]['Protocol'].upper()
                        ):
                        list_forward[j]['id'] = rule_db[i]['id']
                        list_forward[j]['brief'] = rule_db[i]['brief']
                        list_forward[j]['addtime'] = rule_db[i]['addtime']
                        break

                if get.query != "":
                    if (get.query in list_forward[j]['brief'] or get.query in list_forward[j][
                        'S_Address'] or get.query in
                            list_forward[j]['S_Port'] or
                            get.query in list_forward[j]['T_Address'] or get.query in list_forward[j]['T_Port']):
                        new_list.append(list_forward[j])

            if len(new_list) > 0 or get.query != "":
                sort_data = sorted(new_list, key=lambda x: x['addtime'], reverse=True)
            else:
                sort_data = sorted(list_forward, key=lambda x: x['addtime'], reverse=True)

            if get.query == "":
                cache.set(cache_key, sort_data, 86400)

        return self.return_page(sort_data, get)

    # 2024/3/25 上午 11:05 获取所有端口规则列表
    def port_rules_list(self, get):
        '''
            @name 获取所有端口规则列表
            @author wzz <2024/3/25 上午 11:06>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return list[dict{}...]
        '''
        get.chain = get.get('chain/s', 'ALL')
        get.query = get.get('query/s', '')
        get.p = get.get('p', 1)
        get.row = get.get('row', 20)
        get.export = get.get('export/s', '0')  # 是否导出数据 0非导出 1导出

        rule_db = self.get_port_db(get)

        if get.chain == "INPUT":
            list_port = self.firewall.list_input_port()
        elif get.chain == "OUTPUT":
            list_port = self.firewall.list_output_port()
        else:
            list_port = self.firewall.list_port()

        return self.structure_port_return_data(list_port, rule_db, get)

    # 2024/3/26 下午 3:17 导出规则
    def export_rules(self, get):
        '''
            @name 导出规则
            @author wzz <2024/3/26 下午 3:17>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        get.rule = get.get('rule/s', 'port')
        get.export = "1"
        if get.rule == "port":
            return self.export_port_rules(get)
        elif get.rule == "ip":
            return self.export_ip_rules(get)
        else:
            return self.export_port_forward(get)

    # 2024/3/26 下午 3:18 导入规则
    def import_rules(self, get):
        '''
            @name 导入规则
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        # 2024/4/17 下午4:47 检查防火墙状态，如果未启动则不允许设置导入规则
        if not self.get_firewall_status():
            return public.returnMsg(False, '请先启动防火墙后再导入规则！')

        get.rule = get.get('rule/s', 'port')
        if get.rule == "port":
            return self.import_port_rules(get)
        elif get.rule == "ip":
            return self.import_ip_rules(get)
        else:
            return self.import_port_forward(get)

    # 2024/3/26 下午 2:38 导出所有端口规则
    def export_port_rules(self, get):
        '''
            @name 导出所有端口规则
            @author wzz <2024/3/26 下午 2:39>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        get.chain = get.get('chain/s', 'all')

        if get.chain == "INPUT":
            file_name = "input_port_rules_{}".format(int(time.time()))
        elif get.chain == "OUTPUT":
            file_name = "output_port_rules_{}".format(int(time.time()))
        else:
            file_name = "port_rules_{}".format(int(time.time()))

        data = self.port_rules_list(get)['data']
        if not data:
            return public.returnMsg(False, '没有规则无法导出')
        if not os.path.exists(self.config_path):
            os.makedirs(self.config_path, exist_ok=True)
        file_path = "{}/{}.json".format(self.config_path, file_name)

        public.writeFile(file_path, public.GetJson(data))
        public.WriteLog("系统防火墙", "导出端口规则")
        return public.returnMsg(True, file_path)

    # 2024/3/26 下午 2:41 导入端口规则
    def import_port_rules(self, get):
        '''
            @name 导入端口规则
            @author wzz <2024/3/26 下午 2:58>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        get.file = get.get('file/s', '')

        if not get.file:
            return public.returnMsg(False, '文件不能为空')

        if not os.path.exists(get.file):
            return public.returnMsg(False, '文件不存在')

        try:
            data = public.readFile(get.file)
            if "|" in data and not "{" in data:
                get.rule_name = "port_rule"
                return self.import_rules_old(get)

            data = json.loads(data)
            # 2024/4/10 下午2:51 反转数据
            data.reverse()
        except:
            return public.returnMsg(False, '文件内容异常或格式错误')

        args = public.dict_obj()
        for item in data:
            args.operation = 'add'
            args.protocol = item['Protocol']
            args.port = item['Port']
            args.strategy = item['Strategy']
            args.chain = item['Chain']
            args.address = item.get('Address', 'all')
            args.brief = item.get('brief', '')
            args.reload = "0"

            self.set_port_rule(args)

        if self._isFirewalld:
            self.firewall.reload()

        return public.returnMsg(True, '导入成功')

    # 2024/5/14 上午10:27 调用旧的导入规则方法
    def import_rules_old(self, get):
        '''
            @name 调用旧的导入规则方法
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        try:
            from safeModel.firewallModel import main as firewall
            firewall_obj = firewall()
            get.file_name = get.file.split("/")[-1]
            firewall_obj.import_rules(get)

            return public.returnMsg(True, '导入成功')
        except Exception as e:
            return public.returnMsg(False, str(e))

    # 2024/3/26 上午 9:30 处理多个ip以换行的方式添加/删除
    def set_nline_port_ip(self, get):
        '''
            @name 处理多个ip以换行的方式添加/删除
            @author wzz <2024/3/26 上午 9:32>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        address = get.address.split("\n")
        failed_list = []
        for addr in address:
            if not public.checkIp(addr):
                return public.returnMsg(False, '目标地址格式错误')

            get.address = addr
            if get.chain == "INPUT":
                result = self.input_port(get)
            else:
                result = self.output_port(get)

            if not result['status']:
                failed_list.append({
                    "address": addr,
                    "msg": result['msg']
                })
        if len(failed_list) > 0:
            return public.returnMsg(True, '设置成功,以下规则设置失败:{}'.format(failed_list))

        # if self._isFirewalld:
        #     self.firewall.reload()

        return public.returnMsg(True, '设置成功')

    # 2024/3/26 上午 9:30 处理多个ip以逗号的方式添加/删除
    def set_tline_port_ip(self, get):
        '''
            @name 处理多个ip以逗号的方式添加
            @author wzz <2024/3/26 上午 9:32>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        address = get.address.split(",")
        failed_list = []
        for addr in address:
            if not public.checkIp(addr):
                return public.returnMsg(False, '目标地址格式错误')

            get.address = addr
            if get.chain == "INPUT":
                result = self.input_port(get)
            else:
                result = self.output_port(get)

            if not result['status']:
                failed_list.append({
                    "address": addr,
                    "msg": result['msg']
                })
        if len(failed_list) > 0:
            return public.returnMsg(True, '设置成功,以下规则设置失败:{}'.format(failed_list))

        # if self._isFirewalld:
        #     self.firewall.reload()

        return public.returnMsg(True, '设置成功')

    # 2024/3/26 上午 9:34 处理192.168.1.10-192.168.1.20这种范围ip的添加/删除
    def set_range_port_ip(self, get):
        '''
            @name 处理192.168.1.10-192.168.1.20这种范围ip的添加/删除
            @author wzz <2024/3/26 上午 9:35>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        address = self.firewall.handle_ip_range(get.address)
        failed_list = []
        for addr in address:
            get.address = addr
            if get.chain == "INPUT":
                result = self.input_port(get)
            else:
                result = self.output_port(get)

            if not result['status']:
                failed_list.append({
                    "address": addr,
                    "msg": result['msg']
                })
        if len(failed_list) > 0:
            return public.returnMsg(True, '设置成功,以下规则设置失败:{}'.format(failed_list))

        # if self._isFirewalld:
        #     self.firewall.reload()

        return public.returnMsg(True, '设置成功')

    # 2024/3/25 下午 6:27 设置端口规则
    def set_port_rule(self, get):
        '''
            @name 设置端口规则
            @author wzz <2024/3/25 下午 6:28>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        # 2024/4/17 下午4:47 检查防火墙状态，如果未启动则不允许设置端口规则
        if not self.get_firewall_status():
            return public.returnMsg(False, '请先启动防火墙后再设置规则！')

        get.operation = get.get('operation/s', 'add')
        get.protocol = get.get('protocol/s', 'tcp')
        get.address = get.get('address/s', 'all')
        get.port = get.get('port/s', '')
        get.strategy = get.get('strategy/s', 'accept')
        get.chain = get.get('chain/s', 'INPUT')
        get.reload = get.get('reload/s', "1")
        get.brief = get.get('brief/s', '')

        if get.address == "Anywhere" or get.address == "":
            get.address = "all"

        if get.protocol == "all":
            get.protocol = "tcp/udp"

        if get.port == "":
            return public.returnMsg(False, '目标端口不能为空')

        if get.address != "all" and "," in get.address:
            import copy
            args = copy.deepcopy(get)
            address_list = get.address.split(",")
            for address in address_list:
                args.address = address
                result = self.more_prot_rule(args)
                if not result['status']:
                    return result
        elif get.address != "all" and "\n" in get.address:
            import copy
            args = copy.deepcopy(get)
            address_list = get.address.split("\n")
            for address in address_list:
                args.address = address
                result = self.more_prot_rule(args)
                if not result['status']:
                    return result
        else:
            result = self.more_prot_rule(get)
            if not result['status']:
                return result

        if self._isFirewalld and get.reload == "1":
            self.firewall.reload()

        cache_key = "firewall_info"
        from BTPanel import cache
        data = cache.get(cache_key)
        if data: cache.delete(cache_key)
        cache_key = "port_rules_list"
        data = cache.get(cache_key)
        if data: cache.delete(cache_key)

        public.WriteLog("系统防火墙", "设置端口规则：{}".format(get.port))
        return public.returnMsg(True, '设置成功')

    # 2024/3/29 下午 4:04 处理多个ip的端口规则情况
    def more_prot_rule(self, get):
        '''
            @name 处理多个ip的端口规则情况
            @author wzz <2024/3/29 下午 4:02>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        if get.port.find(",") != -1:
            import copy
            args = copy.deepcopy(get)
            port_list = get.port.split(",")
            for port in port_list:
                args.port = port
                result = self.exec_port_rule(args)
                if not result['status']:
                    return result
            return public.returnMsg(True, '设置成功')
        else:
            return self.exec_port_rule(get)

    # 2024/3/28 下午 6:29 执行端口设置
    def exec_port_rule(self, get):
        '''
            @name 执行端口设置
            @author wzz <2024/3/28 下午 6:29>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        if get.operation == "add" and not self.check_port_exist(get):
            return public.returnMsg(False, '端口{}已存在，请勿重复添加'.format(get.port))

        self.set_port_db(get)

        # 2024/3/25 下午 8:23 处理多个ip的情况,例如出现每行一个ip
        if get.address != "all" and "\n" in get.address:
            return self.set_nline_port_ip(get)
        elif get.address != "all" and "-" in get.address:
            return self.set_range_port_ip(get)
        elif get.address != "all" and "," in get.address:
            return self.set_tline_port_ip(get)
        elif get.address != "all" and "/" in get.address:
            if get.chain == "INPUT":
                result = self.input_port(get)
            else:
                result = self.output_port(get)
        elif get.address != "all" and not public.checkIp(get.address) and not public.is_ipv6(get.address):
            return public.returnMsg(False, '指定IP地址格式错误')
        else:
            if get.chain == "INPUT":
                result = self.input_port(get)
            else:
                result = self.output_port(get)

        return result

    # 2024/5/14 上午10:40 前置检测ip是否合法
    def check_ips(self, get):
        '''
            @name 前置检测ip是否合法
            @author wzz <2024/5/14 上午10:40>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        if get.address != "all" and "\n" in get.address:
            address = get.address.split("\n")
            for addr in address:
                if addr != "all" and not public.checkIp(addr) and not public.is_ipv6(addr):
                    return public.returnMsg(False, '指定IP地址格式错误')
        elif get.address != "all" and "," in get.address:
            address = get.address.split(",")
            for addr in address:
                if addr != "all" and not public.checkIp(addr) and not public.is_ipv6(addr):
                    return public.returnMsg(False, '指定IP地址格式错误')
        else:
            if get.address != "all" and not public.checkIp(get.address) and not public.is_ipv6(get.address):
                return public.returnMsg(False, '指定IP地址格式错误')

        return public.returnMsg(True, 'ok')

    # 2024/3/27 上午 9:37 修改端口规则
    def modify_port_rule(self, get):
        '''
            @name 修改端口规则
            @author wzz <2024/3/27 上午 9:38>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        # 2024/4/17 下午4:47 检查防火墙状态，如果未启动则不允许设置规则
        if not self.get_firewall_status():
            return public.returnMsg(False, '请先启动防火墙后再设置规则！')
        get.old_data = get.get('old_data/s', '')
        get.new_data = get.get('new_data/s', '')

        if get.old_data == "":
            return public.returnMsg(False, '请传入old_data')

        if get.new_data == "":
            return public.returnMsg(False, '请传入new_data')

        get.old_data = json.loads(get.old_data)
        get.new_data = json.loads(get.new_data)

        args1 = public.dict_obj()
        args1.operation = 'remove'
        args1.port = get.old_data['Port']
        args1.protocol = get.old_data['Protocol']
        args1.address = get.old_data['Address']
        args1.strategy = get.old_data['Strategy']
        args1.chain = get.old_data['Chain']
        args1.id = get.old_data['id']
        args1.sid = get.old_data['sid']
        args1.reload = "0"
        self.set_port_rule(args1)

        args2 = public.dict_obj()
        args2.operation = 'add'
        args2.port = get.new_data['port']
        args2.protocol = get.new_data['protocol']
        args2.address = get.new_data['address'] if "address" in get.new_data else "all"
        args2.strategy = get.new_data['strategy']
        args2.chain = get.new_data['chain']
        args2.brief = get.new_data['brief'] if 'brief' in get.new_data else ""
        args2.reload = "1"
        self.set_port_rule(args2)

        return public.returnMsg(True, '修改成功')

    # 2024/3/27 下午 4:03 修改域名端口规则
    def modify_domain_port_rule(self, get):
        '''
            @name 修改域名端口规则
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        # 2024/4/17 下午4:47 检查防火墙状态，如果未启动则不允许设置设置规则
        if not self.get_firewall_status():
            return public.returnMsg(False, '请先启动防火墙后再设置规则！')
        get.old_data = get.get('old_data/s', '')
        get.new_data = get.get('new_data/s', '')

        if get.old_data == "":
            return public.returnMsg(False, '请传入old_data')

        if get.new_data == "":
            return public.returnMsg(False, '请传入new_data')

        get.old_data = json.loads(get.old_data)
        get.new_data = json.loads(get.new_data)

        address = self.get_a_ip(get.new_data['domain'])

        if address == "":
            return public.returnMsg(False, '域名: 【{}】解析失败'.format(get.domain))

        args1 = public.dict_obj()
        args1.operation = 'remove'
        args1.port = get.old_data['Port']
        args1.protocol = get.old_data['Protocol']
        args1.address = get.old_data['Address']
        args1.strategy = get.old_data['Strategy']
        args1.chain = get.old_data['Chain']
        args1.id = get.old_data['id']
        args1.sid = get.old_data['sid']
        self.set_port_rule(args1)

        args2 = public.dict_obj()
        args2.operation = 'add'
        args2.port = get.new_data['port']
        args2.protocol = get.new_data['protocol']
        args2.address = address
        args2.strategy = get.new_data['strategy']
        args2.chain = get.new_data['chain']
        args2.brief = get.new_data['brief'] if "brief" in get.new_data else ""
        args2.domain = get.new_data['domain']
        self.set_port_rule(args2)

        if self._isFirewalld:
            self.firewall.reload()

        return public.returnMsg(True, '修改成功')

    # 2024/3/26 下午 5:10 设置域名端口规则
    def set_domain_port_rule(self, get):
        '''
            @name 设置域名端口规则
            @author wzz <2024/3/26 下午 5:11>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        # 2024/4/17 下午4:47 检查防火墙状态，如果未启动则不允许设置规则
        if not self.get_firewall_status():
            return public.returnMsg(False, '请先启动防火墙后再设置规则！')

        public.set_module_logs('设置域名端口规则', 'set_domain_port_rule', 1)
        get.operation = get.get('operation/s', 'add')
        get.protocol = get.get('protocol/s', 'tcp')
        get.domain = get.get('domain/s', '')
        get.port = get.get('port/s', '')
        get.strategy = get.get('strategy/s', 'accept')
        get.chain = get.get('chain/s', 'INPUT')

        if get.domain == "":
            return public.returnMsg(False, '目标域名不能为空')

        if get.port == "":
            return public.returnMsg(False, '目标端口不能为空')

        if not public.is_domain(get.domain):
            return public.returnMsg(False, '目标域名格式错误')

        if "|" in get.domain:
            get.domain = get.domain.split("|")[0]

        address = self.get_a_ip(get.domain)

        if address == "":
            return public.returnMsg(False, '域名: 【{}】解析失败'.format(get.domain))

        get.address = address
        self.set_port_db(get)

        if get.chain == "INPUT":
            result = self.input_port(get)
        else:
            result = self.output_port(get)

        if result['status'] and self._isFirewalld:
            self.firewall.reload()

        return result

    # 2024/5/13 下午4:46 添加端口规则到指定数据库
    def add_port_db(self, get, protocol, addtime, domain):
        '''
            @name 添加端口规则到指定数据库
            @author wzz <2024/5/13 下午4:46>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        add_sid = public.M('firewall_new').add(
            'ports,brief,protocol,address,types,addtime,domain,sid,chain',
            (
                get.port, public.xsssec(get.brief), protocol, get.address, get.strategy, addtime, domain, 0,
                get.chain)
        )

        if get.domain != "":
            domain_sid = public.M('firewall_domain').add(
                'types,domain,port,address,brief,addtime,sid,protocol,domain_total',
                (get.strategy, domain, get.port, get.address, public.xsssec(get.brief),
                 addtime, add_sid, get.protocol, get.domain)
            )
            public.M('firewall_new').where("id=?", (add_sid,)).save('sid', domain_sid)
            self.check_resolve_crontab()

    # 2024/5/13 下午4:49 从指定数据库删除端口规则
    def remove_port_db(self, get, protocol, addtime, domain):
        '''
            @name 从指定数据库删除端口规则
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        public.M('firewall_new').where("ports=? and protocol=? and address=? and types=? and chain=?", (
            get.port, protocol, get.address, get.strategy, get.chain
        )).delete()
        get.domain = get.get('domain/s', '')
        if get.domain != "":
            public.M('firewall_domain').where("domain=?", (get.domain)).delete()

        self.remove_resolve_crontab()

    # 2024/3/26 下午 5:52 添加/删除数据库的端口规则
    def set_port_db(self, get):
        '''
            @name 添加/删除数据库的端口规则
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        if get.operation == "add":
            # 检测端口是否已经添加过
            query_result = public.M('firewall_new').where(
                'ports=? and address=? and protocol=? and types=? and chain=?',
                (get.port, get.address, get.protocol, get.strategy, get.chain)
            ).find()

            if not query_result:
                get.domain = get.get('domain/s', '')
                domain = "{}|{}".format(get.domain, get.address) if get.domain != "" else ""
                addtime = time.strftime('%Y-%m-%d %X', time.localtime())

                if get.protocol == "tcp/udp" and self._isFirewalld:
                    self.add_port_db(get, "tcp", addtime, domain)
                    self.add_port_db(get, "udp", addtime, domain)
                else:
                    self.add_port_db(get, get.protocol, addtime, domain)
        else:
            query_result = public.M('firewall_new').where(
                'ports=? and address=? and protocol=? and types=? and chain=?',
                (get.port, get.address, get.protocol, get.strategy, get.chain)
            ).find()
            if query_result:
                if get.protocol == "tcp/udp" and self._isFirewalld:
                    self.remove_port_db(get, "tcp", query_result['addtime'], query_result['domain'])
                    self.remove_port_db(get, "udp", query_result['addtime'], query_result['domain'])
                else:
                    self.remove_port_db(get, get.protocol, query_result['addtime'], query_result['domain'])

    # 2024/3/26 下午 11:23 添加/删除数据库的ip规则
    def set_ip_db(self, get):
        '''
            @name 添加/删除数据库的ip规则
            @author wzz <2024/3/26 下午 11:24>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        if get.operation == "add":
            get.domain = get.get('domain/s', '')
            domain = "{}|{}".format(get.domain, get.address) if get.domain != "" else ""
            query_result = public.M('firewall_ip').where("address=? and types=? and domain=? and chain=?",
                                                         (get.address, get.strategy, domain, get.chain)).find()

            if not query_result:
                addtime = time.strftime('%Y-%m-%d %X', time.localtime())
                self._add_sid = public.M('firewall_ip').add(
                    'address,types,brief,addtime,domain,sid,chain',
                    (get.address, get.strategy, public.xsssec(get.brief), addtime, domain, 0, get.chain)
                )

                if get.domain != "":
                    domain_sid = public.M('firewall_domain').add(
                        'types,domain,port,address,brief,addtime,sid,protocol,domain_total',
                        (get.strategy, domain, '', get.address, public.xsssec(get.brief), addtime, self._add_sid, '',
                         get.domain)
                    )
                    public.M('firewall_ip').where("id=?", (self._add_sid,)).save('sid', domain_sid)
                    self.check_resolve_crontab()
        else:
            get.address = get.get("address/s", '')
            get.strategy = get.get("strategy/s", '')
            if get.address == "":
                return public.returnMsg(False, '请传入id')
            public.M('firewall_ip').where("address=? and types=? and chain=?", (get.address, get.strategy, get.chain)).delete()
            get.domain = get.get('domain/s', '')
            if get.domain != "":
                public.M('firewall_domain').where("domain=?", (get.domain)).delete()

            self.remove_resolve_crontab()

    # 2024/3/26 下午 11:40 添加/删除数据库的端口转发规则
    def set_forward_db(self, get):
        '''
            @name 添加/删除数据库的端口转发规则
            @author wzz <2024/3/26 下午 11:40>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        if get.operation == "add":
            query_result = public.M('firewall_forward').where("S_Port=? and T_Address=? and T_Port=? and Protocol=?", (
                get.S_Port, get.T_Address, get.T_Port, get.protocol
            )).find()

            if not query_result:
                get.brief = get.get('brief/s', '')
                addtime = time.strftime('%Y-%m-%d %X', time.localtime())
                self._add_sid = public.M('firewall_forward').add(
                    'S_Port,T_Address,T_Port,Protocol,Family,addtime,brief',
                    (get.S_Port, get.T_Address, get.T_Port, get.protocol, "ipv4", addtime, get.brief)
                )
        else:
            public.M('firewall_forward').where(
                "S_Port=? and T_Address=? and T_Port=? and Protocol=?",
                (get.S_Port, get.T_Address, get.T_Port, get.protocol)
            ).delete()

    # 2024/3/25 下午 6:55 入站端口规则
    def input_port(self, get):
        '''
            @name 入站端口规则
            @param "data":{"参数名":""} <数据类型> 参数描述 dabao
            @return list[dict{}...]
        '''
        info = {
            "Port": get.port,
            "Protocol": get.protocol.lower(),
            "Strategy": get.strategy.lower(),
            "Family": "ipv4",
        }

        if ":" in get.address:
            info["Family"] = "ipv6"

        if get.address != "all":
            info["Address"] = get.address
            result = self.firewall.rich_rules(info=info, operation=get.operation)
        elif get.address == "all" and get.strategy == "drop":
            result = self.firewall.rich_rules(info=info, operation=get.operation)
        else:
            result = self.firewall.input_port(info=info, operation=get.operation)

        return result

    # 2024/3/25 下午 6:56 出站端口规则
    def output_port(self, get):
        '''
            @name 出站端口规则
            @author wzz <2024/3/25 下午 6:56>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        info = {
            "Port": get.port,
            "Protocol": get.protocol.lower(),
            "Strategy": get.strategy.lower(),
            "Priority": "0",
            "Family": "ipv4",
        }

        if ":" in get.address:
            info["Family"] = "ipv6"

        if get.address != "all":
            info["Address"] = get.address
            result = self.firewall.output_rich_rules(info=info, operation=get.operation)
        else:
            result = self.firewall.output_port(info=info, operation=get.operation)

        return result

    # 2024/3/26 上午 9:40 处理多个ip的情况,例如出现每行一个ip
    def set_nline_ip_rule(self, get):
        '''
            @name 处理多个ip的情况,例如出现每行一个ip
            @author wzz <2024/3/26 上午 9:40>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        address = get.address.split("\n")
        failed_list = []
        import copy
        for addr in address:
            verify_addr = addr.split("/")[0]
            if not public.is_ipv4(verify_addr) and not public.is_ipv6(verify_addr):
                continue

            args = copy.deepcopy(get)
            args.address = addr
            args.family = "ipv4" if ":" not in addr else "ipv6"

            if self.check_is_user_ip(args):
                continue

            if get.operation == "add" and not self.check_ip_exist(args):
                continue

            self.set_ip_db(args)

            info = {
                "Address": args.address,
                "Family": args.family,
                "Strategy": args.strategy,
                "Priority": args.priority,
                "Zone": get.zone.lower(),
            }

            result = self.iptables.rich_rules(info=info, operation=get.operation,chain=get.chain)

            if not result['status']:
                failed_list.append({
                    "address": addr,
                    "msg": result['msg']
                })
        if len(failed_list) > 0:
            return public.returnMsg(True, '设置成功,以下规则设置失败:{}'.format(failed_list))

        if self._isFirewalld:
            self.firewall.reload()

        return public.returnMsg(True, '设置成功')

    # 2024/3/26 上午 9:40 处理多个ip的情况,例如出现逗号隔开ip
    def set_tline_ip_rule(self, get):
        '''
            @name 处理多个ip的情况,例如出现逗号隔开ip
            @author wzz <2024/3/26 上午 9:40>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        address = get.address.split(",")
        failed_list = []
        import copy
        for addr in address:
            if "/" in addr:
                a_rgs = copy.deepcopy(get)
                a_rgs.address = addr
                self.set_mask_ip_rule(get)
                del a_rgs
                continue
            if "-" in addr:
                a_rgs = copy.deepcopy(get)
                a_rgs.address = addr
                self.set_range_ip_rule(a_rgs)
                del a_rgs
                continue
            if not public.checkIp(addr):
                return public.returnMsg(False, '目标地址格式错误')

            args = copy.deepcopy(get)
            args.address = addr

            if self.check_is_user_ip(args):
                continue

            if get.operation == "add" and not self.check_ip_exist(args):
                continue

            self.set_ip_db(args)

            info = {
                "Address": args.address,
                "Family": args.family,
                "Strategy": args.strategy,
                "Priority": args.priority,
                "Zone": get.zone.lower(),
            }

            result = self.iptables.rich_rules(info=info, operation=get.operation, chain=get.chain)

            if not result['status']:
                failed_list.append({
                    "address": addr,
                    "msg": result['msg']
                })
        if len(failed_list) > 0:
            return public.returnMsg(True, '设置成功,以下规则设置失败:{}'.format(failed_list))

        if self._isFirewalld:
            self.firewall.reload()

        return public.returnMsg(True, '设置成功')

    # 2024/3/26 上午 9:43 处理192.168.1.10-192.168.1.20这种范围ip的添加/删除
    def set_range_ip_rule(self, get):
        '''
            @name 处理192.168.1.10-192.168.1.20这种范围ip的添加/删除
            @author wzz <2024/3/26 上午 9:43>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        address = self.firewall.handle_ip_range(get.address)
        failed_list = []
        import copy
        for addr in address:
            args = copy.deepcopy(get)
            args.address = addr

            if self.check_is_user_ip(args):
                continue

            if get.operation == "add" and not self.check_ip_exist(args):
                continue

            self.set_ip_db(args)

            info = {
                "Address": args.address,
                "Family": args.family,
                "Strategy": args.strategy,
                "Priority": args.priority,
                "Zone": get.zone.lower(),
            }

            result = self.iptables.rich_rules(info=info, operation=get.operation, chain=get.chain)

            if not result['status']:
                failed_list.append({
                    "address": addr,
                    "msg": result['msg']
                })
        if len(failed_list) > 0:
            return public.returnMsg(True, '设置成功,以下规则设置失败:{}'.format(failed_list))

        if self._isFirewalld:
            self.firewall.reload()

        return public.returnMsg(True, '设置成功')

    # 2024/3/26 上午 9:46 设置带掩码的ip段
    def set_mask_ip_rule(self, get):
        '''
            @name 设置带掩码的ip段
            @author wzz <2024/3/26 上午 9:47>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        if get.operation == "add" and not self.check_ip_exist(get):
            return public.returnMsg(False, '目标地址{}已存在，请勿重复添加'.format(get.address))

        self.set_ip_db(get)
        info = {
            "Address": get.address,
            "Family": get.family,
            "Strategy": get.strategy,
            "Priority": get.priority,
            "Zone": get.zone.lower(),
        }

        if get.chain == "INPUT":
            result = self.firewall.rich_rules(info=info, operation=get.operation)
        else:
            result = self.firewall.output_rich_rules(info=info, operation=get.operation)

        if result['status'] and self._isFirewalld:
            self.firewall.reload()

        return result

    # 2024/4/9 下午11:31 检查是否会自己的ip，如果是则返回
    def check_is_user_ip(self, get):
        '''
            @name
            @author wzz <2024/4/9 下午11:31>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        # 2024/3/26 下午 11:27 处理用户当前的远程ip，如果添加的ip与此ip一直则返回
        try:
            from flask import request
            user_ip = request.remote_addr
            if user_ip in get.address:
                return True
            return False
        except:
            return False
        
    # 2024/3/25 下午 7:16 设置ip规则
    def set_ip_rule(self, get):
        '''
            @name 设置ip规则
            @author wzz <2024/3/25 下午 7:16>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        # 2024/4/17 下午4:47 检查防火墙状态，如果未启动则不允许设置规则
        if not self.get_firewall_status():
            return public.returnMsg(False, '请先启动防火墙后再设置规则！')

        get.operation = get.get('operation/s', 'add')
        get.address = get.get('address/s', '')
        get.strategy = get.get('strategy/s', 'accept')
        get.chain = get.get('chain/s', 'INPUT')
        get.family = get.get('family/s', 'ipv4')
        get.priority = get.get('priority/s', '0')
        get.reload = get.get('reload/s', "1")
        get.zone = get.get('zone', "public")
        get.timeout = get.get('timeout/d', 0)
        get.stype = get.get('stype/d', 1)  #1托管的IPTABLES   0原生系统防火墙

        if get.address == "":
            return public.returnMsg(False, '目标ip不能为空')
        if not get.strategy.lower() in ["accept", "drop"]:
            return public.returnMsg(False, "设置规则失败:{}".format("不支持的策略类型"))
        if get.chain not in ["INPUT", "OUTPUT"]:
            return public.returnMsg(False, '不支持的链类型')

        option_result = self.ip_rule_option(get)

        cache_key = "firewall_info"
        from BTPanel import cache
        data = cache.get(cache_key)
        if data: cache.delete(cache_key)
        cache_key = "ip_rules_list"
        data = cache.get(cache_key)
        if data: cache.delete(cache_key)

        return option_result

    # 2024/12/21 15:53 开始设置ip规则
    def ip_rule_option(self, get):
        '''
            @name 开始设置ip规则
        '''
        # 2024/3/25 下午 8:23 处理多个ip的情况,例如出现每行一个ip
        if get.address != "all" and "\n" in get.address:
            return self.set_nline_ip_rule(get)
        elif get.address != "all" and "," in get.address:
            return self.set_tline_ip_rule(get)
        elif get.address != "all" and "-" in get.address:
            return self.set_range_ip_rule(get)
        elif get.address != "all" and "/" not in get.address and not public.checkIp(get.address) and not public.is_ipv6(get.address):
            return public.returnMsg(False, '目标地址格式错误')
        else:
            if get.operation == "add" and get.strategy == "drop":
                if self.check_is_user_ip(get):
                    return public.returnMsg(False, '不能添加自己的ip')

            if get.operation == "add" and not self.check_ip_exist(get):
                return public.returnMsg(False, '目标地址{}已存在，请勿重复添加'.format(get.address))

            self.set_ip_db(get)

            info = {
                "Address": get.address,
                "Family": get.family,
                "Strategy": get.strategy.lower(),
                "Priority": get.priority.lower(),
                "Zone": get.zone.lower(),
                "Timeout": get.timeout  #过期时间 可以不传 默认为0永久
            }
            if get.stype == 1:  #接管的iptables规则
                result = self.iptables.rich_rules(info=info, operation=get.operation, chain=get.chain)
                if get.reload == "1":
                    public.ExecShell("systemctl reload BT-FirewallServices")
            else:               #原生系统防火墙的规则
                result = self.firewall.rich_rules(info=info, operation=get.operation)
                if get.reload == "1":
                    self.firewall.reload()

            public.WriteLog("系统防火墙", "设置IP规则：{}".format(get.address))
            return result

    # 2024/3/27 上午 9:44 修改ip规则
    def modify_ip_rule(self, get):
        '''
            @name 修改ip规则
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        # 2024/4/17 下午4:47 检查防火墙状态，如果未启动则不允许设置设置规则
        if not self.get_firewall_status():
            return public.returnMsg(False, '请先启动防火墙后再设置规则！')
        get.old_data = get.get('old_data/s', '')
        get.new_data = get.get('new_data/s', '')

        if get.old_data == "":
            return public.returnMsg(False, '请传入old_data')

        if get.new_data == "":
            return public.returnMsg(False, '请传入new_data')

        get.old_data = json.loads(get.old_data)
        get.new_data = json.loads(get.new_data)

        args1 = public.dict_obj()
        args1.operation = 'remove'
        args1.address = get.old_data['Address']
        args1.strategy = get.old_data['Strategy']
        args1.family = get.old_data['Family']
        args1.chain = get.old_data['Chain']
        args1.id = get.old_data['id']
        args1.sid = get.old_data['sid']
        args1.zone = get.old_data['Zone'] if "Zone" in get.old_data else "public"
        args1.reload = "0"
        args1.stype = get.old_data['stype']
        self.set_ip_rule(args1)

        args2 = public.dict_obj()
        args2.operation = 'add'
        args2.address = get.new_data['address']
        args2.strategy = get.new_data['strategy']
        args2.family = get.new_data['family']
        args2.chain = get.new_data['chain']
        args2.brief = get.new_data['brief']
        args2.zone = get.new_data['zone'] if "zone" in get.new_data else "public"
        args2.reload = "0"
        self.set_ip_rule(args2)

        if self._isFirewalld:
            self.firewall.reload()

        return public.returnMsg(True, '修改成功')

    # 2024/3/26 下午 5:18 设置域名ip规则
    def set_domain_ip_rule(self, get):
        '''
            @name 设置域名ip规则
            @author wzz <2024/3/26 下午 5:19>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        get.operation = get.get('operation/s', 'add')
        get.protocol = get.get('protocol/s', 'tcp')
        get.domain = get.get('domain/s', '')
        get.port = get.get('port/s', '')
        get.strategy = get.get('strategy/s', 'accept')
        get.chain = get.get('chain/s', 'INPUT')

        if get.domain == "":
            return public.returnMsg(False, '目标域名不能为空')

        if get.port == "":
            return public.returnMsg(False, '目标端口不能为空')

        if not public.is_domain(get.domain):
            return public.returnMsg(False, '目标域名格式错误')

        address = self.get_a_ip(get.domain)

        if address == "":
            return public.returnMsg(False, '域名: 【{}】解析失败'.format(get.domain))

        if not public.checkIp(get.address):
            return public.returnMsg(False, '目标地址格式错误')

        info = {
            "Address": address,
            "Family": get.family,
            "Strategy": get.strategy.lower(),
            "Priority": get.priority.lower(),
        }
        if get.chain == "INPUT":
            result = self.firewall.rich_rules(info=info, operation=get.operation)
        else:
            result = self.firewall.output_rich_rules(info=info, operation=get.operation)

        if result['status'] and self._isFirewalld:
            self.firewall.reload()

        return result

    # 2024/3/25 上午 11:18 获取所有ip规则列表
    def ip_rules_list(self, get):
        '''
            @name 获取所有ip规则列表
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return list[dict{}...]
        '''
        get.chain = get.get('chain/s', 'all')
        get.query = get.get('query/s', '')
        get.p = get.get('p', 1)
        get.row = get.get('row', 20)
        get.export = get.get('export/s', '0')  # 是否导出数据 0非导出 1导出

        return self.structure_ip_return_data(get)

    # 2024/3/26 下午 3:03 导出所有ip规则
    def export_ip_rules(self, get):
        '''
            @name 导出所有ip规则
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        get.chain = get.get('chain/s', 'all')

        if get.chain == "INPUT":
            file_name = "input_ip_rules_{}".format(int(time.time()))
        elif get.chain == "OUTPUT":
            file_name = "output_ip_rules_{}".format(int(time.time()))
        else:
            file_name = "ip_rules_{}".format(int(time.time()))

        data = self.ip_rules_list(get)["data"]
        if not data:
            return public.returnMsg(False, '没有规则无法导出')

        file_path = "{}/{}.json".format(self.config_path, file_name)
        if not os.path.exists(self.config_path):
            os.makedirs(self.config_path)
        public.writeFile(file_path, public.GetJson(data))
        public.WriteLog("系统防火墙", "导出ip规则")
        return public.returnMsg(True, file_path)

    # 2024/3/26 下午 3:05 导入ip规则
    def import_ip_rules(self, get):
        '''
            @name 导入ip规则
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        get.file = get.get('file/s', '')

        if not get.file:
            return public.returnMsg(False, '文件不能为空')

        if not os.path.exists(get.file):
            return public.returnMsg(False, '文件不存在')

        try:
            data = public.readFile(get.file)
            if "|" in data and not "{" in data:
                get.rule_name = "ip_rule"
                return self.import_rules_old(get)

            data = json.loads(data)
            # 2024/4/10 下午2:51 反转数据
            data.reverse()
        except:
            return public.returnMsg(False, '文件内容异常或格式错误')

        args = public.dict_obj()
        for item in data:
            args.operation = 'add'
            args.address = item['Address']
            args.strategy = item['Strategy']
            args.chain = item['Chain']
            args.family = item['Family']
            args.brief = item['brief']
            args.reload = "0"

            self.set_ip_rule(args)

        if self._isFirewalld:
            self.firewall.reload()

        return public.returnMsg(True, '导入成功')

    # 2024/3/25 下午 2:34 获取端口转发列表
    def port_forward_list(self, get):
        '''
            @name 获取端口转发列表
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return list[dict{}...]
        '''
        get.query = get.get('query/s', '')
        get.p = get.get('p', 1)
        get.row = get.get('row', 20)

        list_port_forward = self.iptables.list_port_forward()
        forward_db = self.get_forward_db(get)
        if type(list_port_forward) == list and type(forward_db) == list:
            return self.structure_forward_return_data(list_port_forward, forward_db, get)
        return self.return_page([], get)

    # 2024/3/26 下午 3:08 导出所有端口转发规则
    def export_port_forward(self, get):
        '''
            @name 导出所有端口转发规则
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        data = self.iptables.list_port_forward()
        if not data:
            return public.returnMsg(False, '没有规则无法导出')
        file_name = "port_forward_{}".format(int(time.time()))
        file_path = "{}/{}.json".format(self.config_path, file_name)

        public.writeFile(file_path, public.GetJson(data))
        public.WriteLog("系统防火墙", "导出端口转发规则")
        return public.returnMsg(True, file_path)

    # 2024/3/26 下午 3:10 导入端口转发规则
    def import_port_forward(self, get):
        '''
            @name 导入端口转发规则
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        get.file = get.get('file/s', '')

        if not get.file:
            return public.returnMsg(False, '文件不能为空')

        if not os.path.exists(get.file):
            return public.returnMsg(False, '文件不存在')

        try:
            data = public.readFile(get.file)
            if "|" in data and not "{" in data:
                get.rule_name = "trans_rule"
                return self.import_rules_old(get)

            data = json.loads(data)
            # 2024/4/10 下午2:51 反转数据
            data.reverse()
        except:
            return public.returnMsg(False, '文件内容异常或格式错误')

        args = public.dict_obj()
        for item in data:
            args.operation = 'add'
            args.protocol = item['Protocol']
            args.S_Address = item['S_Address']
            args.S_Port = item['S_Port']
            args.T_Address = item['T_Address']
            args.T_Port = item['T_Port']
            args.reload = "0"

            self.set_port_forward(args)

        if self._isFirewalld:
            self.firewall.reload()

        return public.returnMsg(True, '导入成功')

    # 2024/3/25 下午 3:43 设置端口转发
    def set_port_forward(self, get):
        '''
            @name 设置端口转发
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        # 2024/4/17 下午4:47 检查防火墙状态，如果未启动则不允许设置设置规则
        if not self.get_firewall_status():
            return public.returnMsg(False, '请先启动防火墙后再设置规则！')

        get.operation = get.get('operation/s', 'add')
        get.protocol = get.get('protocol/s', 'tcp')
        get.S_Address = get.get('S_Address/s', '')
        get.S_Port = get.get('S_Port/s', '')
        get.T_Address = get.get("T_Address/s", '')
        get.T_Port = get.get("T_Port/s", '')
        get.reload = get.get('reload/s', "1")

        if get.S_Port == "":
            return public.returnMsg(False, '源端口不能为空')
        # if get.T_Address == "":
        #     return public.returnMsg(False, '目标地址不能为空')
        if get.T_Port == "":
            return public.returnMsg(False, '目标端口不能为空')

        # 2024/3/25 下午 5:49 前置检测
        if get.operation == "add":
            check_ip_forward = self.firewall.check_ip_forward()
            if not check_ip_forward["status"]:
                return check_ip_forward

            if not self.check_forward_exist(get):
                return public.returnMsg(False, '端口转发规则已存在，请勿重复添加')

        self.set_forward_db(get)

        # 2024/3/25 下午 5:50 构造传参,调用底层方法设置端口转发
        if get.protocol == "tcp/udp" or get.protocol == "all":
            info = {"Family": "ipv4", "Protocol": "tcp", "S_Address": get.S_Address, "S_Port": get.S_Port,
                    "T_Address": get.T_Address, "T_Port": get.T_Port}
            result = self.iptables.port_forward(info=info, operation=get.operation)
            if not result['status']:
                return result

            info["Protocol"] = "udp"
            result = self.iptables.port_forward(info=info, operation=get.operation)
        else:
            info = {
                "Family": "ipv4",
                "Protocol": get.protocol,
                "S_Address": get.S_Address,
                "S_Port": get.S_Port,
                "T_Address": get.T_Address,
                "T_Port": get.T_Port,
            }
            result = self.iptables.port_forward(info=info, operation=get.operation)

        cache_key = "firewall_info"
        from BTPanel import cache
        data = cache.get(cache_key)
        if data: cache.delete(cache_key)
        cache_key = "port_forward_list"
        data = cache.get(cache_key)
        if data: cache.delete(cache_key)

        return result

    # 2024/3/27 上午 9:44 修改端口转发规则
    def modify_forward_rule(self, get):
        '''
            @name 修改端口转发规则
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        # 2024/4/17 下午4:47 检查防火墙状态，如果未启动则不允许设置规则
        if not self.get_firewall_status():
            return public.returnMsg(False, '请先启动防火墙后再设置规则！')

        get.old_data = get.get('old_data/s', '')
        get.new_data = get.get('new_data/s', '')

        if get.old_data == "":
            return public.returnMsg(False, '请传入old_data')

        if get.new_data == "":
            return public.returnMsg(False, '请传入new_data')

        get.old_data = json.loads(get.old_data)
        get.new_data = json.loads(get.new_data)

        args1 = public.dict_obj()
        args1.operation = 'remove'
        args1.S_Address = get.old_data['S_Address']
        args1.S_Port = get.old_data['S_Port']
        args1.T_Address = get.old_data['T_Address']
        args1.T_Port = get.old_data['T_Port']
        args1.protocol = get.old_data['Protocol']
        args1.id = get.old_data['id']
        args1.reload = "0"
        self.set_port_forward(args1)

        args2 = public.dict_obj()
        args2.operation = 'add'
        args2.S_Port = get.new_data['S_Port']
        args2.T_Address = get.new_data['T_Address']
        args2.T_Port = get.new_data['T_Port']
        args2.protocol = get.new_data['protocol']
        args2.brief = get.new_data['brief']
        args2.reload = "0"
        return self.set_port_forward(args2)
