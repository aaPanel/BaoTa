#coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板 
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: hwliang <hwl@bt.cn>
# +-------------------------------------------------------------------

#--------------------------------
# 宝塔公共库
#--------------------------------

import json,os,sys,time,re,socket,importlib,binascii,base64,io,string
from random import choice
_LAN_PUBLIC = None
_LAN_LOG = None
_LAN_TEMPLATE = None

if sys.version_info[0] == 2:
    reload(sys)
    sys.setdefaultencoding('utf8')
else:
    from importlib import reload

def M(table):
    """
        @name 访问面板数据库
        @author hwliang<hwl@bt.cn>
        @table 被访问的表名(必需)
        @return db.Sql object

        ps: 默认访问data/default.db
    """
    import db
    with db.Sql() as sql:
        #sql = db.Sql()
        return sql.table(table)

def HttpGet(url,timeout = 6,headers = {}):
    """
        @name 发送GET请求
        @author hwliang<hwl@bt.cn>
        @url 被请求的URL地址(必需)
        @timeout 超时时间默认60秒
        @return string
    """
    if is_local(): return False
    home = 'www.bt.cn'
    host_home = 'data/home_host.pl'
    old_url = url
    if url.find(home) != -1:
        if os.path.exists(host_home): 
            headers['host'] = home
            url = url.replace(home,readFile(host_home))
    
    import http_requests
    res = http_requests.get(url,timeout=timeout,headers = headers)
    if res.status_code == 0:
        if old_url.find(home) != -1: return http_get_home(old_url,timeout,res.text)
        if headers: return False
        s_body = res.text
        return s_body
    s_body = res.text
    del res
    return s_body

def http_get_home(url,timeout,ex):
    """
        @name Get方式使用优选节点访问官网
        @author hwliang<hwl@bt.cn>
        @param url 当前官网URL地址
        @param timeout 用于测试超时时间
        @param ex 上一次错误的响应内容
        @return string 响应内容

        如果已经是优选节点，将直接返回ex
    """
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
    """
        @name 设置官网hosts
        @author hwliang<hwl@bt.cn>
        @param host IP地址
        @return void
    """
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

    import http_requests
    res = http_requests.post(url,data=data,timeout=timeout,headers = headers)
    if res.status_code == 0:
        if old_url.find(home) != -1: return http_post_home(old_url,data,timeout,res.text)
        if headers: return False
        s_body = res.text
        return s_body
    s_body = res.text
    return s_body
            

def http_post_home(url,data,timeout,ex):
    """
        @name POST方式使用优选节点访问官网
        @author hwliang<hwl@bt.cn>
        @param url(string) 当前官网URL地址
        @param data(dict) POST数据
        @param timeout(int) 用于测试超时时间
        @param ex(string) 上一次错误的响应内容
        @return string 响应内容

        如果已经是优选节点，将直接返回ex
    """
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
    """
        @name 发送POST请求
        @author hwliang<hwl@bt.cn>
        @param url 被请求的URL地址(必需)
        @param data POST参数，可以是字符串或字典(必需)
        @param timeout 超时时间默认60秒
        @return string
    """
    return HttpPost(url,data,timeout)

def check_home():
    return True

def Md5(strings):
    """
        @name 生成MD5
        @author hwliang<hwl@bt.cn>
        @param strings 要被处理的字符串
        @return string(32)
    """
    if type(strings) != bytes:
        strings = strings.encode()
    import hashlib
    m = hashlib.md5()
    m.update(strings)
    return m.hexdigest()

def md5(strings):
    return Md5(strings)

def FileMd5(filename):
    """
        @name 生成文件的MD5
        @author hwliang<hwl@bt.cn>
        @param filename 文件名
        @return string(32) or False
    """
    if not os.path.isfile(filename): return False
    import hashlib
    my_hash = hashlib.md5()
    f = open(filename,'rb')
    while True:
        b = f.read(8096)
        if not b :
            break
        my_hash.update(b)
    f.close()
    return my_hash.hexdigest()


def GetRandomString(length):
    """
       @name 取随机字符串
       @author hwliang<hwl@bt.cn>
       @param length 要获取的长度
       @return string(length)
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
        @name 取通用Json返回
        @author hwliang<hwl@bt.cn>
        @param status  返回状态
        @param msg  返回消息
        @return string(json)
    """
    return GetJson(ReturnMsg(status,msg,args))

def returnJson(status,msg,args=()):
    """
        @name 取通用Json返回
        @author hwliang<hwl@bt.cn>
        @param status  返回状态
        @param msg  返回消息
        @return string(json)
    """
    return ReturnJson(status,msg,args)

def ReturnMsg(status,msg,args = ()):
    """
        @name 取通用dict返回
        @author hwliang<hwl@bt.cn>
        @param status  返回状态
        @param msg  返回消息
        @return dict  {"status":bool,"msg":string}
    """
    log_message = json.loads(ReadFile('BTPanel/static/language/' + GetLanguage() + '/public.json'))
    keys = log_message.keys()
    if type(msg) == str:
        if msg in keys:
            msg = log_message[msg]
            for i in range(len(args)):
                rep = '{'+str(i+1)+'}'
                msg = msg.replace(rep,args[i])
    return {'status':status,'msg':msg}

def returnMsg(status,msg,args = ()):
    """
        @name 取通用dict返回
        @author hwliang<hwl@bt.cn>
        @param status  返回状态
        @param msg  返回消息
        @return dict  {"status":bool,"msg":string}
    """
    return ReturnMsg(status,msg,args)


def GetFileMode(filename):
    """
        @name 取文件权限字符串
        @author hwliang<hwl@bt.cn>
        @param filename  文件全路径
        @return string  如：644/777/755
    """
    stat = os.stat(filename)
    accept = str(oct(stat.st_mode)[-3:])
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
        return dumps(data,ensure_ascii=False)
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
                fp = open(filename, mode,encoding="utf-8")
                f_body = fp.read()
                fp.close()
            except Exception as ex2:
                return False
        else:
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
        fp = open(filename, mode)
        fp.write(s_body)
        fp.close()
        return True
    except:
        try:
            fp = open(filename, mode,encoding="utf-8")
            fp.write(s_body)
            fp.close()
            return True
        except:
            return False

def writeFile(filename,s_body,mode='w+'):
    return WriteFile(filename,s_body,mode)

