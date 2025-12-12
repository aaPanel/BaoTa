# coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author: csj <csj@bt.cn>
# -------------------------------------------------------------------
import json
import os
import re

import public


class main():
    def __init__(self):
        #{name:安全项名称,desc:描述,suggest:修复建议,check:检查函数,repair:修复函数,value:获取当前值函数,status:状态}
        self.config = [
            {"name": "SSH默认端口", "desc": "修改SSH默认端口，提高服务器安全性","suggest":"使用高位非22端口", "check": self.check_ssh_port,"repair": None,"value":None},
            {"name": "密码复杂度策略", "desc": "启用密码复杂度检查，确保密码安全","suggest":"使用大于3的等级","check": self.check_ssh_minclass, "repair": self.repair_ssh_minclass,"value":None},
            {"name": "密码长度限制", "desc": "设置最低密码长度要求","suggest":"使用9-20位的密码", "check": self.check_ssh_security,"repair": self.repair_ssh_passwd_len,"value":None},
            {"name": "SSH登录告警", "desc": "SSH登录时发送告警通知","suggest":"开启SSH登录告警", "check": self.check_ssh_login_sender,"repair": None,"value":None},
            {"name": "root登录设置", "desc": "推荐仅允许密钥登录","suggest":"使用仅允许密钥登录", "check": self.check_ssh_login_root_with_key,"repair": None,"value":None},
            {"name": "SSH防爆破", "desc": "防止SSH暴力破解攻击","suggest":"开启防SSH破解", "check": self.check_ssh_fail2ban_brute, "repair": None,"status": False,"value":None},
            {"name": "面板登录告警", "desc": "面板登录时发送告警通知","suggest":"开启面板登录告警","check": self.check_panel_swing, "repair": None,"value":None},
            {"name": "面板登录动态口令认证", "desc": "启用TOTP动态口令增强安全性","suggest":"开启OTP动态口令验证", "check": self.check_panel_login_2fa,"repair": None,"value":None},
            {"name": "未登录响应状态码", "desc": "设置未登录访问时的HTTP响应状态码","suggest":"设置404为响应吗","check": self.check_panel_not_auth_code, "repair": None,"value":None},
            {"name": "面板开启SSL", "desc": "启用HTTPS加密传输（设置会重启面板）","suggest":"开启面板HTTPS", "check": self.check_panel_ssl,"repair": None,"value":None}
        ]
    
    def get_security_info(self, get):
        """
        @name 获取安全评分
        """
        for module in self.config:
            if module['check'] is not None:
                try:
                    check_status = module['check']()
                    # 统一支持 (status, value) 或包含 status 的 dict，或简单类型返回
                    if isinstance(check_status, tuple) and len(check_status) >= 2:
                        module['status'] = bool(check_status[0])
                        module['value'] = check_status[1]
                except:
                    module['status'] = False
                    module['value'] = None
            
            del module['check']
            del module['repair']
        
        # 总分
        total_score = 100
        # 每条的分数
        score = total_score / len(self.config)
        # 缺少的条数
        missing_count = 0
        for module in self.config:
            if module['status'] == False:
                missing_count += 1
        # 计算总分
        security_score = total_score - (missing_count * score)
        security_score = round(security_score, 2)
        
        # 计算得分文本
        score_text = ""
        if security_score >= 90:
            score_text = "安全"
        elif security_score >= 70:
            score_text = "较安全"
        elif security_score >= 50:
            score_text = "安全性一般"
        else:
            score_text = "不安全"
        
        public.set_module_logs('server_secury', 'get_security_info', 1)
        return public.return_data(True,{
            "security_data": self.config,
            "total_score": total_score,
            "score_text": score_text,
            "score": int(security_score)
        })
    
    def install_fail2ban(self,get):
        from panelPlugin import panelPlugin
        public.set_module_logs('server_secury', 'install_fail2ban', 1)
        return panelPlugin().install_plugin(get)
    
    def repair_security(self,get):
        """
        @name   修复安全项
        @parma  {"name":"","args":{}}
        """
        name = get.name
        if not name:
            return public.returnMsg(False,"缺少安全项参数")
        
        for security in self.config:
            if security["name"] == name and security["repair"] is not None:
                return security["repair"](get.args)
                
    def check_ssh_port(self):
        """
        @name 检查SSH端口是否为默认端口22
        @return (status, value)
        """
        current_port = public.get_ssh_port()
        return (current_port != 22, current_port)
    
    def check_ssh_minclass(self):
        """
        @name 检查SSH密码复杂度策略
        @return (status, value)
        """
        try:
            p_file = '/etc/security/pwquality.conf'
            p_body = public.readFile(p_file)
            if not p_body: 
                return (True, None)  # 无配置文件时认为无风险
            tmp = re.findall(r"\n\s*minclass\s+=\s+(.+)", p_body, re.M)
            if not tmp: 
                return (False, None)  # 未设置minclass
            minclass = tmp[0].strip()
            minclass_value = int(minclass)
            return (minclass_value >= 3, minclass_value)
        except:
            return (True, None)  # 异常时认为无风险
    
    def check_ssh_security(self):
        """
        @name 检查SSH密码长度限制
        @return (status, value)
        """
        try:
            p_file = '/etc/security/pwquality.conf'
            p_body = public.readFile(p_file)
            if not p_body: 
                return (True, None)  # 无配置文件时认为无风险
            tmp = re.findall(r"\s*minlen\s+=\s+(.+)", p_body, re.M)
            if not tmp: 
                return (True, None)  # 未设置minlen时认为无风险
            minlen = tmp[0].strip()
            minlen_value = int(minlen)
            return (minlen_value >= 9, minlen_value)
        except:
            return (True, None)  # 异常时认为无风险
    
    def check_panel_swing(self):
        """
        @name 检查面板登录告警是否开启
        @return (status, value)
        """
        tip_files = ['panel_login_send.pl','login_send_type.pl','login_send_mail.pl','login_send_dingding.pl']
        enabled_files = []
        for fname in tip_files:
            filename = 'data/' + fname
            if os.path.exists(filename):
                enabled_files.append(fname)
                break
        
        is_enabled = len(enabled_files) > 0
        value = None
        #获取回显数据
        if is_enabled:
            task_file_path = '/www/server/panel/data/mod_push_data/task.json'
            sender_file_path = '/www/server/panel/data/mod_push_data/sender.json'
            task_data = {}
            
            try:
                with open(task_file_path, 'r') as file:
                    tasks = json.load(file)
                
                # 读取发送者配置文件
                with open(sender_file_path, 'r') as file:
                    senders = json.load(file)
                sender_dict = {sender['id']: sender for sender in senders}
                
                # 查找特定的告警任务
                for task in tasks:
                    if task.get('keyword') == "panel_login":
                        task_data = task
                        sender_types = set()  # 使用集合来保证类型的唯一性
                        
                        # 对应sender的ID，获取sender_type，并保证唯一性
                        for sender_id in task.get('sender', []):
                            if sender_id in sender_dict:
                                sender_types.add(sender_dict[sender_id]['sender_type'])
                        
                        # 将唯一的通道类型列表转回列表格式，添加到告警数据中
                        task_data['channels'] = list(sender_types)
                        break
            except:
                pass
            value = task_data
        
        return (is_enabled, value)
    
    def check_ssh_login_sender(self):
        """
        @name 检查SSH登录告警是否启用
        @return (status, value)
        """
        from ssh_security import ssh_security
        result = ssh_security().get_login_send(None)
        current_value = result.get('status')
        return (bool(current_value), result)
    
    def check_ssh_login_root_with_key(self):
        """
        @name 检查SSH是否仅允许密钥登录root
        @return (status, value)
        """
        from ssh_security import ssh_security
        parsed = ssh_security().paser_root_login()
        current_policy = None
        try:
            current_policy = parsed[1]
        except Exception:
            # 兜底从返回结构中取可能的字段
            if isinstance(parsed, dict):
                current_policy = parsed.get('policy')
        status = (current_policy == 'without-password')
        return (status, current_policy)
    
    def check_ssh_fail2ban_brute(self):
        """
        @name 检查SSH防爆破是否启用
        @return (status, value)
        """
        from safeModel.sshModel import main as sshmod
        cfg = sshmod._get_ssh_fail2ban()
        current_value = None
        try:
            current_value = cfg['status']
        except Exception:
            current_value = cfg
        status = (current_value == 1)
        return (status, current_value)
    
    def check_panel_login_2fa(self):
        """
        @name 检查面板登录动态口令认证是否启用
        @return (status, value)
        """
        from config import config
        current_value = config().check_two_step(None)['status']
        return (bool(current_value), current_value)
    
    def check_panel_not_auth_code(self):
        """
        @name 检查面板未登录响应状态码是否设置为403
        @return (status, value)
        """
        from config import config
        current_code = config().get_not_auth_status()
        return (current_code != 0, current_code)
    
    def check_panel_ssl(self):
        """
        @name 检查面板是否开启SSL
        @return (status, value)
        """
        enabled = os.path.exists('data/ssl.pl')
        return (bool(enabled), enabled)
    
    def repair_ssh_minclass(self,args):
        """
        @name 修复SSH密码复杂度
        @param {"minclass":9}
        """
        if args["minclass"] is None or args["minclass"] <=0:
            return public.returnMsg(False,"修复失败，参数错误")
        minclass = int(args["minclass"])
        
        file = "/etc/security/pwquality.conf"
        result = {"status": False, "msg": "SSH密码复杂度设置失败,请关闭系统加固或手动设置"}
        if not os.path.exists(file): public.ExecShell("apt install libpam-pwquality -y")
        if os.path.exists(file):
            f_data = public.readFile(file)
            if re.findall("\n\s*minclass\s*=\s*\d*", f_data):
                file_result = re.sub("\n\s*minclass\s*=\s*\d*", "\nminclass = {}".format(minclass), f_data)
            else:
                file_result = f_data + "\nminclass = {}".format(minclass)
            public.writeFile(file, file_result)
            f_data = public.readFile(file)
            if f_data.find("minclass = {}".format(minclass)) != -1:
                result["status"] = True
                result["msg"] = "已设置ssh密码最小复杂度"
        return result
    
    def repair_ssh_passwd_len(self,args):
        '''
        @name SSH密码最小长度设置
        @param {"len":9}
        '''
        if args['len'] is None or args['len'] <= 0:
            return public.returnMsg(False,"修复失败，参数错误")
        pwd_len = int(args['len'])
        file = "/etc/security/pwquality.conf"
        result = {"status": False, "msg": "SSH密码最小长度设置失败,请手动设置"}
        if not os.path.exists(file): public.ExecShell("apt install libpam-pwquality -y")
        if os.path.exists(file):
            f_data = public.readFile(file)
            ssh_minlen = "\n#?\s*minlen\s*=\s*\d*"
            file_result = re.sub(ssh_minlen, "\nminlen = {}".format(pwd_len), f_data)
            public.writeFile(file, file_result)
            f_data = public.readFile(file)
            if f_data.find("minlen = {}".format(pwd_len)) != -1:
                result["status"] = True
                result["msg"] = "已设置SSH密码最小长度为{}".format(pwd_len)
        return result