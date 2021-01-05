# coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板 x6
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2017 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: lkqiang<lkq@bt.cn>
# +-------------------------------------------------------------------
# +--------------------------------------------------------------------
# |   宝塔webshell 内置扫描
# +--------------------------------------------------------------------
import public, hashlib, os, sys, json, time, re
import send_mail,requests

class webshell_check:
    __PATH = '/www/server/panel/data/'
    __mail_config = '/www/server/panel/data/stmp_mail.json'
    __mail_list_data = '/www/server/panel/data/mail_list.json'
    __dingding_config = '/www/server/panel/data/dingding.json'
    __mail_list = []
    __weixin_user = []
    __rule = ["@\\$\\_\\(\\$\\_", "\\$\\_=\"\"", "\\${'\\_'",
              "@preg\\_replace\\((\")*\\/(\\S)*\\/e(\")*,\\$_POST\\[\\S*\\]", "base64\\_decode\\(\\$\\_",
              "'e'\\.'v'\\.'a'\\.'l'", "\"e\"\\.\"v\"\\.\"a\"\\.\"l\"", "\"e\"\\.\"v\"\\.\"a\"\\.\"l\"",
              "\\$(\\w)+\\(\"\\/(\\S)+\\/e", "\\(array\\)\\$_(POST|GET|REQUEST|COOKIE)", "\\$(\\w)+\\(\\${",
              "@\\$\\_=", "\\$\\_=\\$\\_", "chr\\((\\d)+\\)\\.chr\\((\\d)+\\)", "phpjm\\.net", "cha88\\.cn",
              "c99shell", "phpspy", "Scanners", "cmd\\.php", "str_rot13", "webshell", "EgY_SpIdEr",
              "tools88\\.com", "SECFORCE", "eval\\(('|\")\\?>", "preg_replace\\(\"\\/\\.\\*\\/e\"",
              "assert\\(('|\"|\\s*)\\$", "eval\\(gzinflate\\(", "gzinflate\\(base64_decode\\(",
              "eval\\(base64_decode\\(", "eval\\(gzuncompress\\(", "ies\",gzuncompress\\(\\$",
              "eval\\(gzdecode\\(", "eval\\(str_rot13\\(", "gzuncompress\\(base64_decode\\(",
              "base64_decode\\(gzuncompress\\(", "eval\\(('|\"|\\s*)\\$_(POST|GET|REQUEST|COOKIE)",
              "assert\\(('|\"|\\s*)\\$_(POST|GET|REQUEST|COOKIE)",
              "require\\(('|\"|\\s*)\\$_(POST|GET|REQUEST|COOKIE)",
              "require_once\\(('|\"|\\s*)\\$_(POST|GET|REQUEST|COOKIE)",
              "include\\(('|\"|\\s*)\\$_(POST|GET|REQUEST|COOKIE)",
              "include_once\\(('|\"|\\s*)\\$_(POST|GET|REQUEST|COOKIE)", "call_user_func\\((\"|')assert(\"|')",
              "call_user_func\\(('|\"|\\s*)\\$_(POST|GET|REQUEST|COOKIE)",
              "\\$_(POST|GET|REQUEST|COOKIE)\\[([^\\]]+)\\]\\(('|\"|\\s*)\\$_(POST|GET|REQUEST|COOKIE)\\[",
              "echo\\(file_get_contents\\(('|\"|\\s*)\\$_(POST|GET|REQUEST|COOKIE)",
              "file_put_contents\\(('|\"|\\s*)\\$_(POST|GET|REQUEST|COOKIE)\\[([^\\]]+)\\],('|\"|\\s*)\\$_(POST|GET|REQUEST|COOKIE)",
              "fputs\\(fopen\\((.+),('|\")w('|\")\\),('|\"|\\s*)\\$_(POST|GET|REQUEST|COOKIE)\\[",
              "SetHandlerapplication\\/x-httpd-php", "php_valueauto_prepend_file", "php_valueauto_append_file"]

    def __init__(self):
        self.mail = send_mail.send_mail()

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



    def ReadFile(self,filename, mode='r'):
        import os
        if not os.path.exists(filename): return False
        try:
            fp = open(filename, mode)
            f_body = fp.read()
            fp.close()
        except Exception as ex:
            if sys.version_info[0] != 2:
                try:
                    fp = open(filename, mode, encoding="utf-8")
                    f_body = fp.read()
                    fp.close()
                except Exception as ex2:
                    return False
            else:
                return False
        return f_body


    # 返回配置邮件地址
    def return_mail_list(self):
        return self.__mail_list

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

    # 返回站点
    def return_site(self):
        data = public.M('sites').field('name,path').select()
        ret = {}
        for i in data:
            ret[i['name']] = i['path']
        return public.returnMsg(True, ret)

    # 获取规则
    def get_rule(self):
        return  self.__rule
        

    def get_dir(self, path):
        return_data = []
        data2 = []
        [[return_data.append(os.path.join(root, file)) for file in files] for root, dirs, files in os.walk(path)]
        for i in return_data:
            if str(i.lower())[-4:] == '.php':
                data2.append(i)
        return data2

    # 目录
    def getdir_list(self, path_data):
        if os.path.exists(str(path_data)):
            return self.get_dir(path_data)
        else:
            return False

    # 扫描
    def scan(self, filelist, rule):
        import time
        time_data = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        ret = []
        data2 = []
        for file in filelist:
            try:
                data = self.ReadFile(file)
                for r in rule:
                    if re.compile(r).findall(str(data)):
                        result = {}
                        result[file] = r
                        ret.append(result)
                        data = ("%s [!] %s %s  \n" % (time_data, file, r))
                        data2.append(file)
            except:print('%s文件打开失败！！跳过中'%file)
        return data2

    #get_url
    def get_check_url(self):
        try:
            ret=requests.get('http://www.bt.cn/checkWebShell.php').json()
            if ret['status']:
                return ret['url']
            return False
        except:
            return False

    # 上传webshell
    def upload_shell(self, data):
        if len(data) == 0: return []
        return_data = []
        url=self.get_check_url()
        if not url: return []
        for i in data:
            if self.upload_file_url2(i,url):
                return_data.append(i)
        return return_data

    def san_dir(self, path, send='mail'):
        file = self.getdir_list(path)
        if not file:
            return []
        rule = self.get_rule()
        if not rule:
            return []
        result = self.scan(file, rule)
        return_data = self.upload_shell(result)
        tongdao = self.get_settings()
        if len(return_data) >= 1:
            if send == 'dingding':
                if tongdao['dingding']:
                    msg = "webshell查杀发现%s目录中存在木马如下:%s" % (path, return_data)
                    self.mail.dingding_send(msg)
            elif send == 'mail':
                if tongdao['user_mail']:

                    title = "webshell查杀发现%s目录中存在木马如下" % (path)
                    body = "webshell查杀发现%s目录中存在木马如下:%s" % (path, return_data)
                    if len(self.__mail_list) == 0:
                        if tongdao['user_mail']['user_name']:
                            self.mail.qq_smtp_send(str(tongdao['user_mail']['info']['qq_mail']), title=title, body=body)
                    else:
                        for i in self.__mail_list:
                            if tongdao['user_mail']['user_name']:
                                self.mail.qq_smtp_send(str(i), title=title, body=body)
        return return_data

    def send_san_dir(self, path, send):
        file = self.getdir_list(path)
        if not file:return []
        rule = self.get_rule()
        if not rule:return []
        result = self.scan(file, rule)
        return_data = self.upload_shell(result)
        tongdao = self.get_settings()
        if len(return_data) >= 1:
            if send == 'dingding':
                if tongdao['dingding']:
                    msg = "webshell查杀发现%s目录中存在木马如下:%s" % (path, return_data)
                    self.mail.dingding_send(msg)
            elif send == 'mail':
                if tongdao['user_mail']:
                    title = "webshell查杀发现%s目录中存在木马如下" % (path)
                    body = "webshell查杀发现%s目录中存在木马如下:%s" % (path, return_data)
                    if len(self.__mail_list) == 0:
                        self.mail.qq_smtp_send(str(tongdao['user_mail']['info']['qq_mail']), title=title, body=body)
                    else:
                        for i in self.__mail_list:
                            self.mail.qq_smtp_send(str(i), title=title, body=body)
        return return_data

    def webshellchop(self,filename,url):
        try:
            upload_url =url
            size = os.path.getsize(filename)
            if size > 1024000: return False
            upload_data = {'inputfile': self.ReadFile(filename)}
            upload_res = requests.post(upload_url, upload_data, timeout=20).json()
            if upload_res['msg']=='ok':
                if (upload_res['data']['data']['level']==5):
                    print('%s文件为木马  hash:%s' % (filename,upload_res['data']['data']['hash']))
                    self.send_baota2(filename)
                    return True
                elif upload_res['data']['level'] >= 3:
                    print('%s可疑文件,建议手工检查' % filename)
                    self.send_baota2(filename)
                    return False
                return False
        except:
            return False


    def upload_file_url(self, filename):
        try:
            url = self.get_check_url()
            if not url: return []
            if os.path.exists(filename):
                if  self.webshellchop(filename,url):return True
                return False
            else:
                return False
        except:
            return False

    def upload_file_url2(self, filename,url):
        try:
            if os.path.exists(filename):
                if  self.webshellchop(filename,url):return True
                return False
            else:
                return False
        except:
            return False

    def read_file_md5(self, filename):
        if os.path.exists(filename):
            with open(filename, 'rb') as fp:
                data = fp.read()
            file_md5 = hashlib.md5(data).hexdigest()
            return file_md5
        else:
            return False

    def send_baota2(self, filename):
        cloudUrl = 'http://www.bt.cn/api/panel/btwaf_submit'
        pdata = {'codetxt': self.ReadFile(filename), 'md5': self.read_file_md5(filename), 'type': '0',
                 'host_ip': public.GetLocalIp(), 'size': os.path.getsize(filename)}
        ret = public.httpPost(cloudUrl, pdata)
        return True

    def send_baota(self, filename):
        if not os.path.exists(filename): return False
        cloudUrl = 'http://www.bt.cn/api/panel/btwaf_submit'
        pdata = {'codetxt': self.ReadFile(filename), 'md5': self.read_file_md5(filename), 'type': '0',
                 'host_ip': public.GetLocalIp(), 'size': os.path.getsize(filename)}
        ret = public.httpPost(cloudUrl, pdata)
        if ret == '1':
            return self.check_webshell(filename)
        elif ret == '-1':
            return self.check_webshell(filename)
        else:
            return False

    def check_webshell(self, filename):
        if not os.path.exists(filename): return False
        cloudUrl = 'http://www.bt.cn/api/panel/btwaf_check_file'
        pdata = {'md5': self.read_file_md5(filename), 'size': os.path.getsize(filename)}
        ret = public.httpPost(cloudUrl, pdata)
        if ret == '0':
            return False
        elif ret == '1':
            return False
        elif ret == '-1':
            return False
        else:
            return False

    def __get_md5(self, s):
        m = hashlib.md5()
        m.update(s.encode('utf-8'))
        return m.hexdigest()

