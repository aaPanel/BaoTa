#coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板 
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: 黄文良 <287962566@qq.com>
# +-------------------------------------------------------------------

#--------------------------------
# 宝塔公共库
#--------------------------------

import json,os,sys,time,re,socket,importlib,binascii,base64

if sys.version_info[0] == 2:
    reload(sys)
    sys.setdefaultencoding('utf8')

def M(table):
    import db
    sql = db.Sql()
    return sql.table(table);

def HttpGet(url,timeout = 6,headers = {}):
    """
    发送GET请求
    @url 被请求的URL地址(必需)
    @timeout 超时时间默认60秒
    return string
    """

    if is_local(): return False
    home = 'www.bt.cn'
    host_home = 'data/home_host.pl'
    old_url = url
    if url.find(home) != -1:
        if os.path.exists(host_home): 
            headers['host'] = home
            url = url.replace(home,readFile(host_home))
    if sys.version_info[0] == 2:
        try:
            import urllib2,ssl
            if sys.version_info[0] == 2:
                reload(urllib2)
                reload(ssl)
            try:
                ssl._create_default_https_context = ssl._create_unverified_context
            except:pass;
            req = urllib2.Request(url, headers = headers)
            response = urllib2.urlopen(req,timeout = timeout,)
            return response.read()
        except Exception as ex:
            if old_url.find(home) != -1: return http_get_home(old_url,timeout,str(ex))
            if headers: return False
            return str(ex);
    else:
        try:
            import urllib.request,ssl
            try:
                ssl._create_default_https_context = ssl._create_unverified_context
            except:pass;
            req = urllib.request.Request(url,headers = headers)
            response = urllib.request.urlopen(req,timeout = timeout)
            result = response.read()
            if type(result) == bytes: result = result.decode('utf-8')
            return result
        except Exception as ex:
            if old_url.find(home) != -1: return http_get_home(old_url,timeout,str(ex))
            if headers: return False
            return str(ex)

def http_get_home(url,timeout,ex):
    try:
        home = 'www.bt.cn'
        if url.find(home) == -1: return ex
        hosts_file = "config/hosts.json"
        if not os.path.exists(hosts_file): return ex
        hosts = json.loads(readFile(hosts_file))
        headers = {"host":home}
        for host in hosts:
            new_url = url.replace(home,host)
            res = HttpGet(new_url,timeout,headers)
            if res: 
                writeFile("data/home_host.pl",host)
                set_home_host(host)
                return res
        return ex
    except: return ex


def set_home_host(host):
    ExecShell('sed -i "/www.bt.cn/d" /etc/hosts')
    ExecShell("echo '' >> /etc/hosts")
    ExecShell("echo '%s www.bt.cn' >> /etc/hosts" % host)
    ExecShell('sed -i "/^\s*$/d" /etc/hosts')

def httpGet(url,timeout=6):
    return HttpGet(url,timeout)

def HttpPost(url,data,timeout = 6,headers = {}):
    """
    发送POST请求
    @url 被请求的URL地址(必需)
    @data POST参数，可以是字符串或字典(必需)
    @timeout 超时时间默认60秒
    return string
    """
    if is_local(): return False
    home = 'www.bt.cn'
    host_home = 'data/home_host.pl'
    old_url = url
    if url.find(home) != -1:
        if os.path.exists(host_home): 
            headers['host'] = home
            url = url.replace(home,readFile(host_home))

    if sys.version_info[0] == 2:
        try:
            import urllib,urllib2,ssl
            try:
                ssl._create_default_https_context = ssl._create_unverified_context
            except:pass
            data2 = urllib.urlencode(data)
            req = urllib2.Request(url, data2,headers = headers)
            response = urllib2.urlopen(req,timeout=timeout)
            return response.read()
        except Exception as ex:
            if old_url.find(home) != -1: return http_post_home(old_url,data,timeout,str(ex))
            if headers: return False
            return str(ex);
    else:
        try:
            import urllib.request,ssl
            try:
                ssl._create_default_https_context = ssl._create_unverified_context
            except:pass;
            data2 = urllib.parse.urlencode(data).encode('utf-8')
            req = urllib.request.Request(url, data2,headers = headers)
            response = urllib.request.urlopen(req,timeout = timeout)
            result = response.read()
            if type(result) == bytes: result = result.decode('utf-8')
            return result
        except Exception as ex:
            if old_url.find(home) != -1: return http_post_home(old_url,data,timeout,str(ex))
            if headers: return False
            return str(ex);

def http_post_home(url,data,timeout,ex):
    try:
        home = 'www.bt.cn'
        if url.find(home) == -1: return ex
        hosts_file = "config/hosts.json"
        if not os.path.exists(hosts_file): return ex
        hosts = json.loads(readFile(hosts_file))
        headers = {"host":home}
        for host in hosts:
            new_url = url.replace(home,host)
            res = HttpPost(new_url,data,timeout,headers)
            if res: 
                writeFile("data/home_host.pl",host)
                set_home_host(host)
                return res
        return ex
    except: return ex

def httpPost(url,data,timeout=6):
    return HttpPost(url,data,timeout)

def check_home():
    return True

def Md5(strings):
    """
    生成MD5
    @strings 要被处理的字符串
    return string(32)
    """
    import hashlib
    m = hashlib.md5()
    m.update(strings.encode('utf-8'))
    return m.hexdigest()

def md5(strings):
    return Md5(strings)

def FileMd5(filename):
    """
    生成文件的MD5
    @filename 文件名
    return string(32) or False
    """
    if not os.path.isfile(filename): return False;
    import hashlib;
    my_hash = hashlib.md5()
    f = open(filename,'rb')
    while True:
        b = f.read(8096)
        if not b :
            break
        my_hash.update(b)
    f.close()
    return my_hash.hexdigest();


def GetRandomString(length):
    """
       取随机字符串
       @length 要获取的长度
       return string(length)
    """
    from random import Random
    strings = ''
    chars = 'AaBbCcDdEeFfGgHhIiJjKkLlMmNnOoPpQqRrSsTtUuVvWwXxYyZz0123456789'
    chrlen = len(chars) - 1
    random = Random()
    for i in range(length):
        strings += chars[random.randint(0, chrlen)]
    return strings

def ReturnJson(status,msg,args=()):
    """
    取通用Json返回
    @status  返回状态
    @msg  返回消息
    return string(json)
    """
    return GetJson(ReturnMsg(status,msg,args));

def returnJson(status,msg,args=()):
    return ReturnJson(status,msg,args)