def WriteLog(type,logMsg,args=(),not_web = False):
    #写日志
    #try:
    import time,db,json
    username = 'system'
    uid = 1
    tmp_msg = ''
    if not not_web:
        try:
            from BTPanel import session
            if 'username' in session:
                username = session['username']
                uid = session['uid']
                if session.get('debug') == 1: return
        except:
            pass
    global _LAN_LOG
    if not _LAN_LOG:
        _LAN_LOG = json.loads(ReadFile('BTPanel/static/language/' + GetLanguage() + '/log.json'))
    keys = _LAN_LOG.keys()
    if logMsg in keys:
        logMsg = _LAN_LOG[logMsg]
        for i in range(len(args)):
            rep = '{'+str(i+1)+'}'
            logMsg = logMsg.replace(rep,args[i])
    if type in keys: type = _LAN_LOG[type]
    sql = db.Sql()
    mDate = time.strftime('%Y-%m-%d %X',time.localtime())
    data = (uid,username,type,logMsg + tmp_msg,mDate)
    result = sql.table('logs').add('uid,username,type,log,addtime',data)
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
    global _LAN_TEMPLATE
    if not _LAN_TEMPLATE:
        _LAN_TEMPLATE = json.loads(ReadFile('BTPanel/static/language/' + GetLanguage() + '/template.json'))
    keys = _LAN_TEMPLATE.keys()
    msg = None
    if key in keys:
        msg = _LAN_TEMPLATE[key]
    return msg
def getLan(key):
    return GetLan(key)

def GetMsg(key,args = ()):
    try:
        global _LAN_PUBLIC
        if not _LAN_PUBLIC:
            _LAN_PUBLIC = json.loads(ReadFile('BTPanel/static/language/' + GetLanguage() + '/public.json'))
        keys = _LAN_PUBLIC.keys()
        msg = None
        if key in keys:
            msg = _LAN_PUBLIC[key]
            for i in range(len(args)):
                rep = '{'+str(i+1)+'}'
                msg = msg.replace(rep,args[i])
        return msg
    except:
        return key
def getMsg(key,args = ()):
    return GetMsg(key,args)


#获取Web服务器
def GetWebServer():
    if os.path.exists('/www/server/apache/bin/apachectl'):
        webserver = 'apache'
    elif os.path.exists('/usr/local/lsws/bin/lswsctrl'):
        webserver = 'openlitespeed'
    else:
        webserver = 'nginx'
    return webserver

def get_webserver():
    return GetWebServer()

def ServiceReload():
    #重载Web服务配置
    if os.path.exists('/www/server/nginx/sbin/nginx'):
        result = ExecShell('/etc/init.d/nginx reload')
        if result[1].find('nginx.pid') != -1:
            ExecShell('pkill -9 nginx && sleep 1')
            ExecShell('/etc/init.d/nginx start')
    elif os.path.exists('/www/server/apache/bin/apachectl'):
        result = ExecShell('/etc/init.d/httpd reload')
    else:
        result = ExecShell('rm -f /tmp/lshttpd/*.sock* && /usr/local/lsws/bin/lswsctrl restart')
    return result
def serviceReload():
    return ServiceReload()


def ExecShell(cmdstring, cwd=None, timeout=None, shell=True):
    a = ''
    e = ''
    import subprocess,tempfile
    
    try:
        rx = md5(cmdstring)
        succ_f = tempfile.SpooledTemporaryFile(max_size=4096,mode='wb+',suffix='_succ',prefix='btex_' + rx ,dir='/dev/shm')
        err_f = tempfile.SpooledTemporaryFile(max_size=4096,mode='wb+',suffix='_err',prefix='btex_' + rx ,dir='/dev/shm')
        sub = subprocess.Popen(cmdstring, close_fds=True, shell=shell,bufsize=128,stdout=succ_f,stderr=err_f)
        sub.wait()
        err_f.seek(0)
        succ_f.seek(0)
        a = succ_f.read()
        e = err_f.read()
        if not err_f.closed: err_f.close()
        if not succ_f.closed: succ_f.close()
    except:
        print(get_error_info())
    try:
        #编码修正
        if type(a) == bytes: a = a.decode('utf-8')
        if type(e) == bytes: e = e.decode('utf-8')
    except:pass

    return a,e

def GetLocalIp():
    #取本地外网IP    
    try:
        filename = 'data/iplist.txt'
        ipaddress = readFile(filename)
        if not ipaddress:
            url = 'http://pv.sohu.com/cityjson?ie=utf-8'
            m_str = HttpGet(url)
            ipaddress = re.search(r'\d+.\d+.\d+.\d+',m_str).group(0)
            WriteFile(filename,ipaddress)
        c_ip = check_ip(ipaddress)
        if not c_ip: return GetHost()
        return ipaddress
    except:
        try:
            url = GetConfigValue('home') + '/Api/getIpAddress'
            return HttpGet(url)
        except:
            return GetHost()

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
            tmp = re.findall(r"(https|http)://([\w:\.-]+)",request.url_root)
            if tmp: host_tmp = tmp[0][1]
    if not host_tmp:
        host_tmp = GetLocalIp() + ':' + readFile('data/port.pl').strip()
    try:
        if host_tmp.find(':') == -1: host_tmp += ':80'
    except:
        host_tmp = "127.0.0.1:8888"
    h = host_tmp.split(':')
    if port: return h[-1]
    return ':'.join(h[0:-1])

def GetClientIp():
    from flask import request
    return request.remote_addr.replace('::ffff:','')

def phpReload(version):
    #重载PHP配置
    import os
    if os.path.exists('/www/server/php/' + version + '/libphp5.so'):
        ExecShell('/etc/init.d/httpd reload')
    else:
        ExecShell('/etc/init.d/php-fpm-'+version+' reload')

def get_timeout(url,timeout=3):
    try:
        start = time.time()
        result = int(httpGet(url,timeout))
        return result,int((time.time() - start) * 1000 - 500)
    except: return 0,False

def get_url(timeout = 0.5):
    import json
    try:
        pkey = 'node_url'
        node_url =  cache_get(pkey)
        if node_url: return node_url
        nodeFile = 'data/node.json'
        node_list = json.loads(readFile(nodeFile))
        mnode1 = []
        mnode2 = []
        mnode3 = []
        new_node_list = {}
        for node in node_list:
            node['net'],node['ping'] = get_timeout(node['protocol'] + node['address'] + ':' + node['port'] + '/net_test',1)
            new_node_list[node['address']] = node['ping']
            if not node['ping']: continue
            if node['ping'] < 100:      #当响应时间<100ms且可用带宽大于1500KB时
                if node['net'] > 1500:
                    mnode1.append(node)
                elif node['net'] > 1000:
                    mnode3.append(node)
            else:
                if node['net'] > 1000:  #当响应时间>=100ms且可用带宽大于1000KB时
                    mnode2.append(node)
            if node['ping'] < 100:
                if node['net'] > 3000: break #有节点可用带宽大于3000时，不再检查其它节点
        if mnode1: #优选低延迟高带宽
            mnode = sorted(mnode1,key= lambda  x:x['net'],reverse=True)
        elif mnode3: #备选低延迟，中等带宽
            mnode = sorted(mnode3,key= lambda  x:x['net'],reverse=True)
        else: #终选中等延迟，中等带宽
            mnode = sorted(mnode2,key= lambda  x:x['ping'],reverse=False)
        
        if not mnode: return 'http://download.bt.cn'

        new_node_keys = new_node_list.keys()
        for i in range(len(node_list)):
            if node_list[i]['address'] in new_node_keys:
                node_list[i]['ping'] = new_node_list[node_list[i]['address']]
            else:
                node_list[i]['ping'] = 500

        new_node_list = sorted(node_list,key=lambda x: x['ping'],reverse=False)
        writeFile(nodeFile,json.dumps(new_node_list))
        node_url = mnode[0]['protocol'] + mnode[0]['address'] + ':' + mnode[0]['port']
        cache_set(pkey,node_url,86400)
        return node_url
    except:
        return 'http://download.bt.cn'


