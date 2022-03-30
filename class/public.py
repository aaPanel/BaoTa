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
    if url.find('GetAuthToken') == -1:
        if is_local(): return False
    # rep_home_host()
    import http_requests
    res = http_requests.get(url,timeout=timeout,headers = headers)
    if res.status_code == 0:
        if headers: return False
        s_body = res.text
        return s_body
    s_body = res.text
    del res
    return s_body

def rep_home_host():
    hosts_file = "data/home_host.pl"
    if os.path.exists(hosts_file):
        ExecShell('sed -i "/www.bt.cn/d" /etc/hosts')
        os.remove(hosts_file)

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
    if url.find('GetAuthToken') == -1:
        if is_local(): return False
    # rep_home_host()
    import http_requests
    res = http_requests.post(url,data=data,timeout=timeout,headers = headers)
    if res.status_code == 0:
        if headers: return False
        s_body = res.text
        return s_body
    s_body = res.text
    return s_body

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
    fp = None
    try:
        fp = open(filename, mode)
        f_body = fp.read()
    except Exception as ex:
        if sys.version_info[0] != 2:
            try:
                fp = open(filename, mode,encoding="utf-8")
                f_body = fp.read()
            except:
                fp = open(filename, mode,encoding="GBK")
                f_body = fp.read()
        else:
            return False
    finally:
        if fp and not fp.closed:
            fp.close()
    return f_body

def readFile(filename,mode='r'):
    '''
        @name 读取指定文件数据
        @author hwliang<2021-06-09>
        @param filename<string> 文件名
        @param mode<string> 文件打开模式，默认r
        @return string or bytes or False 如果返回False则说明读取失败
    '''
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
    '''
        @name 写入到指定文件
        @author hwliang<2021-06-09>
        @param filename<string> 文件名
        @param s_boey<string/bytes> 被写入的内容，字节或字符串
        @param mode<string> 文件打开模式，默认w+
        @return bool
    '''
    return WriteFile(filename,s_body,mode)

def WriteLog(type,logMsg,args=(),not_web = False):
    #写日志
    try:
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
    except:
        pass

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
    if not key in config.keys(): 
        if key == 'download': return 'https://download.bt.cn'
        return None
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
    if os.path.exists('{}/apache/bin/apachectl'.format(get_setup_path())):
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
    if os.path.exists('{}/nginx/sbin/nginx'.format(get_setup_path())):
        result = ExecShell('/etc/init.d/nginx reload')
        if result[1].find('nginx.pid') != -1:
            ExecShell('pkill -9 nginx && sleep 1')
            ExecShell('/etc/init.d/nginx start')
    elif os.path.exists('{}/apache/bin/apachectl'.format(get_setup_path())):
        result = ExecShell('/etc/init.d/httpd reload')
    else:
        result = ExecShell('rm -f /tmp/lshttpd/*.sock* && /usr/local/lsws/bin/lswsctrl restart')
    return result

def serviceReload():
    return ServiceReload()



def get_preexec_fn(run_user):
    '''
        @name 获取指定执行用户预处理函数
        @author hwliang<2021-08-19>
        @param run_user<string> 运行用户
        @return 预处理函数
    '''
    import pwd
    pid = pwd.getpwnam(run_user)
    uid = pid.pw_uid
    gid = pid.pw_gid

    def _exec_rn():
        os.setgid(gid)
        os.setuid(uid)
    return _exec_rn


def ExecShell(cmdstring, timeout=None, shell=True,cwd=None,env=None,user = None):
    '''
        @name 执行命令
        @author hwliang<2021-08-19>
        @param cmdstring 命令 [必传]
        @param timeout 超时时间
        @param shell 是否通过shell运行
        @param cwd 进入的目录
        @param env 环境变量
        @param user 执行用户名
        @return 命令执行结果
    '''
    a = ''
    e = ''
    import subprocess,tempfile
    preexec_fn = None
    tmp_dir = '/dev/shm'
    if user:
        preexec_fn = get_preexec_fn(user)
        tmp_dir = '/tmp'
    try:
        rx = md5(cmdstring)
        succ_f = tempfile.SpooledTemporaryFile(max_size=4096,mode='wb+',suffix='_succ',prefix='btex_' + rx ,dir=tmp_dir)
        err_f = tempfile.SpooledTemporaryFile(max_size=4096,mode='wb+',suffix='_err',prefix='btex_' + rx ,dir=tmp_dir)
        sub = subprocess.Popen(cmdstring, close_fds=True, shell=shell,bufsize=128,stdout=succ_f,stderr=err_f,cwd=cwd,env=env,preexec_fn=preexec_fn)
        if timeout:
            s = 0
            d = 0.01
            while sub.poll() == None:
                time.sleep(d)
                s += d
                if s >= timeout:
                    if not err_f.closed: err_f.close()
                    if not succ_f.closed: succ_f.close()
                    return 'Timed out'
        else:
            sub.wait()

        err_f.seek(0)
        succ_f.seek(0)
        a = succ_f.read()
        e = err_f.read()
        if not err_f.closed: err_f.close()
        if not succ_f.closed: succ_f.close()
    except:
        return '',get_error_info()
    try:
        #编码修正
        if type(a) == bytes: a = a.decode('utf-8')
        if type(e) == bytes: e = e.decode('utf-8')
    except:
        a = str(a)
        e = str(e)

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
    ipaddr =  request.remote_addr.replace('::ffff:','')
    if not check_ip(ipaddr): return '未知IP地址'
    return ipaddr

def get_client_ip():
    return GetClientIp()

def phpReload(version):
    #重载PHP配置
    import os
    if os.path.exists(get_setup_path()+'/php/' + version + '/libphp5.so'):
        ExecShell('/etc/init.d/httpd reload')
    else:
        ExecShell('/etc/init.d/php-fpm-'+version+' reload')
        ExecShell("/etc/init.d/php-fpm-{} start".format(version))


def get_timeout(url,timeout=3):
    try:
        start = time.time()
        result = int(httpGet(url,timeout))
        return result,int((time.time() - start) * 1000 - 500)
    except: return 0,False

def get_url(timeout = 0.5):
    return 'https://download.bt.cn'

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
        from cgi import html
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
                            data.insert(0,html.escape(line))
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

def get_requests_headers():
    return {"Content-type":"application/x-www-form-urlencoded","User-Agent":"BT-Panel"}

def downloadFile(url,filename):
    try:
        import requests
        from requests.packages.urllib3.exceptions import InsecureRequestWarning
        requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
        # import requests.packages.urllib3.util.connection as urllib3_conn
        # old_family = urllib3_conn.allowed_gai_family
        # urllib3_conn.allowed_gai_family = lambda: socket.AF_INET
        res = requests.get(url,headers=get_requests_headers(),timeout=30,stream=True)
        with open(filename,"wb") as f:
            for _chunk in res.iter_content(chunk_size=8192):
                f.write(_chunk)
        # urllib3_conn.allowed_gai_family = old_family
    except:
        ExecShell("wget -O {} {} --no-check-certificate".format(filename,url))

def exists_args(args,get):
    '''
        @name 检查参数是否存在
        @author hwliang<2021-06-08>
        @param args<list or str> 参数列表 允许是列表或字符串
        @param get<dict_obj> 参数对像
        @return bool 都存在返回True，否则抛出KeyError异常
    '''
    if type(args) == str:
        args = args.split(',')
    for arg in args:
        if not arg in get:
            raise KeyError('缺少必要参数: {}'.format(arg))
    return True


def get_error_info():
    import traceback
    errorMsg = traceback.format_exc()
    return errorMsg


def get_plugin_replace_rules():
    '''
        @name 获取插件文件内容替换规则
        @author hwliang<2021-06-28>
        @return list
    '''
    return [
        {
            "find":"[PATH]",
            "replace": "[PATH]"
        }
    ]


def get_plugin_title(plugin_name):
    '''
        @name 获取插件标题
        @author hwliang<2021-06-24>
        @param plugin_name<string> 插件名称
        @return string
    '''

    info_file = '{}/{}/info.json'.format(get_plugin_path(),plugin_name)
    try:
        return json.loads(readFile(info_file))['title']
    except:
        return plugin_name


def get_error_object(plugin_title = None,plugin_name = None):
    '''
        @name 获取格式化错误响应对像
        @author hwliang<2021-06-21>
        @return Resp
    '''
    if not plugin_title: plugin_title = get_plugin_title(plugin_name)
    try:
        from BTPanel import request,Resp
        is_cli = False
    except:
        is_cli = True

    if is_cli:
        raise get_error_info()
    ss = '''404 Not Found: The requested URL was not found on the server. If you entered the URL manually please check your spelling and try again.

During handling of the above exception, another exception occurred:'''
    error_info = get_error_info().strip().split(ss)[-1].strip()
    request_info = '''REQUEST_DATE: {request_date}
 PAN_VERSION: {panel_version}
  OS_VERSION: {os_version}
 REMOTE_ADDR: {remote_addr}
 REQUEST_URI: {method} {full_path}
REQUEST_FORM: {request_form}
  USER_AGENT: {user_agent}'''.format(
    request_date = getDate(),
    remote_addr = GetClientIp(),
    method = request.method,
    full_path = request.full_path,
    request_form = request.form.to_dict(),
    user_agent = request.headers.get('User-Agent'),
    panel_version = version(),
    os_version = get_os_version()
)

    result =readFile('{}/BTPanel/templates/default/plugin_error.html'.format(get_panel_path())).format(
        plugin_name=plugin_title,
        request_info=request_info,
        error_title=error_info.split("\n")[-1],
        error_msg=error_info
        )
    return Resp(result,500)





