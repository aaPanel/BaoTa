# coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# |  Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author:  hwliang <hwl@bt.cn>
# +-------------------------------------------------------------------

# --------------------------------
# 宝塔公共库
# --------------------------------
import json, os, sys, time, re, socket, importlib, binascii, base64, string, psutil

_LAN_PUBLIC = None
_LAN_LOG = None
_LAN_TEMPLATE = None

from urllib.parse import urlparse, urlunparse

import warnings
warnings.filterwarnings("ignore", message=r".*doesn't\s+match\s+a\s+supported\s+version", module="requests")

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
        # sql = db.Sql()
        return sql.table(table)


"""
@name 检查表字段是否存在
@param table 被检查的表名  sites
@param field 被检查的字段名  status
@param s_type 字段类型    INTEGER DEFAULT 1
"""


def check_field(table, field, s_type):
    res = M(table).field(field).limit(1).select()
    try:
        if res.find('error') >= 0:
            M(table).execute("ALTER TABLE '{}' ADD '{}' {}".format(table, field, s_type), ())
    except:
        pass
    return True


"""
@name 检查表是否存在
@param table 被检查的表名  sites
@param table_sql 表结构sql语句
"""


def check_table(table, table_sql):
    db_obj = M(table)
    res = db_obj.query("SELECT * FROM sqlite_master WHERE type='table' AND name='{}';".format(table))
    is_create = True
    if not isinstance(res, list): is_create = False
    if len(res) <= 0: is_create = False

    if not is_create:
        db_obj.execute(table_sql, ())
    return True


# 获取计划任务列表
def HttpGet(url, timeout=(3, 6), headers={}):
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
    res = http_requests.get(url, timeout=timeout, headers=headers)
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


def http_get_home(url, timeout, ex):
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
        headers = {"host": home}
        for host in hosts:
            new_url = url.replace(home, host)
            res = HttpGet(new_url, timeout, headers)
            if res:
                writeFile("data/home_host.pl", host)
                set_home_host(host)
                return res
        return ex
    except:
        return ex


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


def httpGet(url, timeout=(3, 6)):
    return HttpGet(url, timeout)


def HttpPost(url, data, timeout=(3, 6), headers={}):
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
    res = http_requests.post(url, data=data, timeout=timeout, headers=headers)
    if res.status_code == 0:
        if headers: return False
        s_body = res.text
        return s_body
    s_body = res.text
    return s_body


def httpPost(url, data, timeout=(3, 6)):
    """
        @name 发送POST请求
        @author hwliang<hwl@bt.cn>
        @param url 被请求的URL地址(必需)
        @param data POST参数，可以是字符串或字典(必需)
        @param timeout 超时时间默认60秒
        @return string
    """
    res = HttpPost(url, data, timeout)
    return res


def check_home():
    return True


def Md5(strings):
    """
        @name    生成MD5
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
    f = open(filename, 'rb')
    while True:
        b = f.read(8096)
        if not b:
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


def ReturnJson(status, msg, args=()):
    """
        @name 取通用Json返回
        @author hwliang<hwl@bt.cn>
        @param status  返回状态
        @param msg  返回消息
        @return string(json)
    """
    return GetJson(ReturnMsg(status, msg, args))


def returnJson(status, msg, args=()):
    """
        @name 取通用Json返回
        @author hwliang<hwl@bt.cn>
        @param status  返回状态
        @param msg  返回消息
        @return string(json)
    """
    return ReturnJson(status, msg, args)


def ReturnMsg(status, msg, args=()):
    """
        @name 取通用dict返回
        @author hwliang<hwl@bt.cn>
        @param status  返回状态
        @param msg  返回消息
        @return dict  {"status":bool,"msg":string}
    """
    try:
        log_message = json.loads(ReadFile('BTPanel/static/language/' + GetLanguage() + '/public.json'))
    except:
        log_message = {}

    keys = log_message.keys()
    if type(msg) == str:
        if msg in keys:
            msg = log_message[msg]
            for i in range(len(args)):
                rep = '{' + str(i + 1) + '}'
                msg = msg.replace(rep, args[i])
    return {'status': status, 'msg': msg}


def returnMsg(status, msg, args=()):
    """
        @name 取通用dict返回
        @author hwliang<hwl@bt.cn>
        @param status  返回状态
        @param msg  返回消息
        @return dict  {"status":bool,"msg":string}
    """
    return ReturnMsg(status, msg, args)


def returnCode(status, msg, code):
    """
        @name 取通用dict返回(带code返回值)
        @author hwliang<
        @param status  返回状态
        @param msg  返回消息
        @param code  返回code
        @return dict  {"status":bool,"msg":string,"code":int}
    """
    return {'status': status, 'msg': msg, 'code': code}


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


class ijson:
    def loads(self, data):
        return json.loads(data)

    def dumps(self, data):
        try:
            try:
                return json.dumps(data)
            except:
                return json.dumps(data, ensure_ascii=False)
        except:
            return json.dumps({'status': False, 'msg': "错误的响应: %s" % str(data)})


def GetJson(data):
    """
    将对象转换为JSON
    @data 被转换的对象(dict/list/str/int...)
    """
    if data == bytes: data = data.decode('utf-8')
    ijson_obj = ijson()
    data = ijson_obj.dumps(data)
    del (ijson_obj)
    return data


def getJson(data):
    return GetJson(data)


def ReadFile(filename, mode='r'):
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
                fp = open(filename, mode, encoding="utf-8", errors='ignore')
                f_body = fp.read()
            except:
                try:
                    fp = open(filename, mode, encoding="GBK", errors='ignore')
                    f_body = fp.read()
                except:
                    return False
        else:
            return False
    finally:
        if fp and not fp.closed:
            fp.close()
    return f_body


def readFile(filename, mode='r'):
    '''
        @name 读取指定文件数据
        @author hwliang<2021-06-09>
        @param filename<string> 文件名
        @param mode<string> 文件打开模式，默认r
        @return string or bytes or False 如果返回False则说明读取失败
    '''
    return ReadFile(filename, mode)


def WriteFile(filename, s_body, mode='w+'):
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
            fp = open(filename, mode, encoding="utf-8")
            fp.write(s_body)
            fp.close()
            return True
        except:
            return False


def writeFile(filename, s_body, mode='w+'):
    '''
        @name 写入到指定文件
        @author hwliang<2021-06-09>
        @param filename<string> 文件名
        @param s_boey<string/bytes> 被写入的内容，字节或字符串
        @param mode<string> 文件打开模式，默认w+
        @return bool
    '''
    return WriteFile(filename, s_body, mode)


def WriteLog(type, logMsg, args=(), not_web=False):
    # 写日志
    try:
        import time, db, json
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
                rep = '{' + str(i + 1) + '}'
                logMsg = logMsg.replace(rep, args[i])
        if type in keys: type = _LAN_LOG[type]

        try:
            if 'login_address' in session:
                logMsg = '{} {}'.format(session['login_address'], logMsg)
        except:
            pass

        sql = db.Sql()
        mDate = time.strftime('%Y-%m-%d %X', time.localtime())
        data = (uid, username, type, logMsg + tmp_msg, mDate)
        result = sql.table('logs').add('uid,username,type,log,addtime', data)
        return result
    except:
        return None


def GetLanguage():
    '''
    取语言
    '''
    return GetConfigValue("language")


def get_language():
    return GetLanguage()


def GetConfigValue(key):
    '''
    @取配置值
    '''
    config = GetConfig()

    if key == 'home': return en_hexb("6148523063484d364c79393364336375596e51755932343d")
    if key == 'download': return en_hexb("6148523063484d364c79396b62336475624739685a4335696443356a62673d3d")
    if not key in config.keys():
        return None
    return config[key]


def SetConfigValue(key, value):
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
    WriteFile(path, json.dumps(config))


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


def GetMsg(key, args=()):
    try:
        global _LAN_PUBLIC
        if not _LAN_PUBLIC:
            _LAN_PUBLIC = json.loads(ReadFile('BTPanel/static/language/' + GetLanguage() + '/public.json'))
        keys = _LAN_PUBLIC.keys()
        msg = None
        if key in keys:
            msg = _LAN_PUBLIC[key]
            for i in range(len(args)):
                rep = '{' + str(i + 1) + '}'
                msg = msg.replace(rep, args[i])
        return msg
    except:
        return key


def getMsg(key, args=()):
    return GetMsg(key, args)


# 获取Web服务器
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
    # 重载Web服务配置
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


def ExecShell(cmdstring, timeout=None, shell=True, cwd=None, env=None, user=None):
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
    import subprocess, tempfile, shutil
    preexec_fn = None
    tmp_dir = '/dev/shm'
    if writeFile(tmp_dir + "/execShell_test.pl", b'\0'*1024, "wb+"):
        try:
            os.remove(tmp_dir + "/execShell_test.pl")
        except:
            pass
    else:
        tmp_dir = "{}/tmp".format(get_panel_path())
        if not os.path.exists(tmp_dir):
            os.makedirs(tmp_dir, exist_ok=True)
    if user:
        preexec_fn = get_preexec_fn(user)
        tmp_dir = '/tmp'

    bash_bin = shutil.which("bash")
    # 将执行命令的shell改为bash，因为Debian13中 &> 的输出重定向被shell截断到&（即后台执行）
    if not bash_bin:
        bash_paths = ("/usr/bin/bash", "/bin/bash", "/usr/local/bin/bash")
        for path in bash_paths:
            if os.path.exists(path):
                bash_bin = path
                break
    try:
        rx = md5(cmdstring)
        succ_f = tempfile.SpooledTemporaryFile(max_size=4096, mode='wb+', suffix='_succ', prefix='btex_' + rx, dir=tmp_dir)
        err_f = tempfile.SpooledTemporaryFile(max_size=4096, mode='wb+', suffix='_err', prefix='btex_' + rx, dir=tmp_dir)
        # env = {"BT-NAME":"panel"}
        sub = subprocess.Popen(cmdstring, close_fds=True, shell=shell, bufsize=128, stdout=succ_f, stderr=err_f, cwd=cwd, env=env, preexec_fn=preexec_fn, executable=bash_bin)
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
        return '', get_error_info()
    try:
        # 编码修正
        if type(a) == bytes: a = a.decode('utf-8')
        if type(e) == bytes: e = e.decode('utf-8')
    except:
        a = str(a)
        e = str(e)

    return a, e


def GetLocalIp():
    # 取本地外网IP
    try:
        filename = 'data/iplist.txt'
        ipaddress = readFile(filename)
        if not ipaddress:
            url = GetConfigValue('home') + '/Api/getIpAddress'
            m_str = HttpGet(url)
            ipaddress = re.search(r"^\d{1,3}.\d{1,3}.\d{1,3}.\d{1,3}$", m_str).group(0)
            WriteFile(filename, ipaddress)
        c_ip = check_ip(ipaddress.strip())
        if not c_ip: return GetHost().strip()
        return ipaddress.strip()
    except:
        try:
            url = GetConfigValue('home') + '/Api/getIpAddress'
            return HttpGet(url).strip()
        except:
            return GetHost().strip()


def is_ipv4(ip):
    '''
        @name 是否是IPV4地址
        @author hwliang
        @param ip<string> IP地址
        @return True/False
    '''
    # 验证基本格式
    if not re.match(r"^\d{1,3}.\d{1,3}.\d{1,3}.\d{1,3}$", ip):
        return False

    # 验证每个段是否在合理范围
    try:
        socket.inet_pton(socket.AF_INET, ip)
    except AttributeError:
        try:
            socket.inet_aton(ip)
        except socket.error:
            return False
    except socket.error:
        return False
    return True


def is_ipv6(ip):
    '''
        @name 是否为IPv6地址
        @author hwliang
        @param ip<string> 地址
        @return True/False
    '''
    # 验证基本格式
    if not re.match(r"^[\w:]+$", ip):
        return False

    # 验证IPv6地址
    try:
        socket.inet_pton(socket.AF_INET6, ip)
    except socket.error:
        return False
    return True


def check_ip(ip):
    return is_ipv4(ip) or is_ipv6(ip)


def GetHost(port=False):
    from flask import request
    host_tmp = request.headers.get('host')
    # 验证基本格式
    if host_tmp:
        if not re.match("^[\w\.\:\-]+$", host_tmp):
            host_tmp = ''

    if not host_tmp:
        if request.url_root:
            tmp = re.findall(r"(https|http)://([\w:\.-]+)", request.url_root)
            if tmp: host_tmp = tmp[0][1]
    if not host_tmp:
        host_tmp = '127.0.0.1:' + readFile('data/port.pl').strip()
    try:
        # 不能使用80作为默认端口
        if host_tmp.find(':') == -1: host_tmp += (':{}'.format(readFile('data/port.pl')))
    except:
        host_tmp = "127.0.0.1:8888"
    h = host_tmp.split(':')
    if port: return h[-1]
    return ':'.join(h[0:-1])


def GetClientIp():
    from flask import request
    ipaddr = request.remote_addr
    if ipaddr:
        ipaddr = ipaddr.replace('::ffff:', '')
    if ipaddr in ('127.0.0.1', '::1', "localhost"): # 仅信任本地代理，在本地代理时，认为是开启了免端口访问
        forwarded_ips = request.headers.get('X-Forwarded-For', "").split(',')
        if len(forwarded_ips) > 0:
            ipaddr = forwarded_ips[-1]
        elif "X-Real-Ip" in request.headers:
            ipaddr = request.headers.get('X-Real-Ip')

    if not isinstance(ipaddr, str):
        return '未知IP地址'

    ipaddr = ipaddr.replace('::ffff:', '')

    if not check_ip(ipaddr): return '未知IP地址'
    return ipaddr


def get_remote_port():
    '''
        @name 获取客户端端口号
        @return int
    '''
    from flask import request
    port = request.headers.get('X-Real-Port', '0')
    if port == '0': port = request.environ.get('REMOTE_PORT')
    return str(port)


def get_client_ip():
    return GetClientIp()


def phpReload(version):
    # 重载PHP配置
    import os
    if os.path.exists(get_setup_path() + '/php/' + version + '/libphp5.so'):
        ExecShell('/etc/init.d/httpd reload')
    else:
        ExecShell('/etc/init.d/php-fpm-' + version + ' reload')
        ExecShell("/etc/init.d/php-fpm-{} start".format(version))


def get_timeout(url, timeout=3):
    try:
        start = time.time()
        result = int(httpGet(url, timeout))
        return result, int((time.time() - start) * 1000 - 500)
    except:
        return 0, False


def get_url(timeout=0.5):
    try:
        import json
        res = json.loads(readFile('{}/data/node_url.pl'.format(get_panel_path())))
        down_url = res['down-node']['url']
        if down_url:
            return "https://{}".format(down_url)
    except:
        pass
    return 'https://download.bt.cn'

    import json
    try:
        pkey = 'node_url'
        node_url = cache_get(pkey)
        if node_url: return node_url
        nodeFile = 'data/node.json'
        node_list = json.loads(readFile(nodeFile))
        mnode1 = []
        mnode2 = []
        mnode3 = []
        new_node_list = {}
        for node in node_list:
            node['net'], node['ping'] = get_timeout(node['protocol'] + node['address'] + ':' + node['port'] + '/net_test', 1)
            new_node_list[node['address']] = node['ping']
            if not node['ping']: continue
            if node['ping'] < 100:  # 当响应时间<100ms且可用带宽大于1500KB时
                if node['net'] > 1500:
                    mnode1.append(node)
                elif node['net'] > 1000:
                    mnode3.append(node)
            else:
                if node['net'] > 1000:  # 当响应时间>=100ms且可用带宽大于1000KB时
                    mnode2.append(node)
            if node['ping'] < 100:
                if node['net'] > 3000: break  # 有节点可用带宽大于3000时，不再检查其它节点
        if mnode1:  # 优选低延迟高带宽
            mnode = sorted(mnode1, key=lambda x: x['net'], reverse=True)
        elif mnode3:  # 备选低延迟，中等带宽
            mnode = sorted(mnode3, key=lambda x: x['net'], reverse=True)
        else:  # 终选中等延迟，中等带宽
            mnode = sorted(mnode2, key=lambda x: x['ping'], reverse=False)

        if not mnode: return 'http://download.bt.cn'

        new_node_keys = new_node_list.keys()
        for i in range(len(node_list)):
            if node_list[i]['address'] in new_node_keys:
                node_list[i]['ping'] = new_node_list[node_list[i]['address']]
            else:
                node_list[i]['ping'] = 500

        new_node_list = sorted(node_list, key=lambda x: x['ping'], reverse=False)
        writeFile(nodeFile, json.dumps(new_node_list))
        node_url = mnode[0]['protocol'] + mnode[0]['address'] + ':' + mnode[0]['port']
        cache_set(pkey, node_url, 86400)
        return node_url
    except:
        return 'http://download.bt.cn'


# 过滤输入
def checkInput(data):
    if not data: return data
    if type(data) != str: return data
    checkList = [
        {'d': '<', 'r': '＜'},
        {'d': '>', 'r': '＞'},
        {'d': '\'', 'r': '‘'},
        {'d': '"', 'r': '“'},
        {'d': '&', 'r': '＆'},
        {'d': '#', 'r': '＃'},
        {'d': '<', 'r': '＜'}
    ]
    for v in checkList:
        data = data.replace(v['d'], v['r'])
    return data


# 取文件指定尾行数
def GetNumLines(path, num, p=1):
    if not os.path.exists(path): return ""
    if isinstance(num, str) and not re.match("\d+", num):
        return ""

    pyVersion = sys.version_info[0]
    max_len = 1024 * 1024 * 10
    try:

        start_line = (p - 1) * num
        count = start_line + num
        fp = open(path, 'rb')
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
                            data.insert(0, line)
                        except:
                            pass
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
                        t_buf = t_buf.decode('utf-8', errors='ignore')

                    buf = t_buf + buf
                    fp.seek(-to_read, 1)
                    if pos - to_read == 0:
                        buf = "\n" + buf
                if total_len >= max_len: break
            if not b: break
        fp.close()
        result = "\n".join(data)
    except:
        if re.match("[`\$\&\;]+", path): return ""
        result = ExecShell("tail -n {} {}".format(num, path))[0]
        if len(result) > max_len:
            result = result[-max_len:]

    try:
        try:
            result = json.dumps(result)
            return json.loads(result).strip()
        except:
            if pyVersion == 2:
                result = result.decode('utf8', errors='ignore')
            else:
                result = result.encode('utf-8', errors='ignore').decode("utf-8", errors="ignore")
        return result.strip()
    except:
        return ""


# 验证证书
def CheckCert(certPath='ssl/certificate.pem'):
    try:
        return get_cert_data(certPath)
    except:
        openssl = '/usr/local/openssl/bin/openssl'
        if not os.path.exists(openssl): openssl = 'openssl'
        certPem = readFile(certPath)
        s = "\n-----BEGIN CERTIFICATE-----"
        tmp = certPem.strip().split(s)
        res = True
        for tmp1 in tmp:
            if tmp1.find('-----BEGIN CERTIFICATE-----') == -1:  tmp1 = s + tmp1
            writeFile(certPath, tmp1)
            result = ExecShell(openssl + " x509 -in " + certPath + " -noout -subject")
            if result[1].find('-bash:') != -1: res = True
            if len(result[1]) > 2: res = False
            if result[0].find('error:') != -1: res = False
        return res


# 获取面板地址
def getPanelAddr():
    from flask import request
    protocol = 'https://' if os.path.exists("data/ssl.pl") else 'http://'
    host = request.headers.get('host')
    if host.find(':') == -1:
        host = "{}:{}".format(host,get_panel_port())
    return protocol + host


# 字节单位转换
def to_size(size):
    if not size: return '0.00 b'
    size = float(size)
    d = ('b', 'KB', 'MB', 'GB', 'TB')
    s = d[0]
    for b in d:
        if size < 1024: return ("%.2f" % size) + ' ' + b
        size = size / 1024
        s = b
    return ("%.2f" % size) + ' ' + b


def checkCode(code, outime=120):
    # 校验验证码
    from BTPanel import session, cache
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


# 写进度
def writeSpeed(title, used, total, speed=0):
    import json
    if not title:
        data = {'title': None, 'progress': 0, 'total': 0, 'used': 0, 'speed': 0}
    else:
        try:
            progress = int((100.0 * used / total))
        except:
            progress = 0
        data = {'title': title, 'progress': progress, 'total': total, 'used': used, 'speed': speed}
    writeFile('/tmp/panelSpeed.pl', json.dumps(data))
    return True


# 取进度
def getSpeed():
    import json;
    data = readFile('/tmp/panelSpeed.pl')
    if not data:
        data = json.dumps({'title': None, 'progress': 0, 'total': 0, 'used': 0, 'speed': 0})
        writeFile('/tmp/panelSpeed.pl', data)
    return json.loads(data)


def get_requests_headers():
    return {"Content-type": "application/x-www-form-urlencoded", "User-Agent": "BT-Panel"}


# 替换官网节点
def get_home_node(url):
    try:
        parsed_url = urlparse(url)
        domain = parsed_url.netloc
        if domain in ['www.bt.cn', 'api.bt.cn', 'download.bt.cn']:
            if parsed_url.path in ['/api/index']:
                return url
            sfile = '{}/data/node_url.pl'.format(get_panel_path())
            node_info = json.loads(readFile(sfile))
            if domain == 'www.bt.cn':
                if not node_info['www-node']:
                    return url
                return urlunparse(parsed_url._replace(netloc=node_info['www-node']['url']))
            elif domain == 'api.bt.cn':
                if not node_info['api-node']:
                    return url
                return urlunparse(parsed_url._replace(netloc=node_info['api-node']['url']))
            elif domain == 'download.bt.cn':
                if not node_info['down-node']:
                    return url
                return urlunparse(parsed_url._replace(netloc=node_info['down-node']['url']))
    except:
        pass
    return url


def downloadFile(url, filename):
    try:

        url = get_home_node(url)
        import requests, config
        from requests.packages.urllib3.exceptions import InsecureRequestWarning
        requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
        import requests.packages.urllib3.util.connection as urllib3_conn
        _ip_type = config.config().get_request_iptype()
        # old_family = urllib3_conn.allowed_gai_family
        if _ip_type == 'ipv4':
            urllib3_conn.allowed_gai_family = lambda: socket.AF_INET
        elif _ip_type == 'ipv6':
            urllib3_conn.allowed_gai_family = lambda: socket.AF_INET6
        try:
            res = requests.get(url, headers=get_requests_headers(), timeout=30, stream=True)
        except Exception as ex:
            raise PanelError(error_conn_cloud(str(ex)))
        finally:
            # urllib3_conn.allowed_gai_family = old_family
            reset_allowed_gai_family()
        with open(filename, "wb") as f:
            for _chunk in res.iter_content(chunk_size=8192):
                f.write(_chunk)
    except:
        ExecShell("wget -O {} {} --no-check-certificate".format(filename, url))


def exists_args(args, get):
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
            "find": "[PATH]",
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

    info_file = '{}/{}/info.json'.format(get_plugin_path(), plugin_name)
    try:
        return json.loads(readFile(info_file))['title']
    except:
        return plugin_name


def get_error_object(plugin_title=None, plugin_name=None):
    '''
        @name 获取格式化错误响应对像
        @author hwliang<2021-06-21>
        @return Resp
    '''
    if not plugin_title: plugin_title = get_plugin_title(plugin_name)
    try:
        from BTPanel import request, Resp
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
        request_date=getDate(),
        remote_addr=GetClientIp(),
        method=request.method,
        full_path=url_encode(xsssec(request.full_path)),
        request_form=xsssec(str(request.form.to_dict())),
        user_agent=xsssec(request.headers.get('User-Agent')),
        panel_version=version(),
        os_version=get_os_version()
    )

    result = readFile('{}/BTPanel/templates/default/plugin_error.html'.format(get_panel_path())).format(
        plugin_name=plugin_title,
        request_info=request_info,
        error_title=error_info.split("\n")[-1],
        error_msg=error_info
    )
    return Resp(result, 500)


def submit_error(err_msg=None):
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
        httpPost(GetConfigValue('home') + "/api/panel/s_error", pdata, timeout=3)
    except:
        pass


# 搜索数据中是否存在
def inArray(arrays, searchStr):
    for key in arrays:
        if key == searchStr: return True

    return False


# 格式化指定时间戳
def format_date(format="%Y-%m-%d %H:%M:%S", times=None):
    if not times: times = int(time.time())
    time_local = time.localtime(times)
    return time.strftime(format, time_local)


# 检查Web服务器配置文件是否有错误
def checkWebConfig(repair_num=3):
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
            writeFile(f1 + 'apache/btwaf.conf', 'LoadModule lua_module modules/mod_lua.so')
            writeFile(f1 + 'apache/total.conf', 'LuaHookLog {}/total/httpd_log.lua run_logs'.format(setup_path))
        else:
            f3 = f1 + 'apache/total.conf'
            if os.path.exists(f3): os.remove(f3)

    web_s = get_webserver()
    if web_s == 'nginx':
        result = ExecShell("ulimit -n 8192 ; {setup_path}/nginx/sbin/nginx -t -c {setup_path}/nginx/conf/nginx.conf".format(setup_path=setup_path))
        searchStr = 'successful'
        nginx_version = ExecShell("{}/nginx/sbin/nginx -v".format(setup_path))
        version_info = nginx_version[1]
    elif web_s == 'apache':
        # else:
        result = ExecShell("ulimit -n 8192 ; {setup_path}/apache/bin/apachectl -t".format(setup_path=setup_path))
        searchStr = 'Syntax OK'
        apache_version = ExecShell("{}/apache/bin/httpd -v".format(setup_path))
        version_info = apache_version[1]
    else:
        result = ["1", "1"]
        searchStr = "1"
        version_info = "Unknow"

    if result[1].find('unknown log format "monitor"') != -1 and web_s == "nginx":
        if repair_num > 0:
            repair_num -= 1
            repair_monitor_log_format(result[1])
            return checkWebConfig(repair_num)

    if result[1].find('the "listen ... http2" directive is deprecated, use the "http2" directive instead') != -1 and web_s == "nginx" and is_change_nginx_http2():
        if repair_num > 0:
            repair_num -= 1
            change_nginx_http2()
            return checkWebConfig(repair_num)

    if result[1].find(searchStr) == -1:
        if result[1].find('[emerg] unknown directive "http2"') != -1 and web_s == "nginx" and is_change_nginx_old_http2():
            if repair_num > 0:
                repair_num -= 1
                change_nginx_old_http2()
                return checkWebConfig(repair_num)

        if result[1].find('[emerg] invalid parameter "quic" in') != -1 and web_s == "nginx" and not is_nginx_http3():
            if repair_num > 0:
                repair_num -= 1
                remove_nginx_quic()
                return checkWebConfig(repair_num)

        if result[1].find('well-known') != -1 and web_s == "nginx" and result[1].find("No such file") != -1:
            if repair_num > 0:
                repair_num -= 1
                repair_not_such_well_know(result[1])
                return checkWebConfig(repair_num)

        if result[1].find('/conf/enable-php') != -1 and web_s == "nginx" and result[1].find("No such file") != -1:
            if repair_num > 0:
                repair_num -= 1
                repair_not_such_enable_php(result[1])
                return checkWebConfig(repair_num)
        if result[1].find('[emerg] "ssl_protocols" must enable TLSv1.3 for the "listen ... quic" directive') != -1 and web_s == "nginx":
            if repair_num > 0:
                repair_num -= 1
                repair_nginx_quic_ssl_protocols()
                return checkWebConfig(repair_num)

        WriteLog("TYPE_SOFT", 'CONF_CHECK_ERR', (result[1],))
        collect_type = 0
        # if collect_to_other_error(result[1]):
        #     collect_type = 4
        try:
            err_info = [
                "错误信息原文：\n{}".format(result[1].strip()),
                "版本信息: {}".format(version_info.strip()),
                "报错文件列表："
            ]
            rep_file = re.compile(r"in\s+(/.*):(\d+)", re.M)
            for idx, tmp_res in enumerate(rep_file.finditer(result[1])):
                err_info.append("第{}个文件-----------------------------".format(idx + 1))
                err_info.append("{} 第 {} 行".format(tmp_res.group(1), tmp_res.group(2)))
                try:
                    t_idx = int(tmp_res.group(2))
                    err_info.append(
                        read_file_lines_range(tmp_res.group(1), max(0, t_idx - 5), t_idx + 5)
                    )
                except:
                    err_info.append("读取文件失败")

            err_collect("\n".join(err_info), collect_type, result[1].split("\n")[0].strip())

        except Exception as e:
            try:
                err_collect(result[1], collect_type, result[1].split("\n")[0].strip())
            except:
                pass
        try:
            conf_err = '{} \n {} '.format(version_info.strip(), result[1])
            return conf_err
        except:
            pass
        return result[1]
    return True


# 检查是否为IPv4地址
def checkIp(ip):
    p = re.compile(r'^((25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(25[0-5]|2[0-4]\d|[01]?\d\d?)$')
    if p.match(ip):
        return True
    else:
        return False


# 检查端口是否合法
def checkPort(port):
    if not re.match("^\d+$", port): return False
    ports = ['21', '25', '443', '8080', '888', '8888', '8443']
    if port in ports: return False
    intport = int(port)
    if intport < 1 or intport > 65535: return False
    return True


# 字符串取中间
def getStrBetween(startStr, endStr, srcStr):
    start = srcStr.find(startStr)
    if start == -1: return None
    end = srcStr.find(endStr)
    if end == -1: return None
    return srcStr[start + 1:end]


# 取CPU类型
def getCpuType():
    cpuinfo = open('/proc/cpuinfo', 'r').read()
    rep = "model\s+name\s+:\s+(.+)"
    tmp = re.search(rep, cpuinfo, re.I)
    cpuType = ''
    if tmp:
        cpuType = tmp.groups()[0]
    else:
        cpuinfo = ExecShell('LANG="en_US.UTF-8" && lscpu')[0]
        rep = "Model\s+name:\s+(.+)"
        tmp = re.search(rep, cpuinfo, re.I)
        if tmp: cpuType = tmp.groups()[0]
    return cpuType


# 检查是否允许重启
def IsRestart():
    num = M('tasks').where('status!=?', ('1',)).count()
    if num > 0: return False
    return True


# 加密密码字符
def hasPwd(password):
    import crypt;
    return crypt.crypt(password, password)


def getDate(format='%Y-%m-%d %X'):
    # 取格式时间
    return time.strftime(format, time.localtime())


# 处理MySQL配置文件
def CheckMyCnf():
    import os;
    confFile = '/etc/my.cnf'
    if os.path.exists(confFile):
        conf = readFile(confFile)
        if conf.find('[mysqld]') != -1: return True
    versionFile = get_setup_path() + '/mysql/version.pl'
    if not os.path.exists(versionFile): return False

    versions = ['5.1', '5.5', '5.6', '5.7', '8.0', 'AliSQL']
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
    # 判断是否迁移目录
    if os.path.exists('data/datadir.pl'):
        newPath = readFile('data/datadir.pl')
        if os.path.exists(newPath):
            mycnf = readFile('/etc/my.cnf')
            mycnf = mycnf.replace('/www/server/data', newPath)
            writeFile('/etc/my.cnf', mycnf)
    WriteLog('TYPE_SOFE', 'MYSQL_CHECK_ERR')
    return True


def get_ssh_port():
    '''
        @name 获取本机SSH端口
        @author hwliang<2020-08-07>
        @return int
    '''
    s_file = '/etc/ssh/sshd_config'
    conf = readFile(s_file)
    if not conf: conf = ''
    port_all = re.findall(r".*Port\s+[0-9]+", conf)
    ssh_port = 22
    for p in port_all:
        rep = r"^\s*Port\s+([0-9]+)\s*"
        tmp1 = re.findall(rep, p)
        if tmp1:
            ssh_port = int(tmp1[0])

    return ssh_port


def GetSSHPort():
    # try:
    #     file = '/etc/ssh/sshd_config'
    #     conf = ReadFile(file)
    #     rep = "#*Port\s+([0-9]+)\s*\n"
    #     port = re.search(rep, conf).groups(0)[0]
    #     return int(port)
    # except:
    #     return 22

    try:
        file_list = ['/etc/ssh/sshd_config',]
        if os.path.isdir("/etc/ssh/sshd_config.d"):
            for file in os.listdir("/etc/ssh/sshd_config.d"):
                if file.endswith(".conf"):
                    file_list.insert(0, os.path.join("/etc/ssh/sshd_config.d", file))

        regexp = re.compile(r'(?P<sgin>#.*)?[ \t\r\v\f]*Port\s+(?P<port>[0-9]+)(\s+|#)')
        port_list = []
        for file in file_list:
            conf = ReadFile(file)
            for tmp in regexp.finditer(conf):
                if not tmp.group('sgin'):
                    port_list.append(int(tmp.group('port')))
        if len(port_list) == 0:
            return 22
        print_log(port_list)
        return port_list[0]
    except:
        return 22


def get_sshd_port():
    '''
        @name 获取sshd端口
        @author hwliang
        @return int
    '''
    # 先尝试从进程中获取当前实际的监听端口
    sshd_port = 22
    is_ok = 0
    pid = get_sshd_pid_of_pidfile()
    if not pid: pid = get_sshd_pid_of_binfile()
    if pid:
        try:
            import psutil
            p = psutil.Process(pid)
            for conn in p.connections():
                if conn.status == 'LISTEN':
                    sshd_port = conn.laddr[1]
                    is_ok = 1
                    break
        except:
            pass

    # 如果从进程获取失败，则尝试从配置文件获取
    if not is_ok: sshd_port = GetSSHPort()

    return sshd_port


def get_sshd_pid_of_pidfile():
    '''
        @name 通过PID文件获取SSH状态
        @author hwliang
        @return int 0:关闭 pid:开启
    '''
    sshd_pid_list = ['/run/sshd.pid', '/var/run/sshd.pid', '/run/ssh.pid', '/var/run/ssh.pid']
    sshd_pid_file = None
    for spid_file in sshd_pid_list:
        if os.path.exists(spid_file):
            sshd_pid_file = spid_file
            break

    if sshd_pid_file:
        sshd_pid = readFile(sshd_pid_file)
        if not sshd_pid: return 0
        try:
            sshd_pid = int(sshd_pid)
            if not sshd_pid: return 0
            if pid_exists(sshd_pid):
                return sshd_pid
        except:
            pass
    return 0


def get_sshd_pid_of_binfile():
    '''
        @name 通过执行文件获取SSH状态
        @author hwliang
        @return int 进程pid
    '''
    sshd_bin_list = ['/usr/sbin/sshd', '/usr/bin/sshd', '/usr/sbin/ssh', '/usr/bin/ssh']
    sshd_bin = None
    pid = 0
    for sbin in sshd_bin_list:
        if os.path.exists(sbin):
            sshd_bin = sbin
            break
    try:
        if sshd_bin:
            pid = get_process_pid(sshd_bin.split('/')[-1], sshd_bin, '-D')
    except:
        pass

    return pid


def GetSSHStatus():
    '''
        @name 获取SSH状态
        @author hwliang
        @return bool
    '''
    if get_sshd_pid_of_pidfile():
        return True
    elif get_sshd_pid_of_binfile():
        return True
    return False


def get_sshd_status():
    '''
        @name 获取SSH状态
        @author hwliang
        @return bool
    '''
    return GetSSHStatus()


def set_sshd_status(status_act: str = "restart"):
    """
        @name 设置SSH状态
        @author baozi
        @param status_act: str 状态操作 restart|start|stop
        @return bool
    """
    if os.path.exists("/etc/init.d/sshd"):
        ExecShell("/etc/init.d/sshd {}".format(status_act))
    elif os.path.exists("/etc/init.d/ssh"):
        ExecShell("/etc/init.d/ssh {}".format(status_act))
    else:
        cmd = """