#过滤输入
def checkInput(data):
   if not data: return data
   if type(data) != str: return data
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
       data = data.replace(v['d'],v['r'])
   return data

#取文件指定尾行数
def GetNumLines(path,num,p=1):
    pyVersion = sys.version_info[0]
    max_len = 1024*128
    try:
        import cgi
        if not os.path.exists(path): return ""
        start_line = (p - 1) * num
        count = start_line + num
        fp = open(path,'r')
        buf = ""
        fp.seek(-1, 2)
        if fp.read(1) == "\n": fp.seek(-1, 2)
        data = []
        total_len = 0
        b = True
        n = 0
        for i in range(count):
            while True:
                newline_pos = str.rfind(str(buf), "\n")
                pos = fp.tell()
                if newline_pos != -1:
                    if n >= start_line:
                        line = buf[newline_pos + 1:]
                        line_len = len(line)
                        total_len += line_len
                        sp_len = total_len - max_len
                        if sp_len > 0:
                            line = line[sp_len:]
                        try:
                            data.insert(0,cgi.escape(line))
                        except: pass
                    buf = buf[:newline_pos]
                    n += 1
                    break
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
                if total_len >= max_len: break
            if not b: break
        fp.close()
        result = "\n".join(data)
        if not result: raise Exception('null')
    except:
        result = ExecShell("tail -n {} {}".format(num,path))[0]
        if len(result) > max_len:
            result = result[-max_len:]

    try:
        try:
            result = json.dumps(result)
            return json.loads(result).strip()
        except:
            if pyVersion == 2:
                result = result.decode('utf8',errors='ignore')
            else:
                result = result.encode('utf-8',errors='ignore').decode("utf-8",errors="ignore")
        return result.strip()
    except: return ""

#验证证书
def CheckCert(certPath = 'ssl/certificate.pem'):
    openssl = '/usr/local/openssl/bin/openssl'
    if not os.path.exists(openssl): openssl = 'openssl'
    certPem = readFile(certPath)
    s = "\n-----BEGIN CERTIFICATE-----"
    tmp = certPem.strip().split(s)
    for tmp1 in tmp:
        if tmp1.find('-----BEGIN CERTIFICATE-----') == -1:  tmp1 = s + tmp1
        writeFile(certPath,tmp1)
        result = ExecShell(openssl + " x509 -in "+certPath+" -noout -subject")
        if result[1].find('-bash:') != -1: return True
        if len(result[1]) > 2: return False
        if result[0].find('error:') != -1: return False
    return True


# 获取面板地址
def getPanelAddr():
    from flask import request
    protocol = 'https://' if os.path.exists("data/ssl.pl") else 'http://'
    return protocol + request.headers.get('host')


#字节单位转换
def to_size(size):
    if not size: return '0.00 b'
    size = float(size)
    d = ('b','KB','MB','GB','TB')
    s = d[0]
    for b in d:
        if size < 1024: return ("%.2f" % size) + ' ' + b
        size = size / 1024
        s = b
    return ("%.2f" % size) + ' ' + b


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
        progress = int((100.0 * used / total))
        data = {'title':title,'progress':progress,'total':total,'used':used,'speed':speed}
    writeFile('/tmp/panelSpeed.pl',json.dumps(data))
    return True

#取进度
def getSpeed():
    import json;
    data = readFile('/tmp/panelSpeed.pl')
    if not data: 
        data = json.dumps({'title':None,'progress':0,'total':0,'used':0,'speed':0})
        writeFile('/tmp/panelSpeed.pl',data)
    return json.loads(data)

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
    errorMsg = traceback.format_exc()
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
    # if not os.path.exists(f2 + 'btwaf_httpd'):
    #     f3 = f1 + 'apache/btwaf.conf'
    #     if os.path.exists(f3): os.remove(f3)

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
        result = ExecShell("ulimit -n 8192 ; /www/server/nginx/sbin/nginx -t -c /www/server/nginx/conf/nginx.conf")
        searchStr = 'successful'
    elif get_webserver() == 'apache':
    # else:
        result = ExecShell("ulimit -n 8192 ; /www/server/apache/bin/apachectl -t")
        searchStr = 'Syntax OK'
    else:
        result = ["1","1"]
        searchStr = "1"
    if result[1].find(searchStr) == -1:
        WriteLog("TYPE_SOFT", 'CONF_CHECK_ERR',(result[1],))
        return result[1]
    return True


#检查是否为IPv4地址
def checkIp(ip):
    p = re.compile(r'^((25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(25[0-5]|2[0-4]\d|[01]?\d\d?)$')  
    if p.match(ip):  
        return True  
    else:  
        return False
    
#检查端口是否合法
def checkPort(port):
    if not re.match("^\d+$",port): return False
    ports = ['21','25','443','8080','888','8888','8443']
    if port in ports: return False
    intport = int(port)
    if intport < 1 or intport > 65535: return False
    return True

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
    tmp = re.search(rep,cpuinfo,re.I)
    cpuType = ''
    if tmp:
        cpuType = tmp.groups()[0]
    else:
        cpuinfo = ExecShell('LANG="en_US.UTF-8" && lscpu')[0]
        rep = "Model\s+name:\s+(.+)"
        tmp = re.search(rep,cpuinfo,re.I)
        if tmp: cpuType = tmp.groups()[0]
    return cpuType


#检查是否允许重启
def IsRestart():
    num  = M('tasks').where('status!=?',('1',)).count()
    if num > 0: return False
    return True

#加密密码字符
def hasPwd(password):
    import crypt;
    return crypt.crypt(password,password)

def getDate(format='%Y-%m-%d %X'):
    #取格式时间
    return time.strftime(format,time.localtime())


#处理MySQL配置文件
def CheckMyCnf():
    import os;
    confFile = '/etc/my.cnf'
    if os.path.exists(confFile): 
        conf = readFile(confFile)
        if conf.find('[mysqld]') != -1: return True
    versionFile = '/www/server/mysql/version.pl'
    if not os.path.exists(versionFile): return False
    
    versions = ['5.1','5.5','5.6','5.7','8.0','AliSQL']
    version = readFile(versionFile)
    for key in versions:
        if key in version:
            version = key
            break
    
    shellStr = '''
#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH

CN='dg2.bt.cn'
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
chmod 644 /etc/my.cnf
MySQL_Opt
''' % (version,)
    ExecShell(shellStr)
    #判断是否迁移目录
    if os.path.exists('data/datadir.pl'):
        newPath = readFile('data/datadir.pl')
        if os.path.exists(newPath):
            mycnf = readFile('/etc/my.cnf')
            mycnf = mycnf.replace('/www/server/data',newPath)
            writeFile('/etc/my.cnf',mycnf)
    WriteLog('TYPE_SOFE', 'MYSQL_CHECK_ERR')
    return True


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
        panelsys = system.system()
        version = panelsys.GetSystemVersion()
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
        tokenFile = 'data/token.json'
        if not os.path.exists(tokenFile): return False
        token = loads(readFile(tokenFile))
        return token
    except:
        return False

