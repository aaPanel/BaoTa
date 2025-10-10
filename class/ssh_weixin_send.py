#!/usr/bin/python
# -*- coding: utf-8 -*-
import pwd
import json
import string
import random
import hashlib
import datetime
import platform
import httplib
import os,sys,time

def auth_log(msg):
    """写入日志"""
    f=open('/tmp/1.json','a+')
    f.write(json.dumps(msg)+"\n")
    f.close()

def ReadFile(filename,mode = 'r'):
    import os
    if not os.path.exists(filename): return False
    try:
        fp = open(filename, mode)
        f_body = fp.read()
        fp.close()
    except Exception as ex:
        if sys.version_info[0] != 2:
            try:
                fp = open(filename, mode,encoding="utf-8")
                f_body = fp.read()
                fp.close()
            except:
                fp = open(filename, mode,encoding="GBK")
                f_body = fp.read()
                fp.close()
        else:
            return False
    return f_body

#获取服务器IP
def get_ip():
    if os.path.exists('/www/server/panel/data/iplist.txt'):
        data=ReadFile('/www/server/panel/data/iplist.txt')
        if data:
            return data.strip()
        else:
            return 'None'
    else:
        return 'None'

def dingding_send(config_url,url, content):
    host=url.replace('https://','').replace('http://','').split('/')[0]
    send_url=url.replace('https://','').replace('http://','').replace(host,'')
    if 'weixin.qq.com' in host:
        data = {"msgtype": "markdown","markdown": {"content": content}}
    elif 'dingtalk.com' in host:
        if config_url['isAtAll']:
            data = {"msgtype": "markdown","markdown": {"title": "SSH二次认证","text": content},"at": {"atMobiles": ["1"],"isAtAll":True}}
        else:
            data = {"msgtype": "markdown","markdown": {"title": "SSH二次认证","text": content},"at": {"atMobiles": ["1"],"isAtAll":False}}
    else:
        return False
    headers = {'Content-Type': 'application/json'}
    try:
        httpClient = httplib.HTTPSConnection(host, timeout=10)
        httpClient.request("POST", send_url, json.dumps(data), headers=headers)
        response = httpClient.getresponse()
        result = json.loads(response.read())
        if result["errcode"] == 0:
            return True
        else:
            return False
    except:
        cmd='/usr/local/curl/bin/curl  -H "Content-Type:application/json"  -X POST --data \'%s\' %s'%(json.dumps(data),url)
        try:
            data=json.loads(os.popen(cmd).read())
            if data["errcode"] == 0:
                return True
        except:
            return False
        return False

def action_wechat(config_url,url,content):
    """微信通知"""
    return dingding_send(config_url,url, content)

def get_user_comment(user):
    try:
        comments = pwd.getpwnam(user).pw_gecos
    except:
        comments = ''
    return comments

def get_hash(plain_text):
    key_hash = hashlib.sha512()
    key_hash.update(plain_text)
    return key_hash.digest()

def gen_key(config_url,url,pamh, user, length):
    pin = ''.join(random.choice(string.digits) for i in range(length))
    hostname = platform.node().split('.')[0]
    content = "####SSH动态密码 \n\n >客户端IP: %s\n\n >登录的账户: %s\n\n >服务器外网IP: %s \n\n >主机名:%s \n\n>验证码:【%s】\n\n >发送时间: %s\n\n >有效期: 2分钟" % (pamh.rhost, user,get_ip(),hostname, pin,time.strftime('%Y-%m-%d %X', time.localtime()))
    is_send=action_wechat(config_url,url,content)
    pin_time = datetime.datetime.now()
    return get_hash(pin), pin_time,is_send

#检查配置文件是否存在
def is_config():
    if not os.path.exists('/www/server/panel/data/dingding.json'):
        return False
    else:return True

def pam_sm_authenticate(pamh, flags, argv):
    if not os.path.exists('/www/server/panel/data/dingding.json'):return pamh.PAM_SUCCESS
    try:
        config=ReadFile('/www/server/panel/data/dingding.json')
        config_url=json.loads(config)
        url=config_url['dingding_url']
    except:
        return pamh.PAM_SUCCESS
    PIN_LENGTH = 6
    PIN_LIVE = 120
    PIN_LIMIT = 3
    try:
        user = pamh.get_user()
    except pamh.exception as e:
        return e.pam_result
    pin, pin_time,is_send = gen_key(config_url,url,pamh, user, PIN_LENGTH)
    if not is_send:
        msg = pamh.Message(pamh.PAM_ERROR_MSG, "[Warning] Failed to send verification code, please check the configuration file")
        pamh.conversation(msg)
        return pamh.PAM_SUCCESS
    for attempt in range(0, PIN_LIMIT):
        msg = pamh.Message(pamh.PAM_PROMPT_ECHO_OFF, "Verification code:")
        resp = pamh.conversation(msg)
        resp_time = datetime.datetime.now()
        input_interval = resp_time - pin_time
        if input_interval.seconds > PIN_LIVE:
            msg = pamh.Message(pamh.PAM_ERROR_MSG, "[Warning] Time limit exceeded.")
            pamh.conversation(msg)
            return pamh.PAM_ABORT
        resp_hash = get_hash(resp.resp)
        if resp_hash == pin:
            return pamh.PAM_SUCCESS
        else:
            continue
    msg = pamh.Message(pamh.PAM_ERROR_MSG, "[Warning] Too many authentication failures.")
    pamh.conversation(msg)
    return pamh.PAM_AUTH_ERR

def pam_sm_setcred(pamh, flags, argv):
    return pamh.PAM_SUCCESS

def pam_sm_acct_mgmt(pamh, flags, argv):
    return pamh.PAM_SUCCESS

def pam_sm_open_session(pamh, flags, argv):
    return pamh.PAM_SUCCESS

def pam_sm_close_session(pamh, flags, argv):
    return pamh.PAM_SUCCESS

def pam_sm_chauthtok(pamh, flags, argv):
    return pamh.PAM_SUCCESS