SU_DO=""
if command -v sudo >/dev/null 2>&1; then
    SU_DO="sudo"
fi

SERVICE_NAME=""
if "$SU_DO" systemctl list-unit-files --type=service | grep -q 'sshd.service'; then
    SERVICE_NAME="sshd.service"
elif "$SU_DO" systemctl list-units-files --type=service | grep -q 'ssh.service'; then
    SERVICE_NAME="ssh.service"
else
    echo "Error: Neither sshd.service nor ssh.service exists."
    exit 1
fi

"$SU_DO" systemctl {} "$SERVICE_NAME"  
""".format(status_act)
        out, err = ExecShell(cmd)
        print_log("sshd 启动成功")
        if "Error" in (out + err) and is_debug():
            print_log("sshd 启动失败")

    return None


# 检查端口是否合法
def CheckPort(port, other=None):
    if type(port) == str: port = int(port)
    if port < 1 or port > 65535: return False
    if other:
        checks = [22, 20, 21, 8888, 3306, 11211, 888, 25]
        if port in checks: return False
    return True


# 获取Token
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
    skey = md5(pluginCode + 'code')
    if cache: pluginInfo = cache.get(skey)
    if not pluginInfo:
        import panelAuth
        pdata = panelAuth.panelAuth().create_serverid(None)
        pdata['pid'] = pluginCode
        url = GetConfigValue('home') + '/api/panel/get_py_module'
        pluginTmp = httpPost(url, pdata)
        try:
            pluginInfo = json.loads(pluginTmp)
        except:
            if not os.path.exists(p_tk): return False
            pluginInfo = json.loads(ReadFile(p_tk))
        if pluginInfo['status'] == False: return False
        WriteFile(p_tk, json.dumps(pluginInfo))
        os.chmod(p_tk, 384)
        if cache: cache.set(skey, pluginInfo, 1800)

    mod = sys.modules.setdefault(pluginCode, new_module(pluginCode))
    code = compile(pluginInfo['msg'].encode('utf-8'), pluginCode, 'exec')
    mod.__file__ = pluginCode
    mod.__package__ = ''
    exec(code, mod.__dict__)
    return mod


# 解密数据
def auth_decode(data):
    token = GetToken()
    # 是否有生成Token
    if not token: return returnMsg(False, 'REQUEST_ERR')

    # 校验access_key是否正确
    if token['access_key'] != data['btauth_key']: return returnMsg(False, 'REQUEST_ERR')

    # 解码数据
    import binascii, hashlib, urllib, hmac, json
    tdata = binascii.unhexlify(data['data'])

    # 校验signature是否正确
    signature = binascii.hexlify(hmac.new(token['secret_key'], tdata, digestmod=hashlib.sha256).digest())
    if signature != data['signature']: return returnMsg(False, 'REQUEST_ERR')

    # 返回
    return json.loads(urllib.unquote(tdata))


# 数据加密
def auth_encode(data):
    token = GetToken()
    pdata = {}

    # 是否有生成Token
    if not token: return returnMsg(False, 'REQUEST_ERR')

    # 生成signature
    import binascii, hashlib, urllib, hmac, json
    tdata = urllib.quote(json.dumps(data))
    # 公式  hex(hmac_sha256(data))
    pdata['signature'] = binascii.hexlify(hmac.new(token['secret_key'], tdata, digestmod=hashlib.sha256).digest())

    # 加密数据
    pdata['btauth_key'] = token['access_key']
    pdata['data'] = binascii.hexlify(tdata)
    pdata['timestamp'] = time.time()

    # 返回
    return pdata


# 检查Token
def checkToken(get):
    tempFile = 'data/tempToken.json'
    if not os.path.exists(tempFile): return False
    import json, time
    tempToken = json.loads(readFile(tempFile))
    if time.time() > tempToken['timeout']: return False
    if get.token != tempToken['token']: return False
    return True


# 获取识别码
def get_uuid():
    import uuid
    return uuid.UUID(int=uuid.getnode()).hex[-12:]


# 取计算机名
def get_hostname():
    import socket
    return socket.gethostname()


# 取mysql datadir
def get_datadir():
    mycnf_file = '/etc/my.cnf'
    if not os.path.exists(mycnf_file): return ''
    mycnf = readFile(mycnf_file)
    if isinstance(mycnf, str) and mycnf.find('[mysqld]') > -1:
        import re
        tmp = re.findall(r"datadir\s*=\s*(.+)", mycnf)
        if not tmp:
            return ''
        return tmp[0]
    return ''


# 进程是否存在
def process_exists(pname, exe=None, cmdline=None):
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
                            if cmdline in p.cmdline(): return True
            except:
                pass
        return False
    except:
        return True


def get_process_pid(pname, exe=None, cmdline=None):
    '''
        @name 通过进程名获取进程PID
        @author hwliang
        @param pname 进程名
        @param exe 进程路径
        @param cmdline 进程任意命令行参数
        @return  int 返回进程PID
    '''
    import psutil
    pids = psutil.pids()
    for pid in pids:
        try:
            p = psutil.Process(pid)
            if p.name() == pname:
                if not exe and not cmdline:
                    return pid
                else:
                    if exe:
                        if p.exe() == exe:
                            if not cmdline:
                                return pid
                            return 0
                    if cmdline:
                        if cmdline in p.cmdline(): return pid
        except:
            pass
    return 0


# pid是否存在
def pid_exists(pid):
    if os.path.exists('/proc/{}/exe'.format(pid)):
        return True
    return False


# 重启面板
def restart_panel():
    import system
    return system.system().ReWeb(None)


# 获取mac
def get_mac_address():
    import uuid
    mac = uuid.UUID(int=uuid.getnode()).hex[-12:]
    return ":".join([mac[e:e + 2] for e in range(0, 11, 2)])


# 转码
def to_string(lites):
    if type(lites) != list: lites = [lites]
    m_str = ''
    for mu in lites:
        if sys.version_info[0] == 2:
            m_str += unichr(mu).encode('utf-8')
        else:
            m_str += chr(mu)
    return m_str


# 解码
def to_ord(string):
    o = []
    for s in string:
        o.append(ord(s))
    return o


# xss 防御
def xssencode(text):
    try:
        from cgi import html
        list = ['`', '~', '&', '#', '/', '*', '$', '@', '<', '>', '\"', '\'', ';', '%', ',', '.', '\\u']
        ret = []
        for i in text:
            if i in list:
                i = ''
            ret.append(i)
        str_convert = ''.join(ret)
        text2 = html.escape(str_convert, quote=True)
        return text2
    except:
        return text.replace('&', '&amp;').replace('"', '&quot;').replace('<', '&lt;').replace('>', '&gt;')


def html_decode(text):
    '''
        @name HTML解码
        @author hwliang
        @param text 要解码的HTML
        @return string 返回解码后的HTML
    '''
    try:
        from cgi import html
        text2 = html.unescape(text)
        return text2
    except:
        return text


def html_encode(text):
    '''
        @name HTML编码
        @author hwliang
        @param text 要编码的HTML
        @return string 返回编码后的HTML
    '''
    try:
        from cgi import html
        text2 = html.escape(text)
        return text2
    except:
        return text


# xss 防御
def xsssec(text):
    return xsssec3(text)  # text.replace('&', '&amp;').replace('"', '&quot;').replace('<', '&lt;').replace('>', '&gt;')


# xss 防御
def xsssec2(text):
    if not text or not isinstance(text, str): return text
    return text.replace('<', '&lt;').replace('>', '&gt;')


def xsssec3(text):
    '''
        @name XSS防御，只替换关键字符，不转义字符
        @author hwliang
        @param text 要转义的字符
        @return str
    '''
    sub_list = {
        '<': '＜',
        '>': '＞',
        '"': '＂',
        "'": '＇'
    }
    for s in sub_list.keys():
        text = text.replace(s, sub_list[s])
    return text


# xss version
def xss_version(text):
    try:
        if not text or not isinstance(text, str): return text
        text = text.strip()
        list = ['`', '~', '&', '#', '/', '*', '$', '@', '<', '>', '\"', '\'', ';', '%', ',', '\\u']
        ret = []
        for i in text:
            if i in list:
                i = ''
            ret.append(i)
        str_convert = ''.join(ret)
        return str_convert
    except:
        return text.replace('&', '&amp;').replace('"', '&quot;').replace('<', '&lt;').replace('>', '&gt;')


# 获取数据库配置信息
def get_mysql_info():
    data = {}
    try:
        CheckMyCnf()
        myfile = '/etc/my.cnf'
        mycnf = readFile(myfile)
        rep = "datadir\s*=\s*(.+)\n"
        data['datadir'] = re.search(rep, mycnf).groups()[0]
        rep = "port\s*=\s*([0-9]+)\s*\n"
        data['port'] = re.search(rep, mycnf).groups()[0]
    except:
        data['datadir'] = '/www/server/data'
        data['port'] = '3306'
    return data


# xss 防御
def xssencode2(text):
    try:
        from cgi import html
        text2 = html.escape(text, quote=True)
        return text2
    except:
        return text.replace('&', '&amp;').replace('"', '&quot;').replace('<', '&lt;').replace('>', '&gt;')


# 取缓存
def cache_get(key):
    from BTPanel import cache
    return cache.get(key)


def add_security_logs(type, log, is_ip=True):
    try:
        if is_ip:
            from flask import request
            log = GetClientIp() + ":" + str(get_remote_port()) + log
        M('security').add('type,log,addtime', (type, log, time.strftime('%Y-%m-%d %X', time.localtime())))
    except:
        pass


# 设置缓存
def cache_set(key, value, timeout=None):
    from BTPanel import cache
    if value == 'check':
        admin_path = "/www/server/panel/data/admin_path.pl"
        path = ReadFile(admin_path)
        if path and len(path) > 3:
            if not cache.get(GetClientIp() + 'admin_path_info'):
                add_security_logs("安全入口正确", "访问安全入口成功")
                cache.set(GetClientIp() + 'admin_path_info', 1, 60)
    return cache.set(key, value, timeout)


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
def sess_set(key, value):
    from BTPanel import session
    session[key] = value
    return True


# 删除指定session值
def sess_remove(key):
    from BTPanel import session
    if key in session: del (session[key])
    return True


# 构造分页
def get_page(count, p=1, rows=12, callback='', result='1,2,3,4,5,8'):
    import page
    try:
        from BTPanel import request
        uri = url_encode(request.full_path)
    except:
        uri = ''
    page = page.Page()
    info = {'count': count, 'row': rows, 'p': p, 'return_js': callback, 'uri': uri}
    data = {'page': page.GetPage(info, result), 'shift': str(page.SHIFT), 'row': str(page.ROW)}
    return data


# 取面板版本
def version():
    try:
        comm = ReadFile('{}/common.py'.format(get_class_path()))
        return re.search("g\.version\s*=\s*'(\d+\.\d+\.\d+)'", comm).groups()[0]
    except:
        return get_panel_version()


def get_panel_version():
    comm = ReadFile('{}/common.py'.format(get_class_path()))
    s_key = 'g.version = '
    s_len = len(s_key)
    s_leff = comm.find(s_key) + s_len
    version = comm[s_leff:s_leff + 10].strip().strip("'")
    return version


def get_os_version():
    '''
        @name 取操作系统版本
        @author hwliang<2021-08-07>
        @return string
    '''
    version = ""
    if os.path.exists("/etc/.productinfo"):
        s_tmp = readFile("/etc/.productinfo").split("\n")
        if s_tmp[0].find('Kylin') != -1 and len(s_tmp) > 1:
            version = s_tmp[0] + ' ' + s_tmp[1].split('/')[0].strip()

    release_version = ("/etc/redhat-release", "/etc/system-release", "/etc/amazon-linux-release")
    for tmp_file in release_version:
        if not version and os.path.exists(tmp_file):
            s_tmp = readFile(tmp_file)
            version = s_tmp
            break

    if not version:
        for path_tmp in str(readFile("/etc/os-release")).split("\n"):
            tmp_list = path_tmp.split("=")
            if len(tmp_list) >= 2:
                name, value = tmp_list[0], tmp_list[1]
                value = str(value).strip().strip('"')
                # if name == "PRETTY_NAME":
                #     version = value
                if name == "NAME":
                    version = value
                elif name == "VERSION":
                    version = "{} {}".format(version, value)
        # if not version:
        #     version = readFile('/etc/issue').strip().split("\n")[0].replace('\\n','').replace('\l','').strip()
    else:
        version = version.replace('release ', '').replace('Linux', '').replace('(Core)', '').strip()
    v_info = sys.version_info
    try:
        version = "{} {}(Py{}.{}.{})".format(version, os.uname().machine, v_info.major, v_info.minor, v_info.micro)
    except:
        version = "{} (Py{}.{}.{})".format(version, v_info.major, v_info.minor, v_info.micro)
    return xsssec(version)


# 获取总大小
def get_size_total(paths=[]):
    data = {}
    try:
        if type(paths) == str:
            paths = [paths]

        n_list = []
        for path in paths:
            if os.path.exists(path):
                n_list.append(path)
            else:
                data[path] = 0

        if len(n_list) > 0:
            shell = 'du -s {}'.format(' '.join(n_list).strip())
            res = ExecShell(shell)[0]
            for n in res.split("\n"):
                tmp = n.split("\t")
                if len(tmp) < 2: continue
                data[tmp[1]] = int(tmp[0]) * 1024
    except:
        pass
    return data


# 取文件或目录大小
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
                new_exc = e.replace(basename + "/", "")
                new_exc = os.path.join(path, new_exc)
                exclude.append(new_exc)

    # print(exclude)
    total_size = 0
    count = 0
    for root, dirs, files in os.walk(path, topdown=True):
        # filter path
        for exc in exclude:
            for d in dirs:
                sub_dir = os.path.normcase(root + os.path.sep + d)
                if fnmatch.fnmatch(sub_dir, exc) or d == exc:
                    # print("排除目录:"+sub_dir)
                    dirs.remove(d)
        count += 1
        for f in files:
            to_exclude = False
            count += 1
            filename = os.path.normcase(root + os.path.sep + f)
            if not os.path.exists(filename): continue
            if os.path.islink(filename): continue
            # filter file
            norm_filename = os.path.normcase(filename)
            for fexc in exclude:
                if fnmatch.fnmatch(norm_filename, fexc) or fexc == f:
                    to_exclude = True
                    # print("排除文件:"+norm_filename)
                    break
            if to_exclude:
                continue
            total_size += os.path.getsize(filename)
    return total_size


# 写关键请求日志
def write_request_log(reques=None):
    try:
        from BTPanel import request, g, session
        if session.get('debug') == 1: return
        log_path = '{}/logs/request'.format(get_panel_path())
        log_path2 = '/www/wwwlogs/request'
        log_file = getDate(format='%Y-%m-%d') + '.json'
        if not os.path.exists(log_path): os.makedirs(log_path)
        if not os.path.exists(log_path2): os.makedirs(log_path2)

        log_data = []
        log_data.append(getDate())
        log_data.append(GetClientIp() + ':' + str(get_remote_port()))
        log_data.append(request.method)
        log_data.append(request.full_path)
        log_data.append(request.headers.get('User-Agent'))
        if request.method == 'POST':
            args = request.form.to_dict()
            for k in args.keys():
                if k.find('pass') != -1 or k.find('user') != -1:
                    args[k] = '******'
                if len(args[k]) > 4096:
                    args[k] = args[k][0:1024] + " -- >4096"
            log_data.append(str(args))
        else:
            log_data.append('{}')
        log_data.append(int((time.time() - g.request_time) * 1000))
        log_data.append(g.response.status_code)
        log_data.append(g.response.content_length)
        log_data.append(g.response.headers.get('Content-Type'))
        log_data.append(request.headers.get('Host'))
        log_data.append(str(reques))
        log_msg = json.dumps(log_data) + "\n"
        WriteFile(log_path + '/' + log_file, log_msg, 'a+')
        WriteFile(log_path2 + '/' + log_file, log_msg, 'a+')
        rep_sys_path()
    except:
        pass


# 重载模块
def mod_reload(mode):
    if not mode: return False
    try:
        if sys.version_info[0] == 2:
            reload(mode)
        else:
            import imp
            imp.reload(mode)
        return True
    except:
        return False


# 设置权限
def set_mode(filename, mode):
    if not os.path.exists(filename): return False
    mode = int(str(mode), 8)
    try:
        os.chmod(filename, mode)
    except:
        return False
    return True


def create_linux_user(user, group):
    '''
        @name 创建系统用户
        @author hwliang<2022-01-15>
        @param user<string> 用户名
        @param group<string> 所属组
        @return bool
    '''
    ExecShell("groupadd {}".format(group))
    ExecShell('useradd -s /sbin/nologin -g {} {}'.format(user, group))
    return True


# 设置用户组
def set_own(filename, user, group=None):
    if not os.path.exists(filename): return False
    from pwd import getpwnam
    try:
        user_info = getpwnam(user)
        user = user_info.pw_uid
        if group:
            user_info = getpwnam(group)
        group = user_info.pw_gid
    except:
        if user == 'www':
            create_linux_user(user, user)
        # 如果指定用户或组不存在，则使用www
        try:
            user_info = getpwnam('www')
        except:
            create_linux_user(user, user)
            user_info = getpwnam('www')
        user = user_info.pw_uid
        group = user_info.pw_gid
    os.chown(filename, user, group)
    return True


# 校验路径安全
def path_safe_check(path, force=True):
    if len(path) > 256: return False
    checks = ['..', './', '\\', '%', '$', '^', '&', '*', '~', '"', "'", ';', '|', '{', '}', '`']
    for c in checks:
        if path.find(c) != -1: return False
    if force:
        rep = r"^[\w\s\.\/-]+$"
        if not re.match(rep, path): return False
    return True


# 取数据库字符集
def get_database_character(db_name):
    try:
        db_obj = get_mysql_obj(db_name)
        tmp = db_obj.query("show create database `%s`" % db_name.strip())
        c_type = str(re.findall(r"SET\s+([\w\d-]+)\s", tmp[0][1])[0])
        c_types = ['utf8', 'utf-8', 'gbk', 'big5', 'utf8mb4']
        if not c_type.lower() in c_types: return 'utf8'
        return c_type
    except:
        return 'utf8'


# 取mysql数据库对象
def get_mysql_obj(db_name):
    is_cloud_db = False
    if db_name:
        db_find = M('databases').where("name=?", db_name).find()
        if 'sid' in db_find:
            return get_mysql_obj_by_sid(db_find['sid'])
        is_cloud_db = db_find['db_type'] in ['1', 1]
    if is_cloud_db:
        import db_mysql
        db_obj = db_mysql.panelMysql()
        conn_config = json.loads(db_find['conn_config'])
        try:
            db_obj = db_obj.set_host(conn_config['db_host'], conn_config['db_port'], conn_config['db_name'], conn_config['db_user'], conn_config['db_password'])
        except Exception as e:
            raise PanelError(GetMySQLError(e))
    else:
        import panelMysql
        db_obj = panelMysql.panelMysql()
    return db_obj


# 取mysql数据库对像 By sid
def get_mysql_obj_by_sid(sid=0, conn_config=None):
    if sid in ['0', '', 0]: sid = 0
    import db_mysql
    db_obj = db_mysql.panelMysql()
    if sid:
        if not conn_config: conn_config = M('database_servers').where("id=?", sid).find()
        try:
            db_obj = db_obj.set_host(conn_config['db_host'], conn_config['db_port'], None, conn_config['db_user'], conn_config['db_password'])
        except Exception as e:
            raise PanelError(GetMySQLError(e))
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
        'utf8': 'utf8_general_ci',
        'utf8mb4': 'utf8mb4_general_ci',
        'gbk': 'gbk_chinese_ci',
        'big5': 'big5_chinese_ci'
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
                if len(x) < 2: continue
                if x[1] == None: continue
                data[x[0]] = int(x[1])
    except:
        return data
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
    except:
        return data
    return data


def get_database_size_by_id(id):
    """
    @获取数据库大小
    """
    data = 0
    try:
        name = M('databases').where('id=?', id).getField('name')
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
        # 匹配非ascii字符
        match = re.search(u"[\x80-\xff]+", dkey)
        if not match: match = re.search(u"[\u4e00-\u9fa5]+", dkey)
        if not match:
            newdomain += dkey + '.'
        else:
            if sys.version_info[0] == 2:
                newdomain += 'xn--' + dkey.decode('utf-8').encode('punycode') + '.'
            else:
                newdomain += 'xn--' + dkey.encode('punycode').decode('utf-8') + '.'
    if tmp[0] == '*': newdomain = "*." + newdomain
    return newdomain[0:-1]


# punycode 转中文
def de_punycode(domain):
    tmp = domain.split('.')
    newdomain = ''
    for dkey in tmp:
        if dkey.find('xn--') >= 0:
            newdomain += dkey.replace('xn--', '').encode('utf-8').decode('punycode') + '.'
        else:
            newdomain += dkey + '.'
    return newdomain[0:-1]


# 取计划任务文件路径
def get_cron_path():
    u_file = '/var/spool/cron/crontabs/root'
    if not os.path.exists(u_file):
        file = '/var/spool/cron/root'
    else:
        file = u_file
    return file


# 加密字符串
def en_crypt(key, strings):
    try:
        if type(strings) != bytes: strings = strings.encode('utf-8')
        from cryptography.fernet import Fernet
        f = Fernet(key)
        result = f.encrypt(strings)
        return result.decode('utf-8')
    except:
        # print(get_error_info())
        return strings


# 解密字符串
def de_crypt(key, strings):
    try:
        if type(strings) != bytes: strings = strings.decode('utf-8')
        from cryptography.fernet import Fernet
        f = Fernet(key)
        result = f.decrypt(strings).decode('utf-8')
        return result
    except:
        # print(get_error_info())
        return strings


# 获取IP限制列表
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
        if not iplist: return iplong_list
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

        cache.set(ikey, iplong_list, 3600)
    except:
        pass
    return iplong_list


def is_api_limit_ip(ip_list, client_ip):
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
        if limit_ip in ['*', 'all', '0.0.0.0', '0.0.0.0/0', '0.0.0.0/24', '0.0.0.0/32']: return True
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


# 检查IP白名单
def check_ip_panel():
    iplong_list = get_limit_ip()
    if not iplong_list: return False
    client_ip = GetClientIp()
    if client_ip in ['127.0.0.1', 'localhost', '::1']: return False
    client_ip_long = ip2long(client_ip)
    for limit_ip in iplong_list:
        if client_ip_long >= limit_ip['min'] and client_ip_long <= limit_ip['max']:
            return False

    # errorStr = ReadFile('./BTPanel/templates/' + GetConfigValue('template') + '/error2.html')
    # try:
    #     errorStr = errorStr.format(getMsg('PAGE_ERR_TITLE'),getMsg('PAGE_ERR_IP_H1'),getMsg('PAGE_ERR_IP_P1',(GetClientIp(),)),getMsg('PAGE_ERR_IP_P2'),getMsg('PAGE_ERR_IP_P3'),getMsg('NAME'),getMsg('PAGE_ERR_HELP'))
    # except IndexError:pass
    # return error_not_login(errorStr,True)
    return error_403(None)


# 检查面板域名
def check_domain_panel():
    tmp = GetHost()
    domain = ReadFile('data/domain.conf')
    if domain:
        client_ip = GetClientIp()
        if client_ip in ['127.0.0.1', 'localhost', '::1']: return False
        if tmp.strip().lower() != domain.strip().lower():
            if check_client_info():
                try:
                    from flask import render_template
                    return render_template('error2.html')
                except:
                    pass

            return error_403(None)
    return False


def check_ua_panel():
    import json
    ua_file = 'data/limitua.conf'
    if not os.path.exists(ua_file): return False
    with open(ua_file, 'r') as f:
        data = json.load(f)  # 读取JSON文件
    if data.get('status', '1') == '0':  # 如果status为"0"，就返回False
        return False
    ua_list = [ua['name'] for ua in data.get('ua_list', [])]  # 获取ua_list字段的值
    if not ua_list: return False
    from flask import request
    client_ua = request.user_agent.string
    if client_ua not in ua_list:
        return error_403(None)
    return False


# 是否离线模式
def is_local():
    s_file = '{}/data/not_network.pl'.format(get_panel_path())
    return os.path.exists(s_file)


def auto_backup_defalt_db():
    """
    @name 自动备份默认数据库，除logs表外
    @return:
    """
    b_path = '{}/default_sql'.format(get_backup_path())
    day_date = format_date('%Y-%m-%d')
    backup_path = b_path + '/' + day_date
    output_file = backup_path + '/default_db.sql'

    if os.path.exists(backup_path) or os.path.exists(output_file): return True

    os.makedirs(backup_path, 384)
    with open(output_file, 'w') as f:
        import sqlite3
        conn = sqlite3.connect('{}/data/default.db'.format(get_panel_path()))
        for line in conn.iterdump():
            if 'INSERT INTO "logs"' not in line:
                f.write('%s\n' % line)
        conn.close()

    # 自动清理180天前的备份
    import shutil
    time_now = time.time() - (86400 * 180)
    for f in os.listdir(b_path):

        if time.mktime(time.strptime(f, "%Y-%m-%d")) < time_now:
            path = b_path + '/' + f
            if os.path.exists(path):
                shutil.rmtree(path)
    return True


def recover_default_db(date):
    """
    @name 根据日期恢复默认数据库，支持%Y-%m-%d/%Y%m%d格式
    @param date:
    @return:
    """
    b_path = '{}/default_sql'.format(get_backup_path())
    if date == "default":
        move_old_default_db()
        create_default_db()
        return True
    else:
        backup_path = b_path + '/' + date
        output_file = backup_path + '/default_db.sql'

    if not os.path.exists(output_file):
        print("{} 不存在".format(output_file))
        return False

    move_old_default_db()

    import sqlite3
    conn = sqlite3.connect('{}/data/default.db'.format(get_panel_path()))
    with open(output_file, 'r') as f:
        queries = f.read()
        conn.executescript(queries)
    conn.commit()
    conn.close()
    return True


def move_old_default_db():
    """
    @name 转移旧数据库
    @return:
    """
    import shutil
    if os.path.exists('{}/data/default.db'.format(get_panel_path())):
        shutil.move('{}/data/default.db'.format(get_panel_path()),
                    '{}/data/default.db.{}'.format(get_panel_path(), time.strftime("%Y%m%d%H%M%S", time.localtime())))
        print("原数据库已备份为default.db.{}".format(time.strftime("%Y%m%d%H%M%S", time.localtime())))


def create_default_db():
    """
    创建默认的default.db数据库
    @return:
    """
    exec_sql = """
PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;
CREATE TABLE `backup` (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `type` INTEGER,
  `name` TEXT,
  `pid` INTEGER,
  `filename` TEXT,
  `size` INTEGER,
  `addtime` TEXT
);
CREATE TABLE `binding` (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `pid` INTEGER,
  `domain` TEXT,
  `path` TEXT,
  `port` INTEGER,
  `addtime` TEXT
);
CREATE TABLE `config` (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `webserver` TEXT,
  `backup_path` TEXT,
  `sites_path` TEXT,
  `status` INTEGER,
  `mysql_root` TEXT
);
INSERT INTO config VALUES(1,'nginx','/www/backup','/www/wwwroot',0,'admin');
CREATE TABLE `crontab` (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `name` TEXT,
  `type` TEXT,
  `where1` TEXT,
  `where_hour` INTEGER,
  `where_minute` INTEGER,
  `echo` TEXT,
  `addtime` TEXT
);
CREATE TABLE `databases` (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `pid` INTEGER,
  `name` TEXT,
  `username` TEXT,
  `password` TEXT,
  `accept` TEXT,
  `ps` TEXT,
  `addtime` TEXT
);
CREATE TABLE `firewall` (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `port` TEXT,
  `ps` TEXT,
  `addtime` TEXT
);
INSERT INTO firewall VALUES(2,'80','网站默认端口','0000-00-00 00:00:00');
INSERT INTO firewall VALUES(3,'8888','WEB面板','0000-00-00 00:00:00');
INSERT INTO firewall VALUES(4,'21','FTP服务','0000-00-00 00:00:00');
INSERT INTO firewall VALUES(5,'22','SSH远程管理服务','0000-00-00 00:00:00');
CREATE TABLE `ftps` (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `pid` INTEGER,
  `name` TEXT,
  `password` TEXT,
  `path` TEXT,
  `status` TEXT,
  `ps` TEXT,
  `addtime` TEXT
);
CREATE TABLE `logs` (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `type` TEXT,
  `log` TEXT,
  `addtime` TEXT
);
CREATE TABLE `sites` (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `name` TEXT,
  `path` TEXT,
  `status` TEXT,
  `index` TEXT,
  `ps` TEXT,
  `addtime` TEXT
);
CREATE TABLE `domain` (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `pid` INTEGER,
  `name` TEXT,
  `port` INTEGER,
  `addtime` TEXT
);
CREATE TABLE `users` (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `username` TEXT,
  `password` TEXT,
  `login_ip` TEXT,
  `login_time` TEXT,
  `phone` TEXT,
  `email` TEXT
);
INSERT INTO users VALUES(1,'admin','21232f297a57a5a743894a0e4a801fc3','192.168.0.10','2016-12-10 15:12:56','0','aaa@qq.com');
CREATE TABLE `tasks` (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `name` 			TEXT,
  `type`			TEXT,
  `status` 		TEXT,
  `addtime` 	TEXT,
  `start` 	  INTEGER,
  `end` 	    INTEGER,
  `execstr` 	TEXT
);
DELETE FROM sqlite_sequence;
INSERT INTO sqlite_sequence VALUES('config',1);
INSERT INTO sqlite_sequence VALUES('firewall',5);
INSERT INTO sqlite_sequence VALUES('users',1);
COMMIT;"""
    import sqlite3
    conn = sqlite3.connect('{}/data/default.db'.format(get_panel_path()))
    conn.executescript(exec_sql)
    conn.commit()
    conn.close()


def get_default_db_backup_dates(count=10, l_all=False):
    """
    @name 获取默认数据库备份目录的所有备份日期，并返回一个list
    @return:
    """
    b_path = '{}/default_sql'.format(get_backup_path())
    dates = []
    for f in os.listdir(b_path):
        if os.path.isdir(b_path + '/' + f):
            dates.append(f)

    dates.sort(reverse=True)
    if l_all is False: return dates[0:count]
    return dates


# 自动备份面板数据1
def auto_backup_panel():
    time.sleep(120)
    try:
        panel_paeh = get_panel_path()
        paths = panel_paeh + '/data/not_auto_backup.pl'
        if os.path.exists(paths): return False

        b_path = '{}/panel'.format(get_backup_path())
        day_date = format_date('%Y-%m-%d')
        backup_path = b_path + '/' + day_date
        backup_db_path = b_path + '/db'
        os.makedirs(backup_db_path, 384, exist_ok=True)
        backup_file = backup_path + '.zip'

        if os.path.exists(backup_path) or os.path.exists(backup_file): return True

        # 清除gzip缓存
        compress_caches_path = " {}/data/compress_caches".format(panel_paeh)
        if os.path.exists(compress_caches_path):
            ExecShell("rm -rf {}/*".format(compress_caches_path))

        ignore_default = ''
        ignore_system = ''
        ignore_hids= panel_paeh + '/data/hids_data'
        max_size = 100 * 1024 * 1024
        if os.path.getsize('{}/data/default.db'.format(panel_paeh)) > max_size:
            ignore_default = 'default.db'
        if os.path.getsize('{}/data/system.db'.format(panel_paeh)) > max_size:
            ignore_system = 'system.db'

        os.makedirs(backup_path, 384, exist_ok=True)
        import shutil
        shutil.copytree(panel_paeh + '/data', backup_path + '/data',
                        ignore=shutil.ignore_patterns(ignore_system, ignore_default,ignore_hids))
        shutil.copytree(panel_paeh + '/config', backup_path + '/config')
        shutil.copytree(panel_paeh + '/vhost', backup_path + '/vhost')

        # 2024/3/14 下午 4:53 永远保存最新的数据库到/www/backup/panel/db
        import sqlite3
        source_dir = panel_paeh + '/data/db'
        os.makedirs(backup_path + '/data/db', 384, exist_ok=True)
        for filename in os.listdir(source_dir):
            source_file = os.path.join(source_dir, filename)

            if os.path.isfile(source_file) and filename.endswith('.db'):
                try:
                    conn = sqlite3.connect(source_file)
                    cursor = conn.cursor()
                    cursor.execute("SELECT * FROM sqlite_master")
                    if "site" in filename:
                        cursor.execute("SELECT * FROM sites")
                        cursor.execute("SELECT * FROM domain")
                    elif "database" in filename:
                        cursor.execute("SELECT * FROM databases")
                    elif "crontab" in filename:
                        cursor.execute("SELECT * FROM crontab")
                    elif "ftp" in filename:
                        cursor.execute("SELECT * FROM ftps")
                    rows = cursor.fetchall()
                    conn.close()

                    shutil.copy(source_file, backup_db_path)
                except Exception as e:
                    if os.path.exists("/www/server/panel/data/debug.pl"):
                        print("Database File: {}/{}".format(source_dir, filename))
                    continue

        ExecShell("cd {} && zip {} -r {}/".format(b_path, backup_file, day_date))
        ExecShell("chmod -R 600 {path};chown -R root.root {path}".format(path=backup_file))
        if os.path.exists(backup_path): shutil.rmtree(backup_path)
        time_now = time.time() - (86400 * 15)
        _date_compile = re.compile(r"(\d{4}-\d{2}-\d{2})")
        for f in os.listdir(b_path):
            _date = _date_compile.match(f)
            if not _date: continue
            if time.mktime(time.strptime(_date.group(), "%Y-%m-%d")) < time_now:
                b_file = os.path.join(b_path, f)
                if os.path.exists(b_file):
                    ExecShell("rm -rf {}".format(b_file))
        set_php_cli_env()
    except:
        if os.path.exists("/www/server/panel/data/debug.pl"):
            import traceback
            print(traceback.format_exc())


def set_php_cli_env():
    '''
        @name 重新设置php-cli.ini配置
    '''
    import jobs
    jobs.set_php_cli_env()


# 检查端口状态
def check_port_stat(port, localIP='127.0.0.1'):
    import socket
    temp = {}
    temp['port'] = port
    temp['local'] = True
    try:
        s = socket.socket()
        s.settimeout(0.15)
        s.connect((localIP, port))
        s.close()
    except:
        temp['local'] = False

    result = 0
    if temp['local']: result += 2
    return result


# 同步时间
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
        writeFile(tip_file, str(s_time))
        return True
    except:
        if os.path.exists(tip_file): os.remove(tip_file)
        return False


# 重载模块
def reload_mod(mod_name=None):
    # 是否重载指定模块
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
                    modules.append([mod_name, True])
                except:
                    modules.append([mod_name, False])
            else:
                modules.append([mod_name, False])
        return modules

    # 重载所有模块
    for mod_name in sys.modules.keys():
        if mod_name in ['BTPanel']: continue
        f = getattr(sys.modules[mod_name], '__file__', None)
        if f:
            try:
                if f.find('panel/') == -1: continue
                if sys.version_info[0] == 2:
                    reload(sys.modules[mod_name])
                else:
                    importlib.reload(sys.modules[mod_name])
                modules.append([mod_name, True])
            except:
                modules.append([mod_name, False])
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


# 直接请求到PHP-FPM
# version php版本
# uri 请求uri
# filename 要执行的php文件
# args 请求参数
# method 请求方式
def request_php(version, uri, document_root, method='GET', pdata=b''):
    import panelPHP
    if type(pdata) == dict: pdata = url_encode(pdata)
    fpm_address = get_fpm_address(version)
    p = panelPHP.FPM(fpm_address, document_root)
    result = p.load_url_public(uri, pdata, method)
    return result


def get_fpm_address(php_version, bind=False):
    '''
        @name 获取FPM请求地址
        @author hwliang<2020-10-23>
        @param php_version string PHP版本
        @return tuple or string
    '''
    fpm_address = '/tmp/php-cgi-{}.sock'.format(php_version)
    php_fpm_file = '{}/php/{}/etc/php-fpm.conf'.format(get_setup_path(), php_version)
    try:
        fpm_conf = readFile(php_fpm_file)
        tmp = re.findall(r"listen\s*=\s*(.+)", fpm_conf)
        if not tmp: return fpm_address
        if tmp[0].find('sock') != -1: return fpm_address
        if tmp[0].find(':') != -1:
            listen_tmp = tmp[0].split(':')
            if bind:
                fpm_address = (listen_tmp[0], int(listen_tmp[1]))
            else:
                fpm_address = ('127.0.0.1', int(listen_tmp[1]))
        else:
            fpm_address = ('127.0.0.1', int(tmp[0]))
        return fpm_address
    except:
        return fpm_address


def get_php_proxy(php_version, webserver='nginx'):
    '''
        @name 获取PHP代理地址
        @author hwliang<2020-10-24>
        @param php_version string php版本  (52|53|54|55|56|70|71|72|73|74)
        @param webserver string web服务器类型 (nginx|apache|ols)
        return string
    '''
    php_address = get_fpm_address(php_version)
    if isinstance(php_address, str):
        if webserver == 'nginx':
            return 'unix:{}'.format(php_address)
        elif webserver == 'apache':
            return 'unix:{}|fcgi://localhost'.format(php_address)
    else:
        if webserver == 'nginx':
            return '{}:{}'.format(php_address[0], php_address[1])
        elif webserver == 'apache':
            return 'fcgi://{}:{}'.format(php_address[0], php_address[1])


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
        tmp = re.findall(rep, conf)
        if not tmp:
            rep = r"enable-php-(\w{2,5})-wpfastcgi\.conf"
            tmp = re.findall(rep, conf)
        if not tmp: return '00'
    elif conf.find('/usr/local/lsws/lsphp') != -1:
        rep = r"path\s*/usr/local/lsws/lsphp(\d+)/bin/lsphp"
        tmp = re.findall(rep, conf)
        if not tmp: return '00'
    else:
        rep = r"php-cgi-([0-9]{2,3})\.sock"
        tmp = re.findall(rep, conf)
        if not tmp:
            rep = r'\d+\.\d+\.\d+\.\d+:10(\d{2,2})1'
            tmp = re.findall(rep, conf)
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
    conf = readFile(vhost_path + '/' + web_server + '/' + siteName + '.conf')
    if web_server == 'openlitespeed':
        conf = readFile(vhost_path + '/' + web_server + '/detail/' + siteName + '.conf')
    return get_php_version_conf(conf)


def check_tcp(ip, port):
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
        s.connect((ip.strip(), int(port)))
        s.close()
    except:
        return False
    return True


def sub_php_address(conf_file, rep, tsub, php_version):
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
    # if conf.find('#PHP') == -1 and conf.find('pathinfo.conf') == -1: return False
    if conf_file.split('-')[-1].find(php_version + ".") != 0:
        phpv = get_php_version_conf(conf)
        if phpv != php_version: return False

    tmp = re.search(rep, conf)
    if not tmp: return False
    if tmp.group() == tsub: return False
    conf = conf.replace(tmp.group(), tsub)  # re.sub(rep,php_proxy,conf)
    writeFile(conf_file, conf)
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
    if not os.path.exists('{}/php/{}/bin/php'.format(get_setup_path(), php_version)):  # 指定PHP版本是否安装
        return False
    ngx_rep = r"(unix:/tmp/php-cgi.*\.sock|\d+\.\d+\.\d+\.\d+:\d+)"
    apa_rep = r"(unix:/tmp/php-cgi.*\.sock\|fcgi://localhost|fcgi://\d+\.\d+\.\d+\.\d+:\d+)"
    ngx_proxy = get_php_proxy(php_version, 'nginx')
    apa_proxy = get_php_proxy(php_version, 'apache')
    is_write = False

    # nginx的PHP配置文件
    nginx_conf_path = '{}/nginx/conf'.format(get_setup_path())

    if os.path.exists(nginx_conf_path):
        for f_name in os.listdir(nginx_conf_path):
            if f_name.find('enable-php') != -1:
                conf_file = '/'.join((nginx_conf_path, f_name))
                if sub_php_address(conf_file, ngx_rep, ngx_proxy, php_version):
                    is_write = True
    # nginx的phpmyadmin
    # conf_file = '/www/server/nginx/conf/nginx.conf'
    # if os.path.exists(conf_file):
    #     if sub_php_address(conf_file,ngx_rep,ngx_proxy,php_version):
    #         is_write = True

    # apache的网站配置文件
    apache_conf_path = '{}/apache'.format(get_vhost_path())
    if os.path.exists(apache_conf_path):
        for f_name in os.listdir(apache_conf_path):
            conf_file = '/'.join((apache_conf_path, f_name))
            if sub_php_address(conf_file, apa_rep, apa_proxy, php_version):
                is_write = True
    # apache的phpmyadmin
    conf_file = '{}/apache/conf/extra/httpd-vhosts.conf'.format(get_setup_path())
    if os.path.exists(conf_file):
        if sub_php_address(conf_file, apa_rep, apa_proxy, php_version):
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
            result = unicode(data, errors='ignore')
        else:
            result = data.encode('utf8', errors='ignore')
        return result
    except:
        return data


def unicode_decode(data, charset='utf8'):
    try:
        if sys.version_info[0] == 2:
            result = unicode(data, errors='ignore')
        else:
            result = data.decode('utf8', errors='ignore')
        return result
    except:
        return data


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
        cache.set('cdn_url', cdn_url, 3)
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
    bin_file = '{}/pyenv/bin/python3'.format(get_panel_path())
    if os.path.exists(bin_file):
        return bin_file
    return '/usr/bin/python'


def aes_encrypt(data, key):
    import panelAes
    if sys.version_info[0] == 2:
        aes_obj = panelAes.aescrypt_py2(key)
        return aes_obj.aesencrypt(data)
    else:
        aes_obj = panelAes.aescrypt_py3(key)
        return aes_obj.aesencrypt(data)


def aes_decrypt(data, key):
    import panelAes
    if sys.version_info[0] == 2:
        aes_obj = panelAes.aescrypt_py2(key)
        return aes_obj.aesdecrypt(data)
    else:
        aes_obj = panelAes.aescrypt_py3(key)
        return aes_obj.aesdecrypt(data)


# 清理大日志文件
def clean_max_log(log_file, max_size=100, old_line=100):
    if not os.path.exists(log_file): return False
    max_size = 1024 * 1024 * max_size
    if os.path.getsize(log_file) > max_size:
        try:
            old_body = GetNumLines(log_file, old_line)
            writeFile(log_file, old_body)
        except:
            print(get_error_info())


# 获取证书哈希
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
    i2 = int((ips - i1 * (2 ** 24)) / (2 ** 16))
    i3 = int(((ips - i1 * (2 ** 24)) - i2 * (2 ** 16)) / (2 ** 8))
    i4 = int(((ips - i1 * (2 ** 24)) - i2 * (2 ** 16)) - i3 * (2 ** 8))
    return "{}.{}.{}.{}".format(i1, i2, i3, i4)


def ip2long(ip):
    '''
        @name 将IP地址转换为整数
        @author hwliang<2020-06-11>
        @param ip string(ipv4)
        @return long
    '''
    ips = ip.split('.')
    if len(ips) != 4: return 0
    iplong = 2 ** 24 * int(ips[0]) + 2 ** 16 * int(ips[1]) + 2 ** 8 * int(ips[2]) + int(ips[3])
    return iplong


def is_local_ip(ip):
    '''
        @name 判断是否为本地(内网)IP地址
        @author hwliang<2021-03-26>
        @param ip string(ipv4)
        @return bool
    '''
    patt = r"^(192\.168|127|10|172\.(16|17|18|19|20|21|22|23|24|25|26|27|28|29|30|31))\."
    if re.match(patt, ip): return True
    return False


# 提交关键词
def submit_keyword(keyword):
    pdata = {"keyword": keyword}
    httpPost(GetConfigValue('home') + '/api/panel/total_keyword', pdata)


# 统计关键词
def total_keyword(keyword):
    import threading
    p = threading.Thread(target=submit_keyword, args=(keyword,))
    # p.setDaemon(True)
    p.start()


# 获取debug日志
def get_debug_log():
    from BTPanel import request
    return GetClientIp() + ':' + str(get_remote_port()) + '|' + str(int(time.time())) + '|' + get_error_info()


# 获取sessionid
def get_session_id():
    from BTPanel import request, app
    session_id = request.cookies.get(app.config['SESSION_COOKIE_NAME'], '')
    if not re.findall(r"^(([\w\.-]{64})|([\w\.-]{71}))$", session_id):
        return GetRandomString(64)
    return session_id


# 尝试自动恢复面板数据库
def rep_default_db():
    db_path = '{}/data/'.format(get_panel_path())
    db_file = db_path + 'default.db'
    db_tmp_backup = db_path + 'default_' + format_date("%Y%m%d_%H%M%S") + ".db"

    panel_backup = '{}/panel'.format(get_backup_path())
    bak_list = os.listdir(panel_backup)
    if not bak_list: return False
    bak_list = sorted(bak_list, reverse=True)
    db_bak_file = ''
    for d_name in bak_list:
        db_bak_file = panel_backup + '/' + d_name + '/data/default.db'
        if not os.path.exists(db_bak_file): continue
        if os.path.getsize(db_bak_file) < 17408: continue
        break

    if not db_bak_file: return False
    ExecShell("\cp -arf {} {}".format(db_file, db_tmp_backup))
    ExecShell("\cp -arf {} {}".format(db_bak_file, db_file))
    return True


def chdck_salt():
    '''
        @name 检查所有用户密码是否加盐，若没有则自动加上
        @author hwliang<2020-07-08>
        @return void
    '''

    if not M('sqlite_master').where('type=? AND name=? AND sql LIKE ?', ('table', 'users', '%salt%')).count():
        M('users').execute("ALTER TABLE 'users' ADD 'salt' TEXT", ())
    u_list = M('users').where('salt is NULL', ()).field('id,username,password,salt').select()
    if isinstance(u_list, str):
        if u_list.find('no such table: users') != -1:
            rep_default_db()
            if not M('sqlite_master').where('type=? AND name=? AND sql LIKE ?', ('table', 'users', '%salt%')).count():
                M('users').execute("ALTER TABLE 'users' ADD 'salt' TEXT", ())
            u_list = M('users').where('salt is NULL', ()).field('id,username,password,salt').select()

    for u_info in u_list:
        salt = GetRandomString(12)  # 12位随机
        pdata = {}
        pdata['password'] = md5(md5(u_info['password'] + '_bt.cn') + salt)
        pdata['salt'] = salt
        M('users').where('id=?', (u_info['id'],)).update(pdata)


def get_login_token():
    token_s = readFile('{}/data/login_token.pl'.format(get_panel_path()))
    if not token_s: return GetRandomString(32)
    return token_s


def get_sess_key():
    return md5(get_login_token() + get_csrf_sess_html_token_value())


def password_salt(password, username=None, uid=None):
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
        uid = M('users').where('username=?', (username,)).getField('id')
    salt = M('users').where('id=?', (uid,)).getField('salt')
    return md5(md5(password + '_bt.cn') + salt)


def package_path_append(path):
    if not path in sys.path:
        sys.path.insert(0, path)


def rep_sys_path():
    sys_path = []
    for p in sys.path:
        if p in sys_path: continue
        sys_path.append(p)
    sys.path = sys_path


def set_error_num(key, empty=False, expire=3600):
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
    cache.set(key, num + 1, expire)
    return True


def get_error_num(key, limit=False):
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
    if not os.path.exists('config/show_menu.json'):
        import config
        con = config.config()
        con.get_menu_list(None)
    hide_menu = ReadFile('config/show_menu.json')
    debug = session.get('debug')
    if hide_menu:
        try:
            hide_menu = json.loads(hide_menu)
        except:
            ExecShell('rm -f config/show_menu.json')
            hide_menu = ['memuA', 'memuAsite', 'memuAftp', 'memuAdatabase', 'memuDocker', 'memuAcontrol', 'memuAfirewall', 'memuAfiles', 'memuAlogs', 'memuAxterm', 'memuAcrontab', 'memuAsoft',
                         'memuAconfig', 'dologin', 'memu_btwaf', 'memuAssl']
            writeFile('config/show_menu.json', json.dumps(hide_menu))
        show_menu = []
        for i in range(len(data)):
            if data[i]['id'] not in hide_menu: continue
            if data[i]['id'] == "memuAxterm":
                if debug: continue
            # if data[i]['id'] == "memu_btwaf":
            #     if not os.path.exists('plugin/btwaf/btwaf_main.py'): continue
            show_menu.append(data[i])

        data = show_menu
        del (hide_menu)
        del (show_menu)
    menus = sorted(data, key=lambda x: x['sort'])
    return menus


# 取CURL路径
def get_curl_bin():
    '''
        @name 取CURL执行路径
        @author hwliang<2020-09-01>
        @return string
    '''
    c_bin = ['/usr/local/curl2/bin/curl', '/usr/local/curl/bin/curl', '/usr/bin/curl']
    for cb in c_bin:
        if os.path.exists(cb): return cb
    return 'curl'


# 设置防跨站配置
def set_open_basedir():
    try:
        fastcgi_file = '{}/nginx/conf/fastcgi.conf'.format(get_setup_path())

        if os.path.exists(fastcgi_file):
            fastcgi_body = readFile(fastcgi_file)
            if fastcgi_body.find('bt_safe_dir') == -1:
                fastcgi_body = fastcgi_body + "\n" + 'fastcgi_param  PHP_ADMIN_VALUE    "$bt_safe_dir=$bt_safe_open";'
                writeFile(fastcgi_file, fastcgi_body)

        proxy_file = '{}/nginx/conf/proxy.conf'.format(get_setup_path())
        if os.path.exists(proxy_file):
            proxy_body = readFile(proxy_file)
            if proxy_body.find('bt_safe_dir') == -1:
                proxy_body = proxy_body + "\n" + '''map "baota_dir" $bt_safe_dir {
    default "baota_dir";
}
map "baota_open" $bt_safe_open {
    default "baota_open";
} '''
                writeFile(proxy_file, proxy_body)

        open_basedir_path = '{}/open_basedir/nginx'.format(get_vhost_path())
        if not os.path.exists(open_basedir_path):
            os.makedirs(open_basedir_path, 384)

        site_list = M('sites').field('id,name,path').select()
        for site_info in site_list:
            set_site_open_basedir_nginx(site_info['name'])
    except:
        return


# 处理指定站点的防跨站配置 for Nginx
def set_site_open_basedir_nginx(siteName):
    try:
        return
        open_basedir_path = '/www/server/panel/vhost/open_basedir/nginx'
        if not os.path.exists(open_basedir_path):
            os.makedirs(open_basedir_path, 384)
        config_file = '/www/server/panel/vhost/nginx/{}.conf'.format(siteName)
        open_basedir_file = "/".join(
            (open_basedir_path, '{}.conf'.format(siteName))
        )
        if not os.path.exists(config_file): return
        if not os.path.exists(open_basedir_file):
            writeFile(open_basedir_file, '')
        config_body = readFile(config_file)
        if config_body.find(open_basedir_path) == -1:
            config_body = config_body.replace("include enable-php", "include {};\n\t\tinclude enable-php".format(open_basedir_file))
            writeFile(config_file, config_body)

        root_path = re.findall(r"root\s+(.+);", config_body)[0]
        if not root_path: return
        userini_file = root_path + '/.user.ini'
        if not os.path.exists(userini_file):
            writeFile(open_basedir_file, '')
            return
        userini_body = readFile(userini_file)
        if not userini_body: return
        if userini_body.find('open_basedir') == -1:
            writeFile(open_basedir_file, '')
            return

        open_basedir_conf = re.findall("open_basedir=(.+)", userini_body)
        if not open_basedir_conf: return
        open_basedir_conf = open_basedir_conf[0]
        open_basedir_body = '''set $bt_safe_dir "open_basedir";
set $bt_safe_open "{}";'''.format(open_basedir_conf)
        writeFile(open_basedir_file, open_basedir_body)
    except:
        return


def run_thread(fun, args=(), daemon=False):
    '''
        @name 使用线程执行指定方法
        @author hwliang<2020-10-27>
        @param fun {def} 函数对像
        @param args {tuple} 参数元组
        @param daemon {bool} 是否守护线程
        @return bool
    '''
    import threading
    p = threading.Thread(target=fun, args=args)
    p.setDaemon(daemon)
    p.start()
    return True


def check_domain_cloud(domain):
    run_thread(cloud_check_domain, (domain,))


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
            os.makedirs(check_domain_path, 384)
        pdata = get_user_info()
        pdata['domain'] = domain
        result = httpPost('https://www.bt.cn/api/panel/check_domain', pdata)
        cd_file = check_domain_path + domain + '.pl'
        writeFile(cd_file, result)
    except:
        pass


def get_mac_address():
    import uuid
    mac = uuid.UUID(int=uuid.getnode()).hex[-12:]
    return ":".join([mac[e:e + 2] for e in range(0, 11, 2)])

def get_user_info():
    user_file = '{}/data/userInfo.json'.format(get_panel_path())
    # if not os.path.exists(user_file): 
    #     return {}
    

    userInfo = {}
    userInfo['oem'] = get_oem_name()
    userInfo['o'] = userInfo['oem']
    userInfo['mac'] = get_mac_address()

    try:
        userTmp = json.loads(readFile(user_file))
        if not 'serverid' in userTmp or len(userTmp['serverid']) != 64:
            import panelAuth
            userTmp = panelAuth.panelAuth().create_serverid(None)
        userInfo['uid'] = userTmp['uid']
        userInfo['address'] = userTmp['address']
        userInfo['access_key'] = userTmp['access_key']
        userInfo['username'] = userTmp['username']
        userInfo['serverid'] = userTmp['serverid']
    except:
        import panelAuth
        userInfo['uid'] = -1
        userInfo['address'] = get_local_ip()
        userInfo['access_key'] = "F"*48
        userInfo['username'] = 'None'
        userInfo['serverid'] = panelAuth.panelAuth().get_serverid()
        pass    
    return userInfo


def is_bind():
    # if not os.path.exists('{}/data/bind.pl'.format(get_panel_path())): return True
    # return not not get_user_info()
    if not os.path.exists('data/initBind.pl'):
        writeFile('data/initBind.pl', 'True')
        return False
    else:
        return True


def send_file(data, fname='', mimetype=''):
    '''
        @name 以文件流的形式返回
        @author heliang<2020-10-27>
        @param data {bytes|string} 文件数据或路径
        @param mimetype {string} 文件类型
        @param fname {string} 文件名
        @return Response
    '''
    d_type = type(data)
    from io import BytesIO, StringIO
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

    import flask
    if flask.__version__ < "2.1.0":
        return send_to(fp,
                       mimetype=mimetype,
                       as_attachment=True,
                       add_etags=True,
                       conditional=True,
                       attachment_filename=fname,
                       cache_timeout=0)
    else:
        return send_to(fp,
                       mimetype=mimetype,
                       as_attachment=True,
                       etag=True,
                       conditional=True,
                       download_name=fname,
                       max_age=0)


def gen_password(length=8, chars=string.ascii_letters + string.digits):
    from random import choice
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
        cs = {"&quot": '"', "&#x27": "'"}
        for c in cs.keys():
            text = text.replace(c, cs[c])

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
                       '.ln.cn', '.mo.cn', '.net.cn', '.nm.cn', '.nx.cn', '.org.cn', '.cn.com']
    old_domain_name = domain_name
    top_domain = "." + ".".join(domain_name.rsplit('.')[-2:])
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


def query_dns(domain, dns_type='A', is_root=False):
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
    except:
        os.system('{} -m pip install dnspython'.format(get_python_bin()))
        import dns.resolver

    if is_root: domain, zone = get_root_domain(domain)
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
    except:
        return False


# 取通用对象
re_key_match = re.compile(r'^[\w\s\[\]\-\.]+$')
re_key_match2 = re.compile(r'^\.?__[\w\s[\]\-]+__\.?$')
key_filter_list = ['get', 'set', 'get_items', 'exists', '__contains__', '__setitem__', '__getitem__', '__delitem__', '__delattr__', '__setattr__', '__getattr__', '__class__']


class dict_obj:
    def __contains__(self, key):
        return hasattr(self, key)

    def __setitem__(self, key, value):
        if key in key_filter_list:
            return
        if not re_key_match.match(key) or re_key_match2.match(key):
            return
        setattr(self, key, value)

    def __getitem__(self, key):
        return getattr(self, key, None)

    def __delitem__(self, key):
        delattr(self, key)

    def __delattr__(self, key):
        delattr(self, key)

    def get_items(self):
        return self

    def exists(self, keys):
        return exists_args(keys, self)

    def set(self, key, value):
        if not isinstance(value, str) or not isinstance(key, str): return False
        if key in key_filter_list:
            return
        if not re_key_match.match(key) or re_key_match2.match(key):
            return
        return setattr(self, key, value)

    def get(self, key, default='', format='', limit=[]):
        '''
            @name 获取指定参数
            @param key<string> 参数名称，允许在/后面限制参数格式，请参考参数值格式(format)
            @param default<string> 默认值，默认空字符串
            @param format<string>  参数值格式(int|str|port|float|json|xss|path|url|ip|ipv4|ipv6|letter|mail|phone|正则表达式|>1|<1|=1)，默认为空
            @param limit<list> 限制参数值内容
            @param return mixed

            @name 获取指定参数
            @param key<string> 参数名称，允许在/后面限制参数格式，请参考参数值格式(format)
            @param default<string> 默认值，默认空字符串
            @param format<string>  参数值格式，默认为空
                    int or d: 强制转换为整数
                    str or s：转换为字符串
                    port: 检查端口合法性
                    float or f: 转换为float
                    json or j: 解析json
                    xss or x: 过滤XSS
                    path or p: 检查目录路径安全性
                    url or u: 检查URL是否合法
                    ip|ipv4|ipv6/i:判断IP地址是否合法
                    letter or w: 判断是否为字母或数值组成(^\w+$)
                    mail or m: 判断是否为合法Email地址
                    phone: 判断是否为合法国内手机号码
                    直接输入正则表达式：正则表达式
                    >x: 判断指定参数值长度是否>x，如：>2 ，如果失败，则抛出异常
                    <x: 判断指定参数值长度是否<x，如：<2 ，如果失败，则抛出异常
                    =x: 判断指定参数值长度是否=x，如：=2 ，如果失败，则抛出异常
            @param limit<list> 限制参数值内容
            @param return mixed

            @示例：
            class test_main:
                def test(self,args):
                    # 获取id参数并转换为整数，如果不存在，则使用默认值：0
                    id = args.get('id/d',0) # 方法1
                    id = args.get('id',0,'int') # 方法2
                    # 获取name参数并进行xss过滤，如果不存在，则使用默认值：""
                    name = args.get('name/x','') # 方法1
                    name = args.get('name','','xss') # 方法2

                    # 限制指定参数值范围
                    sex = args.get('sex/s','男',limit=['男','女'])

                    # 使用正则表达式，如果不符合，则抛出异常
                    re_test = args.get('re_test','','^[\w\s]+$')

                    # 获取并解析参数值中的json字符串，如果参数不存在，则使用默认值：[]，解析失败，则抛出异常
                    json_test = args.get('json_test/j',[]) # 方法1
                    json_test = args.get('json_test',[],'json') # 方法2

                    # 获取参数，并校验参数长度，如：password参数的长度大于等于8
                    password = args.get('password/>8','')

                    # 获取参数，并判断IP地址是否合法
                    ip = args.get('ip/i')  # 方式1 -- ipv4 and ipv6
                    ip = args.get('ip/ipv4') # 方式2
                    ip = args.get('ip/ipv6') # 方式3
                    ip = args.get('ip','0.0.0.0','ip') # 方式4 -- ipv4 and ipv6
        '''
        if key.find('/') != -1:
            key, format = key.split('/')
        result = getattr(self, key, default)
        if isinstance(result, str): result = result.strip()
        if format:
            if format in ['str', 'string', 's']:
                result = str(result)
            elif format in ['int', 'd']:
                try:
                    result = int(result)
                except:
                    raise ValueError("参数：{}，要求int类型数据".format(key))
            elif format in ['float', 'f']:
                try:
                    result = float(result)
                except:
                    raise ValueError("参数：{}，要求float类型数据".format(key))
            elif format in ['json', 'j']:
                try:
                    result = json.loads(result)
                except:
                    raise ValueError("参数：{}, 要求JSON字符串".format(key))
            elif format in ['xss', 'x']:
                result = xssencode(result)
            elif format in ['path', 'p']:
                if not path_safe_check(result):
                    raise ValueError("参数：{}，要求正确的路径格式".format(key))
                result = result.replace('//', '/')
            elif format in ['url', 'u']:
                regex = re.compile(
                    r'^(?:http|ftp)s?://'
                    r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'
                    r'localhost|'
                    r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
                    r'(?::\d+)?'
                    r'(?:/?|[/?]\S+)$', re.IGNORECASE)
                if not re.match(regex, result):
                    raise ValueError('参数：{}，要求正确的URL格式'.format(key))
            elif format in ['ip', 'ipaddr', 'i', 'ipv4', 'ipv6']:
                if format == 'ipv4':
                    if not is_ipv4(result):
                        raise ValueError('参数：{}，要求正确的ipv4地址'.format(key))
                elif format == 'ipv6':
                    if not is_ipv6(result):
                        raise ValueError('参数：{}，要求正确的ipv6地址'.format(key))
                else:
                    if not is_ipv4(result) and not is_ipv6(result):
                        raise ValueError('参数：{}，要求正确的ipv4/ipv6地址'.format(key))
            elif format in ['w', 'letter']:
                if not re.match(r'^\w+$', result):
                    raise ValueError('参数：{}，要求只能是英文字母或数据组成'.format(key))
            elif format in ['email', 'mail', 'm']:
                if not re.match(r"^.+\\@(\\[?)[a-zA-Z0-9\\-\\.]+\\.([a-zA-Z]{2,3}|[0-9]{1,3})(\\]?)$", result):
                    raise ValueError("参数：{}，要求正确的邮箱地址格式".format(key))
            elif format in ['phone', 'mobile', 'p']:
                if not re.match("^[0-9]{11,11}$", result):
                    raise ValueError("参数：{}，要求手机号码格式".format(key))
            elif format in ['port']:
                result_port = int(result)
                if result_port > 65535 or result_port < 0:
                    raise ValueError("参数：{}，要求端口号为0-65535".format(key))
                result = result_port
            elif re.match(r"^[<>=]\d+$", result):
                operator = format[0]
                length = int(format[1:].strip())
                result_len = len(result)
                error_obj = ValueError("参数：{}，要求长度为{}".format(key, format))
                if operator == '=':
                    if result_len != length:
                        raise error_obj
                elif operator == '>':
                    if result_len < length:
                        raise error_obj
                else:
                    if result_len > length:
                        raise error_obj
            elif format[0] in ['^', '(', '[', '\\', '.'] or format[-1] in ['$', ')', ']', '+', '}']:
                if not re.match(format, result):
                    raise ValueError("指定参数格式不正确, {}:{}".format(key, format))

        if limit:
            if not result in limit:
                raise ValueError("指定参数值范围不正确, {}:{}".format(key, limit))
        return result


# 实例化定目录下的所有模块
class get_modules:

    def __contains__(self, key):
        return self.get_attr(key)

    def __setitem__(self, key, value):
        setattr(self, key, value)

    def get_attr(self, key):
        '''
            尝试获取模块，若为字符串，则尝试实例化模块，否则直接返回模块对像
        '''
        res = getattr(self, key)
        if isinstance(res, str):
            try:
                tmp_obj = __import__(key)
                reload(tmp_obj)
                setattr(self, key, tmp_obj)
                return tmp_obj
            except:
                raise Exception(get_error_info())
        return res

    def __getitem__(self, key):
        return self.get_attr(key)

    def __delitem__(self, key):
        delattr(self, key)

    def __delattr__(self, key):
        delattr(self, key)

    def get_items(self):
        return self

    def __init__(self, path="class", limit=None):
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
        exp_files = ['__init__.py', '__pycache__']
        if not path in sys.path:
            sys.path.insert(0, path)
        for fname in os.listdir(path):
            if fname in exp_files: continue
            filename = '/'.join([path, fname])
            if os.path.isfile(filename):
                if not fname[-3:] in ['.py', '.so']: continue
                mod_name = fname[:-3]
            else:
                c_file = '/'.join((filename, '__init__.py'))
                if not os.path.exists(c_file):
                    continue
                mod_name = fname

            if limit:
                if not isinstance(limit, list) and not isinstance(limit, tuple):
                    limit = (limit,)
                if not mod_name in limit:
                    continue

            setattr(self, mod_name, mod_name)


# 检查App和小程序的绑定
def check_app(check='app'):
    path = get_panel_path() + '/'
    if check == 'app':
        try:
            if not os.path.exists("/www/server/panel/plugin/btapp/btapp_main.py"): return False
            if not os.path.exists(path + 'config/api.json'): return False
            if os.path.exists(path + 'config/api.json'):
                btapp_info = json.loads(readFile(path + 'config/api.json'))
                if not btapp_info['open']: return False
                if not 'apps' in btapp_info: return False
                if not btapp_info['apps']: return False
                return True
            return False
        except:
            return False
    elif check == 'app_bind':
        if not cache_get(Md5(os.uname().version)): return False
        if not os.path.exists("/www/server/panel/plugin/btapp/btapp_main.py"): return False
        if not os.path.exists(path + 'config/api.json'): return False
        btapp_info = json.loads(readFile(path + 'config/api.json'))
        if not btapp_info: return False
        if not btapp_info['open']: return False
        return True
    elif check == 'wxapp':
        if not os.path.exists(path + 'plugin/app/user.json'): return False
        app_info = json.loads(readFile(path + 'plugin/app/user.json'))
        if not app_info: return False
        return True


# 宝塔邮件报警
def send_mail(title, body, is_logs=False, is_type="堡塔登录提醒"):
    try:
        import panelPush
        msg_data = {
            "msg": body.replace("\n", "<br/>"),
            "title": title
        }
        if is_logs: WriteLog2(is_type, body)
        return panelPush.panelPush().push_message_immediately({"mail": msg_data})
    except Exception as ex:
        return returnMsg(False, '发送失败: {}'.format(ex))


# 发送钉钉告警
def send_dingding(body, is_logs=False, is_type="堡塔登录提醒"):
    try:
        import panelPush
        if is_logs: WriteLog2(is_type, body)
        return panelPush.panelPush().push_message_immediately({"dingding": {"msg": body}})
    except Exception as ex:
        return returnMsg(False, '发送失败: {}'.format(ex))


# 发送微信告警
def send_weixin(body, is_logs=False, is_type="堡塔登录提醒"):
    try:
        import panelPush
        if is_logs: WriteLog2(is_type, body)
        return panelPush.panelPush().push_message_immediately({"weixin": {"msg": body}})
    except Exception as ex:
        return returnMsg(False, '发送失败: {}'.format(ex))


# 发送飞书告警
def send_feishu(body, is_logs=False, is_type="堡塔登录提醒"):
    try:
        import panelPush
        if is_logs: WriteLog2(is_type, body)
        return panelPush.panelPush().push_message_immediately({"feishu": {"msg": body}})
    except Exception as ex:
        return returnMsg(False, '发送失败: {}'.format(ex))


# 发送除短信以外的所有告警通道
def send_all(body, title=None):
    try:
        import panelPush
        msg_dict = {"msg": body}
        msg_all = {
            "feishu": msg_dict,
            "weixin": msg_dict,
            "dingding": msg_dict,
            "mail": {
                "msg": body.replace("\n", "<br/>"),
                "title": title
            }
        }
        return panelPush.panelPush().push_message_immediately(msg_all)
    except Exception as ex:
        return returnMsg(False, '发送失败: {}'.format(ex))


# 获取服务器IP
def get_ip():
    iplist_file = '{}/data/iplist.txt'.format(get_panel_path())
    if os.path.exists(iplist_file):
        data = ReadFile(iplist_file)
        return data.strip()
    else:
        return '127.0.0.1'


# 获取服务器内网Ip
def get_local_ip():
    try:
        ret = ExecShell("ip addr | grep -E -o '[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}' | grep -E -v \"^127\.|^255\.|^0\.\" | head -n 1")
        local_ip = ret[0].strip()
        return local_ip
    except:
        return '127.0.0.1'


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


def WriteLog2(type, logMsg, args=(), not_web=False):
    import db
    create_logs()
    username = 'system'
    uid = 1
    tmp_msg = ''
    sql = db.Sql()
    mDate = time.strftime('%Y-%m-%d %X', time.localtime())
    data = (uid, username, type, logMsg + tmp_msg, mDate)
    result = sql.table('logs2').add('uid,username,type,log,addtime', data)


def check_ip_white(path, ip):
    if os.path.exists(path):
        try:
            path_json = json.loads(ReadFile(path))
        except:
            WriteFile(path, '[]')
            return False
        if ip in path_json:
            return True
        else:
            return False
    else:
        return False


def check_login_area(login_ip, login_type='panel'):
    """
    @name 检测登录地区
    @login_type 登录类型 panel:宝塔面板登录, ssh:ssh登录
    """

    login_ip_area = ''
    ip_info = get_ips_area([login_ip])

    if 'status' in ip_info:
        login_ip_area = '****（开通企业版可查看）'
    else:
        ip_info = ip_info[login_ip]
        if not 'city' in ip_info:
            login_ip_area = ip_info['info']

    data = {}
    status = False
    sfile = '{}/data/{}_login_area.pl'.format(get_panel_path(), login_type)
    s_conf = '{}/data/{}_login_area.json'.format(get_panel_path(), login_type)
    if os.path.exists(sfile):
        status = True

    data = {}
    try:
        data = json.loads(readFile(s_conf))
    except:
        pass

    if not login_ip_area and 'city' in ip_info:
        city = ip_info['city']
        login_ip_area = ip_info['info']

        if not city in data:
            data[city] = 0

        if data[city] < 3:
            login_ip_area += '（<font color=red>异地</font>）'
        data[city] += 1

        writeFile(s_conf, json.dumps(data))

    data['login_ip_area'] = login_ip_area
    return status, data


def get_free_ips_area(ips):
    '''
    @name 免费IP库 获取ip地址所在地
    @author cjxin
    @param ips<list>
    @return list
    '''
    import PluginLoader
    args = dict_obj()
    args.model_index = 'safe'
    args.ips = ips
    res = PluginLoader.module_run("freeip", "get_ip_area", args)
    return res


def get_free_ip_info(address):
    '''
    @name 免费IP库 获取ip地址所在地
    @param ip<string>
    @return dict
    '''
    ip = address.split(':')[0]
    if not is_ipv4(ip):
        return {'info': '未知归属地'}
    if is_local_ip(ip):
        return {'info': '内网地址', 'local': True}

    ip_info = {}
    sfile = '{}/data/ip_area.json'.format(get_panel_path())
    try:
        ip_info = json.loads(readFile(sfile))
    except:
        pass

    if ip in ip_info:
        return ip_info[ip]
    try:
        param = get_user_info()
        param['ip'] = address
        res = json.loads(httpPost('https://www.bt.cn/api/ip/info_json', param))
        # 解决无法访问官网时获取ip归属地的问题
        if not address in res:
            host_list = json.loads(readFile("config/hosts.json"))
            headers = {"host": "www.bt.cn"}
            for host in host_list:
                try:
                    new_url = "https://{}/api/ip/info_json?ip={}".format(host, address)
                    res = HttpGet(new_url, 1, headers=headers)
                except:
                    continue

        if address in res:
            info = res[address]
            ip_info[ip] = info
            ip_info[ip]['info'] = '{} {} {} {}'.format(info['carrier'], info['country'], info['province'], info['city']).strip()
            ip_info[ip]['ip'] = ip
            writeFile(sfile, json.dumps(ip_info))
            return res[address]
    except:
        pass

    return {'info': '未知归属地'}


# 使用免费IP库获取IP地区
def free_login_area(login_ip, login_type='panel'):
    """
    @name 使用免费IP库获取IP地区
    @login_type 登录类型 panel:宝塔面板登录, ssh:ssh登录
    """
    # 判断是否开启免费IP库
    if os.path.exists('{}/data/{}_login_area.pl'.format(get_panel_path(), 'btpanel')):
        return False, {}
    login_ip_area = ''
    ip_info = get_free_ips_area([login_ip])
    if not login_ip in ip_info:
        return False, {}
    ip_info = ip_info[login_ip]
    if not 'city' in ip_info:
        login_ip_area = ip_info['info']
    status = True
    s_conf = '{}/data/{}_login_area.json'.format(get_panel_path(), login_type)
    data = {}
    try:
        data = json.loads(readFile(s_conf))
    except:
        pass
    if not login_ip_area and 'city' in ip_info:
        city = ip_info['city']
        login_ip_area = ip_info['info']
        if len(city) >= 1 and not city in data:
            data[city] = 0
        if data[city] < 3 and city == "内网地址":
            login_ip_area += '（<font color=red>内网</font>）'
            # if city == '内网地址':
            #     login_ip_area += '（<font color=red>内网</font>）'
            # else:
            #     login_ip_area += '（<font color=red>异地</font>）'
        data[city] += 1
        writeFile(s_conf, json.dumps(data))
    data['login_ip_area'] = login_ip_area
    return status, data


# 登陆告警
def login_send_body(is_type, username, login_ip, port):
    send_type = ""
    panel_path = get_panel_path()
    login_send_type_conf = "/www/server/panel/data/panel_login_send.pl"
    if os.path.exists(login_send_type_conf):
        send_type = ReadFile(login_send_type_conf).strip()
    else:
        # 兼容之前的
        if os.path.exists("/www/server/panel/data/login_send_type.pl"):
            send_type = readFile("/www/server/panel/data/login_send_type.pl")
        else:
            if os.path.exists('/www/server/panel/data/login_send_mail.pl'):
                send_type = "mail"
            if os.path.exists('/www/server/panel/data/login_send_dingding.pl'):
                send_type = "dingding"

    # 增加异地登录告警
    server_ip_area = login_ip + ":" + port
    login_aera_status, login_aera = free_login_area(login_ip=server_ip_area, login_type='panel')
    if login_aera_status:
        login_ip_area = ">归属地：" + login_aera['login_ip_area']
        # 如果存在归属地则修改日志内容
        time.sleep(0.2)
        if cache_get(server_ip_area):
            id = cache_get(server_ip_area)
            logs = M("logs").where("id=?", id).getField("log")
            data = M("logs").where("id=?", id).setField("log", logs + login_ip_area)
    else:
        login_ip_area = ''

    add_security_logs('登录成功', server_ip_area + login_ip_area, False)
    if not send_type:
        return False

    object = init_msg(send_type.strip())
    if not object: return

    send_login_white = '{}/data/send_login_white.json'.format(panel_path)
    if check_ip_white(send_login_white, login_ip):
        return False

    if login_ip_area:
        plist = [
            ">登录方式：" + is_type,
            ">登录账号：" + username,
            ">登录IP：" + login_ip + ":" + port,
            login_ip_area,
            ">登录状态：<font color=#20a53a>成功</font>"
        ]
    else:
        plist = [
            ">登录方式：" + is_type,
            ">登录账号：" + username,
            ">登录IP：" + login_ip + ":" + port,
            ">登录状态：<font color=#20a53a>成功</font>"
        ]

    push_data = {
        "ip": get_server_ip(),
        "is_type": is_type,
        "username": username,
        "login_ip": login_ip,
        "login_ip_area": login_ip_area,
        "msg_list": plist
    }
    try:
        from mod.base.push_mod import push_by_task_keyword
        res = push_by_task_keyword("panel_login", "panel_login", push_data=push_data)
        if res:
            return
    except:
        print_log(get_error_info())
        pass

    if send_type == 'sms':
        data = {}
        data['ip'] = get_server_ip()
        data['local_ip'] = get_network_ip()
        # 不加内网IP，否则短信模板参数长度超过限制
        ip = "{}(外)".format(data['ip'])
        sm_args = {'name': '[' + ip + ']', 'time': time.strftime('%Y-%m-%d %X', time.localtime()), 'type': '[' + is_type + ']',
                   'user': username}
        rdata = object.send_msg('login_panel', check_sms_argv(sm_args))
    else:
        from panel_msg.collector import SitePushMsgCollect

        msg = SitePushMsgCollect.panel_login(plist)

        if send_type.strip() == "wx_account":
            from push.site_push import ToWechatAccountMsg
            object.send_msg(ToWechatAccountMsg.panel_login(
                name=username,
                ip=login_ip,
                login_type=is_type,
                address=login_ip_area,
                login_time=time.strftime('%Y-%m-%d %X', time.localtime())
            ))
        else:
            info = get_push_info("面板登录告警", plist)
            info["push_type"] = "面板登录告警"
            object.push_data(info)

        # if send_type == "dingding":
        #     msg = "#### 堡塔登录提醒\n\n > 服务器　："+get_ip()+"\n\n > 登录方式："+is_type+"\n\n > 登录账号："+username+"\n\n > 登录ＩＰ："+login_ip+":"+port+"\n\n > 登录时间："+time.strftime('%Y-%m-%d %X',time.localtime())+'\n\n > 登录状态:  <font color=#20a53a>成功</font>'
        #     send_dingding(msg, False)
        # elif send_type == "weixin":
        #     msg = "#### 堡塔登录提醒\n\n > 服务器　："+get_ip()+"\n\n > 登录方式："+is_type+"\n\n > 登录账号："+username+"\n\n > 登录ＩＰ："+login_ip+":"+port+"\n\n > 登录时间："+time.strftime('%Y-%m-%d %X',time.localtime())+'\n\n > 登录状态:  <font color=#20a53a>成功</font>'
        #     send_weixin(msg, False)
        # elif send_type == "feishu":
        #     msg = "堡塔登录提醒\n > 服务器　："+get_ip()+"\n > 登录方式："+is_type+"\n > 登录账号："+username+"\n > 登录ＩＰ："+login_ip+":"+port+"\n > 登录时间："+time.strftime('%Y-%m-%d %X',time.localtime())+'\n > 登录状态: 成功'
        #     send_feishu(msg, False)


# 普通模式下调用发送消息【设置登陆告警后的设置】
# title= 发送的title
# body= 发送的body
# is_logs= 是否记录日志
# is_type=发送告警的类型
def send_to_body(title, body, is_logs=False, is_type="堡塔邮件告警"):
    login_send_mail = "{}/data/login_send_mail.pl".format(get_panel_path())
    login_send_dingding = "{}/data/login_send_dingding.pl".format(get_panel_path())
    if os.path.exists(login_send_mail):
        if is_logs:
            send_mail(title, body, True, is_type)
        send_mail(title, body)

    if os.path.exists(login_send_dingding):
        if is_logs:
            send_dingding(body, True, is_type)
        send_dingding(body)


# 普通发送消息
# send_type= ["mail","dingding"]
# title =发送的头
# body= 发送消息的内容
def send_body_words(send_type, title, body):
    if send_type == 'mail':
        return send_mail(title, body)
    if send_type == 'dingding':
        return send_dingding(body)


def return_is_send_info():
    import send_mail
    send_mail22 = send_mail.send_mail()
    tongdao = send_mail22.get_settings()
    ret = {}
    ret['mail'] = tongdao['user_mail']['user_name']
    ret['dingding'] = tongdao['dingding']['dingding']
    return ret


def get_sys_path():
    '''
        @name 关键目录
        @author hwliang<2021-06-11>
        @return tuple
    '''
    a = ['/www', '/usr', '/', '/dev', '/home', '/media', '/mnt', '/opt', '/tmp', '/var']
    c = ['/www/.Recycle_bin/', '/www/backup/', '/www/php_session/', '/www/wwwlogs/', '/www/server/', '/etc/', '/usr/', '/var/', '/boot/', '/proc/', '/sys/', '/tmp/', '/root/', '/lib/', '/bin/',
         '/sbin/', '/run/', '/lib64/', '/lib32/', '/srv/']
    return a, c


def check_site_path(site_path):
    '''
        @name 检查网站根目录是否为系统关键目录
        @author hwliang<2021-05-31>
        @param site_path<string> 网站根目录全路径
        @return bool
    '''
    try:
        if site_path.find('/usr/local/lighthouse/') >= 0:
            return True

        if site_path in ['/', '/usr', '/dev', '/home', '/media', '/mnt', '/opt', '/tmp', '/var']:
            return False
        whites = ['/www/server/tomcat', '/www/server/stop', '/www/server/phpmyadmin']
        for w in whites:
            if site_path.find(w) == 0: return True
        a, error_paths = get_sys_path()
        site_path = site_path.strip()
        if site_path[-1] == '/': site_path = site_path[:-1]
        if site_path in a:
            return False
        site_path += '/'
        for ep in error_paths:
            if site_path.find(ep) == 0: return False
        return True
    except:
        return False


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


def sys_path_append(path):
    '''
        @name 追加引用路径
        @author hwliang<2021-07-07>
        @param path<string> 路径
        @return void
    '''
    try:
        if not path in sys.path:
            sys.path.insert(0, path)
    except:
        pass


def get_plugin_find(upgrade_plugin_name=None):
    '''
        @name 获取指定软件信息
        @author hwliang<2021-06-15>
        @param upgrade_plugin_name<string> 插件名称
        @return dict
    '''
    import panelPlugin
    plugin_list_data = panelPlugin.panelPlugin().get_cloud_list()

    for p_data_info in plugin_list_data['list']:
        if p_data_info['name'] == upgrade_plugin_name:
            upgrade_plugin_name = p_data_info['name']
            return p_data_info

    return get_plugin_info(upgrade_plugin_name)


def get_plugin_value(plugin_name, key):
    '''
        @name 获取插件配置值
        @author hwliang
        @param plugin_name<string> 插件名称
        @param key<string> 字段名
        @return mixed
    '''
    plugin_info = get_plugin_find(plugin_name)
    return plugin_info.get(key, None)


def get_plugin_pid(plugin_name):
    '''
        @name 获取指定插件的pid
        @author hwliang<2021-06-15>
        @param plugin_name<string> 插件名称
        @return string
    '''
    plugin_info = get_plugin_find(plugin_name)
    if not plugin_info: return 0
    if 'pid' in plugin_info:
        return plugin_info['pid']
    return 0


def get_plugin_info(upgrade_plugin_name):
    '''
        @name 获取插件信息
        @author hwliang<2021-06-15>
        @param upgrade_plugin_name<string> 插件名称
        @return dict
    '''
    plugin_path = get_plugin_path()
    plugin_info_file = '{}/{}/info.json'.format(plugin_path, upgrade_plugin_name)
    if not os.path.exists(plugin_info_file): return {}
    info_body = readFile(plugin_info_file)
    if not info_body: return {}
    plugin_info = json.loads(info_body)
    return plugin_info


def download_main(upgrade_plugin_name, upgrade_version):
    '''
        @name 下载插件主程序文件
        @author hwliang<2021-06-25>
        @param upgrade_plugin_name<string> 插件名称
        @param upgrade_version<string> 插件版本
        @return void
    '''
    import requests, shutil
    plugin_path = get_plugin_path()
    tmp_path = '{}/temp'.format(get_panel_path())
    download_d_main_url = 'https://api.bt.cn/down/download_plugin_main'
    pdata = get_user_info()
    pdata['name'] = upgrade_plugin_name
    pdata['version'] = upgrade_version
    pdata['os'] = 'Linux'
    import config, socket
    import requests.packages.urllib3.util.connection as urllib3_conn
    _ip_type = config.config().get_request_iptype()
    # old_family = urllib3_conn.allowed_gai_family
    if _ip_type == 'ipv4':
        urllib3_conn.allowed_gai_family = lambda: socket.AF_INET
    elif _ip_type == 'ipv6':
        urllib3_conn.allowed_gai_family = lambda: socket.AF_INET6
    try:
        download_res = requests.post(download_d_main_url, pdata, timeout=30, headers=get_requests_headers())
    except Exception as ex:
        raise PanelError(error_conn_cloud(str(ex)))
    finally:
        reset_allowed_gai_family()
    filename = '{}/{}.py'.format(tmp_path, upgrade_plugin_name)
    with open(filename, 'wb+') as save_script_f:
        save_script_f.write(download_res.content)
        save_script_f.close()

    if md5(download_res.content) != download_res.headers.get('Content-md5'):
        raise PanelError('插件安装包HASH校验失败')
    dst_file = '{plugin_path}/{plugin_name}/{plugin_name}_main.py'.format(plugin_path=plugin_path, plugin_name=upgrade_plugin_name)
    shutil.copyfile(filename, dst_file)
    if os.path.exists(filename): os.remove(filename)
    WriteLog('软件管理', "检测到插件[{}]程序文件异常，已尝试自动修复!".format(get_plugin_info(upgrade_plugin_name)['title']))


def get_plugin_bin(plugin_save_file, plugin_timeout):
    list_body = None
    plugin_timeout = 86400
    if not os.path.exists(plugin_save_file): return list_body
    s_time = time.time()
    m_time = os.stat(plugin_save_file).st_mtime
    if (s_time - m_time) < plugin_timeout or not plugin_timeout:
        list_body = readFile(plugin_save_file, 'rb')
    return list_body


def get_plugin_main_object(plugin_name, sys_path):
    os_file = sys_path + '/' + plugin_name + '_main.so'
    php_file = sys_path + '/index.php'
    is_php = False
    plugin_obj = None
    if os.path.exists(os_file):  # 是否为编译后的so文件
        try:
            plugin_obj = __import__(plugin_name + '_main')
        except Exception as ex:
            if str(ex).find('undefined symbol') != -1:
                re_download_main(plugin_name, get_plugin_path())
                writeFile("{}/data/{}.pl".format(get_panel_path(), plugin_name), '1')
                raise PanelError('插件程序文件异常，已尝试自动修复，请刷新页面重试!')
    elif os.path.exists(php_file):  # 是否为PHP代码
        import panelPHP
        is_php = True
        plugin_obj = panelPHP.panelPHP(plugin_name)

    return plugin_obj, is_php


def get_plugin_script(plugin_name, plugin_path):
    # 优先运行py文件
    plugin_file = '{plugin_path}/{name}/{name}_main.py'.format(plugin_path=plugin_path, name=plugin_name)
    if not os.path.exists(plugin_file): return '', True
    plugin_body = readFile(plugin_file, 'rb')

    if plugin_body.find(b'import') != -1:
        return plugin_body, True

    # 重新下载空文件
    if not plugin_body.strip():
        re_download_main(plugin_name, get_plugin_path())
        writeFile("{}/data/{}.pl".format(get_panel_path(), plugin_name), '1')
        plugin_body = readFile(plugin_file, 'rb')
        if plugin_body.find(b'import') != -1: return plugin_body, True

    plugin_file_so = '{plugin_path}/{name}/{name}_main.so'.format(plugin_path=plugin_path, name=plugin_name)
    if len(plugin_body) > 1024 and plugin_body.find(b'+') != -1 and plugin_body.find(b'/') != -1:
        plugin_path = get_plugin_path(plugin_name)
        up_file = '{}/upgrade.sh'.format(plugin_path)
        if os.path.exists(up_file) and os.path.exists(plugin_file_so):  # 删除无效的so文件
            ExecShell("rm -f {}/*.so".format(plugin_path))
        return plugin_body, False

    # 无py文件再运行so
    if os.path.exists(plugin_file_so): return '', True

    return plugin_body, False


def re_download_main(plugin_name, plugin_path):
    plugin_file = '{plugin_path}{name}/{name}_main.py'.format(plugin_path=plugin_path, name=plugin_name)
    plugin_info = get_plugin_info(plugin_name)
    if 'versions' in plugin_info:
        version = plugin_info['versions']
        download_main(plugin_name, version)
        plugin_body = readFile(plugin_file, 'rb')
        return plugin_body
    return b''


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


def get_soft_path():
    return get_setup_path()


def get_panel_path():
    '''
        @name 取面板根目录
        @author hwliang<2021-07-14>
        @return string
    '''
    return '{}/panel'.format(get_setup_path())


def get_plugin_path(plugin_name=None):
    '''
        @name 取指定插件目录
        @author hwliang<2021-07-14>
        @param plugin_name<string> 插件名称 不传则返回插件根目录
        @return string
    '''

    root_path = "{}/plugin".format(get_panel_path())
    if not plugin_name: return root_path
    return "{}/{}".format(root_path, plugin_name)


def get_class_path():
    '''
        @name 取类库所在路径
        @author hwliang<2021-07-14>
        @return string
    '''
    return "{}/class".format(get_panel_path())


def decode_data(srcBody):
    """
    遍历解码字符串
    """
    arrs = ['utf-8', 'GBK', 'ANSI', 'BIG5']
    for encoding in arrs:
        try:
            data = srcBody.decode(encoding)
            return encoding, data
        except:
            pass
    return False, None


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
    backup_path = M('config').where("id=?", (1,)).getField('backup_path')
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
    site_path = M('config').where("id=?", (1,)).getField('sites_path')
    if not site_path: return default_site_path
    if os.path.exists(site_path): return site_path
    return default_site_path


def read_config(config_name, ext_name='json'):
    '''
        @name 读取指定配置文件
        @author hwliang<2021-07-14>
        @param config_name<string> 配置文件名称(不含扩展名)
        @param ext_name<string> 配置文件扩展名，默认为json
        @return string 如果发生错误，将抛出PanelError异常
    '''
    config_file = "{}/config/{}.{}".format(get_panel_path(), config_name, ext_name)
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


def save_config(config_name, config_body, ext_name='json'):
    '''
        @name 保存配置文件
        @author hwliang<2021-07-14>
        @param config_name<string> 配置文件名称(不含扩展名)
        @param config_body<mixed> 被保存的内容, ext_name为json，请传入可解析为json的参数类型，如list,dict,int,str等
        @param ext_name<string> 配置文件扩展名，默认为json
        @return string 如果发生错误，将抛出PanelError异常
    '''

    config_file = "{}/config/{}.{}".format(get_panel_path(), config_name, ext_name)
    if ext_name == 'json':
        try:
            config_body = json.dumps(config_body)
        except Exception as ex:
            raise PanelError('配置内容无法被转换为json格式!\n{}'.format(ex))

    return writeFile(config_file, config_body)


def get_config_value(config_name, key, default='', ext_name='json'):
    '''
        @name 获取指定配置文件的指定配置项
        @author hwliang<2021-07-14>
        @param config_name<string> 配置文件名称(不含扩展名)
        @param key<string> 配置项
        @param default<mixed> 获不存在则返回的默认值，默认为空字符串
        @param ext_name<string> 配置文件扩展名，默认为json
        @return mixed 如果发生错误，将抛出PanelError异常
    '''
    config_data = read_config(config_name, ext_name)
    return config_data.get(key, default)


def set_config_value(config_name, key, value, ext_name='json'):
    '''
        @name 设置指定配置文件的指定配置项
        @author hwliang<2021-07-14>
        @param config_name<string> 配置文件名称(不含扩展名)
        @param key<string> 配置项
        @param value<mixed> 配置值
        @param ext_name<string> 配置文件扩展名，默认为json
        @return mixed  如果发生错误，将抛出PanelError异常
    '''
    config_data = read_config(config_name, ext_name)
    config_data[key] = value
    return save_config(config_name, config_data, ext_name)


def return_data(status, data={}, status_code=None, error_msg=None):
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
        'status': status,
        "status_code": status_code,
        'error_msg': str(error_msg),
        'data': data
    }
    return result


def return_error(error_msg, status_code=-1, data=[]):
    '''
        @name 格式化错误响应内容
        @author hwliang<2021-07-15>
        @param error_msg<string> 错误消息
        @param status_code<int> 状态码，默认为-1
        @param data<mixed> 响应数据
        @return dict
    '''
    if not data: data = error_msg
    return return_data(False, data, status_code, str(error_msg))


def error(error_msg, status_code=-1, data=[]):
    '''
        @name 格式化错误响应内容
        @author hwliang<2021-07-15>
        @param error_msg<string> 错误消息
        @param status_code<int> 状态码，默认为-1
        @param data<mixed> 响应数据
        @return dict
    '''
    if not data: data = error_msg
    return return_error(error_msg, status_code, data)


def success(data=[], status_code=1, error_msg=''):
    '''
        @name 格式化成功响应内容
        @author hwliang<2021-07-15>
        @param data<mixed> 响应数据
        @param status_code<int> 状态码，默认为0
        @return dict
    '''
    return return_data(True, data, status_code, error_msg)


def return_status_code(status_code, format_body, data=[]):
    '''
        @name 按状态码返回
        @author hwliang<2021-07-15>
        @param status_code<int> 状态码
        @param format_body<string> 错误内容
        @param data<mixed> 响应数据
        @return dict
    '''
    error_msg = get_config_value('status_code', str(status_code))
    if not error_msg: raise PanelError('指定状态码不存在!')
    return return_data(error_msg[0], data, status_code, error_msg[1].format(format_body))


def to_dict_obj(data):
    '''
        @name 将dict转换为dict_obj
        @author hwliang<2021-07-15>
        @param data<dict> 要被转换的数据
        @return dict_obj
    '''
    if not isinstance(data, dict):
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
    _obj = sys.modules.get(filename, None)
    if _obj: return _obj
    from types import ModuleType
    _obj = sys.modules.setdefault(filename, ModuleType(filename))
    _code = readFile(filename)
    _code_object = compile(_code, filename, 'exec')
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
        filename = os.path.join(hooks_path, hook_name)
        _obj = get_script_object(filename)
        _main = getattr(_obj, 'main', None)
        if not _main: continue
        _main()


def register_hook(hook_index, hook_def):
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


def exec_hook(hook_index, data):
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


def get_hook_index(mod_name, def_name):
    '''
        @name 获取HOOK位置
        @author hwliang<2021-07-19>
        @param mod_name<string> 模块名称
        @param def_name<string> 方法名称
        @return tuple
    '''
    mod_name = mod_name.upper()
    def_name = def_name.upper()
    last_index = '{}_{}_LAST'.format(mod_name, def_name)
    end_index = '{}_{}_END'.format(mod_name, def_name)
    return last_index, end_index


def flush_plugin_list():
    '''
        @name 刷新插件列表
        @author hwliang<2021-07-22>
        @return bool
    '''
    skey = 'TNaMJdG3mDHKRS6Y'
    from BTPanel import cache
    # from pluginAuth import Plugin
    import PluginLoader
    if cache.get(skey): cache.delete(skey)
    PluginLoader.get_plugin_list(1)
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
    cache.set(skey, session_timeout, 3600)
    return session_timeout


def clear_sql_session():
    """
    清空所用数据库中存储的session内容
    :return:
    """
    import tempfile
    import sqlite3

    db_file = "{}/data/db/session.db".format(get_panel_path())
    fd, tmp_file = tempfile.mkstemp(suffix="____.tmp_session", dir=os.path.dirname(db_file))
    os.close(fd)
    conn = sqlite3.connect(tmp_file)
    cur = conn.cursor()
    cur.executescript("""