def to_btint(string):
    m_list = []
    for s in string:
        m_list.append(ord(s))
    return m_list

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
    tdata = binascii.unhexlify(data['data'])
    
    #校验signature是否正确
    signature = binascii.hexlify(hmac.new(token['secret_key'], tdata, digestmod=hashlib.sha256).digest())
    if signature != data['signature']: return returnMsg(False,'REQUEST_ERR')
    
    #返回
    return json.loads(urllib.unquote(tdata))
    

#数据加密
def auth_encode(data):
    token = GetToken()
    pdata = {}
    
    #是否有生成Token
    if not token: return returnMsg(False,'REQUEST_ERR')
    
    #生成signature
    import binascii,hashlib,urllib,hmac,json
    tdata = urllib.quote(json.dumps(data))
    #公式  hex(hmac_sha256(data))
    pdata['signature'] = binascii.hexlify(hmac.new(token['secret_key'], tdata, digestmod=hashlib.sha256).digest())
    
    #加密数据
    pdata['btauth_key'] = token['access_key']
    pdata['data'] = binascii.hexlify(tdata)
    pdata['timestamp'] = time.time()
    
    #返回
    return pdata

#检查Token
def checkToken(get):
    tempFile = 'data/tempToken.json'
    if not os.path.exists(tempFile): return False
    import json,time
    tempToken = json.loads(readFile(tempFile))
    if time.time() > tempToken['timeout']: return False
    if get.token != tempToken['token']: return False
    return True

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
                        return True
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

#解码
def to_ord(string):
    o  = []
    for s in string:
        o.append(ord(s))
    return o

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
    page = page.Page()
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
    if not os.path.exists(path): return 0
    if not os.path.isdir(path): return os.path.getsize(path)
    size_total = 0
    for nf in os.walk(path):
        for f in nf[2]:
            filename = nf[0] + '/' + f
            if not os.path.exists(filename): continue
            if os.path.islink(filename): continue
            size_total += os.path.getsize(filename)
    return size_total

#写关键请求日志
def write_request_log(reques = None):
    try:
        from BTPanel import request,g,session
        if session.get('debug') == 1: return
        if request.path in ['/service_status','/favicon.ico','/task','/system','/ajax','/control','/data','/ssl']:
            return False

        log_path = '/www/server/panel/logs/request'
        log_file = getDate(format='%Y-%m-%d') + '.json'
        if not os.path.exists(log_path): os.makedirs(log_path)
        
        log_data = []
        log_data.append(getDate())
        log_data.append(GetClientIp() + ':' + str(request.environ.get('REMOTE_PORT')))
        log_data.append(request.method)
        log_data.append(request.full_path)
        log_data.append(request.headers.get('User-Agent'))
        if request.method == 'POST':
            args = str(request.form.to_dict())
            if len(args) < 2048 and args.find('pass') == -1 and args.find('user') == -1:
                log_data.append(args)
            else:
                log_data.append('{}')
        else:
            log_data.append('{}')
        log_data.append(int((time.time() - g.request_time) * 1000))
        WriteFile(log_path + '/' + log_file,json.dumps(log_data) + "\n",'a+')
        rep_sys_path()
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
def path_safe_check(path,force=True):
    if len(path) > 256: return False 
    checks = ['..','./','\\','%','$','^','&','*','~','"',"'",';','|','{','}','`']
    for c in checks:
        if path.find(c) != -1: return False
    if force:
        rep = r"^[\w\s\.\/-]+$"
        if not re.match(rep,path): return False
    return True

#取数据库字符集
def get_database_character(db_name):
    try:
        import panelMysql
        tmp = panelMysql.panelMysql().query("show create database `%s`" % db_name.strip())
        c_type = str(re.findall(r"SET\s+([\w\d-]+)\s",tmp[0][1])[0])
        c_types = ['utf8','utf-8','gbk','big5','utf8mb4']
        if not c_type.lower() in c_types: return 'utf8'
        return c_type
    except:
        return 'utf8'

def en_punycode(domain):
    if sys.version_info[0] == 2: 
        domain = domain.encode('utf8')
    tmp = domain.split('.')
    newdomain = ''
    for dkey in tmp:
        if dkey == '*': continue
        #匹配非ascii字符
        match = re.search(u"[\x80-\xff]+",dkey)
        if not match: match = re.search(u"[\u4e00-\u9fa5]+",dkey)
        if not match:
            newdomain += dkey + '.'
        else:
            if sys.version_info[0] == 2:
                newdomain += 'xn--' + dkey.decode('utf-8').encode('punycode') + '.'
            else:
                newdomain += 'xn--' + dkey.encode('punycode').decode('utf-8') + '.'
    if tmp[0] == '*': newdomain = "*." + newdomain
    return newdomain[0:-1]



#punycode 转中文
def de_punycode(domain):
    tmp = domain.split('.')
    newdomain = ''
    for dkey in tmp:
        if dkey.find('xn--') >=0:
            newdomain += dkey.replace('xn--','').encode('utf-8').decode('punycode') + '.'
        else:
            newdomain += dkey + '.'
    return newdomain[0:-1]

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
            iplist = iplist.strip()
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
    try:
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
        shutil.copytree(panel_paeh + '/vhost',backup_path + '/vhost')
        ExecShell("chmod -R 600 {path};chown -R root.root {path}".format(paht=b_path))
        time_now = time.time() - (86400 * 15)
        for f in os.listdir(b_path):
            try:
                if time.mktime(time.strptime(f, "%Y-%m-%d")) < time_now: 
                    path = b_path + '/' + f
                    if os.path.exists(path): shutil.rmtree(path)
            except: continue
    except:pass


#检查端口状态
def check_port_stat(port,localIP = '127.0.0.1'):
    import socket
    temp = {}
    temp['port'] = port
    temp['local'] = True
    try:
        s = socket.socket()
        s.settimeout(0.15)
        s.connect((localIP,port))
        s.close()
    except:
        temp['local'] = False
        
    result = 0
    if temp['local']: result +=2
    return result


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
        ExecShell('date -s "%s"' % date_str)
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
    pdata = base64.b64encode(data)
    if sys.version_info[0] != 2:
        if type(pdata) == str: pdata = pdata.encode('utf-8')
    return binascii.hexlify(pdata)

def en_hexb(data):
    if sys.version_info[0] != 2:
        if type(data) == str: data = data.encode('utf-8')
    result = base64.b64decode(binascii.unhexlify(data))
    if type(result) != str: result = result.decode('utf-8')
    return result

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