def submit_error(err_msg = None):
    try:
        if os.path.exists('{}/not_submit_errinfo.pl'.format(get_panel_path())): return False
        from BTPanel import request
        import system
        if not err_msg: err_msg = get_error_info()
        pdata = {}
        pdata['err_info'] = err_msg
        pdata['path_full'] = request.full_path
        pdata['version'] = 'Linux-Panel-%s' % version()
        pdata['os'] = system.system().GetSystemVersion()
        pdata['py_version'] = sys.version
        pdata['install_date'] = int(os.stat('{}/common.py'.format(get_class_path())).st_mtime)
        httpPost(GetConfigValue('home') + "/api/panel/s_error",pdata,timeout=3)
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
    f1 = '{}/'.format(get_vhost_path())
    f2 = '{}/'.format(get_plugin_path())
    setup_path = get_setup_path()
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
        if os.path.exists(setup_path + '/apache/modules/mod_lua.so'): 
            writeFile(f1 + 'apache/btwaf.conf','LoadModule lua_module modules/mod_lua.so')
            writeFile(f1 + 'apache/total.conf','LuaHookLog {}/total/httpd_log.lua run_logs'.format(setup_path))
        else:
            f3 = f1 + 'apache/total.conf'
            if os.path.exists(f3): os.remove(f3)

    if get_webserver() == 'nginx':
        result = ExecShell("ulimit -n 8192 ; {setup_path}/nginx/sbin/nginx -t -c {setup_path}/nginx/conf/nginx.conf".format(setup_path = setup_path))
        searchStr = 'successful'
    elif get_webserver() == 'apache':
    # else:
        result = ExecShell("ulimit -n 8192 ; {setup_path}/apache/bin/apachectl -t".format(setup_path = setup_path))
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
    versionFile = get_setup_path() + '/mysql/version.pl'
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

#取计算机名
def get_hostname():
    import socket
    return socket.gethostname()


#取mysql datadir
def get_datadir():
    mycnf_file = '/etc/my.cnf'
    if not os.path.exists(mycnf_file): return ''
    mycnf = readFile(mycnf_file)
    import re
    tmp = re.findall(r"datadir\s*=\s*(.+)",mycnf)
    if not tmp: return ''
    return tmp[0]


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

#pid是否存在
def pid_exists(pid):
    if os.path.exists('/proc/{}/exe'.format(pid)):
        return True
    return False


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
    from cgi import html
    list=['`','~','&','#','/','*','$','@','<','>','\"','\'',';','%',',','.','\\u']
    ret=[]
    for i in text:
        if i in list:
            i=''
        ret.append(i)
    str_convert = ''.join(ret)
    text2=html.escape(str_convert, quote=True)
    return text2
#xss 防御
def xssencode2(text):
    from cgi import html
    text2=html.escape(text, quote=True)
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
        comm = ReadFile('{}/common.py'.format(get_class_path()))
        return re.search("g\.version\s*=\s*'(\d+\.\d+\.\d+)'",comm).groups()[0]
    except:
        return get_panel_version()

def get_panel_version():
    comm = ReadFile('{}/common.py'.format(get_class_path()))
    s_key = 'g.version = '
    s_len = len(s_key)
    s_leff = comm.find(s_key) + s_len
    version = comm[s_leff:s_leff+10].strip().strip("'")
    return version


def get_os_version():
    '''
        @name 取操作系统版本
        @author hwliang<2021-08-07>
        @return string
    '''
    p_file = '/etc/.productinfo'
    if os.path.exists(p_file):
        s_tmp = readFile(p_file).split("\n")
        if s_tmp[0].find('Kylin') != -1 and len(s_tmp) > 1:
            version = s_tmp[0] + ' ' + s_tmp[1].split('/')[0].strip()
    else:
        version = readFile('/etc/redhat-release')
    if not version:
        version = readFile('/etc/issue').strip().split("\n")[0].replace('\\n','').replace('\l','').strip()
    else:
        version = version.replace('release ','').replace('Linux','').replace('(Core)','').strip()
    v_info = sys.version_info
    try:
        version = "{} {}(Py{}.{}.{})".format(version,os.uname().machine,v_info.major,v_info.minor,v_info.micro)
    except:
        version = "{} (Py{}.{}.{})".format(version,v_info.major,v_info.minor,v_info.micro)
    return version

#取文件或目录大小
def get_path_size(path, exclude=[]):
    """根据排除目录获取路径的总大小
    
    :path 目标路径
    :exclude 排除路径单个字符串或者多个列表。匹配路径是基于path的相对路径,规则是
        tar命令的--exclude规则的子集。
    """
    import fnmatch
    if not os.path.exists(path): return 0
    if os.path.isfile(path): return os.path.getsize(path)
    if type(exclude) != type([]):
        exclude = [exclude]

    path = path[0:-1] if path[-1] == "/" else path
    path = os.path.normcase(path)
    # print("path:"+ path)
    # print("exclude:"+ str(exclude))
    _exclude = exclude[0:]
    for i, e in enumerate(_exclude):
        if not e.startswith(path):
            basename = os.path.basename(path)
            if not e.startswith(basename):
                exclude.append(os.path.join(path, e))
            else:
                new_exc = e.replace(basename+"/", "")
                new_exc = os.path.join(path, new_exc)
                exclude.append(new_exc)

    # print(exclude)
    total_size = 0
    count = 0
    for root, dirs, files in os.walk(path, topdown=True):
        # filter path
        for exc in exclude:
            for d in dirs:
                sub_dir = os.path.normcase(root+os.path.sep+d)
                if fnmatch.fnmatch(sub_dir, exc) or d==exc:
                    # print("排除目录:"+sub_dir)
                    dirs.remove(d)
        count += 1
        for f in files:
            to_exclude = False
            count += 1
            filename = os.path.normcase(root+os.path.sep+f)
            if not os.path.exists(filename): continue
            if os.path.islink(filename): continue
            # filter file
            norm_filename = os.path.normcase(filename)
            for fexc in exclude:
                if fnmatch.fnmatch(norm_filename, fexc) or fexc==f:
                    to_exclude = True
                    # print("排除文件:"+norm_filename)
                    break
            if to_exclude: 
                continue
            total_size += os.path.getsize(filename)
    return total_size

#写关键请求日志
def write_request_log(reques = None):
    try:
        from BTPanel import request,g,session
        if session.get('debug') == 1: return
        if request.path in ['/service_status','/favicon.ico','/task','/system','/ajax','/control','/data','/ssl']:
            return False

        log_path = '{}/logs/request'.format(get_panel_path())
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

def create_linux_user(user,group):
    '''
        @name 创建系统用户
        @author hwliang<2022-01-15>
        @param user<string> 用户名
        @param group<string> 所属组
        @return bool
    '''
    ExecShell("groupadd {}".format(group))
    ExecShell('useradd -s /sbin/nologin -g {} {}'.format(user,group))
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
        if user == 'www': create_linux_user(user)
        #如果指定用户或组不存在，则使用www
        try:
            user_info = getpwnam('www')
        except:
            create_linux_user(user)
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
        db_obj = get_mysql_obj(db_name)
        tmp = db_obj.query("show create database `%s`" % db_name.strip())
        c_type = str(re.findall(r"SET\s+([\w\d-]+)\s",tmp[0][1])[0])
        c_types = ['utf8','utf-8','gbk','big5','utf8mb4']
        if not c_type.lower() in c_types: return 'utf8'
        return c_type
    except:
        return 'utf8'

# 取mysql数据库对象
def get_mysql_obj(db_name):
    is_cloud_db = False
    if db_name:
        db_find = M('databases').where("name=?" ,db_name).find()
        if db_find['sid']:
            return get_mysql_obj_by_sid(db_find['sid'])
        is_cloud_db = db_find['db_type'] in ['1',1]
    if is_cloud_db:
        import db_mysql
        db_obj = db_mysql.panelMysql()
        conn_config = json.loads(db_find['conn_config'])
        try:
            db_obj = db_obj.set_host(conn_config['db_host'],conn_config['db_port'],conn_config['db_name'],conn_config['db_user'],conn_config['db_password'])
        except Exception as e:
            raise PanelError(GetMySQLError(e))
    else:
        import panelMysql
        db_obj = panelMysql.panelMysql()
    return db_obj

# 取mysql数据库对像 By sid
def get_mysql_obj_by_sid(sid = 0,conn_config = None):
    if sid:
        if not conn_config: conn_config = M('database_servers').where("id=?" ,sid).find()
        import db_mysql
        db_obj = db_mysql.panelMysql()
        try:
            db_obj = db_obj.set_host(conn_config['db_host'],conn_config['db_port'],None,conn_config['db_user'],conn_config['db_password'])
        except Exception as e:
            raise PanelError(GetMySQLError(e))
    else:
        import panelMysql
        db_obj = panelMysql.panelMysql()
    return db_obj

def GetMySQLError(e):
    res = ''
    if e.args[0] == 1045:
        res = '数据库用户名或密码错误!'
    if e.args[0] == 1049:
        res = '数据库不存在!'
    if e.args[0] == 1044:
        res = '没有指定数据库的访问权限，或指定数据库不存在!'
    if e.args[0] == 1062:
        res = '数据库已存在!'
    if e.args[0] == 1146:
        res = '数据表不存在!'
    if e.args[0] == 2003:
        res = '数据库服务器连接失败!'
    if e.args[0] == 1142:
        res = '指定用户权限不足!'
    if res: 
        res = res + "<pre>" + str(e) + "</pre>"
    else:
        res = str(e)
    return res


