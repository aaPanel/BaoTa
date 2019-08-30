#coding:utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: 黄文良 <287962566@qq.com>
# +-------------------------------------------------------------------

import sys,os,public,time,json,pwd,cgi,threading,socket
from BTPanel import session,request
import paramiko

class Terminal(paramiko.ServerInterface):
    trans = None
    ssh = None
    shell = None
    def __init__(self):
        self.event = threading.Event()

    def check_auth_password(self, username, password):
        return paramiko.AUTH_FAILED

    def check_channel_request(self, kind, chanid):
        if kind == 'session':
            return paramiko.OPEN_SUCCEEDED





bhSession = paramiko.Transport()
server = Terminal()
bhSession.start_server(server=server)