def ReturnMsg(status,msg,args = ()):
    log_message = json.loads(ReadFile('BTPanel/static/language/' + GetLanguage() + '/public.json'));
    keys = log_message.keys();
    if type(msg) == str:
        if msg in keys:
            msg = log_message[msg];
            for i in range(len(args)):
                rep = '{'+str(i+1)+'}'
                msg = msg.replace(rep,args[i]);
    return {'status':status,'msg':msg}

def returnMsg(status,msg,args = ()):
    return ReturnMsg(status,msg,args)


def GetFileMode(filename):
    '''取文件权限'''
    stat = os.stat(filename)
    accept = str(oct(stat.st_mode)[-3:]);
    return accept

def get_mode_and_user(path):
    '''取文件或目录权限信息'''
    import pwd
    data = {}
    if not os.path.exists(path): return None
    stat = os.stat(path)
    data['mode'] = str(oct(stat.st_mode)[-3:])
    try:
        data['user'] = pwd.getpwuid(stat.st_uid).pw_name
    except:
        data['user'] = str(stat.st_uid)
    return data


def GetJson(data):
    """
    将对象转换为JSON
    @data 被转换的对象(dict/list/str/int...)
    """
    from json import dumps
    if data == bytes: data = data.decode('utf-8')
    try:
        return dumps(data)
    except:
        return dumps(returnMsg(False,"错误的响应: %s" % str(data)))

def getJson(data):
    return GetJson(data)

def ReadFile(filename,mode = 'r'):
    """
    读取文件内容
    @filename 文件名
    return string(bin) 若文件不存在，则返回None
    """
    import os
    if not os.path.exists(filename): return False
    try:
        fp = open(filename, mode)
        f_body = fp.read()
        fp.close()
    except Exception as ex:
        if sys.version_info[0] != 2:
            try:
                fp = open(filename, mode,encoding="utf-8");
                f_body = fp.read()
                fp.close()
            except Exception as ex2:
                WriteLog('打开文件',str(ex2))
                return False
        else:
            WriteLog('打开文件',str(ex))
            return False
    return f_body

def readFile(filename,mode='r'):
    return ReadFile(filename,mode)

def WriteFile(filename,s_body,mode='w+'):
    """
    写入文件内容
    @filename 文件名
    @s_body 欲写入的内容
    return bool 若文件不存在则尝试自动创建
    """
    try:
        fp = open(filename, mode);
        fp.write(s_body)
        fp.close()
        return True
    except:
        try:
            fp = open(filename, mode,encoding="utf-8");
            fp.write(s_body)
            fp.close()
            return True
        except:
            return False

def writeFile(filename,s_body,mode='w+'):
    return WriteFile(filename,s_body,mode)

def WriteLog(type,logMsg,args=()):
    #写日志
    #try:
    import time,db,json
    logMessage = json.loads(readFile('BTPanel/static/language/' + get_language() + '/log.json'));
    keys = logMessage.keys();
    if logMsg in keys:
        logMsg = logMessage[logMsg];
        for i in range(len(args)):
            rep = '{'+str(i+1)+'}'
            logMsg = logMsg.replace(rep,args[i]);
    if type in keys: type = logMessage[type];
    sql = db.Sql()
    mDate = time.strftime('%Y-%m-%d %X',time.localtime());
    data = (type,logMsg,mDate);
    result = sql.table('logs').add('type,log,addtime',data);
    #except:
        #pass

def GetLanguage():
    '''
    取语言
    '''
    return GetConfigValue("language")

def get_language():
    return GetLanguage()

def GetConfigValue(key):
    '''
    取配置值
    '''
    config = GetConfig()
    if not key in config.keys(): return None
    return config[key]

def SetConfigValue(key,value):
    config = GetConfig()
    config[key] = value
    WriteConfig(config)

def GetConfig():
    '''
    取所有配置项
    '''
    path = "config/config.json"
    if not os.path.exists(path): return {}
    f_body = ReadFile(path)
    if not f_body: return {}
    return json.loads(f_body)

def WriteConfig(config):
    path = "config/config.json"
    WriteFile(path,json.dumps(config))


def GetLan(key):
    """
    取提示消息
    """
    log_message = json.loads(ReadFile('BTPanel/static/language/' + GetLanguage() + '/template.json'));
    keys = log_message.keys();
    msg = None;
    if key in keys:
        msg = log_message[key];
    return msg;
def getLan(key):
    return GetLan(key)

def GetMsg(key,args = ()):
    try:
        log_message = json.loads(ReadFile('BTPanel/static/language/' + GetLanguage() + '/public.json'));
        keys = log_message.keys();
        msg = None;
        if key in keys:
            msg = log_message[key];
            for i in range(len(args)):
                rep = '{'+str(i+1)+'}'
                msg = msg.replace(rep,args[i]);
        return msg;
    except:
        return key
def getMsg(key,args = ()):
    return GetMsg(key,args)


#获取Web服务器
def GetWebServer():
    webserver = 'nginx';
    if not os.path.exists('/www/server/nginx/sbin/nginx'): webserver = 'apache';
    return webserver;

def get_webserver():
    return GetWebServer()


def ServiceReload():
    #重载Web服务配置
    if os.path.exists('/www/server/nginx/sbin/nginx'):
        result = ExecShell('/etc/init.d/nginx reload')
        if result[1].find('nginx.pid') != -1:
            ExecShell('pkill -9 nginx && sleep 1');
            ExecShell('/etc/init.d/nginx start');
    else:
        result = ExecShell('/etc/init.d/httpd reload')
    return result;
def serviceReload():
    return ServiceReload()


