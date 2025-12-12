# coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c)  2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: hwliang  <hwl@bt.cn>
# +-------------------------------------------------------------------
import json
import pty
import shutil
import struct
import subprocess
import time
import os
import sys
import socket
import threading
import re
import ipaddress
import traceback
from itertools import chain

import fcntl
import select
import termios

if not 'class/' in sys.path:
    sys.path.insert(0, 'class/')
from io import BytesIO, StringIO


def returnMsg(status, msg):
    return {'status': status, 'msg': msg}


import public

try:
    import chardet
except:
    os.system('btpip install chardet')
    import chardet


class ssh_terminal:
    _panel_path = '/www/server/panel'
    _save_path = _panel_path + '/config/ssh_info/'
    _host = None
    _port = 22
    _user = None
    _pass = None
    _pkey = None
    _ws = None
    _ssh = None
    _last_cmd = ""
    _last_cmd_tip = 0
    _log_type = '宝塔终端'
    _history_len = 0
    _client = ""
    _rep_ssh_config = False
    _sshd_config_backup = None
    _rep_ssh_service = False
    _tp = None
    _old_conf = None
    _debug_file = 'logs/terminal.log'
    _s_code = None
    _last_num = 0
    _key_passwd = None
    _host_row_id = ""

    def __init__(self):
        # 创建jp_login_record表记录ssh登录记录
        import db
        sql = db.Sql().dbfile('/www/server/panel/data/db/default.db')
        if not sql.table('sqlite_master').where('type=? AND name=?', ('table', 'ssh_login_record')).count():
            sql.execute('''CREATE TABLE ssh_login_record (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                addr TEXT,
                server_ip TEXT,
                user_agent TEXT,
                ssh_user TEXT,
                login_time INTEGER DEFAULT 0,
                close_time INTEGER DEFAULT 0,
                video_addr TEXT);''')
            sql.execute('CREATE INDEX ssh_login_record ON ssh_login_record (addr);')
        self.time = time.time()
        self._video_addr = ""
        self._connect_ua = ""

    def record(self, rtype, data):
        if os.path.exists(public.get_panel_path() + "/data/open_ssh_login.pl") and self._video_addr:
            path = self._video_addr
            if rtype == 'header':
                with open(path, 'w') as fw:
                    fw.write(json.dumps(data) + '\n')
                    return True
            else:
                if not os.path.exists(path):
                    self._host_row_id = public.M('ssh_login_record').add(
                        'addr,server_ip,ssh_user,user_agent,login_time,video_addr',
                        (self._client, self._host, self._user, self._connect_ua
                         , int(self._connect_time),
                         self._video_addr))

                    self.time = time.time()
                    with open(path, 'w') as fw:
                        fw.write(json.dumps({
                            "version": 1,
                            "width": 100,
                            "height": 29,
                            "timestamp": int(self.time) -1,
                            "env": {
                                "TERM": "xterm",
                                "SHELL": "/bin/bash",
                            },
                            "stdout": []
                        }) + '\n')
                with open(path, 'r') as fr:
                    content = json.loads(fr.read())
                    stdout = content["stdout"]
                atime = time.time()
                iodata = [atime - self.time, data]
                stdout.append(iodata)
                content["stdout"] = stdout
                with open(path, 'w') as fw:
                    fw.write(json.dumps(content) + '\n')
                    self.time = atime
                    return True
        return False

    @staticmethod
    def _is_ipv6(ip_str: str) -> bool:
        try:
            ipaddress.IPv6Address(ip_str)
            return True
        except:
            return False

    def connect(self):
        '''
            @name 连接服务器
            @author hwliang<2020-08-07>
            @return dict{
                status: bool 状态
                msg: string 详情
            }
        '''
        if not self._host: return returnMsg(False, '错误的连接地址')

        if not self._user: self._user = 'root'
        if not self._port: self._port = 22
        self.is_local()

        if self._host in ['127.0.0.1', 'localhost']:
            self._port = public.get_sshd_port()
        # self.set_sshd_config(True)

        sock = None
        for num in range(5):
            try:
                self.debug('正在尝试第{}次连接'.format(num))
                if self._rep_ssh_config: time.sleep(0.1)
                if self._is_ipv6(self._host):
                    family = socket.AF_INET6
                else:
                    family = socket.AF_INET
                sock = socket.socket(family, socket.SOCK_STREAM)
                sock.settimeout(2 + num)
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 8192)
                sock.connect((self._host, self._port))
                break
            except Exception as e:
                self.debug('重试连接失败,{}'.format(e))
                sock = None
                time.sleep(0.2)

        if self._is_ipv6(self._host):
            self._host = '[{}]'.format(self._host)

        if not sock:
            self.set_sshd_config(True)
            if self._host in ['127.0.0.1', 'localhost']:
                return returnMsg(False, '连接目标服务器失败: {}'.format(
                    "Authentication failed ," + self._user + "@" + self._host + ":" + str(self._port)))
            return returnMsg(False, '连接目标服务器失败, {}:{}'.format(self._host, self._port))

        try:
            try:
                import paramiko
            except:
                public.ExecShell('btpip uninstall paramiko')
                public.ExecShell('btpip uninstall cryptography')
                public.ExecShell('btpip install paramiko==2.7.2')
                public.ExecShell('btpip install cryptography==42.0.5')
                import paramiko
        except:
            return returnMsg(False, 'paramiko模块不存在且安装失败，请联系宝塔官方人员!')

        self._tp = paramiko.Transport(sock)
        print(self._tp.banner_timeout)

        pkey = None
        try:
            self._tp.start_client()
            if not self._pass and not self._pkey:
                self.set_sshd_config(True)
                return public.returnMsg(False, '密码或私钥不能都为空: {}:{}'.format(self._host, self._port))
            self._tp.banner_timeout = 60
            print(self._tp.banner_timeout)
            if self._pkey:
                self.debug('正在认证私钥')
                if sys.version_info[0] == 2:
                    try:
                        self._pkey = self._pkey.encode('utf-8')
                    except:
                        pass
                    p_file = BytesIO(self._pkey)
                else:
                    p_file = StringIO(self._pkey)

                pkey = None
                key_cls_list = [paramiko.RSAKey, paramiko.Ed25519Key, paramiko.ECDSAKey]
                if hasattr(paramiko, 'DSSKey'):  # DSSKey 在最新的 paramiko 版本中被弃用, 也不够安全
                    key_cls_list.append(paramiko.DSSKey)
                for key_cls in [paramiko.RSAKey, paramiko.Ed25519Key, paramiko.ECDSAKey]:
                    p_file.seek(0)
                    try:
                        pkey = key_cls.from_private_key(p_file, password=(self._key_passwd if self._key_passwd else None))
                    except Exception as e:
                        if "base64 decoding error" in str(e):
                            return returnMsg(False, "私钥数据错误，请检查是完整复制的私钥信息")
                        elif "Private key file is encrypted" in str(e):
                            return returnMsg(False, "私钥已加密，但未提供私钥的密码，无法验证私钥信息")
                        elif "Invalid key" in str(e):
                            return returnMsg(False,"私钥解析错误，请检查私钥的密码是否正确")
                        continue
                    else:
                        break
                else:
                    return returnMsg(False,"私钥格式错误, 请确认输入的秘钥格式正确")

                if not pkey: return public.returnMsg(False, '私钥错误!')
                self._tp.auth_publickey(username=self._user, key=pkey)
            else:
                try:
                    self._tp.auth_none(self._user)
                except Exception as e:
                    e = str(e)
                    if e.find('keyboard-interactive') >= 0:
                        self._auth_interactive()
                    else:
                        self.debug('正在认证密码')
                        self._tp.auth_password(username=self._user, password=self._pass)
                # self._tp.auth_password(username=self._user, password=self._pass)
        except Exception as e:
            if self._old_conf:
                s_file = '/www/server/panel/config/t_info.json'
                if os.path.exists(s_file): os.remove(s_file)
            self.set_sshd_config(True)
            self._tp.close()
            e = str(e)
            if e.find('websocket error!') != -1:
                return returnMsg(True, '连接成功')
            if e.find('Authentication timeout') != -1:
                self.debug("认证超时{}".format(e))
                return returnMsg(False, '认证超时,请按回车重试!{}'.format(e))
            if e.find('Authentication failed') != -1:
                self.debug('认证失败{}'.format(e))
                if self._key_passwd:
                    sshd_config = public.readFile('/etc/ssh/sshd_config')
                    if sshd_config and sshd_config.find('ssh-dss') == -1:
                        return returnMsg(False,
                                         '私钥验证失败，可能私钥不正确，也可能/etc/ssh/sshd_config配置文件中未开启ssh-dss私钥认证类型')
                    return returnMsg(False, '认证失败，请检查私钥是否正确: {}'.format(
                        e + "," + self._user + "@" + self._host + ":" + str(self._port)))
                return returnMsg(False, '帐号或密码错误: {}'.format(
                    e + "," + self._user + "@" + self._host + ":" + str(self._port)))
            if e.find('Bad authentication type; allowed types') != -1:
                self.debug('认证失败{}'.format(e))
                if self._host in ['127.0.0.1', 'localhost'] and self._pass == 'none':
                    return returnMsg(False, '帐号或密码错误: {}'.format(
                        "Authentication failed ," + self._user + "@" + self._host + ":" + str(self._port)))
                return returnMsg(False, '不支持的身份验证类型: {}'.format(e))
            if e.find('Connection reset by peer') != -1:
                self.debug('目标服务器主动拒绝连接')
                return returnMsg(False, '目标服务器主动拒绝连接')
            if e.find('Error reading SSH protocol banner') != -1:
                self.debug('协议头响应超时')
                return returnMsg(False, '协议头响应超时，与目标服务器之间的网络质量太糟糕：' + e)
            if not e:
                self.debug('SSH协议握手超时')
                return returnMsg(False, "SSH协议握手超时，与目标服务器之间的网络质量太糟糕")
            err = public.get_error_info()
            self.debug(err)
            return returnMsg(False, "未知错误: {}".format(err))

        self.debug('认证成功，正在构建会话通道')
        self._ssh = self._tp.open_session()
        self._ssh.get_pty(term='xterm', width=100, height=34)
        self._ssh.invoke_shell()
        self._connect_time = time.time()
        self._last_send = []
        from BTPanel import request
        self._client = public.GetClientIp() + ':' + str(public.get_remote_port())
        public.WriteLog(self._log_type, '成功登录到SSH服务器 [{}:{}]'.format(self._host, self._port))
        self.history_send("登录成功\n")
        self.set_sshd_config(True)
        self.debug('通道已构建')
        from BTPanel import session
        self._video_addr = "/www/server/panel/data/jumpserver_video/%s.json" % str(int(self._connect_time))
        if not os.path.exists("/www/server/panel/data/jumpserver_video/"):
            os.makedirs("/www/server/panel/data/jumpserver_video/")
        # 如果开启了录像功能
        self._connect_ua = str(request.headers.get('User-Agent'))
        if os.path.exists(public.get_panel_path() + "/data/open_ssh_login.pl"):
            self._host_row_id = public.M('ssh_login_record').add(
                'addr,server_ip,ssh_user,user_agent,login_time,video_addr',
                (self._client, self._host, self._user, self._connect_ua
                 , int(self._connect_time),
                 self._video_addr))

            self.record('header', {
                "version": 1,
                "width": 100,
                "height": 29,
                "timestamp": int(self._connect_time),
                "env": {
                    "TERM": "xterm",
                    "SHELL": "/bin/bash",
                },
                "stdout": []
            })

        return returnMsg(True, '连接成功')

    def _auth_interactive(self):
        self.debug('正在二次认证 Verification Code')

        self.brk = False

        def handler(title, instructions, prompt_list):
            if not self._ws:  raise public.PanelError('websocket error!')
            if instructions:
                self._ws.send(instructions)
            if title:
                self._ws.send(title)
            resp = []
            for pr in prompt_list:
                if str(pr[0]).strip() == "Password:":
                    resp.append(self._pass)
                elif str(pr[0]).strip() == "Verification code:":
                    # 获取前段传入的验证码
                    self._ws.send("Verification code# ")
                    self._s_code = True
                    code = ""
                    while True:
                        data = self._ws.receive()
                        if data.find('"resize":1') != -1:
                            self.resize(data)
                            continue
                        self._ws.send(data)
                        if data in ["\n", "\r"]: break
                        code += data
                    resp.append(code)
                    self._ws.send("\n")
            self._s_code = None
            return tuple(resp)

        self._tp.auth_interactive(self._user, handler)

    def get_login_user(self):
        '''
            @name 获取本地登录用户
            @author hwliang<2020-08-07>
            @return string
        '''

        if self._user != 'root':
            return self._user
        l_user = 'root'
        ssh_config_file = '/etc/ssh/sshd_config'
        ssh_config = public.readFile(ssh_config_file)
        if not ssh_config:
            return l_user

        if public.get_os_version().lower().find('centos') >= 0:
            return l_user

        # 检查是不是 【允许root登录】 或 【允许root用秘钥登录】
        from ssh_security import ssh_security
        can_login, _ = ssh_security().paser_root_login()
        # rep = re.compile(r"\n[ \t]*PermitRootLogin +((yes)|(without-password))")
        if can_login == "yes":
            return l_user

        user_list = self.get_ulist()
        can_login = []
        root_group_user = []

        # 过滤出能登陆的root组用户 和 能登陆的普通用户
        for u_info in user_list:
            if u_info['user'] == 'root':
                continue
            if u_info['login'] in ('/bin/bash', '/bin/sh', '/bin/dash'):
                if u_info['gid'] == "0":
                    root_group_user.append(u_info)
                    continue
                can_login.append(u_info)

        # 找出能登陆的root组用户的可用的
        for u_info in chain(root_group_user, can_login):  # 通过chain链接并优先使用root组的用户
            if os.path.exists(u_info["home"]):  # 有家目录的优先
                return u_info["user"]

        # 如果没有则使用 root_group_user 的第1个
        if len(root_group_user) >= 1:
            return root_group_user[0]["user"]

        # 如果没有则使用 can_login 的第1个
        if len(can_login) >= 1:
            return root_group_user[0]["user"]

        return l_user

    @staticmethod
    def _get_user_info_by_name(user_name: str):
        u_data = public.readFile('/etc/passwd')
        for i in u_data.split("\n"):
            u_tmp = i.split(':')
            if len(u_tmp) < 3:
                continue
            if u_tmp[0] == user_name:
                return {
                    'user': u_tmp[0],
                    'pass': u_tmp[1],
                    'uid': u_tmp[2],
                    'gid': u_tmp[3],
                    'user_msg': u_tmp[4],
                    'home': u_tmp[5],
                    'login': u_tmp[6]
                }
        return None

    def get_ulist(self):
        '''
            @name 获取本地用户列表
            @author hwliang<2020-08-07>
            @return list
        '''
        u_data = public.readFile('/etc/passwd')
        u_list = []
        for i in u_data.split("\n"):
            u_tmp = i.split(':')
            if len(u_tmp) < 3: continue
            u_info = {
                'user': u_tmp[0],
                'pass': u_tmp[1],
                'uid': u_tmp[2],
                'gid': u_tmp[3],
                'user_msg': u_tmp[4],
                'home': u_tmp[5],
                'login': u_tmp[6]
            }
            u_list.append(u_info)
        return u_list

    def is_local(self):
        '''
            @name 处理本地连接
            @author hwliang<2020-08-07>
            @ps 如果host为127.0.0.1或localhost，则尝试自动使用publicKey登录
            @return void
        '''

        if self._pass: return
        if self._pkey: return
        if self._host in ['127.0.0.1', 'localhost']:
            try:
                self._port = public.get_sshd_port()
                self.set_sshd_config()
                s_file = '/www/server/panel/config/t_info.json'
                if os.path.exists(s_file):
                    ssh_info = json.loads(public.en_hexb(public.readFile(s_file)))
                    self._host = ssh_info['host'].strip()
                    if 'username' in ssh_info:
                        self._user = ssh_info['username']
                    if 'pkey' in ssh_info:
                        self._pkey = ssh_info['pkey']
                    if 'password' in ssh_info:
                        self._pass = ssh_info['password']
                    self._old_conf = True
                    return
                ssh_key_type_file = '{}/data/ssh_key_type.pl'.format(public.get_panel_path())
                ssh_key_type = ''
                if os.path.exists(ssh_key_type_file):
                    ssh_key_type_new = public.readFile(ssh_key_type_file)
                    if ssh_key_type_new: ssh_key_type = ssh_key_type_new.strip()
                login_user = self.get_login_user()
                if self._user == 'root' and login_user == 'root':
                    id_rsa_file = ['/root/.ssh/id_ed25519', '/root/.ssh/id_ecdsa', '/root/.ssh/id_rsa',
                                   '/root/.ssh/id_rsa_bt']
                    if ssh_key_type:
                        id_rsa_file.insert(0, '/root/.ssh/id_{}'.format(ssh_key_type))
                    for ifile in id_rsa_file:
                        if os.path.exists(ifile):
                            self._pkey = public.readFile(ifile)
                            host_path = self._save_path + self._host
                            if not os.path.exists(host_path):
                                os.makedirs(host_path, 384)
                            return
                    # 没有找到key文件时，自动创建
                    self.create_ssh_key("ed25519")
                    ssh_key_type = "ed25519"

                    for ifile in id_rsa_file:
                        if os.path.exists(ifile):
                            self._pkey = public.readFile(ifile)
                            host_path = self._save_path + self._host
                            if not os.path.exists(host_path):
                                os.makedirs(host_path, 384)
                            return
                # 登录用户是root, 但root用户不能登录其他用户可以登录时，结合这次登录请求不包含 密码或者秘钥，则必然是初次请求终端
                # 则尝试以 login_user 登录，且自动创建所需秘钥
                if (self._user == 'root' and login_user != "root") and not (self._pass or self._pkey):
                    self._user = login_user
                    login_user_info = self._get_user_info_by_name(login_user)
                    id_rsa_file = ['.ssh/id_ed25519', '.ssh/id_ecdsa', '.ssh/id_rsa', '.ssh/id_rsa_bt']
                    for ifile in id_rsa_file:
                        k_file = "{}/{}".format(login_user_info["home"], ifile)
                        if os.path.exists(k_file):
                            self._pkey = public.readFile(k_file)
                            host_path = self._save_path + self._host
                            if not os.path.exists(host_path):
                                os.makedirs(host_path, 384)
                            return

                    # 没有找到key文件时，自动创建
                    self.create_ssh_key_for_other_user(login_user, login_user_info["home"], "ed25519")
                    k_file = "{}/{}".format(login_user_info["home"], '.ssh/id_ed25519')
                    if os.path.exists(k_file):
                        self._pkey = public.readFile(k_file)
                        host_path = self._save_path + self._host
                        if not os.path.exists(host_path):
                            os.makedirs(host_path, 384)
                        return

                if not self._pass or not self._pkey or not self._user:
                    home_path = '/home/' + login_user
                    if login_user == 'root':
                        home_path = '/root'
                    self._user = login_user
                    id_rsa_file = [home_path + '/.ssh/id_ed25519', home_path + '/.ssh/id_ecdsa',
                                   home_path + '/.ssh/id_rsa', home_path + '/.ssh/id_rsa_bt']
                    if ssh_key_type:
                        id_rsa_file.insert(0, home_path + '/.ssh/id_{}'.format(ssh_key_type))
                    for ifile in id_rsa_file:
                        if os.path.exists(ifile):
                            self._pkey = public.readFile(ifile)
                            return

                    self._pass = 'none'
                    return

            except:
                return

    def get_sys_version(self):
        '''
            @name 获取操作系统版本
            @author hwliang<2020-08-13>
            @return bool
        '''
        version = public.readFile('/etc/redhat-release')
        if not version:
            version = public.readFile('/etc/issue').strip().split("\n")[0].replace('\\n', '').replace('\\l', '').strip()
        else:
            version = version.replace('release ', '').replace('Linux', '').replace('(Core)', '').strip()
        return version

    def get_ssh_status(self):
        """
            @name 获取SSH服务状态
            @author hwliang<2020-08-13>
            @return bool
        """
        status = public.get_sshd_status()
        return status
        # version = self.get_sys_version()
        # if os.path.exists('/usr/bin/apt-get'):
        #     if os.path.exists('/etc/init.d/sshd'):
        #         status = public.ExecShell("service sshd status | grep -P '(dead|stop|not running)'|grep -v grep")
        #     else:
        #         status = public.ExecShell("service ssh status | grep -P '(dead|stop|not running)'|grep -v grep")
        # else:
        #     if version.find(' 7.') != -1 or version.find(' 8.') != -1 or version.find('Fedora') != -1:
        #         status = public.ExecShell("systemctl status sshd.service | grep 'dead'|grep -v grep")
        #     else:
        #         status = public.ExecShell("/etc/init.d/sshd status | grep -e 'stopped' -e '已停'|grep -v grep")
        # if len(status[0]) > 3:
        #     status = False
        # else:
        #     status = True
        # return status

    def is_running(self, rep=False):
        '''
            @name 处理SSH服务状态
            @author hwliang<2020-08-13>
            @param rep<bool> 是否恢复原来的SSH服务状态
            @return bool
        '''
        try:
            if rep and self._rep_ssh_service:
                self.restart_ssh('stop')
                return True

            ssh_status = self.get_ssh_status()
            if not ssh_status:
                self.restart_ssh('start')
                self._rep_ssh_service = True
                return True
            return False
        except:
            return False

    def set_sshd_config(self, rep=False):
        '''
            @name 设置本地SSH配置文件，以支持pubkey认证
            @author hwliang<2020-08-13>
            @param rep<bool> 是否恢复ssh配置文件
            @return bool
        '''
        self.is_running(rep)
        if rep and not self._rep_ssh_config:
            return False

        try:
            sshd_config_file = '/etc/ssh/sshd_config'
            if not os.path.exists(sshd_config_file):
                return False

            sshd_config = public.readFile(sshd_config_file)

            if not sshd_config:
                return False

            if rep:
                if self._sshd_config_backup:
                    public.writeFile(sshd_config_file, self._sshd_config_backup)
                    self.restart_ssh()
                return True

            pin = r'^\s*PubkeyAuthentication\s+(yes|no)'
            pubkey_status = re.findall(pin, sshd_config, re.I)
            if pubkey_status:
                if pubkey_status[0] == 'yes':
                    pubkey_status = True
                else:
                    pubkey_status = False

            pin = r'^\s*RSAAuthentication\s+(yes|no)'
            rsa_status = re.findall(pin, sshd_config, re.I)
            if rsa_status:
                if rsa_status[0] == 'yes':
                    rsa_status = True
                else:
                    rsa_status = False

            self._sshd_config_backup = sshd_config
            is_write = False
            if not pubkey_status:
                sshd_config = re.sub(r'\n#?PubkeyAuthentication\s\w+', '\nPubkeyAuthentication yes', sshd_config)
                is_write = True
            if not rsa_status:
                sshd_config = re.sub(r'\n#?RSAAuthentication\s\w+', '\nRSAAuthentication yes', sshd_config)
                is_write = True

            if is_write:
                public.writeFile(sshd_config_file, sshd_config)
                self._rep_ssh_config = True
                self.restart_ssh()
            else:
                self._sshd_config_backup = None

            return True
        except:
            return False

    def restart_ssh(self, act='reload'):
        """
        重启ssh 无参数传递
        """
        return public.set_sshd_status(act)


    def resize(self, data):
        '''
            @name 调整终端大小
            @author hwliang<2020-08-07>
            @param data<dict> 终端尺寸数据
            {
                cols: int 列
                rows: int 行
            }
            @return bool
        '''
        try:
            data = json.loads(data)
            self._ssh.resize_pty(width=data['cols'], height=data['rows'])
            return True
        except:
            return False

    def recv(self):
        '''
            @name 读取tty缓冲区数据
            @author hwliang<2020-08-07>
            @return void
        '''
        n = 0
        try:
            while self._ws.connected:
                resp_line = self._ssh.recv(1024)
                if not resp_line:
                    if not self._tp.is_active():
                        self.debug('通道已断开')
                        self._ws.send('连接已断开,按回车将尝试重新连接!')
                        self.close()
                        return

                if not resp_line:
                    n += 1
                    if n > 5: break
                    continue
                n = 0
                if not self._ws.connected:
                    return
                try:
                    result = resp_line.decode('utf-8', 'ignore')
                except:
                    try:
                        result = resp_line.decode()
                    except:
                        result = str(resp_line)
                self.record('iodata', result)
                self._ws.send(result)

                # self.history_recv(result)
        except Exception as e:
            e = str(e)
            if e.find('closed') != -1:
                self.debug('会话已中断')
            elif self._ws.connected:
                self.debug('读取tty缓冲区数据发生错误,{}'.format(e))

        if not self._ws.connected:
            self.debug('客户端已主动断开连接')
        self.close()

    def send(self):
        '''
            @name 写入数据到缓冲区
            @author hwliang<2020-08-07>
            @return void
        '''
        try:
            while self._ws.connected:
                if self._s_code:
                    time.sleep(0.1)
                    continue
                client_data = self._ws.receive()
                if not client_data: continue
                if client_data == '{}': continue
                if len(client_data) > 10:
                    if client_data.find('{"host":"') != -1:
                        continue
                    if client_data.find('"resize":1') != -1:
                        self.resize(client_data)
                        continue
                self._ssh.send(client_data)
                # self.history_send(client_data)
        except Exception as ex:
            ex = str(ex)

            if ex.find('_io.BufferedReader') != -1:
                self.debug('从websocket读取数据发生错误，正在重新试')
                self.send()
                return
            elif ex.find('closed') != -1:
                self.debug('会话已中断')
            else:
                self.debug('写入数据到缓冲区发生错误: {}'.format(ex))

        if not self._ws.connected:
            self.debug('客户端已主动断开连接')
        self.close()

    def history_recv(self, recv_data):
        '''
            @name 从接收实体保存命令
            @author hwliang<2020-08-12>
            @param recv_data<string> 数据实体
            @return void
        '''
        # 处理TAB补登
        if self._last_cmd_tip == 1:
            if not recv_data.startswith('\r\n'):
                self._last_cmd += recv_data.replace('\u0007', '').replace("\x07", "").strip()
            self._last_cmd_tip = 0

        # 上下切换命令
        if self._last_cmd_tip == 2:
            self._last_cmd = recv_data.strip().replace("\x08", "").replace("\x07", "").replace("\x1b[K", "")
            self._last_cmd_tip = 0

    def history_send(self, send_data):
        '''
            @name 从发送实体保存命令
            @author hwliang<2020-08-12>
            @param send_data<string> 数据实体
            @return void
        '''
        if not send_data: return
        his_path = self._save_path + self._host
        if not os.path.exists(his_path): return
        his_file = his_path + '/history.pl'

        # 上下切换命令
        if send_data in ["\x1b[A", "\x1b[B"]:
            self._last_cmd_tip = 2
            return

        # 左移光标
        if send_data in ["\x1b[C"]:
            self._last_num -= 1
            return

        # 右移光标
        if send_data in ["\x1b[D"]:
            self._last_num += 1
            return

        # 退格
        if send_data == "\x7f":
            self._last_cmd = self._last_cmd[:-1]
            return

        # 过滤特殊符号
        if send_data in ["\x1b[C", "\x1b[D", "\x1b[K", "\x07", "\x08", "\x03", "\x01", "\x02", "\x04", "\x05", "\x06",
                         "\x1bOB", "\x1bOA", "\x1b[8P", "\x1b", "\x1b[4P", "\x1b[6P", "\x1b[5P"]:
            return

        # Tab补全处理
        if send_data == "\t":
            self._last_cmd_tip = 1
            return

        if str(send_data).find("\x1b") != -1:
            return

        if send_data[-1] in ['\r', '\n']:
            if not self._last_cmd: return
            his_shell = [int(time.time()), self._client, self._user, self._last_cmd]
            public.writeFile(his_file, json.dumps(his_shell) + "\n", "a+")
            self._last_cmd = ""

            # 超过50M则保留最新的20000行
            if os.stat(his_file).st_size > 52428800:
                his_tmp = public.GetNumLines(his_file, 20000)
                public.writeFile(his_file, his_tmp)
        else:
            if self._last_num >= 0:
                self._last_cmd += send_data

    def close(self):
        '''
            @name 释放连接
            @author hwliang<2020-08-07>
            @return void
        '''
        try:
            if self._host_row_id:
                public.M('ssh_login_record').where('id=?', self._host_row_id).update(
                    {'close_time': int(time.time())})
            if self._ssh:
                self._ssh.close()
            if self._tp:  # 关闭宿主服务
                self._tp.close()
            if self._ws.connected:
                self._ws.close()
        except:
            pass

    def set_attr(self, ssh_info):
        '''
            @name 设置对象属性，并连接服务器
            @author hwliang<2020-08-07>
            @return void
        '''
        self._host = ssh_info['host'].strip()
        self._port = int(ssh_info['port'])
        if 'username' in ssh_info:
            self._user = ssh_info['username']
        if 'pkey' in ssh_info:
            self._pkey = ssh_info['pkey']
        if 'password' in ssh_info:
            self._pass = ssh_info['password']
        if 'pkey_passwd' in ssh_info:
            self._key_passwd = ssh_info['pkey_passwd']
        try:
            result = self.connect()
        except Exception as ex:
            if str(ex).find("NoneType") == -1:
                raise public.PanelError(ex)
        return result

    def heartbeat(self):
        '''
            @name 心跳包
            @author hwliang<2020-09-10>
            @return void
        '''
        while True:
            time.sleep(30)
            if self._tp.is_active():
                self._tp.send_ignore()
            else:
                break
            if self._ws.connected:
                self._ws.send("")
            else:
                break

    def debug(self, msg):
        '''
            @name 写debug日志
            @author hwliang<2020-09-10>
            @return void
        '''
        msg = "{} - {}:{} => {} \n".format(public.format_date(), self._host, self._port, msg)
        self.history_send(msg)
        public.writeFile(self._debug_file, msg, 'a+')

    def run(self, web_socket, ssh_info=None):
        '''
            @name 启动SSH客户端对象
            @author hwliang<2020-08-07>
            @param web_socket<websocket> websocket句柄对像
            @param ssh_info<dict> SSH信息{
                host: 主机地址,
                port: 端口
                username: 用户名
                password: 密码
                pkey: 密钥(如果不为空，将使用密钥连接)
            }
            @return void
        '''
        try:
            self._ws = web_socket
            if not self._ssh:
                if not ssh_info:
                    return
                result = self.set_attr(ssh_info)
            else:
                result = returnMsg(True, '已连接')
            if result['status']:
                sendt = threading.Thread(target=self.send)
                recvt = threading.Thread(target=self.recv)
                ht = threading.Thread(target=self.heartbeat)
                sendt.start()
                recvt.start()
                ht.start()
                sendt.join()
                recvt.join()
                ht.join()
                self.close()
            else:
                self._ws.send(result['msg'])
                self.close()
        except:
            print(traceback.format_exc(), flush=True)

    def __del__(self):
        '''
            自动释放
        '''
        self.close()

    @staticmethod
    def create_ssh_key(key_type: str):
        """在没有秘钥时，自动创建"""
        public.ExecShell("ssh-keygen -t {s_type} -P '' -f /root/.ssh/id_{s_type} |echo y".format(s_type=key_type))
        authorized_keys = '/root/.ssh/authorized_keys'
        pub_file = "/root/.ssh/id_{s_type}.pub".format(s_type=key_type)
        public.ExecShell('cat %s >> %s && chmod 600 %s' % (pub_file, authorized_keys, authorized_keys))
        key_type_file = '{}/data/ssh_key_type.pl'.format(public.get_panel_path())
        public.writeFile(key_type_file, key_type)

    @staticmethod
    def create_ssh_key_for_other_user(user_name: str, user_home: str, key_type: str):
        tmp_sh_file = "/tmp/create_ssh_key_{}.sh".format(int(time.time()))
        public.writeFile(tmp_sh_file, """#!/bin/bash
HOME=$1
HASH_TYPE=$2

# 检查家目录是否存在，如果不存在则创建
if [ ! -d "${HOME}" ]; then
    mkdir "${HOME}"
fi

# 检查 .ssh 目录是否存在，如果不存在则创建
if [ ! -d "${HOME}/.ssh" ]; then
    mkdir "${HOME}/.ssh"
fi
# 设置正确的权限
chmod 700 "${HOME}/.ssh"

# 生成密钥对
# 检查 ${HASH_TYPE} 文件是否存在，如果不存在则生成密钥对
if [ ! -f "${HOME}/.ssh/id_${HASH_TYPE}" ]; then
    ssh-keygen -t ed25519 -f "${HOME}/.ssh/id_${HASH_TYPE}" -P ""
    # 将公钥添加到 authorized_keys 文件
    cat "${HOME}/.ssh/id_${HASH_TYPE}.pub" >> "${HOME}/.ssh/authorized_keys"
    chmod 600 "${HOME}/.ssh/id_${HASH_TYPE}"
    chmod 644 "${HOME}/.ssh/id_${HASH_TYPE}.pub"
    chmod 600 "${HOME}/.ssh/authorized_keys"
fi
""")
        public.ExecShell("sudo -u {user_name} bash {tmp_sh_file} {uer_home} {key_type}".format(
            user_name=user_name,
            tmp_sh_file=tmp_sh_file,
            uer_home=user_home,
            key_type=key_type,
        ))

        if os.path.exists(tmp_sh_file):
            os.remove(tmp_sh_file)


