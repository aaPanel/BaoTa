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
# 系统防火墙模型 - ufw封装库
# ------------------------------

import subprocess
import os
import sys
if "/www/server/panel/class" not in sys.path:
    sys.path.insert(0, "/www/server/panel/class")
import public
# import re
from firewallModel.app.appBase import Base

class Ufw(Base):
    def __init__(self):
        self.cmd_str = self._set_cmd_str()

    def _set_cmd_str(self):
        return "ufw"

    # 2024/3/19 下午 5:00 获取系统防火墙的运行状态
    def status(self):
        '''
            @name 获取系统防火墙的运行状态
            @author wzz <2024/3/19 下午 5:00>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        try:
            result = subprocess.run([self.cmd_str, "status"], capture_output=True, text=True, check=True)
            if "Status: active" in result.stdout:
                return "running"
            elif "状态： 激活" in result.stdout:
                return "running"
            else:
                return "not running"
        except subprocess.CalledProcessError:
            return "not running"
        except Exception as e:
            return "not running"

    # 2024/3/19 下午 5:00 获取系统防火墙的版本号
    def version(self):
        '''
            @name 获取系统防火墙的版本号
            @author wzz <2024/3/19 下午 5:00>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        try:
            result = subprocess.run([self.cmd_str, "version"], capture_output=True, text=True, check=True)
            info = result.stdout.replace("\n", "")
            return info.replace("ufw ", "")
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
        try:
            stdout, stderr = public.ExecShell("echo y | {} enable".format(self.cmd_str))
            if stderr and "setlocale: LC_ALL: cannot change locale (en_US.UTF-8)" not in stderr:
                return public.returnMsg(False, "启动防火墙失败: {}".format(stderr))
            return self._result(True, "启动防火墙成功")
        except Exception as e:
            return self._result(False, "启动防火墙失败:{}".format(str(e)))

    # 2024/3/19 下午 5:00 停止防火墙
    def stop(self):
        '''
            @name 停止防火墙
            @author wzz <2024/3/19 下午 5:00>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        try:
            stdout, stderr = public.ExecShell("{} disable".format(self.cmd_str))
            if stderr and "setlocale: LC_ALL: cannot change locale (en_US.UTF-8)" not in stderr:
                return public.returnMsg(False, "停止防火墙失败: {}".format(stderr))
            return self._result(True, "停止防火墙成功")
        except Exception as e:
            return self._result(False, "停止防火墙失败:{}".format(str(e)))

    # 2024/3/19 下午 4:59 重启防火墙
    def restart(self):
        '''
            @name 重启防火墙
            @author wzz <2024/3/19 下午 4:59>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        try:
            self.stop()
            self.start()
        except Exception as e:
            return self._result(False, "重启防火墙失败:{}".format(str(e)))

    # 2024/3/19 下午 4:59 重载防火墙
    def reload(self):
        '''
            @name 重载防火墙
            @author wzz <2024/3/19 下午 4:59>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        try:
            subprocess.run([self.cmd_str, "reload"], check=True, stdout=subprocess.PIPE)
        except Exception as e:
            return self._result(False, "重载防火墙失败:{}".format(str(e)))

    # 2024/3/19 上午 10:39 列出防火墙中所有端口规则
    def list_port(self):
        '''
            @name 列出防火墙中所有端口规则
            @author wzz <2024/3/19 上午 10:39>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        try:
            result = subprocess.run(
                [self.cmd_str, "status", "verbose"], capture_output=True, text=True, check=True
            )
            port_infos = result.stdout.split("\n")
            datas = []
            is_start = False
            for line in port_infos:
                if "fail2ban" in line.lower(): continue
                if line.startswith("-"):
                    is_start = True
                    continue
                if not is_start:
                    continue
                item_fire = self._load_info(line, "port")
                if item_fire.get("Port") and item_fire["Port"] != "Anywhere" and "." not in item_fire["Port"]:
                    item_fire["Port"] = item_fire["Port"].replace(":", "-")
                    item_fire["Address"] = "all" if item_fire["Address"] == "Anywhere" else item_fire["Address"]

                    datas.append(item_fire)
            return datas
        except Exception as e:
            return []

    # 2024/3/19 上午 10:39 列出防火墙中所有input端口规则
    def list_input_port(self):
        '''
            @name 列出防火墙中所有input端口规则
            @author wzz <2024/3/19 上午 10:39>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        try:
            result = subprocess.run(
                [self.cmd_str, "status", "verbose"], capture_output=True, text=True, check=True
            )
            port_infos = result.stdout.split("\n")
            datas = []
            is_start = False
            for line in port_infos:
                if "fail2ban" in line.lower(): continue
                if line.startswith("-"):
                    is_start = True
                    continue
                if not is_start:
                    continue
                item_fire = self._load_info(line, "port")
                if item_fire.get("Port") and item_fire["Port"] != "Anywhere" and "." not in item_fire["Port"]:
                    item_fire["Port"] = item_fire["Port"].replace(":", "-")

                    if item_fire["Chain"] == "INPUT":
                        datas.append(item_fire)
            return datas
        except Exception as e:
            return []

    # 2024/3/19 上午 10:39 列出防火墙中所有output端口规则
    def list_output_port(self):
        '''
            @name 列出防火墙中所有output端口规则
            @author wzz <2024/3/19 上午 10:39>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        try:
            result = subprocess.run(
                [self.cmd_str, "status", "verbose"], capture_output=True, text=True, check=True
            )
            port_infos = result.stdout.split("\n")
            datas = []
            is_start = False
            for line in port_infos:
                if "fail2ban" in line.lower(): continue
                if line.startswith("-"):
                    is_start = True
                    continue
                if not is_start:
                    continue
                item_fire = self._load_info(line, "port")
                if item_fire.get("Port") and item_fire["Port"] != "Anywhere" and "." not in item_fire["Port"]:
                    item_fire["Port"] = item_fire["Port"].replace(":", "-")

                    if item_fire["Chain"] == "OUTPUT":
                        datas.append(item_fire)
            return datas
        except Exception as e:
            return []

    # 2024/3/19 上午 10:39 列出防火墙中所有的ip规则
    def list_address(self):
        '''
            @name 列出防火墙中所有的ip规则
            @author wzz <2024/3/19 上午 10:39>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        try:
            result = subprocess.run(
                [self.cmd_str, "status", "verbose"],  capture_output=True, text=True, check=True
            )
            port_infos = result.stdout.split("\n")
            datas = []
            is_start = False
            for line in port_infos:
                if "fail2ban" in line.lower(): continue
                if line.startswith("-"):
                    is_start = True
                    continue
                if not is_start:
                    continue
                item_fire = self._load_info(line, "address")
                if "Port" in item_fire: continue
                if item_fire.get("Address"):
                    datas.append(item_fire)
            return datas
        except Exception as e:
            return []

    # 2024/3/19 上午 10:39 列出防火墙中所有input的ip规则
    def list_input_address(self):
        '''
            @name 列出防火墙中所有input的ip规则
            @author wzz <2024/3/19 上午 10:39>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        try:
            result = subprocess.run(
                [self.cmd_str, "status", "verbose"],  capture_output=True, text=True, check=True
            )
            port_infos = result.stdout.split("\n")
            datas = []
            is_start = False
            for line in port_infos:
                if "fail2ban" in line.lower(): continue
                if line.startswith("-"):
                    is_start = True
                    continue
                if not is_start:
                    continue
                if " IN" not in line:
                    continue
                item_fire = self._load_info(line, "address")
                if "Port" in item_fire: continue
                if item_fire.get("Address"):
                    datas.append(item_fire)
            return datas
        except Exception as e:
            return []

    # 2024/3/19 上午 10:39 列出防火墙中所有output的ip规则
    def list_output_address(self):
        '''
            @name 列出防火墙中所有output的ip规则
            @author wzz <2024/3/19 上午 10:39>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        try:
            result = subprocess.run(
                [self.cmd_str, "status", "verbose"],  capture_output=True, text=True, check=True
            )
            port_infos = result.stdout.split("\n")
            datas = []
            is_start = False
            for line in port_infos:
                if "fail2ban" in line.lower(): continue
                if line.startswith("-"):
                    is_start = True
                    continue
                if not is_start:
                    continue
                if " OUT" not in line:
                    continue
                item_fire = self._load_info(line, "address")
                if "Port" in item_fire: continue
                if item_fire.get("Address"):
                    datas.append(item_fire)
            return datas
        except Exception as e:
            return []

    # 2024/3/19 下午 4:59 添加端口规则
    def input_port(self, info, operation):
        '''
            @name 添加端口规则
            @author wzz <2024/3/19 下午 4:59>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        try:
            if info["Strategy"] == "accept":
                info["Strategy"] = "allow"
            elif info["Strategy"] == "drop":
                info["Strategy"] = "deny"

            if "Port" in info and info["Port"].find('-') != -1:
                info["Port"] = info["Port"].replace('-', ':')

            if operation == "add":
                if info['Protocol'] == "tcp/udp":
                    cmd = "{cmd_str} allow {port}/tcp;{cmd_str} allow {port}/udp".format(cmd_str = self.cmd_str,port=info['Port'])
                    stdout, stderr = public.ExecShell(cmd)
                else:
                    stdout, stderr = public.ExecShell(self.cmd_str + " allow " + info['Port'] + "/" + info['Protocol'])
            else:
                if info['Protocol'] == "tcp/udp":
                    cmd = "{cmd_str} delete allow {port}/tcp;{cmd_str} delete allow {port}/udp".format(cmd_str=self.cmd_str,port=info['Port'])
                    stdout, stderr = public.ExecShell(cmd)
                else:
                    stdout, stderr = public.ExecShell(self.cmd_str + " delete allow " + info['Port'] + "/" + info['Protocol'])

            if stderr:
                if "setlocale" in stderr:
                    return self._result(True, "设置端口规则成功")
                return self._result(False, "设置端口规则失败:{}".format(stderr))

            return self._result(True, "设置端口规则成功")

        except Exception as e:
            if "setlocale" in str(e):
                return self._result(True, "设置端口规则成功")
            return self._result(False, "设置端口规则失败:{}".format(str(e)))

    # 2024/3/24 下午 11:28 设置output端口策略
    def output_port(self, info, operation):
        '''
            @name 设置output端口策略
            @param info: 端口号
            @param operation: 操作
            @return None
        '''
        try:
            if info["Strategy"] == "accept":
                info["Strategy"] = "allow"
            elif info["Strategy"] == "drop":
                info["Strategy"] = "deny"

            if "Port" in info and info["Port"].find('-') != -1:
                info["Port"] = info["Port"].replace('-', ':')

            if operation == "add":
                if info['Protocol'].find('/') != -1:
                    cmd = "{cmd_str} {strategy} out {port}/tcp;{cmd_str} {strategy} out {port}/udp".format(cmd_str=self.cmd_str,strategy = info['Strategy'],port=info['Port'])
                else:
                    cmd = "{} {} out {}/{}".format(self.cmd_str, info['Strategy'], info['Port'], info['Protocol'])
            else:
                if info['Protocol'].find('/') != -1:
                    cmd = "{cmd_str} delete {strategy} out {port}/tcp;{cmd_str} delete {strategy} out {port}/udp".format(cmd_str=self.cmd_str, strategy=info['Strategy'], port=info['Port'])
                else:
                    cmd = "{} delete {} out {}/{}".format(self.cmd_str, info['Strategy'], info['Port'], info['Protocol'])
            stdout, stderr = public.ExecShell(cmd)
            if stderr:
                if "setlocale" in stderr:
                    return self._result(True, "设置端口规则成功")
                return self._result(False, "设置output端口规则失败:{}".format(stderr))
            return self._result(True, "设置output端口规则成功")
        except Exception as e:
            if "setlocale" in str(e):
                return self._result(True, "设置output端口规则成功")
            return self._result(False, "设置output端口规则失败:{}".format(str(e)))

    # 2024/3/19 下午 4:58 复杂一些的规则管理
    def rich_rules(self, info, operation):
        '''
            @name 复杂一些的规则管理
            @author wzz <2024/3/19 下午 4:58>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        try:
            if info["Strategy"] == "accept":
                info["Strategy"] = "allow"
            elif info["Strategy"] == "drop":
                info["Strategy"] = "deny"
            else:
                return self._result(False, "未知的策略参数:{}".format(info["Strategy"]))

            if "Port" in info and info["Port"].find('-') != -1:
                info["Port"] = info["Port"].replace('-', ':')

            rule_str = "{} insert 1 {} ".format(self.cmd_str, info["Strategy"])
            if "Address" in info and public.is_ipv6(info['Address']):
                rule_str = "{} {} ".format(self.cmd_str, info["Strategy"])
            if operation == "remove":
                rule_str = "{} delete {} ".format(self.cmd_str, info["Strategy"])

            if "Address" in info and info['Address'] != "all":
                rule_str += "from {} ".format(info['Address'])
            if len(info.get("Protocol", "")) != 0 and "/" not in info['Protocol']:
                rule_str += "proto {} ".format(info['Protocol'])
            if len(info.get("Protocol", "")) != 0 and "/" in info['Protocol']:
                if "Address" in info and info['Address'] != "all":
                    if not "from {} ".format(info['Address']) in rule_str:
                        rule_str += "from any "
            if len(info.get("Port", "")) != 0:
                rule_str += "to any port {} ".format(info['Port'])

            if len(info.get("Protocol", "")) != 0 and "/" in info['Protocol']:
                for i in ["tcp", "udp"]:
                    cmd_str = rule_str + "proto {}".format(i)
                    stdout, stderr = public.ExecShell(cmd_str)
                    if stderr:
                        if "Rule added" in stdout or "Rule deleted" in stdout or "Rule updated" in stdout or "Rule inserted" in stdout or "Skipping adding existing rule" in stdout:
                            return self._result(True, "设置规则成功")
                        if "setlocale" in stderr:
                            return self._result(True, "设置规则成功")
                        return self._result(False, "规则设置失败:{}".format(stderr))

                return self._result(True, "设置规则成功")

            stdout, stderr = public.ExecShell(rule_str)
            if stderr:
                if "Rule added" in stdout or "Rule deleted" in stdout or "Rule updated" in stdout or "Rule inserted" in stdout or "Skipping adding existing rule" in stdout:
                    return self._result(True, "设置规则成功")
                if "setlocale" in stderr:
                    return self._result(True, "设置规则成功")
                return self._result(False, "规则设置失败:{}".format(stderr))
            return self._result(True, "设置规则成功")
        except Exception as e:
            if "setlocale" in str(e):
                return self._result(True, "设置规则成功")
            return self._result(False, "规则设置失败:{}".format(e))

    # 2024/3/24 下午 11:29 设置output rich_rules
    def output_rich_rules(self, info, operation):
        '''
            @name 设置output rich_rules
            @param info: 规则
            @param operation: 操作
            @return None
        '''
        try:
            if info["Strategy"] == "accept":
                info["Strategy"] = "allow"
            elif info["Strategy"] == "drop":
                info["Strategy"] = "deny"
            else:
                return self._result(False, "未知的策略: {}".format(info["Strategy"]))

            if "Port" in info and info["Port"].find('-') != -1:
                info["Port"] = info["Port"].replace('-', ':')

            rule_str = "{} insert 1 {} ".format(self.cmd_str, info["Strategy"])
            if "Address" in info and public.is_ipv6(info['Address']):
                rule_str = "{} {} ".format(self.cmd_str, info["Strategy"])
            if operation == "remove":
                rule_str = "{} delete {} ".format(self.cmd_str, info["Strategy"])

            if len(info.get("Address", "")) != 0:
                rule_str += "out from {} ".format(info['Address'])
            if len(info.get("Protocol", "")) != 0:
                rule_str += "proto {} ".format(info['Protocol'])
            if len(info.get("Port", "")) != 0:
                rule_str += "to any port {} ".format(info['Port'])
            stdout, stderr = public.ExecShell(rule_str)
            if stderr:
                if "Rule added" in stdout or "Rule deleted" in stdout or "Rule updated" in stdout or "Rule inserted" in stdout or "Skipping adding existing rule" in stdout:
                    return self._result(True, "设置output规则成功")
                if "setlocale" in stderr:
                    return self._result(True, "设置规则成功")
                return self._result(False, "outpu规则设置失败:{}".format(stderr))
            return self._result(True, "设置output规则成功")
        except Exception as e:
            if "setlocale" in str(e):
                return self._result(True, "设置output规则成功")
            return self._result(False, "outpu规则设置失败:{}".format(e))

    # 2024/3/19 下午 5:01 解析防火墙规则信息，返回字典格式数据，用于添加或删除防火墙规则
    def _load_info(self, line, fire_type):
        '''
            @name 解析防火墙规则信息，返回字典格式数据，用于添加或删除防火墙规则
            @author wzz <2024/3/19 上午 10:38>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        fields = line.split()
        item_info = {}
        if "LIMIT" in line or "ALLOW FWD" in line:
            return item_info
        if len(fields) < 4:
            return item_info
        if fields[0] == "Anywhere" and fire_type != "port":
            item_info["Strategy"] = "drop"

            if fields[1] != "(v6)":
                if fields[1] == "ALLOW":
                    item_info["Strategy"] = "accept"
                if fields[2] == "IN":
                    item_info["Chain"] = "INPUT"
                elif fields[2] == "OUT":
                    item_info["Chain"] = "OUTPUT"
                item_info["Address"] = fields[3] if fields[3] != "Anywhere" else "all"
                item_info["Family"] = "ipv4"
            else:
                if fields[2] == "ALLOW":
                    item_info["Strategy"] = "accept"
                if fields[3] == "IN":
                    item_info["Chain"] = "INPUT"
                elif fields[3] == "OUT":
                    item_info["Chain"] = "OUTPUT"
                item_info["Address"] = fields[4] if fields[4] != "Anywhere" else "all"
                item_info["Family"] = "ipv6"

            return item_info

        if "/" in fields[0]:
            item_info["Port"] = fields[0].split("/")[0]
            item_info["Protocol"] = fields[0].split("/")[1]
        else:
            item_info["Port"] = fields[0]
            item_info["Protocol"] = "tcp/udp"

        if "v6" in fields[1]:
            item_info["Family"] = "ipv6"
            if fields[2] == "ALLOW":
                item_info["Strategy"] = "accept"
            else:
                item_info["Strategy"] = "drop"

            if fields[3] == "IN":
                item_info["Chain"] = "INPUT"
            elif fields[3] == "OUT":
                item_info["Chain"] = "OUTPUT"
            item_info["Address"] = fields[4] if fields[4] != "Anywhere" else "all"

        else:
            item_info["Family"] = "ipv4" if ":" not in fields[3] else "ipv6"

            if fields[1] == "ALLOW":
                item_info["Strategy"] = "accept"
            else:
                item_info["Strategy"] = "drop"

            if fields[2] == "IN":
                item_info["Chain"] = "INPUT"
            elif fields[2] == "OUT":
                item_info["Chain"] = "OUTPUT"
            item_info["Address"] = fields[3] if fields[3] != "Anywhere" else "all"

        return item_info

    # 2024/3/25 下午 2:29 设置端口转发
    def port_forward(self, info, operation):
        '''
            @name 设置端口转发
            @param port: 端口号
            @param ip: ip地址
            @param operation: 操作
            @return None
        '''
        from firewallModel.app.iptables import Iptables
        self.firewall = Iptables()
        return self.firewall.port_forward(info, operation)

    # 2024/3/25 下午 2:34 获取所有端口转发列表
    def list_port_forward(self):
        '''
            @name 获取所有端口转发列表
            @return None
        '''
        from firewallModel.app.iptables import Iptables
        self.firewall = Iptables()
        return self.firewall.get_nat_prerouting_rules()