CREATE TABLE sessions (
        id INTEGER NOT NULL, 
        session_id VARCHAR(255), 
        data BLOB, 
        expiry DATETIME, 
        PRIMARY KEY (id), 
        UNIQUE (session_id)
);
CREATE INDEX ix_sessions_expiry ON sessions (expiry);
""")
    cur.close()
    conn.close()
    os.replace(tmp_file, db_file)


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
    cache.set(skey, login_token, 3600)
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


def print_log(*args, _level='DEBUG', color="debug"):
    '''
        @name 写入日志
        @author hwliang<2021-08-12>
        @param *args <any> 要写入到日志文件的信息可以是多个，任意类型
        @param _level<string> 日志级别
        @param color<string> 日志颜色，可选值：red,green,yellow,blue,purple,cyan,white,gray,black,info,success,warning,warn,err,error,debug,trace,critical,fatal
        @return void
    '''
    import inspect
    import json
    color_start = ''
    color_end = ''
    color_dict = {
        'red': '\033[31m',
        'green': '\033[32m',
        'yellow': '\033[33m',
        'blue': '\033[34m',
        'purple': '\033[35m',
        'cyan': '\033[36m',
        'white': '\033[37m',
        'gray': '\033[90m',
        'black': '\033[30m',
        'info': '\033[0m',
        'success': '\033[32m',
        'warning': '\033[33m',
        'warn': '\033[33m',
        'err': '\033[31m',
        'error': '\033[31m',
        'debug': '\033[36m',
        'trace': '\033[35m',
        'critical': '\033[31m',
        'fatal': '\033[31m'
    }
    if color:
        color = color.strip().lower()
        if color in color_dict:
            color_start = color_dict[color]
            color_end = '\033[0m'

    # 获取调用者的文件名、函数名和行号
    caller_file = ''
    caller_function = ''
    caller_lineno = 0
    try:
        frame = inspect.currentframe()
        caller_frame = frame.f_back
        caller_info = inspect.getframeinfo(caller_frame)
        caller_file = caller_info.filename
        caller_function = caller_info.function
        caller_lineno = caller_info.lineno
        if caller_function == "print_error" and caller_file.find("public.py") != -1:
            caller_frame = caller_frame.f_back
            caller_info = inspect.getframeinfo(caller_frame)
            caller_file = caller_info.filename
            caller_function = caller_info.function
            caller_lineno = caller_info.lineno
    except:
        pass

    log_body = "{}[{}][{}][{}:{}:{}]".format(
        color_start, format_date(), _level.upper(), caller_file, caller_function, caller_lineno
    )

    for _info in args:
        try:
            if isinstance(_info, (dict, list, tuple)):
                _info = json.dumps(_info, indent=4, ensure_ascii=False)
            else:
                _info = str(_info)
        except:
            _info = str(_info)

        log_body += " {}".format(_info)

    log_body += "{}\n".format(color_end)
    # 2024/11/25 11:31 输出结果解析：
    # [2024-11-25 11:30:35][DEBUG][class/config.py:get_menu_list:2403] 1
    # [时间：0000-00-00 00:00:00][日志级别][文件名:函数名:行号] 日志内容

    # debug 状态会把 stdout 和 stderr 重定向到日志文件，所以不需要print输出
    # print(log_body.strip())
    WriteFile(get_panel_log_file(), log_body, 'a+')


def print_error():
    '''
        @name 打印错误信息到日志文件
        @author hwliang
        @return void
    '''
    print_log(get_error_info(), 'ERROR')


def to_date(format="%Y-%m-%d %H:%M:%S", times=None):
    '''
        @name 格式时间转时间戳
        @author hwliang<2021-08-17>
        @param format<string> 时间格式
        @param times<date> 时间
        @return int
    '''
    if times:
        if isinstance(times, int): return times
        if isinstance(times, float): return int(times)
        if re.match("^\d+$", times): return int(times)
    else:
        return 0
    ts = time.strptime(times, format)
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


def error_not_login(e=None, _src=None):
    '''
        @name 未登录时且未输入正确的安全入口时的响应
        @author hwliang<2021-12-16>
        @return Response
    '''
    from BTPanel import Response, render_template, redirect, request
    client_status = check_client_info()
    x_http_token = request.headers.get('x-http-token')
    if client_status == 1:
        if x_http_token:
            result = {"status": False, "code": -8888, "redirect": get_admin_path(), "msg": "当前登录会话已经失效，请重新登录!"}
            return Response(json.dumps(result), mimetype='application/json', status=200)
        return redirect(get_admin_path())
    elif client_status == 2:
        if x_http_token:
            result = {"status": False, "code": -8888, "redirect": "/login", "msg": "当前登录会话已经失效，请重新登录!"}
            return Response(json.dumps(result), mimetype='application/json', status=200)
        return render_template('autherr.html')

    try:
        abort_code = read_config('abort')
        if not abort_code in [None, 1, 0, '0', '1']:
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
        return error_404(e)


def error_403(e):
    from BTPanel import Response, session
    # if not session.get('login',None): return error_not_login()
    errorStr = '''<html>\r\n<head><title>403 Forbidden</title></head>\r\n<body>\r\n<center><h1>403 Forbidden</h1></center>\r\n<hr><center>nginx</center>\r\n</body>\r\n</html>\r\n'''
    headers = {
        "Content-Type": "text/html"
    }
    return Response(errorStr, status="403 Forbidden", headers=headers)


def error_404(e):
    from BTPanel import Response, session
    # if not session.get('login',None): return error_not_login()
    errorStr = "<html>\r\n<head><title>404 Not Found</title></head>\r\n<body>\r\n<center><h1>404 Not Found</h1></center>\r\n<hr><center>nginx</center>\r\n</body>\r\n</html>\r\n"
    headers = {
        "Content-Type": "text/html"
    }
    return Response(errorStr, status="404 Not Found", headers=headers)


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
    flag = False
    try:
        nginx_path = '/www/server/panel/vhost/nginx/btwaf.conf'
        if os.path.exists(nginx_path):
            ExecShell('mv  %s %s.bak' % (nginx_path, nginx_path))
            flag = True
        nginx_path = '/www/server/panel/vhost/nginx/free_waf.conf'
        if os.path.exists(nginx_path):
            ExecShell('mv  %s %s.bak' % (nginx_path, nginx_path))
            flag = True
        apache_path = '/www/server/panel/vhost/apache/btwaf.conf'
        if os.path.exists(apache_path):
            ExecShell('chattr -i %s && mv %s %s.bak' % (apache_path, apache_path, apache_path))
            flag = True
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
        version_list = json.loads(readFile(_file))
    else:
        version_list = ['52', '53', '54', '55', '56', '70', '71', '72', '73', '74', '80', '81', '82', '83','84','85']

    return sorted(version_list, reverse=reverse)


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
    else:
        code_msg = text
    err_template_file = '{}/BTPanel/templates/default/error_connect.html'.format(get_panel_path())
    msg = readFile(err_template_file)
    msg = msg.format(code=code_msg)
    return PanelError(msg)


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
    mount_list.sort(key=lambda i: len(i), reverse=True)
    return mount_list


def get_path_in_mountpoint(path):
    '''
        @name 获取文件或目录目录所在挂载点
        @author hwliang<2022-03-30>
        @param path<string> 文件或目录路径
        @return string
    '''
    if not os.path.islink(path):
        path = os.path.realpath(path)
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
    try:
        if not os.path.exists(recycle_bin_path):
            os.mkdir(recycle_bin_path, 384)
    except:
        return '/www/.Recycle_bin/'
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
        try:
            os.rename(default_path_src, default_path)
        except:
            ExecShell("mv {} {}".format(default_path_src, default_path))

    if not os.path.exists(default_path):
        os.makedirs(default_path, 384)

    # 获取回收站列表
    recycle_bin_list = []
    mtime_list = []  # 修改时间
    for mountpoint in get_mountpoint_list():
        recycle_bin_path = '{}.Recycle_bin/'.format(mountpoint)

        try:
            if not os.path.exists(recycle_bin_path):
                os.mkdir(recycle_bin_path, 384)
            if not os.path.exists(recycle_bin_path): continue
            mtime = os.path.getmtime(recycle_bin_path)
            if mtime in mtime_list: continue  # 通过修改时间去重
            mtime_list.append(mtime)
            recycle_bin_list.append(recycle_bin_path)
        except:
            continue

    # 包含默认回收站路径？
    if not default_path + '/' in recycle_bin_list:
        recycle_bin_list.append(default_path + '/')

    return recycle_bin_list


def set_module_logs(mod_name, fun_name, count=1):
    """
    @模块使用次数
    @mod_name 模块名称
    @fun_name 函数名
    """
    import datetime
    data = {}
    path = '{}/data/mod_log.json'.format(get_panel_path())
    if os.path.exists(path):
        try:
            data = json.loads(readFile(path))
        except:
            pass

    if type(data) != dict:
        data = {}

    key = datetime.datetime.now().strftime("%Y-%m-%d")
    if not key in data: data[key] = {}

    if not mod_name in data[key]:
        data[key][mod_name] = {}

    if not fun_name in data[key][mod_name]:
        data[key][mod_name][fun_name] = 0

    data[key][mod_name][fun_name] += count

    writeFile(path, json.dumps(data))
    return True


headers_filter_rules = None


def filter_headers():
    '''
        @name 过滤请求头
        @author hwliang<2021-12-18>
        @return dict
    '''
    global headers_filter_rules

    # 预编译过滤规则
    if not headers_filter_rules:
        headers_filter_rules = {
            'host': re.compile(r'^[\w\.\-\:]+$'),
            'accept': re.compile(r'^[\w\s\.\-\*\/\,\=\;\+]+$'),
            'accept-encoding': re.compile(r'^[\w\s\.\-\*\/\,]+$'),
            'accept-language': re.compile(r'^[\w\s\.\-\*\/\,\=\:\;]+$'),
            'cache-control': re.compile(r'^[\w\s\.\-\=\;]+$'),
            'connection': re.compile(r'^[\w\s\.\-]+$'),
            'content-length': re.compile(r'^[\d]+$'),
            'cookie': re.compile(r'^[\w\s\=\%\+\&\;\:\@\$\,\.\-\_\*\/\?\!\~\#]+$'),
            'origin': re.compile(r'^(http|https)://[\w\.\-\?\=\&\/\:]+$'),
            'pragma': re.compile(r'^[\w\s\.\-]+$'),
            'referer': re.compile(r'^(http|https)://[\w\.\-\?\=\&\/\:\%\#\~\!\*\+\@]+$'),
            'user-agent': re.compile(r'^[\w\s\.\-\*\/\,\(\)\=\+\;\:\@\$\,\.\-\_\~\#]+$'),
            'x-cookie-token': re.compile(r'^\w+$'),
            'x-http-token': re.compile(r'^\w+$'),
            'X-KL-Ajax-Request': re.compile(r'^\w+$'),
            'X-Requested-With': re.compile(r'^\w+$')
        }
    from flask import request
    headers = request.headers
    skeys = headers_filter_rules.keys()

    for k in skeys:
        v = headers.get(k, None)
        if not v: continue
        if not headers_filter_rules[k].match(v):
            return False
    return True


def trim(data):
    """
    @去除所有空格
    """
    return data.replace(' ', '').strip()


def get_os(_os='windows'):
    """
    @验证系统版本
    """
    src_os = 'windows'
    if os.path.exists('/www/server/panel'): src_os = 'linux'
    if src_os == _os: return True
    return False


def get_file_list(path, flist):
    """
    递归获取目录所有文件列表
    @path 目录路径
    @flist 返回文件列表
    """
    if os.path.exists(path):
        files = os.listdir(path)
        flist.append(path)
        for file in files:
            if os.path.isdir(path + '/' + file):
                get_file_list(path + '/' + file, flist)
            else:
                flist.append(path + '/' + file)


def writeFile2(filename, s_body, mode='w+'):
    """
    写入字节文件内容
    @filename 文件名
    @s_body 欲写入的内容

    """
    try:
        fp = open(filename, mode);
        fp.write(s_body)
        fp.close()
        return True
    except:
        return False


def check_obj_upgrade(_obj, filename=None):
    '''
        @name 检查指定模块是否修改
        @author hwliang
        @param <string>文件名
        @param <object>模块对象
        @return void
    '''

    # 引用缓存
    try:
        from BTPanel import cache
    except:
        return

    # 是否传递文件名？
    if not filename:
        filename = _obj.__file__

    # 获取文件修改时间
    skey = "obj_up_{}".format(md5(filename))
    mtime = os.path.getmtime(filename)  # 当前
    old_mtime = cache.get(skey)  # 旧的

    # 直接设置当前修改时间
    if not old_mtime:
        cache.set(skey, mtime)
        return

    # 检查是否修改
    if old_mtime == mtime:
        return

    # 重新加载模块
    import importlib
    importlib.reload(_obj)
    cache.set(skey, mtime)


def version_to_tuple(version):
    '''
        @name 将版本号转为元组
        @version 字符串版本号
        @return 元组版本号
    '''
    if not version:
        return ()
    if not isinstance(version, str):
        return version
    version = re.sub(r"[^\.\d]+", "", version)
    version = version.split('.')
    version = tuple(map(int, version))
    return version


def set_search_history(mod_name, key, val):
    """
    @保存搜索历史
    @mod_name 模块名称
    @key 关键字
    @val string 搜索内容
    """
    if not val:
        return False
    val = val.strip()
    val = val.replace("/_", "_")
    max = 10
    p_file = get_panel_path()
    m_file = p_file + '/data/search.limit'
    d_file = p_file + '/data/search.json'
    try:
        sdata = int(readFile(m_file))
        if sdata: max = sdata
    except:
        pass

    result = {}
    try:
        result = json.loads(readFile(d_file))
    except:
        pass

    if result.get(mod_name) is None:
        result[mod_name] = {}
    if result[mod_name].get(key) is None:
        result[mod_name][key] = []

    result[mod_name][key] = sorted(result[mod_name][key], key=lambda x: x['time'], reverse=True)

    result[mod_name][key] = [info for info in result[mod_name][key] if info["val"] != val]
    result[mod_name][key].insert(0, {'val': val, 'time': int(time.time())})

    if len(result[mod_name][key]) > max:
        result[mod_name][key] = result[mod_name][key][:max]

    writeFile(d_file, json.dumps(result))
    return True


def get_search_history(mod_name, key):
    """
    @获取搜索历史
    @mod_name string 模块名称
    @key string 关键字
    """

    result = []
    d_file = get_panel_path() + '/data/search.json'
    try:
        result = json.loads(readFile(d_file))[mod_name][key]
    except:
        pass

    result = sorted(result, key=lambda x: x['time'], reverse=True)

    return result


def set_dir_history(mod_name, key, val):
    """
    @设置目录打开历史
    @mod_name string 模块名称
    @key string 函数名
    @val string 路径
    """
    if not val:  return False

    max = 10
    result = {}
    d_file = get_panel_path() + '/data/dir_history.json'
    try:
        result = json.loads(readFile(d_file))
    except:
        pass

    if not mod_name in result: result[mod_name] = {}
    if not key in result[mod_name]:  result[mod_name][key] = []

    data = result[mod_name][key]
    for info in data:
        if val.find(info['val']) >= 0:
            if time.time() - info['time'] < 15:
                data.remove(info)

    data.append({'val': val, 'time': int(time.time())})
    result[mod_name][key] = data[0:max]
    writeFile(d_file, json.dumps(result))
    return True


def get_dir_history(mod_name, key):
    """
    @获取目录打开历史
    @mod_name string 模块名称
    @key string 关键字
    """
    result = []
    d_file = get_panel_path() + '/data/dir_history.json'
    try:
        result = json.loads(readFile(d_file))[mod_name][key]
    except:
        pass
    return result


def get_run_pip():
    pass


def install_pip(shell):
    """
    @name 安装pip模块
    @author cjxin
    @param shell<string> 安装命令
    """
    if get_os('windows'):
        os.system(get_run_pip(shell.replace('pip', '[PIP]')))
    else:
        os.system(shell.replace('pip', 'btpip'))


def is_domain(domain):
    """
    @验证是否域名
    """
    reg = "^([\w\-\*]{1,100}\.){1,10}([\w\-]{1,24}|[\w\-]{1,24}\.[\w\-]{1,24})$";
    if re.match(reg, domain): return True
    return False


def init_msg(module):
    """
    初始化消息通道
    @module 消息通道模块名称
    """
    res = _init_msg_compatible(module)
    if res:
        return res
    module = module.strip()
    if module == "":
        return None
    import os, sys
    if not os.path.exists('class/msg'): os.makedirs('class/msg')
    panelPath = get_panel_path()

    # 查找标识信息中是否使用
    tip_file = '{}/data/msg_not_use.tip'.format(panelPath)
    not_use_tip = readFile(tip_file)
    if not_use_tip:
        try:
            not_use_tip = json.loads(not_use_tip)
        except json.JSONDecodeError:
            pass
        if module in not_use_tip:
            return False

    if "{}/class/msg".format(panelPath) not in sys.path:
        sys.path.insert(0, "{}/class/msg".format(panelPath))

    if module in ("dingding", "feishu", "mail", "sms", "weixin", "wx_account"):
        sfile = 'class/msg/{}_msg.py'.format(module)
        if not os.path.exists(sfile):
            return False
        msg_main = __import__('{}_msg'.format(module))
        is_hook = False
    else:
        sfile = 'class/msg/web_hook_msg.py'
        if not os.path.exists(sfile):
            return False
        msg_main = __import__('web_hook_msg')
        is_hook = True
    try:
        mod_reload(msg_main)
    except:
        pass
    if is_hook:
        if module == "web_hook":
            module = None
        msg_cls_obj = getattr(msg_main, "web_hook_msg")(module)
        return msg_cls_obj
    return eval('msg_main.{}_msg()'.format(module))


def _init_msg_compatible(module):
    if "/www/server/panel" not in sys.path:
        sys.path.insert(0, "/www/server/panel")

    from mod.base.msg import compatible
    return compatible.get_sender_by_id(module)


def push_argv(msg):
    """
    @处理短信参数，否则会被拦截
    """
    if is_ipv4(msg):
        tmp1 = msg.split('.')
        msg = '{}.***.***.{}'.format(tmp1[0], tmp1[3])
    else:
        if is_domain(msg):
            msg = msg.replace('.', '_')
    return msg


def check_sms_argv(data):
    """
    @批量处理短信参数，否则会被拦截
    """
    for key in data:
        val = data[key]
        if type(val) == str:
            data[key] = push_argv(val)
    return data


"""
@获取推送ip
"""


def get_push_address():
    ip = push_argv(GetLocalIp())
    return ip


def get_ips_area(ips):
    '''
    @name 获取ip地址所在地
    @author cjxin
    @param ips<list>
    @return list
    '''
    import PluginLoader

    args = dict_obj()
    args.model_index = 'safe'
    args.ips = ips

    res = PluginLoader.module_run("ips", "get_ip_area", args)
    return res


def return_area(result, key):
    """
    @name 格式化返回带IP归属地的数组
    @param result<list> 数据数组
    @param key<str> ip所在字段
    @return list
    """
    tmps = []
    for data in result:
        data['area'] = ''
        tmps.append(data[key])

    res = get_ips_area(tmps)
    if 'status' in res: return result

    for data in result:
        if data[key] in res:
            data['area'] = res[data[key]]
    return result


def get_network_ip():
    """
    @name 获取本机ip
    @return string
    """

    import socket
    s = None
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        return ip
    except Exception:
        return '127.0.0.1'
    finally:
        if s is not None:
            s.close()


def get_server_ip():
    """
    @获取服务器外网ip
    """

    user_file = '{}/data/userInfo.json'.format(get_panel_path())
    if os.path.exists(user_file):
        try:
            userTmp = json.loads(readFile(user_file))
            return userTmp['address']
        except:
            pass

    return GetLocalIp()


def get_push_info(title, slist=[]):
    """
    @name 获取推送信息
    @param title<str> 推送标题
    @param slist<list> 推送追加的列表
            如：slist = ['>发送内容:xxx']
    @return dict
    """
    data = {}
    data['title'] = title
    data['ip'] = get_server_ip()

    data['local_ip'] = get_network_ip()
    data['time'] = format_date()
    data['server_name'] = GetConfigValue('title')

    dlist = [
        "#### {}".format(data['title']),
        ">服务器：" + data['server_name'],
        ">IP地址：{}(外) {}(内)".format(data['ip'], data['local_ip']),
        ">发送时间：" + data['time']
    ]
    dlist.extend(slist)
    msg = "\n\n".join(dlist)
    data['msg'] = msg
    data['list'] = dlist
    return data


def write_push_log(module, msg, res):
    """
    @name 写推送日志
    @module string 模块名称
    @msg string 消息内容
    @res dict 推送结果
    """
    user = ''
    for key in res:
        status = '<span style="color:#20a53a;">成功</span>'
        if res[key] == 0: status = '<span style="color:red;">失败</span>'
        user += '【 {}：{} 】 '.format(key, status)

    if not user: user = '[ 默认 ] '
    try:
        msg_obj = init_msg(module)
        if msg_obj: module = msg_obj.get_version_info(None)['title']
    except:
        pass

    log = '标题：【{}】，通知方式：【{}】，收件人：{}'.format(xsssec(msg), module, user)
    WriteLog('告警通知', log)
    return True


def push_msg(module, data):
    """
    @name 推送消息
    @param module<str> 模块名称
    @param msg<str> 消息内容
    @return dict
    """
    msg_obj = init_msg(module)
    if not msg_obj:
        returnMsg(False, '模块{}不存在!'.format(module))

    res = msg_obj.push_data(data)
    return res


def check_chinese(data):
    """
    @name 判断字符串是否包含中文
    """
    if re.search('[\u4e00-\u9fa5]', data):
        return True
    return False


def is_ssl():
    '''
        @name 是否开启SSL
        @author hwliang
        @return bool
    '''
    return os.path.exists(get_panel_path() + '/data/ssl.pl')


def get_cookie(key, default=None):
    '''
        @name 获取指定Cookie值
        @author hwliang
        @param key<str> Cookie键
        @param default<str> 默认值
        @return str
    '''
    from flask import request
    return request.cookies.get(key, default)


def get_csrf_cookie_token_key():
    '''
        @name 获取CSRF Cookie Key
        @author hwliang
        @return string
    '''
    if is_ssl():
        token_key = 'request_token'
    else:
        token_key = 'request_token'
    return token_key


def get_csrf_cookie_token_value():
    '''
        @name 获取CSRF Cookie Value
        @author hwliang
        @return string
    '''
    token_key = get_csrf_cookie_token_key()
    return get_cookie(token_key)


def get_csrf_html_token_key():
    '''
        @name 获取CSRF HTML Key
        @author hwliang
        @return string
    '''
    if is_ssl():
        token_key = 'request_token_head'
    else:
        token_key = 'request_token_head'
    return token_key


def get_csrf_html_token_value():
    '''
        @name 获取CSRF HTML Value
        @author hwliang
        @return string
    '''
    token_key = get_csrf_html_token_key()
    return get_cookie(token_key)


def get_csrf_sess_html_token_value():
    '''
        @name 从SESSION获取CSRF HTML value
        @author hwliang
        @return string
    '''
    from flask import session
    return session.get(get_csrf_html_token_key(), "")


def get_csrf_sess_cookie_token_value():
    '''
        @name 从SESSION获取CSRF Cookie value
        @author hwliang
        @return string
    '''
    from flask import session
    return session.get(get_csrf_cookie_token_key(), "")


def get_sys_install_bin():
    '''
        @name 获取系统包管理器命令
        @author hwliang
        @return string
    '''
    install_bins = ['/usr/bin/yum', '/usr/bin/apt-get', '/usr/bin/dnf']
    for bin in install_bins:
        if os.path.exists(bin):
            return bin
    return ''


def get_firewall_status():
    '''
        @name 获取系统防火墙状态
        @author hwliang
        @return int 0.关闭 1.开启 -1.未安装
    '''
    import psutil
    firewall_files = {'/usr/sbin/firewalld': "pid", '/usr/bin/firewalld': "pid", '/usr/sbin/ufw': "ufw status verbose|grep -E '(Status: active|激活)'",
                      '/sbin/ufw': "/sbin/ufw status |grep -E '(Status: active|激活)'", '/usr/sbin/iptables': "service iptables status|grep 'Chain INPUT'"}
    for f in firewall_files.keys():
        if not os.path.exists(f): continue
        _cmd = firewall_files[f]
        if _cmd != "pid":
            res = ExecShell(_cmd)
            if res[0].strip():
                return 1
            else:
                return 0
        for pid in psutil.pids():
            try:
                p = psutil.Process(pid)
                if f in p.cmdline():
                    return 1
            except:
                pass
        return 0
    return -1


def get_panel_port():
    '''
        @name 获取面板端口
        @author hwliang
        @return int
    '''
    port_file = '{}/data/port.pl'.format(get_panel_path())
    if not os.path.exists(port_file):
        return 8888
    try:
        return int(readFile(port_file))
    except:
        return 8888


def install_sys_firewall():
    '''
        @name 安装系统防火墙
        @author hwliang
        @return bool
    '''
    if get_firewall_status() != -1: return True

    install_bin = get_sys_install_bin()
    if not install_bin: return False
    if install_bin.find('apt-get') != -1:
        ExecShell("{} install -y ufw".format(install_bin))
        if get_firewall_status() != -1:
            _cmd = '''ufw allow 20/tcp
ufw allow 21/tcp
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow ${panelPort}/tcp
ufw allow ${sshPort}/tcp
ufw allow 39000:40000/tcp
ufw_status=`ufw status`
echo y|ufw enable
ufw default deny
ufw reload
'''.format(panelPort=get_panel_port(), sshPort=get_ssh_port())
            ExecShell(_cmd)
    elif install_bin.find('yum') != -1 or install_bin.find('dnf') != -1:
        ExecShell("{} install -y firewalld".format(install_bin))
        if get_firewall_status() != -1:
            _cmd = '''systemctl enable firewalld
			systemctl start firewalld
			firewall-cmd --set-default-zone=public > /dev/null 2>&1
			firewall-cmd --permanent --zone=public --add-port=20/tcp > /dev/null 2>&1
			firewall-cmd --permanent --zone=public --add-port=21/tcp > /dev/null 2>&1
			firewall-cmd --permanent --zone=public --add-port=22/tcp > /dev/null 2>&1
			firewall-cmd --permanent --zone=public --add-port=80/tcp > /dev/null 2>&1
            firewall-cmd --permanent --zone=public --add-port=443/tcp > /dev/null 2>&1
			firewall-cmd --permanent --zone=public --add-port={panelPort}/tcp > /dev/null 2>&1
			firewall-cmd --permanent --zone=public --add-port={sshPort}/tcp > /dev/null 2>&1
			firewall-cmd --permanent --zone=public --add-port=39000-40000/tcp > /dev/null 2>&1
			firewall-cmd --reload
'''.format(panelPort=get_panel_port(), sshPort=get_ssh_port())
            ExecShell(_cmd)

    return False


def check_firewall_rule(port):
    '''
    @name 检测防火墙是否已经添加规则
    @author cjxin
    @param port int 端口号
    '''

    args = dict_obj()
    args.model_index = 'safe'
    args.port = port

    import PluginLoader
    res = PluginLoader.module_run("firewall", "check_firewall_rule", args)
    return res


def add_firewall_rule(port, protocol='tcp', types='accept', address='0.0.0.0/0', brief=None):
    """
    @name 添加防火墙规则
    @author cjxin
    @param port int 端口号
    @param protocol string 协议类型 tcp udp
    @param types string 添加类型 accept reject
    @param address string 地址
    @param brief string 描述
    """

    args = dict_obj()
    args.model_index = 'safe'
    args.port = port
    args.protocol = protocol
    args.types = types
    args.address = address
    args.brief = brief
    if not brief: args.brief = str(port)

    import PluginLoader
    res = PluginLoader.module_run("firewall", "create_rules", args)
    return res


def del_firewall_rule(port, protocol='tcp', types='accept', address='0.0.0.0/0'):
    '''
    @name 删除防火墙规则
    @author cjxin
    @param port int 端口号
    @param protocol str 协议
    @param types str 类型
    @param address str 地址
    '''

    args = dict_obj()
    args.model_index = 'safe'
    args.port = port
    args.protocol = protocol
    args.types = types
    args.address = address
    import PluginLoader
    res = PluginLoader.module_run("firewall", "remove_rules", args)
    return res


def is_aarch():
    '''
        @name 是否是arm架构
        @author hwliang
        @return bool
    '''
    uname = None
    if hasattr(os, 'uname'): uname = os.uname()
    aarch_list = ['aarch64', 'aarch']
    try:
        return uname.machine in aarch_list
    except:
        if uname:
            return uname[-1] in aarch_list
    return False


def is_process_exists_by_cmdline(_cmd):
    '''
        @name 根据命令行参数查找进程是否存在
        @author hwliang
        @param _cmd 命令行
        @return bool
    '''
    if isinstance(_cmd, str):
        _cmd = [_cmd]
    if not isinstance(_cmd, list):
        return False
    for pid in psutil.pids():
        try:
            p = psutil.Process(pid)
            cmd_line = p.cmdline()
            for _c in _cmd:
                if _c in cmd_line:
                    return True
        except:
            continue
    return False


def is_process_exists_by_exe(_exe):
    '''
        @name 根据执行文件路径查找进程是否存在
        @author hwliang
        @param _exe 命令行
        @return bool
    '''
    if isinstance(_exe, str):
        _exe = [_exe]
    if not isinstance(_exe, list):
        return False

    try:
        for _pid_num in psutil.pids():
            try:
                process = psutil.Process(_pid_num)
                _exe_bin = process.exe()
                for _e in _exe:
                    if _exe_bin.find(_e) != -1: return True
            except:
                continue
    except:
        return False
    return False


def is_process_exists_by_name(_name):
    '''
        @name 根据进程名查找进程是否存在
        @author hwliang
        @param _name 命令行
        @return bool
    '''
    if isinstance(_name, str):
        _name = [_name]
    if not isinstance(_name, list):
        return False
    for pid in psutil.pids():
        try:
            p = psutil.Process(pid)
            name = p.name()
            for _n in _name:
                if name == _n: return True
        except:
            continue
    return False


def is_mysql_process_exists():
    '''
        @name 检查mysql进程是否存在
        @author hwliang
        @return bool
    '''
    _exe = ['server/mysql/bin/mysqld_safe', 'server/mysql/bin/mariadbd', 'server/mysql/bin/mysqld']
    return is_process_exists_by_exe(_exe)


def is_redis_process_exists():
    '''
        @name 检查redis进程是否存在
        @author hwliang
        @return bool
    '''
    _exe = ['server/redis/src/redis-server']
    return is_process_exists_by_exe(_exe)


def is_pure_ftpd_process_exists():
    '''
        @name 检查pure-ftpd进程是否存在
        @author hwliang
        @return bool
    '''
    _exe = ['server/pure-ftpd/sbin/pure-ftpd']
    return is_process_exists_by_exe(_exe)


def is_php_fpm_process_exists(name):
    '''
        @name 检查php-fpm进程是否存在
        @author hwliang
        @return bool
    '''
    _php_version = name.split('-')[-1]
    _exe = ['server/php/{}/sbin/php-fpm'.format(_php_version)]
    return is_process_exists_by_exe(_exe)


def is_nginx_process_exists():
    '''
        @name 检查nginx进程是否存在
        @author hwliang
        @return bool
    '''
    _exe = ('server/nginx/sbin/nginx', 'server/nginx/nginx/sbin/nginx')
    for i in _exe:
        result = is_process_exists_by_exe(i)
        if result: return result
    return False


def is_httpd_process_exists():
    '''
        @name 检查httpd进程是否存在
        @author hwliang
        @return bool
    '''
    _exe = ['server/apache/bin/httpd']
    return is_process_exists_by_exe(_exe)


def is_memcached_process_exists():
    '''
        @name 检查memcached进程是否存在
        @author hwliang
        @return bool
    '''
    _exe = ['/usr/local/memcached/bin/memcached']
    return is_process_exists_by_exe(_exe)


def is_mongodb_process_exists():
    '''
        @name 检查mongodb进程是否存在
        @author hwliang
        @return bool
    '''
    _exe = ['server/mongodb/bin/mongod']
    return is_process_exists_by_exe(_exe)


def check_auth_ip():
    """
    @name 检测api和www的服务器ip是否一致
    @auther cjxin 2022-09-13
    @return bool
    """
    import http_requests
    result = {'www': '', 'api': ''}
    res = http_requests.post('https://www.bt.cn/api/getIpAddress', data={}, timeout=5, headers={})
    if res.status_code == 200:
        result['www'] = res.text

    res1 = http_requests.post('https://api.bt.cn/api/getIpAddress', data={}, timeout=5, headers={})
    if res1.status_code == 200:
        result['api'] = res1.text

    return result


def set_func(key, count=0):
    """
    设置指定key的操作时间
    @key 面板访问函数
    """
    path = 'data/func.json'
    data = {}
    try:
        data = json.loads(readFile(path))
    except:
        pass
    if not key in data:
        data[key] = {}
        data[key]['time'] = 0
        data[key]['count'] = 0
    data[key]['time'] = int(time.time())

    if count > 0:
        data[key]['count'] = count
    else:
        data[key]['count'] += 1
    writeFile(path, json.dumps(data))


def get_func(key):
    """
    获取指定功能的操作时间
    @key 面板函数
    """
    path = 'data/func.json'
    ret = {}
    ret['count'] = 0
    ret['time'] = 0
    if not os.path.exists(path): return ret
    data = {}
    try:
        data = json.loads(readFile(path))
    except:
        pass
    if not key in data: return ret
    return data[key]


def set_cache_func(key, info):
    """
    设置指定key的操作时间
    @key 缓存的key函数
    """
    data = {}
    path = '{}/data/cache_func.json'.format(get_panel_path())

    try:
        data = json.loads(readFile(path))
    except:
        pass
    if not key in data: data[key] = {}

    data[key]['time'] = int(time.time())
    data[key]['data'] = info

    writeFile(path, json.dumps(data))


def get_cache_func(key):
    """
    获取指定功能的操作时间
    @key 缓存的key函数
    """

    ret = {}
    data = {}
    ret['data'] = ''
    ret['time'] = 0
    path = '{}/data/cache_func.json'.format(get_panel_path())
    if not os.path.exists(path):
        return ret
    try:
        data = json.loads(readFile(path))
    except:
        pass
    if not key in data: return ret
    return data[key]


def set_split_logs(path, status=1, info=None):
    """
    @name 添加日志切割
    @path 日志路径，
    @data dict
    {
        'type':'day/size'
        'limit': 180,保留份数
        'size': 日志超过多少进行切割,type=size时生效
        'callback': 回调命令,部分日志切割后需要重启服务
    }
    """

    data = {}
    sfile = '{}/data/cutting_log.json'.format(get_panel_path())
    if os.path.exists(sfile):
        try:
            data = json.loads(readFile(sfile))
        except:
            pass

    if path in data:
        del data[path]

    if status:
        if not info:
            return False
        if not 'type' in info or not 'limit' in info:
            return False
        data[path] = info
    writeFile(sfile, json.dumps(data))

    # 计划任务切割
    echo = md5(md5('set_split_logs'))
    find = M('crontab').where('echo=?', (echo,)).find()

    try:
        import crontab
        args_obj = dict_obj()

        if not find:
            cronPath = GetConfigValue('setup_path') + '/cron/' + echo
            shell = '{} -u /www/server/panel/script/logSplit.py'.format(sys.executable)
            writeFile(cronPath, shell)

            args_obj.id = M('crontab').add('name,type,where1,where_hour,where_minute,echo,addtime,status,save,backupTo,sType,sName,sBody,urladdress',
                                           ("[删除]切割日志文件", 'minute-n', '10', '0', '0', echo, time.strftime('%Y-%m-%d %X', time.localtime()), 0, '', 'localhost', 'toShell', '', shell, ''))
            crontab.crontab().set_cron_status(args_obj)
        else:
            cron_path = get_cron_path()
            if os.path.exists(cron_path):
                cron_s = readFile(cron_path)
                if cron_s.find(echo) == -1:
                    M('crontab').where('echo=?', (echo,)).setField('status', 0)
                    args_obj.id = find['id']
                    crontab.crontab().set_cron_status(args_obj)
        return True
    except:
        pass

    return False


def get_admin_path():
    '''
        @name 取安全入口
        @author hwliang
        @return string
    '''
    login_path = '/login'
    path = '{}/data/admin_path.pl'.format(get_panel_path())
    if not os.path.exists(path): return login_path
    admin_path = readFile(path)
    if not admin_path: return login_path
    admin_path = admin_path.strip()
    if admin_path in ['', '/']:
        return login_path
    if admin_path[-1] == '/': admin_path = admin_path[:-1]
    return admin_path


def get_improvement():
    '''
        @name 获取用户体验改进计划状态
        @author hwliang
        @return bool
    '''
    tip_file = '{}/data/improvement.pl'.format(get_panel_path())
    tip_file_set = '{}/data/is_set_improvement.pl'.format(get_panel_path())
    if not os.path.exists(tip_file_set):
        return True
    return os.path.exists(tip_file)


def is_spider():
    '''
        @name 判断是否为爬虫
        @return bool
    '''
    from BTPanel import request
    import panelDefense
    p = panelDefense.bot_safe()
    return not p.spider(request.headers.get('User-Agent'), request.remote_addr)


# def get_rsa_public_key_file():
#     '''
#         @name 获取RSA公钥文件路径
#         @author hwliang
#         @return str
#     '''
#     return '{}/data/rsa_public_key.pem'.format(get_panel_path())

# def get_rsa_private_key_file():
#     '''
#         @name 获取RSA私钥文件路径
#         @author hwliang
#         @return str
#     '''
#     return '{}/data/rsa_private_key.pem'.format(get_panel_path())


def get_rsa_public_key():
    '''
        @name 获取RSA公钥内容
        @author hwliang
        @return str
    '''
    from BTPanel import session
    pub_key = 'rsa_public_key'
    public_key = session.get(pub_key)
    if not public_key:
        create_rsa_key()
        public_key = session.get(pub_key)
    return public_key

    # path = get_rsa_public_key_file()
    # if not os.path.exists(path): create_rsa_key()
    # if not os.path.exists(path): return ''
    # return readFile(path)


def get_rsa_private_key():
    '''
        @name 获取RSA私钥内容
        @author hwliang
        @return str
    '''
    from BTPanel import session
    prv_key = 'rsa_private_key'
    private_key = session.get(prv_key)
    if not private_key:
        create_rsa_key()
        private_key = session.get(prv_key)
    return private_key


def create_rsa_key():
    '''
        @name 创建RSA密钥
        @author hwliang
        @return bool
    '''
    try:
        # private_key_file = get_rsa_private_key_file()
        # public_key_file = get_rsa_public_key_file()
        # if os.path.exists(private_key_file) and os.path.exists(public_key_file): return True
        from BTPanel import session
        pub_key = 'rsa_public_key'
        prv_key = 'rsa_private_key'
        if pub_key in session and prv_key in session:
            return True
        try:
            from Crypto.PublicKey import RSA
            key = RSA.generate(1024)
            private_key = key.exportKey("PEM")
            public_key = key.publickey().exportKey("PEM")
        except:
            is_re_install = '{}/data/pycryptodome_re_install.pl'.format(get_panel_path())
            if not os.path.exists(is_re_install):
                os.system("nohup btpip install pycryptodome -I &> /dev/null &")
                writeFile(is_re_install, 'True')

            priv_pem = '/tmp/private.pem'
            pub_pem = '/tmp/public.pem'
            ExecShell("openssl genrsa -out {} 1024".format(priv_pem))
            ExecShell("openssl rsa -pubout -in {} -out {}".format(priv_pem, pub_pem))
            if not os.path.exists(priv_pem) or not os.path.exists(pub_pem):
                return False

            private_key = readFile(priv_pem, 'rb')
            public_key = readFile(pub_pem, 'rb')

            if os.path.exists(priv_pem): os.remove(priv_pem)
            if os.path.exists(pub_pem): os.remove(pub_pem)

        session[pub_key] = public_key.decode('utf-8').replace("\n", "")
        session[prv_key] = private_key.decode('utf-8')

        # writeFile(private_key_file,private_key,'wb+')
        # writeFile(public_key_file,public_key,'wb+')
        return True
    except:
        return False


def rsa_encrypt(data):
    '''
        @name RSA加密数据
        @param data str 要加密的数据
        @return str
    '''
    # 分片长度 1024 / 8 - 11 = 117
    split_length = 117
    try:
        from Crypto.PublicKey import RSA
        from Crypto.Cipher import PKCS1_v1_5 as Cipher_pkcs

        # 初始化RSA加密对象
        public_key = get_rsa_public_key()
        cipher_public = Cipher_pkcs.new(RSA.importKey(public_key))

        # 分片加密
        data = data.encode('utf-8')
        encrypted_arr = []
        for i in range(0, len(data), split_length):
            d = data[i:i + split_length]
            encrypted_data = cipher_public.encrypt(d)
            encrypted_base64 = base64.b64encode(encrypted_data).decode()
            encrypted_arr.append(encrypted_base64)

        # 用换行符拼接
        return "\n".join(encrypted_arr)
    except:
        return ''


def rsa_decrypt(data):
    '''
        @name RSA解密数据
        @param data str 要解密的数据
        @return str
    '''
    try:
        from Crypto.PublicKey import RSA
        from Crypto.Cipher import PKCS1_v1_5 as Cipher_pkcs

        # 初始化RSA解密对象
        private_key = get_rsa_private_key()
        cipher_private = Cipher_pkcs.new(RSA.importKey(private_key))

        # 分片解密
        decrypted_str = b""
        for d in data.split("\n"):
            if not d: continue
            res = base64.b64decode(d)
            if not res: continue
            decrypted_data = cipher_private.decrypt(res, None)
            decrypted_str += decrypted_data
        return decrypted_str.decode('utf-8')
    except:
        return ''


def rsa_encrypt_for_private_key(data):
    '''
        @name RSA私钥加密数据
        @author hwliang
        @param data str 要加密的数据
        @return str
    '''
    # 分片长度 1024 / 8 - 11 = 117
    split_length = 117
    try:
        from Crypto.PublicKey import RSA
        from Crypto.Cipher import PKCS1_v1_5 as Cipher_pkcs

        # 初始化RSA加密对象
        private_key = get_rsa_private_key()
        cipher_private = Cipher_pkcs.new(RSA.importKey(private_key))

        # 分片加密
        data = data.encode('utf-8')
        encrypted_arr = []
        for i in range(0, len(data), split_length):
            d = data[i:i + split_length]
            encrypted_data = cipher_private.encrypt(d)
            encrypted_base64 = base64.b64encode(encrypted_data).decode()
            encrypted_arr.append(encrypted_base64)

        # 用换行符拼接
        return "\n".join(encrypted_arr)
    except:
        return ''


def get_client_hash():
    '''
        @name 获取客户端HASH
        @author hwliang
        @return str
    '''
    from flask import session, request
    is_tmp_login = session.get('tmp_login')  # 是否临时登录
    is_session_safe_mode = session.get('session_safe_mode')  # 是否安全模式
    if is_tmp_login or is_session_safe_mode:
        client_hash = md5(request.remote_addr)
    else:
        skey = 'client_ips'
        ckey = 'client_sync_count'
        client_ips = session.get(skey, [])
        client_sync_count = session.get(ckey, 0)

        # 是否唯一IP
        if len(client_ips) <= 1:
            # 唯一IP连续访问次数超过100次，使用IP+UA生成HASH
            r_max = 101
            if client_sync_count >= r_max - 1:
                client_hash = md5(request.remote_addr)
                if client_sync_count < r_max:
                    session['client_hash'] = client_hash
                    client_sync_count += 1
                    session[ckey] = client_sync_count
                return client_hash
            # 记录IP
            if not request.remote_addr in client_ips:
                client_ips.append(request.remote_addr)
                session[skey] = client_ips

            # 记录访问次数
            client_sync_count += 1
            session[ckey] = client_sync_count

        # 非唯一IP，使用UA生成HASH
        client_hash = md5('')

    return client_hash


def check_client_hash():
    '''
        @name 验证客户端HASH
        @author hwliang
        @return bool
    '''
    from BTPanel import session, request

    # 如果未开启SSL，不验证
    if is_ssl(): return True

    skey = 'client_hash'
    client_hash = get_client_hash()
    if not skey in session:
        session[skey] = client_hash
        return True

    if session[skey] != client_hash:
        # 如果登录时间存在，且登录时间小于2分钟，自动调整为普通模式，不强制退出登录
        login_time = session.get('login_time')
        if login_time:
            max_timeout = 120
            if time.time() - login_time < max_timeout:
                session['session_safe_mode'] = False
                session[skey] = get_client_hash()
                return True

        # 强制退出登录
        WriteLog('用户登录', '客户端HASH验证失败，已强制退出登录，建议开启面板SSL来关闭IP-HASH验证!')
        return False
    return True


def shell_quote(cmd):
    '''
        @name shell转义
        @author hwliang
        @param cmd str 要转义的命令
        @return str
    '''
    if not cmd: return ''
    if isinstance(cmd, bytes): cmd = cmd.decode('utf-8')
    if not isinstance(cmd, str): return cmd
    try:
        import shlex
        return shlex.quote(cmd)
    except:
        try:
            import pipes
            return pipes.quote(cmd)
        except:
            return cmd


def get_div(div):
    sql = M('sqlite_master')
    if not sql.where('type=? AND name=? AND sql LIKE ?', ('table', 'div_list', '%div%')).count():
        sql_str = '''CREATE TABLE IF NOT EXISTS `div_list` (
`id` INTEGER PRIMARY KEY AUTOINCREMENT,
`div` TEXT
)'''
        sql.execute(sql_str)
    my_div = sql.table('div_list').where('id=1', ()).getField('div')
    if not my_div:
        sql.table('div_list').insert({'div': div})
        my_div = div
    return my_div


def set_tasks_run(data):
    '''
        @name 设置运行时间
        @param data dict 数据        @param data.type int 类型 1:面板 2：插件
        @param data.time int 执行时间（必传）
        @param data.name str 插件名称、模块名称（必传）
        @param data.title str 插件中文名（必传）
        @param data.fun str 执行方法（必传）
        @param data.args dict 参数
        @param data.model_index  模块索引

    '''
    spath = '{}/data/tasks'.format(get_panel_path())
    if not os.path.exists(spath): os.makedirs(spath, 384)

    task_file = '{}/{}'.format(spath, md5(str(time.time())))
    writeFile(task_file, json.dumps(data))
    return returnMsg(True, task_file)


def Get_ip_info(get_speed=False, get_user=True):
    '''
    获取bt官网ip归属地列表
    @author wzz <wzz@bt.cn>
    @return: list[dict{}]
    '''
    host_list = json.loads(readFile("config/hosts_dict.json"))
    print("host_list: ", host_list)

    # 推荐，一般，较差，不推荐，不测速时，ipv6，用户服务器IP
    level = (1, 2, 3, 4, 5, 6, 0)
    user_server_ipaddress = []
    if get_user:
        user_server_ipaddress = get_user_server_ipaddress(host_list, level)
    bt_host = get_bt_hosts(get_speed, host_list, level)
    ips_result = user_server_ipaddress + bt_host
    if ips_result: return ips_result


def get_user_server_ipaddress(host_list, level):
    '''
    获取服务器公网ip归属地信息
    @param host_list: host列表
    @param level: 等级元组
    @return:
    '''
    ips_result = []
    headers = {"host": "www.bt.cn"}
    for host in host_list:
        try:
            new_url = "https://{}/Api/getIpAddress".format(host["ip"])
            m_str = HttpGet(new_url, 1, headers=headers)
            ipaddress = re.search(r"^\d{1,3}.\d{1,3}.\d{1,3}.\d{1,3}$", m_str).group(0)
            s_ip_info = get_free_ip_info("{}".format(ipaddress))
            if "ip" in s_ip_info.keys():
                s_ip_info["info"] = "本服务器公网IP归属地信息"
                s_ip_info["level"] = level[-1]
                ips_result.append(s_ip_info)
                return ips_result
        except:
            continue
    return  ips_result


def get_bt_hosts(get_speed, host_list, level):
    '''
    获取bt官网ip归属地列表
    @param get_speed: 是否测速
    @param host_list: 传host列表
    @param level: 传等级元组
    @return:
    '''
    ips_result = []

    for ip in host_list:
        ipv6 = {
            "continent": "",
            "country": "",
            "province": "",
            "city": "ipv6 地址",
            "region": "",
            "carrier": "",
            "division": "",
            "en_country": "",
            "en_short_code": "",
            "longitude": "",
            "latitude": "",
            "info": "该节点为ipv6地址,若服务器无ipv6请勿选择!",
            "ip": "",
            "level": None
        }
        try:
            # 获取节点响应延迟
            if get_speed: n_net, n_ping = get_timeout("https://{}".format(ip["ip"]) + ':80/net_test', 1)
            if not is_ipv4(ip["ip"]):
                ipv6['ip'] = ip["ip"]
                # ipv6地址默认一般推荐
                ipv6['level'] = level[-2]
                if get_speed: ipv6['speed'] = ""
                ips_result.append(ipv6)
                continue
            ip_result = get_free_ip_info("{}".format(ip["ip"]))
            if "ip" in ip_result.keys():
                ip_result['level'] = level[-3]
                if get_speed:
                    if int(n_ping) < 100: ip_result['level'] = level[0]
                    if 100 < int(n_ping) < 500: ip_result['level'] = level[1]
                    if int(n_ping) > 500: ip_result['level'] = level[2]
                    ip_result["speed"] = n_ping + 500
                ips_result.append(ip_result)
                continue
            if "info" in ip_result.keys():
                if ip_result["info"] == "未知归属地":
                    ipv6['ip'] = ip["ip"]
                    ipv6["city"] = ip["area"]
                    ipv6['level'] = level[1]
                    if get_speed: ipv6['speed'] = ""
                    ipv6["info"] = "节点无法测速,请选择离您服务器最近的尝试!"
                    ips_result.append(ipv6)
        except:
            continue
    if len(ips_result) < 2 and ips_result[-1]["city"] == "ipv6 地址": ips_result.pop(-1)
    return ips_result


def set_home_host2(host):
    """
    @name 设置官网hosts
    @author wzz<wzz@bt.cn>
    @param host IP地址
    @return void
    """
    msg = "请尝试点击【清理旧节点】,如果仍然不行,请联系堡塔运维! https://www.bt.cn/bbs"
    www_set = ExecShell("echo \"{} www.bt.cn\" >> /etc/hosts".format(host))
    api_set = ExecShell("echo \"{} api.bt.cn\" >> /etc/hosts".format(host))
    if not www_set[1] and not api_set[1]: return returnMsg(True, "节点设置成功")
    if www_set[1]: return returnMsg(False, "节点设置失败: {}, {}".format(www_set[1], msg))
    if api_set[1]: return returnMsg(False, "节点设置失败: {}, {}".format(api_set[1], msg))
    return returnMsg(False, "节点设置失败: {}".format(msg))


def Clean_bt_host():
    '''
    删除bt.cn相关的hosts绑定信息
    @author wzz <wzz@bt.cn>
    @return:
    '''
    check_hosts = ExecShell("grep \"bt.cn\" /etc/hosts")
    if check_hosts[0]:
        result = ExecShell("sed -i \"/bt.cn/d\" /etc/hosts")
        if result[1]: return returnMsg(False, "旧节点清理失败: {}".format(result[1]))
        return returnMsg(True, "旧节点已清理")
    return returnMsg(True, "hosts没有绑定旧节点无需清理")


def Set_bt_host(ip=None):
    '''
    设置bt官网(www && api)指定hosts节点
    @author wzz <wzz@bt.cn>
    @param get: 手动设置 get.ip 官网传ip地址,从public.Get_ip_info方法获取 | 自动设置
    @return:
    '''
    Clean_bt_host()

    if ip: return set_home_host2(ip)
    # 如果不传ip则自动设置
    ips_info = Get_ip_info(get_user=False)
    headers = {"host": "www.bt.cn"}
    for host in ips_info:
        new_url = "https://{}".format(host['ip'])
        res = HttpGet(new_url, 1, headers=headers)
        if res:
            writeFile("{}/data/home_host.pl".format(get_panel_path()), host["ip"])
            result = set_home_host2(host["ip"])
            if result["status"]:
                return returnMsg(True, "已自动选择为{}{}的最优节点,运营商是: {}"
                                 .format(host['province'], host['city'], host['carrier']))
    return returnMsg(False, "自动选择节点失败,请尝试手动设置")


def set_ownership(directory, user):
    '''
    设置指定目录及目录下所有文件、子目录所属为user
    @param directory:
    @param user:
    @return:
    '''
    import pwd
    uid = pwd.getpwnam(user).pw_uid
    gid = pwd.getpwnam(user).pw_gid

    os.chown(directory, uid, gid)

    for root, dirs, files in os.walk(directory):
        for d in dirs:
            dir_path = os.path.join(root, d)
            os.chown(dir_path, uid, gid)
        for f in files:
            file_path = os.path.join(root, f)
            os.chown(file_path, uid, gid)


def set_permissions(directory, permissions):
    '''
    设置指定目录及目录下所有文件、子目录权限为permissions
    @param directory:
    @param permissions: 传八进制，如0o755
    @return:
    '''
    os.chmod(directory, permissions)

    for root, dirs, files in os.walk(directory):
        for d in dirs:
            dir_path = os.path.join(root, d)
            os.chmod(dir_path, permissions)
        for f in files:
            file_path = os.path.join(root, f)
            os.chmod(file_path, permissions)


def check_ssl_verify(certPath='ssl/ca.pem'):
    '''
    校验面板设置SSL双向认证证书格式
    @param certPath:
    @return:
    '''
    if "crl.pem" in certPath:
        certKey = readFile(certPath)
        if "-----BEGIN X509 CRL-----" not in certKey:
            return False
        return True

    res = False
    openssl = '/usr/local/openssl/bin/openssl'
    if not os.path.exists(openssl): openssl = 'openssl'
    certPem = readFile(certPath)
    if "-----BEGIN CERTIFICATE-----" in certPem and "Certificate" in certPem:
        result = ExecShell(openssl + " x509 -in " + certPath + " -noout -subject")
        res = True
        if len(result[1]) > 2: res = False
        if result[0].find('error:') != -1: res = False
    return res


def is_write_file():
    '''
        @name 测试是否能写入文件
        @return void
    '''
    test_file = '/etc/init.d/bt_10000100.pl'
    writeFile(test_file, 'True')
    if os.path.exists(test_file):
        if readFile(test_file) == 'True':
            os.remove(test_file)
            return True
        os.remove(test_file)
    return False


def stop_syssafe():
    '''
        @name 临时停用系统加固
        @return bool
    '''
    # 检测是否可写
    ret = is_write_file()
    is_stop_syssafe_file = '{}/data/is_stop_syssafe.pl'.format(get_panel_path())
    # 如果不可写，则尝试停用系统加固
    if not ret:
        syssafe_path = get_plugin_path('syssafe')
        if os.path.exists(syssafe_path):
            writeFile(is_stop_syssafe_file, 'True')
            if not os.path.exists("/etc/init.d/bt_syssafe"):
                ExecShell("cp -r /www/server/panel/plugin/syssafe/init.sh /etc/init.d/bt_syssafe && chmod +x /etc/init.d/bt_syssafe")
            ExecShell("/etc/init.d/bt_syssafe stop")

            # 停用系统加固后再检测一次
            ret = is_write_file()
            return ret

    return ret


def start_syssafe():
    '''
        @name 恢复系统加固的运行状态
        @return void
    '''
    is_stop_syssafe_file = '{}/data/is_stop_syssafe.pl'.format(get_panel_path())
    if os.path.exists(is_stop_syssafe_file):
        ExecShell("/etc/init.d/bt_syssafe start")
        if os.path.exists(is_stop_syssafe_file):
            os.remove(is_stop_syssafe_file)


def check_sys_write():
    '''
        @name 检查关键目录是否可写
        @return bool
    '''
    return stop_syssafe()


def prevent_re_key(input_str):
    # 防正则转译
    re_char = ['$', '(', ')', '*', '+', '.', '[', ']', '{', '}', '?', '^', '|', '\\']
    res = []
    for i in input_str:
        if i in re_char:
            res.append("\\" + i)
        else:
            res.append(i)
    return "".join(res)


def check_area_panel():
    '''
    @name: 检查地区限制
    @return:
    '''
    import contextlib
    areas_dict = get_limit_area()

    # 关闭状态直接返回false
    if areas_dict["limit_area_status"] == "false": return False
    # 2024/1/3 下午 2:23 兼容配置文件如果为空或者地区为空或配置文件异常，则直接跳过验证
    if len(areas_dict["limit_area"]) == 0: return False
    if len(areas_dict["limit_area"]["city"]) == 0:
        if "province" in areas_dict["limit_area"] and len(areas_dict["limit_area"]["province"]) == 0:
            if "country" in areas_dict["limit_area"] and len(areas_dict["limit_area"]["country"]) == 0:
                return False

    client_ip = GetClientIp()
    # 本地访问直接返回false
    if client_ip in ['127.0.0.1', 'localhost', '::1']: return False
    if is_ipv6(client_ip): return False
    ip_area_dict = get_ip_location(client_ip)
    # 没有查询到地区返回false，内网地址直接返回false
    if not ip_area_dict: return False
    if ip_area_dict["country"]["country"] == "内网地址": return False
    try:
        error_str = "<h2>{}</h2> {}</br> {}</br> {}".format(
            getMsg('PAGE_ERR_IP_AREA_H1'),
            getMsg('PAGE_ERR_IP_AREA_P1', ("{} {} {}".format(
                ip_area_dict["country"]["country"],
                ip_area_dict["country"]["province"],
                ip_area_dict["country"]["city"]
            ),)),
            getMsg('PAGE_ERR_IP_AREA_P2'),
            getMsg('PAGE_ERR_IP_AREA_P3')
        )

        # 仅允许allow列表中的地区,其他地区都不可以访问
        if areas_dict["limit_type"] == "allow":
            for city in areas_dict["limit_area"]["city"]:
                if len(ip_area_dict["country"]["city"].strip()) == 0:
                    break

                if ip_area_dict["country"]["city"].strip() in city["name"]:
                    return False

            for province in areas_dict["limit_area"]["province"]:
                if len(ip_area_dict["country"]["province"].strip()) == 0:
                    break

                if ip_area_dict["country"]["province"].strip() in province["name"]:
                    return False

            for country in areas_dict["limit_area"]["country"]:
                if len(ip_area_dict["country"]["country"].strip()) == 0:
                    break

                if ip_area_dict["country"]["country"].strip() in country["name"]:
                    return False

            return error_str

        # 仅禁止deny列表中的地区,其他地区都可以访问
        if areas_dict["limit_type"] == "deny":
            for city in areas_dict["limit_area"]["city"]:
                if len(ip_area_dict["country"]["city"].strip()) == 0:
                    break

                if ip_area_dict["country"]["city"].strip() in city["name"]:
                    return error_str

            for province in areas_dict["limit_area"]["province"]:
                if len(ip_area_dict["country"]["province"].strip()) == 0:
                    break

                if ip_area_dict["country"]["province"].strip() in province["name"]:
                    return error_str

            for country in areas_dict["limit_area"]["country"]:
                if len(ip_area_dict["country"]["country"].strip()) == 0:
                    break

                if ip_area_dict["country"]["country"].strip() in country["name"]:
                    return error_str
    except:
        import traceback
        print(traceback.format_exc())
    return False


def get_ip_location(ip_address):
    '''
    获取ip地址的地理位置
    @param ip_address:
    @return:
    '''
    from maxminddb import open_database

    data_path = '{}/config/GeoLite2-City.mmdb'.format(get_panel_path())
    reader = open_database(data_path)
    response = reader.get(ip_address)
    reader.close()
    if not isinstance(response, dict):
        return None

    return response


def get_limit_area():
    '''
    获取地区限制列表
    @return:
    '''
    empty_content = {
        "limit_area": {
            "city": [],
            "province": [],
            "country": []
        },
        "limit_area_status": "false",
        "limit_type": "deny"
    }
    try:
        areas_file = 'data/limit_area.json'
        if not os.path.exists(areas_file): return empty_content

        try:
            areas_dict = json.loads(ReadFile(areas_file))
            if "limit_area" not in areas_dict:
                return empty_content

            if "city" not in areas_dict["limit_area"]:
                areas_dict["limit_area"]["city"] = []
            if "province" not in areas_dict["limit_area"]:
                areas_dict["limit_area"]["province"] = []
            if "country" not in areas_dict["limit_area"]:
                areas_dict["limit_area"]["country"] = []
        except json.decoder.JSONDecodeError:
            return empty_content

        return areas_dict
    except:
        print_log(get_error_info())
    return empty_content


# 密码复杂度验证
def check_password_safe(password: str) -> bool:
    '''
        @name 密码复杂度验证
        @param password(string) 密码
        @return bool
    '''
    # 是否检测密码复杂度

    # 密码长度验证
    if len(password) < 8: return False

    num = 0
    # 密码是否包含数字
    if re.search(r'[0-9]+', password): num += 1
    # 密码是否包含小写字母
    if re.search(r'[a-z]+', password): num += 1
    # 密码是否包含大写字母
    if re.search(r'[A-Z]+', password): num += 1
    # 密码是否包含特殊字符
    if re.search(r'[^\w\s]+', password): num += 1
    # 密码是否包含以上任意3种组合
    if num < 3: return False
    return True


def show_menu(menu_id, status):
    """
    设置显示隐藏菜单
    :param menu_id: 菜单id
    :param status: 0 | 1
    :return:
    """

    show_menu_file = '/www/server/panel/config/show_menu.json'
    hide_menu_file = '/www/server/panel/config/hide_menu.json'
    defanlt_data = ['memuA', 'memuAsite', 'memuAftp', 'memuAdatabase', 'memuDocker', 'memuAcontrol', 'memuAfirewall', 'memuAfiles', 'memuAlogs', 'memuAxterm', 'memuAcrontab', 'memuAsoft',
                    'memuAconfig', 'dologin', 'memuAssl']
    show_menu_data = defanlt_data
    if os.path.exists(show_menu_file):
        show_menu_data = json.loads(ReadFile(show_menu_file))

    # 获取之前设置的隐藏页面
    try:
        if os.path.exists(hide_menu_file):
            hide_menu = ReadFile(hide_menu_file)
            show_menu_data = [i for i in show_menu_data if i not in hide_menu]
            ExecShell("rm -rf {}".format(hide_menu_file))
            WriteFile(show_menu_file, json.dumps(show_menu_data))
    except:
        pass
    if status == 1 and menu_id not in show_menu_data:
        show_menu_data.append(menu_id)
    elif status == 0 and menu_id in show_menu_data:
        show_menu_data.remove(menu_id)
    WriteFile(show_menu_file, json.dumps(show_menu_data))
    return returnMsg(True, '设置成功')


def task_service_status():
    '''
        @name 检查后台任务服务状态
        @return bool
    '''
    pid_file = '{}/logs/task.pid'.format(get_panel_path())
    if not os.path.exists(pid_file): return False
    pid = readFile(pid_file)
    if not pid: return False
    if not os.path.exists('/proc/{}'.format(pid)): return False
    return True


def reload_panel():
    '''
        @name 重载面板
        @return void
    '''

    # 重载面板
    WriteFile('{}/data/reload.pl'.format(get_panel_path()), 'True')
    if not task_service_status():
        ExecShell("bash {}/init.sh start")


def restart_panel():
    '''
        @name 重启面板
        @return void
    '''

    # 重启面板
    WriteFile('{}/data/restart.pl'.format(get_panel_path()), 'True')
    if not task_service_status():
        ExecShell("bash {}/init.sh start")


# 2024/1/24 上午 10:38 通用响应对象
def returnResult(status=True, msg="OK", data=None, timestamp=None, code=0, args=None):
    '''
    通用响应对象
    @param code: 0:成功 1:失败 2:警告 ...
    @param status:
    @param msg: 只传msg,不传需要前端处理的数据
    @param data: 只传需要前端处理的数据
    @param timestamp: 秒级时间戳
    @return:

    使用示例：
    成功：return dp.returnResult(data=data)
    失败：return dp.returnResult(code=1, status=False, msg="获取失败!", data=[])
    失败：return dp.returnResult(code=1, status=False, msg="获取失败!")
    警告：return dp.returnResult(code=2, status=False, msg="警告，xxxxxxxxxxx!")
    ...
    '''
    import time
    if timestamp is None:
        timestamp = int(time.time())

    try:
        log_message = json.loads(ReadFile('BTPanel/static/language/' + GetLanguage() + '/public.json'))
        keys = log_message.keys()
    except:
        log_message = {}
        keys = []

    if type(msg) == str:
        if msg in keys:
            msg = log_message[msg]
            for i in range(len(args)):
                rep = '{' + str(i + 1) + '}'
                msg = msg.replace(rep, args[i])

    return {
        "code": code,
        "status": status,
        "msg": msg,
        "data": data,
        "timestamp": timestamp
    }


# 2024/1/24 上午 11:56 取指定模型目录
def get_mod_path(mod_name=None):
    '''
        @name 取指定插件目录
        @author hwliang<2021-07-14>
        @param mod_name<string> 模型名称 不传则返回模型根目录
        @return string
    '''

    root_path = "{}/mod/project".format(get_panel_path())
    if not mod_name: return root_path
    return "{}/{}".format(root_path, mod_name)


def get_client_info_db_obj():
    '''
        @name 获取客户端信息数据库对象
        @return object
    '''
    db_path = '{}/data/db'.format(get_panel_path())
    db_file = '{}/client_info.db'.format(db_path)
    if not os.path.exists(db_path): os.makedirs(db_path, 384)
    db_obj = M('')
    db_obj._Sql__DB_FILE = db_file
    # 如果数据库文件不存在则创建
    if not os.path.exists(db_file):
        db_obj.execute('''CREATE TABLE client_info (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            remote_addr VARCHAR(50) NOT NULL,
            remote_port INTEGER DEFAULT 0,
            session_id VARCHAR(32) NOT NULL,
            user_agent TEXT NOT NULL,
            login_time  INTEGER DEFAULT 0
        )''')

        # 创建索引
        db_obj.execute('CREATE INDEX client_ip_index ON client_info(client_ip)')
        db_obj.execute('CREATE INDEX session_id_index ON client_info(session_id)')
        db_obj.execute('CREATE INDEX login_time_index ON client_info(login_time)')
    return db_obj


def record_client_info(type=1):
    '''
        @name 记录客户端信息
        @type 记录登陆类型type 0 失败 1 成功
        @return void
    '''
    from flask import request
    from BTPanel import cache
    db_obj = get_client_info_db_obj()
    remote_addr = get_client_ip()
    user_agent = request.headers.get('User-Agent', '')
    pdata = {
        'remote_addr': remote_addr,
        'remote_port': get_remote_port(),
        'session_id': md5(remote_addr + user_agent),
        'user_agent': user_agent,
        'login_time': int(time.time()),
        'login_type': type
    }
    db_obj.table('client_info').insert(pdata)
    db_obj.close()

    # 设置缓存
    cache.set('last_client_session_id', pdata['session_id'], 86400 * 2)


def check_client_info():
    '''
        @name 检查客户端信息
        @return int 0:陌生IP，1:上次登录的IP且UA一致，2:近30天内登录过的IP
    '''
    from flask import request
    from BTPanel import cache
    remote_addr = get_client_ip()
    # 如果是本地访问或为未来IP则当作陌生IP
    if remote_addr in ['0.0.0.0', '127.0.0.1', '::1', '::']: return 0
    user_agent = request.headers.get('User-Agent', '')
    # 如果UA不是浏览器则当作陌生IP
    if user_agent.find('Mozilla') == -1: return 0

    session_id = md5(remote_addr + user_agent)
    if cache.get('last_client_session_id') == session_id: return 1

    db_obj = get_client_info_db_obj()
    if not db_obj: return 0

    last_login_info = db_obj.table('client_info').order('id desc').field('remote_addr,session_id,login_time').find()
    if not last_login_info: return 0

    # 如果上次登录的IP且UA一致
    now_time = int(time.time())
    if last_login_info['session_id'] == session_id:
        s_time = now_time - last_login_info['login_time']
        if s_time < (86400 * 2):
            cache.set('last_client_session_id', session_id, 86400 * 2 - s_time)
            return 1
        if s_time < (86400 * 30): return 2
        return 0

    # 如果近30天内登录过的IP
    if remote_addr == last_login_info['remote_addr'] and now_time - last_login_info['login_time'] < 2592000: return 2
    if db_obj.table('client_info').where('remote_addr=?', remote_addr).count(): return 2

    # 陌生IP
    return 0


def redirect_to_login(default_callback_def=None):
    '''
        @name 重定向到登录页面
        @return void
    '''
    from flask import redirect, request, Response
    client_status = check_client_info()
    admin_path = get_admin_path()
    # 获取请求头
    x_http_token = request.headers.get('x-http-token', '')
    if client_status == 0:
        if default_callback_def:
            return default_callback_def(None)
        return error_404(None)
    elif client_status == 1:
        if x_http_token:
            result = {"status": False, "code": -8888, "redirect": admin_path, "msg": "当前登录会话已经失效，请重新登录!"}
            return Response(json.dumps(result), mimetype='application/json', status=200)
        return redirect(admin_path)
    elif client_status == 2:
        if x_http_token:
            result = {"status": False, "code": -8888, "redirect": "/login", "msg": "当前登录会话已经失效，请重新登录!"}
            return Response(json.dumps(result), mimetype='application/json', status=200)
        return redirect('/login')

    if default_callback_def:
        return default_callback_def(None)

    # 如果安全入口为空则跳转到登录页面
    if admin_path in ['/login', '', '/', None]:
        return redirect('/login')

    return error_404(None)


def ws_send(data: str):
    try:
        if '/www/server/panel' not in sys.path:
            sys.path.insert(0, '/www/server/panel')
        from BTPanel import WS_OBJ
        ws_obj = {i: j for i, j in WS_OBJ.items() if j['timeout'] > int(time.time())}
        if ws_obj == {}: return False
        for i, j in ws_obj.items():
            j['ws_obj'].send(data)
        return True
    except:
        return False


def read_file_lines_range(filename, start_line: int, end_line: int):
    """
    读取文件指定行数范围内容

    Args:
        filename: 文件名
        start_line: 开始行号
        end_line: 结束行号

    Returns:
        list: 指定行数范围内容列表
    """
    try:
        with open(filename, 'r') as f:
            lines = f.readlines()
            return "".join(lines[start_line:end_line])
    except:
        return "获取文件内容报错了"


def err_collect(error_info, type, error_id):
    '''
        @error_info 错误信息
        @type 错误类型
        @error_id 错误ID
    '''

    from flask import redirect, request, Response
    _form = request.form.to_dict()
    if 'username' in _form: _form['username'] = '******'
    if 'password' in _form: _form['password'] = '******'
    if 'phone' in _form: _form['phone'] = '******'

    # 错误信息
    error_infos = {
        "REQUEST_DATE": getDate(),  # 请求时间
        "PANEL_VERSION": version(),  # 面板版本
        "OS_VERSION": get_os_version(),  # 操作系统版本
        "REMOTE_ADDR": GetClientIp(),  # 请求IP
        "REQUEST_URI": request.method + request.full_path,  # 请求URI
        "REQUEST_FORM": xsssec(str(_form)),  # 请求表单
        "USER_AGENT": xsssec(request.headers.get('User-Agent')),  # 客户端连接信息
        "ERROR_INFO": error_info,  # 错误信息
        "PACK_TIME": readFile("/www/server/panel/config/update_time.pl") if os.path.exists("/www/server/panel/config/update_time.pl") else getDate(),  # 打包时间
        "TYPE": type,
        "ERROR_ID": error_id,
    }
    pkey = Md5(error_infos["ERROR_ID"])

    # 提交异常报告
    if not cache_get(pkey) and "缺少必要参数" not in error_info:
        try:
            run_thread(httpPost, ("https://api.bt.cn/bt_error/index.php", error_infos))
            cache_set(pkey, 1, 1800)
        except Exception as e:
            pass  # 错误信息


# 在创建一个目录时调用，将传入路径上层的所有同名文件改名，防止文件夹创建失败
def rename_parent_file(tanget_path: str):
    from uuid import uuid4

    base_dir = os.path.dirname(tanget_path)

    while base_dir not in ("/", ""):
        if os.path.isfile(base_dir):  # 如果是文件，就重命名
            os.rename(base_dir, "{}_{}".format(base_dir, uuid4().hex[::2]))
        base_dir = os.path.dirname(base_dir)  # 向上寻找


# 获取nginx版本，没有获取到版本时返回None，获取到时，返回一个3位长度的列表，如[1, 25, 1], 表示1.25.1版本
def nginx_version():
    out, _ = ExecShell("/www/server/nginx/sbin/nginx -V 2>&1  | grep 'version'")
    out: str = out.strip()
    if not out:
        return None

    rep_ver = re.compile(r"nginx\s+version.*/(?P<ver>\d+\.\d+(\.\d+)*)")
    res = rep_ver.search(out)
    if not res:
        return None
    ver = res.group("ver")
    ver_list = [int(i) for i in ver.split(".")]
    if len(ver_list) < 3:
        ver_list.extend([0] * (3 - len(ver_list)))
    if len(ver_list) > 3:
        ver_list = ver_list[:3]
    return ver_list


def change_nginx_http2():
    import os
    nginx_file_path = "/www/server/panel/vhost/nginx"
    for i in os.listdir(nginx_file_path):
        if not i.endswith(".conf"):
            continue
        nginx_file = os.path.join(nginx_file_path, i)
        change_nginx_server_http2(nginx_file)


def change_nginx_server_http2(nginx_file: str):
    if not os.path.isfile(nginx_file):
        return
    data = ReadFile(nginx_file)
    rep_listen = re.compile(r"\s*listen\s+[\[\]:]*([0-9]+).*;[^\n]*\n", re.M)

    conf_list = []
    start_idx, last_listen_idx = 0, -1
    for tmp in rep_listen.finditer(data):
        listen_str = tmp.group()
        if "http2" in listen_str:
            listen_str = listen_str.replace("http2", "")
            last_listen_idx = len(conf_list) + 2

        conf_list.append(data[start_idx:tmp.start()])
        conf_list.append(listen_str)
        start_idx = tmp.end()

    conf_list.append(data[start_idx:])
    if last_listen_idx > 0:
        conf_list.insert(last_listen_idx, "    http2 on;\n")

        new_conf = "".join(conf_list)
        writeFile(nginx_file, new_conf)


def is_change_nginx_http2() -> bool:
    nginx_ver = nginx_version()
    if not nginx_ver:
        return False

    if nginx_ver >= [1, 25, 1]:
        return True

    return False


def is_change_nginx_old_http2() -> bool:
    nginx_ver = nginx_version()
    if not nginx_ver:
        return False
    if nginx_ver < [1, 25, 1]:
        return True

    return False


def change_nginx_old_http2():
    nginx_file_path = "/www/server/panel/vhost/nginx"
    for i in os.listdir(nginx_file_path):
        if not i.endswith(".conf"):
            continue
        nginx_file = os.path.join(nginx_file_path, i)
        change_nginx_server_old_http2(nginx_file)


def change_nginx_server_old_http2(nginx_file: str):
    if not os.path.isfile(nginx_file):
        return
    data = ReadFile(nginx_file)
    if not isinstance(data, str):
        return

    rep_http2_on = re.compile(r"\s*http2\s+on;[^\n]*\n", re.M)
    if not rep_http2_on.search(data):
        return
    else:
        data = rep_http2_on.sub("\n", data)

    rep_listen = re.compile(r"\s*listen\s+[\[\]:]*443.*;[^\n]*\n", re.M)
    conf_list = []
    start_idx = 0
    for tmp in rep_listen.finditer(data):
        listen_str = tmp.group()
        conf_list.append(data[start_idx:tmp.start()])
        conf_list.append(listen_str.replace(";", " http2;"))
        start_idx = tmp.end()

    conf_list.append(data[start_idx:])
    new_conf = "".join(conf_list)
    writeFile(nginx_file, new_conf)


def remove_nginx_quic():
    nginx_file_path = "/www/server/panel/vhost/nginx"
    for i in os.listdir(nginx_file_path):
        if not i.endswith(".conf"):
            continue
        nginx_file = os.path.join(nginx_file_path, i)
        remove_nginx_server_quic(nginx_file)

def remove_nginx_server_quic(nginx_file: str):
    if not os.path.isfile(nginx_file):
        return
    data = ReadFile(nginx_file)
    if not isinstance(data, str):
        return

    rep_listen_quic = re.compile(r"\s*listen\s+.*quic;", re.M)
    if not rep_listen_quic.search(data):
        return

    new_conf = rep_listen_quic.sub('', data)
    writeFile(nginx_file, new_conf)


def repair_nginx_quic_ssl_protocols():
    nginx_file_path = "/www/server/panel/vhost/nginx"
    for i in os.listdir(nginx_file_path):
        if not i.endswith(".conf"):
            continue
        nginx_file = os.path.join(nginx_file_path, i)
        repair_nginx_server_quic_ssl_protocols(nginx_file)

    file_path = get_panel_path() + "/data/ssl_protocol.json"
    if os.path.exists(file_path):
        data = readFile(file_path)
        if isinstance(data, str):
            data_dict = json.loads(data)
            data_dict["TLSv1.3"] = True
            writeFile(file_path, json.dumps(data_dict))

def repair_nginx_server_quic_ssl_protocols(nginx_file: str):
    if not os.path.isfile(nginx_file):
        return
    data = ReadFile(nginx_file)
    if not isinstance(data, str):
        return

    rep_listen_quic = re.compile(r"\s*listen\s+.*quic;", re.M)
    if not rep_listen_quic.search(data):
        return

    rep_ssl_protocols = re.compile(r"\s*ssl_protocols\s+[^;\n]*;", re.M)
    if not rep_ssl_protocols.search(data):
        return

    tmp = rep_ssl_protocols.search(data)
    ssl_protocols_str = tmp.group()
    if ssl_protocols_str.find("TLSv1.3") != -1:
        return
    new_ssl_protocols_str = ssl_protocols_str[:-1] + " TLSv1.3;"
    data = data.replace(ssl_protocols_str, new_ssl_protocols_str, 1)

    writeFile(nginx_file, data)


def is_nginx_http3():
    return ExecShell("nginx -V 2>&1| grep 'http_v3_module'")[0].strip() != ''


def repair_lack_field():
    ExecShell("btpython {}/script/init_db.py".format(get_panel_path()))


def repair_db():
    """
    @name 修复数据库
    """
    try:
        writeFile('/www/server/panel/data/db/update', '3')
    except:
        pass
    ExecShell("btpython {}/script/init_db.py".format(get_panel_path()))


def check_database_field(database_name, table_name):
    ExecShell("btpython /www/server/panel/script/check_sql.py {} {}".format(database_name, table_name))


def repair_not_such_well_know(error_msg):
    rep_open_failed = re.compile(r'\[emerg]\s+open\(\)\s*"(?P<file>.*)"\s+failed\s+(?P<err>.*)\s+in\s+.*:(\d+)', re.M)
    res = rep_open_failed.search(error_msg)
    if not res:
        return

    for t_res in rep_open_failed.finditer(error_msg):
        if t_res.group("err").find("No such file") != -1 and t_res.group("file").find("vhost/nginx/well-known") != -1:
            if not os.path.exists(t_res.group("file")):
                if not os.path.isdir(os.path.dirname(t_res.group("file"))):
                    os.makedirs(os.path.dirname(t_res.group("file")), 0o755)
                writeFile(t_res.group("file"), "")


def repair_not_such_enable_php(error_msg):
    rep_open_failed = re.compile(r'\[emerg]\s+open\(\)\s*"(?P<file>.*)"\s+failed\s+(?P<err>.*)\s+in\s+.*:(\d+)', re.M)
    res = rep_open_failed.search(error_msg)
    if not res:
        return

    for t_res in rep_open_failed.finditer(error_msg):
        file_path = t_res.group("file")
        if t_res.group("err").find("No such file") != -1 and file_path.find("nginx/conf/enable-php") != -1:
            if os.path.exists(file_path):
                continue
            ver = file_path[-7:-5]
            if ver == "00":
                writeFile(file_path, "")
                continue
            if ver == "hp":
                ver = phpmyadmin_php_version()
            if not ver.isdigit():
                continue
            writeFile(file_path, """    location ~ [^/]\.php(/|$)
    {{
        try_files $uri =404;
        fastcgi_pass  unix:/tmp/php-cgi-{}.sock;
        fastcgi_index index.php;
        include fastcgi.conf;
        include pathinfo.conf;
    }}
