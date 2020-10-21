#coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板 
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: hwliang <hwl@bt.cn>
# +-------------------------------------------------------------------
import json
import time
import os
import sys
import socket
import threading
import re


if not 'class/' in sys.path:
    sys.path.insert(0,'class/')
from io import BytesIO, StringIO

def returnMsg(status,msg):
    return {'status':status,'msg':msg}

import public

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

    def connect(self):
        '''
            @name 连接服务器
            @author hwliang<2020-08-07>
            @return dict{
                status: bool 状态
                msg: string 详情
            }
        '''
        if not self._host: return returnMsg(False,'错误的连接地址')

        if not self._user: self._user = 'root'
        if not self._port: self._port = 22
        self.is_local()

        if self._host in ['127.0.0.1','localhost']:
            self._port = public.get_ssh_port()

        num = 0
        while num < 5:
            num +=1
            try:
                self.debug('正在尝试第{}次连接'.format(num))
                if self._rep_ssh_config: time.sleep(0.1)
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2 + num)
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 8192)
                sock.connect((self._host, self._port))
                break
            except Exception as e:
                if num == 5:
                    self.set_sshd_config(True)
                    self.debug('重试连接失败,{}'.format(e))
                    if self._host in ['127.0.0.1','localhost']:
                        return returnMsg(False,'连接目标服务器失败: {}'.format("Authentication failed ," + self._user + "@" + self._host + ":" +str(self._port)))
                    return returnMsg(False,'连接目标服务器失败, {}:{}'.format(self._host,self._port))
                else:
                    time.sleep(0.2)


        import paramiko

        self._tp = paramiko.Transport(sock)

        try:
            self._tp.start_client()
            self.debug(self._pkey)
            if not self._pass and not self._pkey:
                self.set_sshd_config(True)
                return public.returnMsg(False,'密码或私钥不能都为空: {}:{}'.format(self._host,self._port))
            self._tp.banner_timeout=60
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
                
                try:
                    pkey = paramiko.RSAKey.from_private_key(p_file)
                except:
                    try:
                        p_file.seek(0) # 重置游标
                        pkey = paramiko.Ed25519Key.from_private_key(p_file)
                    except:
                        try:
                            p_file.seek(0)
                            pkey = paramiko.ECDSAKey.from_private_key(p_file)
                        except:
                            p_file.seek(0)
                            pkey = paramiko.DSSKey.from_private_key(p_file)

                self._tp.auth_publickey(username=self._user, key=pkey)
            else:
                self.debug('正在认证密码')
                self._tp.auth_password(username=self._user, password=self._pass)
        except Exception as e:
            if self._old_conf:
                s_file = '/www/server/panel/config/t_info.json'
                if os.path.exists(s_file): os.remove(s_file)
            self.set_sshd_config(True)
            self._tp.close()
            e = str(e)
            if e.find('Authentication failed') != -1:
                self.debug('认证失败{}'.format(e))
                return returnMsg(False,'帐号或密码错误: {}'.format(e + "," + self._user + "@" + self._host + ":" +str(self._port)))
            if e.find('Bad authentication type; allowed types') != -1:
                self.debug('认证失败{}'.format(e))
                if self._host in ['127.0.0.1','localhost'] and self._pass == 'none':
                    return returnMsg(False,'帐号或密码错误: {}'.format("Authentication failed ," + self._user + "@" + self._host + ":" +str(self._port))) 
                return returnMsg(False,'不支持的身份验证类型: {}'.format(e))
            if e.find('Connection reset by peer') != -1:
                self.debug('目标服务器主动拒绝连接')
                return returnMsg(False,'目标服务器主动拒绝连接')
            if e.find('Error reading SSH protocol banner') != -1:
                self.debug('协议头响应超时')
                return returnMsg(False,'协议头响应超时，与目标服务器之间的网络质量太糟糕：' + e)
            if not e:
                self.debug('SSH协议握手超时')
                return returnMsg(False,"SSH协议握手超时，与目标服务器之间的网络质量太糟糕")
            err =  public.get_error_info()
            self.debug(err)
            return returnMsg(False,"未知错误: {}".format(err))

        self.debug('认证成功，正在构建会话通道')
        self._ssh = self._tp.open_session()
        self._ssh.get_pty(term='xterm', width=100, height=34)
        self._ssh.invoke_shell()
        self._connect_time = time.time()
        self._last_send = []
        from BTPanel import request
        self._client = public.GetClientIp() +':' + str(request.environ.get('REMOTE_PORT'))
        public.WriteLog(self._log_type,'成功登录到SSH服务器 [{}:{}]'.format(self._host,self._port))
        self.history_send("登录成功\n")
        self.set_sshd_config(True)
        self.debug('通道已构建')
        return returnMsg(True,'连接成功')


    def get_login_user(self):
        '''
            @name 获取本地登录用户
            @author hwliang<2020-08-07>
            @return string
        '''

        if self._user != 'root': return self._user
        l_user = 'root'
        ssh_config_file = '/etc/ssh/sshd_config'
        ssh_config = public.readFile(ssh_config_file)
        if not ssh_config: return l_user
        
        if ssh_config.find('PermitRootLogin yes') != -1: return l_user


        user_list  = self.get_ulist()
        login_user = ''
        for u_info in user_list:
            if u_info['user'] == 'root': continue
            if u_info['login'] == '/bin/bash':
                login_user = u_info['user']
                break

        if not login_user:
            return l_user
        
        return login_user


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
            u_info = {}
            u_info['user'],u_info['pass'],u_info['uid'],u_info['gid'],u_info['user_msg'],u_info['home'],u_info['login'] = u_tmp
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
        if self._host in ['127.0.0.1','localhost']:
            try:
                self._port = public.get_ssh_port()
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

                login_user = self.get_login_user()
                if self._user == 'root' and login_user == 'root':
                    id_rsa_file = ['/root/.ssh/id_rsa','/root/.ssh/id_rsa_bt']
                    for ifile in id_rsa_file:
                        if os.path.exists(ifile):
                            self._pkey = public.readFile(ifile)
                            host_path = self._save_path + self._host
                            if not os.path.exists(host_path):
                                os.makedirs(host_path,384)
                            return


                if not self._pass or not self._pkey or not self._user:
                    home_path = '/home/' + login_user
                    if login_user == 'root':
                        home_path = '/root'
                    self._user = login_user
                    id_rsa_file = [home_path + '/.ssh/id_rsa',home_path + '/.ssh/id_rsa_bt']
                    for ifile in id_rsa_file:
                        if os.path.exists(ifile):
                            self._pkey = public.readFile(ifile)
                            return
                
                    self._pass = 'none'
                    return
                    # _ssh_ks = home_path + '/.ssh'
                    # if not  os.path.exists(_ssh_ks):
                    #     os.makedirs(_ssh_ks,384)
                    # os.system("ssh-keygen -t rsa -P '' -f {}/.ssh/id_rsa |echo y".format(home_path))
                    # pub_file = home_path + '/.ssh/id_rsa.pub'
                    # az_file = home_path + '/.ssh/authorized_keys'
                    # rsa_file = home_path + '/.ssh/id_rsa'
                    # public.ExecShell('cat {} >> {} && chmod 600 {} {}'.format(pub_file, az_file, az_file,rsa_file))
                    # os.remove(pub_file)
                    # public.ExecShell("chown -R {}:{} {}".format(self._user,self._user,_ssh_ks))
                    # public.ExecShell("chmod -R 600 {}".format(_ssh_ks))
                    # self._pkey = public.readFile(rsa_file)
                    

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
            version = public.readFile('/etc/issue').strip().split("\n")[0].replace('\\n','').replace('\l','').strip()
        else:
            version = version.replace('release ','').replace('Linux','').replace('(Core)','').strip()
        return version

    def get_ssh_status(self):
        '''
            @name 获取SSH服务状态
            @author hwliang<2020-08-13>
            @return bool
        '''
        version = self.get_sys_version()
        if os.path.exists('/usr/bin/apt-get'):
            if os.path.exists('/etc/init.d/sshd'):
                status = public.ExecShell("service sshd status | grep -P '(dead|stop|not running)'|grep -v grep")
            else:
                status = public.ExecShell("service ssh status | grep -P '(dead|stop|not running)'|grep -v grep")
        else:
            if version.find(' 7.') != -1 or version.find(' 8.') != -1 or version.find('Fedora') != -1:
                status = public.ExecShell("systemctl status sshd.service | grep 'dead'|grep -v grep")
            else:
                status = public.ExecShell("/etc/init.d/sshd status | grep -e 'stopped' -e '已停'|grep -v grep")
        if len(status[0]) > 3:
            status = False
        else:
            status = True
        return status

    def is_running(self,rep = False):
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


    def set_sshd_config(self,rep = False):
        '''
            @name 设置本地SSH配置文件，以支持pubkey认证
            @author hwliang<2020-08-13>
            @param rep<bool> 是否恢复ssh配置文件
            @return bool
        '''
        self.is_running(rep)
        return False
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
                    public.writeFile(sshd_config_file,self._sshd_config_backup)
                    self.restart_ssh()
                return True

            

            pin = r'^\s*PubkeyAuthentication\s+(yes|no)'
            pubkey_status = re.findall(pin,sshd_config,re.I)
            if pubkey_status:
                if pubkey_status[0] == 'yes':
                    pubkey_status = True
                else:
                    pubkey_status = False
            
            pin = r'^\s*RSAAuthentication\s+(yes|no)'
            rsa_status = re.findall(pin,sshd_config,re.I)
            if rsa_status:
                if rsa_status[0] == 'yes':
                    rsa_status = True
                else:
                    rsa_status = False
            
            self._sshd_config_backup = sshd_config
            is_write = False
            if not pubkey_status:
                sshd_config = re.sub(r'\n#?PubkeyAuthentication\s\w+','\nPubkeyAuthentication yes',sshd_config)
                is_write = True
            if not rsa_status:
                sshd_config = re.sub(r'\n#?RSAAuthentication\s\w+','\nRSAAuthentication yes',sshd_config)
                is_write = True

            if is_write:
                public.writeFile(sshd_config_file,sshd_config)
                self._rep_ssh_config = True
                self.restart_ssh()
            else:
                self._sshd_config_backup = None

            return True
        except:
            return False
    
    def restart_ssh(self,act = 'reload'):
        '''
        重启ssh 无参数传递
        '''
        version = public.readFile('/etc/redhat-release')
        if not os.path.exists('/etc/redhat-release'):
            public.ExecShell('service ssh ' + act)
        elif version.find(' 7.') != -1 or version.find(' 8.') != -1:
            public.ExecShell("systemctl " + act + " sshd.service")
        else:
            public.ExecShell("/etc/init.d/sshd " + act)
    
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
            while not self._ws.closed:
                resp_line = self._ssh.recv(1024)
                if not resp_line:
                    if not self._tp.is_active():
                        self.debug('通道已断开')
                        self._ws.send('连接已断开,按回车将尝试重新连接!')
                        self.close()
                        return
                
                if not resp_line: 
                    n+=1
                    if n > 5: break
                    continue
                n = 0
                if self._ws.closed:
                    return
                try:
                    result = resp_line.decode('utf-8','ignore')
                except:
                    try:
                        result = resp_line.decode()
                    except:
                        result = str(resp_line)

                self._ws.send(result)
                
                self.history_recv(result)
        except Exception as e:
            e = str(e)
            if e.find('closed') != -1:
                self.debug('会话已中断')
            elif not self._ws.closed:
                self.debug('读取tty缓冲区数据发生错误,{}'.format(e))
            
        if self._ws.closed:
            self.debug('客户端已主动断开连接')
        self.close()
    
    def send(self):
        '''
            @name 写入数据到缓冲区
            @author hwliang<2020-08-07>
            @return void
        '''
        try:
            while not self._ws.closed:
                client_data = self._ws.receive()
                if not client_data: continue
                if len(client_data) > 10:
                    if client_data.find('{"host":"') != -1:
                        continue
                    if client_data.find('"resize":1') != -1:
                        self.resize(client_data)
                        continue
                self._ssh.send(client_data)
                self.history_send(client_data)
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

        if self._ws.closed:
            self.debug('客户端已主动断开连接')
        self.close()


    def history_recv(self,recv_data):
        '''
            @name 从接收实体保存命令
            @author hwliang<2020-08-12>
            @param recv_data<string> 数据实体
            @return void
        '''
        #处理TAB补登
        if self._last_cmd_tip == 1:
            if not recv_data.startswith('\r\n'):
                self._last_cmd += recv_data.replace('\u0007','').strip()
            self._last_cmd_tip = 0

        #上下切换命令
        if self._last_cmd_tip == 2:
            self._last_cmd = recv_data.strip().replace("\x08","").replace("\x07","").replace("\x1b[K","")
            self._last_cmd_tip = 0

    def history_send(self,send_data):
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

        #上下切换命令
        if send_data in ["\x1b[A","\x1b[B"]:
            self._last_cmd_tip = 2
            return
        
        #退格
        if send_data == "\x7f":
            self._last_cmd = self._last_cmd[:-1]
            return

        #过滤特殊符号
        if send_data in ["\x1b[C","\x1b[D","\x1b[K","\x07","\x08","\x03","\x01","\x02","\x04","\x05","\x06","\u0007"]:
            return
        
        #Tab补全处理
        if send_data == '\t':
            self._last_cmd_tip = 1
            return

        if send_data[-1] in ['\r','\n']:
            if not self._last_cmd: return
            his_shell = [int(time.time()),self._client,self._user,self._last_cmd]
            public.writeFile(his_file, json.dumps(his_shell) + "\n","a+")
            self._last_cmd = ""

            #超过5M则保留最新的200行
            if os.stat(his_file).st_size > 5242880:
                his_tmp = public.GetNumLines(his_file,200)
                public.writeFile(his_file, his_tmp)
        else:
            self._last_cmd += send_data
    

    def close(self):
        '''
            @name 释放连接
            @author hwliang<2020-08-07>
            @return void
        '''
        try:
            if self._ssh:
                self._ssh.close()
                #self._ssh = None
            if not self._ws.closed:
                self._ws.close()
        except:
            pass


    def set_attr(self,ssh_info):
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
        
        result = self.connect()
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
            if not self._ws.closed:
                self._ws.send("")
            else:
                break
                
    def debug(self,msg):
        '''
            @name 写debug日志
            @author hwliang<2020-09-10>
            @return void
        '''
        msg = "{} - {}:{} => {} \n".format(public.format_date(),self._host,self._port,msg)
        public.writeFile(self._debug_file,msg,'a+')

    def run(self,web_socket, ssh_info=None):
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
        self._ws = web_socket
        if not self._ssh:
            if not ssh_info:
                return
            result = self.set_attr(ssh_info)
        else:
            result = returnMsg(True,'已连接')
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

    def __del__(self):
        '''
            自动释放
        '''
        self.close()



