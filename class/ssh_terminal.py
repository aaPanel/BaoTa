#coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板 
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: hwliang <hwl@bt.cn>
# +-------------------------------------------------------------------
try:
    import paramiko
except: pass
import json
import time
import os
import sys
import socket
import threading

sys.path.insert(0, '/www/server/panel/class/')
import public
from io import BytesIO, StringIO




class ssh_terminal:
    __log_type = '宝塔终端'
    _coll_user = None
    _host = None
    _web_socket = None
    _ssh_info = None
    _ssh_socket = None
    _en_key = '4BbA7076e19H'
    _thread = None
    _my_terms = {}
    _room = "ssh_data"
    _send_last = False
    _send_last_time = 0
    _connect_time = 0

    def __init__(self):
        pass


    def connect(self, ssh_info=None):
        if ssh_info: self._ssh_info = ssh_info
        if not self._host: self._host = self._ssh_info['host']
        # print('----------连接时的ssh_info--------------')
        if self._ssh_info['host'] in self._my_terms:
            if time.time() - self._my_terms[self._host].last_time < 86400:
                return True
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 262144)
            sock.connect((self._ssh_info['host'], int(self._ssh_info['port'])))
        except Exception as e:
            self._web_socket.send("\r服务器连接失败!\r")
            return False
        # 使用Transport连接
        p1 = paramiko.Transport(sock)
        p1.start_client()
        if not 'pkey' in self._ssh_info: self._ssh_info['pkey'] = None
        if not 'c_type' in self._ssh_info: self._ssh_info['c_type'] = None
        try:
            # 如果有pkey时则使用RSA私钥登录
            if self._ssh_info['pkey'] and self._ssh_info['c_type']:
                # print('------使用私钥登陆---------')
                # 将RSA私钥转换为io对象，然后生成rsa_key对象
                p_file = StringIO(self._ssh_info['pkey'])
                pkey = paramiko.RSAKey.from_private_key(p_file)
                p1.auth_publickey(username=self._ssh_info['username'].strip(), key=pkey)
            else:
                # print('-----------使用密码登陆-----------')
                p1.auth_password(username=self._ssh_info['username'].strip(), password=self._ssh_info['password'])
        except Exception as e:
            self._web_socket.send("\r用户名或密码错误!\r")
            p1.close()
            return False

        self._my_terms[self._host] = public.dict_obj()
        self._my_terms[self._host].last_time = time.time()
        self._my_terms[self._host].connect_time = time.time()
        # 打开会话
        self._my_terms[self._host].tty = p1.open_session()
        # 获取终端对象
        self._my_terms[self._host].tty.get_pty(term='xterm', width=100, height=34)
        self._my_terms[self._host].tty.invoke_shell()
        # 记录登陆记录
        #public.M('ssh_records').add('coll_user,ssh_user,host,cmd,addtime', (self._coll_user, self._ssh_info['username'], self._ssh_info['host'], 'login', int(time.time())))
        #print("登录成功")
        self._my_terms[self._host].last_send = []
        self._send_last = True
        self._connect_time = time.time()
        return True

    def resize(self, data):
        try:
            data = json.loads(data)
            self._my_terms[self._host].tty.resize_pty(width=data['width'], height=data['height'], width_pixels=data['width_px'], height_pixels=data['height_px'])
            return True
        except:
            print(public.get_error_info())
            return False

    def send(self):
        try:
            while not self._web_socket.closed:
                c_data = self._web_socket.receive()
                if not c_data: continue
                if len(c_data) > 10:
                    if c_data.find('new_terminal') != -1:
                        if not self._host in self._my_terms: 
                            self.connect()
                        else:
                            if time.time() - self._connect_time > 3:
                                self.last_send()
                        continue
                    if c_data.find("reset_connect") != -1:
                        if not self._host in self._my_terms: self.connect()
                        continue

                if self._host in self._my_terms:
                    self._my_terms[self._host].last_time = time.time()
                    self._my_terms[self._host].tty.send(c_data)
                else:
                    return
        except:
            print(public.get_error_info())

    def recv(self):
        try:
            n = 0
            while not self._web_socket.closed:
                self.not_send()
                #if n == 0: self.last_send()
                data = self._my_terms[self._host].tty.recv(1024)
                self.not_send()
                if not data:
                    self.close()
                    self._web_socket.send('连接已断开,连续按两次回车将尝试重新连接!')
                    return
                try:
                    result = data.decode()
                except:
                    result = str(data)
                if not result: continue
                if self._web_socket.closed:
                    self._my_terms[self._host].not_send = result
                    return
                self.set_last_send(result)
                if not n: n = 1
                self._web_socket.send(result)
        except:
            print(public.get_error_info())

    def set_last_send(self,result):
        last_size = 1024
        if not 'last_send' in self._my_terms[self._host]: 
            self._my_terms[self._host].last_send = []

        self._my_terms[self._host].last_send.append(result)
        last_len = len(self._my_terms[self._host].last_send)
        if last_len > last_size:
            self._my_terms[self._host].last_send = self._my_terms[self._host].last_send[last_len-last_size:]

    def not_send(self):
        if 'not_send' in self._my_terms[self._host]:
            if self._my_terms[self._host].not_send:
                self._web_socket.send(self._my_terms[self._host].not_send)
                self._my_terms[self._host].not_send = ""

    def last_send(self):
        if time.time()- self._send_last_time < 3: return False
        self._send_last_time = time.time()
        time.sleep(0.3)
        if not self._host in self._my_terms: return False
        if 'last_send' in self._my_terms[self._host]:
            for d in self._my_terms[self._host].last_send:
                self._web_socket.send(d)

    def close(self):
        try:
            self._my_terms[self._host].tty.close()
        except:pass
        if self._host in self._my_terms:
            del self._my_terms[self._host] 
        self._thread = None

    def run(self,web_socket, ssh_info=None):
        self._web_socket = web_socket
        if 'id' in ssh_info:
            self._ssh_info = self.get_server_ssh_info(ssh_info)
        else:
            self._ssh_info = ssh_info
        if not self._ssh_info:
            return
        result = self.connect()
        time.sleep(0.1)
        if result:
            sendt = threading.Thread(target=self.send)
            recvt = threading.Thread(target=self.recv)
            sendt.start()
            recvt.start()
            sendt.join()
            recvt.join()
            if time.time() - self._my_terms[self._host].last_time > 86400: self.close()
            self._web_socket = None
