#!/www/server/panel/pyenv/bin/python3.7
# coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2014-2099 宝塔软件(http://bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author: wzz <wzz@bt.cn>
# -------------------------------------------------------------------

# ------------------------------
# 系统防火墙模型 - iptables封装库
# ------------------------------

import re
import subprocess
import os
import sys

if "/www/server/panel/class" not in sys.path:
    sys.path.insert(0, "/www/server/panel/class")
import public
from firewallModel.app.appBase import Base


# import re

class Iptables(Base):
    def __init__(self):
        self.cmd_str = self._set_cmd_str()
        self.protocol = {
            "6": "tcp",
            "17": "udp",
            "0": "all"
        }

    def _set_cmd_str(self):
        return "iptables"

    # 2024/3/19 下午 5:00 获取系统防火墙的运行状态
    def status(self):
        '''
            @name 获取系统防火墙的运行状态
            @author wzz <2024/3/19 下午 5:00>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        return "running"

    # 2024/3/19 下午 5:00 获取系统防火墙的版本号
    def version(self):
        '''
            @name 获取系统防火墙的版本号
            @author wzz <2024/3/19 下午 5:00>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        try:
            result = public.ExecShell("iptables -v 2>&1|awk '{print $2}'|head -1")[0].replace("\n", "")
            if result == "":
                return "未知的iptables版本"
            return result
        except Exception as e:
            return "未知版本"

    # 2024/3/19 下午 5:00 启动防火墙
    def start(self):
        '''
            @name 启动防火墙
            @author wzz <2024/3/19 下午 5:00>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        return self._result(True, "当前系统防火墙为iptables，不支持设置状态")

    # 2024/3/19 下午 5:00 停止防火墙
    def stop(self):
        '''
            @name 停止防火墙
            @author wzz <2024/3/19 下午 5:00>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        return self._result(True, "当前系统防火墙为iptables，不支持停止")

    # 2024/3/19 下午 4:59 重启防火墙
    def restart(self):
        '''
            @name 重启防火墙
            @author wzz <2024/3/19 下午 4:59>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        return self._result(True, "当前系统防火墙为iptables，不支持重启")

    # 2024/3/19 下午 4:59 重载防火墙
    def reload(self):
        '''
            @name 重载防火墙
            @author wzz <2024/3/19 下午 4:59>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        return self._result(True, "当前系统防火墙为iptables，不支持重载")

    # 2024/3/19 下午 3:36 检查表名是否合法
    def check_table_name(self, table_name):
        '''
            @name 检查表名是否合法
            @param "table_name": "filter/nat/mangle/raw/security"
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        table_names = ['filter', 'nat', 'mangle', 'raw', 'security']
        if table_name not in table_names:
            return False
        return True

    # 2024/3/19 下午 3:55 解析规则列表输出，返回规则列表字典
    def parse_rules(self, stdout):
        '''
            @name 解析规则列表输出，返回规则列表字典
            @author wzz <2024/3/19 下午 3:53>
                字段含义:
                    "number": 规则编号，对应规则在链中的顺序。
                    "chain": 规则所属的链的名称。
                    "pkts": 规则匹配的数据包数量。
                    "bytes": 规则匹配的数据包字节数。
                    "target": 规则的目标动作，表示数据包匹配到该规则后应该执行的操作。
                    "prot": 规则适用的协议类型。
                    "opt": 规则的选项，包括规则中使用的匹配条件或特定选项。
                    "in": 规则匹配的数据包的输入接口。
                    "out": 规则匹配的数据包的输出接口。
                    "source": 规则匹配的数据包的源地址。
                    "destination": 规则匹配的数据包的目标地址。
                    "options": 规则的其他选项或说明，通常是规则中的注释或附加信息。

                protocol(port协议头中数字对应的协议类型):
                    0: 表示所有协议
                    1: ICMP（Internet 控制消息协议）
                    6: TCP（传输控制协议）
                    17: UDP（用户数据报协议）
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        lines = stdout.strip().split('\n')
        rules = []
        current_chain = None
        for line in lines:
            if line.startswith("Chain"):
                current_chain = line.split()[1]
            elif (line.startswith("target") or line.strip() == "" or "source" in line or
                  "Warning: iptables-legacy tables present" in line):
                # 过滤表头,空行,警告
                continue
            else:
                rule_info = line.split()
                rule = {
                    "number": rule_info[0],
                    "chain": current_chain,
                    "pkts": rule_info[1],
                    "bytes": rule_info[2],
                    "target": rule_info[3],
                    "prot": rule_info[4],
                    "opt": rule_info[5],
                    "in": rule_info[6],
                    "out": rule_info[7],
                    "source": rule_info[8],
                    "destination": rule_info[9],
                    "options": " ".join(rule_info[10:]).strip()
                }
                rules.append(rule)
        return rules

    # 2024/3/19 下午 3:02 列出指定表的指定链的规则
    def list_rules(self, parm):
        '''
            @name 列出指定表的指定链的规则
            @author wzz <2024/3/19 下午 3:02>
            @param
            @return
        '''
        try:
            if not self.check_table_name(parm['table']):
                return "错误： 不支持的表名."
            stdout = subprocess.check_output(
                [self.cmd_str, '-t', parm['table'], '-L', parm['chain_name'], '-nv', '--line-numbers'],
                stderr=subprocess.STDOUT, universal_newlines=True
            )
            return self.parse_rules(stdout)
        except Exception as e:
            return []

    # 2024/4/29 下午12:16 列出iptables中所有INPUT和OUTPUT的端口规则
    def list_port(self):
        '''
            @name 列出iptables中所有INPUT和OUTPUT的端口规则
            @return [{
                      "Protocol": "tcp",
                      "Port": "8888",
                      "Strategy": "accept",
                      "Family": "ipv4",
                      "Address": "all",
                      "Chain": "INPUT"
                   }]
        '''
        try:
            list_port = self.list_input_port() + self.list_output_port()
            for i in list_port:
                i["Strategy"] = i["Strategy"].lower()
            return list_port
        except Exception as e:
            return []

    # 2024/4/29 下午2:39 列出防火墙中所有的INPUT端口规则
    def list_input_port(self):
        '''
            @name 列出防火墙中所有的INPUT端口规则
            @return [{
                      "Protocol": "tcp",
                      "Port": "8888",
                      "Strategy": "accept",
                      "Family": "ipv4",
                      "Address": "all",
                      "Chain": "INPUT"
                   }]
        '''
        try:
            list_port = self.get_chain_port("INPUT")
            for i in list_port:
                i["Strategy"] = i["Strategy"].lower()
            return list_port
        except Exception as e:
            return []

    # 2024/4/29 下午2:39 列出防火墙中所有的OUTPUT端口规则
    def list_output_port(self):
        '''
            @name 列出防火墙中所有的OUTPUT端口规则
            @return [{
                      "Protocol": "tcp",
                      "Port": "8888",
                      "Strategy": "accept",
                      "Family": "ipv4",
                      "Address": "all",
                      "Chain": "OUTPUT"
                   }]
        '''
        try:
            list_port = self.get_chain_port("OUTPUT")
            for i in list_port:
                i["Strategy"] = i["Strategy"].lower()
            return list_port
        except Exception as e:
            return []

    # 2024/4/29 下午3:28 根据链来获取端口规则，暂时只支持INPUT/OUTPUT链
    def get_chain_port(self, chain):
        '''
            @name 根据链来获取端口规则
            @author wzz <2024/4/29 下午3:29>
            @param chain = INPUT/OUTPUT
            @return [{
                      "Protocol": "tcp",
                      "Port": "8888",
                      "Strategy": "accept",
                      "Family": "ipv4",
                      "Address": "all",
                      "Chain": "OUTPUT"
                   }]
        '''
        if chain not in ["INPUT", "OUTPUT"]:
            return []

        try:
            stdout = self.get_chain_data(chain)
            if stdout == "":
                return []

            lines = stdout.strip().split('\n')
            rules = []
            for line in lines:
                if line.startswith("Chain"):
                    continue
                if not "dpt:" in line and not "multiport sports" in line:
                    continue
                rule_info = line.split()
                if rule_info[0] == "num":
                    continue
                if not rule_info[3] in ["ACCEPT", "DROP", "REJECT"]:
                    continue
                if not rule_info[4] in self.protocol:
                    continue
                if not "dpt" in rule_info[-1] and not "-" in rule_info[-1] and not ":" in rule_info[-1]:
                    continue

                if ":" in rule_info[-1] and not "dpt" in rule_info[-1]:
                    Port = rule_info[-1]
                elif "-" in rule_info[-1]:
                    Port = rule_info[-5].split(":")[1]
                else:
                    Port = rule_info[-1].split(":")[1]

                if "source IP range" in line and "multiport sports" in line:
                    Address = rule_info[-4]
                elif not "0.0.0.0/0" in rule_info[8]:
                    Address = rule_info[8]
                elif "-" in rule_info[-1]:
                    Address = rule_info[-1]
                else:
                    Address = "all"

                rule = {
                    "Protocol": self.protocol[rule_info[4]],
                    "Port": Port,
                    "Strategy": rule_info[3],
                    "Family": "ipv4",
                    "Address": Address,
                    "Chain": chain,
                }
                rules.append(rule)

            return rules
        except Exception as e:
            return []

    # 2024/4/29 下午3:28 根据链来获取IP规则，暂时只支持INPUT/OUTPUT链
    def get_chain_ip(self, chain):
        '''
            @name 根据链来获取端口规则
            @author wzz <2024/4/29 下午3:29>
            @param chain = INPUT/OUTPUT
            @return [
                       {
                          "Family": "ipv4",
                          "Address": "192.168.1.190",
                          "Strategy": "accept",
                          "Chain": "INPUT"
                       }
                    ]
        '''
        if chain not in ["INPUT", "OUTPUT"]:
            return []

        try:
            stdout = self.get_chain_data(chain)
            if stdout == "":
                return []

            lines = stdout.strip().split('\n')
            rules = []
            for line in lines:
                if line.startswith("Chain"):
                    continue
                if "dpt:" in line or "multiport sports" in line:
                    continue
                rule_info = line.split()
                if rule_info[0] == "num":
                    continue
                if not rule_info[3] in ["ACCEPT", "DROP", "REJECT"]:
                    continue
                if not rule_info[4] in self.protocol:
                    continue

                Address = ""
                if not "0.0.0.0/0" in rule_info[8]:
                    Address = rule_info[8]
                elif "0.0.0.0/0" in rule_info[8] and "-" in rule_info[-1]:
                    Address = rule_info[-1]

                if Address == "":
                    continue

                rule = {
                    "Family": "ipv4",
                    "Address": Address,
                    "Strategy": rule_info[3],
                    "Chain": chain,
                }
                rules.append(rule)

            return rules
        except Exception as e:
            return []

    # 2024/4/29 下午4:01 获取指定链的数据
    def get_chain_data(self, chain):
        '''
            @name 获取指定链的数据
            @author wzz <2024/4/29 下午4:01>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        try:
            cmd = "{} -t filter -L {} -nv --line-numbers".format(self.cmd_str, chain)
            stdout, stderr = public.ExecShell(cmd)
            return stdout
        except Exception as e:
            return ""

    # 2024/4/29 下午2:46 列出防火墙中所有的INPUT和OUTPUT的ip规则
    def list_address(self):
        '''
            @name 列出防火墙中所有的ip规则
            @author wzz <2024/4/29 下午2:47>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return
        '''
        try:
            list_address = self.get_chain_ip("INPUT") + self.get_chain_ip("OUTPUT")
            for i in list_address:
                i["Strategy"] = i["Strategy"].lower()
            return list_address
        except Exception as e:
            return []

    # 2024/4/29 下午2:48 列出防火墙中所有input的ip规则
    def list_input_address(self):
        '''
            @name 列出防火墙中所有input的ip规则
            @author wzz <2024/4/29 下午2:48>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        try:
            list_address = self.get_chain_ip("INPUT")
            for i in list_address:
                i["Strategy"] = i["Strategy"].lower()
            return list_address
        except Exception as e:
            return []

    # 2024/4/29 下午2:49 列出防火墙中所有output的ip规则
    def list_output_address(self):
        '''
            @name 列出防火墙中所有output的ip规则
            @author wzz <2024/4/29 下午2:49>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        try:
            list_address = self.get_chain_ip("OUTPUT")
            for i in list_address:
                i["Strategy"] = i["Strategy"].lower()
            return list_address
        except Exception as e:
            return []

    # 2024/4/29 下午2:49 添加INPUT端口规则
    def input_port(self, info, operation):
        '''
            @name 添加INPUT端口规则
            @author wzz <2024/4/29 下午2:50>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        try:
            return self.set_chain_port(info, operation, "INPUT")
        except Exception as e:
            return self._result(False, "设置端口规则失败:{}".format(str(e)))

    # 2024/4/29 下午2:50 设置output端口策略
    def output_port(self, info, operation):
        '''
            @name 设置output端口策略
            @author wzz <2024/4/29 下午2:50>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        try:
            return self.set_chain_port(info, operation, "OUTPUT")
        except Exception as e:
            return self._result(False, "设置端口规则失败:{}".format(str(e)))

    # 2024/4/29 下午4:49 添加/删除指定链的端口规则
    def set_chain_port(self, info, operation, chain):
        '''
            @name 添加/删除指定链的端口规则
            @author wzz <2024/4/29 下午4:49>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        try:
            if not chain in ["INPUT", "OUTPUT"]:
                return self._result(False, "设置端口规则失败:{}".format("不支持的链类型"))

            if info['Protocol'] not in ["tcp", "udp"]:
                return self._result(False, "设置端口规则失败:{}".format("不支持的协议类型"))
            if info["Strategy"] == "accept":
                info["Strategy"] = "ACCEPT"
            elif info["Strategy"] == "drop":
                info["Strategy"] = "DROP"
            elif info["Strategy"] == "reject":
                info["Strategy"] = "REJECT"
            else:
                return self._result(False, "设置端口规则失败:{}".format("不支持的策略类型"))

            if operation == "add":
                operation = "-I"
            elif operation == "remove":
                operation = "-D"

            rule = "{} -t filter {} {} -p {} --dport {} -j {}".format(
                self.cmd_str,
                operation,
                chain,
                info['Protocol'],
                info['Port'],
                info['Strategy']
            )
            stdout, stderr = public.ExecShell(rule)
            if stderr and "setlocale: LC_ALL: cannot change locale (en_US.UTF-8)" not in stderr:
                return public.returnMsg(False, "设置端口规则失败: {}".format(stderr))
            return self._result(True, "设置端口规则成功")
        except Exception as e:
            return self._result(False, "设置端口规则失败:{}".format(str(e)))

    # 2024/4/29 下午5:01 添加/删除指定链的复杂端口规则
    def set_chain_rich_port(self, info, operation, chain):
        '''
            @name 添加/删除指定链的复杂端口规则
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        try:
            if not chain in ["INPUT", "OUTPUT"]:
                return self._result(False, "设置端口规则失败:{}".format("不支持的链类型"))

            if "Address" in info and info["Address"] == "":
                info["Address"] = "all"
            if "Address" in info and public.is_ipv6(info['Address']):
                return self._result(False, "设置端口规则失败:{}".format("不支持的IPV6地址"))

            if info['Protocol'] not in ["tcp", "udp"]:
                return self._result(False, "设置端口规则失败:{}".format("不支持的协议类型"))
            if info["Strategy"] == "accept":
                info["Strategy"] = "ACCEPT"
            elif info["Strategy"] == "drop":
                info["Strategy"] = "DROP"
            elif info["Strategy"] == "reject":
                info["Strategy"] = "REJECT"
            else:
                return self._result(False, "设置端口规则失败:{}".format("不支持的策略类型"))

            if operation == "add":
                operation = "-I"
            elif operation == "remove":
                operation = "-D"

            info['Port'] = info['Port'].replace("-", ":")
            info["Address"] = info["Address"].replace(":", "-")
            if ":" in info['Port'] or "-" in info['Port']:
                if ":" in info["Address"] or "-" in info["Address"]:
                    # iptables -t filter -I INPUT -m iprange --src-range 192.168.1.100-192.168.1.200 -p tcp -m multiport --sports 8000:9000 -j ACCEPT
                    rule = "{} -t filter {} {} -m iprange --src-range {} -p {} -m multiport --sports {} -j {}".format(
                        self.cmd_str,
                        operation,
                        chain,
                        info['Address'],
                        info['Protocol'],
                        info['Port'],
                        info['Strategy']
                    )
                else:
                    # iptables -t filter -I INPUT -p tcp -m multiport --sports 8000:9000 -s 192.168.1.100 -j ACCEPT
                    rule = "{} -t filter {} {} -p {} -m multiport --sports {} -s {} -j {}".format(
                        self.cmd_str,
                        operation,
                        chain,
                        info['Protocol'],
                        info['Port'],
                        info['Address'],
                        info['Strategy']
                    )
            else:
                if ":" in info["Address"] or "-" in info["Address"]:
                    # iptables -t filter -I OUTPUT -p tcp --dport 22333 -m iprange --src-range 192.168.1.100-192.168.1.200 -j ACCEPT
                    rule = "{} -t filter {} {} -p {} --dport {} -m iprange --src-range {} -j {}".format(
                        self.cmd_str,
                        operation,
                        chain,
                        info['Protocol'],
                        info['Port'],
                        info['Address'],
                        info['Strategy']
                    )
                else:
                    # iptables -t filter -I OUTPUT -p tcp --dport 22333 -s 192.168.1.0/24 -j ACCEPT
                    rule = "{} -t filter {} {} -p {} --dport {} -s {} -j {}".format(
                        self.cmd_str,
                        operation,
                        chain,
                        info['Protocol'],
                        info['Port'],
                        info['Address'],
                        info['Strategy']
                    )

            stdout, stderr = public.ExecShell(rule)
            if stderr and "setlocale: LC_ALL: cannot change locale (en_US.UTF-8)" not in stderr:
                return public.returnMsg(False, "设置端口规则失败: {}".format(stderr))
            return self._result(True, "设置端口规则成功")
        except Exception as e:
            return self._result(False, "设置端口规则失败:{}".format(str(e)))

    # 2024/4/29 下午5:01 添加/删除指定链的复杂ip规则
    def set_chain_rich_ip(self, info, operation, chain):
        '''
            @name 添加/删除指定链的复杂ip规则
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        try:
            if not chain in ["INPUT", "OUTPUT"]:
                return self._result(False, "设置规则失败:{}".format("不支持的链类型"))

            if "Address" in info and info["Address"] == "":
                info["Address"] = "all"
            if "Address" in info and public.is_ipv6(info['Address']):
                return self._result(False, "设置规则失败:{}".format("不支持的IPV6地址"))

            if info["Strategy"] == "accept":
                info["Strategy"] = "ACCEPT"
            elif info["Strategy"] == "drop":
                info["Strategy"] = "DROP"
            elif info["Strategy"] == "reject":
                info["Strategy"] = "REJECT"
            else:
                return self._result(False, "设置规则失败:{}".format("不支持的策略类型"))

            if operation == "add":
                operation = "-I"
            elif operation == "remove":
                operation = "-D"

            if ":" in info["Address"] or "-" in info["Address"]:
                # iptables -t filter -I INPUT -m iprange --src-range 192.168.1.100-192.168.1.200 -j ACCEPT
                rule = "{} -t filter {} {} -m iprange --src-range {} -j {}".format(
                    self.cmd_str,
                    operation,
                    chain,
                    info['Address'],
                    info['Strategy']
                )
            else:
                # iptables -t filter -I INPUT -s 192.168.1.100 -j ACCEPT
                rule = "{} -t filter {} {} -s {} -j {}".format(
                    self.cmd_str,
                    operation,
                    chain,
                    info['Address'],
                    info['Strategy']
                )


            stdout, stderr = public.ExecShell(rule)
            if stderr and "setlocale: LC_ALL: cannot change locale (en_US.UTF-8)" not in stderr:
                return public.returnMsg(False, "设置规则失败: {}".format(stderr))
            return self._result(True, "设置规则成功")
        except Exception as e:
            return self._result(False, "设置规则失败:{}".format(str(e)))

    # 2024/4/29 下午2:51 INPUT复杂一些的规则管理
    def rich_rules(self, info, operation):
        '''
            @name
            @author wzz <2024/4/29 下午2:51>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        try:
            if "Priority" in info and not "Port" in info:
                return self.set_chain_rich_ip(info, operation, "INPUT")
            else:
                return self.set_chain_rich_port(info, operation, "INPUT")
        except Exception as e:
            return self._result(False, "设置端口规则失败:{}".format(str(e)))

    # 2024/4/29 下午2:52 OUTPUT复杂一些的规则管理
    def output_rich_rules(self, info, operation):
        '''
            @name OUTPUT复杂一些的规则管理
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        try:
            if "Priority" in info and not "Port" in info:
                return self.set_chain_rich_ip(info, operation, "OUTPUT")
            else:
                return self.set_chain_rich_port(info, operation, "OUTPUT")
        except Exception as e:
            return self._result(False, "设置端口规则失败:{}".format(str(e)))

    # 2024/3/19 下午 3:03 清空指定链中的所有规则
    def flush_chain(self, chain_name):
        '''
            @name 清空指定链中的所有规则
            @author wzz <2024/3/19 下午 3:03>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        try:
            subprocess.check_output(
                [self.cmd_str, '-F', chain_name], stderr=subprocess.STDOUT, universal_newlines=True
            )
            return chain_name + " chain flushed successfully."
        except Exception as e:
            return "Failed to flush " + chain_name + " chain."

    # 2024/3/19 下午 3:03 获取当前系统中可用的链的名称列表
    def get_chain_names(self, parm):
        '''
            @name 获取当前系统中可用的链的名称列表
            @author wzz <2024/3/19 下午 3:03>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        try:
            if not self.check_table_name(parm['table']):
                return "错误： 不支持的表名."
            stdout = subprocess.check_output(
                [self.cmd_str, '-t', parm['table'], '-L'], stderr=subprocess.STDOUT, universal_newlines=True
            )
            chain_names = re.findall(r"Chain\s([A-Z]+)", stdout)
            return chain_names
        except Exception as e:
            return []

    # 2024/3/19 下午 3:17 构造端口转发规则，然后调用insert_rule方法插入规则
    def port_forward(self, info, operation):
        '''
            @name 构造端口转发规则，然后调用insert_rule方法插入规则
            @param "info": {
                    "Protocol": "tcp/udp",
                    "S_Port": "80",
                    "T_Address": "0.0.0.0/0",
                    "T_Port": "8080"
                }
            @param "operation": "add" or "remove"
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        try:
            rule = " -p {}".format(info['Protocol'])

            if "S_Address" in info and info['S_Address'] != "":
                rule += " -s {}".format(info['S_Address'])

            rule += " --dport {0} -j DNAT --to-destination {1}:{2}".format(
                info['S_Port'],
                info['T_Address'],
                info['T_Port'],
            )

            parm = {
                "table": "nat",
                "chain_name": "PREROUTING",
                "rule": rule
            }
            if operation not in ["add", "remove"]:
                return "请输入正确的操作类型. (add/remove)"

            if operation == "add":
                parm['type'] = "-I"
            elif operation == "remove":
                parm['type'] = "-D"
            return self.rule_manage(parm)
        except Exception as e:
            return self._result(False, "设置端口转发规则失败:{}".format(str(e)))

    # 2024/3/19 下午 3:03 在指定链中管理规则
    def rule_manage(self, parm):
        '''
            @name 在指定链中管理规则
            @author wzz <2024/3/19 下午 3:03>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        try:
            if not self.check_table_name(parm['table']):
                return self._result(False, "不支持的表名{}".format(parm['table']))

            rule = "{} -t {} {} {} {}".format(
                self.cmd_str, parm['table'], parm['type'], parm['chain_name'], parm['rule']
            )
            stdout, stderr = public.ExecShell(rule)
            if stderr and "setlocale: LC_ALL: cannot change locale (en_US.UTF-8)" not in stderr:
                return public.returnMsg(False, "规则设置失败: {}".format(stderr))
            return self._result(True, "规则设置成功")
        except Exception as e:
            return self._result(False, "规则设置失败: {}".format(str(e)))

    # 2024/4/29 下午5:55 获取所有端口转发列表
    def list_port_forward(self):
        '''
            @name 获取所有端口转发列表
            @author wzz <2024/4/29 下午5:55>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        return self.get_nat_prerouting_rules()

    # 2024/3/19 下午 4:00 调用list_rules获取所有nat表中的PREROUTING链的规则(端口转发规则),并分析成字典返回
    def get_nat_prerouting_rules(self):
        '''
            @name 调用list_rules获取所有nat表中的PREROUTING链的规则(端口转发规则),并分析成字典返回
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        try:
            port_forward_rules = self.list_rules({"table": "nat", "chain_name": "PREROUTING"})
            rules = []
            for rule in port_forward_rules:
                if rule["target"] != "DNAT": continue
                options = rule["options"].split(' ')

                protocol = "TCP"
                if rule["prot"] == "6" or rule["prot"] == "tcp":
                    protocol = "TCP"
                elif rule["prot"] == "17" or rule["prot"] == "udp":
                    protocol = "UDP"
                elif rule["prot"] == "0" or rule["prot"] == "all":
                    protocol = "TCP/UDP"
                rules.append({
                    "type": "port_forward",
                    "number": rule["number"],
                    "S_Address": rule["source"],
                    "S_Port": options[1].split("dpt:")[1],
                    "T_Address": options[2].split("to:")[1].split(":")[0],
                    "T_Port": options[2].split("to:")[1].split(":")[1],
                    "Protocol": protocol.lower()
                })
            return rules
        except Exception as e:
            return []

    # 2024/4/29 下午2:43 格式化输出json
    def format_json(self, data):
        '''
            @name 格式化输出json
            @param "data": json数据
            @return json字符串
        '''
        import json
        from pygments import highlight, lexers, formatters

        formatted_json = json.dumps(data, indent=3)
        colorful_json = highlight(formatted_json.encode('utf-8'), lexers.JsonLexer(),
                                  formatters.TerminalFormatter())
        return colorful_json