def get_database_codestr(codeing):
    wheres = {
        'utf8'      :   'utf8_general_ci',
        'utf8mb4'   :   'utf8mb4_general_ci',
        'gbk'       :   'gbk_chinese_ci',
        'big5'      :   'big5_chinese_ci'
    }
    return wheres[codeing]


def get_database_size(name=None):
    """
    @获取数据库大小
    """
    data = {}
    try:
        mysql_obj = get_mysql_obj(name)
        tables = mysql_obj.query("select table_schema, (sum(DATA_LENGTH)+sum(INDEX_LENGTH)) as data from information_schema.TABLES group by table_schema")
        if type(tables) == list: 
            for x in tables:
                if len(x) < 2:continue
                if x[1] == None:continue
                data[x[0]] = int(x[1])
    except: return data
    return data

def get_database_size_by_name(name):
    """
    @获取数据库大小
    """
    data = 0
    try:
        mysql_obj = get_mysql_obj(name)
        tables = mysql_obj.query("select table_schema, (sum(DATA_LENGTH)+sum(INDEX_LENGTH)) as data from information_schema.TABLES WHERE table_schema='{}' group by table_schema".format(name))
        data = tables[0][1]  
        if not data: data = 0
    except: return data
    return data

def get_database_size_by_id(id):
    """
    @获取数据库大小
    """
    data = 0
    try:
        name = M('databases').where('id=?',id).getField('name')
        mysql_obj = get_mysql_obj(name)
        tables = mysql_obj.query("select table_schema, (sum(DATA_LENGTH)+sum(INDEX_LENGTH)) as data from information_schema.TABLES WHERE table_schema='{}' group by table_schema".format(name))
        data = tables[0][1]  
        if not data: data = 0
    except:
        return data
    return data


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


#获取IP限制列表
def get_limit_ip():
    iplong_list = []
    try:
        ip_file = 'data/limitip.conf'
        if not os.path.exists(ip_file): return iplong_list

        from BTPanel import cache
        ikey = 'limit_ip'
        iplong_list = cache.get(ikey)
        if iplong_list: return iplong_list

        iplong_list = []
        iplist = ReadFile(ip_file)
        if not iplist:return iplong_list
        iplist = iplist.strip()
        for limit_ip in iplist.split(','):
            if not limit_ip: continue
            limit_ip = limit_ip.split('-')
            iplong = {}
            iplong['min'] = ip2long(limit_ip[0])
            if len(limit_ip) > 1:
                iplong['max'] = ip2long(limit_ip[1])
            else:
                iplong['max'] = iplong['min']
            iplong_list.append(iplong)

        cache.set(ikey,iplong_list,3600)
    except:pass
    return iplong_list


def is_api_limit_ip(ip_list,client_ip):
    '''
        @name 判断IP是否在限制列表中
        @author hwliang<2022-02-10>
        @param ip_list<list> 限制IP列表
        @param client_ip<string> 客户端IP
        @return bool
    '''
    iplong_list = []
    for limit_ip in ip_list:
        if not limit_ip: continue
        if limit_ip in ['*','all','0.0.0.0','0.0.0.0/0','0.0.0.0/24','0.0.0.0/32']: return True
        limit_ip = limit_ip.split('-')
        iplong = {}
        iplong['min'] = ip2long(limit_ip[0])
        if len(limit_ip) > 1:
            iplong['max'] = ip2long(limit_ip[1])
        else:
            iplong['max'] = iplong['min']
        iplong_list.append(iplong)

    client_ip_long = ip2long(client_ip)
    for limit_ip in iplong_list:
        if client_ip_long >= limit_ip['min'] and client_ip_long <= limit_ip['max']:
            return True
    return False
    




#检查IP白名单
def check_ip_panel():
    iplong_list = get_limit_ip()
    if not iplong_list: return False
    client_ip = GetClientIp()
    if client_ip in ['127.0.0.1','localhost','::1']: return False
    client_ip_long = ip2long(client_ip)
    for limit_ip in iplong_list:
        if client_ip_long >= limit_ip['min'] and client_ip_long <= limit_ip['max']:
            return False
    
    errorStr = ReadFile('./BTPanel/templates/' + GetConfigValue('template') + '/error2.html')
    try:
        errorStr = errorStr.format(getMsg('PAGE_ERR_TITLE'),getMsg('PAGE_ERR_IP_H1'),getMsg('PAGE_ERR_IP_P1',(GetClientIp(),)),getMsg('PAGE_ERR_IP_P2'),getMsg('PAGE_ERR_IP_P3'),getMsg('NAME'),getMsg('PAGE_ERR_HELP'))
    except IndexError:pass
    return error_not_login(errorStr,True)

#检查面板域名
def check_domain_panel():
    tmp = GetHost()
    domain = ReadFile('data/domain.conf')
    if domain:
        client_ip = GetClientIp()
        if client_ip in ['127.0.0.1','localhost','::1']: return False
        if tmp.strip().lower() != domain.strip().lower(): 
            errorStr = ReadFile('./BTPanel/templates/' + GetConfigValue('template') + '/error2.html')
            try:
                errorStr = errorStr.format(getMsg('PAGE_ERR_TITLE'),getMsg('PAGE_ERR_DOMAIN_H1'),getMsg('PAGE_ERR_DOMAIN_P1'),getMsg('PAGE_ERR_DOMAIN_P2'),getMsg('PAGE_ERR_DOMAIN_P3'),getMsg('NAME'),getMsg('PAGE_ERR_HELP'))
            except:pass
            return error_not_login(errorStr,True)
    return False

#是否离线模式
def is_local():
    s_file = '{}/data/not_network.pl'.format(get_panel_path())
    return os.path.exists(s_file)


#自动备份面板数据
def auto_backup_panel():
    try:
        panel_paeh = get_panel_path()
        paths = panel_paeh + '/data/not_auto_backup.pl'
        if os.path.exists(paths): return False
        b_path = '{}/panel'.format(get_backup_path())
        day_date = format_date('%Y-%m-%d')
        backup_path = b_path + '/' + day_date
        backup_file = backup_path + '.zip'
        if os.path.exists(backup_path) or os.path.exists(backup_file): return True
        ignore_default = ''
        ignore_system = ''
        max_size = 100 * 1024 * 1024
        if os.path.getsize('{}/data/default.db'.format(panel_paeh)) > max_size:
            ignore_default = 'default.db'
        if os.path.getsize('{}/data/system.db'.format(panel_paeh)) > max_size:
            ignore_system = 'system.db'
        os.makedirs(backup_path,384)
        import shutil
        shutil.copytree(panel_paeh + '/data',backup_path + '/data',ignore = shutil.ignore_patterns(ignore_system,ignore_default))
        shutil.copytree(panel_paeh + '/config',backup_path + '/config')
        shutil.copytree(panel_paeh + '/vhost',backup_path + '/vhost')
        ExecShell("cd {} && zip {} -r {}/".format(b_path,backup_file,day_date))
        ExecShell("chmod -R 600 {path};chown -R root.root {path}".format(path=backup_file))
        if os.path.exists(backup_path): shutil.rmtree(backup_path)

        time_now = time.time() - (86400 * 15)
        for f in os.listdir(b_path):
            if time.mktime(time.strptime(f, "%Y-%m-%d")) < time_now: 
                path = b_path + '/' + f
                b_file = path + '.zip'
                if os.path.exists(path): 
                    shutil.rmtree(path)
                if os.path.exists(b_file):
                    os.remove(b_file)
        set_php_cli_env()
    except:pass

            

def set_php_cli_env():
    '''
        @name 重新设置php-cli.ini配置
    '''
    import jobs
    jobs.set_php_cli_env()
    


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
        time_str = HttpGet(GetConfigValue('home') + '/api/index/get_time')
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


def get_fpm_address(php_version,bind=False):
    '''
        @name 获取FPM请求地址
        @author hwliang<2020-10-23>
        @param php_version string PHP版本
        @return tuple or string
    '''
    fpm_address = '/tmp/php-cgi-{}.sock'.format(php_version)
    php_fpm_file = '{}/php/{}/etc/php-fpm.conf'.format(get_setup_path(),php_version)
    try:
        fpm_conf = readFile(php_fpm_file)
        tmp = re.findall(r"listen\s*=\s*(.+)",fpm_conf)
        if not tmp: return fpm_address
        if tmp[0].find('sock') != -1: return fpm_address
        if tmp[0].find(':') != -1:
            listen_tmp = tmp[0].split(':')
            if bind:
                fpm_address = (listen_tmp[0],int(listen_tmp[1]))
            else:
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
        rep = r"enable-php-(\w{2,5})\.conf"
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
    vhost_path = get_vhost_path()
    conf = readFile(vhost_path + '/'+web_server+'/'+siteName+'.conf')
    if web_server == 'openlitespeed':
        conf = readFile(vhost_path + '/' + web_server + '/detail/' + siteName + '.conf')
    return get_php_version_conf(conf)


