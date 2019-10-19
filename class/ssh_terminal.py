#coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板 
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: 黄文良 <287962566@qq.com>
# +-------------------------------------------------------------------

import paramiko
import json
import time
import os
import sys
import socket

sys.path.insert(0, '/www/server/panel/class/')
import public
from io import BytesIO, StringIO
from BTPanel import session,socketio

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
            socketio.emit(self._room,"\r服务器连接失败!\r")
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
            socketio.emit(self._room,"\r用户名或密码错误!\r")
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
        return True

    def resize(self, data):
        try:
            data = json.loads(data)
            self._my_terms[self._host].tty.resize_pty(width=data['width'], height=data['height'], width_pixels=data['width_px'], height_pixels=data['height_px'])
            return True
        except:
            print(public.get_error_info())
            return False

    def send(self,c_data):
        try:
            if not c_data: return
            if not self._thread:
                s_file = '/www/server/panel/config/t_info.json'
                ssh_info = None
                if os.path.exists(s_file):
                    ssh_info = json.loads(public.en_hexb(public.readFile(s_file)))

                if not 'host' in c_data: 
                    host = "127.0.0.1"
                    if ssh_info: 
                        c_data = ssh_info
                        host = c_data['host']
                else:
                    host = c_data['host']
                if not host: 
                    if not ssh_info: return socketio.emit(self._room,"\r用户名或密码错误!\r")
                    c_data = ssh_info
                key = 'ssh_' + host
                if 'password' in c_data:
                    session[key] = c_data
                if not key in session: return socketio.emit(self._room,"\r用户名或密码错误!\r")
                result = self.run(session[key])
            else:
                if len(c_data) > 10:
                    if c_data == 'new_bt_terminal': 
                        if not self._send_last: self.last_send()
                        self._send_last = False
                        return
                    if c_data.find('resize_pty') != -1:
                        if self.resize(c_data): return
                if type(c_data) == dict: return
                if self._host in self._my_terms:
                    self._my_terms[self._host].last_time = time.time()
                    self._my_terms[self._host].tty.send(c_data)
                else:
                    return
        except:
            self.close()
            socketio.emit(self._room,'\r连接服务器失败!\r')
            print(public.get_error_info())

    def recv(self):
        try:
            while True:
                data = self._my_terms[self._host].tty.recv(1024)
                if not data:
                    self.close()
                    socketio.emit(self._room,"\r连接已断开,按回车将尝试重新连接!\r")
                    return
                try:
                    result = data.decode()
                except:
                    result = str(data)
                if not result: continue
                self.set_last_send(result)
                socketio.emit(self._room,result)
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
                socketio.emit(self._room,self._my_terms[self._host].not_send)
                self._my_terms[self._host].not_send = ""

    def last_send(self):
        time.sleep(0.3)
        if 'last_send' in self._my_terms[self._host]:
            for d in self._my_terms[self._host].last_send:
                socketio.emit(self._room,d)

    def close(self):
        try:
            self._my_terms[self._host].tty.close()
        except:pass
        if self._host in self._my_terms:
            del self._my_terms[self._host] 
        self._thread = None

    def run(self, ssh_info=None):
        if not ssh_info:
            return
        if 'id' in ssh_info:
            self._ssh_info = self.get_server_ssh_info(ssh_info)
        else:
            self._ssh_info = ssh_info
        result = self.connect()
        if result and not self._thread:
            self._thread = socketio.start_background_task(target=self.recv)
        return result
