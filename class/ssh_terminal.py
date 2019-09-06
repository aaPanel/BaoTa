#coding:utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: 黄文良 <287962566@qq.com>
# +-------------------------------------------------------------------

import sys,os,public,time,json,pwd,cgi,threading,socket
from BTPanel import session,request,emit
import paramiko

class Terminal:
    trans = None
    ssh = None
    shell = None
    def __init__(self):
        pass
        #self.ssh = paramiko.SSHClient()
        #self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    def connect(self,host,port,user,pwd,cert = None):

        if cert:
            key=paramiko.RSAKey.from_private_key_file(pkey)
            self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.ssh.connect(host, port,username=user,pkey=key)
        else:
            self.ssh = paramiko.Transport((host, port))
            self.ssh.start_client()
            self.ssh.auth_password(username=user,password=pwd)
        
        self.shell = self.ssh.open_session()
        self.shell.get_pty()
        self.shell.invoke_shell()

        #self.shell.setblocking(0)
        self.shell.settimeout(0)
        self.shell_recv()

    def shell_send(self,msg):
        self.shell.send(msg)

    def shell_recv(self):
        time.sleep(1)
        while True:
            recv = self.shell.recv(1024)
            print(recv)
            emit('server_response',{'data':recv.decode("utf-8")})

    def create_rsa(self):
        id_ras = '/root/.ssh/id_rsa_bt'
        a_keys = '/root/.ssh/authorized_keys'
        if not os.path.exists(a_keys) or not os.path.exists(id_ras):
            public.ExecShell("rm -f /root/.ssh/id_rsa_bt*")
            public.ExecShell('ssh-keygen -q -t rsa -P "" -f /root/.ssh/id_rsa_bt')
            public.ExecShell('cat /root/.ssh/id_rsa_bt.pub >> /root/.ssh/authorized_keys')
        else:
            id_ras_pub = '/root/.ssh/id_rsa_bt.pub'
            if os.path.exists(id_ras_pub):
                pub_body = public.readFile(id_ras_pub)
                keys_body = public.readFile(a_keys)
                if keys_body.find(pub_body) == -1:
                    public.ExecShell('cat /root/.ssh/id_rsa_bt.pub >> /root/.ssh/authorized_keys')
        public.ExecShell('chmod 600 /root/.ssh/authorized_keys')