def check_tcp(ip,port):
    '''
        @name 使用TCP的方式检测指定IP:端口是否能连接
        @author hwliang<2021-06-01>
        @param ip<string> IP地址
        @param port<int> 端口
        @return bool
    '''
    import socket
    try:
        s = socket.socket()
        s.settimeout(5)
        s.connect((ip.strip(),int(port)))
        s.close()
    except:
        return False
    return True


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
    if not os.path.isfile(conf_file): return False
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
    php_versions = get_php_versions()
    for phpv in php_versions:
        sync_php_address(phpv)

def sync_php_address(php_version):
    '''
        @name 同步PHP版本配置到所有配置文件
        @author hwliang<2020-10-24>
        @param php_version string PHP版本
        @return void
    '''
    if not os.path.exists('{}/php/{}/bin/php'.format(get_setup_path(),php_version)): # 指定PHP版本是否安装
        return False
    ngx_rep = r"(unix:/tmp/php-cgi.*\.sock|127.0.0.1:\d+)"
    apa_rep = r"(unix:/tmp/php-cgi.*\.sock\|fcgi://localhost|fcgi://127.0.0.1:\d+)"
    ngx_proxy = get_php_proxy(php_version,'nginx')
    apa_proxy = get_php_proxy(php_version,'apache')
    is_write = False

    #nginx的PHP配置文件
    nginx_conf_path = '{}/nginx/conf'.format(get_setup_path())
    
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
    apache_conf_path = '{}/apache'.format(get_vhost_path())
    if os.path.exists(apache_conf_path):
        for f_name in os.listdir(apache_conf_path):
            conf_file = '/'.join((apache_conf_path,f_name))
            if sub_php_address(conf_file,apa_rep,apa_proxy,php_version):
                is_write = True
    #apache的phpmyadmin
    conf_file = '{}/apache/conf/extra/httpd-vhosts.conf'.format(get_setup_path())
    if os.path.exists(conf_file):
        if sub_php_address(conf_file,apa_rep,apa_proxy,php_version):
            is_write = True
    
    if is_write: serviceReload()
    return True




def url_encode(data):
    if type(data) != str: return data
    if sys.version_info[0] != 2:
        import urllib.parse
        pdata = urllib.parse.quote(data)
    else:
        import urllib
        pdata = urllib.urlencode(data)
    return pdata

def url_decode(data):
    if type(data) != str: return data
    if sys.version_info[0] != 2:
        import urllib.parse
        pdata = urllib.parse.unquote(data)
    else:
        import urllib
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
    bin_file = '{}/pyenv/bin/python'.format(get_panel_path())
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
            distribution = 'centos{}'.format(tmp)
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

def is_local_ip(ip):
    '''
        @name 判断是否为本地(内网)IP地址
        @author hwliang<2021-03-26>
        @param ip string(ipv4)
        @return bool
    '''
    patt = r"^(192\.168|127|10|172\.(16|17|18|19|20|21|22|23|24|25|26|27|28|29|30|31))\."
    if re.match(patt,ip): return True
    return False

#提交关键词
def submit_keyword(keyword):
    pdata = {"keyword":keyword}
    httpPost(GetConfigValue('home') + '/api/panel/total_keyword',pdata)

#统计关键词
def total_keyword(keyword):
    import threading
    p = threading.Thread(target=submit_keyword,args=(keyword,))
    # p.setDaemon(True)
    p.start()

#获取debug日志
def get_debug_log():
    from BTPanel import request
    return GetClientIp() +':'+ str(request.environ.get('REMOTE_PORT')) + '|' + str(int(time.time())) + '|' + get_error_info()

#获取sessionid
def get_session_id():
    from BTPanel import request,app
    session_id =  request.cookies.get(app.config['SESSION_COOKIE_NAME'],'')
    if not re.findall(r"^([\w\.-]{64,64})$",session_id):
        return GetRandomString(64)
    return session_id

#尝试自动恢复面板数据库
def rep_default_db():
    db_path = '{}/data/'.format(get_panel_path())
    db_file = db_path + 'default.db'
    db_tmp_backup = db_path + 'default_' + format_date("%Y%m%d_%H%M%S") + ".db"

    panel_backup = '{}/panel'.format(get_backup_path())
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
    token_s = readFile('{}/data/login_token.pl'.format(get_panel_path()))
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
    port_all = re.findall(r".*Port\s+[0-9]+",conf)
    ssh_port = 22
    for p in port_all:
        rep = r"^\s*Port\s+([0-9]+)\s*"
        tmp1 = re.findall(rep,p)
        if tmp1:
            ssh_port = int(tmp1[0])

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
            # if data[i]['id'] == "memu_btwaf": 
            #     if not os.path.exists('plugin/btwaf/btwaf_main.py'): continue
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
        fastcgi_file = '{}/nginx/conf/fastcgi.conf'.format(get_setup_path())

        if os.path.exists(fastcgi_file):
            fastcgi_body = readFile(fastcgi_file)
            if fastcgi_body.find('bt_safe_dir') == -1:
                fastcgi_body = fastcgi_body + "\n"+'fastcgi_param  PHP_ADMIN_VALUE    "$bt_safe_dir=$bt_safe_open";'
                writeFile(fastcgi_file,fastcgi_body)

        proxy_file = '{}/nginx/conf/proxy.conf'.format(get_setup_path())
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

        open_basedir_path = '{}/open_basedir/nginx'.format(get_vhost_path())
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
        check_domain_path = '{}/data/check_domain/'.format(get_panel_path())
        if not os.path.exists(check_domain_path):
            os.makedirs(check_domain_path,384)
        pdata = get_user_info()
        pdata['domain'] = domain
        result = httpPost('https://www.bt.cn/api/panel/check_domain',pdata)
        cd_file = check_domain_path + domain +'.pl'
        writeFile(cd_file,result)
    except:
        pass

def get_mac_address():
    import uuid
    mac=uuid.UUID(int = uuid.getnode()).hex[-12:]
    return ":".join([mac[e:e+2] for e in range(0,11,2)])

def get_user_info():
    user_file = '{}/data/userInfo.json'.format(get_panel_path())
    if not os.path.exists(user_file): return {}
    userInfo = {}
    try:
        userTmp = json.loads(readFile(user_file))
        if not 'serverid' in userTmp or len(userTmp['serverid']) != 64:
            import panelAuth
            userTmp = panelAuth.panelAuth().create_serverid(None)
        userInfo['uid'] = userTmp['uid']
        userInfo['access_key'] = userTmp['access_key']
        userInfo['username'] = userTmp['username']
        userInfo['serverid'] = userTmp['serverid']
        userInfo['oem'] =  get_oem_name()
        userInfo['o'] = userInfo['oem']
        userInfo['mac'] = get_mac_address()
    except: pass
    return userInfo

def is_bind():
    # if not os.path.exists('{}/data/bind.pl'.format(get_panel_path())): return True
    return not not get_user_info()


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

def get_oem_name():
    '''
        @name 获取OEM名称
        @author hwliang<2021-03-24>
        @return string
    '''
    oem = ''
    oem_file = '{}/data/o.pl'.format(get_panel_path())
    if os.path.exists(oem_file):
        oem = readFile(oem_file)
        if oem: oem = oem.strip()
    return oem

def get_pdata():
    '''
        @name 构造POST基础参数
        @author hwliang<2021-03-24>
        @return dict
    '''
    import panelAuth
    pdata = panelAuth.panelAuth().create_serverid(None)
    pdata['oem'] = get_oem_name()
    return pdata


# 名称输入系列化
def xssdecode(text):
    try:
        cs = {"&quot":'"',"&#x27":"'"}
        for c in cs.keys():
            text = text.replace(c,cs[c])

        str_convert = text
        if sys.version_info[0] == 3:
            import html
            text2 = html.unescape(str_convert)
        else:
            text2 = cgi.unescape(str_convert)
        return text2
    except:
        return text


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
    def exists(self,keys):
        return exists_args(keys,self)
    def get(self,key,default='',format='',limit = []):
        '''
            @name 获取指定参数
            @param key<string> 参数名称，允许在/后面限制参数格式，请参考参数值格式(format)
            @param default<string> 默认值，默认空字符串
            @param format<string>  参数值格式(int|str|port|float|json|xss|path|url|ip|ipv4|ipv6|letter|mail|phone|正则表达式|>1|<1|=1)，默认为空
            @param limit<list> 限制参数值内容
            @param return mixed
        '''
        if key.find('/') != -1:
            key,format = key.split('/')
        result = getattr(self,key,default)
        if isinstance(result,str): result = result.strip()
        if format:
            if format in ['str','string','s']:
                result = str(result)
            elif format in ['int','d']:
                try:
                    result = int(result)
                except:
                    raise ValueError("参数：{}，要求int类型数据".format(key))
            elif format in ['float','f']:
                try:
                    result = float(result)
                except:
                    raise ValueError("参数：{}，要求float类型数据".format(key))
            elif format in ['json','j']:
                try:
                    result = json.loads(result)
                except:
                    raise ValueError("参数：{}, 要求JSON字符串".format(key))
            elif format in ['xss','x']:
                result = xssencode(result)
            elif format in ['path','p']:
                if not path_safe_check(result):
                    raise ValueError("参数：{}，要求正确的路径格式".format(key))
                result = result.replace('//','/')
            elif format in ['url','u']:
                regex = re.compile(
                     r'^(?:http|ftp)s?://'
                     r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'
                     r'localhost|'
                     r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
                     r'(?::\d+)?'
                     r'(?:/?|[/?]\S+)$', re.IGNORECASE)
                if not re.match(regex,result):
                    raise ValueError('参数：{}，要求正确的URL格式'.format(key))
            elif format in ['ip','ipaddr','i','ipv4','ipv6']:
                if format == 'ipv4':
                    if not is_ipv4(result):
                        raise ValueError('参数：{}，要求正确的ipv4地址'.format(key))
                elif format == 'ipv6':
                    if not is_ipv6(result):
                        raise ValueError('参数：{}，要求正确的ipv6地址'.format(key))
                else:
                    if not is_ipv4(result) and not is_ipv6(result):
                        raise ValueError('参数：{}，要求正确的ipv4/ipv6地址'.format(key))
            elif format in ['w','letter']:
                if not re.match(r'^\w+$',result):
                    raise ValueError('参数：{}，要求只能是英文字母或数据组成'.format(key))
            elif format in ['email','mail','m']:
                if not re.match(r"^.+\\@(\\[?)[a-zA-Z0-9\\-\\.]+\\.([a-zA-Z]{2,3}|[0-9]{1,3})(\\]?)$",result):
                    raise ValueError("参数：{}，要求正确的邮箱地址格式".format(key))
            elif format in ['phone','mobile','p']:
                if not re.match("^[0-9]{11,11}$",result):
                    raise ValueError("参数：{}，要求手机号码格式".format(key))
            elif format in ['port']:
                result_port = int(result)
                if result_port > 65535 or result_port < 0:
                    raise ValueError("参数：{}，要求端口号为0-65535".format(key))
                result = result_port
            elif re.match(r"^[<>=]\d+$",result):
                operator = format[0]
                length = int(format[1:].strip())
                result_len = len(result)
                error_obj = ValueError("参数：{}，要求长度为{}".format(key,format))
                if operator == '=':
                    if result_len != length:
                        raise error_obj
                elif operator == '>':
                    if result_len < length:
                        raise error_obj
                else:
                    if result_len > length:
                        raise error_obj
            elif format[0] in ['^','(','[','\\','.'] or format[-1] in ['$',')',']','+','}']:
                if not re.match(format,result):
                    raise ValueError("指定参数格式不正确, {}:{}".format(key,format))
            
        if limit:
            if not result in limit:
                raise ValueError("指定参数值范围不正确, {}:{}".format(key,limit))
        return result

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
        os.chdir(get_panel_path())
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