class ssh_host_admin(ssh_terminal):
    _panel_path = '/www/server/panel'
    _save_path = _panel_path + '/config/ssh_info/'
    _pass_file = _panel_path + '/data/a_pass.pl'
    _user_command_file = _save_path + '/user_command.json'
    _sys_command_file = _save_path + '/sys_command.json'
    _pass_str = None

    def __init__(self):
        if not os.path.exists(self._save_path):
            os.makedirs(self._save_path,384)
        if not os.path.exists(self._pass_file):
            public.writeFile(self._pass_file,public.GetRandomString(16))
            public.set_mode(self._pass_file,600)
        if not self._pass_str:
            self._pass_str = public.readFile(self._pass_file)

    def get_host_list(self,args = None):
        '''
            @name 获取本机保存的SSH信息列表
            @author hwliang<2020-08-07>
            @param args<dict_obj or None>
            @return list
        '''

        host_list = []
        for name in os.listdir(self._save_path):
            info_file = self._save_path + name +'/info.json'
            if not os.path.exists(info_file): continue
            info_tmp = self.get_ssh_info(name)
            host_info = {}
            host_info['host'] = name
            host_info['port'] = info_tmp['port']
            host_info['ps'] = info_tmp['ps']
            host_info['sort'] = int(info_tmp['sort'])

            host_list.append(host_info)
        
        host_list = sorted(host_list,key=lambda x: x['sort'],reverse=False)
        return host_list

    def get_host_find(self,args):
        '''
            @name 获取指定SSH信息
            @author hwliang<2020-08-07>
            @param args<dict_obj>{
                host: 主机地址
            }
            @return dict
        '''
        args.host = args.host.strip()
        info_file = self._save_path + args.host +'/info.json'
        if not os.path.exists(info_file):
            return public.returnMsg(False,'指定SSH信息不存在!')
        info_tmp = self.get_ssh_info(args.host)
        host_info = {}
        host_info['host'] = args.host
        host_info['port'] = info_tmp['port']
        host_info['ps'] = info_tmp['ps']
        host_info['sort'] = info_tmp['sort']
        host_info['username'] = info_tmp['username']
        host_info['password'] = info_tmp['password']
        host_info['pkey'] = info_tmp['pkey']
        return host_info

    def modify_host(self,args):
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
            }
            @return dict
        '''
        args.new_host = args.new_host.strip()
        args.host = args.host.strip()
        if args.host != args.new_host:
            info_file = self._save_path + args.new_host +'/info.json'
            if os.path.exists(info_file):
                return public.returnMsg(False,'指定host地址已经在其它SSH信息中添加过了!')

        info_file = self._save_path + args.host +'/info.json'

        if not os.path.exists(info_file):
            return public.returnMsg(False,'指定SSH信息不存在!')
        
        if not 'sort' in args:
            r_data = public.aes_decrypt(public.readFile(info_file),self._pass_str)
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
        if not host_info['pkey']: host_info['pkey'] = ''
        result = self.set_attr(host_info)
        if not result['status']: return result
        self.save_ssh_info(args.host,host_info)
        if args.host != args.new_host:
            public.ExecShell('mv {} {}'.format(self._save_path + args.host,self._save_path + args.new_host))
        public.WriteLog(self._log_type,'修改HOST:{}的SSH信息'.format(args.host))
        return public.returnMsg(True,'修改成功')

    def create_host(self,args):
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
            }
            @return dict
        '''
        args.host = args.host.strip()
        host_path = self._save_path + args.host
        info_file = host_path +'/info.json'
        if os.path.exists(info_file):
            args.new_host = args.host
            return self.modify_host(args)
            #return public.returnMsg(False,'指定SSH信息已经添加过了!')
        if not os.path.exists(host_path):
            os.makedirs(host_path,384)
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
        result = self.set_attr(host_info)
        if not result['status']: return result
        self.save_ssh_info(args.host,host_info)
        public.WriteLog(self._log_type,'添加HOST:{} SSH信息'.format(args.host))
        return public.returnMsg(True,'添加成功')


    def remove_host(self,args):
        '''
            @name 删除指定SSH信息
            @author hwliang<2020-08-07>
            @param args<dict_obj>{
                host: 主机地址
            }
            @return dict
        '''
        args.host = args.host.strip()
        if not args.host: return public.returnMsg(False,'错误的参数')
        host_path = self._save_path + args.host
        if not os.path.exists(host_path):
            return public.returnMsg(False,'指定SSH信息不存在!')
        public.ExecShell("rm -rf {}".format(host_path))
        public.WriteLog(self._log_type,'删除HOST:{} SSH信息'.format(args.host))
        return public.returnMsg(True,'删除成功')


    def get_ssh_info(self,host):
        '''
            @name 获取并解密指定SSH信息
            @author hwliang<2020-08-07>
            @param  host<string> 主机地址
            @return dict or False
        '''
        info_file = self._save_path + host + '/info.json'
        if not os.path.exists(info_file): return False
        r_data = public.aes_decrypt(public.readFile(info_file),self._pass_str)
        return json.loads(r_data)

    def save_ssh_info(self,host,host_info):
        '''
            @name 获取并解密指定SSH信息
            @author hwliang<2020-08-07>
            @param  host<string> 主机地址
            @param  host_info<dict> ssh信息字典
            @return bool
        '''
        host_path = self._save_path + host
        if not os.path.exists(host_path):
            os.makedirs(host_path,384)
        info_file = host_path +'/info.json'
        r_data = public.aes_encrypt(json.dumps(host_info),self._pass_str)
        public.writeFile(info_file,r_data)
        return True

    def set_sort(self,args):
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
            return public.returnMsg(False,'请传入sort_list字段')
        sort_list = json.loads(args.sort_list)
        for name in sort_list.keys():
            info_file = self._save_path + name + '/info.json'
            if not os.path.exists(info_file): continue
            
            ssh_info = self.get_ssh_info(name)
            ssh_info['sort'] = int(sort_list[name])
            self.save_ssh_info(name,ssh_info)
        return public.returnMsg(True,'排序已保存')

    def get_command_list(self,args = None, user_cmd = False , sys_cmd = False):
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

    
    def command_exists(self,command,title):
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

    def save_command(self,command,sys_cmd=False):
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
        public.writeFile(s_file,json.dumps(command))

    def create_command(self,args):
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
        
        if self.command_exists(command,args.title):
            return public.returnMsg(False,'指定命令名称已存在')
        
        cmd = {
            "title": args.title,
            "shell": args.shell.strip()
        }

        command.append(cmd)
        self.save_command(command)
        public.WriteLog(self._log_type,'添加常用命令[{}]'.format(args.title))
        return public.returnMsg(True,'添加成功')

    def get_command_find(self,args = None, title=None):
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
            if cmd['title'] == title:
                return cmd
        return public.returnMsg(False,'指定命令不存在')

    def modify_command(self,args):
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
        args.title = args.title.strip()
        command = self.get_command_list(sys_cmd=True)
        if not self.command_exists(command,args.title):
            return public.returnMsg(False,'指定命令不存在')
        for i in range(len(command)):
            if command[i]['title'] == args.title:
                command[i]['title'] = args.new_title
                command[i]['shell'] = args.shell.strip()
                break
        self.save_command(command)
        public.WriteLog(self._log_type,'修改常用命令[{}]'.format(args.title))
        return public.returnMsg(True,'修改成功')

    def remove_command(self,args):
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
        if not self.command_exists(command,args.title):
            return public.returnMsg(False,'指定命令不存在')
        for i in range(len(command)):
            if command[i]['title'] == args.title:
                del(command[i])
                break

        self.save_command(command)
        public.WriteLog(self._log_type,'删除常用命令[{}]'.format(args.title))
        return public.returnMsg(True,'删除成功')