#直接请求到PHP-FPM
#version php版本
#uri 请求uri
#filename 要执行的php文件
#args 请求参数
#method 请求方式
def request_php(version,uri,document_root,method='GET',pdata=b''):
    import panelPHP
    if type(pdata) == dict: pdata = url_encode(pdata)
    fpm_address = get_fpm_address(version)
    p = panelPHP.FPM(fpm_address,document_root)
    result = p.load_url_public(uri,pdata,method)
    return result


def get_fpm_address(php_version):
    '''
        @name 获取FPM请求地址
        @author hwliang<2020-10-23>
        @param php_version string PHP版本
        @return tuple or string
    '''
    fpm_address = '/tmp/php-cgi-{}.sock'.format(php_version)
    php_fpm_file = '/www/server/php/{}/etc/php-fpm.conf'.format(php_version)
    try:
        fpm_conf = readFile(php_fpm_file)
        tmp = re.findall(r"listen\s*=\s*(.+)",fpm_conf)
        if not tmp: return fpm_address
        if tmp[0].find('sock') != -1: return fpm_address
        if tmp[0].find(':') != -1:
            listen_tmp = tmp[0].split(':')
            fpm_address = ('127.0.0.1',int(listen_tmp[1]))
        else:
            fpm_address = ('127.0.0.1',int(tmp[0]))
        return fpm_address
    except:
        return fpm_address


def get_php_proxy(php_version,webserver = 'nginx'):
    '''
        @name 获取PHP代理地址
        @author hwliang<2020-10-24>
        @param php_version string php版本  (52|53|54|55|56|70|71|72|73|74)
        @param webserver string web服务器类型 (nginx|apache|ols)
        return string
    '''
    php_address = get_fpm_address(php_version)
    if isinstance(php_address,str):
        if webserver == 'nginx':
            return 'unix:{}'.format(php_address)
        elif webserver == 'apache':
            return 'unix:{}|fcgi://localhost'.format(php_address)
    else:
        if webserver == 'nginx':
            return '{}:{}'.format(php_address[0],php_address[1])
        elif webserver == 'apache':
            return 'fcgi://{}:{}'.format(php_address[0],php_address[1])

def get_php_version_conf(conf):
    '''
        @name 从指定配置文件获取PHP版本
        @author hwliang<2020-10-24>
        @param conf string 配置文件内容
        @return string
    '''
    if not conf: return '00'
    if conf.find('enable-php-') != -1:
        rep = r"enable-php-([0-9]{2,3})\.conf"
        tmp = re.findall(rep,conf)
        if not tmp: return '00'
    elif conf.find('/usr/local/lsws/lsphp') != -1:
        rep = r"path\s*/usr/local/lsws/lsphp(\d+)/bin/lsphp"
        tmp = re.findall(rep,conf)
        if not tmp: return '00'
    else:
        rep = r"php-cgi-([0-9]{2,3})\.sock"
        tmp = re.findall(rep,conf)
        if not tmp:
            rep = r'127.0.0.1:10(\d{2,2})1'
            tmp = re.findall(rep,conf)
            if not tmp:
                return '00'
    return tmp[0]


def get_site_php_version(siteName):
    '''
        @name 获取指定网站当前使用的PHP版本
        @author hwliang<2020-10-24>
        @param siteName string 网站名称
        @return string
    '''
    web_server = get_webserver()
    conf = readFile('/www/server/panel/vhost/'+web_server+'/'+siteName+'.conf')
    if web_server == 'openlitespeed':
        conf = readFile('/www/server/panel/vhost/' + web_server + '/detail/' + siteName + '.conf')
    return get_php_version_conf(conf)


def sub_php_address(conf_file,rep,tsub,php_version):
    '''
        @name 替换新的PHP配置到配置文件
        @author hwliang<2020-10-24>
        @param conf_file string 配置文件全路径
        @param rep string 用于查找目标替换内容的正则表达式
        @param tsub string 新的内容
        @param php_version string 指定PHP版本
        @return bool
    '''
    if not os.path.exists(conf_file): return False
    conf = readFile(conf_file)
    if not conf: return False
    #if conf.find('#PHP') == -1 and conf.find('pathinfo.conf') == -1: return False
    phpv = get_php_version_conf(conf)
    if phpv != php_version: return False
    tmp = re.search(rep,conf)
    if not tmp: return False
    if tmp.group() == tsub: return False
    conf = conf.replace(tmp.group(),tsub) #re.sub(rep,php_proxy,conf)
    writeFile(conf_file,conf)
    return True


def sync_all_address():
    '''
        @name 同步所有PHP版本配置到配置文件
        @author hwliang<2020-10-24>
        @return void
    '''
    php_versions = ['52','53','54','55','56','70','71','72','73','74','75','80','81']
    for phpv in php_versions:
        sync_php_address(phpv)

def sync_php_address(php_version):
    '''
        @name 同步PHP版本配置到所有配置文件
        @author hwliang<2020-10-24>
        @param php_version string PHP版本
        @return void
    '''
    if not os.path.exists('/www/server/php/{}/bin/php'.format(php_version)): # 指定PHP版本是否安装
        return False
    ngx_rep = r"(unix:/tmp/php-cgi.*\.sock|127.0.0.1:\d+)"
    apa_rep = r"(unix:/tmp/php-cgi.*\.sock\|fcgi://localhost|fcgi://127.0.0.1:\d+)"
    ngx_proxy = get_php_proxy(php_version,'nginx')
    apa_proxy = get_php_proxy(php_version,'apache')
    is_write = False

    #nginx的PHP配置文件
    nginx_conf_path = '/www/server/nginx/conf'
    
    if os.path.exists(nginx_conf_path):
        for f_name in os.listdir(nginx_conf_path):
            if f_name.find('enable-php') != -1:
                conf_file = '/'.join((nginx_conf_path,f_name))
                if sub_php_address(conf_file,ngx_rep,ngx_proxy,php_version):
                    is_write = True
    #nginx的phpmyadmin
    # conf_file = '/www/server/nginx/conf/nginx.conf'
    # if os.path.exists(conf_file):
    #     if sub_php_address(conf_file,ngx_rep,ngx_proxy,php_version):
    #         is_write = True
    
    #apache的网站配置文件
    apache_conf_path = '/www/server/panel/vhost/apache'
    if os.path.exists(apache_conf_path):
        for f_name in os.listdir(apache_conf_path):
            conf_file = '/'.join((apache_conf_path,f_name))
            if sub_php_address(conf_file,apa_rep,apa_proxy,php_version):
                is_write = True
    #apache的phpmyadmin
    conf_file = '/www/server/apache/conf/extra/httpd-vhosts.conf'
    if os.path.exists(conf_file):
        if sub_php_address(conf_file,apa_rep,apa_proxy,php_version):
            is_write = True
    
    if is_write: serviceReload()
    return True




def url_encode(data):
    if type(data) == str: return data
    import urllib
    if sys.version_info[0] != 2:
        pdata = urllib.parse.urlencode(data).encode('utf-8')
    else:
        pdata = urllib.urlencode(data)
    return pdata