if __name__ == '__main__':
    args = sys.argv
    firewall = Iptables()
    if len(args) < 2:
        print("Welcome to the iptables command-line interface!")
        print()
        print("Available options:")
        print("list_rules: list_rules <table> <chain_name>")
        print("flush_chain: flush_chain <table>")
        print("get_chain_names: get_chain_names <table>")
        print("port_forward: port_forward <S_Address> <S_Port> <T_Address> <T_Port> <Protocol> <Operation>")
        print("get_nat_prerouting_rules: get_nat_prerouting_rules")
        print()
        sys.exit(1)
    if args[1] == "list_rules":
        # firewall.list_rules({"table": args[2], "chain_name": args[3]})
        print(firewall.list_rules({"table": args[2], "chain_name": args[3]}))
    elif args[1] == "flush_chain":
        print(firewall.flush_chain(args[2]))
    elif args[1] == "get_chain_names":
        table = args[2] if len(args) > 2 else "filter"
        print(firewall.get_chain_names({"table": table}))
    elif args[1] == "port_forward":
        if len(args) < 8:
            print("传参使用方法: port_forward <S_Address> <S_Port> <T_Address> <T_Port> <Protocol> <Operation>")
            sys.exit(1)

        info = {
            "S_Address": args[2],
            "S_Port": args[3],
            "T_Address": args[4],
            "T_Port": args[5],
            "Protocol": args[6]
        }
        print(firewall.port_forward(info, args[7]))
    elif args[1] == "get_nat_prerouting_rules":
        import json
        from pygments import highlight, lexers, formatters

        formatted_json = json.dumps(firewall.get_nat_prerouting_rules(), indent=3)
        colorful_json = highlight(formatted_json.encode('utf-8'), lexers.JsonLexer(),
                                  formatters.TerminalFormatter())
        print(colorful_json)
        # print(firewall.get_nat_prerouting_rules())
    elif args[1] == "list_port":
        print(firewall.format_json(firewall.list_port()))
    elif args[1] == "list_input_port":
        print(firewall.format_json(firewall.list_input_port()))
    elif args[1] == "list_output_port":
        print(firewall.format_json(firewall.list_output_port()))
    elif args[1] == "list_address":
        print(firewall.format_json(firewall.list_address()))
    elif args[1] == "list_input_address":
        print(firewall.format_json(firewall.list_input_address()))
    elif args[1] == "list_output_address":
        print(firewall.format_json(firewall.list_output_address()))
    elif args[1] == "input_port":
        info = {
            "Protocol": args[2],
            "Port": args[3],
            "Strategy": args[4]
        }
        print(firewall.input_port(info, args[5]))
    elif args[1] == "output_port":
        info = {
            "Protocol": args[2],
            "Port": args[3],
            "Strategy": args[4]
        }
        print(firewall.output_port(info, args[5]))
    elif args[1] == "rich_rules":
        info = {
            "Protocol": args[2],
            "Port": args[3],
            "Address": args[4],
            "Strategy": args[5]
        }
        print(firewall.rich_rules(info, args[6]))
    elif args[1] == "output_rich_rules":
        info = {
            "Protocol": args[2],
            "Port": args[3],
            "Address": args[4],
            "Strategy": args[5]
        }
        print(firewall.output_rich_rules(info, args[6]))
    else:
        print("不支持的传参: " + args[1])
        sys.exit(1)