class local_ssh_terminal(ssh_terminal):

    class _LocalShell:
        basic_env = {
            "PATH": "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
            "HOME": "/root",  # 或其他你希望的家目录
            "TERM": "xterm-256color",
        }

        @staticmethod
        def get_last_login(username) -> str:
            # 执行 lastlog 命令
            try:
                output = subprocess.check_output(['lastlog', '-u', username]).decode()
            except:
                return ""

            # 提取信息
            lines = output.strip().split('\n')
            if len(lines) < 2:
                return ""  # 无登录记录

            data = lines[1].split()
            if len(data) < 3:
                return ""  # 无登录记录
            from_ip = data[2] if len(data) > 2 else "N/A"
            login_time = ' '.join(data[3:]) if len(data) > 3 else "Never"
            return "Last login: {} from {}\r\n".format(login_time, from_ip)

        @staticmethod
        def get_motd() -> str:
            if os.path.exists("/etc/motd"):
                data = public.readFile("/etc/motd")
                if isinstance(data, str):
                    if "\r\n" not in data:
                        data = data.replace("\n", "\r\n")
                    if not data.endswith("\r\n"):
                        data += "\r\n"
                    return  data
            return ""

        @staticmethod
        def _preexec_fn():
            os.setsid()
            os.chdir("/root")
            import signal
            # 重置 SIGINT 处理方式为默认
            signal.signal(signal.SIGINT, signal.SIG_DFL)
            signal.signal(signal.SIGTERM, signal.SIG_DFL)
            signal.signal(signal.SIGQUIT, signal.SIG_DFL)

        def __init__(self):
            self.master_fd, slave_fd = pty.openpty()

            # 设置PTY的终端属性，确保它可以正确处理控制字符
            try:
                # 获取当前终端属性
                attrs = termios.tcgetattr(slave_fd)
                # 启用规范模式和回显等
                attrs[0] |= termios.BRKINT | termios.ICRNL | termios.IXON
                attrs[0] &= ~termios.BRKINT  # 清除 IGNBRK 标志位
                attrs[3] |= termios.ECHO | termios.ECHONL | termios.ICANON | termios.ISIG | termios.IEXTEN
                # 设置输出标志
                attrs[1] |= termios.OPOST | termios.ONLCR
                # 设置控制字符
                attrs[6][termios.VINTR] = 3   # Ctrl+C -> SIGINT
                attrs[6][termios.VQUIT] = 28  # Ctrl+\ -> SIGQUIT
                attrs[6][termios.VERASE] = 127 # Backspace
                attrs[6][termios.VKILL] = 21  # Ctrl+U
                attrs[6][termios.VSTART] = 17 # Ctrl+Q
                attrs[6][termios.VSTOP] = 19  # Ctrl+S
                attrs[6][termios.VSUSP] = 26  # Ctrl+Z
                # 应用设置
                termios.tcsetattr(slave_fd, termios.TCSANOW, attrs)
            except termios.error:
                # 如果设置失败，继续使用默认设置
                public.print_error()

            # env -0 以\0 分割环境变量更稳定
            res = public.ExecShell("source /etc/profile > /dev/null 2>&1 && env -0", timeout=1, env=self.basic_env)
            env_dict = {}
            if isinstance(res, (tuple,list)):
                for line in res[0].split('\0'):
                    tmp = line.split('=', 1)
                    if len(tmp) == 2:
                        env_dict[tmp[0]] = tmp[1]
            env_dict.update(PWD="/root")
            sh_path = shutil.which('bash')
            if not sh_path:
                sh_path = shutil.which('sh')
            if not sh_path:
                bash_paths = ("/bin/bash", "/usr/bin/bash", "/usr/local/bin/bash", "/bin/sh")
                for path in bash_paths:
                    if os.path.exists(path):
                        sh_path = path
                        break
            if not sh_path:
                sh_path = "bash"
            self.proc = subprocess.Popen(
                [sh_path, "-l"],
                preexec_fn=self._preexec_fn,
                stdin=slave_fd,
                stdout=slave_fd,
                stderr=slave_fd,
                close_fds=True,
                env=env_dict,  # 只传递你想要的环境变量
            )

            os.close(slave_fd)
            self.maybe_logout = False
            self.first_recv = b"The current terminal create by BT-Panel.\r\n"
            last_log = self.get_last_login("root")
            if last_log:
                self.first_recv = last_log.encode() + self.first_recv
            motd = self.get_motd()
            if motd:
                self.first_recv = motd.encode() + self.first_recv

        def send(self, data: str):
            if not self.is_active():
                return
            try:
                os.write(self.master_fd, data.encode())
            except OSError as e:
                self.close()
                raise

        def send_ignore(self):
            self.send('')

        def recv(self, length: int) -> bytes:
            if self.first_recv:
                res = self.first_recv
                self.first_recv = None
                return res
            r, _, _ = select.select([self.master_fd], [], [])
            res = b''
            if self.master_fd in r:
                try:
                    res = os.read(self.master_fd, length)
                    if res.endswith(b"exit\r\n"):
                        self.maybe_logout = True
                    else:
                        self.maybe_logout = False
                except OSError as e:
                    self.close()

            if self.maybe_logout and not res:
                res = '登出\r\n'.encode()
            return res

        def resize_pty(self, width, height):
            win_size = struct.pack('HHHH', height, width, 0, 0)
            fcntl.ioctl(self.master_fd, termios.TIOCSWINSZ, win_size)

        def close(self):
            if hasattr(self, 'master_fd') and self.master_fd >= 0:
                try:
                    os.close(self.master_fd)
                except OSError:
                    pass
                finally:
                    self.master_fd = -1  # 标记为已关闭

            if hasattr(self, 'proc') and self.proc:
                try:
                    self.proc.terminate()
                    self.proc.wait(timeout=1)
                except (subprocess.TimeoutExpired, OSError):
                    self.proc.kill()
                finally:
                    self.proc = None

        def is_active(self):
            if self.proc is None:
                return False
            if self.proc.poll() is not None:
                self.close()  # 自动清理资源
                return False
            return True

    def connect(self):
        '''
            @name 连接服务器
            @author hwliang<2020-08-07>
            @return dict{
                status: bool 状态
                msg: string 详情
            }
        '''
        if not self._host: return returnMsg(False, '错误的连接地址')
        if not self._user: self._user = 'root'
        if not self._port: self._port = 22
        if not self._host in ['127.0.0.1', 'localhost']:
            return returnMsg(False, '仅用于本机链接')
        if os.path.isfile(public.get_panel_path() + "/data/fast_shell_off.pl"):
            return returnMsg(False, '请先开启快速登录功能')

        self.debug('认证成功，正在构建会话通道')
        try:
            self._ssh = self._LocalShell()
        except:
            self.debug('自动认证失败，正在尝试使用密码认证')
            public.print_error()
            return super(local_ssh_terminal, self).connect()
        self._tp = self._ssh
        self._connect_time = time.time()
        self._last_send = []
        from BTPanel import request, session
        self._client = public.GetClientIp() + ':' + str(public.get_remote_port())
        public.WriteLog(self._log_type, '成功登录到SSH服务器 [{}:{}]'.format(self._host, self._port))
        self.history_send("登录成功\n")
        self.debug('通道已构建')
        self._video_addr = "/www/server/panel/data/jumpserver_video/%s.json" % str(int(self._connect_time))
        if not os.path.exists("//www/server/panel/data/jumpserver_video/"):
            os.makedirs("/www/server/panel/data/jumpserver_video/")
        # 如果开启了录像功能
        self._connect_ua = str(request.headers.get('User-Agent'))
        if os.path.exists(public.get_panel_path() + "/data/open_ssh_login.pl"):
            self._host_row_id = public.M('ssh_login_record').add(
                'addr,server_ip,ssh_user,user_agent,login_time,video_addr',
                (self._client, self._host, self._user, self._connect_ua
                     , int(self._connect_time),
                 self._video_addr))

            self.record('header', {
                "version": 1,
                "width": 100,
                "height": 29,
                "timestamp": int(self._connect_time),
                "env": {
                    "TERM": "xterm",
                    "SHELL": "/bin/bash",
                },
                "stdout": []
            })

        return returnMsg(True, '连接成功')