#检查App和小程序的绑定
def check_app(check='app'):
    path=get_panel_path() + '/'
    if check=='app':
        try:
            if not os.path.exists("/www/server/panel/plugin/btapp/btapp_main.py"): return False
            if not os.path.exists(path+'config/api.json'):return False
            if os.path.exists(path+'config/api.json'):
                btapp_info = json.loads(readFile(path+'config/api.json'))
                if not  btapp_info['open']:return False
                if not 'apps' in btapp_info:return False
                if not btapp_info['apps']:return False
                return True
            return False
        except:
            return False
    elif check=='app_bind':
        if not cache_get('get_bind_status'):return False
        if not os.path.exists("/www/server/panel/plugin/btapp/btapp_main.py"):return False
        if not os.path.exists(path + 'config/api.json'):return False
        btapp_info = json.loads(readFile(path +'config/api.json'))
        if not btapp_info: return False
        if not btapp_info['open']: return False
        return True
    elif check=='wxapp':
        if not os.path.exists(path+'plugin/app/user.json'):return False
        app_info = json.loads(readFile(path+'plugin/app/user.json'))
        if not app_info: return False
        return True


#宝塔邮件报警
def send_mail(title,body,is_logs=False,is_type="堡塔登录提醒"):
    if is_logs:
        try:
            import send_mail
            send_mail22 = send_mail.send_mail()
            tongdao = send_mail22.get_settings()
            if tongdao['user_mail']['mail_list']==0:return False
            if not tongdao['user_mail']['info']: return False
            if len(tongdao['user_mail']['mail_list'])==1:
                send_mail=tongdao['user_mail']['mail_list'][0]
                send_mail22.qq_smtp_send(send_mail, title=title, body=body)
            else:
                send_mail22.qq_smtp_send(tongdao['user_mail']['mail_list'], title=title, body=body)
            if is_logs:
                WriteLog2(is_type, body)
        except:
            return False
    else:
        try:
            import send_mail
            send_mail22 = send_mail.send_mail()
            tongdao = send_mail22.get_settings()
            if tongdao['user_mail']['mail_list'] == 0: return False
            if not tongdao['user_mail']['info']: return False
            if len(tongdao['user_mail']['mail_list']) == 1:
                send_mail = tongdao['user_mail']['mail_list'][0]
                return send_mail22.qq_smtp_send(send_mail, title=title, body=body)
            else:
                return send_mail22.qq_smtp_send(tongdao['user_mail']['mail_list'], title=title, body=body)
        except:
            return False

#宝塔钉钉 or 微信告警
def send_dingding(body,is_logs=False,is_type="堡塔登录提醒"):
    if is_logs:
        try:
            import send_mail
            send_mail22 = send_mail.send_mail()
            tongdao = send_mail22.get_settings()
            if not tongdao['dingding']['info']: return False
            tongdao = send_mail22.get_settings()
            if is_logs:
                WriteLog2(is_type,body)
            return send_mail22.dingding_send(body)
        except:
            return False
    else:
        try:
            import send_mail
            send_mail22 = send_mail.send_mail()
            tongdao = send_mail22.get_settings()
            if not tongdao['dingding']['info']: return False
            tongdao = send_mail22.get_settings()
            return send_mail22.dingding_send(body)
        except:return False

#获取服务器IP
def get_ip():
    iplist_file = '{}/data/iplist.txt'.format(get_panel_path())
    if os.path.exists(iplist_file):
        data=ReadFile(iplist_file)
        return data.strip()
    else:return '127.0.0.1'

#获取服务器内网Ip
def get_local_ip():
    try:
        ret=ExecShell("ip addr | grep -E -o '[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}' | grep -E -v \"^127\.|^255\.|^0\.\" | head -n 1")
        local_ip=ret[0].strip()
        return local_ip
    except:return '127.0.0.1'

def create_logs():
    import db
    sql = db.Sql()
    if not sql.table('sqlite_master').where('type=? AND name=?', ('table', 'logs2')).count():
        csql = '''CREATE TABLE `logs2` (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `type` TEXT,
  `log` TEXT,
  `addtime` TEXT
, uid integer DEFAULT '1', username TEXT DEFAULT 'system')'''
        sql.execute(csql, ())

def WriteLog2(type,logMsg,args=(),not_web = False):
    import db
    create_logs()
    username = 'system'
    uid = 1
    tmp_msg = ''
    sql = db.Sql()
    mDate = time.strftime('%Y-%m-%d %X',time.localtime())
    data = (uid,username,type,logMsg + tmp_msg,mDate)
    result = sql.table('logs2').add('uid,username,type,log,addtime',data)

def check_ip_white(path,ip):
    if os.path.exists(path):
        try:
            path_json=json.loads(ReadFile(path))
        except:
            WriteFile(path,'[]')
            return False
        if ip in path_json:return True
        else:return False
    else:
        return False

#登陆告警
def login_send_body(is_type,username,login_ip,port):
    login_send_mail = "{}/data/login_send_mail.pl".format(get_panel_path())
    send_login_white = '{}/data/send_login_white.json'.format(get_panel_path())
    login_send_dingding = "{}/data/login_send_dingding.pl".format(get_panel_path())
    if os.path.exists(login_send_mail):
        if check_ip_white(send_login_white,login_ip):return False
        send_mail("堡塔登录提醒","堡塔登录提醒：您的服务器"+get_ip()+"通过"+is_type+"登录成功，账号："+username+"，登录IP："+login_ip+":"+port+"，登录时间："+time.strftime('%Y-%m-%d %X',time.localtime()), True)
    if os.path.exists(login_send_dingding):
        if check_ip_white(send_login_white,login_ip):return False
        send_dingding("#### 堡塔登录提醒\n\n > 服务器　："+get_ip()+"\n\n > 登录方式："+is_type+"\n\n > 登录账号："+username+"\n\n > 登录ＩＰ："+login_ip+":"+port+"\n\n > 登录时间："+time.strftime('%Y-%m-%d %X',time.localtime())+'\n\n > 登录状态:  <font color=#20a53a>成功</font>', True)


#普通模式下调用发送消息【设置登陆告警后的设置】
#title= 发送的title
#body= 发送的body
#is_logs= 是否记录日志
#is_type=发送告警的类型
def send_to_body(title,body,is_logs=False,is_type="堡塔邮件告警"):
    login_send_mail = "{}/data/login_send_mail.pl".format(get_panel_path())
    login_send_dingding = "{}/data/login_send_dingding.pl".format(get_panel_path())
    if os.path.exists(login_send_mail):
        if is_logs:
            send_mail(title, body,True,is_type)
        send_mail(title,body)
    
    if os.path.exists(login_send_dingding):
        if is_logs:
            send_dingding(body,True,is_type)
        send_dingding(body)

#普通发送消息
#send_type= ["mail","dingding"]
#title =发送的头
#body= 发送消息的内容
def send_body_words(send_type,title,body):
    if send_type=='mail':
        return send_mail(title,body)
    if send_type=='dingding':
        return  send_dingding(body)

def return_is_send_info():
    import send_mail
    send_mail22 = send_mail.send_mail()
    tongdao = send_mail22.get_settings()
    ret={}
    ret['mail']=tongdao['user_mail']['user_name']
    ret['dingding']=tongdao['dingding']['dingding']
    return ret