""".format(ver))


def phpmyadmin_php_version() -> str:
    # 获取 PhpMyAdmin 默认使用0的php版本， 如果没有就用54版本
    pm_v = readFile("/www/server/phpmyadmin/version.pl")
    if not pm_v:
        return "54"
    if not os.path.exists("/www/server/php"):
        return "54"

    php_ver = []
    for i in os.listdir("/www/server/php"):
        if os.path.isdir(os.path.join("/www/server/php", i)) and i.isdigit():
            try:
                php_ver.append(int(i))
            except:
                continue
    php_ver.sort(reverse=True)

    ver_list = [i for i in pm_v.split(".")]
    if len(ver_list) > 2:
        ver_list = ver_list[:2]

    pm_v_data = "".join(ver_list)
    if pm_v_data == "40":
        min_php = 52
        max_php = 74
    elif pm_v_data == "44":
        min_php = 54
        max_php = 73
    elif pm_v_data == "49":
        min_php = 56
        max_php = 80
    elif pm_v_data == "50" and pm_v_data == "51" or pm_v_data == "52":
        min_php = 72
        max_php = 1000
    else:
        return "54"

    for i in php_ver:
        if min_php <= i <= max_php:
            return str(i)
    return "54"


def clear_tmp_file():
    '''
        @name 清理临时文件缓存
        @return void
    '''

    # 清理缓存
    compress_caches_path = '{}/data/compress_caches'.format(get_panel_path())
    if os.path.exists(compress_caches_path):
        dir_list = os.listdir(compress_caches_path)
        for i in dir_list:
            os.system('rm -rf {}/{}'.format(compress_caches_path, i))

    # 清理无用的js文件
    vite_path = 'BTPanel/static/vite/js'
    if os.path.exists(vite_path):
        if os.path.exists('{}/loginLogs.js.map'.format(vite_path)):
            os.system('rm -f {}/*.map'.format(vite_path))
            os.system('rm -f {}/*.gz'.format(vite_path))

    # 清理临时文件
    tmp_path = '{}/tmp'.format(get_panel_path())
    if os.path.exists(tmp_path):
        dir_list = os.listdir(tmp_path)
        for i in dir_list:
            os.system('rm -rf {}/{}'.format(tmp_path, i))

    temp_path = '{}/temp'.format(get_panel_path())
    if os.path.exists(temp_path):
        dir_list = os.listdir(temp_path)
        for i in dir_list:
            os.system('rm -rf {}/{}'.format(temp_path, i))


# 检查导出的sql文件是否完整
def check_sql_file(filename, tables):
    '''
        @name 检查导出的sql文件是否完整
        @param filename<string> 文件名
        @param tables<list> 表名列表
        @return tuple (status_code<int>,msg<string>) 状态码 0:sql文件不存在 1:无异常,-1:sql文件不完整,-2:缺少表，消息
    '''
    if not os.path.exists(filename): return 0, '备份文件不存在'
    file_size = os.path.getsize(filename)
    # 超过10M的文件不检查
    if file_size > 10 * 1024 * 1024: return 1, '无异常'

    # 读取文件
    with open(filename, 'rb') as f:
        # 读取文件尾 128 字节
        f.seek(-1, 2)  # 从文件尾开始向前移动1个字节
        pos = f.tell()  # 获取当前位置
        to_read = min(128, pos)  # 获取读取位置

        f.seek(-to_read, 1)  # 从当前位置向前移动to_read个字节
        last_line = f.read(to_read)  # 读取最后to_read个字节

        # 检查文件尾是否有结束标识
        if last_line.find(b"Dump completed on") == -1:
            return -1, '备份文件缺少结束标识'

        # 逐行检查表是否存在
        f.seek(0)
        checked_tables = []

        while True:
            line = f.readline()
            if not line: break

            line = line.strip()
            # 跳过空行
            if not line: continue

            # 检查是否是创建表语句
            if not line.startswith(b"CREATE TABLE "): continue

            # 获取表名
            table = line.split(b"`")[1].decode('utf-8')

            # 跳过空表名
            if not table: continue

            # 跳过已检查的表
            if table in checked_tables: continue

            # 检查是否在表名列表中
            if table in tables:
                checked_tables.append(table)  # 添加到已检查列表

        # 检查是否有缺少的表
        if len(checked_tables) != len(tables):
            # 计算两个列表的差集
            empty_tables = set(tables).difference(checked_tables)
            return -2, '备份文件中缺少表:{}'.format(','.join(empty_tables))

    return 1, '无异常'


def get_disk_usage(path):
    """
        @name 获取目录可用空间
    """

    if not os.path.exists(path):
        return returnMsg(False, '指定目录不存在.')

    res = psutil.disk_usage(path)
    return res


def get_dir_used(path):
    """
        @name 获取目录已用空间
    """
    try:
        if not os.path.exists(path):
            return returnMsg(False, '指定目录不存在.')

        res = get_size_total([path])
        if path in res:
            return res[path]
        return 0
    except:
        return 0


def check_disk_status():
    '''
        @name 检查磁盘状态
        @return int 1:正常 2:磁盘已满 3:磁盘不可写 4:Inode不足
    '''
    panel_path = get_panel_path()
    # 检查Inode是否足够
    inode = os.statvfs(panel_path)
    if inode.f_files > 0 and inode.f_favail < 2:
        return 4, '检测到磁盘Inode已耗尽，无法访问面板数据库，请登录SSH手动清理磁盘后重试!'

    # 检查磁盘是否已满
    import psutil

    disk = psutil.disk_usage(panel_path)
    if disk.free < 1024 * 512:
        return 2, '检测到磁盘可用空间不足，无法访问面板数据库，请登录SSH手动清理磁盘后重试!'

    # 检查磁盘是否可写
    test_file = '{}/data/db/test.txt'.format(panel_path)
    if writeFile(test_file, 'test'):
        os.remove(test_file)
    else:
        return 3, '检测到面板目录不可写，无法访问面板数据库，请登录SSH检查原因，确保面板data目录可写后再尝试!'

    # 磁盘状态正常
    return 1, ''


def read_rare_charset_file(filename: str):
    """
    读取文件内容, 返回本信息， 如果出错返回 False，与readFile相比可以处理更多种编码格式。
    于24-05-23日，为处理python项目中存在的编码问题而添加
    todo: 若日后验证为有效。则可推广应用于其他位置
    """
    import chardet
    if not os.path.exists(filename):
        return False

    fp = None
    try:
        fp = open(filename, "rb")
        f_body_bytes: bytes = fp.read()
        fp.close()
    except:
        if fp and not fp.closed:
            fp.close()

        return False

    if hasattr(chardet, "detect_all"):  # 处理部分版本没有detect_all方法的问题
        tmp_eng_list = chardet.detect_all(f_body_bytes)[:3]
    else:
        tmp_eng_list = [chardet.detect(f_body_bytes)]
    for tmp_eng in tmp_eng_list:
        try:
            f_body = f_body_bytes.decode(tmp_eng["encoding"])
        except:
            continue
        return f_body

    for eng in ("utf-8", "GBK", "utf-16", "utf-32", "BIG5"):
        try:
            f_body = f_body_bytes.decode(eng, errors="ignore")
        except:
            continue
        return f_body

    return False


# 解析journalctl --disk-usage 获取的容量
def parse_journal_disk_usage(output):
    import re
    # 使用正则表达式来提取数字和单位
    match = re.search(r'take up (\d+(\.\d+)?)\s*([KMGTP]?)', output)
    total_bytes = 0
    if match:
        value = float(match.group(1))  # 数字
        unit = match.group(3)  # 单位
        # 将所有单位转换为字节
        if unit == '':
            unit_value = 1
        elif unit == 'K':
            unit_value = 1024
        elif unit == 'M':
            unit_value = 1024 * 1024
        elif unit == 'G':
            unit_value = 1024 * 1024 * 1024
        elif unit == 'T':
            unit_value = 1024 * 1024 * 1024 * 1024
        elif unit == 'P':
            unit_value = 1024 * 1024 * 1024 * 1024 * 1024
        else:
            unit_value = 0

        # 计算总字节数
        total_bytes = value * unit_value
    return total_bytes


def repair_monitor_log_format(error_msg: str):
    if not error_msg:
        return False
    # 如果有监控报表重构版就把日志格式移过来
    if os.path.exists("/www/server/monitor/monitor"):
        try:
            shutil.copyfile(
                "/www/server/panel/plugin/monitor/monitor/config/nginx_log_format.conf",
                "/www/server/panel/vhost/nginx/0.monitor_log_format.conf"
            )
        except:
            print_log(get_error_info())
            pass
        return

    rep_open_failed = re.compile(r'unknown log format "monitor" in\s+(?P<file>(/[^/\s]*)+\.conf)')
    res = rep_open_failed.search(error_msg)
    if not res:
        return

    nginx_file_path = "/www/server/panel/vhost/nginx"
    for i in os.listdir(nginx_file_path):
        if not i.endswith(".conf"):
            continue
        nginx_file = os.path.join(nginx_file_path, i)
        remove_nginx_monitor_conf(nginx_file)


def remove_nginx_monitor_conf(nginx_file: str):
    if not os.path.isfile(nginx_file):
        return
    data = ReadFile(nginx_file)
    if not isinstance(data, str):
        return
    if data.find("syslog:server=unix:") == -1:
        return

    # 可能存在的错误配置
    server_config = re.sub(r"(#.*)?\s*access_log\s+syslog:server=unix:.*", "", data)
    server_config = re.sub(r"\s*error_log\s+syslog:server=unix:.*(\n[ \r\t]*#.*)?", "", server_config)
    writeFile(nginx_file, server_config)


# 2024/12/2 17:20 如果是debug模式就输出日志
def debug_log():
    '''
        @name 如果是debug模式就输出日志
        @ public.debug_log()
    '''
    if os.path.exists('data/debug.pl'):
        print(get_error_info())
        print_log(get_error_info())

def get_cloud_server_type():
    """
    获取云服务器厂商和类型
    """
    if not os.path.exists("/www/server/panel/data/server_store.pl"):
        return "others", "others"
    service = readFile("/www/server/panel/data/server_store.pl").strip()
    if service == "aliyun":
        ipv4 = httpGet('http://100.100.100.200/latest/meta-data/eipv4', timeout=(1, 1))
        if ipv4:
            service = "aliyun"
            if os.path.exists("/root/.swas/machine-info"):
                server_type = "lighthouse"
            else:
                server_type = "ecs"
        else:
            service = "others"
            server_type = "others"
    elif service == "tencent":
        if os.path.exists("/usr/local/qcloud/lighthouse/.cert/machine-info"):
            server_type = "lighthouse"
        else:
            server_type = "cvm"
    else:
        server_type = "others"
    return service, server_type


def get_menu():
    path = '/www/server/panel/config/menu.json'
    try:
        data = json.loads(readFile(path))
        return data["menu"]
    except:
        return []


def split_domain_sld(domain: str):
    if not domain or not isinstance(domain, str):
        return domain, ""

    from mod.base.pubsuffix import get_tld

    tld = get_tld(domain)
    parts = domain.strip('.').split('.')
    num_of_tld_parts = 0 if tld is None else tld.count('.') + 1

    # 当域名的子域名数量小于等于TLD数量+1时，则返回整个域名， 如: "baidu.com.cn" 返回 ("baidu.com.cn", "") tld 部分是"com.cn"
    if len(parts) <= num_of_tld_parts + 1:
        return domain, ""
    else:
        return ".".join(parts[-num_of_tld_parts-1:]), ".".join(parts[:-num_of_tld_parts-1])


def _record_allowed_gai_family():
    import requests.packages.urllib3.util.connection as urllib3_conn

    f = urllib3_conn.allowed_gai_family

    def _reset_allowed_gai_family():
        urllib3_conn.allowed_gai_family = f

    return _reset_allowed_gai_family

reset_allowed_gai_family = _record_allowed_gai_family()