def url_decode(data):
    if type(data) == str: return data
    import urllib
    if sys.version_info[0] != 2:
        pdata = urllib.parse.urldecode(data).encode('utf-8')
    else:
        pdata = urllib.urldecode(data)
    return pdata


def unicode_encode(data):
    try:
        if sys.version_info[0] == 2:
            result = unicode(data,errors='ignore')
        else:
            result = data.encode('utf8',errors='ignore')
        return result
    except: return data

def unicode_decode(data,charset = 'utf8'):
    try:
        if sys.version_info[0] == 2:
            result = unicode(data,errors='ignore')
        else:
            result = data.decode('utf8',errors='ignore')
        return result
    except: return data

def import_cdn_plugin():
    plugin_path = 'plugin/static_cdn'
    if not os.path.exists(plugin_path): return True
    try:
        import static_cdn_main
    except:
        package_path_append(plugin_path)
        import static_cdn_main
    

def get_cdn_hosts():
    try:
        if import_cdn_plugin(): return []
        import static_cdn_main
        return static_cdn_main.static_cdn_main().get_hosts(None)
    except:
        return []

def get_cdn_url():
    try:
        if os.path.exists('plugin/static_cdn/not_open.pl'):
            return False
        from BTPanel import cache
        cdn_url = cache.get('cdn_url')
        if cdn_url: return cdn_url
        if import_cdn_plugin(): return False
        import static_cdn_main
        cdn_url = static_cdn_main.static_cdn_main().get_url(None)
        cache.set('cdn_url',cdn_url,3)
        return cdn_url
    except:
        return False

def set_cdn_url(cdn_url):
    if not cdn_url: return False
    import_cdn_plugin()
    get = dict_obj()
    get.cdn_url = cdn_url
    import static_cdn_main
    static_cdn_main.static_cdn_main().set_url(get)
    return True

def get_python_bin():
    bin_file = '/www/server/panel/pyenv/bin/python'
    if os.path.exists(bin_file):
        return bin_file
    return '/usr/bin/python'

def aes_encrypt(data,key):
    import panelAes
    if sys.version_info[0] == 2:
        aes_obj = panelAes.aescrypt_py2(key)
        return aes_obj.aesencrypt(data)
    else:
        aes_obj = panelAes.aescrypt_py3(key)
        return aes_obj.aesencrypt(data)

def aes_decrypt(data,key):
    import panelAes
    if sys.version_info[0] == 2:
        aes_obj = panelAes.aescrypt_py2(key)
        return aes_obj.aesdecrypt(data)
    else:
        aes_obj = panelAes.aescrypt_py3(key)
        return aes_obj.aesdecrypt(data)

#清理大日志文件
def clean_max_log(log_file,max_size = 100,old_line = 100):
    if not os.path.exists(log_file): return False
    max_size = 1024 * 1024 * max_size
    if os.path.getsize(log_file) > max_size:
        try:
            old_body = GetNumLines(log_file,old_line)
            writeFile(log_file,old_body)
        except:
            print(get_error_info())

#获取证书哈希
def get_cert_data(path):
    import panelSSL
    get = dict_obj()
    get.certPath = path
    data = panelSSL.panelSSL().GetCertName(get)
    return data

# 获取系统发行版
def get_linux_distribution():
    distribution = 'ubuntu'
    redhat_file = '/etc/redhat-release'
    if os.path.exists(redhat_file):
        try:
            tmp = readFile(redhat_file).split()[3][0]
            if int(tmp) > 7:
                distribution = 'centos8'
        except:
            distribution = 'centos7'
    return distribution

def long2ip(ips):
    '''
        @name 将整数转换为IP地址
        @author hwliang<2020-06-11>
        @param ips string(ip地址整数)
        @return ipv4
    '''
    i1 = int(ips / (2 ** 24))
    i2 = int((ips - i1 * ( 2 ** 24 )) / ( 2 ** 16 ))
    i3 = int(((ips - i1 * ( 2 ** 24 )) - i2 * ( 2 ** 16 )) / ( 2 ** 8))
    i4 = int(((ips - i1 * ( 2 ** 24 )) - i2 * ( 2 ** 16 )) - i3 * ( 2 ** 8))
    return "{}.{}.{}.{}".format(i1,i2,i3,i4)

def ip2long(ip):
    '''
        @name 将IP地址转换为整数
        @author hwliang<2020-06-11>
        @param ip string(ipv4)
        @return long
    '''
    ips = ip.split('.')
    if len(ips) != 4: return 0
    iplong = 2 ** 24 * int(ips[0]) + 2 ** 16 * int(ips[1])  + 2 ** 8 * int(ips[2])  + int(ips[3])
    return iplong

#提交关键词
def submit_keyword(keyword):
    pdata = {"keyword":keyword}
    httpPost(GetConfigValue('home') + '/api/panel/total_keyword',pdata)

#统计关键词
def total_keyword(keyword):
    import threading
    p = threading.Thread(target=submit_keyword,args=(keyword,))
    p.setDaemon(True)
    p.start()

#获取debug日志
def get_debug_log():
    from BTPanel import request
    return GetClientIp() +':'+ str(request.environ.get('REMOTE_PORT')) + '|' + str(int(time.time())) + '|' + get_error_info()

#获取sessionid
def get_session_id():
    from BTPanel import request
    session_id =  request.cookies.get('SESSIONID','')
    return session_id

#尝试自动恢复面板数据库
def rep_default_db():
    db_path = '/www/server/panel/data/'
    db_file = db_path + 'default.db'
    db_tmp_backup = db_path + 'default_' + format_date("%Y%m%d_%H%M%S") + ".db"

    panel_backup = '/www/backup/panel'
    bak_list = os.listdir(panel_backup)
    if not bak_list: return False
    bak_list = sorted(bak_list,reverse=True)
    db_bak_file = ''
    for d_name in bak_list:
        db_bak_file = panel_backup + '/' + d_name + '/data/default.db'
        if not os.path.exists(db_bak_file): continue
        if os.path.getsize(db_bak_file) < 17408: continue
        break

    if not db_bak_file: return False
    ExecShell("\cp -arf {} {}".format(db_file,db_tmp_backup))
    ExecShell("\cp -arf {} {}".format(db_bak_file,db_file))
    return True
    
    

def chdck_salt():
    '''
        @name 检查所有用户密码是否加盐，若没有则自动加上
        @author hwliang<2020-07-08>
        @return void
    '''

    if not M('sqlite_master').where('type=? AND name=? AND sql LIKE ?', ('table', 'users','%salt%')).count():
        M('users').execute("ALTER TABLE 'users' ADD 'salt' TEXT",())
    u_list = M('users').where('salt is NULL',()).field('id,username,password,salt').select()
    if isinstance(u_list,str):
        if u_list.find('no such table: users') != -1:
            rep_default_db()
            if not M('sqlite_master').where('type=? AND name=? AND sql LIKE ?', ('table', 'users','%salt%')).count():
                M('users').execute("ALTER TABLE 'users' ADD 'salt' TEXT",())
            u_list = M('users').where('salt is NULL',()).field('id,username,password,salt').select()

    for u_info in u_list:
        salt = GetRandomString(12) #12位随机
        pdata = {}
        pdata['password'] = md5(md5(u_info['password']+'_bt.cn') + salt)
        pdata['salt'] = salt
        M('users').where('id=?',(u_info['id'],)).update(pdata)