if __name__ == '__main__':
    args = sys.argv
    firewall = Ufw()
    ufw_status = firewall.status()
    if len(args) < 2:
        print("Welcome to the UFW (Uncomplicated Firewall) command-line interface!")
        print("Firewall status is :", ufw_status)
        print("Firewall version: ", firewall.version())
        if ufw_status == "not running":
            print("ufw未启动,请启动ufw后再执行命令!")
            print("启动命令: start")
            print()
            sys.exit(1)
        print()
        print("Available options:")
        print("1. Check Firewall Status: status")
        print("2. Check Firewall Version: version")
        print("3. Start Firewall: start")
        print("4. Stop Firewall: stop")
        print("5. Restart Firewall: restart")
        print("6. Reload Firewall: reload")
        print("7. List All Ports: list_port")
        print("8. List All IP Addresses: list_address")
        print("9. Add Port: add_port <port> <protocol>")
        print("10. Remove Port: remove_port <port> <protocol>")
        print("11. Add Port Rule: add_port_rule <address> <port> <protocol> <strategy> <operation>")
        print("12. Remove Port Rule: remove_port_rule <address> <port> <protocol> <strategy> <operation>")
        print("13. Add IP Rule: add_ip_rule <address> <strategy> <operation>")
        print("14. Remove IP Rule: remove_ip_rule <address> <strategy> <operation>")
        print()
        sys.exit(1)
    if args[1] == "status":
        print(firewall.status())
    elif args[1] == "version":
        print(firewall.version())
    elif args[1] == "start":
        error = firewall.start()
        if error:
            print(f"Error: {error}")
        else:
            print("Firewall started successfully.")
    elif args[1] == "stop":
        error = firewall.stop()
        if error:
            print(f"Error: {error}")
        else:
            print("Firewall stopped successfully.")
    elif args[1] == "restart":
        error = firewall.restart()
        if error:
            print(f"Error: {error}")
        else:
            print("Firewall restarted successfully.")
    elif args[1] == "reload":
        error = firewall.reload()
        if error:
            print(f"Error: {error}")
        else:
            print("Firewall reloaded successfully.")
    elif args[1] == "list_input_port":
        ports = firewall.list_input_port()
        for p in ports:
            print(p)
    elif args[1] == "list_output_port":
        ports = firewall.list_output_port()
        for p in ports:
            print(p)
    elif args[1] == "list_input_address":
        addresses = firewall.list_input_address()
        for a in addresses:
            print(a)
    elif args[1] == "list_output_address":
        addresses = firewall.list_output_address()
        for a in addresses:
            print(a)
    elif args[1] == "add_port":
        port = args[2]
        protocol = args[3]
        error = firewall.input_port(f"{port}/{protocol}", "allow")
        if error:
            print(f"Error: {error}")
        else:
            print(f"Port {port}/{protocol} added successfully.")
    elif args[1] == "remove_port":
        port = args[2]
        protocol = args[3]
        error = firewall.input_port(f"{port}/{protocol}", "remove")
        if error:
            print(f"Error: {error}")
        else:
            print(f"Port {port}/{protocol} removed successfully.")
    elif args[1] == "add_port_rule":
        address = args[2]
        port = args[3]
        protocol = args[4]
        strategy = args[5]
        operation = args[6]
        error = firewall.rich_rules(
            {"Address": address, "Port": port, "Protocol": protocol, "Strategy": strategy}, operation)
        if error:
            print(f"Error: {error}")
        else:
            print("Rich rule added successfully.")
    elif args[1] == "remove_port_rule":
        address = args[2]
        port = args[3]
        protocol = args[4]
        strategy = args[5]
        operation = args[6]
        error = firewall.rich_rules(
            {"Address": address, "Port": port, "Protocol": protocol, "Strategy": strategy}, operation)
        if error:
            print(f"Error: {error}")
        else:
            print("Rich rule removed successfully.")
    elif args[1] == "add_ip_rule":
        address = args[2]
        strategy = args[3]
        operation = args[4]
        error = firewall.rich_rules(
            {"Address": address, "Strategy": strategy}, operation)
        if error:
            print(f"Error: {error}")
        else:
            print("Rich rule added successfully.")
    elif args[1] == "remove_ip_rule":
        address = args[2]
        strategy = args[3]
        operation = args[4]
        error = firewall.rich_rules(
            {"Address": address, "Strategy": strategy}, operation)
        if error:
            print(f"Error: {error}")
        else:
            print("Rich rule removed successfully.")
    elif args[1] == "output_port":
        port = args[2]
        operation = args[3]
        error = firewall.output_port(port, operation)
        if error:
            print(f"Error: {error}")
        else:
            print(f"Output port {port} {operation} successfully.")
    elif args[1] == "output_rich_rules":
        address = args[2]
        port = args[3]
        protocol = args[4]
        strategy = args[5]
        operation = args[6]
        error = firewall.output_rich_rules(
            {"Address": address, "Port": port, "Protocol": protocol, "Strategy": strategy}, operation)
        if error:
            print(f"Error: {error}")
        else:
            print("Output rich rule added successfully.")
    else:
        print("Invalid args")
        sys.exit(1)

