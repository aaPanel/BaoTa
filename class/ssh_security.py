# coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2015-2017 宝塔软件(http:#bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author: 梁凯强 <1249648969@qq.com>
# -------------------------------------------------------------------
# SSH 安全类
# ------------------------------
import shutil
import warnings  # 处理requests库版本警告

from flask import send_file

warnings.filterwarnings("ignore", message=r".*doesn't\s+match\s+a\s+supported\s+version", module="requests")

import public, os, re, send_mail, json
from datetime import datetime


class ssh_security:
    __type_list = ['ed25519', 'ecdsa', 'rsa', 'dsa']
    __key_type_file = '{}/data/ssh_key_type.pl'.format(public.get_panel_path())
    __key_files = ['/root/.ssh/id_ed25519', '/root/.ssh/id_ecdsa', '/root/.ssh/id_rsa', '/root/.ssh/id_rsa_bt']
    __type_files = {
        "ed25519": "/root/.ssh/id_ed25519",
        "ecdsa": "/root/.ssh/id_ecdsa",
        "rsa": "/root/.ssh/id_rsa",
        "dsa": "/root/.ssh/id_dsa"
    }
    open_ssh_login = public.get_panel_path() + '/data/open_ssh_login.pl'

    __SSH_CONFIG = '/etc/ssh/sshd_config'
    __ip_data = None
    __ClIENT_IP = '/www/server/panel/data/host_login_ip.json'
    __REPAIR = {"1": {"id": 1, "type": "file", "harm": "高", "repaired": "1", "level": "3", "name": "确保SSH MaxAuthTries 设置为3-6之间", "file": "/etc/ssh/sshd_config", "Suggestions": "加固建议   在/etc/ssh/sshd_config 中取消MaxAuthTries注释符号#, 设置最大密码尝试失败次数3-6 建议为4", "repair": "MaxAuthTries 4", "rule": [{"re": "\nMaxAuthTries\\s*(\\d+)", "check": {"type": "number", "max": 7, "min": 3}}], "repair_loophole": [{"re": "\n?#?MaxAuthTries\\s*(\\d+)", "check": "\nMaxAuthTries 4"}]},
                "2": {"id": 2, "repaired": "1", "type": "file", "harm": "高", "level": "3", "name": "SSHD 强制使用V2安全协议", "file": "/etc/ssh/sshd_config", "Suggestions": "加固建议   在/etc/ssh/sshd_config 文件按如相下设置参数", "repair": "Protocol 2", "rule": [{"re": "\nProtocol\\s*(\\d+)", "check": {"type": "number", "max": 3, "min": 1}}], "repair_loophole": [{"re": "\n?#?Protocol\\s*(\\d+)", "check": "\nProtocol 2"}]},
                "3": {"id": 3, "repaired": "1", "type": "file", "harm": "高", "level": "3", "name": "设置SSH空闲超时退出时间", "file": "/etc/ssh/sshd_config", "Suggestions": "加固建议   在/etc/ssh/sshd_config 将ClientAliveInterval设置为300到900，即5-15分钟，将ClientAliveCountMax设置为0-3", "repair": "ClientAliveInterval 600  ClientAliveCountMax 2", "rule": [{"re": "\nClientAliveInterval\\s*(\\d+)", "check": {"type": "number", "max": 900, "min": 300}}], "repair_loophole": [{"re": "\n?#?ClientAliveInterval\\s*(\\d+)", "check": "\nClientAliveInterval 600"}]},
                "4": {"id": 4, "repaired": "1", "type": "file", "harm": "高", "level": "3", "name": "确保SSH LogLevel 设置为INFO", "file": "/etc/ssh/sshd_config", "Suggestions": "加固建议   在/etc/ssh/sshd_config 文件以按如下方式设置参数（取消注释）", "repair": "LogLevel INFO", "rule": [{"re": "\nLogLevel\\s*(\\w+)", "check": {"type": "string", "value": ["INFO"]}}], "repair_loophole": [{"re": "\n?#?LogLevel\\s*(\\w+)", "check": "\nLogLevel INFO"}]},
                "5": {"id": 5, "repaired": "1", "type": "file", "harm": "高", "level": "3", "name": "禁止SSH空密码用户登陆", "file": "/etc/ssh/sshd_config", "Suggestions": "加固建议  在/etc/ssh/sshd_config 将PermitEmptyPasswords配置为no", "repair": "PermitEmptyPasswords no", "rule": [{"re": "\nPermitEmptyPasswords\\s*(\\w+)", "check": {"type": "string", "value": ["no"]}}], "repair_loophole": [{"re": "\n?#?PermitEmptyPasswords\\s*(\\w+)", "check": "\nPermitEmptyPasswords no"}]},
                "6": {"id": 6, "repaired": "1", "type": "file", "name": "SSH使用默认端口22", "harm": "高", "level": "3", "file": "/etc/ssh/sshd_config", "Suggestions": "加固建议   在/etc/ssh/sshd_config 将Port 设置为6000到65535随意一个, 例如", "repair": "Port 60151", "rule": [{"re": "Port\\s*(\\d+)", "check": {"type": "number", "max": 65535, "min": 22}}], "repair_loophole": [{"re": "\n?#?Port\\s*(\\d+)", "check": "\nPort 65531"}]}}
    __root_login_types = {'yes': 'yes - 可密码和密钥登录', 'no': 'no - 禁止登录', 'without-password': 'without-password - 只能密钥登录', 'forced-commands-only': 'forced-commands-only - 只能执行命令'}

    def __init__(self):
        if not public.M('sqlite_master').where('type=? AND name=?', ('table', 'ssh_login_record')).count():
            public.M('').execute('''CREATE TABLE ssh_login_record (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                addr TEXT,
                server_ip TEXT,
                user_agent TEXT,
                ssh_user TEXT,
                login_time INTEGER DEFAULT 0,
                close_time INTEGER DEFAULT 0,
                video_addr TEXT);''')
            public.M('').execute('CREATE INDEX ssh_login_record ON ssh_login_record (addr);')

        if not os.path.exists(self.__ClIENT_IP):
            public.WriteFile(self.__ClIENT_IP, json.dumps([]))
        self.__mail = send_mail.send_mail()
        self.__mail_config = self.__mail.get_settings()
        try:
            self.__ip_data = json.loads(public.ReadFile(self.__ClIENT_IP))
        except:
            self.__ip_data = []

    def get_ssh_key_type(self):
        '''
        获取ssh密钥类型
        @author hwliang
        :return:
        '''
        default_type = 'rsa'
        if not os.path.exists(self.__key_type_file):
            return default_type
        new_type = public.ReadFile(self.__key_type_file)
        if new_type in self.__type_list:
            return new_type
        return default_type

    def return_python(self):
        if os.path.exists('/www/server/panel/pyenv/bin/python'): return '/www/server/panel/pyenv/bin/python'
        if os.path.exists('/usr/bin/python'): return '/usr/bin/python'
        if os.path.exists('/usr/bin/python3'): return '/usr/bin/python3'
        return 'python'

    def return_profile(self):
        if os.path.exists('/root/.bash_profile'): return '/root/.bash_profile'
        if os.path.exists('/etc/profile'): return '/etc/profile'
        fd = open('/root/.bash_profil', mode="w", encoding="utf-8")
        fd.close()
        return '/root/.bash_profil'

    def return_bashrc(self):
        if os.path.exists('/root/.bashrc'): return '/root/.bashrc'
        if os.path.exists('/etc/bashrc'): return '/etc/bashrc'
        if os.path.exists('/etc/bash.bashrc'): return '/etc/bash.bashrc'
        fd = open('/root/.bashrc', mode="w", encoding="utf-8")
        fd.close()
        return '/root/.bashrc'

    def check_files(self):
        try:
            json.loads(public.ReadFile(self.__ClIENT_IP))
        except:
            public.WriteFile(self.__ClIENT_IP, json.dumps([]))

    def get_ssh_port(self):
        conf = public.readFile(self.__SSH_CONFIG)
        if not conf: conf = ''
        tmp1 = re.search(r"#*Port\s+([0-9]+)\s*\n", conf)
        port = '22'
        if tmp1:
            port = tmp1.groups(0)[0]
        return port

    # 主判断函数
    def check_san_baseline(self, base_json):
        if base_json['type'] == 'file':
            if 'check_file' in base_json:
                if not os.path.exists(base_json['check_file']):
                    return False
            else:
                if os.path.exists(base_json['file']):
                    ret = public.ReadFile(base_json['file'])
                    for i in base_json['rule']:
                        valuse = re.findall(i['re'], ret)
                        if i['check']['type'] == 'number':
                            if not valuse: return False
                            if not valuse[0]: return False
                            valuse = int(valuse[0])
                            if valuse > i['check']['min'] and valuse < i['check']['max']:
                                return True
                            else:
                                return False
                        elif i['check']['type'] == 'string':
                            if not valuse: return False
                            if not valuse[0]: return False
                            valuse = valuse[0]
                            if valuse in i['check']['value']:
                                return True
                            else:
                                return False
                return True

    def san_ssh_security(self, get):
        data = {"num": 100, "result": []}
        result = []
        ret = self.check_san_baseline(self.__REPAIR['1'])
        if not ret: result.append(self.__REPAIR['1'])
        ret = self.check_san_baseline(self.__REPAIR['2'])
        if not ret: result.append(self.__REPAIR['2'])
        ret = self.check_san_baseline(self.__REPAIR['3'])
        if not ret: result.append(self.__REPAIR['3'])
        ret = self.check_san_baseline(self.__REPAIR['4'])
        if not ret: result.append(self.__REPAIR['4'])
        ret = self.check_san_baseline(self.__REPAIR['5'])
        if not ret: result.append(self.__REPAIR['5'])
        ret = self.check_san_baseline(self.__REPAIR['6'])
        if not ret: result.append(self.__REPAIR['6'])
        data["result"] = result
        if len(result) >= 1:
            data['num'] = data['num'] - (len(result) * 10)
        return data

    ################## SSH 登陆报警设置 ####################################
    def send_mail_data(self, title, body, login_ip, type=None):
        # public.print_log(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
        # public.print_log((title, body, login_ip))
        from panel_msg.collector import SitePushMsgCollect
        msg = SitePushMsgCollect.ssh_login(body)
        push_data = {
            "login_ip": "" if body.find("后门用户") != -1 else ( login_ip if login_ip != "" else "未知ip"),
            "msg_list": ['>发送内容：' + body]
        }
        # public.print_log(push_data)
        try:
            import sys
            if "/www/server/panel" not in sys.path:
                sys.path.insert(0, "/www/server/panel")

            from mod.base.push_mod import push_by_task_keyword
            # public.print_log(push_data)
            res = push_by_task_keyword("ssh_login", "ssh_login", push_data=push_data)
            if res:
                return
        except:
            pass

        try:
            login_send_type_conf = "/www/server/panel/data/ssh_send_type.pl"
            if not os.path.exists(login_send_type_conf):
                login_type = "mail"
            else:
                login_type = public.readFile(login_send_type_conf).strip()
                if not login_type:
                    login_type = "mail"
            object = public.init_msg(login_type.strip())
            if not object:
                return False
            if login_type == "mail":
                data = {}
                data['title'] = title
                data['msg'] = body
                object.push_data(data)
            elif login_type == "wx_account":
                from push.site_push import ToWechatAccountMsg
                if body.find("后门用户") != -1:
                    msg = ToWechatAccountMsg.ssh_login("")
                else:
                    msg = ToWechatAccountMsg.ssh_login(login_ip if login_ip != "" else "未知ip")
                object.send_msg(msg)
            else:
                msg = public.get_push_info("SSH登录告警", ['>发送内容：' + body])
                msg['push_type'] = "SSH登录告警"
                object.push_data(msg)
        except:
            pass

    # 检测非UID为0的账户
    def check_user(self):
        ret = []
        cfile = '/etc/passwd'
        if os.path.exists(cfile):
            f = open(cfile, 'r')
            for i in f:
                i = i.strip().split(":")
                if i[2] == '0' and i[3] == '0':
                    if i[0] == 'root': continue
                    ret.append(i[0])
        if ret:
            data = ''.join(ret)
            public.run_thread(self.send_mail_data, args=(public.GetLocalIp() + '服务器存在后门用户', public.GetLocalIp() + '服务器存在后门用户' + data + '检查/etc/passwd文件', "",))
            return True
        else:
            return False

    # 记录root 的登陆日志

    # 返回登陆IP
    def return_ip(self, get):
        self.check_files()
        return public.returnMsg(True, self.__ip_data)

    # 添加IP白名单
    def add_return_ip(self, get):
        ip = get.ip.strip()
        try:
            import IPy
            IPy.IP(ip)
        except:
            return public.returnMsg(False, "请输入正确的IP地址")
        self.check_files()
        if ip in self.__ip_data:
            return public.returnMsg(False, "已经存在")
        else:
            self.__ip_data.append(ip)
            public.writeFile(self.__ClIENT_IP, json.dumps(self.__ip_data))
            return public.returnMsg(True, "添加成功")

    def del_return_ip(self, get):
        self.check_files()
        if get.ip.strip() in self.__ip_data:
            self.__ip_data.remove(get.ip.strip())
            public.writeFile(self.__ClIENT_IP, json.dumps(self.__ip_data))
            return public.returnMsg(True, "删除成功")
        else:
            return public.returnMsg(False, "不存在")

    # 取登陆的前50个条记录
    def login_last(self):
        self.check_files()
        data = public.ExecShell('last -n 50')
        data = re.findall("(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)", data[0])
        if data >= 1:
            data2 = list(set(data))
            for i in data2:
                if not i in self.__ip_data:
                    self.__ip_data.append(i)
            public.writeFile(self.__ClIENT_IP, json.dumps(self.__ip_data))
        return self.__ip_data

    # 获取ROOT当前登陆的IP
    def get_ip(self):
        data = public.ExecShell(''' who am i |awk ' {print $5 }' ''')
        data = re.findall("(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)", data[0])
        return data

    def get_user(self):
        data = public.ExecShell('whoami')
        return data[0].strip()

    def get_logs(self, get):
        import page
        page = page.Page();
        count = public.M('logs').where('type=?', ('SSH安全',)).count()
        limit = 10
        info = {}
        info['count'] = count
        info['row'] = limit
        info['p'] = 1
        if hasattr(get, 'p'):
            info['p'] = int(get['p'])
        info['uri'] = get
        info['return_js'] = ''
        if hasattr(get, 'tojs'):
            info['return_js'] = get.tojs
        data = {}
        # 获取分页数据
        data['page'] = page.GetPage(info, '1,2,3,4,5,8')
        data['data'] = public.M('logs').where('type=?', (u'SSH安全',)).order('id desc').limit(
            str(page.SHIFT) + ',' + str(page.ROW)).field('log,addtime').select()
        return data

    def get_server_ip(self):
        if os.path.exists('/www/server/panel/data/iplist.txt'):
            data = public.ReadFile('/www/server/panel/data/iplist.txt')
            return data.strip()
        else:
            return '127.0.0.1'

    # 登陆的情况下
    def login(self):
        self.check_files()
        self.check_user()
        self.__ip_data = json.loads(public.ReadFile(self.__ClIENT_IP))
        ip = self.get_ip()
        login_user = self.get_user()
        if len(ip[0]) == 0: return False
        try:
            import time,IPy
            mDate = time.strftime('%Y-%m-%d %X', time.localtime())
            # 检查IP是否在白名单中
            for ip_data in self.__ip_data:
                if ip[0] in IPy.IP(ip_data):
                    if public.M('logs').where('type=? and addtime=?', ('SSH安全', mDate,)).count(): return False
                    public.WriteLog('SSH安全',self.get_server_ip() + '服务器登陆登陆IP为' + ip[0] + '登陆用户为' + login_user)
                    return False
            # 获取需要告警的用户列表
            user_send_path = os.path.join(public.get_panel_path(), "data/user_send.json")
            if public.M('logs').where('type=? and addtime=?', ('SSH安全', mDate,)).count(): return False

            # 新版的设置了发送告警用户
            if not os.path.exists(user_send_path):
                login_user = "root"
            else:
                if os.path.exists(user_send_path):
                    data = json.loads(public.readFile(user_send_path))
                    if not data or login_user not in data:
                        return False

            # 发送告警
            public.run_thread(self.send_mail_data, args=(self.get_server_ip() + '服务器异常登陆', public.GetLocalIp() + '服务器存在异常登陆登陆IP为' + ip[0] + '登陆用户为' + login_user, ip[0],))
            # 记录日志
            public.WriteLog('SSH安全', public.GetLocalIp() + '服务器存在异常登陆登陆IP为' + ip[0] + '登陆用户为' + login_user)
            return True
        except:
            pass

    # 修复bashrc文件
    def repair_bashrc(self):
        data = public.ReadFile(self.return_bashrc())
        if re.search(self.return_python() + ' /www/server/panel/class/ssh_security.py', data):
            public.WriteFile(self.return_bashrc(), data.replace(self.return_python() + ' /www/server/panel/class/ssh_security.py login', ''))
            # 遗留的错误信息
            datassss = public.ReadFile(self.return_bashrc())
            if re.search(self.return_python(), datassss):
                public.WriteFile(self.return_bashrc(), datassss.replace(self.return_python(), ''))

    # 开启监控
    def start_jian(self, get):
        self.repair_bashrc()
        data = public.ReadFile(self.return_profile())
        if not re.search(self.return_python() + ' /www/server/panel/class/ssh_security.py', data):
            cmd = '''shell="%s /www/server/panel/class/ssh_security.py login"
nohup  `${shell}` &>/dev/null &
disown $!''' % (self.return_python())
            public.WriteFile(self.return_profile(), data.strip() + '\n' + cmd)
            return public.returnMsg(True, '开启成功')
        return public.returnMsg(False, '开启失败')

    # 关闭监控
    def stop_jian(self, get):
        data = public.ReadFile(self.return_profile())
        if re.search(self.return_python() + ' /www/server/panel/class/ssh_security.py', data):
            cmd = '''shell="%s /www/server/panel/class/ssh_security.py login"''' % (self.return_python())
            data = data.replace(cmd, '')
            cmd = '''nohup  `${shell}` &>/dev/null &'''
            data = data.replace(cmd, '')
            cmd = '''disown $!'''
            data = data.replace(cmd, '')
            public.WriteFile(self.return_profile(), data)
            # 检查是否还存在遗留
            if re.search(self.return_python() + ' /www/server/panel/class/ssh_security.py', data):
                public.WriteFile(self.return_profile(), data.replace(self.return_python() + ' /www/server/panel/class/ssh_security.py login', ''))
            # 遗留的错误信息
            datassss = public.ReadFile(self.return_profile())
            if re.search(self.return_python(), datassss):
                public.WriteFile(self.return_profile(), datassss.replace(self.return_python(), ''))

            return public.returnMsg(True, '关闭成功')
        else:
            return public.returnMsg(True, '关闭成功')

    # 监控状态
    def get_jian(self, get):
        data = public.ReadFile(self.return_profile())
        if re.search('/www/server/panel/class/ssh_security.py login', data):
            return public.returnMsg(True, '1')
        else:
            return public.returnMsg(False, '1')

    def set_root_password(self, get):
        """
        @name 设置root密码
        @param get:
        @return:
        """
        password = get.password if "password" in get else ""
        username = get.username if "username" in get else ""
        if not password: return public.returnMsg(False, "密码不能为空")
        if len(password) < 8: return public.returnMsg(False, "密码长度不能小于8位")
        if get.username not in self.get_sys_user(get)['msg']:
            return public.returnMsg(False, '用户名已存在')

        has_letter = bool(re.search(r'[a-zA-Z!@#$%^&*()-_+=]', password))
        has_digit_or_symbol = bool(re.search(r'[0-9!@#$%^&*()-_+=]', password))
        if not has_letter or not has_digit_or_symbol: return public.returnMsg(False, "密码必须包含字母和数字或符号")

        if username == "root":
            cmd_result, cmd_err = public.ExecShell("echo root:%s|chpasswd" % password)
            if cmd_err:
                cmd_result, cmd_err = public.ExecShell("usermod -p $(openssl passwd -1 \"%s\") root" % password)
        else:
            cmd_result, cmd_err = public.ExecShell("echo %s:%s|chpasswd" % (username, password))
            if cmd_err:
                cmd_result, cmd_err = public.ExecShell("usermod -p $(openssl passwd -1 \"%s\") %s" % (password, username))

        if cmd_err: return public.returnMsg(False, "设置失败")
        public.WriteLog("SSH管理", "【安全】-【SSH管理】-【设置%s密码】" % username)
        return public.returnMsg(True, "设置成功")

    def set_anti_conf(self, get):
        """
        @name 设置SSH防爆破
        @param get:
        @return:
        """
        param_dict = {
            'type': 'edit',
            'act': 'true',
            'maxretry': '30',
            'findtime': '300',
            'bantime': '600',
            'port': "{}".format(public.get_sshd_port()),
            'mode': 'sshd'
        }
        _set_up_path = "/www/server/panel/plugin/fail2ban"
        _config = _set_up_path + "/config.json"
        if not os.path.exists(_set_up_path + "/fail2ban_main.py"):
            return public.returnMsg(False, "fail2ban插件未安装")

        if not os.path.exists(_config):
            param_dict["type"] = "add"

        if os.path.exists(_config):
            _conf_data = json.loads(public.ReadFile(_config))

            if not "sshd" in _conf_data:
                param_dict["type"] = "add"

            if "sshd" in _conf_data:
                param_dict["maxretry"] = _conf_data["sshd"]["maxretry"]
                param_dict["findtime"] = _conf_data["sshd"]["findtime"]
                param_dict["bantime"] = _conf_data["sshd"]["bantime"]

        if "maxretry" in get:
            param_dict["maxretry"] = get.maxretry
        if "findtime" in get:
            param_dict["findtime"] = get.findtime
        if "bantime" in get:
            param_dict["bantime"] = get.bantime
        if "act" in get:
            param_dict["act"] = get.act

        param_dict = public.to_dict_obj(param_dict)

        public.WriteLog("SSH管理", "【安全】-【SSH管理】-【设置SSH防爆破状态】")
        import PluginLoader
        return PluginLoader.plugin_run('fail2ban', 'set_anti', param_dict)

    def get_anti_conf(self, get):
        """
        @name 获取SSH防爆破配置
        @param get:
        @return:
        """
        result_data = {
            'maxretry': '30',
            'findtime': '300',
            'bantime': '600'
        }
        _set_up_path = "/www/server/panel/plugin/fail2ban"
        _config = _set_up_path + "/config.json"
        if not os.path.exists(_set_up_path + "/fail2ban_main.py"):
            return public.returnMsg(False, "fail2ban插件未安装")

        if not os.path.exists(_config):
            return result_data

        _conf_data = json.loads(public.ReadFile(_config))
        if not "sshd" in _conf_data:
            return result_data

        result_data["maxretry"] = _conf_data["sshd"]["maxretry"]
        result_data["findtime"] = _conf_data["sshd"]["findtime"]
        result_data["bantime"] = _conf_data["sshd"]["bantime"]

        return result_data

    def get_sshd_anti_logs(self, get):
        """
        @name 获取SSH防爆破日志
        @param get:
        @return:
        """
        get = public.dict_obj()
        get.mode = "sshd"
        import PluginLoader
        logs_result = PluginLoader.plugin_run('fail2ban', 'get_status', get)

        if type(logs_result["msg"]) == str:
            return logs_result
        if logs_result["status"] == False:
            return logs_result

        return {
            "currently_failed": logs_result["msg"]["currently_failed"],
            "total_failed": logs_result["msg"]["total_failed"],
            "currently_banned": logs_result["msg"]["currently_banned"],
            "total_banned": logs_result["msg"]["total_banned"],
            "banned_ip_list": logs_result["msg"]["banned_ip_list"]
        }

    def del_ban_ip(self, get):
        """
        删除封锁IP
        @param get:
        @return:
        """
        get.mode = "sshd"
        get.ip = get.ip
        import PluginLoader
        return PluginLoader.plugin_run('fail2ban', 'ban_ip_release', get)

    def set_password(self, get):
        '''
        开启密码登陆
        get: 无需传递参数
        '''
        ssh_password = '\n#?PasswordAuthentication\s\w+'
        file = public.readFile(self.__SSH_CONFIG)
        if not file: return public.returnMsg(False, '错误：sshd_config配置文件不存在，无法继续!')
        if len(re.findall(ssh_password, file)) == 0:
            file_result = file + '\nPasswordAuthentication yes'
        else:
            file_result = re.sub(ssh_password, '\nPasswordAuthentication yes', file)
        self.wirte(self.__SSH_CONFIG, file_result)
        public.ExecShell("sed -i 's/^PasswordAuthentication no$/PasswordAuthentication yes/' /etc/ssh/sshd_config.d/*.conf")
        self.restart_ssh()
        public.WriteLog('SSH管理', '开启密码登陆')
        return public.returnMsg(True, '开启成功')

    def set_sshkey(self, get):
        '''
        设置ssh 的key
        参数 ssh=rsa&type=yes
        '''

        ssh_type = ['yes', 'no']
        ssh = get.ssh
        if not ssh in ssh_type: return public.returnMsg(False, 'ssh选项失败')
        s_type = get.type
        if not s_type in self.__type_list: return public.returnMsg(False, '加密方式错误')
        authorized_keys = '/root/.ssh/authorized_keys'
        file = ['/root/.ssh/id_{}.pub'.format(s_type), '/root/.ssh/id_{}'.format(s_type)]
        for i in file:
            if os.path.exists(i):
                public.ExecShell('sed -i "\~$(cat %s)~d" %s' % (file[0], authorized_keys))
                os.remove(i)
        os.system("ssh-keygen -t {s_type} -P '' -f /root/.ssh/id_{s_type} |echo y".format(s_type=s_type))
        if os.path.exists(file[0]):
            public.ExecShell('cat %s >> %s && chmod 600 %s' % (file[0], authorized_keys, authorized_keys))
            rec = '\n#?RSAAuthentication\s\w+'
            rec2 = '\n#?PubkeyAuthentication\s\w+'
            file = public.readFile(self.__SSH_CONFIG)
            if not file: return public.returnMsg(False, '错误：sshd_config配置文件不存在，无法继续!')
            if len(re.findall(rec, file)) == 0: file = file + '\nRSAAuthentication yes'
            if len(re.findall(rec2, file)) == 0: file = file + '\nPubkeyAuthentication yes'
            file_ssh = re.sub(rec, '\nRSAAuthentication yes', file)
            file_result = re.sub(rec2, '\nPubkeyAuthentication yes', file_ssh)
            if ssh == 'no':
                ssh_password = '\n#?PasswordAuthentication\s\w+'
                if len(re.findall(ssh_password, file_result)) == 0:
                    file_result = file_result + '\nPasswordAuthentication no'
                else:
                    file_result = re.sub(ssh_password, '\nPasswordAuthentication no', file_result)
            self.wirte(self.__SSH_CONFIG, file_result)
            public.writeFile(self.__key_type_file, s_type)
            self.restart_ssh()
            public.WriteLog('SSH管理', '设置SSH密钥认证，并成功生成密钥')
            return public.returnMsg(True, '开启成功')
        else:
            public.WriteLog('SSH管理', '设置SSH密钥认证失败')
            return public.returnMsg(False, '开启失败')

        # 取SSH信息

    def get_msg_push_list(self, get):
        """
        @name 获取消息通道配置列表
        @auther: cjxin
        @date: 2022-08-16
        """
        config = [
            {
                "name": "wx_account",
                "title": "微信公众号",
                "version": "1.0",
                "date": "2022-08-19",
                "help": "https://www.bt.cn",
                "ps": "宝塔微信公众号通知，用于接收面板消息推送"
            },
            {
                "name": "mail",
                "title": "邮箱",
                "version": "1.1",
                "date": "2022-08-10",
                "help": "https://www.bt.cn/bbs/thread-66183-1-1.html",
                "ps": "宝塔邮箱消息通道，用于接收面板消息推送"
            },
            {
                "name": "dingding",
                "title": "钉钉",
                "version": "1.2",
                "date": "2022-08-10",
                "help": "https://www.bt.cn/bbs/thread-44497-1-1.html",
                "ps": "宝塔钉钉消息通道，用于接收面板消息推送"
            },

            {
                "name": "weixin",
                "title": "企业微信",
                "version": "1.2",
                "date": "2022-08-10",
                "help": "https://www.bt.cn/bbs/thread-52540-1-1.html",
                "ps": "宝塔企业微信消息通道，用于接收面板消息推送"
            },
            {
                "name": "feishu",
                "title": "飞书",
                "version": "1.2",
                "date": "2022-08-10",
                "help": "https://www.bt.cn/bbs/",
                "ps": "宝塔飞书消息通道，用于接收面板消息推送"
            },
            {
                "name": "sms",
                "title": "短信通知",
                "version": "1.1",
                "date": "2022-08-02",
                "help": "https://www.bt.cn",
                "ps": "宝塔短信通知，用于接收面板消息推送"
            }]
        cpath = 'data/msg.json'
        data = {}
        if os.path.exists(cpath):
            try:
                msgs = json.loads(public.readFile(cpath))
            except:
                msgs = config
                public.WriteFile(cpath, json.dumps(msgs))
            for x in msgs:
                x['setup'] = False
                x['info'] = False
                key = x['name']
                try:
                    obj = public.init_msg(x['name'])
                    if obj:
                        x['setup'] = True
                        x['info'] = obj.get_version_info(None)
                except:
                    continue
                data[key] = x
        web_hook = public.init_msg("web_hook")
        if web_hook is False:
            return data
        default = {
            "name": None,
            "title": None,
            "version": "1.0",
            "date": "2023-10-30",
            "help": "https://www.bt.cn/bbs",
            "ps": "宝塔自定义API信息通道，用于接收面板消息推送",
            "setup": True,
            "info": web_hook.get_version_info(),
            "data": None
        }

        web_hook_conf = web_hook.get_config()
        for item in web_hook_conf:
            if item["status"]:
                tmp = default.copy()
                tmp["name"] = item["name"]
                tmp["title"] = "API:" + item["name"]
                tmp["data"] = item
                data[item["name"]] = tmp
        return data

    # 取消告警
    def clear_login_send(self, get):
        login_send_type_conf = "/www/server/panel/data/ssh_send_type.pl"
        os.remove(login_send_type_conf)
        self.stop_jian(get)
        return public.returnMsg(True, '取消登录告警成功！')

    # 设置告警
    def set_login_send(self, get):
        login_send_type_conf = "/www/server/panel/data/ssh_send_type.pl"
        set_type = get.type.strip()
        msg_configs = self.get_msg_push_list(get)
        if set_type not in msg_configs.keys():
            return public.returnMsg(False, '不支持该发送类型')

        from panelMessage import panelMessage
        pm = panelMessage()
        obj = pm.init_msg_module(set_type)
        if not obj:
            return public.returnMsg(False, "消息通道未安装。")

        public.writeFile(login_send_type_conf, set_type)
        self.start_jian(get)
        return public.returnMsg(True, '设置成功')



    # 查看告警
    def get_login_send(self,get):
        task_file_path = '/www/server/panel/data/mod_push_data/task.json'
        sender_file_path = '/www/server/panel/data/mod_push_data/sender.json'
        task_data = {}
        result = {'status': False}

        try:
            with open(task_file_path, 'r') as file:
                tasks = json.load(file)

            # 读取发送者配置文件
            with open(sender_file_path, 'r') as file:
                senders = json.load(file)
            sender_dict = {sender['id']: sender for sender in senders}

            # 查找特定的告警任务
            for task in tasks:
                if task.get('keyword') == "ssh_login":
                    task_data = task
                    sender_types = set()  # 使用集合来保证类型的唯一性
                    
                    # 对应sender的ID，获取sender_type，并保证唯一性
                    for sender_id in task.get('sender', []):
                        if sender_id in sender_dict:
                            sender_types.add(sender_dict[sender_id]['sender_type'])
                    
                    # 将唯一的通道类型列表转回列表格式，添加到告警数据中
                    task_data['channels'] = list(sender_types)
                    break

        except Exception as e:
            # print(f"处理文件或解析数据时发生错误: {e}")
            return result
        if task_data:
            return task_data
        else:
            return result


    def GetSshInfo(self):
        status = public.get_sshd_status()
        return status
        # pid_file = '/run/sshd.pid'
        # if os.path.exists(pid_file):
        #     pid = int(public.readFile(pid_file))
        #     status = public.pid_exists(pid)
        # else:
        #     import system
        #     panelsys = system.system()
        #     version = panelsys.GetSystemVersion()
        #     if os.path.exists('/usr/bin/apt-get'):
        #         if os.path.exists('/etc/init.d/sshd'):
        #             status = public.ExecShell("service sshd status | grep -P '(dead|stop)'|grep -v grep")
        #         else:
        #             status = public.ExecShell("service ssh status | grep -P '(dead|stop)'|grep -v grep")
        #     else:
        #         if version.find(' 7.') != -1 or version.find(' 8.') != -1 or version.find('Fedora') != -1:
        #             status = public.ExecShell("systemctl status sshd.service | grep 'dead'|grep -v grep")
        #         else:
        #             status = public.ExecShell("/etc/init.d/sshd status | grep -e 'stopped' -e '已停'|grep -v grep")
        #
        #     #       return status;
        #     if len(status[0]) > 3:
        #         status = False
        #     else:
        #         status = True
        # return status

    def stop_key(self, get):
        '''
        关闭key
        无需参数传递
        '''
        is_ssh_status = self.GetSshInfo()
        rec = '\n\s*#?\s*RSAAuthentication\s+\w+'
        rec2 = '\n\s*#?\s*PubkeyAuthentication\s+\w+'
        file = public.readFile(self.__SSH_CONFIG)
        if not file: return public.returnMsg(False, '错误：sshd_config配置文件不存在，无法继续!')
        file_ssh = re.sub(rec, '\nRSAAuthentication no', file)
        file_result = re.sub(rec2, '\nPubkeyAuthentication no', file_ssh)
        self.wirte(self.__SSH_CONFIG, file_result)

        if is_ssh_status:
            self.set_password(get)
            self.restart_ssh()
        public.WriteLog('SSH管理', '关闭SSH密钥登录')
        return public.returnMsg(True, '关闭成功')

    def get_config(self, get):
        '''
        获取配置文件
        无参数传递
        '''
        result = {}
        file = public.readFile(self.__SSH_CONFIG)
        if not file: return public.returnMsg(False, '错误：sshd_config配置文件不存在，无法继续!')

        # ========   以下在2022-10-12重构  ==========
        # author : hwliang
        # 是否开启RSA公钥认证
        # 默认开启(最新版openssh已经不支持RSA公钥认证)
        # yes = 开启
        # no = 关闭
        result['rsa_auth'] = 'yes'
        rec = r'^\s*RSAAuthentication\s*(yes|no)'
        rsa_find = re.findall(rec, file, re.M | re.I)
        if rsa_find and rsa_find[0].lower() == 'no': result['rsa_auth'] = 'no'

        # 获取是否开启公钥认证
        # 默认关闭
        # yes = 开启
        # no = 关闭
        result['pubkey'] = 'no'
        if self.get_key(get)['msg']:  # 先检查是否存在可用的公钥
            pubkey = r'^\s*PubkeyAuthentication\s*(yes|no)'
            pubkey_find = re.findall(pubkey, file, re.M | re.I)
            if pubkey_find and pubkey_find[0].lower() == 'yes': result['pubkey'] = 'yes'

        # 是否开启密码登录
        # 默认开启
        # yes = 开启
        # no = 关闭
        result['password'] = 'yes'
        ssh_password = r'^\s*PasswordAuthentication\s*([\w\-]+)'
        ssh_password_find = re.findall(ssh_password, file, re.M | re.I)
        if ssh_password_find and ssh_password_find[0].lower() == 'no': result['password'] = 'no'

        # 是否允许root登录
        # 默认允许
        # yes = 允许
        # no = 不允许
        # without-password = 允许，但不允许使用密码登录
        # forced-commands-only = 允许，但只允许执行命令，不能使用终端
        can_login, login_type = self.paser_root_login(file)
        result['root_is_login'] = can_login
        result['root_login_type'] = login_type
        result['root_login_types'] = self.__root_login_types
        result['key_type'] = public.ReadFile(self.__key_type_file)
        return result

    def set_root(self, get):
        '''
        开启密码登陆
        get: 无需传递参数
        '''
        p_type = 'yes'
        if 'p_type' in get:
            p_type = get.p_type.strip()
        if p_type not in self.__root_login_types.keys():
            return public.returnMsg(False, '错误：参数传递错误!')
        # ssh_password = r'^\s*#?\s*PermitRootLogin\s*([\w\-]+)'
        # file = public.readFile(self.__SSH_CONFIG)
        # src_line = re.search(ssh_password, file, re.M)
        # new_line = 'PermitRootLogin {}'.format(p_type)
        # if not src_line:
        #     file_result = file + '\n{}'.format(new_line)
        # else:
        #     file_result = file.replace(src_line.group(), new_line)
        # self.wirte(self.__SSH_CONFIG, file_result)
        file = public.readFile(self.__SSH_CONFIG)
        if not file:
            return public.returnMsg(False, '错误：sshd_config配置文件不存在，无法继续!')
        self._set_root_login(p_type, file)
        self.restart_ssh()
        msg = '设置root登录方式为: {}'.format(self.__root_login_types[p_type])
        public.WriteLog('SSH管理', msg)
        return public.returnMsg(True, msg)

    def stop_root(self, get):
        '''
        开启密码登陆
        get: 无需传递参数
        '''
        ssh_password = '\n\s*PermitRootLogin\s+\w+'
        file = public.readFile(self.__SSH_CONFIG)
        if len(re.findall(ssh_password, file)) == 0:
            file_result = file + '\nPermitRootLogin no'
        else:
            file_result = re.sub(ssh_password, '\nPermitRootLogin no', file)
        self.wirte(self.__SSH_CONFIG, file_result)
        self.restart_ssh()
        public.WriteLog('SSH管理', '设置root登录方式为:禁止')
        return public.returnMsg(True, '关闭成功')

    def stop_password(self, get):
        '''
        关闭密码访问
        无参数传递
        '''
        file = public.readFile(self.__SSH_CONFIG)
        ssh_password = '\n#?PasswordAuthentication\s\w+'
        file_result = re.sub(ssh_password, '\nPasswordAuthentication no', file)
        self.wirte(self.__SSH_CONFIG, file_result)
        public.ExecShell("sed -i 's/^PasswordAuthentication yes$/PasswordAuthentication no/' /etc/ssh/sshd_config.d/*.conf")
        self.restart_ssh()
        public.WriteLog('SSH管理', '关闭密码访问')
        return public.returnMsg(True, '关闭成功')

    def get_key(self, get):
        '''
        获取key 无参数传递
        '''
        key_type = self.get_ssh_key_type()
        if key_type in self.__type_files.keys():
            key_file = self.__type_files[key_type]
            key = public.readFile(key_file)
            return public.returnMsg(True, key)
        return public.returnMsg(True, '')

    def download_key(self, get):
        '''
            @name 下载密钥
        '''
        download_file = ''
        key_type = self.get_ssh_key_type()
        if key_type in self.__type_files.keys():
            if os.path.exists(self.__type_files[key_type]):
                download_file = self.__type_files[key_type]

        else:
            for file in self.__key_files:
                if not os.path.exists(file): continue
                download_file = file
                break

        if not download_file: return public.returnMsg(False, '错误：未找到密钥文件!')
        from flask import send_file
        filename = "{}_{}".format(public.GetHost(), os.path.basename(download_file))
        return send_file(download_file, download_name=filename)

    def wirte(self, file, ret):
        result = public.writeFile(file, ret)
        return result

    def restart_ssh(self):
        """
        重启ssh 无参数传递
        """
        public.set_sshd_status(status_act="restart")

    # 检查是否设置了钉钉
    def check_dingding(self, get):
        '''
        检查是否设置了钉钉
        '''
        # 检查文件是否存在
        if not os.path.exists('/www/server/panel/data/dingding.json'): return False
        dingding_config = public.ReadFile('/www/server/panel/data/dingding.json')
        if not dingding_config: return False
        # 解析json
        try:
            dingding = json.loads(dingding_config)
            if dingding['dingding_url']:
                return True
        except:
            return False

    # 开启SSH双因子认证
    def start_auth_method(self, get):
        '''
        开启SSH双因子认证
        '''
        # 检查是否设置了钉钉
        import ssh_authentication
        ssh_class = ssh_authentication.ssh_authentication()
        return ssh_class.start_ssh_authentication_two_factors()

    # 关闭SSH双因子认证
    def stop_auth_method(self, get):
        '''
        关闭SSH双因子认证
        '''
        # 检查是否设置了钉钉
        import ssh_authentication
        ssh_class = ssh_authentication.ssh_authentication()
        return ssh_class.close_ssh_authentication_two_factors()

    # 获取SSH双因子认证状态
    def get_auth_method(self, get):
        '''
        获取SSH双因子认证状态
        '''
        # 检查是否设置了钉钉
        import ssh_authentication
        ssh_class = ssh_authentication.ssh_authentication()
        return ssh_class.check_ssh_authentication_two_factors()

    # 判断so文件是否存在
    def check_so_file(self, get):
        '''
        判断so文件是否存在
        '''
        import ssh_authentication
        ssh_class = ssh_authentication.ssh_authentication()
        return ssh_class.is_check_so()

    # 下载so文件
    def get_so_file(self, get):
        '''
        下载so文件
        '''
        import ssh_authentication
        ssh_class = ssh_authentication.ssh_authentication()
        return ssh_class.download_so()

    # 获取pin
    def get_pin(self, get):
        '''
        获取pin
        '''
        import ssh_authentication
        ssh_class = ssh_authentication.ssh_authentication()
        return public.returnMsg(True, ssh_class.get_pin())

    def get_login_record(self, get):
        if os.path.exists(self.open_ssh_login):

            return public.returnMsg(True, '')
        else:
            return public.returnMsg(False, '')

    def start_login_record(self, get):
        if os.path.exists(self.open_ssh_login):
            return public.returnMsg(True, '')
        else:
            public.writeFile(self.open_ssh_login, "True")
            return public.returnMsg(True, '')

    def stop_login_record(self, get):
        if os.path.exists(self.open_ssh_login):
            os.remove(self.open_ssh_login)
            return public.returnMsg(True, '')
        else:
            return public.returnMsg(True, '')

    # 获取登录记录列表
    def get_record_list(self, get):
        if 'limit' in get:
            limit = int(get.limit.strip())
        else:
            limit = 12
        import page
        page = page.Page()
        count = public.M('ssh_login_record').order("id desc").count()
        info = {}
        info['count'] = count
        info['row'] = limit
        info['p'] = 1
        if hasattr(get, 'p'):
            info['p'] = int(get['p'])
        info['uri'] = get
        info['return_js'] = ''
        if hasattr(get, 'tojs'):
            info['return_js'] = get.tojs
        data = {}
        # 获取分页数据
        data['page'] = page.GetPage(info, '1,2,3,4,5,8')

        data['data'] = public.M('ssh_login_record').order('id desc').limit(
            str(page.SHIFT) + ',' + str(page.ROW)).select()

        return data

    def get_record_video(self, get):
        old_path = "/www/server/panel/plugin/jumpserver/static/video/"
        new_path = "/www/server/panel/data/jumpserver_video/"
        if not os.path.exists(new_path):
            os.makedirs(new_path)
        if os.path.isdir(old_path):
            for old_file in os.listdir(old_path):
                shutil.move(os.path.join(old_path, old_file), new_path)
            shutil.rmtree(old_path)

        record_id = get.get("record_id/d", 0)
        if not record_id:
            return public.returnMsg(False, '记录id错误不存在')
        video_info = public.M('ssh_login_record').where("id=?", (record_id,)).find()
        if not video_info or not isinstance(video_info, dict):
            return public.returnMsg(False, '记录不存在')
        if video_info["close_time"] == 0:
            return public.returnMsg(False, '记录未结束')
        video_path = video_info["video_addr"]
        if video_path.startswith(old_path):
            video_path = video_path.replace(old_path, new_path)
        if not os.path.exists(video_path):
            return public.returnMsg(False, '记录文件不存在')
        else:
            return send_file(video_path, download_name=os.path.basename(video_path))

    def remove_video_record(self, get):
        record_ids = get.get("record_ids/s")
        try:
            record_ids = json.loads(record_ids)
            record_ids = [str(int(i)) for i in record_ids if i]
        except:
            return public.returnMsg(False, '参数错误')

        old_path = "/www/server/panel/plugin/jumpserver/static/video/"
        new_path = "/www/server/panel/data/jumpserver_video/"

        videos_info = public.M('ssh_login_record').where("id in ({})".format(",".join(record_ids)), ()).select()
        if not videos_info or not isinstance(videos_info, list):
            return public.returnMsg(False, '记录不存在')
        for v in videos_info:
            if v["close_time"] == 0:
                record_ids.remove(str(v["id"]))
                continue
            v_file = v["video_addr"]
            if v_file.startswith(old_path):
                v_file = v_file.replace(old_path, new_path)
            try:
                if os.path.exists(v_file):
                    os.remove(v_file)
            except:
                pass

        public.M('ssh_login_record').where("id in ({})".format(",".join(record_ids)), ()).delete()
        return public.returnMsg(True, '删除成功')


    def get_file_json(self, get):

        if os.path.exists(get.path):
            ret = json.loads(public.ReadFile(get.path))
            return ret
        else:
            return ''

    def get_sys_user(self, get):
        """获取所有用户名
        @param:
        @return
        """
        # p = int(get.p) if hasattr(get, 'p') else 1
        # row = int(get.row) if hasattr(get, 'row') else 10
        from collections import deque
        user_set = deque()
        with open('/etc/passwd') as fp:
            for line in fp.readlines():
                # i = line.strip().split(":")
                # if i[2] == '0' and i[3] == '0':
                #     user_set.append(line.split(':', 1)[0]+"*")
                # else:
                user_set.append(line.split(':', 1)[0])

        # user_set = []
        # for line in fp.readlines():
        #     line = line.strip()
        #     if line.endswith(':0:0'):
        #         user_set.append(line.split(':', 1)[0] + '*')
        #     else:
        #         user_set.append(line.split(':', 1)[0])

        # count = len(user_set)
        # data = public.get_page(count, p, row)
        # return data
        # return public.returnMsg(True, list(user_set))
        # public.print_log(public.ExecShell("cat /etc/passwd | grep '^0' "))
        return public.returnMsg(True, list(user_set))

    def add_sys_user(self, get):
        """添加系统用户
        @param get:
        @return:
        """
        password = get.password
        if not get.username:
            return public.returnMsg(False, '用户名不能为空')
        if not get.password:
            return public.returnMsg(False, '密码不能为空')
        if get.username in self.get_sys_user(get)['msg']:
            return public.returnMsg(False, '用户名已存在')

        if len(password) < 8: return public.returnMsg(False, "密码长度不能小于8位")

        has_letter = bool(re.search(r'[a-zA-Z!@#$%^&*()-_+=]', password))
        has_digit_or_symbol = bool(re.search(r'[0-9!@#$%^&*()-_+=]', password))
        if not has_letter or not has_digit_or_symbol: return public.returnMsg(False, "密码必须包含字母和数字或符号")

        # 检查用户名是否合法
        if not re.match(r'^[a-z_][a-z0-9_-]{0,31}$', get.username):
            return public.returnMsg(False,
                                    "用户名不合法，必须以小写字母或下划线开头，并且只能包含小写字母、数字、下划线和连字符，且长度在1到32字符之间")

        public.ExecShell('useradd -m -s /bin/bash ' + get.username)
        public.ExecShell('echo ' + get.username + ':' + get.password + ' | chpasswd')
        return public.returnMsg(True, '添加成功')

    def del_sys_user(self, get):
        """删除系统用户
        @param get:
        @return:
        """
        try:
            if not get.username:
                return public.returnMsg(False, '用户名不能为空')
            if get.username not in self.get_sys_user(get)['msg']:
                return public.returnMsg(False, '用户不存在')

            public.ExecShell('userdel -rf ' + get.username)

        # if len(data[1]) > 0:
        #     match = re.search(r'process (\d+)', data[1])
        #
        #     public.ExecShell('kill -9  ' + match.group(1))
        #     public.ExecShell('userdel -r ' + get.username)

            return public.returnMsg(True, '删除成功')

        except Exception as e:
            return
            # return public.returnMsg(False, '删除失败')

    @staticmethod
    def is_redhat():
        if os.path.exists("/usr/bin/yum") and os.path.exists("/usr/bin/rpm"):
            return True
        return False

    @staticmethod
    def _get_other_conf_list():
        sshd_conf = []
        if os.path.isdir("/etc/ssh/sshd_config.d"):
            for i in os.listdir("/etc/ssh/sshd_config.d"):
                file_path = "/etc/ssh/sshd_config.d/{}".format(i)
                # 以".conf"结尾且为文件
                if i.endswith(".conf") and os.path.isfile(file_path):
                    tmp_data = public.readFile(file_path)
                    if isinstance(tmp_data, str):
                        sshd_conf.append({
                            "data": tmp_data,
                            "path": file_path,
                            "name": i,
                        })
        # 按照字母循序加载的
        sshd_conf.sort(key=lambda x: x["name"])
        return sshd_conf

    def paser_root_login(self, conf_data: str = None):
        can_login = 'no'
        login_type = 'without-password'
        if self.is_redhat():
            can_login = 'yes'
            login_type = 'yes'

        if conf_data is None:
            conf_data = public.readFile(self.__SSH_CONFIG)

        if not isinstance(conf_data, str):
            return can_login, login_type

        other_conf = self._get_other_conf_list()
        sshd_conf = [i["data"] for i in other_conf]
        sshd_conf.insert(0, conf_data)
        test_re = re.compile(r"^\s*PermitRootLogin\s*(?P<target>[\w\-]+)", re.M)
        is_break = False
        for cf in sshd_conf:
            for tmp_res in test_re.finditer(cf):
                login_type = tmp_res.group("target")
                is_break = True
                break

            if is_break: break

        if login_type in ('yes', 'without-password'):
            can_login = 'yes'

        return can_login, login_type

    def _set_root_login(self, p_type, conf_data: str = None):
        if conf_data is None:
            conf_data = public.readFile(self.__SSH_CONFIG)
        if not isinstance(conf_data, str):
            return False, "配置文件不存在"

        sshd_conf = self._get_other_conf_list()
        sshd_conf.insert(0, {"data": conf_data, "path": self.__SSH_CONFIG, "name": ""})
        last_load_file = None
        last_load_data = None
        start_index = None
        end_index = None
        test_re = re.compile(r"^\s*PermitRootLogin\s*(?P<target>[\w\-]+)", re.M)
        is_break = False
        for cf in sshd_conf:
            for tmp_res in test_re.finditer(cf["data"]):
                last_load_file = cf["path"]
                last_load_data = cf["data"]
                start_index = tmp_res.start()
                end_index = tmp_res.end()
                is_break = True
                break

            if is_break: break

        if last_load_file is None or last_load_data is None:
            conf_data = conf_data + '\nPermitRootLogin {}'.format(p_type)
            public.writeFile(self.__SSH_CONFIG, conf_data)
            return True, ""

        new_conf = last_load_data[:start_index] + 'PermitRootLogin {}'.format(p_type) + last_load_data[end_index:]
        public.writeFile(last_load_file, new_conf)
        return True, ""


# # 指定账号登录发送告警
# def set_user_send(self,get):
#     """设置用户发送"""
#     usernames = get["name"].split(',')
#     user_send_path = os.path.join(public.get_panel_path(), "data/user_send.json")
#     if not usernames:
#         return public.returnMsg(False, '用户名不能为空')
#
#     if not os.path.exists(user_send_path):
#         public.writeFile(user_send_path, '[]')
#
#     data = json.loads(public.readFile(user_send_path))
#
#     for temp in usernames:
#         if temp not in data:
#             data.append(temp)
#
#     public.writeFile(user_send_path, json.dumps(data))
#
#     return public.returnMsg(True, '设置成功')
#
# # 获取需要告警的账号列表
# def get_user_send(self,get):
#     """获取需要告警的账号列表"""
#     user_send_path = os.path.join(public.get_panel_path(), "data/user_send.json")
#
#     if not os.path.exists(user_send_path):
#         return []
#
#     data = json.loads(public.readFile(user_send_path))
#
#     return data


if __name__ == '__main__':
    import sys

    type = sys.argv[1]
    if type == 'login':
        try:
            aa = ssh_security()
            aa.login()
        except:
            pass
    else:
        pass