def get_login_token():
    token_s = readFile('/www/server/panel/data/login_token.pl')
    if not token_s: return GetRandomString(32)
    return token_s

def get_sess_key():
    from BTPanel import session
    return md5(get_login_token() + session.get('request_token_head',''))


def password_salt(password,username=None,uid=None):
    '''
        @name 为指定密码加盐
        @author hwliang<2020-07-08>
        @param password string(被md5加密一次的密码)
        @param username string(用户名) 可选
        @param uid int(uid) 可选
        @return string
    '''
    chdck_salt()
    if not uid:
        if not username:
            raise Exception('username或uid必需传一项')
        uid = M('users').where('username=?',(username,)).getField('id')
    salt = M('users').where('id=?',(uid,)).getField('salt')
    return md5(md5(password+'_bt.cn')+salt)

def package_path_append(path):
    if not path in sys.path:
        sys.path.insert(0,path)
    

def rep_sys_path():
    sys_path = []
    for p in sys.path:
        if p in sys_path: continue
        sys_path.append(p)
    sys.path = sys_path


def get_ssh_port():
    '''
        @name 获取本机SSH端口
        @author hwliang<2020-08-07>
        @return int
    '''
    s_file = '/etc/ssh/sshd_config'
    conf = readFile(s_file)
    if not conf: conf = ''
    rep = r"#*Port\s+([0-9]+)\s*\n"
    tmp1 = re.search(rep,conf)
    ssh_port = 22
    if tmp1:
        ssh_port = int(tmp1.groups(0)[0])
    return ssh_port

def set_error_num(key,empty = False,expire=3600):
    '''
        @name 设置失败次数(每调用一次+1)
        @author hwliang<2020-08-21>
        @param key<string> 索引
        @param empty<bool> 是否清空计数
        @param expire<int> 计数器生命周期(秒)
        @return bool
    '''
    from BTPanel import cache
    key = md5(key)
    num = cache.get(key)
    if not num:
        num = 0
    else:
        if empty:
            cache.delete(key)
            return True
    cache.set(key,num + 1,expire)
    return True

def get_error_num(key,limit=False):
    '''
        @name 获取失败次数
        @author hwliang<2020-08-21>
        @param key<string> 索引
        @param limit<False or int> 如果为False，则直接返回失败次数，否则与失败次数比较，若大于失败次数返回True，否则返回False 
        @return int or bool
    '''
    from BTPanel import cache
    key = md5(key)
    num = cache.get(key)
    if not num: num = 0
    if not limit: 
        return num
    if limit > num:
        return True
    return False


def get_menus():
    '''
        @name 获取菜单列表
        @author hwliang<2020-08-31>
        @return list
    '''
    from BTPanel import session
    data = json.loads(ReadFile('config/menu.json'))
    hide_menu = ReadFile('config/hide_menu.json')
    debug = session.get('debug')
    if hide_menu:
        hide_menu = json.loads(hide_menu)
        show_menu = []
        for i in range(len(data)):
            if data[i]['id'] in hide_menu: continue
            if data[i]['id'] == "memuAxterm":
                if debug: continue
            show_menu.append(data[i])
        data = show_menu
        del(hide_menu)
        del(show_menu)
    menus = sorted(data, key=lambda x: x['sort'])
    return menus


#取CURL路径
def get_curl_bin():
    '''
        @name 取CURL执行路径
        @author hwliang<2020-09-01>
        @return string
    '''
    c_bin = ['/usr/local/curl2/bin/curl','/usr/local/curl/bin/curl','/usr/bin/curl']
    for cb in c_bin:
        if os.path.exists(cb): return cb
    return 'curl'


#设置防跨站配置
def set_open_basedir():
    try:
        fastcgi_file = '/www/server/nginx/conf/fastcgi.conf'

        if os.path.exists(fastcgi_file):
            fastcgi_body = readFile(fastcgi_file)
            if fastcgi_body.find('bt_safe_dir') == -1:
                fastcgi_body = fastcgi_body + "\n"+'fastcgi_param  PHP_ADMIN_VALUE    "$bt_safe_dir=$bt_safe_open";'
                writeFile(fastcgi_file,fastcgi_body)

        proxy_file = '/www/server/nginx/conf/proxy.conf'
        if os.path.exists(proxy_file):
            proxy_body = readFile(proxy_file)
            if proxy_body.find('bt_safe_dir') == -1:
                proxy_body = proxy_body + "\n"+'''map "baota_dir" $bt_safe_dir {
    default "baota_dir";
}
map "baota_open" $bt_safe_open {
    default "baota_open";
} '''
                writeFile(proxy_file,proxy_body)

        open_basedir_path = '/www/server/panel/vhost/open_basedir/nginx'
        if not os.path.exists(open_basedir_path):
            os.makedirs(open_basedir_path,384)

        site_list = M('sites').field('id,name,path').select()
        for site_info in site_list:
            set_site_open_basedir_nginx(site_info['name'])
    except: return
        

#处理指定站点的防跨站配置 for Nginx
def set_site_open_basedir_nginx(siteName):
    try:
        return
        open_basedir_path = '/www/server/panel/vhost/open_basedir/nginx'
        if not os.path.exists(open_basedir_path):
            os.makedirs(open_basedir_path,384)
        config_file = '/www/server/panel/vhost/nginx/{}.conf'.format(siteName)
        open_basedir_file = "/".join(
            (open_basedir_path,'{}.conf'.format(siteName))
        )
        if not os.path.exists(config_file): return
        if not os.path.exists(open_basedir_file):
            writeFile(open_basedir_file,'')
        config_body = readFile(config_file)
        if config_body.find(open_basedir_path) == -1:
            config_body = config_body.replace("include enable-php","include {};\n\t\tinclude enable-php".format(open_basedir_file))
            writeFile(config_file,config_body)

        root_path = re.findall(r"root\s+(.+);",config_body)[0]
        if not root_path: return
        userini_file = root_path + '/.user.ini'
        if not os.path.exists(userini_file):
            writeFile(open_basedir_file,'')
            return
        userini_body = readFile(userini_file)
        if not userini_body: return
        if userini_body.find('open_basedir') == -1: 
            writeFile(open_basedir_file,'')
            return
        
        open_basedir_conf = re.findall("open_basedir=(.+)",userini_body)
        if not open_basedir_conf: return
        open_basedir_conf = open_basedir_conf[0]
        open_basedir_body = '''set $bt_safe_dir "open_basedir";
set $bt_safe_open "{}";'''.format(open_basedir_conf)
        writeFile(open_basedir_file,open_basedir_body)
    except: return