def get_sys_path():
    '''
        @name 关键目录
        @author hwliang<2021-06-11>
        @return tuple
    '''
    a = ['/www','/usr','/','/dev','/home','/media','/mnt','/opt','/tmp','/var']
    c = ['/www/.Recycle_bin/','/www/backup/','/www/php_session/','/www/wwwlogs/','/www/server/','/etc/','/usr/','/var/','/boot/','/proc/','/sys/','/tmp/','/root/','/lib/','/bin/','/sbin/','/run/','/lib64/','/lib32/','/srv/']
    return a,c


def check_site_path(site_path):
    '''
        @name 检查网站根目录是否为系统关键目录
        @author hwliang<2021-05-31>
        @param site_path<string> 网站根目录全路径
        @return bool
    '''
    whites = ['/www/server/tomcat','/www/server/stop','/www/server/phpmyadmin']
    for w in whites:
        if site_path.find(w) == 0: return True
    a,error_paths = get_sys_path()
    site_path = site_path.strip()
    if site_path[-1] == '/': site_path = site_path[:-1]
    if site_path in a:
        return False
    site_path += '/'
    for ep in error_paths:
        if site_path.find(ep) == 0: return False
    return True

def is_debug():
    debug_file = "{}/data/debug.pl".format(get_panel_path())
    return os.path.exists(debug_file)


class PanelError(Exception):
    '''
        @name 宝塔通用异常对像
        @author hwliang<2021-06-25>
    '''
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return ("面板运行时发生错误: {}".format(str(self.value)))


def get_plugin_find(upgrade_plugin_name = None):
    '''
        @name 获取指定软件信息
        @author hwliang<2021-06-15>
        @param upgrade_plugin_name<string> 插件名称
        @return dict
    '''
    from pluginAuth import Plugin
    
    plugin_list_data = Plugin(False).get_plugin_list()

    for p_data_info in plugin_list_data['list']:
        if p_data_info['name'] == upgrade_plugin_name: 
            upgrade_plugin_name = p_data_info['name']
            return p_data_info

    return get_plugin_info(upgrade_plugin_name)


def get_plugin_info(upgrade_plugin_name):
    '''
        @name 获取插件信息
        @author hwliang<2021-06-15>
        @param upgrade_plugin_name<string> 插件名称
        @return dict
    '''
    plugin_path = get_plugin_path()
    plugin_info_file = '{}/{}/info.json'.format(plugin_path,upgrade_plugin_name)
    if not os.path.exists(plugin_info_file): return {}
    info_body = readFile(plugin_info_file)
    if not info_body: return {}
    plugin_info = json.loads(info_body)
    return plugin_info

def download_main(upgrade_plugin_name,upgrade_version):
    '''
        @name 下载插件主程序文件
        @author hwliang<2021-06-25>
        @param upgrade_plugin_name<string> 插件名称
        @param upgrade_version<string> 插件版本
        @return void
    '''
    import requests,shutil
    plugin_path = get_plugin_path()
    tmp_path = '{}/temp'.format(get_panel_path())
    download_d_main_url = 'https://api.bt.cn/down/download_plugin_main'
    pdata = get_user_info()
    pdata['name'] = upgrade_plugin_name
    pdata['version'] = upgrade_version
    pdata['os'] = 'Linux'
    download_res = requests.post(download_d_main_url,pdata,timeout=30,headers=get_requests_headers())
    filename = '{}/{}.py'.format(tmp_path,upgrade_plugin_name)
    with open(filename,'wb+') as save_script_f:
        save_script_f.write(download_res.content)
        save_script_f.close()
    if md5(download_res.content) != download_res.headers['Content-md5']:
        raise PanelError('插件安装包HASH校验失败')
    dst_file = '{plugin_path}/{plugin_name}/{plugin_name}_main.py'.format(plugin_path=plugin_path,plugin_name = upgrade_plugin_name)
    shutil.copyfile(filename,dst_file)
    if os.path.exists(filename): os.remove(filename)
    WriteLog('软件管理',"检测到插件[{}]程序文件异常，已尝试自动修复!".format(get_plugin_info(upgrade_plugin_name)['title']))


def get_plugin_bin(plugin_save_file,plugin_timeout):
    list_body = None
    if not os.path.exists(plugin_save_file): return list_body
    s_time = time.time()
    m_time = os.stat(plugin_save_file).st_mtime
    if (s_time - m_time) < plugin_timeout or not plugin_timeout:
        list_body = readFile(plugin_save_file,'rb')
    return list_body


def get_plugin_main_object(plugin_name,sys_path):
    os_file = sys_path + '/' + plugin_name + '_main.so'
    php_file = sys_path + '/index.php'
    is_php = False
    plugin_obj = None
    if os.path.exists(os_file): # 是否为编译后的so文件
        plugin_obj = __import__(plugin_name + '_main')
    elif os.path.exists(php_file): # 是否为PHP代码
        import panelPHP
        is_php = True
        plugin_obj = panelPHP.panelPHP(plugin_name)
    
    return plugin_obj,is_php


def get_plugin_script(plugin_name,plugin_path):
    # 优先运行py文件
    plugin_file = '{plugin_path}/{name}/{name}_main.py'.format(plugin_path =plugin_path, name=plugin_name)
    if not os.path.exists(plugin_file): return '',True
    plugin_body = readFile(plugin_file,'rb')

    if plugin_body.find(b'import') != -1:
        return plugin_body,True

    # 无py文件再运行so
    plugin_file_so = '{plugin_path}/{name}/{name}_main.so'.format(plugin_path =plugin_path, name=plugin_name)
    if os.path.exists(plugin_file_so): return '',True

    return plugin_body,False

def re_download_main(plugin_name,plugin_path):
    plugin_file = '{plugin_path}{name}/{name}_main.py'.format(plugin_path =plugin_path, name=plugin_name)
    version = get_plugin_info(plugin_name)['versions']
    download_main(plugin_name,version)
    plugin_body = readFile(plugin_file,'rb')
    return plugin_body


def get_sysbit():
    '''
        @name 获取操作系统位数
        @author hwliang<2021-07-07>
        @return int 32 or 64
    '''
    import struct
    return struct.calcsize('P') * 8

def get_setup_path():
    '''
        @name 获取安装路径
        @author hwliang<2021-07-22>
        @return string
    '''
    return '/www/server'

def get_panel_path():
    '''
        @name 取面板根目录
        @author hwliang<2021-07-14>
        @return string
    '''
    return '{}/panel'.format(get_setup_path())

def get_plugin_path(plugin_name = None):
    '''
        @name 取指定插件目录
        @author hwliang<2021-07-14>
        @param plugin_name<string> 插件名称 不传则返回插件根目录
        @return string
    '''

    root_path = "{}/plugin".format(get_panel_path())
    if not plugin_name: return root_path
    return "{}/{}".format(root_path,plugin_name)

def get_class_path():
    '''
        @name 取类库所在路径
        @author hwliang<2021-07-14>
        @return string
    '''
    return "{}/class".format(get_panel_path())

def get_logs_path():
    '''
        @name 取日志目录
        @author hwliang<2021-07-14>
        @return string
    '''
    return '/www/wwwlogs'

def get_vhost_path():
    '''
        @name 取虚拟主机目录
        @author hwliang<2021-08-14>
        @return string
    '''
    return '{}/vhost'.format(get_panel_path())


def get_backup_path():
    '''
        @name 取备份目录
        @author hwliang<2021-07-14>
        @return string
    '''
    default_backup_path = '/www/backup'
    backup_path = M('config').where("id=?",(1,)).getField('backup_path')
    if not backup_path: return default_backup_path
    if os.path.exists(backup_path): return backup_path
    return default_backup_path

def get_site_path():
    '''
        @name 取站点默认存储目录
        @author hwliang<2021-07-14>
        @return string
    '''
    default_site_path = '/www/wwwroot'
    site_path = M('config').where("id=?",(1,)).getField('sites_path')
    if not site_path: return default_site_path
    if os.path.exists(site_path): return site_path
    return default_site_path


def read_config(config_name,ext_name = 'json'):
    '''
        @name 读取指定配置文件
        @author hwliang<2021-07-14>
        @param config_name<string> 配置文件名称(不含扩展名)
        @param ext_name<string> 配置文件扩展名，默认为json
        @return string 如果发生错误，将抛出PanelError异常
    '''
    config_file = "{}/config/{}.{}".format(get_panel_path(),config_name,ext_name)
    if not os.path.exists(config_file):
        raise PanelError('指定配置文件{} 不存在'.format(config_name))
    
    config_str = readFile(config_file)
    if ext_name == 'json':
        try:
            config_body = json.loads(config_str)
        except Exception as ex:
            raise PanelError('配置文件不是标准的可解析JSON内容!\n{}'.format(ex))
        return config_body
    return config_str

def save_config(config_name,config_body,ext_name = 'json'):
    '''
        @name 保存配置文件
        @author hwliang<2021-07-14>
        @param config_name<string> 配置文件名称(不含扩展名)
        @param config_body<mixed> 被保存的内容, ext_name为json，请传入可解析为json的参数类型，如list,dict,int,str等
        @param ext_name<string> 配置文件扩展名，默认为json
        @return string 如果发生错误，将抛出PanelError异常
    '''

    config_file = "{}/config/{}.{}".format(get_panel_path(),config_name,ext_name)
    if ext_name == 'json':
        try:
            config_body = json.dumps(config_body)
        except Exception as ex:
            raise PanelError('配置内容无法被转换为json格式!\n{}'.format(ex))
    
    return writeFile(config_file,config_body)

