# coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板 x3
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2017 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: lkqiang<lkq@bt.cn>
# +-------------------------------------------------------------------
# +--------------------------------------------------------------------
# |   宝塔内置消息通道
# +--------------------------------------------------------------------
import os, sys, public, base64, json, re
import smtplib, requests
# import http_requests as requests
from email.mime.text import MIMEText
from email.utils import formataddr

class send_mail:
    __mail_config = '/www/server/panel/data/stmp_mail.json'
    __mail_list_data = '/www/server/panel/data/mail_list.json'
    __qq_mail_user = None
    # 钉钉机器人
    __dingding_config = '/www/server/panel/data/dingding.json'
    __dingding_info = None
    # 微信企业号
    __weixin_config = '/www/server/panel/data/weixin.json'
    __weixin_info = None

    def __init__(self):
        # QQ邮箱基础实例化
        if not os.path.exists(self.__mail_list_data):
            ret = []
            public.writeFile(self.__mail_list_data, json.dumps(ret))
        else:
            try:
                mail_data = json.loads(public.ReadFile(self.__mail_list_data))
                self.__mail_list = mail_data
            except:
                ret = []
                public.writeFile(self.__mail_list_data, json.dumps(ret))

        if not os.path.exists(self.__mail_config):
            ret = []
            public.writeFile(self.__mail_config, json.dumps(ret))
        else:
            try:
                qq_mail_info = json.loads(public.ReadFile(self.__mail_config))
                if 'qq_mail' in qq_mail_info and 'qq_stmp_pwd' in qq_mail_info and 'hosts' in qq_mail_info:
                    self.__qq_mail_user = qq_mail_info
            except:
                ret = []
                public.writeFile(self.__mail_config, json.dumps(ret))

        # 初始化钉钉
        if not os.path.exists(self.__dingding_config):
            ret = []
            public.writeFile(self.__dingding_config, json.dumps(ret))
        else:
            try:
                dingding_info = json.loads(public.ReadFile(self.__dingding_config))
                if 'dingding_url' in dingding_info and 'isAtAll' in dingding_info and 'user' in dingding_info:
                    self.__dingding_info = dingding_info
            except:
                ret = []
                public.writeFile(self.__dingding_config, json.dumps(ret))

        # 初始化微信
        if not os.path.exists(self.__weixin_config):
            ret = []
            public.writeFile(self.__weixin_config, json.dumps(ret))
        else:
            try:
                weixin_info = json.loads(public.ReadFile(self.__weixin_config))
                if 'corpid' in weixin_info and 'corpsecret' in weixin_info and 'user_id' in weixin_info and 'agentid' in weixin_info:
                    self.__weixin_info = weixin_info
            except:
                ret = []
                public.writeFile(self.__weixin_config, json.dumps(ret))

    # 查看自定义邮箱配置
    def get_user_mail(self):
        qq_mail_info = json.loads(public.ReadFile(self.__mail_config))
        if len(qq_mail_info) == 0:
            return False
        return qq_mail_info

    # 查看钉钉
    def get_dingding(self):
        qq_mail_info = json.loads(public.ReadFile(self.__dingding_config))
        if len(qq_mail_info) == 0:
            return False
        return qq_mail_info

    # 查看能使用的告警通道
    def get_settings(self):
        qq_mail_info = json.loads(public.ReadFile(self.__mail_config))
        if len(qq_mail_info) == 0:
            user_mail = False
        else:
            user_mail = True
        dingding_info = json.loads(public.ReadFile(self.__dingding_config))
        if len(dingding_info) == 0:
            dingding = False
        else:
            dingding = True
        ret = {}
        ret['user_mail'] = {"user_name": user_mail, "mail_list": self.__mail_list, "info": self.get_user_mail()}
        ret['dingding'] = {"dingding": dingding, "info": self.get_dingding()}
        return ret


    # QQ邮箱保存账户信息
    def qq_stmp_insert(self, email, stmp_pwd, hosts, port):

        qq_stmp_info = {"qq_mail": email.strip(), "qq_stmp_pwd": stmp_pwd.strip(), "hosts": hosts.strip(), "port": port}
        self.__qq_mail_user = qq_stmp_info
        public.writeFile(self.__mail_config, json.dumps(qq_stmp_info))
        return True

    # qq发送测试
    def qq_smtp_send(self, email, title, body):
        if 'qq_mail' not in self.__qq_mail_user or 'qq_stmp_pwd' not in self.__qq_mail_user or 'hosts' not in self.__qq_mail_user: return -1
        ret = True
        if not 'port' in self.__qq_mail_user: self.__qq_mail_user['port'] = 465
        try:

            msg = MIMEText(body, 'html', 'utf-8')
            msg['From'] = formataddr([self.__qq_mail_user['qq_mail'], self.__qq_mail_user['qq_mail']])
            msg['To'] = formataddr([self.__qq_mail_user['qq_mail'], email.strip()])
            msg['Subject'] = title
            if int(self.__qq_mail_user['port']) == 465:
                server = smtplib.SMTP_SSL(str(self.__qq_mail_user['hosts']), str(self.__qq_mail_user['port']))
            else:
                server = smtplib.SMTP(str(self.__qq_mail_user['hosts']), str(self.__qq_mail_user['port']))
            server.login(self.__qq_mail_user['qq_mail'], self.__qq_mail_user['qq_stmp_pwd'])
            server.sendmail(self.__qq_mail_user['qq_mail'], [email.strip(), ], msg.as_string())
            server.quit()
        except Exception:
            ret = False
        return ret

    def GetAccessKey(self):
        ufile = "/www/server/panel/data/userInfo.json"
        uconf = public.readFile(ufile)
        if uconf:
            uconf = json.loads(uconf)
            ak = uconf["access_key"]
        else:
            return False
        return ak

    def SetToken(self, email_data):
        ufile = "/www/server/panel/data/userInfo.json"
        uconf = public.readFile(ufile)
        if uconf:
            uconf = json.loads(uconf)
            sk = uconf["secret_key"]
        else:
            return False
        token = public.Md5(sk + email_data)
        return token

    def GetLocalIp(self):
        # 取本地外网IP
        try:
            filename = '/www/server/panel/data/iplist.txt'
            ipaddress = public.readFile(filename)
            if not ipaddress:
                import urllib2
                url = 'http://pv.sohu.com/cityjson?ie=utf-8'
                opener = urllib2.urlopen(url)
                m_str = opener.read()
                ipaddress = re.search('\d+.\d+.\d+.\d+', m_str).group(0)
                public.WriteFile(filename, ipaddress)
            c_ip = public.check_ip(ipaddress)
            if not c_ip:
                a, e = public.ExecShell("curl ifconfig.me")
                return a
            return ipaddress
        except:
            try:
                url = public.GetConfigValue('home') + '/Api/getIpAddress'
                return public.HttpGet(url)
            except:
                return public.GetHost()

    # 钉钉保存账户
    def dingding_insert(self, url, atall, user='1'):
        qq_stmp_info = {"dingding_url": url.strip(), "isAtAll": str(atall).strip(), "user": str(user).strip()}
        self.__dingding_info = qq_stmp_info
        public.writeFile(self.__dingding_config, json.dumps(qq_stmp_info))
        return True

    # 钉钉机器人
    def dingding_send(self, content):
        if 'dingding_url' not in self.__dingding_info or 'isAtAll' not in self.__dingding_info or 'user' not in self.__dingding_info: return -1
        data = {
            "msgtype": "text",
            "text": {
                "content": content
            },
            "at": {
                "atMobiles": [
                    self.__dingding_info['user']
                ],
                "isAtAll": self.__dingding_info['isAtAll']
            }
        }
        headers = {'Content-Type': 'application/json'}
        try:
            x = requests.post(url=self.__dingding_info['dingding_url'], data=json.dumps(data), headers=headers,
                              verify=False)
            if x.json()["errcode"] == 0:
                print('发送成功')
                return True

            else:
                print('发送失败')
                return False
        except:
            print('发送失败')
            return False

    # 添加微信用户user_id
    def add_weixin_user(self, uid):
        if 'corpid' not in self.__weixin_info or 'corpsecret' not in self.__weixin_info or 'user_id' not in self.__weixin_info or 'agentid' not in self.__weixin_info: return False
        if uid in self.__weixin_info['user_id']: return False
        self.__weixin_info['user_id'].append(uid)
        public.writeFile(self.__weixin_config, json.dumps(self.__weixin_info))
        return True

    # 微信保存账户
    def weixin_insert(self, corpid, corpsecret, user_id, agentid):
        user_list = []
        user_list.append(user_id)
        user_weixin_info = {"corpid": corpid.strip(), "corpsecret": corpsecret.strip(), "user_id": user_list,
                            "agentid": agentid}
        self.__weixin_info = user_weixin_info
        public.writeFile(self.__weixin_config, json.dumps(user_weixin_info))
        return True

    def get_token(self):
        url = 'https://qyapi.weixin.qq.com/cgi-bin/gettoken'
        values = {'corpid': self.__weixin_info['corpid'],
                  'corpsecret': self.__weixin_info['corpsecret'],
                  }
        try:
            req = requests.post(url, params=values)
            data = json.loads(req.text)
            return data["access_token"]
        except:
            return False

    # 返回微信user
    def return_weixin_user(self):
        if 'corpid' not in self.__weixin_info or 'corpsecret' not in self.__weixin_info or 'user_id' not in self.__weixin_info or 'agentid' not in self.__weixin_info: return 1
        count = len(self.__weixin_info['user_id'])
        new_count = 1
        nrw_data = ''
        for i in self.__weixin_info['user_id']:
            if new_count == 1:
                nrw_data += str(i)
            else:
                nrw_data += '|' + str(i)
            new_count += 1
        return nrw_data

    def send_msg(self, content):
        if 'corpid' not in self.__weixin_info or 'corpsecret' not in self.__weixin_info or 'user_id' not in self.__weixin_info or 'agentid' not in self.__weixin_info: return -1
        if not self.get_token(): return 0
        url = "https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token=" + self.get_token()
        data = {"touser": self.return_weixin_user(),
                "toparty": "1",
                "msgtype": "text",
                "agentid": self.__weixin_info['agentid'],
                "text": {
                    "content": content
                },
                "safe": "0"
                }
        try:
            req = requests.post(url, json.dumps(data))
            data = json.loads(req.text)
            if data['errmsg'] == 'ok':
                return 4
            else:
                return 3
        except:
            return 3