def run_thread(fun,args = (),daemon=False):
    '''
        @name 使用线程执行指定方法
        @author hwliang<2020-10-27>
        @param fun {def} 函数对像
        @param args {tuple} 参数元组
        @param daemon {bool} 是否守护线程
        @return bool
    '''
    import threading
    p = threading.Thread(target=fun,args=args)
    p.setDaemon(daemon)
    p.start()
    return True
    
def check_domain_cloud(domain):
    run_thread(cloud_check_domain,(domain,))
    
def cloud_check_domain(domain):
    '''
        @name 从云端验证域名的可访问性,并将结果保存到文件
        @author hwliang<2020-12-10>
        @param domain {string} 被验证的域名
        @return void
    '''
    try:
        check_domain_path = '/www/server/panel/data/check_domain/'
        if not os.path.exists(check_domain_path):
            os.makedirs(check_domain_path,384)
        result = httpPost('https://www.bt.cn/api/panel/check_domain',{"domain":domain})
        cd_file = check_domain_path + domain +'.pl'
        writeFile(cd_file,result)
    except:
        pass


def send_file(data,fname='',mimetype = ''):
    '''
        @name 以文件流的形式返回
        @author heliang<2020-10-27>
        @param data {bytes|string} 文件数据或路径
        @param mimetype {string} 文件类型
        @param fname {string} 文件名
        @return Response
    '''
    d_type = type(data)
    from io import BytesIO,StringIO
    from flask import send_file as send_to
    if d_type == bytes:
        fp = BytesIO(data)
    else:
        if len(data) < 128:
            if os.path.exists(data):
                fp = data
                if not fname:
                    fname = os.path.basename(fname)
            else:
                fp = StringIO(data)
        else:
            fp = StringIO(data)

    if not mimetype: mimetype = "application/octet-stream"
    if not fname: fname = 'doan.txt'

    return send_to(fp,
                    mimetype=mimetype, 
                    as_attachment=True,
                    add_etags=True,
                    conditional=True,
                    attachment_filename=fname,
                    cache_timeout=0)

def gen_password(length=8,chars=string.ascii_letters+string.digits):
    return ''.join([choice(chars) for i in range(length)])

def get_ipaddress():
    '''
        @name 获取本机IP地址
        @author hwliang<2020-11-24>
        @return list
    '''
    ipa_tmp = ExecShell("ip a |grep inet|grep -v inet6|grep -v 127.0.0.1|grep -v 'inet 192.168.'|grep -v 'inet 10.'|awk '{print $2}'|sed 's#/[0-9]*##g'")[0].strip()
    iplist = ipa_tmp.split('\n')
    return iplist


def get_root_domain(domain_name):
			'''
				@name 根据域名查询根域名和记录值
				@author cjxin<2020-12-17>
				@param domain {string} 被验证的根域名
				@return void
			'''
			top_domain_list = ['.ac.cn', '.ah.cn', '.bj.cn', '.com.cn', '.cq.cn', '.fj.cn', '.gd.cn',
								'.gov.cn', '.gs.cn', '.gx.cn', '.gz.cn', '.ha.cn', '.hb.cn', '.he.cn',
								'.hi.cn', '.hk.cn', '.hl.cn', '.hn.cn', '.jl.cn', '.js.cn', '.jx.cn',
								'.ln.cn', '.mo.cn', '.net.cn', '.nm.cn', '.nx.cn', '.org.cn','.cn.com']
			old_domain_name = domain_name
			top_domain = "."+".".join(domain_name.rsplit('.')[-2:])
			new_top_domain = "." + top_domain.replace(".", "")
			is_tow_top = False
			if top_domain in top_domain_list:
				is_tow_top = True
				domain_name = domain_name[:-len(top_domain)] + new_top_domain

			if domain_name.count(".") > 1:
				zone, middle, last = domain_name.rsplit(".", 2)
				if is_tow_top:
					last = top_domain[1:]
				root = ".".join([middle, last])
			else:
				zone = ""
				root = old_domain_name
			return root, zone

def query_dns(domain,dns_type = 'A',is_root = False):
    '''
        @name 查询域名DNS解析
        @author cjxin<2020-12-17>
        @param domain {string} 被验证的根域名
        @param dns_type {string} dns记录
        @param is_root {bool} 是否查询根域名
        @return void
    '''
    try:
        import dns.resolver
    except :
        os.system('{} -m pip install dnspython'.format(get_python_bin()))
        import dns.resolver

    if is_root: domain,zone = get_root_domain(domain)
    try:
        ret = dns.resolver.query(domain, dns_type)           
        data = []
        for i in ret.response.answer:            
            for j in i.items:
                tmp = {}
                tmp['flags'] = j.flags
                tmp['tag'] = j.tag.decode()
                tmp['value'] = j.value.decode()
                data.append(tmp)
        return data
    except :
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



#实例化定目录下的所有模块
class get_modules:

    def __contains__(self, key):
        return self.get_attr(key)

    def __setitem__(self, key, value):
        setattr(self,key,value)

    def get_attr(self,key):
        '''
            尝试获取模块，若为字符串，则尝试实例化模块，否则直接返回模块对像
        '''
        res = getattr(self,key)
        if isinstance(res,str):
            try:
                tmp_obj = __import__(key)
                reload(tmp_obj)
                setattr(self,key,tmp_obj)
                return tmp_obj
            except:
                raise Exception(get_error_info())
        return res

    def __getitem__(self, key):
        return self.get_attr(key)

    def __delitem__(self,key):
        delattr(self,key)

    def __delattr__(self, key):
        delattr(self,key)

    def get_items(self):
        return self

    def __init__(self,path = "class",limit = None):
        '''
            @name 加载指定目录下的模块
            @author hwliang<2020-08-03>
            @param path<string> 指定目录，可指定绝对目录，也可指定相对于/www/server/panel的相对目录 默认加载class目录
            @param limit<string/list/tuple> 指定限定加载的模块名称，默认加载path目录下的所有模块
            @param object

            @example
                p = get_modules('class')
                if 'public' in p:
                    md5_str = p.public.md5('test')
                    md5_str = p['public'].md5('test')
                    md5_str = getattr(p['public'],'md5')('test')
                else:
                    print(p.__dict__)
        '''
        os.chdir('/www/server/panel')
        exp_files = ['__init__.py','__pycache__']
        if not path in sys.path:
            sys.path.insert(0,path)
        for fname in os.listdir(path):
            if fname in exp_files: continue
            filename = '/'.join([path,fname])
            if os.path.isfile(filename):
                if not fname[-3:] in ['.py','.so']: continue
                mod_name = fname[:-3]
            else:
                c_file = '/'.join((filename,'__init__.py'))
                if not os.path.exists(c_file):
                    continue
                mod_name = fname
            
            if limit:
                if not isinstance(limit,list) and not isinstance(limit,tuple):
                    limit = (limit,)
                if not mod_name in limit:
                    continue

            setattr(self,mod_name,mod_name)