def get_config_value(config_name,key,default='',ext_name='json'):
    '''
        @name 获取指定配置文件的指定配置项
        @author hwliang<2021-07-14>
        @param config_name<string> 配置文件名称(不含扩展名)
        @param key<string> 配置项
        @param default<mixed> 获不存在则返回的默认值，默认为空字符串
        @param ext_name<string> 配置文件扩展名，默认为json
        @return mixed 如果发生错误，将抛出PanelError异常
    '''
    config_data = read_config(config_name,ext_name)
    return config_data.get(key,default)

def set_config_value(config_name,key,value,ext_name='json'):
    '''
        @name 设置指定配置文件的指定配置项
        @author hwliang<2021-07-14>
        @param config_name<string> 配置文件名称(不含扩展名)
        @param key<string> 配置项
        @param value<mixed> 配置值
        @param ext_name<string> 配置文件扩展名，默认为json
        @return mixed  如果发生错误，将抛出PanelError异常
    '''
    config_data = read_config(config_name,ext_name)
    config_data[key] = value
    return save_config(config_name,config_data,ext_name)


def return_data(status,data = {},status_code=None,error_msg = None):
    '''
        @name 格式化响应内容
        @author hwliang<2021-07-14>
        @param status<bool> 状态
        @param data<mixed> 响应数据
        @param status_code<int> 状态码
        @param error_msg<string> 错误消息内容
        @return dict

    '''
    if status_code == None:
        status_code = 1 if status else 0
    if error_msg == None:
        error_msg = '' if status else '未知错误'
    
    result = {
                'status':status,
                "status_code":status_code,
                'error_msg':str(error_msg),
                'data':data
            }
    return result


def return_error(error_msg,status_code = -1,data = []):
    '''
        @name 格式化错误响应内容
        @author hwliang<2021-07-15>
        @param error_msg<string> 错误消息
        @param status_code<int> 状态码，默认为-1
        @param data<mixed> 响应数据
        @return dict
    '''
    return return_data(False,data,status_code,str(error_msg))


def error(error_msg,status_code = -1,data = []):
    '''
        @name 格式化错误响应内容
        @author hwliang<2021-07-15>
        @param error_msg<string> 错误消息
        @param status_code<int> 状态码，默认为-1
        @param data<mixed> 响应数据
        @return dict
    '''
    return return_error(error_msg,status_code,data)

def success(data = [],status_code = 1,error_msg = ''):
    '''
        @name 格式化成功响应内容
        @author hwliang<2021-07-15>
        @param data<mixed> 响应数据
        @param status_code<int> 状态码，默认为0
        @return dict
    '''
    return return_data(True,data,status_code,error_msg)


def return_status_code(status_code,format_body,data = []):
    '''
        @name 按状态码返回
        @author hwliang<2021-07-15>
        @param status_code<int> 状态码
        @param format_body<string> 错误内容
        @param data<mixed> 响应数据
        @return dict
    '''
    error_msg = get_config_value('status_code',str(status_code))
    if not error_msg: raise PanelError('指定状态码不存在!')
    return return_data(error_msg[0],data,status_code,error_msg[1].format(format_body))


def to_dict_obj(data):
    '''
        @name 将dict转换为dict_obj
        @author hwliang<2021-07-15>
        @param data<dict> 要被转换的数据
        @return dict_obj
    '''
    if not isinstance(data,dict):
        raise PanelError('错误的数据类型，只支持将dict转换为dict_obj')
    pdata = dict_obj()
    for key in data.keys():
        pdata[key] = data[key]
    return pdata

def get_script_object(filename):
    '''
        @name 从脚本文件获取对像
        @author hwliang<2021-07-19>
        @param filename<string> 文件名
        @return object
    '''
    _obj =  sys.modules.get(filename,None)
    if _obj: return _obj
    from types import ModuleType
    _obj = sys.modules.setdefault(filename, ModuleType(filename))
    _code = readFile(filename)
    _code_object = compile(_code,filename, 'exec')
    _obj.__file__ = filename
    _obj.__package__ = ''
    exec(_code_object, _obj.__dict__)
    return _obj

def check_hooks():
    '''
        @name 自动注册HOOK
        @author hwliang<2021-07-19>
        @return void
    '''
    hooks_path = '{}/hooks'.format(get_panel_path())
    if not os.path.exists(hooks_path):
        return
    for hook_name in os.listdir(hooks_path):
        if hook_name[-3:] != '.py': continue
        filename = os.path.join(hooks_path,hook_name)
        _obj = get_script_object(filename)
        _main = getattr(_obj,'main',None)
        if not _main: continue
        _main()

def register_hook(hook_index,hook_def):
    '''
        @name 注册HOOK
        @author hwliang<2021-07-15>
        @param hook_index<string> HOOK位置
        @param hook_def<def> HOOK函数对像
        @return void
    '''
    from BTPanel import hooks
    hook_keys = hooks.keys()
    if not hook_index in hook_keys:
        hooks[hook_index] = []
    if not hook_def in hooks[hook_index]:
        hooks[hook_index].append(hook_def)

def exec_hook(hook_index,data):
    '''
        @name 执行HOOk
        @author hwliang<2021-07-15>
        @param hook_index<string> HOOK索引位置，格式限制：^\w+$
        @param data<mixed> 运行数据
        @return mixed
    '''
    
    from BTPanel import hooks
    hook_keys = hooks.keys()
    if not hook_index in hook_keys:
        return data

    for hook_def in hooks[hook_index]:
        data = hook_def(data)
    return data

def get_hook_index(mod_name,def_name):
    '''
        @name 获取HOOK位置
        @author hwliang<2021-07-19>
        @param mod_name<string> 模块名称
        @param def_name<string> 方法名称
        @return tuple
    '''
    mod_name = mod_name.upper()
    def_name = def_name.upper()
    last_index = '{}_{}_LAST'.format(mod_name,def_name)
    end_index = '{}_{}_END'.format(mod_name,def_name)
    return last_index,end_index


def flush_plugin_list():
    '''
        @name 刷新插件列表
        @author hwliang<2021-07-22>
        @return bool
    '''
    skey = 'TNaMJdG3mDHKRS6Y'
    from BTPanel import cache
    from pluginAuth import Plugin
    if cache.get(skey): cache.delete(skey)
    Plugin(False).get_plugin_list(True)
    return True


def get_session_timeout():
    '''
        @name 获取session过期时间
        @author hwliang<2021-07-28>
        @return int
    '''
    from BTPanel import cache
    skey = 'session_timeout'
    session_timeout = cache.get(skey)
    if not session_timeout == None: return session_timeout

    sess_out_path = '{}/data/session_timeout.pl'.format(get_panel_path())
    session_timeout = 86400
    if not os.path.exists(sess_out_path):
        return session_timeout
    try:
        session_timeout = int(readFile(sess_out_path))
    except:
        session_timeout = 86400
    cache.set(skey,session_timeout,3600)
    return session_timeout


def get_login_token_auth():
    '''
        @name 获取登录token
        @author hwliang<2021-07-28>
        @return string
    '''
    from BTPanel import cache
    skey = 'login_token'
    login_token = cache.get(skey)
    if not login_token == None: return login_token

    login_token_file = '{}/data/login_token.pl'.format(get_panel_path())
    login_token = '1234567890'
    if not os.path.exists(login_token_file):
        return login_token
    login_token = readFile(login_token_file)
    cache.set(skey,login_token,3600)
    return login_token


def listen_ipv6():
    '''
        @name 是否监听ipv6
        @author hwliang<2021-08-12>
        @return bool
    '''
    ipv6_file = '{}/data/ipv6.pl'.format(get_panel_path())
    return os.path.exists(ipv6_file)

def get_panel_log_file():
    '''
        @name 获取panel日志文件
        @author hwliang<2021-08-12>
        @return string
    '''
    return "{}/logs/error.log".format(get_panel_path())


def print_log(_info,_level = 'DEBUG'):
    '''
        @name 写入日志
        @author hwliang<2021-08-12>
        @param _info<string> 要写入到日志文件的信息
        @param _level<string> 日志级别
        @return void
    '''
    log_body = "[{}][{}] - {}\n".format(format_date(),_level.upper(),_info)
    return WriteFile(get_panel_log_file(),log_body,'a+')



def to_date(format = "%Y-%m-%d %H:%M:%S",times = None):
    '''
        @name 格式时间转时间戳
        @author hwliang<2021-08-17>
        @param format<string> 时间格式
        @param times<date> 时间
        @return int
    '''
    if times:
        if isinstance(times,int): return times
        if isinstance(times,float): return int(times)
        if re.match("^\d+$",times): return int(times)
    else: return 0
    ts = time.strptime(times, "%Y-%m-%d %H:%M:%S")
    return time.mktime(ts)


def get_glibc_version():
    '''
        @name 获取glibc版本
        @author hwliang<2021-08-17>
        @return string
    '''
    try:
        cmd_result = ExecShell("ldd --version")[0]
        if not cmd_result: return ''
        glibc_version = cmd_result.split("\n")[0].split()[-1]
    except:
        return ''
    return glibc_version


def is_apache_nginx():
    '''
        @name 是否是apache或nginx
        @author hwliang<2021-08-17>
        @return bool
    '''
    setup_path = get_setup_path()
    return os.path.exists(setup_path + '/apache') or os.path.exists(setup_path + '/nginx')