def ExecShell(cmdstring, cwd=None, timeout=None, shell=True):
    a = ''
    e = ''
    try:
        #通过管道执行SHELL
        import shlex
        import datetime
        import subprocess
        import time

        if shell:
            cmdstring_list = cmdstring
        else:
            cmdstring_list = shlex.split(cmdstring)
        if timeout:
            end_time = datetime.datetime.now() + datetime.timedelta(seconds=timeout)
        sub = subprocess.Popen(cmdstring_list, cwd=cwd, stdin=subprocess.PIPE,shell=shell,bufsize=4096,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        while sub.poll() is None:
            time.sleep(0.1)
            if timeout:
                if end_time <= datetime.datetime.now():
                    raise Exception("Timeout：%s"%cmdstring)
        a,e = sub.communicate()
        try:
            if type(a) == bytes: a = a.decode('utf-8')
            if type(e) == bytes: e = e.decode('utf-8')
        except:pass
    except:
        if not a:
            a = os.popen(cmdstring).read()

    return a,e

def GetLocalIp():
    #取本地外网IP    
    try:
        filename = 'data/iplist.txt'
        ipaddress = readFile(filename)
        if not ipaddress:
            url = 'http://pv.sohu.com/cityjson?ie=utf-8'
            m_str = HttpGet(url)
            ipaddress = re.search('\d+.\d+.\d+.\d+',m_str).group(0)
            WriteFile(filename,ipaddress)
        c_ip = check_ip(ipaddress)
        if not c_ip: return GetHost()
        return ipaddress
    except:
        try:
            url = GetConfigValue('home') + '/Api/getIpAddress';
            return HttpGet(url)
        except:
            return GetHost();

def is_ipv4(ip):
    try:
        socket.inet_pton(socket.AF_INET, ip)
    except AttributeError:
        try:
            socket.inet_aton(ip)
        except socket.error:
            return False
        return ip.count('.') == 3
    except socket.error:
        return False
    return True
 
 
def is_ipv6(ip):
    try:
        socket.inet_pton(socket.AF_INET6, ip)
    except socket.error:
        return False
    return True
 
 
def check_ip(ip):
    return is_ipv4(ip) or is_ipv6(ip)

def GetHost(port = False):
    from flask import request
    host_tmp = request.headers.get('host')
    if not host_tmp: 
        if request.url_root:
            tmp = re.findall("(https|http)://([\w:\.-]+)",request.url_root)
            if tmp: host_tmp = tmp[0][1]
    if not host_tmp:
        host_tmp = GetLocalIp() + ':' + readFile('data/port.pl').strip()
    try:
        if host_tmp.find(':') == -1: host_tmp += ':80';
    except:
        host_tmp = "127.0.0.1:8888"
    h = host_tmp.split(':')
    if port: return h[1]
    return h[0]

def GetClientIp():
    from flask import request
    return request.remote_addr.replace('::ffff:','')

def phpReload(version):
    #重载PHP配置
    import os
    if os.path.exists('/www/server/php/' + version + '/libphp5.so'):
        ExecShell('/etc/init.d/httpd reload');
    else:
        ExecShell('/etc/init.d/php-fpm-'+version+' reload');

def get_url(timeout = 0.5):
    import json
    try:
        nodeFile = 'data/node.json';
        node_list = json.loads(readFile(nodeFile));
        mnode = None
        for node in node_list:
            node['ping'] = get_timeout(node['protocol'] + node['address'] + ':' + node['port'] + '/check.txt');
            if not node['ping']: continue;
            if not mnode: mnode = node;
            if node['ping'] < mnode['ping']: mnode = node;
            if mnode['ping'] < 50: break
        return mnode['protocol'] + mnode['address'] + ':' + mnode['port'];
    except:
        return 'http://download.bt.cn';


#过滤输入
def checkInput(data):
   if not data: return data;
   if type(data) != str: return data;
   checkList = [
                {'d':'<','r':'＜'},
                {'d':'>','r':'＞'},
                {'d':'\'','r':'‘'},
                {'d':'"','r':'“'},
                {'d':'&','r':'＆'},
                {'d':'#','r':'＃'},
                {'d':'<','r':'＜'}
                ]
   for v in checkList:
       data = data.replace(v['d'],v['r']);
   return data;

#取文件指定尾行数
def GetNumLines(path,num,p=1):
    pyVersion = sys.version_info[0]
    try:
        import cgi
        if not os.path.exists(path): return "";
        start_line = (p - 1) * num;
        count = start_line + num;
        fp = open(path,'rb')
        buf = ""
        fp.seek(-1, 2)
        if fp.read(1) == "\n": fp.seek(-1, 2)
        data = []
        b = True
        n = 0;
        for i in range(count):
            while True:
                newline_pos = str.rfind(str(buf), "\n")
                pos = fp.tell()
                if newline_pos != -1:
                    if n >= start_line:
                        line = buf[newline_pos + 1:]
                        try:
                            data.insert(0,cgi.escape(line))
                        except: pass
                    buf = buf[:newline_pos]
                    n += 1;
                    break;
                else:
                    if pos == 0:
                        b = False
                        break
                    to_read = min(4096, pos)
                    fp.seek(-to_read, 1)
                    t_buf = fp.read(to_read)
                    if pyVersion == 3:
                        try:
                            if type(t_buf) == bytes: t_buf = t_buf.decode('utf-8')
                        except:t_buf = str(t_buf)
                    buf = t_buf + buf
                    fp.seek(-to_read, 1)
                    if pos - to_read == 0:
                        buf = "\n" + buf
            if not b: break;
        fp.close()
    except: return ""
    return "\n".join(data)

#验证证书
def CheckCert(certPath = 'ssl/certificate.pem'):
    openssl = '/usr/local/openssl/bin/openssl';
    if not os.path.exists(openssl): openssl = 'openssl';
    certPem = readFile(certPath);
    s = "\n-----BEGIN CERTIFICATE-----";
    tmp = certPem.strip().split(s)
    for tmp1 in tmp:
        if tmp1.find('-----BEGIN CERTIFICATE-----') == -1:  tmp1 = s + tmp1;
        writeFile(certPath,tmp1);
        result = ExecShell(openssl + " x509 -in "+certPath+" -noout -subject")
        if result[1].find('-bash:') != -1: return True
        if len(result[1]) > 2: return False
        if result[0].find('error:') != -1: return False;
    return True;


# 获取面板地址
def getPanelAddr():
    from flask import request
    protocol = 'https://' if os.path.exists("data/ssl.pl") else 'http://'
    return protocol + request.headers.get('host')


#字节单位转换
def to_size(size):
    d = ('b','KB','MB','GB','TB');
    s = d[0];
    for b in d:
        if size < 1024: return ("%.2f" % size) + ' ' + b;
        size = size / 1024;
        s = b;
    return ("%.2f" % size) + ' ' + b;


def checkCode(code,outime = 120):
    #校验验证码
    from BTPanel import session,cache
    try:
        codeStr = cache.get('codeStr')
        cache.delete('codeStr')
        if not codeStr:
            session['login_error'] = GetMsg('CODE_TIMEOUT')
            return False

        if md5(code.lower()) != codeStr:
            session['login_error'] = GetMsg('CODE_ERR')
            return False
        return True
    except:
        session['login_error'] = GetMsg('CODE_NOT_EXISTS')
        return False

#写进度
def writeSpeed(title,used,total,speed = 0):
    import json
    if not title:
        data = {'title':None,'progress':0,'total':0,'used':0,'speed':0}
    else:
        progress = int((100.0 * used / total));
        data = {'title':title,'progress':progress,'total':total,'used':used,'speed':speed}
    writeFile('/tmp/panelSpeed.pl',json.dumps(data));
    return True;

#取进度
def getSpeed():
    import json;
    data = readFile('/tmp/panelSpeed.pl');
    if not data: 
        data = json.dumps({'title':None,'progress':0,'total':0,'used':0,'speed':0})
        writeFile('/tmp/panelSpeed.pl',data);
    return json.loads(data);

def downloadFile(url,filename):
    try:
        if sys.version_info[0] == 2:
            import urllib
            urllib.urlretrieve(url,filename=filename ,reporthook= downloadHook)
        else:
            import urllib.request
            urllib.request.urlretrieve(url,filename=filename ,reporthook= downloadHook)
    except:
        return False
    
def downloadHook(count, blockSize, totalSize):
    speed = {'total':totalSize,'block':blockSize,'count':count}
    #print('%02d%%'%(100.0 * count * blockSize / totalSize))

def get_error_info():
    import traceback
    errorMsg = traceback.format_exc();
    return errorMsg

def submit_error(err_msg = None):
    try:
        if os.path.exists('/www/server/panel/not_submit_errinfo.pl'): return False
        from BTPanel import request
        import system
        if not err_msg: err_msg = get_error_info()
        pdata = {}
        pdata['err_info'] = err_msg
        pdata['path_full'] = request.full_path
        pdata['version'] = 'Linux-Panel-%s' % version()
        pdata['os'] = system.system().GetSystemVersion()
        pdata['py_version'] = sys.version
        pdata['install_date'] = int(os.stat('/www/server/panel/class/common.py').st_mtime)
        httpPost("http://www.bt.cn/api/panel/s_error",pdata,timeout=3)
    except:
        pass



#搜索数据中是否存在
def inArray(arrays,searchStr):
    for key in arrays:
        if key == searchStr: return True
    
    return False

#格式化指定时间戳
def format_date(format="%Y-%m-%d %H:%M:%S",times = None):
    if not times: times = int(time.time())
    time_local = time.localtime(times)
    return time.strftime(format, time_local) 


#检查Web服务器配置文件是否有错误
def checkWebConfig():
    f1 = '/www/server/panel/vhost/'
    f2 = '/www/server/panel/plugin/'
    if not os.path.exists(f2 + 'btwaf'):
        f3 = f1 + 'nginx/btwaf.conf'
        if os.path.exists(f3): os.remove(f3)
    if not os.path.exists(f2 + 'btwaf_httpd'):
        f3 = f1 + 'apache/btwaf.conf'
        if os.path.exists(f3): os.remove(f3)

    if not os.path.exists(f2 + 'total'):
        f3 = f1 + 'apache/total.conf'
        if os.path.exists(f3): os.remove(f3)
        f3 = f1 + 'nginx/total.conf'
        if os.path.exists(f3): os.remove(f3)
    else:
        if os.path.exists('/www/server/apache/modules/mod_lua.so'): 
            writeFile(f1 + 'apache/btwaf.conf','LoadModule lua_module modules/mod_lua.so')
            writeFile(f1 + 'apache/total.conf','LuaHookLog /www/server/total/httpd_log.lua run_logs')
        else:
            f3 = f1 + 'apache/total.conf'
            if os.path.exists(f3): os.remove(f3)

    if get_webserver() == 'nginx':
        result = ExecShell("ulimit -n 8192 ; /www/server/nginx/sbin/nginx -t -c /www/server/nginx/conf/nginx.conf");
        searchStr = 'successful'
    else:
        result = ExecShell("ulimit -n 8192 ; /www/server/apache/bin/apachectl -t");
        searchStr = 'Syntax OK'
    
    if result[1].find(searchStr) == -1:
        WriteLog("TYPE_SOFT", 'CONF_CHECK_ERR',(result[1],));
        return result[1];
    return True;


#检查是否为IPv4地址
def checkIp(ip):
    p = re.compile('^((25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(25[0-5]|2[0-4]\d|[01]?\d\d?)$')  
    if p.match(ip):  
        return True  
    else:  
        return False
    
#检查端口是否合法
def checkPort(port):
    if not re.match("^\d+$",port): return False
    ports = ['21','25','443','8080','888','8888','8443'];
    if port in ports: return False;
    intport = int(port);
    if intport < 1 or intport > 65535: return False;
    return True;

#字符串取中间
def getStrBetween(startStr,endStr,srcStr):
    start = srcStr.find(startStr)
    if start == -1: return None
    end = srcStr.find(endStr)
    if end == -1: return None
    return srcStr[start+1:end]

#取CPU类型
def getCpuType():
    cpuinfo = open('/proc/cpuinfo','r').read()
    rep = "model\s+name\s+:\s+(.+)"
    tmp = re.search(rep,cpuinfo,re.I);
    cpuType = ''
    if tmp:
        cpuType = tmp.groups()[0]
    else:
        cpuinfo = ExecShell('LANG="en_US.UTF-8" && lscpu')[0]
        rep = "Model\s+name:\s+(.+)"
        tmp = re.search(rep,cpuinfo,re.I)
        if tmp: cpuType = tmp.groups()[0]
    return cpuType;


#检查是否允许重启
def IsRestart():
    num  = M('tasks').where('status!=?',('1',)).count();
    if num > 0: return False;
    return True;

#加密密码字符
def hasPwd(password):
    import crypt;
    return crypt.crypt(password,password);

def get_timeout(url,timeout=3):
    try:
        start = time.time();
        result = httpGet(url,timeout);
        if result != 'True': return False;
        return int((time.time() - start) * 1000);
    except: return False

def getDate(format='%Y-%m-%d %X'):
    #取格式时间
    return time.strftime(format,time.localtime())


#处理MySQL配置文件
def CheckMyCnf():
    import os;
    confFile = '/etc/my.cnf'
    if os.path.exists(confFile): 
        conf = readFile(confFile)
        if conf.find('[mysqld]') != -1: return True;
    versionFile = '/www/server/mysql/version.pl';
    if not os.path.exists(versionFile): return False;
    
    versions = ['5.1','5.5','5.6','5.7','AliSQL']
    version = readFile(versionFile);
    for key in versions:
        if key in version:
            version = key;
            break;
    
    shellStr = '''
#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH

CN='125.88.182.172'
HK='download.bt.cn'
HK2='103.224.251.67'
US='128.1.164.196'
sleep 0.5;
CN_PING=`ping -c 1 -w 1 $CN|grep time=|awk '{print $7}'|sed "s/time=//"`
HK_PING=`ping -c 1 -w 1 $HK|grep time=|awk '{print $7}'|sed "s/time=//"`
HK2_PING=`ping -c 1 -w 1 $HK2|grep time=|awk '{print $7}'|sed "s/time=//"`
US_PING=`ping -c 1 -w 1 $US|grep time=|awk '{print $7}'|sed "s/time=//"`

echo "$HK_PING $HK" > ping.pl
echo "$HK2_PING $HK2" >> ping.pl
echo "$US_PING $US" >> ping.pl
echo "$CN_PING $CN" >> ping.pl
nodeAddr=`sort -V ping.pl|sed -n '1p'|awk '{print $2}'`
if [ "$nodeAddr" == "" ];then
    nodeAddr=$HK
fi

Download_Url=http://$nodeAddr:5880


MySQL_Opt()
{
    MemTotal=`free -m | grep Mem | awk '{print  $2}'`
    if [[ ${MemTotal} -gt 1024 && ${MemTotal} -lt 2048 ]]; then
        sed -i "s#^key_buffer_size.*#key_buffer_size = 32M#" /etc/my.cnf
        sed -i "s#^table_open_cache.*#table_open_cache = 128#" /etc/my.cnf
        sed -i "s#^sort_buffer_size.*#sort_buffer_size = 768K#" /etc/my.cnf
        sed -i "s#^read_buffer_size.*#read_buffer_size = 768K#" /etc/my.cnf
        sed -i "s#^myisam_sort_buffer_size.*#myisam_sort_buffer_size = 8M#" /etc/my.cnf
        sed -i "s#^thread_cache_size.*#thread_cache_size = 16#" /etc/my.cnf
        sed -i "s#^query_cache_size.*#query_cache_size = 16M#" /etc/my.cnf
        sed -i "s#^tmp_table_size.*#tmp_table_size = 32M#" /etc/my.cnf
        sed -i "s#^innodb_buffer_pool_size.*#innodb_buffer_pool_size = 128M#" /etc/my.cnf
        sed -i "s#^innodb_log_file_size.*#innodb_log_file_size = 32M#" /etc/my.cnf
    elif [[ ${MemTotal} -ge 2048 && ${MemTotal} -lt 4096 ]]; then
        sed -i "s#^key_buffer_size.*#key_buffer_size = 64M#" /etc/my.cnf
        sed -i "s#^table_open_cache.*#table_open_cache = 256#" /etc/my.cnf
        sed -i "s#^sort_buffer_size.*#sort_buffer_size = 1M#" /etc/my.cnf
        sed -i "s#^read_buffer_size.*#read_buffer_size = 1M#" /etc/my.cnf
        sed -i "s#^myisam_sort_buffer_size.*#myisam_sort_buffer_size = 16M#" /etc/my.cnf
        sed -i "s#^thread_cache_size.*#thread_cache_size = 32#" /etc/my.cnf
        sed -i "s#^query_cache_size.*#query_cache_size = 32M#" /etc/my.cnf
        sed -i "s#^tmp_table_size.*#tmp_table_size = 64M#" /etc/my.cnf
        sed -i "s#^innodb_buffer_pool_size.*#innodb_buffer_pool_size = 256M#" /etc/my.cnf
        sed -i "s#^innodb_log_file_size.*#innodb_log_file_size = 64M#" /etc/my.cnf
    elif [[ ${MemTotal} -ge 4096 && ${MemTotal} -lt 8192 ]]; then
        sed -i "s#^key_buffer_size.*#key_buffer_size = 128M#" /etc/my.cnf
        sed -i "s#^table_open_cache.*#table_open_cache = 512#" /etc/my.cnf
        sed -i "s#^sort_buffer_size.*#sort_buffer_size = 2M#" /etc/my.cnf
        sed -i "s#^read_buffer_size.*#read_buffer_size = 2M#" /etc/my.cnf
        sed -i "s#^myisam_sort_buffer_size.*#myisam_sort_buffer_size = 32M#" /etc/my.cnf
        sed -i "s#^thread_cache_size.*#thread_cache_size = 64#" /etc/my.cnf
        sed -i "s#^query_cache_size.*#query_cache_size = 64M#" /etc/my.cnf
        sed -i "s#^tmp_table_size.*#tmp_table_size = 64M#" /etc/my.cnf
        sed -i "s#^innodb_buffer_pool_size.*#innodb_buffer_pool_size = 512M#" /etc/my.cnf
        sed -i "s#^innodb_log_file_size.*#innodb_log_file_size = 128M#" /etc/my.cnf
    elif [[ ${MemTotal} -ge 8192 && ${MemTotal} -lt 16384 ]]; then
        sed -i "s#^key_buffer_size.*#key_buffer_size = 256M#" /etc/my.cnf
        sed -i "s#^table_open_cache.*#table_open_cache = 1024#" /etc/my.cnf
        sed -i "s#^sort_buffer_size.*#sort_buffer_size = 4M#" /etc/my.cnf
        sed -i "s#^read_buffer_size.*#read_buffer_size = 4M#" /etc/my.cnf
        sed -i "s#^myisam_sort_buffer_size.*#myisam_sort_buffer_size = 64M#" /etc/my.cnf
        sed -i "s#^thread_cache_size.*#thread_cache_size = 128#" /etc/my.cnf
        sed -i "s#^query_cache_size.*#query_cache_size = 128M#" /etc/my.cnf
        sed -i "s#^tmp_table_size.*#tmp_table_size = 128M#" /etc/my.cnf
        sed -i "s#^innodb_buffer_pool_size.*#innodb_buffer_pool_size = 1024M#" /etc/my.cnf
        sed -i "s#^innodb_log_file_size.*#innodb_log_file_size = 256M#" /etc/my.cnf
    elif [[ ${MemTotal} -ge 16384 && ${MemTotal} -lt 32768 ]]; then
        sed -i "s#^key_buffer_size.*#key_buffer_size = 512M#" /etc/my.cnf
        sed -i "s#^table_open_cache.*#table_open_cache = 2048#" /etc/my.cnf
        sed -i "s#^sort_buffer_size.*#sort_buffer_size = 8M#" /etc/my.cnf
        sed -i "s#^read_buffer_size.*#read_buffer_size = 8M#" /etc/my.cnf
        sed -i "s#^myisam_sort_buffer_size.*#myisam_sort_buffer_size = 128M#" /etc/my.cnf
        sed -i "s#^thread_cache_size.*#thread_cache_size = 256#" /etc/my.cnf
        sed -i "s#^query_cache_size.*#query_cache_size = 256M#" /etc/my.cnf
        sed -i "s#^tmp_table_size.*#tmp_table_size = 256M#" /etc/my.cnf
        sed -i "s#^innodb_buffer_pool_size.*#innodb_buffer_pool_size = 2048M#" /etc/my.cnf
        sed -i "s#^innodb_log_file_size.*#innodb_log_file_size = 512M#" /etc/my.cnf
    elif [[ ${MemTotal} -ge 32768 ]]; then
        sed -i "s#^key_buffer_size.*#key_buffer_size = 1024M#" /etc/my.cnf
        sed -i "s#^table_open_cache.*#table_open_cache = 4096#" /etc/my.cnf
        sed -i "s#^sort_buffer_size.*#sort_buffer_size = 16M#" /etc/my.cnf
        sed -i "s#^read_buffer_size.*#read_buffer_size = 16M#" /etc/my.cnf
        sed -i "s#^myisam_sort_buffer_size.*#myisam_sort_buffer_size = 256M#" /etc/my.cnf
        sed -i "s#^thread_cache_size.*#thread_cache_size = 512#" /etc/my.cnf
        sed -i "s#^query_cache_size.*#query_cache_size = 512M#" /etc/my.cnf
        sed -i "s#^tmp_table_size.*#tmp_table_size = 512M#" /etc/my.cnf
        sed -i "s#^innodb_buffer_pool_size.*#innodb_buffer_pool_size = 4096M#" /etc/my.cnf
        sed -i "s#^innodb_log_file_size.*#innodb_log_file_size = 1024M#" /etc/my.cnf
    fi
}

wget -O /etc/my.cnf $Download_Url/install/conf/mysql-%s.conf -T 5
MySQL_Opt
''' % (version,)
    #判断是否迁移目录
    if os.path.exists('data/datadir.pl'):
        newPath = readFile('data/datadir.pl');
        mycnf = readFile('/etc/my.cnf');
        mycnf = mycnf.replace('/www/server/data',newPath);
        writeFile('/etc/my.cnf',mycnf);
        
    os.system(shellStr);
    WriteLog('TYPE_SOFE', 'MYSQL_CHECK_ERR');
    return True;


def GetSSHPort():
    try:
        file = '/etc/ssh/sshd_config'
        conf = ReadFile(file)
        rep = "#*Port\s+([0-9]+)\s*\n"
        port = re.search(rep,conf).groups(0)[0]
        return int(port)
    except:
        return 22

def GetSSHStatus():
    if os.path.exists('/usr/bin/apt-get'):
             status = ExecShell("service ssh status | grep -P '(dead|stop)'")
    else:
        import system
        panelsys = system.system();
        version = panelsys.GetSystemVersion();
        if version.find(' 7.') != -1:
            status = ExecShell("systemctl status sshd.service | grep 'dead'")
        else:
            status = ExecShell("/etc/init.d/sshd status | grep -e 'stopped' -e '已停'")
    if len(status[0]) > 3:
        status = False
    else:
        status = True
    return status

#检查端口是否合法
def CheckPort(port,other=None):
    if type(port) == str: port = int(port)
    if port < 1 or port > 65535: return False
    if other:
        checks = [22,20,21,8888,3306,11211,888,25]
        if port in checks: return False
    return True

#获取Token
def GetToken():
    try:
        from json import loads
        tokenFile = 'data/token.json';
        if not os.path.exists(tokenFile): return False;
        token = loads(readFile(tokenFile));
        return token;
    except:
        return False

def to_btint(string):
    m_list = []
    for s in string:
        m_list.append(ord(s))
    return m_list;

def load_module(pluginCode):
    from imp import new_module
    from BTPanel import cache
    p_tk = 'data/%s' % md5(pluginCode + get_uuid())
    pluginInfo = None
    if cache: pluginInfo = cache.get(pluginCode+'code')
    if not pluginInfo:
        import panelAuth
        pdata = panelAuth.panelAuth().create_serverid(None)
        pdata['pid'] = pluginCode
        url = GetConfigValue('home') + '/api/panel/get_py_module'
        pluginTmp = httpPost(url,pdata)
        try:
            pluginInfo = json.loads(pluginTmp)
        except:
            if not os.path.exists(p_tk): return False
            pluginInfo = json.loads(ReadFile(p_tk))
        if pluginInfo['status'] == False: return False
        WriteFile(p_tk,json.dumps(pluginInfo))
        os.chmod(p_tk,384)
        if cache: cache.set(pluginCode+'code',pluginInfo,1800)

    mod = sys.modules.setdefault(pluginCode, new_module(pluginCode))
    code = compile(pluginInfo['msg'].encode('utf-8'),pluginCode, 'exec')
    mod.__file__ = pluginCode
    mod.__package__ = ''
    exec(code, mod.__dict__)
    return mod

#解密数据
def auth_decode(data):
    token = GetToken()
    #是否有生成Token
    if not token: return returnMsg(False,'REQUEST_ERR')
    
    #校验access_key是否正确
    if token['access_key'] != data['btauth_key']: return returnMsg(False,'REQUEST_ERR')
    
    #解码数据
    import binascii,hashlib,urllib,hmac,json
    tdata = binascii.unhexlify(data['data']);
    
    #校验signature是否正确
    signature = binascii.hexlify(hmac.new(token['secret_key'], tdata, digestmod=hashlib.sha256).digest());
    if signature != data['signature']: return returnMsg(False,'REQUEST_ERR');
    
    #返回
    return json.loads(urllib.unquote(tdata));
    

#数据加密
def auth_encode(data):
    token = GetToken()
    pdata = {}
    
    #是否有生成Token
    if not token: return returnMsg(False,'REQUEST_ERR')
    
    #生成signature
    import binascii,hashlib,urllib,hmac,json
    tdata = urllib.quote(json.dumps(data));
    #公式  hex(hmac_sha256(data))
    pdata['signature'] = binascii.hexlify(hmac.new(token['secret_key'], tdata, digestmod=hashlib.sha256).digest());
    
    #加密数据
    pdata['btauth_key'] = token['access_key'];
    pdata['data'] = binascii.hexlify(tdata);
    pdata['timestamp'] = time.time()
    
    #返回
    return pdata;

#检查Token
def checkToken(get):
    tempFile = 'data/tempToken.json'
    if not os.path.exists(tempFile): return False
    import json,time
    tempToken = json.loads(readFile(tempFile))
    if time.time() > tempToken['timeout']: return False
    if get.token != tempToken['token']: return False
    return True;

#获取识别码
def get_uuid():
    import uuid
    return uuid.UUID(int=uuid.getnode()).hex[-12:]


#进程是否存在
def process_exists(pname,exe = None,cmdline = None):
    try:
        import psutil
        pids = psutil.pids()
        for pid in pids:
            try:
                p = psutil.Process(pid)
                if p.name() == pname: 
                    if not exe and not cmdline:
                        return True;
                    else:
                        if exe:
                            if p.exe() == exe: return True
                        if cmdline:
                            if cmdline in  p.cmdline(): return True
            except:pass
        return False
    except: return True


#重启面板
def restart_panel():
    import system
    return system.system().ReWeb(None)

#获取mac
def get_mac_address():
    import uuid
    mac=uuid.UUID(int = uuid.getnode()).hex[-12:]
    return ":".join([mac[e:e+2] for e in range(0,11,2)])


#转码
def to_string(lites):
    if type(lites) != list: lites = [lites]
    m_str = ''
    for mu in lites:
        if sys.version_info[0] == 2:
            m_str += unichr(mu).encode('utf-8')
        else:
            m_str += chr(mu)
    return m_str

#xss 防御
def xssencode(text):
    import cgi
    list=['`','~','&','#','/','*','$','@','<','>','\"','\'',';','%',',','.','\\u']
    ret=[]
    for i in text:
        if i in list:
            i=''
        ret.append(i)
    str_convert = ''.join(ret)
    text2=cgi.escape(str_convert, quote=True)
    return text2

# 取缓存
def cache_get(key):
    from BTPanel import cache
    return cache.get(key)

# 设置缓存
def cache_set(key,value,timeout = None):
    from BTPanel import cache
    return cache.set(key,value,timeout)

# 删除缓存
def cache_remove(key):
    from BTPanel import cache
    return cache.delete(key)

# 取session值
def sess_get(key):
    from BTPanel import session
    if key in session: return session[key]
    return None

# 设置或修改session值
def sess_set(key,value):
    from BTPanel import session
    session[key] = value
    return True

# 删除指定session值
def sess_remove(key):
    from BTPanel import session
    if key in session: del(session[key])
    return True

# 构造分页
def get_page(count,p=1,rows=12,callback='',result='1,2,3,4,5,8'):
    import page
    from BTPanel import request
    page = page.Page();
    info = { 'count':count,  'row':rows,  'p':p, 'return_js':callback ,'uri':request.full_path}
    data = { 'page': page.GetPage(info,result),  'shift': str(page.SHIFT), 'row': str(page.ROW) }
    return data

# 取面板版本
def version():
    try:
        from BTPanel import g
        return g.version
    except:
        comm = ReadFile('/www/server/panel/class/common.py')
        return re.search("g\.version\s*=\s*'(\d+\.\d+\.\d+)'",comm).groups()[0]


#取文件或目录大小
def get_path_size(path):
    if not os.path.exists(path): return 0;
    if not os.path.isdir(path): return os.path.getsize(path)
    size_total = 0
    for nf in os.walk(path):
        for f in nf[2]:
            filename = nf[0] + '/' + f
            if not os.path.exists(filename): continue;
            if os.path.islink(filename): continue;
            size_total += os.path.getsize(filename)
    return size_total

#写关键请求日志
def write_request_log(reques = None):
    try:
        log_path = '/www/server/panel/logs/request'
        log_file = getDate(format='%Y-%m-%d') + '.json'
        if not os.path.exists(log_path): os.makedirs(log_path)

        from flask import request
        log_data = []
        log_data.append(getDate())
        log_data.append(GetClientIp())
        log_data.append(request.method)
        log_data.append(request.full_path)
        log_data.append(request.headers.get('User-Agent'))
        WriteFile(log_path + '/' + log_file,json.dumps(log_data) + "\n",'a+')
    except: pass

#重载模块
def mod_reload(mode):
    if not mode: return False
    try:
        if sys.version_info[0] == 2:
            reload(mode)
        else:
            import imp
            imp.reload(mode)
        return True
    except: return False

#设置权限
def set_mode(filename,mode):
    if not os.path.exists(filename): return False
    mode = int(str(mode),8)
    os.chmod(filename,mode)
    return True


#设置用户组
def set_own(filename,user,group=None):
    if not os.path.exists(filename): return False
    from pwd import getpwnam
    try:
        user_info = getpwnam(user)
        user = user_info.pw_uid
        if group:
            user_info = getpwnam(group)
        group = user_info.pw_gid
    except:
        #如果指定用户或组不存在，则使用www
        user_info = getpwnam('www')
        user = user_info.pw_uid
        group = user_info.pw_gid
    os.chown(filename,user,group)
    return True

#校验路径安全
def path_safe_check(path):
    checks = ['..','./','\\','%','$','^','&','*','~','@','#']
    for c in checks:
        if path.find(c) != -1: return False
    rep = "^[\w\s\.\/-]+$"
    if not re.match(rep,path): return False
    return True

#取数据库字符集
def get_database_character(db_name):
    try:
        import panelMysql
        tmp = panelMysql.panelMysql().query("show create database `%s`" % db_name.strip())
        c_type = str(re.findall("SET\s+([\w\d-]+)\s",tmp[0][1])[0])
        c_types = ['utf8','utf-8','gbk','big5','utf8mb4']
        if not c_type.lower() in c_types: return 'utf8'
        return c_type
    except:
        return 'utf8'

def en_punycode(domain):
        tmp = domain.split('.');
        newdomain = '';
        for dkey in tmp:
            #匹配非ascii字符
            match = re.search(u"[\x80-\xff]+",dkey);
            if not match: match = re.search(u"[\u4e00-\u9fa5]+",dkey);
            if not match:
                newdomain += dkey + '.';
            else:
                newdomain += 'xn--' + dkey.encode('punycode').decode('utf-8') + '.'
        return newdomain[0:-1];

#punycode 转中文
def de_punycode(domain):
    tmp = domain.split('.');
    newdomain = '';
    for dkey in tmp:
        if dkey.find('xn--') >=0:
            newdomain += dkey.replace('xn--','').encode('utf-8').decode('punycode') + '.'
        else:
            newdomain += dkey + '.'
    return newdomain[0:-1];

#取计划任务文件路径
def get_cron_path():
    u_file = '/var/spool/cron/crontabs/root'
    if not os.path.exists(u_file):
        file='/var/spool/cron/root'
    else:
        file=u_file
    return file

#加密字符串
def en_crypt(key,strings):
    try:
        if type(strings) != bytes: strings = strings.encode('utf-8')
        from cryptography.fernet import Fernet
        f = Fernet(key)
        result = f.encrypt(strings)
        return result.decode('utf-8')
    except:
        #print(get_error_info())
        return strings

#解密字符串
def de_crypt(key,strings):
    try:
        if type(strings) != bytes: strings = strings.decode('utf-8')
        from cryptography.fernet import Fernet
        f = Fernet(key)
        result =  f.decrypt(strings).decode('utf-8')
        return result
    except:
        #print(get_error_info())
        return strings


#检查IP白名单
def check_ip_panel():
    ip_file = 'data/limitip.conf'
    if os.path.exists(ip_file):
        iplist = ReadFile(ip_file)
        if iplist:
            iplist = iplist.strip();
            if not GetClientIp() in iplist.split(','): 
                errorStr = ReadFile('./BTPanel/templates/' + GetConfigValue('template') + '/error2.html')
                try:
                    errorStr = errorStr.format(getMsg('PAGE_ERR_TITLE'),getMsg('PAGE_ERR_IP_H1'),getMsg('PAGE_ERR_IP_P1',(GetClientIp(),)),getMsg('PAGE_ERR_IP_P2'),getMsg('PAGE_ERR_IP_P3'),getMsg('NAME'),getMsg('PAGE_ERR_HELP'))
                except IndexError:pass
                return errorStr
    return False

#检查面板域名
def check_domain_panel():
    tmp = GetHost()
    domain = ReadFile('data/domain.conf')
    if domain:
        if tmp.strip().lower() != domain.strip().lower(): 
            errorStr = ReadFile('./BTPanel/templates/' + GetConfigValue('template') + '/error2.html')
            try:
                errorStr = errorStr.format(getMsg('PAGE_ERR_TITLE'),getMsg('PAGE_ERR_DOMAIN_H1'),getMsg('PAGE_ERR_DOMAIN_P1'),getMsg('PAGE_ERR_DOMAIN_P2'),getMsg('PAGE_ERR_DOMAIN_P3'),getMsg('NAME'),getMsg('PAGE_ERR_HELP'))
            except:pass
            return errorStr
    return False

#是否离线模式
def is_local():
    s_file = '/www/server/panel/data/not_network.pl'
    return os.path.exists(s_file)


#自动备份面板数据
def auto_backup_panel():
    panel_paeh = '/www/server/panel'
    paths = panel_paeh + '/data/not_auto_backup.pl'
    if os.path.exists(paths): return False
    b_path = '/www/backup/panel'
    backup_path = b_path + '/' + format_date('%Y-%m-%d')
    if os.path.exists(backup_path): return True
    if os.path.getsize(panel_paeh + '/data/default.db') > 104857600 * 2: return False
    os.makedirs(backup_path,384)
    import shutil
    shutil.copytree(panel_paeh + '/data',backup_path + '/data')
    shutil.copytree(panel_paeh + '/config',backup_path + '/config')
    time_now = time.time() - (86400 * 15)
    for f in os.listdir(b_path):
        try:
            if time.mktime(time.strptime(f, "%Y-%m-%d")) < time_now: 
                path = b_path + '/' + f
                if os.path.exists(path): shutil.rmtree(path)
        except: continue


#检查端口状态
def check_port_stat(port):
    import socket
    localIP = '127.0.0.1';
    temp = {}
    temp['port'] = port;
    temp['local'] = True;
    try:
        s = socket.socket()
        s.settimeout(0.15)
        s.connect((localIP,port))
        s.close()
    except:
        temp['local'] = False;
        
    result = 0;
    if temp['local']: result +=2;
    return result;


#同步时间
def sync_date():
    tip_file = "/dev/shm/last_sync_time.pl"
    s_time = int(time.time())
    try:
        if os.path.exists(tip_file):
            if s_time - int(readFile(tip_file)) < 60: return False
            os.remove(tip_file)
        time_str = HttpGet('http://www.bt.cn/api/index/get_time')
        new_time = int(time_str)
        time_arr = time.localtime(new_time)
        date_str = time.strftime("%Y-%m-%d %H:%M:%S", time_arr)
        os.system('date -s "%s"' % date_str)
        writeFile(tip_file,str(s_time))
        return True
    except: 
        if os.path.exists(tip_file): os.remove(tip_file)
        return False


#重载模块
def reload_mod(mod_name = None):
    #是否重载指定模块
    modules = []
    if mod_name:
        if type(mod_name) == str:
            mod_names = mod_name.split(',')
        
        for mod_name in mod_names:
            if mod_name in sys.modules:
                print(mod_name)
                try:
                    if sys.version_info[0] == 2:
                        reload(sys.modules[mod_name])
                    else:
                        importlib.reload(sys.modules[mod_name])
                    modules.append([mod_name,True])
                except:
                    modules.append([mod_name,False])
            else:
                modules.append([mod_name,False])
        return modules

    #重载所有模块
    for mod_name in sys.modules.keys():
        if mod_name in ['BTPanel']: continue
        f = getattr(sys.modules[mod_name],'__file__',None)
        if f:
            try:
                if f.find('panel/') == -1: continue
                if sys.version_info[0] == 2:
                    reload(sys.modules[mod_name])
                else:
                    importlib.reload(sys.modules[mod_name])
                modules.append([mod_name,True])
            except:
                modules.append([mod_name,False])
    return modules


def de_hexb(data):
    if sys.version_info[0] != 2:
        if type(data) == str: data = data.encode('utf-8')
    pdata = base64.b64encode(data);
    if sys.version_info[0] != 2:
        if type(pdata) == str: pdata = pdata.encode('utf-8')
    return binascii.hexlify(pdata);

def en_hexb(data):
    if sys.version_info[0] != 2:
        if type(data) == str: data = data.encode('utf-8')
    result = base64.b64decode(binascii.unhexlify(data));
    if type(result) != str: result = result.decode('utf-8')
    return result;

def upload_file_url(filename):
    try:
        if os.path.exists(filename):
            data = ExecShell('/usr/bin/curl https://scanner.baidu.com/enqueue -F archive=@%s' % filename)
            data = json.loads(data[0])
            time.sleep(1)
            import requests
            default_headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36'
            }
            data_list = requests.get(url=data['url'], headers=default_headers, verify=False)
            return (data_list.json())
        else:
            return False
    except:
        return False

#取通用对象
class dict_obj:
    def __contains__(self, key):
        return getattr(self,key,None)
    def __setitem__(self, key, value): setattr(self,key,value)
    def __getitem__(self, key): return getattr(self,key,None)
    def __delitem__(self,key): delattr(self,key)
    def __delattr__(self, key): delattr(self,key)
    def get_items(self): return self