class ssh_host_admin(ssh_terminal):
    _panel_path = '/www/server/panel'
    _save_path = _panel_path + '/config/ssh_info/'
    _pass_file = _panel_path + '/data/a_pass.pl'
    _user_command_file = _save_path + '/user_command.json'
    _sys_command_file = _save_path + '/sys_command.json'
    _pass_str = None

    def __init__(self):
        self.__create_aes_pass()

    def __create_aes_pass(self):
        '''
            @name 创建AES密码
            @author
            @return string
        '''
        if not os.path.exists(self._save_path):
            os.makedirs(self._save_path, 384)
        if not os.path.exists(self._pass_file):
            public.writeFile(self._pass_file, public.GetRandomString(16))
            public.set_mode(self._pass_file, 600)
        if not self._pass_str:
            self._pass_str = public.readFile(self._pass_file)
            if not self._pass_str:
                self._pass_str = public.GetRandomString(16)
                public.writeFile(self._pass_file, self._pass_str)
                public.set_mode(self._pass_file, 600)

    def get_host_list(self, args=None):
        '''
            @name 获取本机保存的SSH信息列表
            @author hwliang<2020-08-07>
            @param args<dict_obj or None>
            @return list
        '''

        host_list = []
        for name in os.listdir(self._save_path):
            info_file = self._save_path + name + '/info.json'
            if not os.path.exists(info_file): continue
            try:
                info_tmp = self.get_ssh_info(name)
                host_info = {}
                host_info['host'] = name
                host_info['port'] = info_tmp['port']
                host_info['ps'] = info_tmp['ps']
                host_info['sort'] = int(info_tmp['sort'])
            except:
                if os.path.exists(info_file):
                    os.remove(info_file)
                continue

            host_list.append(host_info)

        host_list = sorted(host_list, key=lambda x: x['sort'], reverse=False)
        return host_list

    def get_host_find(self, args):
        '''
            @name 获取指定SSH信息
            @author hwliang<2020-08-07>
            @param args<dict_obj>{
                host: 主机地址
            }
            @return dict
        '''
        args.host = args.host.strip()
        info_file = self._save_path + args.host + '/info.json'
        if not os.path.exists(info_file):
            return public.returnMsg(False, '指定SSH信息不存在!')
        info_tmp = self.get_ssh_info(args.host)
        host_info = {}
        host_info['host'] = info_tmp['host']
        host_info['port'] = info_tmp['port']
        host_info['ps'] = info_tmp['ps']
        host_info['sort'] = info_tmp['sort']
        host_info['username'] = info_tmp['username']
        host_info['password'] = info_tmp['password']
        host_info['pkey'] = info_tmp['pkey']
        host_info['pkey_passwd'] = ''
        if 'pkey_passwd' in info_tmp:
            host_info['pkey_passwd'] = info_tmp['pkey_passwd']
        return host_info

    def modify_host(self, args, old_type=False):
        '''
            @name 修改SSH信息
            @author hwliang<2020-08-07>
            @param args<dict_obj>{
                host: 被修改的主机地址,
                new_host: 新的主机地址,
                port: 端口
                ps: 备注
                sort: 排序(可选)
                username: 用户名
                password: 密码
                pkey: 密钥(如果不为空，将使用密钥连接)
                pkey_passwd: 密钥的密码
            }
            @return dict
        '''
        args.new_host = args.new_host.strip()
        args.host = args.host.strip()
        old_host_path = self._save_path + args.new_host + "_" + args.port + '/info.json'
        if old_type:
            old_host_path = self._save_path + args.new_host + '/info.json'
        new_host_path = self._save_path + args.host + "_" + args.port + '/info.json'

        if args.host != args.new_host:
            # info_file = self._save_path + args.new_host+ "_" + args.port + '/info.json'
            if os.path.exists(new_host_path):
                return public.returnMsg(False, '指定host地址已经在其它SSH信息中添加过了!')

        # info_file = self._save_path + args.host + "_" + args.port + '/info.json'

        if not os.path.exists(old_host_path):
            return public.returnMsg(False, '指定SSH信息不存在!')

        if not 'sort' in args:
            r_data = public.aes_decrypt(public.readFile(old_host_path), self._pass_str)
            info_tmp = json.loads(r_data)
            args.sort = info_tmp['sort']

        host_info = {}
        host_info['host'] = args.new_host
        host_info['port'] = int(args['port'])
        host_info['ps'] = args['ps']
        host_info['sort'] = args['sort']
        host_info['username'] = args['username']
        host_info['password'] = args['password']
        host_info['pkey'] = args['pkey']
        if 'pkey_passwd' in args:
            host_info['pkey_passwd'] = args['pkey_passwd']
        else:
            host_info['pkey_passwd'] = ''
        if not host_info['pkey']: host_info['pkey'] = ''
        # result = self.set_attr(host_info)
        # if not result['status']: return result
        self.save_ssh_info(args.host, host_info, self._save_path + args.new_host + "_" + args.port)
        if old_type:
            import shutil
            shutil.rmtree(os.path.dirname(old_host_path))
        if args.host != args.new_host:
            public.ExecShell('mv {} {}'.format(old_host_path, new_host_path))
        public.WriteLog(self._log_type, '修改HOST:{}的SSH信息'.format(args.host))
        return public.returnMsg(True, '修改成功')

    def create_host(self, args):
        '''
            @name 添加SSH信息
            @author hwliang<2020-08-07>
            @param args<dict_obj>{
                host: 主机地址,
                port: 端口
                ps: 备注
                sort: 排序(可选，默认0)
                username: 用户名
                password: 密码
                pkey: 密钥(如果不为空，将使用密钥连接)
                pkey_passwd： 密钥的密码
            }
            @return dict
        '''
        args.host = args.host.strip()
        host_path = self._save_path + args.host + "_" + args.port
        old_type_info = self.get_ssh_info(args.host)
        if isinstance(old_type_info, dict) and old_type_info.get("host", None) == args.host and str(old_type_info.get("port", None)) == args.port:
            args.new_host = args.host
            return self.modify_host(args, old_type=True)
        info_file = host_path + '/info.json'
        if os.path.exists(info_file):
            args.new_host = args.host
            return self.modify_host(args)
            # return public.returnMsg(False,'指定SSH信息已经添加过了!')
        if not os.path.exists(host_path):
            os.makedirs(host_path, 384)
        if not 'sort' in args: args.sort = 0
        if not 'ps' in args: args.ps = args.host
        host_info = {}
        host_info['host'] = args.host
        host_info['port'] = int(args['port'])
        host_info['ps'] = args['ps']
        host_info['sort'] = int(args['sort'])
        host_info['username'] = args['username']
        host_info['password'] = args['password']
        host_info['pkey'] = args['pkey']
        host_info['pkey_passwd'] = ''
        if 'pkey_passwd' in args:
            host_info['pkey_passwd'] = args['pkey_passwd']
        # result = self.set_attr(host_info)
        # if not result['status']: return result
        self.save_ssh_info(args.host, host_info, host_path)
        public.WriteLog(self._log_type, '添加HOST:{} SSH信息'.format(args.host))
        return public.returnMsg(True, '添加成功')

    def remove_host(self, args):
        '''
            @name 删除指定SSH信息
            @author hwliang<2020-08-07>
            @param args<dict_obj>{
                host: 主机地址
            }
            @return dict
        '''
        args.host = args.host.strip()
        if not args.host: return public.returnMsg(False, '错误的参数')
        host_path = self._save_path + args.host
        if not os.path.exists(host_path):
            return public.returnMsg(False, '指定SSH信息不存在!')
        public.ExecShell("rm -rf {}".format(host_path))
        public.WriteLog(self._log_type, '删除HOST:{} SSH信息'.format(args.host))
        return public.returnMsg(True, '删除成功')

    def get_ssh_info(self, host):
        '''
            @name 获取并解密指定SSH信息
            @author hwliang<2020-08-07>
            @param  host<string> 主机地址
            @return dict or False
        '''
        info_file = self._save_path + host + '/info.json'
        if not os.path.exists(info_file): return False
        try:
            r_data = public.aes_decrypt(public.readFile(info_file), self._pass_str)
        except ValueError as ex:
            r_data = '{}'
            if str(ex).find('Incorrect AES key length') != -1:
                if os.path.exists(self._pass_file):
                    os.remove(self._pass_file)
                self.__create_aes_pass()
                r_data = public.aes_decrypt(public.readFile(info_file), self._pass_str)

        return json.loads(r_data)

    def save_ssh_info(self, host, host_info, host_path=None):

        '''
            @name 获取并解密指定SSH信息
            @author hwliang<2020-08-07>
            @param  host<string> 主机地址
            @param  host_info<dict> ssh信息字典
            @return bool
        '''
        host_path = host_path if host_path else self._save_path + host
        if not os.path.exists(host_path):
            os.makedirs(host_path, 384)
        info_file = host_path + '/info.json'
        r_data = public.aes_encrypt(json.dumps(host_info), self._pass_str)
        public.writeFile(info_file, r_data)
        return True

    def set_sort(self, args):
        '''
            @name 获取并解密指定SSH信息
            @author hwliang<2020-08-07>
            @param  args<dict_obj>{
                sort_list<json>{
                    主机host : 排序编号,
                    主机host : 排序编号,
                    ...
                }
            }
            @return bool
        '''
        if not 'sort_list' in args:
            return public.returnMsg(False, '请传入sort_list字段')
        sort_list = json.loads(args.sort_list)
        for name in sort_list.keys():
            info_file = self._save_path + name + '/info.json'
            if not os.path.exists(info_file): continue

            ssh_info = self.get_ssh_info(name)
            ssh_info['sort'] = int(sort_list[name])
            self.save_ssh_info(name, ssh_info)
        return public.returnMsg(True, '排序已保存')

    def get_command_list(self, args=None, user_cmd=False, sys_cmd=False):
        '''
            @name 获取常用命令列表
            @author hwliang<2020-08-08>
            @param  args<dict_obj>
            @param  user_cmd<bool> 是否不获取用户配置
            @param  sys_cmd<bool>  是否不获取系统配置
            @return list
        '''
        sys_command = []
        if not sys_cmd:
            if os.path.exists(self._sys_command_file):
                sys_command = json.loads(public.readFile(self._sys_command_file))

        user_command = []
        if not user_cmd:
            if os.path.exists(self._user_command_file):
                user_command = json.loads(public.readFile(self._user_command_file))

        command = sys_command + user_command
        return command

    def command_exists(self, command, title):
        '''
            @name 判断命令是否存在
            @author hwliang<2020-08-08>
            @param  command<list> 常用命令列表
            @param  title<string> 命令标题
            @return bool
        '''
        for cmd in command:
            if cmd['title'] == title: return True
        return False

    def save_command(self, command, sys_cmd=False):
        '''
            @name 保存常用命令
            @author hwliang<2020-08-08>
            @param  command<list> 常用命令列表
            @param  sys_cmd<bool> 是否为系统配置
            @return void
        '''
        s_file = self._user_command_file
        if sys_cmd:
            s_file = self._sys_command_file
        public.writeFile(s_file, json.dumps(command))

    def create_command(self, args):
        '''
            @name 创建常用命令
            @author hwliang<2020-08-08>
            @param  args<dict_obj>{
                title<string> 标题
                shell<string> 命令文本
            }
            @return dict
        '''
        args.title = args.title.strip()
        command = self.get_command_list(sys_cmd=True)

        if self.command_exists(command, args.title):
            return public.returnMsg(False, '指定命令名称已存在')

        cmd = {
            "title": args.title,
            "shell": args.shell.strip()
        }

        command.append(cmd)
        self.save_command(command)
        public.WriteLog(self._log_type, '添加常用命令[{}]'.format(args.title))
        return public.returnMsg(True, '添加成功')

    def get_command_find(self, args=None, title=None):
        '''
            @name 获取指定命令信息
            @author hwliang<2020-08-08>
            @param  args<dict_obj>{
                title<string> 标题
            } 可选
            @param title 标题 可选
            @return dict
        '''
        if args: title = args.title.strip()
        command = self.get_command_list()
        for cmd in command:
            if cmd['title'] == title or cmd['title'] == args.title:
                return cmd
        return public.returnMsg(False, '指定命令不存在')

    def modify_command(self, args):
        '''
            @name 修改常用命令
            @author hwliang<2020-08-08>
            @param  args<dict_obj>{
                title<string> 标题
                new_title<string> 新标题
                shell<string> 命令文本
            }
            @return dict
        '''
        title = args.title.strip()
        command = self.get_command_list(sys_cmd=True)
        if not self.command_exists(command, args.title):
            return public.returnMsg(False, '指定命令不存在')
        for i in range(len(command)):
            if command[i]['title'] == args.title or command[i]['title'] == title:
                command[i]['title'] = args.new_title.strip()
                command[i]['shell'] = args.shell.strip()
                break
        self.save_command(command)
        public.WriteLog(self._log_type, '修改常用命令[{}]'.format(args.title))
        return public.returnMsg(True, '修改成功')

    def remove_command(self, args):
        '''
            @name 删除指定命令
            @author hwliang<2020-08-08>
            @param  args<dict_obj>{
                title<string> 标题
            }
            @return dict
        '''
        args.title = args.title.strip()
        command = self.get_command_list(sys_cmd=True)
        if not self.command_exists(command, args.title):
            return public.returnMsg(False, '指定命令不存在')
        for i in range(len(command)):
            if command[i]['title'] == args.title:
                del (command[i])
                break

        self.save_command(command)
        public.WriteLog(self._log_type, '删除常用命令[{}]'.format(args.title))
        return public.returnMsg(True, '删除成功')

    def into_command(self, args):
        '''
            @name 导入命令
            @author law<2023-11-13>
            @param  args
            @return
        '''
        command_file_path = "/tmp/incommand.csv"

        from files import files
        fileObj = files()
        ff = fileObj.upload(args)

        if ff["status"]:
            command = self.get_command_list(sys_cmd=True)
            import csv
            import chardet

            encoding = "utf-8"
            with open(command_file_path, "rb") as f:
                encoding = chardet.detect(f.read())['encoding']
            with open(command_file_path, 'r', encoding=encoding) as f:
                reader = csv.reader(f)

                next(reader)
                for row in reader:
                    cmd = {
                        "title": row[0].strip(),
                        "shell": row[1].strip()
                    }

                    if self.command_exists(command, cmd['title']):
                        continue

                    command.append(cmd)

            # 写日志
            titles = [t["title"] for t in command]
            public.WriteLog(self._log_type, '导入常用命令[{}]'.format(titles))

            self.save_command(command)

            # 删除临时文件
            if os.path.exists(command_file_path):
                os.remove(command_file_path)

            return public.returnMsg(True, '导入成功')

        return public.returnMsg(False, '导入失败')


    def out_command(self, args):
        '''
            @name 导出命令
            @author law<2023-11-13>
            @return .csv
        '''
        export_file_path = "/tmp/outcommand.csv"

        # 删除临时文件
        if os.path.exists(export_file_path):
            os.remove(export_file_path)
        try:
            command = self.get_command_list(sys_cmd=True)
            if not command:
                return public.returnMsg(False, '没有可导出的命令')

            for i in command:
                i["title"] = i["title"].strip()
                i["shell"] = i["shell"].strip()

            # 写日志
            titles = [t["title"] for t in command]
            public.WriteLog(self._log_type, '导出常用命令{}'.format(titles))

            # 写入临时文件
            with open(export_file_path, mode="w+", encoding="utf-8") as fp:
                fp.write("名称,命令\n")
                for line in command:
                    tmp = (
                        line["title"],
                        line["shell"],
                    )
                    fp.write(",".join(tmp))
                    fp.write("\n")

            return public.returnMsg(True, export_file_path)

        except Exception as e:
            return public.returnMsg(False, '导出失败')

    @staticmethod
    def completion_tool_status(args):
        zh_json_file = "{}/BTPanel/static/zh.json.gz".format(public.get_panel_path())
        status_file = "{}/data/use_completion_tool.pl".format(public.get_panel_path())
        if os.path.exists(status_file) and os.path.exists(zh_json_file):
                return public.returnMsg(True, "启用中")
        return public.returnMsg(False, "未启用")

    @staticmethod
    def set_completion_tool_status(args):
        status = args.get("status/d", 0)
        status_file = "{}/data/use_completion_tool.pl".format(public.get_panel_path())
        if not status:
            if os.path.exists(status_file):
                os.remove(status_file)
            return public.returnMsg(True, "关闭成功")


        zh_json_file = "{}/BTPanel/static/zh.json.gz".format(public.get_panel_path())
        if not os.path.exists(zh_json_file):
            public.downloadFile("https://download.bt.cn/src/zh.json.gz", zh_json_file)
        if not os.path.exists(zh_json_file):
            return public.returnMsg(False, "开启失败，获取补全插件包失败，无法打开，请检查网络环境后再重试")
        if not os.path.exists(status_file):
            public.writeFile(status_file, "")
        return public.returnMsg(True, "开启成功")