if __name__ == "__main__":
    public.WriteFile('/www/server/panel/data/webshell_data.json', json.dumps([]))
    type = sys.argv[1]
    path = sys.argv[2]
    send = sys.argv[3]
    os.chdir("/www/server/panel")
    import sys
    sys.path.append('class')
    import public
    aa = webshell_check()
    print('开始扫描webshell 本次查杀由长亭牧云强力驱动')
    start_time=time.time()

    if type == 'dir':
        data = aa.san_dir(path)
        public.WriteFile('/www/server/panel/data/webshell_data.json', json.dumps(data))
        localtime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        if len(data) >= 1:
            public.WriteLog('宝塔内置webshell查杀', '查杀%s目录查到如下木马%s' % (path, data))
            print('【%s】 扫描完毕！本次扫描耗时%s秒，发现%s个木马。' % (localtime, int(time.time() - start_time), len(data)))
        else:
            print('【%s】 扫描完毕！本次扫描耗时%s秒，未发现存在木马。' % (localtime, int(time.time() - start_time)))
    elif type == 'site':
        if path == 'ALL' or path == 'all':
            data = public.M('sites').field('name,id,path').limit('500').select()
            if len(data) >= 1:
                for i in data:
                    localtime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                    print('【%s】 正在扫描网站 【%s】' % (time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), i['name']))
                    path = i['path']
                    ##木马返回在这里
                    data = aa.send_san_dir(path, send)
                    if len(data) >= 1:
                        public.WriteLog('宝塔内置webshell查杀', '查杀%s目录查到如下木马%s' % (path, data))
                        print('【%s】 扫描完毕！本次扫描耗时%s秒，发现%s个木马。' % (localtime, int(time.time() - start_time), len(data)))
                    else:
                        print('【%s】 扫描完毕！本次扫描耗时%s秒，未发现存在木马。' % (localtime, int(time.time() - start_time)))
        else:
            data = public.M('sites').where('name=?', (path,)).field('name,id,path').select()
            localtime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            if len(data) >= 1:
                path = data[0]['path']
                ##木马返回在这里
                data = aa.send_san_dir(path, send)
                if len(data) >= 1:
                    public.WriteLog('宝塔内置webshell查杀', '查杀%s目录查到如下木马%s' % (path, data))
                print('【%s】 扫描完毕！本次扫描耗时%s秒，发现%s个木马。' % (localtime,int(time.time() - start_time),len(data)))
            else:
                print('【%s】 扫描完毕！本次扫描耗时%s秒，未发现存在木马。' % (localtime, int(time.time() - start_time)))