def error_not_login(e = None,_src = None):
    '''
        @name 未登录时且未输入正确的安全入口时的响应
        @author hwliang<2021-12-16>
        @return Response
    '''
    from BTPanel import Response,render_template,redirect
    
    try:
        abort_code = read_config('abort')
        if not abort_code in [None,1,0,'0','1']:
            if abort_code == 404: return error_404(e)
            if abort_code == 403: return error_403(e)
            return Response(status=int(abort_code))
    except:
        pass

    if e in ['/login']:
        return redirect(e)

    if _src:
        return e
    else:
        return render_template('autherr.html')

def error_403(e):
    from BTPanel import Response,session
    if not session.get('login',None): return error_not_login()
    errorStr = '''<html>
<head><title>403 Forbidden</title></head>
<body>
<center><h1>403 Forbidden</h1></center>
<hr><center>nginx</center>
</body>
</html>'''
    headers = {
        "Content-Type": "text/html"
    }
    return Response(errorStr, status=403, headers=headers)

def error_404(e):
    from BTPanel import Response,session
    if not session.get('login',None): return error_not_login()
    errorStr = '''<html>
<head><title>404 Not Found</title></head>
<body>
<center><h1>404 Not Found</h1></center>
<hr><center>nginx</center>
</body>
</html>'''
    headers = {
        "Content-Type": "text/html"
    }
    return Response(errorStr, status=404, headers=headers)


def get_password_config():
    '''
        @name 获取密码安全配置
        @author hwliang<2021-10-18>
        @return int
    '''
    import config
    return config.config().get_password_config(None)


def password_expire_check():
    '''
        @name 密码过期检查
        @author hwliang<2021-10-18>
        @return bool
    '''
    p_config = get_password_config()
    if p_config['expire'] == 0: return True
    if time.time() > p_config['expire_time']: return False
    return True

def stop_status_mvore():
    flag=False
    try:
        nginx_path='/www/server/panel/vhost/nginx/btwaf.conf'
        if os.path.exists(nginx_path):
            ExecShell('mv  %s %s.bak'%(nginx_path,nginx_path))
            flag=True
        nginx_path='/www/server/panel/vhost/nginx/free_waf.conf'
        if os.path.exists(nginx_path):
            ExecShell('mv  %s %s.bak'%(nginx_path,nginx_path))
            flag=True
        apache_path='/www/server/panel/vhost/apache/btwaf.conf'
        if os.path.exists(apache_path):
            ExecShell('chattr -i %s && mv %s %s.bak'%(apache_path,apache_path,apache_path))
            flag=True
        if flag:
            serviceReload()
    except:
        pass
    
def is_error_path():
    if os.path.exists("/www/server/panel/data/error_pl.pl"):
        stop_status_mvore()
        return True
    return False

def get_php_versions(reverse=False):
    '''
        @name 取PHP版本列表
        @author hwliang<2021-12-16>
        @param reverse<bool> 是否降序
        @return list
    '''
    _file = get_panel_path() + '/config/php_versions.json'
    if os.path.exists(_file):
        version_list  = json.loads(readFile(_file))
    else:
        version_list = ['52','53','54','55','56','70','71','72','73','74','80','81','82','83','84']

    return sorted(version_list,reverse=reverse)

def get_full_session_file():
    '''
        @name 获取临时SESSION文件
        @author hwliang<2021-12-28>
        @return string
    '''
    from BTPanel import app
    full_session_key = app.config['SESSION_KEY_PREFIX'] + get_session_id()
    sess_path = get_panel_path() + '/data/session/'
    return sess_path + '/' + md5(full_session_key)



def install_mysql_client():
    '''
        @name 安装mysql客户端
        @author hwliang<2022-01-14>
        @return void
    '''
    if os.path.exists('/usr/bin/yum'):
        os.system("yum install mariadb -y")
        if not os.path.exists('/usr/bin/mysql'):
            os.system("yum reinstall mariadb -y")
    elif os.path.exists('/usr/bin/apt-get'):
        os.system('apt-get install mariadb-client -y')
        if not os.path.exists('/usr/bin/mysql'):
            os.system('apt-get reinstall mariadb-client* -y')

def get_mysqldump_bin():
    '''
        @name 获取mysqldump路径
        @author hwliang<2022-01-14>
        @return string
    '''
    bin_files = [
        '{}/mysql/bin/mysqldump'.format(get_setup_path()),
        '/usr/bin/mysqldump',
        '/usr/local/bin/mysqldump',
        '/usr/sbin/mysqldump',
        '/usr/local/sbin/mysqldump'
    ]
    
    for bin_file in bin_files:
        if os.path.exists(bin_file):
            return bin_file
    
    install_mysql_client()

    for bin_file in bin_files:
        if os.path.exists(bin_file):
            return bin_file

    return bin_files[0]

def get_mysql_bin():
    '''
        @name 获取mysql路径
        @author hwliang<2022-01-14>
        @return string
    '''
    bin_files = [
        '{}/mysql/bin/mysql'.format(get_setup_path()),
        '/usr/bin/mysql',
        '/usr/local/bin/mysql',
        '/usr/sbin/mysql',
        '/usr/local/sbin/mysql'
    ]
    
    for bin_file in bin_files:
        if os.path.exists(bin_file):
            return bin_file
    
    install_mysql_client()
        
    for bin_file in bin_files:
        if os.path.exists(bin_file):
            return bin_file
    return bin_files[0]

def error_conn_cloud(text):
    '''
        @name 连接云端失败
        @author hwliang<2021-12-18>
        @return void
    '''
    code_msg = ''
    if text.find("502 Bad Gateway") != -1:
        code_msg = '502 Bad Gateway'
    if text.find("504 Bad Gateway") != -1:
        code_msg = '504 Bad Gateway'
    elif text.find("Connection refused") != -1:
        code_msg = 'Connection refused'
    elif text.find("Connection timed out") != -1:
        code_msg = 'Connection timed out'
    elif text.find("Connection reset by peer") != -1:
        code_msg = 'Connection reset by peer'
    elif text.find("Name or service not known") != -1:
        code_msg = 'Name or service not known'
    elif text.find("No route to host") != -1:
        code_msg = 'No route to host'
    elif text.find("No such file or directory") != -1:
        code_msg = 'No such file or directory'
    elif text.find("404 Not Found") != -1:
        code_msg = '404 Not Found'
    elif text.find("403 Forbidden") != -1:
        code_msg = '403 Forbidden'
    elif text.find("401 Unauthorized") != -1:
        code_msg = '401 Unauthorized'
    elif text.find("400 Bad Request") != -1:
        code_msg = '400 Bad Request'
    elif text.find("Remote end closed connection without response") != -1:
        code_msg = 'Remote end closed connection'
    err_template_file = '{}/BTPanel/templates/default/error_connect.html'.format(get_panel_path())
    msg = readFile(err_template_file)
    msg = msg.format(code=code_msg)
    return msg

def get_mountpoint_list():
    '''
        @name 获取挂载点列表
        @author hwliang<2021-12-18>
        @return list
    '''
    import psutil
    mount_list = []
    for mount in psutil.disk_partitions():
        mountpoint = mount.mountpoint if mount.mountpoint[-1] == '/' else mount.mountpoint + '/'
        mount_list.append(mountpoint)
    # 根据挂载点字符长度排序
    mount_list.sort(key = lambda i:len(i),reverse=True)
    return mount_list

def get_path_in_mountpoint(path):
    '''
        @name 获取文件或目录目录所在挂载点
        @author hwliang<2022-03-30>
        @param path<string> 文件或目录路径
        @return string
    '''
    # 判断是否是绝对路径
    if path.find('./') != -1 or path[0] != '/': raise PanelError("不能使用相对路径")
    if not path: raise PanelError("文件或目录路径不能为空")

    # 在目录尾加/
    if os.path.isdir(path):
        path = path if path[-1] == '/' else path + '/'
    
    # 匹配挂载点
    mount_list = get_mountpoint_list()
    for mountpoint in mount_list:
        if path.startswith(mountpoint):
            return mountpoint
    
    # 没有匹配到挂载点
    return '/'

def get_recycle_bin_path(path):
    '''
        @name 获取指定文件或目录的回收站路径
        @author hwliang<2022-03-30>
        @param path<string> 文件或目录路径
        @return string
    '''
    mountpoint = get_path_in_mountpoint(path)
    recycle_bin_path = '{}/.Recycle_bin/'.format(mountpoint)
    if not os.path.exists(recycle_bin_path):
        os.mkdir(recycle_bin_path,384)
    return recycle_bin_path

def get_recycle_bin_list():
    '''
        @name 获取回收站列表
        @author hwliang<2022-03-30>
        @return list
    '''
    # 旧的回收站重命名为.Recycle_bin
    default_path = '/www/.Recycle_bin'
    default_path_src = '/www/Recycle_bin'
    if os.path.exists(default_path_src) and not os.path.exists(default_path):
        os.rename(default_path_src,default_path)
    
    # 获取回收站列表
    recycle_bin_list = []
    for mountpoint in get_mountpoint_list():
        recycle_bin_path = '{}.Recycle_bin/'.format(mountpoint)
        if not os.path.exists(recycle_bin_path):
            os.mkdir(recycle_bin_path,384)
        recycle_bin_list.append(recycle_bin_path)
    
    # 包含默认回收站路径？
    if not default_path in recycle_bin_list:
        recycle_bin_list.append(default_path)
    
    return recycle_bin_list

