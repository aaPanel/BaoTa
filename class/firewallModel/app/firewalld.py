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
# 系统防火墙模型 - firewalld封装库
# ------------------------------

import os
import sys


if "/www/server/panel/class" not in sys.path:
    sys.path.insert(0, "/www/server/panel/class")
import public
from firewallModel.app.appBase import Base


class Firewalld(Base):
    def __init__(self):
        super().__init__()
        self.cmd_str = self._set_cmd_str()

    def _set_cmd_str(self) -> str:
        return "firewall-cmd"

    # 2024/3/20 下午 12:00 获取防火墙状态
    def status(self) -> bool:
        '''
            @name 获取防火墙状态
            @author wzz <2024/3/20 下午 12:01>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        try:
            stdout, stderr = public.ExecShell("systemctl is-active firewalld")
            if "not running" in stdout:
                return False
            return True
        except Exception as e:
            return False

    # 2024/3/20 下午 12:00 获取防火墙版本号 
    def version(self) -> str:
        '''
            @name 获取防火墙版本号
            @author wzz <2024/3/20 下午 12:00>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        stdout, stderr = self.run_command("firewall-cmd --version")
        if "FirewallD is not running" in stdout:
            return "Firewalld 没有启动,请先启动再试"
        if stderr:
            return "获取firewalld版本失败, err: {}".format(stderr)
        return stdout.strip()

    # 2024/3/20 下午 12:08 启动防火墙
    def start(self) -> dict:
        '''
            @name 启动防火墙
            @author wzz <2024/3/20 下午 12:08>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        stdout, stderr = self.run_command("systemctl start firewalld")
        if stderr:
            return self._result(False, "启动防火墙失败, err: {}".format(stderr))
        return self._result(True, "启动防火墙成功")

    # 2024/3/20 下午 12:10 停止防火墙
    def stop(self) -> dict:
        '''
            @name 停止防火墙
            @author wzz <2024/3/20 下午 12:10>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        stdout, stderr = self.run_command("systemctl stop firewalld")
        if stderr:
            return self._result(False, "停止防火墙失败, err: {}".format(stderr))
        return self._result(True, "停止防火墙成功")

    # 2024/3/20 下午 12:11 重启防火墙
    def restart(self) -> dict:
        '''
            @name 重启防火墙
            @author wzz <2024/3/20 下午 12:11>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        stdout, stderr = self.run_command("systemctl restart firewalld")
        if stderr:
            return self._result(False, "重启防火墙失败, err: {}".format(stderr))
        return self._result(True, "重启防火墙成功")

    # 2024/3/20 下午 12:11 重载防火墙
    def reload(self) -> dict:
        '''
            @name 重载防火墙
            @author wzz <2024/3/20 下午 12:11>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        stdout, stderr = self.run_command("firewall-cmd --reload")
        if stderr:
            return self._result(False, "重载防火墙失败, err: {}".format(stderr))
        return self._result(True, "重载防火墙成功")

    # 2024/3/20 下午 12:12 获取所有防火墙端口列表
    def list_port(self) -> list:
        '''
            @name 获取所有防火墙端口列表
            @author wzz <2024/3/20 下午 12:12>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        return self.parse_public_zone()["ports"] + self.list_output_port()

    # 2024/3/20 下午 12:12 获取防火墙端口INPUT列表
    def list_input_port(self) -> list:
        '''
            @name 获取防火墙端口列表
            @author wzz <2024/3/20 下午 12:12>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        return self.parse_public_zone()["ports"]

    # 2024/3/22 上午 11:28 获取所有OUTPUT的direct 端口规则
    def list_output_port(self) -> list:
        '''
            @name 获取所有OUTPUT的direct 端口规则
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        list_direct_rules = self.parse_direct_xml()["ports"]
        datas = []
        for rule in list_direct_rules:
            if rule.get("Chain") == "OUTPUT":
                datas.append(rule)
        return datas

    # 2024/3/20 下午 12:21 获取防火墙的rule的ip规则列表
    def list_address(self) -> list:
        '''
            @name 获取防火墙的rule的ip规则列表
            @author wzz <2024/3/20 下午 2:45>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        return self.parse_public_zone()["rules"] + self.parse_trusted_zone()["rules"] + self.list_output_address()

    # 2024/3/20 下午 12:21 获取防火墙的rule input的ip规则列表
    def list_input_address(self) -> list:
        '''
            @name 获取防火墙的rule input的ip规则列表
            @author wzz <2024/3/20 下午 2:45>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        return self.parse_public_zone()["rules"] + self.parse_trusted_zone()["rules"]

    # 2024/3/22 下午 4:07 获取所有OUTPUT的direct ip规则
    def list_output_address(self) -> list:
        '''
            @name 获取所有OUTPUT的direct ip规则
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        list_direct_rules = self.parse_direct_xml()["rules"]
        datas = []
        for rule in list_direct_rules:
            if rule.get("Chain") == "OUTPUT":
                datas.append(rule)
        return datas

    # 2024/3/20 下午 5:34 添加或删除防火墙端口
    def input_port(self, info: dict, operation: str) -> dict:
        '''
            @name 添加或删除防火墙端口
            @author wzz <2024/3/20 下午 5:34>
            @param info:{"Port": args[2], "Protocol": args[3]}
                    operation: add/remove
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        if operation not in ["add", "remove"]:
            return self._result(False, "不支持的操作: {}".format(operation))

        # 2024/3/25 下午 6:00 处理tcp/udp双协议的端口
        if info['Protocol'].find("/") != -1:
            stdout, stderr = public.ExecShell(
                "{cmd_str} --zone=public --{operation}-port={port}/{prot} --permanent"
                .format(
                    cmd_str=self.cmd_str,
                    operation=operation,
                    port=info['Port'],
                    prot="tcp"
                )
            )
            if stderr:
                return self._result(False, "设置端口失败, err: {}".format(stderr))
            stdout, stderr = public.ExecShell(
                "{cmd_str} --zone=public --{operation}-port={port}/{prot} --permanent"
                .format(
                    cmd_str=self.cmd_str,
                    operation=operation,
                    port=info['Port'],
                    prot="udp"
                )
            )
            if stderr:
                return self._result(False, "设置端口失败, err: {}".format(stderr))
        else:
            # 2024/3/25 下午 6:00 处理单协议的端口
            stdout, stderr = public.ExecShell(
                "{cmd_str} --zone=public --{operation}-port={port}/{prot} --permanent"
                .format(
                    cmd_str=self.cmd_str,
                    operation=operation,
                    port=info['Port'],
                    prot=info['Protocol']
                )
            )
        if stderr:
            return self._result(False, "设置端口失败, err: {}".format(stderr))
        return self._result(True, "设置入站端口成功")

    # 2024/3/20 下午 6:02 设置output的防火墙端口规则
    def output_port(self, info: dict, operation: str) -> dict:
        '''
            @name 设置output的防火墙端口规则
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        if operation not in ["add", "remove"]:
            return self._result(False, "不支持的操作: {}".format(operation))

        if info['Strategy'] == "accept":
            info['Strategy'] = "ACCEPT"
        elif info['Strategy'] == "drop":
            info['Strategy'] = "DROP"
        elif info['Strategy'] == "reject":
            info['Strategy'] = "REJECT"
        else:
            return self._result(False, "不支持的策略: {}".format(info['Strategy']))

        info['Port'] = info['Port'].replace("-", ":")

        if "/" in info['Protocol']:
            info['Protocol'] = info['Protocol'].split("/")
            for pp in info['Protocol']:
                if not pp in ["tcp", "udp"]:
                    return self._result(False, "设置出站端口失败, err: 协议不支持 {}".format(pp))

                stdout, stderr = public.ExecShell(
                    "{cmd_str} --permanent --direct --{operation}-rule ipv4 filter OUTPUT {priority} -p {prot} --dport {port} -j {strategy}"
                    .format(
                        cmd_str=self.cmd_str,
                        operation=operation,
                        priority=info['Priority'],
                        prot=pp,
                        port=info['Port'],
                        strategy=info['Strategy']
                    )
                )
                if stderr:
                    return self._result(False, "设置出站端口失败, err: {}".format(stderr))
        else:
            stdout, stderr = public.ExecShell(
                "{cmd_str} --permanent --direct --{operation}-rule ipv4 filter OUTPUT {priority} -p {prot} --dport {port} -j {strategy}"
                .format(
                    cmd_str=self.cmd_str,
                    operation=operation,
                    priority=info['Priority'],
                    prot=info['Protocol'],
                    port=info['Port'],
                    strategy=info['Strategy']
                )
            )

            if stderr:
                return self._result(False, "设置出站端口失败, err: {}".format(stderr))

        return self._result(True, "设置出站端口成功")

    def set_rich_rule(self, info: dict, operation: str) -> dict:
        '''
            @name 添加或删除复杂规则
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        rule_str = "rule family={}".format(info['Family'].lower())
        if "Address" in info and info["Address"] != "all":
            rule_str += " source address={}".format(info['Address'])
        if info.get("Port"):
            rule_str += " port port={}".format(info['Port'])
        if info.get("Protocol"):
            rule_str += " protocol={}".format(info['Protocol'])
        rule_str += " {}".format(info['Strategy'])

        stdout, stderr = public.ExecShell(
            "{} --zone=public --{}-rich-rule='{}' --permanent"
            .format(self.cmd_str, operation, rule_str))

        if stderr:
            return self._result(False, "设置规则：{} 失败, err: {}".format(operation, rule_str, stderr))
        return self._result(True, "设置规则成功".format(operation))

    # 2024/3/22 上午 11:35 添加或删除复杂规则
    def rich_rules(self, info: dict, operation: str) -> dict:
        '''
            @name 添加或删除复杂规则
            @author wzz <2024/3/22 上午 11:35>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        if operation not in ["add", "remove"]:
            return self._result(False, "不支持的规则操作: {}".format(operation))

        if "Zone" in info and info["Zone"] == "trusted":
            return self.rich_trusted_rule(info, operation)

        if "Protocol" in info and info["Protocol"] == "all":
            info["Protocol"] = "tcp/udp"

        if "Protocol" in info and info['Protocol'].find("/") != -1:
            result_list = []
            for protocol in info['Protocol'].split("/"):
                info['Protocol'] = protocol
                result_list.append(self.set_rich_rule(info, operation))

            return {"status": True, "msg": result_list}
        else:
            return self.set_rich_rule(info, operation)

    # 2024/7/23 下午4:36 设置trusted区域的ip规则
    def rich_trusted_rule(self, info: dict, operation: str) -> dict:
        '''
            @name 设置trusted区域的ip规则
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        try:
            if operation not in ["add", "remove"]:
                return self._result(False, "不支持的操作: {}".format(operation))

            if not info['Strategy'].lower() in ("accept", "drop", "reject"):
                return self._result(False, "不支持的策略: {}".format(info['Strategy'].lower()))

            rich_rules = self.cmd_str + " --zone=trusted"
            if info['Strategy'].lower() == "accept":
                rich_rules += " --{0}-source='{1}' --permanent".format(operation, info["Address"])
            else:
                rich_rules += " --{0}-rich-rule='rule family=\"{1}\" source address=\"{2}\" {3}' --permanent".format(
                    operation,
                    info['Family'],
                    info['Address'],
                    info['Strategy'].lower()
                )
            stdout, stderr = public.ExecShell(rich_rules)
            if "success" not in stdout and stderr:
                return self._result(False, "设置trusted区域规则失败, err: {}".format(stderr))
            return self._result(True, "设置trusted区域规则成功")
        except:
            return self._result(False, "设置trusted区域规则失败")

    # 2024/3/24 下午 10:43 设置output的防火墙ip规则
    def output_rich_rules(self, info: dict, operation: str) -> dict:
        '''
            @name 设置output的防火墙ip规则
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        if operation not in ["add", "remove"]:
            return self._result(False, "不支持的操作: {}".format(operation))

        if info['Strategy'] == "accept":
            info['Strategy'] = "ACCEPT"
        elif info['Strategy'] == "drop":
            info['Strategy'] = "DROP"
        elif info['Strategy'] == "reject":
            info['Strategy'] = "REJECT"
        else:
            return self._result(False, "不支持的策略: {}".format(info['Strategy']))

        rich_rules = self.cmd_str + " --permanent --direct --{0}-rule ipv4 filter OUTPUT".format(operation)
        if "Priority" in info:
            rich_rules += " {}".format(info["Priority"])
        if "Address" in info:
            rich_rules += " -d {}".format(info["Address"])
        if "Protocol" in info:
            rich_rules += " -p {}".format(info["Protocol"])
        if "Port" in info:
            info["Port"] = info["Port"].replace("-", ":")
            rich_rules += " --dport {}".format(info["Port"])
        if "Strategy" in info:
            rich_rules += " -j {}".format(info["Strategy"])

        stdout, stderr = public.ExecShell(rich_rules)
        if "success" not in stdout and stderr:
            return self._result(False, "设置出站地址失败, err: {}".format(stderr))
        if "NOT_ENABLED" in stderr:
            return self._result(False, "规则不存在")
        return self._result(True, "设置出站地址成功")

    # 2024/3/22 下午 12:22 解析public区域的防火墙规则
    def parse_public_zone(self) -> dict:
        '''
            @name 解析public区域的防火墙规则
            @author wzz <2024/3/22 下午 12:22>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"services": services, "ports": ports, "rules": rules} rules是ip规则
        '''
        try:
            import xml.etree.ElementTree as ET
            file_path = "/etc/firewalld/zones/public.xml"
            if not os.path.exists(file_path):
                return {"services": [], "ports": [], "rules": [], "forward_ports": []}

            services = []
            ports = []
            rules = []
            forward_ports = []

            tree = ET.parse(file_path)
            root = tree.getroot()

            for elem in root:
                # 2024/3/22 下午 3:01 服务规则
                if elem.tag == "service":
                    services.append(elem.attrib['name'])
                # 2024/3/22 下午 3:01 端口规则
                elif elem.tag == "port":
                    port = {
                        "Protocol": elem.attrib["protocol"],
                        "Port": elem.attrib["port"],
                        "Strategy": "accept",
                        "Family": "ipv4",
                        "Address": "all",
                        "Chain": "INPUT",
                    }
                    ports.append(port)
                # 2024/3/22 下午 3:01 复杂的规则配置
                elif elem.tag == "rule":
                    if not "family" in elem.attrib:
                        continue
                    rule = {"Family": elem.attrib["family"]}
                    for subelem in elem:
                        rule["Strategy"] = "accept"
                        if subelem.tag == "source":
                            if "address" in subelem.attrib:
                                rule["Address"] = subelem.attrib["address"]
                            else:
                                continue
                            rule["Address"] = "all" if rule["Address"] == "Anywhere" else rule["Address"]
                        elif subelem.tag == "port":
                            rule["port"] = {"protocol": subelem.attrib["protocol"], "port": subelem.attrib["port"]}
                        elif subelem.tag == "drop":
                            rule["Strategy"] = "drop"
                        elif subelem.tag == "accept":
                            rule["Strategy"] = "accept"
                        elif subelem.tag == "forward-port":
                            rule["forward-port"] = {
                                "protocol": subelem.attrib["protocol"],
                                "S_Port": subelem.attrib["port"],
                                "T_Address": subelem.attrib["to-addr"],
                                "T_Port": subelem.attrib["to-port"],
                            }

                    # 2024/3/22 下午 3:02 如果端口在里面,就放到端口规则列表中,否则就是ip规则
                    if "port" in rule:
                        ports.append({
                            "Protocol": rule["port"]["protocol"] if "protocol" in rule["port"] else "tcp",
                            "Port": rule["port"]["port"],
                            "Strategy": rule["Strategy"] if "Strategy" in rule else "accept",
                            "Family": rule["Family"] if "Family" in rule else "ipv4",
                            "Address": rule["Address"] if "Address" in rule else "all",
                            "Chain": "INPUT",
                        })
                    # 2024/3/25 下午 5:01 处理带源ip的端口转发规则
                    elif "forward-port" in rule:
                        forward_ports.append({
                            "type": "port_forward",
                            "number": len(forward_ports) + 1,
                            "Protocol": rule["forward-port"]["protocol"],
                            "S_Address": rule["Address"],
                            "S_Port": rule["forward-port"]["S_Port"],
                            "T_Address": rule["forward-port"]["T_Address"],
                            "T_Port": rule["forward-port"]["T_Port"],
                        })
                    else:
                        if "Address" not in rule:
                            continue

                        rule["Chain"] = "INPUT"
                        rule["Zone"] = "public"
                        rules.append(rule)
                # 2024/3/25 下午 2:57 端口转发规则
                elif elem.tag == "forward-port":
                    port = {
                        "type": "port_forward",
                        "number": len(forward_ports) + 1,
                        "Protocol": elem.attrib["protocol"] if "protocol" in elem.attrib else "tcp",
                        "S_Address": "",
                        "S_Port": elem.attrib["port"] if "port" in elem.attrib else "",
                        "T_Address": elem.attrib["to-addr"] if "to-addr" in elem.attrib else "",
                        "T_Port": elem.attrib["to-port"] if "to-port" in elem.attrib else "",
                    }
                    forward_ports.append(port)

            return {"services": services, "ports": ports, "rules": rules, "forward_ports": forward_ports}
        except Exception as e:
            return {"services": [], "ports": [], "rules": [], "forward_ports": []}

    # 2024/3/22 下午 2:32 解析direct.xml的防火墙规则
    def parse_direct_xml(self) -> dict:
        '''
            @name 解析direct.xml的防火墙规则
            @author wzz <2024/3/22 下午 2:32>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return list[dict{}...]
        '''
        try:
            import xml.etree.ElementTree as ET
            file_path = "/etc/firewalld/direct.xml"
            if not os.path.exists(file_path):
                return {"ports": [], "rules": []}

            ports = []
            rules = []

            tree = ET.parse(file_path)
            root = tree.getroot()

            for elem in root:
                if elem.tag == "rule":
                    protocol = "tcp"
                    port = ""
                    strategy = ""
                    address = ""

                    elem_t = elem.text.split(" ")
                    # 2024/3/22 下午 4:14 解析 Options 得到端口,策略,地址,协议
                    for i in elem_t:
                        if i == "-p":
                            protocol = elem_t[elem_t.index(i) + 1] # 如果找到匹配项，结果为索引+1的值，-p tcp,值为tcp
                        elif i == "--dport":
                            port = elem_t[elem_t.index(i) + 1]
                        elif i == "-j":
                            strategy = elem_t[elem_t.index(i) + 1]
                        elif i == "-d":
                            address = elem_t[elem_t.index(i) + 1]

                    rule = {
                            "Family": elem.attrib["ipv"],
                            "Chain": elem.attrib["chain"],
                            "Strategy": strategy.lower(),
                            "Address": address if address != "" else "all",
                            "Zone": "direct",
                            # "Options": elem.text
                        }

                    # 2024/3/22 下午 4:13 如果端口不为空,就是端口规则
                    if port != "":
                        rule["Port"] = port
                        rule["Protocol"] = protocol

                        ports.append(rule)
                    # 2024/3/22 下午 4:14 如果端口为空,就是ip规则
                    else:
                        rules.append(rule)

            return {"ports": ports, "rules": rules}
        except Exception as e:
            return {"ports": [], "rules": []}

    # 2024/7/17 下午3:29 解析trusted区域的防火墙规则
    def parse_trusted_zone(self) -> dict:
        '''
            @name 解析trusted区域的防火墙规则
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"services": services, "ports": ports, "rules": rules, "forward_ports": forward_ports} rules是ip规则
        '''
        try:
            import xml.etree.ElementTree as ET
            file_path = "/etc/firewalld/zones/trusted.xml"
            if not os.path.exists(file_path):
                return {"services": [], "ports": [], "rules": [], "forward_ports": []}

            services = []
            ports = []
            rules = []
            forward_ports = []

            tree = ET.parse(file_path)
            root = tree.getroot()

            for elem in root:
                if elem.tag == "source":
                    rule = {
                        "Family": "ipv4",
                        "Strategy": "accept",
                        "Address": elem.attrib["address"],
                        "Chain": "INPUT",
                        "Zone": "trusted",
                    }
                    rules.append(rule)
                elif elem.tag == "rule":
                    rule = {
                        "Family": "ipv4",
                        "Chain": "INPUT",
                        "Zone": "trusted",
                        "Strategy": "accept",
                        "Address": "",
                    }
                    for sb in elem:
                        if sb.tag == "source":
                            rule["Address"] = sb.attrib["address"]
                        elif sb.tag == "drop":
                            rule["Strategy"] = "drop"
                    if rule["Address"] != "":
                        rules.append(rule)

            return {"services": services, "ports": ports, "rules": rules, "forward_ports": forward_ports}
        except Exception as e:
            return {"services": [], "ports": [], "rules": [], "forward_ports": []}

    # 2024/3/22 下午 4:54 检查是否开启了masquerade，没有则开启
    def check_masquerade(self) -> dict:
        '''
            @name 检查是否开启了masquerade，没有则开启
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        stdout, stderr = public.ExecShell("firewall-cmd --query-masquerade")
        if "no" in stdout:
            stdout, stderr = public.ExecShell("firewall-cmd --add-masquerade")
            if stderr:
                return self._result(False, "开启masquerade失败, err: {}".format(stderr))
            return self._result(True, "开启masquerade成功")
        return self._result(True, "masquerade已经开启")

    # 2024/3/22 下午 4:57 设置端口转发
    def port_forward(self, info: dict, operation: str) -> dict:
        '''
            @name 设置端口转发
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        if operation not in ["add", "remove"]:
            return self._result(False, "不支持的操作: {}".format(operation))

        if operation == "add":
            check_masquerade = self.check_masquerade()
            if not check_masquerade["status"]:
                return check_masquerade

        # 2024/3/25 下午 6:07 处理有源地址的情况
        if "S_Address" in info and info["S_Address"] != "":
            # 2024/3/25 下午 6:05 处理tcp/udp双协议的情况
            if info['Protocol'].find("/") != -1:
                rich_rules = self.cmd_str + " --zone=public"
                rich_rules += " --{0}-rich-rule='rule family=\"{1}\" source address=\"{2}\" forward-port port=\"{3}\" protocol=\"tcp\" to-port=\"{4}\" to-addr=\"{5}\"' --permanent".format(
                            operation,
                            info['Family'],
                            info['S_Address'],
                            info['S_Port'],
                            info['T_Port'],
                            info['T_Address'],
                        )
                stdout, stderr = public.ExecShell(rich_rules)
                if "success" not in stdout and stderr:
                    if "ALREADY_ENABLED" in stderr:
                        return self._result(True, "端口转发规则已经存在")
                    return self._result(False, "设置端口转发失败, err: {}".format(stderr))

                rich_rules = self.cmd_str + " --zone=public"
                rich_rules += " --{0}-rich-rule='rule family=\"{1}\" source address=\"{2}\" forward-port port=\"{3}\" protocol=\"udp\" to-port=\"{4}\" to-addr=\"{5}\"' --permanent".format(
                            operation,
                            info['Family'],
                            info['S_Address'],
                            info['S_Port'],
                            info['T_Port'],
                            info['T_Address'],
                        )
                stdout, stderr = public.ExecShell(rich_rules)
                if "success" not in stdout and stderr:
                    if "ALREADY_ENABLED" in stderr:
                        return self._result(True, "端口转发规则已经存在")
                    return self._result(False, "设置端口转发失败, err: {}".format(stderr))

            # 2024/3/25 下午 6:05 处理单协议的情况
            else:
                rich_rules = self.cmd_str + " --zone=public"
                rich_rules += " --{0}-rich-rule='rule family=\"{1}\" source address=\"{2}\" forward-port port=\"{3}\" protocol=\"{4}\" to-port=\"{5}\" to-addr=\"{6}\"'".format(
                    operation,
                    info['Family'],
                    info['S_Address'],
                    info['S_Port'],
                    info['Protocol'],
                    info['T_Port'],
                    info['T_Address'],
                )
                rich_rules += " --permanent"
                stdout, stderr = public.ExecShell(rich_rules)
                if "success" not in stdout and stderr:
                    if "ALREADY_ENABLED" in stderr:
                        return self._result(True, "端口转发规则已经存在")
                    return self._result(False, "设置端口转发失败, err: {}".format(stderr))

        # 2024/3/25 下午 6:08 处理没有源地址的情况
        else:
            # 2024/3/25 下午 6:05 处理tcp/udp双协议的情况
            if info['Protocol'].find("/") != -1:
                stdout, stderr = public.ExecShell(
                    "{} --zone=public --{}-forward-port='port={}:proto={}:toport={}:toaddr={}' --permanent"
                    .format(self.cmd_str, operation, info['S_Port'], "udp", info['T_Port'], info['T_Address'])
                )
                if "success" not in stdout and stderr:
                    if "ALREADY_ENABLED" in stderr:
                        return self._result(True, "端口转发规则已经存在")
                    return self._result(False, "设置端口转发失败, err: {}".format(stderr))

                stdout, stderr = public.ExecShell(
                    "{} --zone=public --{}-forward-port='port={}:proto={}:toport={}:toaddr={}' --permanent"
                    .format(self.cmd_str, operation, info['S_Port'], "tcp", info['T_Port'], info['T_Address'])
                )
                if "success" not in stdout and stderr:
                    if "ALREADY_ENABLED" in stderr:
                        return self._result(True, "端口转发规则已经存在")
                    return self._result(False, "设置端口转发失败, err: {}".format(stderr))
            # 2024/3/25 下午 6:09 处理单协议的情况
            else:
                stdout, stderr = public.ExecShell(
                    "{} --zone=public --{}-forward-port='port={}:proto={}:toport={}:toaddr={}' --permanent"
                    .format(self.cmd_str, operation, info['S_Port'], info['Protocol'], info['T_Port'], info['T_Address'])
                )
                if "success" not in stdout and stderr:
                    if "ALREADY_ENABLED" in stderr:
                        return self._result(True, "端口转发规则已经存在")
                    return self._result(False, "设置端口转发失败, err: {}".format(stderr))

        return self._result(True, "设置端口转发成功")

    # 2024/3/25 下午 2:37 获取所有端口转发规则
    def list_port_forward(self) -> list:
        '''
            @name 获取所有端口转发规则
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return list[dict{}...]
        '''
        return self.parse_public_zone()["forward_ports"]