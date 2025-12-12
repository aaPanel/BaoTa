# coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author:   hwliang <hwl@bt.cn>
# +-------------------------------------------------------------------
import logging
import sys
import json
import os
import threading
import time
import re
import traceback
import uuid
import psutil
import socket

panel_path = '/www/server/panel'
if not os.name in ['nt']:
    os.chdir(panel_path)
if not 'class/' in sys.path:
    sys.path.insert(0, 'class/')

from flask import Flask, session, render_template, send_file, request, redirect, g, make_response, \
    render_template_string, abort, stream_with_context, Response as Resp
from cachelib import SimpleCache,FileSystemCache
from werkzeug.wrappers import Response
from flask_session import Session
from flask_compress import Compress

is_process = os.path.exists(panel_path + '/data/is_process.pl')
if is_process:
    cache = FileSystemCache(panel_path + "/data/cache",5000)
else:
    cache = SimpleCache(5000)
import public

# 初始化Flask应用
app = Flask(__name__,
            template_folder="templates/{}".format(
                public.GetConfigValue('template')))
Compress(app)
try:
    from flask_sock import Sock
except:
    from flask_sockets import Sockets as Sock

sockets = Sock(app)
# 注册HOOK
hooks = {}
if not hooks:
    public.check_hooks()
# import db
dns_client = None
app.config['DEBUG'] = os.path.exists('data/debug.pl')
app.config['SSL'] = os.path.exists('data/ssl.pl')
app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024 * 16 # 最大请求大小，用于支持3M内文件编辑和文件分片传输
app.config['MAX_FORM_MEMORY_SIZE'] = 1024 * 1024 * 4 # 一个表单最大内存大小，用于支持3M内文件编辑

# 设置BasicAuth
basic_auth_conf = 'config/basic_auth.json'
app.config['BASIC_AUTH_OPEN'] = False
if os.path.exists(basic_auth_conf):
    try:
        ba_conf = json.loads(public.readFile(basic_auth_conf))
        app.config['BASIC_AUTH_USERNAME'] = ba_conf['basic_user']
        app.config['BASIC_AUTH_PASSWORD'] = ba_conf['basic_pwd']
        app.config['BASIC_AUTH_OPEN'] = ba_conf['open']
    except:
        pass

# 初始化SESSION服务
app.secret_key = public.md5(
    str(os.uname()) +
    str(psutil.boot_time()))
local_ip = None
my_terms = {}

app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = panel_path + '/data/session'
app.config['SESSION_FILE_THRESHOLD'] = 1000
app.config['SESSION_FILE_MODE'] = 0o600
app.config['SESSION_FILE_LOCK'] = 1

# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///{}/data/db/session.db'.format(panel_path)
# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# app.config['SESSION_TYPE'] = 'sqlalchemy'

app.config['SESSION_PERMANENT'] = True
app.config['SESSION_USE_SIGNER'] = True
app.config['SESSION_KEY_PREFIX'] = 'BT_:'
app.config['PERMANENT_SESSION_LIFETIME'] = max(8600, public.get_session_timeout())
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 86400
if app.config['SSL']:
    app.config['SESSION_COOKIE_SAMESITE'] = None
    # app.config['SESSION_COOKIE_SECURE'] = True
    app.config['SESSION_COOKIE_NAME'] = public.md5(app.secret_key) + "_ssl"
else:
    app.config['SESSION_COOKIE_SAMESITE'] = None
    app.config['SESSION_COOKIE_NAME'] = public.md5(app.secret_key)

Session(app)

import common

# 初始化路由
comm = common.panelAdmin()
method_all = ['GET', 'POST']
method_get = ['GET']
method_post = ['POST']
json_header = {'Content-Type': 'application/json; charset=utf-8'}
text_header = {'Content-Type': 'text/plain; charset=utf-8'}
cache.set('p_token', 'bmac_' + public.Md5(public.get_mac_address()))
admin_path_file = 'data/admin_path.pl'
admin_path = '/'
bind_pl = 'data/bind.pl'

menu_dict = {i["id"].lower(): i["href"] for i in public.get_menu()}

if os.path.exists(admin_path_file):
    admin_path = public.readFile(admin_path_file).strip()
admin_path_checks = [
    '/', '/san', '/bak', '/monitor', '/abnormal', '/close', '/task', '/login',
    '/config', '/site', '/sites', '/ftp', '/public', '/database', '/data',
    '/download_file', '/control', '/crontab', '/firewall', '/files', '/soft',
    '/ajax', '/system', '/panel_data', '/code', '/ssl', '/plugin', '/wxapp',
    '/hook', '/safe', '/yield', '/downloadApi', '/pluginApi', '/auth',
    '/download', '/cloud', '/webssh', '/connect_event', '/panel', '/acme',
    '/down', '/api', '/tips', '/message', '/warning', '/bind', '/daily', '/docker','/logs',
]
if admin_path in admin_path_checks: admin_path = '/bt'
if admin_path[-1] == '/': admin_path = admin_path[:-1]
uri_match = re.compile(
    r"(^/static/[\w_\./\-]+\.(js|css|png|jpg|gif|ico|svg|woff|woff2|ttf|otf|eot|map)$|^/[\w_\./\-]*$)"
)
session_id_match = re.compile(r"^[\w\.\-]+$")


# ===================================Flask HOOK========================#

# ===================================Users Authority========================#
def user_Authority():
    if 'login' not in session: return True
    if session['login'] == False: return True
    menu = ['/', '/home', '/site', '/ftp', '/database', '/docker', '/control', '/firewall', '/waf', '/files', '/logs', '/xterm', '/crontab', '/ssl','/mail','/vhost','/wp','/soft', '/config', '/site_ifame', '/ftp_ifame',
            '/database_ifame',
            '/docker_ifame', '/control_ifame', '/firewall_ifame', '/waf_ifame', '/files_ifame', '/logs_ifame', '/xterm_ifame', '/crontab_ifame', '/soft_ifame', '/config_ifame', 'ssl_ifame']
    uid = session.get('uid')
    if not uid: return False
    if uid == 1: return True
    plugin_path = '/www/server/panel/plugin/users/'
    authority_path = os.path.join(plugin_path, 'authority')
    if not os.path.exists(plugin_path): return False
    if not os.path.exists(authority_path): return False
    uid_authority_path = os.path.join(authority_path, str(uid))
    if not os.path.exists(uid_authority_path): return False
    data = public.readFile(uid_authority_path)
    data = json.loads(_decrypt(data))
    if data['state'] != '1': return False
    if data['role'] == 'administrator':
        return True
    else:
        plugin_authority_path = os.path.join(authority_path, '{}.plugin'.format(uid))
        if os.path.exists(plugin_authority_path):
            pdata = public.readFile(plugin_authority_path)
            pdata = json.loads(_decrypt(pdata))
            compile = re.compile(r'^/plugin\?action=a&name=(.*?)&s=')
            plugin_name = compile.search(request.path)
            if plugin_name:
                plugin_list = pdata['plugin']
                if plugin_name.group(1) not in plugin_list: return False
    if not data['menu']: return False
    lmenu = []
    if request.path == '/':
        path = request.path
    else:
        path = request.path.split('/')
        path = '/' + path[1]
    for i in data['menu']:
        if i == '/': continue
        lmenu.append(i + '_ifame')
    data['menu'] += lmenu
    if path in menu and path not in data['menu']: return False
    return True


# 数据解密
def _decrypt(data):
    import PluginLoader
    if not isinstance(data, str): return data
    if not data: return data
    if data.startswith('BT-0x:'):
        res = PluginLoader.db_decrypt(data[6:])['msg']
        return res
    return data

# Flask请求勾子
@app.before_request
def request_check():
    socket.setdefaulttimeout(None)
    if 'uid' in session and session['uid'] != 1 and not user_Authority():
        if public.M('users').where('id=?', (session['uid'],)).select():
            import config
            con = config.config()
            menus = con.get_menu_list(None)
            show_menus = [i['id'] for i in menus if i['show']]
            show_menus = [i.lower() for i in show_menus]
            if request.path == '/':
                try:
                    path = menu_dict[show_menus[0]]
                    if path == '/login':
                        return render_template('403.html')
                    return redirect('{}'.format(path.lower()), 302)
                except:
                    return render_template('403.html')
            if len(show_menus) < 2: return render_template('403.html')
            if not user_Authority():
                if request.path == '/file' or request.path == '/file_ifame': return render_template('403.html')
                if not request.referrer:
                    return render_template('403.html')
    if request.method not in ['GET', 'POST']: return abort(404)
    g.request_time = time.time()
    # 路由和URI长度过滤
    if len(request.path) > 256: return abort(404)
    if len(request.url) > 1024: return abort(404)
    #  print('url:',request.url)
    # URI过滤
    if not uri_match.match(request.path): return abort(404)

    offline_file = '{}/class/panelOffline.py'.format(panel_path)
    if os.path.exists(offline_file):
        try:
            import panelOffline
            res = panelOffline.panelOffline().check()
            if res: return res
        except:
            pass

    # POST参数过滤
    if request.path in [
        '/login', '/safe', '/hook', '/public', '/down',
        '/get_app_bind_status', '/check_bind'
    ]:
        pdata = request.form.to_dict()
        for k in pdata.keys():
            if len(k) > 48: return abort(404)
            if len(pdata[k]) > 256: return abort(404)
    # SESSIONID过滤
    session_id = request.cookies.get(app.config['SESSION_COOKIE_NAME'], '')
    if session_id and not session_id_match.match(session_id): return abort(404)

    # 请求头过滤
    # if not public.filter_headers():
    #     return abort(403)

    if session.get('debug') == 1: return
    g.get_csrf_html_token_key = public.get_csrf_html_token_key()

    if app.config['BASIC_AUTH_OPEN']:
        if request.path in [
            '/public', '/download', '/mail_sys', '/hook', '/down',
            '/check_bind', '/get_app_bind_status'
        ]:
            return
        auth = request.authorization
        if not comm.get_sk(): return
        if not auth: return send_authenticated()
        tips = '_bt.cn'
        if public.md5(auth.username.strip() + tips) != app.config['BASIC_AUTH_USERNAME'] \
                or public.md5(auth.password.strip() + tips) != app.config['BASIC_AUTH_PASSWORD']:
            return send_authenticated()

    if not request.path in ['/safe', '/hook', '/public', '/mail_sys', '/down']:
        ip_check = public.check_ip_panel()
        if ip_check: return ip_check

    if request.path.startswith('/static/') or request.path == '/code':
        if not 'login' in session and not 'admin_auth' in session and not 'down' in session:
            return abort(401)
    domain_check = public.check_domain_panel()
    if domain_check: return domain_check
    if public.is_local():
        not_networks = ['uninstall_plugin', 'install_plugin', 'UpdatePanel']
        if request.args.get('action') in not_networks:
            return public.returnJson(
                False, 'INIT_REQUEST_CHECK_LOCAL_ERR'), json_header
    path_list =  (
        '/home', '/site', '/ftp', '/database', '/soft', '/control', '/firewall',
        '/files', '/xterm', '/crontab', '/config', '/docker', '/logs', '/ssl','/mail','/wp'
    )
    if request.path.startswith(path_list) and request.method == "GET":
        if request.args.get('action') in [
            'get_tmp_token','download_cert'
        ]:
            return
        if not public.is_bind():
            return redirect('/bind', 302)
        if public.is_error_path():
            return redirect('/error', 302)
        if not request.path in ['/config']:
            reslut = session.get('password_expire', None)
            if reslut is None:
                reslut = not public.password_expire_check()
                session['password_expire'] = reslut
            if reslut:
                return redirect('/modify_password', 302)

    # 处理登录页面相对路径的静态文件
    if request.path.find('/static/') > 0:

        new_auth_path = _auth_path = public.get_admin_path()


        # 2024/1/3 下午 8:35 检测_auth_path是否有包含2个以上/符号,如果有则取最后一个/符号前的字符串然后替换成_auth_path
        if _auth_path.count('/') > 1:
            new_auth_path = _auth_path[:_auth_path.rfind('/')]

        if not public.path_safe_check(request.path): return abort(404)  # 路径安全检查

        _new_route =  request.path[0:request.path.find('/static/')]
        if request.path.find(_auth_path) == 0:
            static_file = public.get_panel_path() + '/BTPanel' + request.path.replace(_auth_path, '').replace('//', '/')
            if not os.path.exists(static_file): return abort(404)
            return send_file(static_file, conditional=True, etag=True)
        elif request.path.find(new_auth_path) == 0:
            static_file = public.get_panel_path() + '/BTPanel' + request.path.replace(new_auth_path, '').replace('//', '/')
            if not os.path.exists(static_file): return abort(404)
            return send_file(static_file, conditional=True, etag=True)
        elif _new_route.startswith(tuple(admin_path_checks)):
            if not session.get('login', False):
                return public.error_not_login()
            static_file = public.get_panel_path() + '/BTPanel' + request.path[len(_new_route):].replace('//','/')

            # 检测是否是插件静态文件
            plugin_static_file = public.get_panel_path() + '/plugin/' + request.path
            is_plugin_static = os.path.exists(plugin_static_file)

            # 既不是面板静态文件也不是插件静态文件
            if not os.path.exists(static_file) and not is_plugin_static: return abort(404)

            # 如果是插件静态文件
            if is_plugin_static: return send_file(plugin_static_file, conditional=True, etag=True)

            # 如果是面板静态文件
            return send_file(static_file, conditional=True, etag=True)

    if request.path.find('/static/img/soft_ico/ico') >= 0:
        if not public.path_safe_check(request.path): return abort(404)  # 路径安全检查
        static_file = "{}/BTPanel/{}".format(panel_path, request.path)
        if not os.path.exists(static_file):
            static_file = "{}/BTPanel/static/img/soft_ico/icon_plug.svg".format(panel_path)
        return send_file(static_file, conditional=True, etag=True)

    # 处理登录成功状态，更新节点
    if 'login' in session and session['login'] == True:
        if not cache.get('bt_home_node'):
            public.run_thread(public.ExecShell, ('btpython /www/server/panel/script/reload_check.py hour',))
            cache.set('bt_home_node', True, 3600)


# Flask 请求结束勾子
@app.teardown_request
def request_end(reques=None):
    if request.method not in ['GET', 'POST']: return
    if not request.path.startswith('/static/'):
        public.write_request_log(reques)
        if 'api_request' in g:
            if g.api_request:
                session.clear()


# Flask 404页面勾子
@app.errorhandler(404)
def error_404(e):
    if request.method not in ['GET', 'POST']: return Response(status=404)
    if not session.get('login', None):
        g.auth_error = True
        return public.error_not_login()
    errorStr = '''<html>
    <head><title>404 Not Found</title></head>
    <body>
    <center><h1>404 Not Found</h1></center>
    <hr><center>nginx</center>
    </body>
    </html>'''
    headers = {"Content-Type": "text/html"}
    return Response(errorStr, status=404, headers=headers)


# Flask 403页面勾子
@app.errorhandler(403)
def error_403(e):
    if request.method not in ['GET', 'POST']: return Response(status=403)
    if not session.get('login', None):
        g.auth_error = True
        return public.error_not_login()
    errorStr = '''<html>
<head><title>403 Forbidden</title></head>
<body>
<center><h1>403 Forbidden</h1></center>
<hr><center>nginx</center>
</body>
</html>'''
    headers = {"Content-Type": "text/html"}
    return Response(errorStr, status=403, headers=headers)


# Flask 500页面勾子
@app.errorhandler(Exception)
def error_500(e):
    if request.method not in ['GET', 'POST']: return Response(status=500)
    ss = '''404 Not Found: The requested URL was not found on the server. If you entered the URL manually please check your spelling and try again.

During handling of the above exception, another exception occurred:'''
    error_info = public.get_error_info().strip().split(ss)[-1].strip()
    if not session.get('login', None):
        is_panel_error = False
        if error_info.find("Traceback (most recent call last):") != -1 and os.path.exists("/www/server/panel/data/debug.pl"):
            is_panel_error = True
        g.auth_error = True
        if not is_panel_error:
            return public.error_not_login()

    nn = 'During handling of the above exception, another exception occurred:'
    if error_info.find(nn) != -1 and error_info.find('public.error_conn_cloud') != -1:
        error_info = error_info.split(nn)[0].strip()

    _form = request.form.to_dict()
    if 'username' in _form: _form['username'] = '******'
    if 'password' in _form: _form['password'] = '******'
    if 'phone' in _form: _form['phone'] = '******'
    if 'pem' in _form: _form['pem'] = '******'
    if 'pwd' in _form: _form['pwd'] = '******'
    if 'key' in _form: _form['key'] = '******'
    if 'csr' in _form: _form['csr'] = '******'
    if 'db_user' in _form: _form['db_user'] = '******'
    if 'db_password' in _form: _form['db_pwd'] = '******'
    if 'privateKey' in _form: _form['privateKey'] = '******'
    if 'certPem' in _form: _form['certPem'] = '******'

    request_info = '''REQUEST_DATE: {request_date}
  VERSION: {os_version} - {panel_version}
 REMOTE_ADDR: {remote_addr}
 REQUEST_URI: {method} {full_path}
REQUEST_FORM: {request_form}
  USER_AGENT: {user_agent}'''.format(
        request_date=public.getDate(),
        remote_addr=public.GetClientIp(),
        method=request.method,
        full_path=public.xsssec(request.full_path),
        request_form=public.xsssec(str(_form)),
        user_agent=public.xsssec(request.headers.get('User-Agent')),
        panel_version=public.version(),
        os_version=public.get_os_version())
    error_title = error_info.split("\n")[-1].replace('public.PanelError: ',
                                                     '').strip()
    if error_info.find('连接云端服务器失败') != -1:
        error_title = "连接云端服务器失败!"

    result = public.readFile(
        public.get_panel_path() +
        '/BTPanel/templates/default/panel_error.html').format(
        error_title=public.xsssec(error_title),
        request_info=request_info,
        error_msg=public.xsssec(error_info))

    # 用户信息
    # if not public.cache_get("infos"):
    #     user_info = json.loads(public.ReadFile("{}/data/userInfo.json".format(public.get_panel_path())))
    #     public.cache_set("infos", user_info, 1800)
    # else:
    #     user_info = public.cache_get("infos")
    try:
        if "import panelSSL" in error_info:
            result = public.ExecShell("btpip list|grep pyOpenSSL")[0]
            error_info = "{}\n版本信息:{}".format(error_info, result.strip())
    except:
        error_info = "{}\n版本信息: 获取失败".format(error_info)

    # 2024/4/7 上午 10:49 处理public的get传参对象参数处理的异常(get.exists)，跳过错误推送
    if "KeyError" in error_info and "缺少必要参数" in error_info:
        return Resp(result, 500)

    # 错误信息
    error_infos = {
        # "UID":  user_info['uid'],  # 用户ID
        # 'ACCESS_KEY': user_info['access_key'],  # 用户密钥
        # 'SERVER_ID': user_info['serverid'],  # 服务器ID
        "REQUEST_DATE": public.getDate(),  # 请求时间
        "PANEL_VERSION": public.version(),  # 面板版本
        "OS_VERSION": public.get_os_version(),  # 操作系统版本
        "REMOTE_ADDR": public.GetClientIp(),  # 请求IP
        "REQUEST_URI": request.method + request.full_path,  # 请求URI
        "REQUEST_FORM": public.xsssec(str(_form)),  # 请求表单
        "USER_AGENT": public.xsssec(request.headers.get('User-Agent')), # 客户端连接信息
        "ERROR_INFO": error_info,  # 错误信息
        "PACK_TIME": public.readFile("/www/server/panel/config/update_time.pl") if os.path.exists("/www/server/panel/config/update_time.pl") else public.getDate(),  # 打包时间
        "TYPE": 0,
        "ERROR_ID":str(e)
    }
    pkey = public.Md5(error_infos["ERROR_ID"])


    # 提交异常报告
    if not public.cache_get(pkey):
        try:
            public.run_thread(public.httpPost, ("https://api.bt.cn/bt_error/index.php", error_infos))
            public.cache_set(pkey, 1, 1800)
        except Exception as e:
            pass

    return Resp(result, 500)


# ===================================Flask HOOK========================#


# ===================================普通路由区========================#
@app.route('/', methods=method_all)
@app.route('/home', methods=method_all)
def home():
    # 面板首页
    comReturn = comm.local()
    if comReturn: return comReturn
    args = get_input()
    licenes = 'data/licenes.pl'
    if 'license' in args:
        public.writeFile(licenes, 'True')
    if not os.path.exists(licenes): return render_template('license.html')
    if not public.is_bind():
        return redirect('/bind', 302)

    import system
    data = system.system().GetConcifInfo()
    data['bind'] = False
    if not os.path.exists('data/userInfo.json'):
        data['bind'] = os.path.exists('data/bind.pl')
    # data[public.to_string([112, 100])], data['pro_end'], data['ltd_end'] = get_pd()
    data[public.to_string([112,
                           100])], data['pro_end'], data['ltd_end'] = get_pd()
    data['siteCount'] = public.M('sites').count()
    data['ftpCount'] = public.M('ftps').count()
    data['databaseCount'] = public.M('databases').count()
    data['lan'] = public.GetLan('index')
    data['js_random'] = get_js_random()
    public.get_rsa_public_key()  # 堡塔多机管理会跳过登录直达 /bind 和 /home 为防无法触发 rsa_public_key 生成
    return render_template('index1.html', data=data)


@app.route('/xterm', methods=method_all)
def xterm():
    # 宝塔终端管理
    comReturn = comm.local()
    if comReturn: return comReturn
    if request.method == method_get[0]:
        import system
        data = system.system().GetConcifInfo()
        return render_template('index1.html', data=data)
    import ssh_terminal

    ssh_host_admin = ssh_terminal.ssh_host_admin()
    defs = ('get_host_list', 'get_host_find', 'modify_host', 'create_host',
            'remove_host', 'set_sort', 'get_command_list', 'create_command',
            'get_command_find', 'modify_command', 'remove_command',
            'into_command', 'out_command', 'completion_tool_status', 'set_completion_tool_status')
    return publicObject(ssh_host_admin, defs, None)


@app.route('/bind', methods=method_get)
def bind():
    comReturn = comm.local()
    if comReturn: return comReturn
    userInfo = public.get_user_info()
    if not userInfo or userInfo['uid'] != -1: return redirect('/', 302)
    data = {}
    g.title = '请先绑定宝塔帐号'
    public.get_rsa_public_key()  # 堡塔多机管理会跳过登录直达 /bind 和 /home 为防无法触发 rsa_public_key 生成
    return render_template('index1.html', data=data)


@app.route('/error', methods=method_get)
def error():
    comReturn = comm.local()
    if comReturn: return comReturn
    data = {}
    g.title = '服务器错误!!!!'
    return render_template('block_error.html', data=data)


@app.route('/modify_password', methods=method_get)
def modify_password():
    comReturn = comm.local()
    if comReturn: return comReturn
    # if not session.get('password_expire',False): return redirect('/',302)
    data = {}
    g.title = '密码已过期，请修改!'
    return render_template('index1.html', data=data)


@app.route('/site', methods=method_all)
@app.route('/site/<action>/', methods=method_all)
@app.route('/site/<action>', methods=method_all)
def site(action=None,pdata=None):
    # 网站管理
    comReturn = comm.local()
    if comReturn: return comReturn
    import panelSite

    if request.method == method_get[0] and not pdata:
        # data = {}
        import system
        data = system.system().GetConcifInfo()
        data['isSetup'] = True
        data['lan'] = public.getLan('site')
        data['js_random'] = get_js_random()
        data['install_msg'] = panelSite.panelSite.check_webserver(use2render=True)
        if os.path.exists(public.GetConfigValue('setup_path') + '/nginx/sbin/nginx') == False \
                and os.path.exists(public.GetConfigValue('setup_path') + '/apache/bin/apachectl') == False \
                and os.path.exists('/usr/local/lsws/bin/lswsctrl') == False:
            data['isSetup'] = False
        is_bind()

        if request.path in ['/site_ifame']:
            return render_template('site.html', data=data)
        return render_template('index1.html', data=data)

    siteObject = panelSite.panelSite()

    defs = ('upload_csv', 'create_website_multiple', 'del_redirect_multiple',
            'del_proxy_multiple', 'delete_dir_auth_multiple', 'site_rname',
            'delete_dir_bind_multiple', 'delete_domain_multiple',
            'set_site_etime_multiple', 'check_del_data', 'set_https_mode',
            'get_https_mode', 'set_site_php_version_multiple',
            'delete_website_multiple', 'set_site_status_multiple',
            'get_site_domains', 'GetRedirectFile', 'SaveRedirectFile',
            'DeleteRedirect', 'GetRedirectList', 'CreateRedirect',
            "set_error_redirect", 'ModifyRedirect', 'set_dir_auth',
            'delete_dir_auth', 'get_dir_auth', 'modify_dir_auth_pass',
            'export_domains', 'import_domains', 'GetSiteLogs',
            'GetSiteDomains', 'GetSecurity', 'SetSecurity', 'ProxyCache',
            'CloseToHttps', 'HttpToHttps', 'SetEdate', 'get_site_errlog',
            'SetRewriteTel', 'GetCheckSafe', 'CheckSafe', 'GetDefaultSite',
            'SetDefaultSite', 'CloseTomcat', 'SetTomcat', 'apacheAddPort',
            'AddSite', 'GetPHPVersion', 'SetPHPVersion', 'DeleteSite',
            'AddDomain', 'DelDomain', 'GetDirBinding', 'AddDirBinding',
            'GetDirRewrite', 'DelDirBinding', 'get_site_types',
            'add_site_type', 'remove_site_type', 'modify_site_type_name',
            'set_site_type', 'UpdateRulelist', 'SetSiteRunPath',
            'GetSiteRunPath', 'SetPath', 'SetIndex', 'GetIndex',
            'GetDirUserINI', 'SetDirUserINI', 'GetRewriteList', 'SetSSL',
            'SetSSLConf', 'CreateLet', 'CloseSSLConf', 'GetSSL', 'SiteStart',
            'SiteStop', 'Set301Status', 'Get301Status', 'CloseLimitNet',
            'SetLimitNet', 'GetLimitNet', 'RemoveProxy', 'GetProxyList',
            'GetProxyDetals', 'CreateProxy', 'ModifyProxy', 'GetProxyFile',
            'SaveProxyFile', 'ToBackup', 'DelBackup', 'GetSitePHPVersion',
            'logsOpen', 'GetLogsStatus', 'CloseHasPwd', 'SetHasPwd',
            'GetHasPwd', 'GetDnsApi', 'SetDnsApi', 'download_cert',
            'GetRewriteLists', 'SetRewriteLists', "webserverprep",
            "get_siteServer_info", "set_siteServer_info", "check_total_install_info",
            "create_flow_rule", "get_generated_flow_info", "get_limit_config",
            "remove_flow_rule", "modify_flow_rule", "check_total_install_info",
            "set_limit_status", "set_ssl_protocol", "get_ssl_protocol",
            "get_sites_ftp", "set_sites_ftp", "create_default_conf", "list", "set_cron_scanin_info", "get_cron_scanin_info",
            "get_Scan", "set_create_default_conf","get_cdn_ip_settings",
            "set_security_headers", "get_security_headers",
            "set_sites_log_path", "get_sites_log_path", "set_dns_domains",
            "add_dns_api", "remove_dns_api", "set_dns_api", "test_domains_api",
            "multiple_basedir", "multiple_limit_net", "multiple_referer", 'check_ssl', "set_404_config", "get_404_config", "set_restart_task", "get_restart_task",
            "get_domains", "InputBackup","export_sites_to_csv","DelRewriteTel","open_cdn_ip","set_site_dns", "set_site_ignore_https_mode",
            "set_ignore_view_domain_title", "get_view_title_content", "set_free_total_status", "get_free_total_status",
            "get_https_settings", "set_global_http2https")
    return publicObject(siteObject, defs, None, pdata)


@app.route('/ftp', methods=method_all)
def ftp(pdata=None):
    # FTP管理
    comReturn = comm.local()
    if comReturn: return comReturn
    if request.method == method_get[0] and not pdata:
        FtpPort()
        import system
        data = system.system().GetConcifInfo()
        data['isSetup'] = True
        data['js_random'] = get_js_random()
        if os.path.exists(public.GetConfigValue('setup_path') +
                          '/pure-ftpd') == False:
            data['isSetup'] = False
        data['lan'] = public.GetLan('ftp')
        is_bind()
        return render_template('index1.html', data=data)
    import ftp
    ftpObject = ftp.ftp()
    defs = ('AddUser', 'DeleteUser', 'SetUserPassword', 'SetStatus', 'setPort',
            'get_login_logs', 'get_action_logs', 'set_ftp_logs', 'BatchSetUserPassword', 'get_cron_config',
            'set_cron_config', 'GetFtpUserAccess', 'ModifyFtpUserAccess', 'SetUser','view_ftp_types','add_ftp_types','delete_ftp_types','update_ftp_types','set_ftp_type_by_id','find_ftp')
    return publicObject(ftpObject, defs, None, pdata)


@app.route('/database', methods=method_all)
@app.route('/database/<action>/', methods=method_all)
@app.route('/database/<action>', methods=method_all)
def database(action=None,pdata=None):
    # 数据库管理
    comReturn = comm.local()
    if comReturn: return comReturn
    if request.method == method_get[0] and not pdata:
        import ajax
        from panelPlugin import panelPlugin

        session['phpmyadminDir'] = False
        if panelPlugin().get_phpmyadmin_stat():
            pmd = get_phpmyadmin_dir()
            if pmd:
                session['phpmyadminDir'] = 'http://' + public.GetHost(
                ) + ':' + pmd[1] + '/' + pmd[0]
        ajax.ajax().set_phpmyadmin_session()
        import system
        data = system.system().GetConcifInfo()
        data['isSetup'] = os.path.exists(
            public.GetConfigValue('setup_path') + '/mysql/bin')
        data['mysql_root'] = public.M('config').where(
            'id=?', (1,)).getField('mysql_root')
        data['lan'] = public.GetLan('database')
        data['js_random'] = get_js_random()
        is_bind()
        return render_template('index1.html', data=data)

    import database
    databaseObject = database.database()
    defs = ('get_mysql_status', 'GetdataInfo', 'check_del_data', 'get_database_size', 'GetInfo',
            'ReTable', 'OpTable', 'AlTable', 'GetSlowLogs', 'GetRunStatus',
            'SetDbConf', 'GetDbStatus', 'BinLog', 'GetErrorLog', 'GetMySQLBinlogs', 'ClearMySQLBinlog',
            'GetMySQLInfo', 'SetDataDir', 'SetMySQLPort', 'AddCloudDatabase',
            'CheckDatabaseStatus', 'check_cloud_database_status', 'AddDatabase',
            'DeleteDatabase', 'get_database_table', 'SetupPassword',
            'ResDatabasePassword', 'AddCloudServer',
            'GetCloudServer', 'RemoveCloudServer', 'ModifyCloudServer',
            'SyncToDatabases', 'SyncGetDatabases',
            'GetDatabaseAccess', 'SetDatabaseAccess',
            'ToBackup', 'GetBackup', 'InputSql', 'DelBackup',
            'GetMysqlUser', 'GetDatabasesList', 'AddMysqlUser', 'DelMysqlUser', 'AddUserGrants', 'DelUserGrants', 'GetUserGrants', 'ChangeUserPass', 'GetUserInfo',
            'GetBackupDatabase', 'GetAllBackup', 'GetBackupInfo', 'ToBackupAll', 'InputSqlAll',
            'set_auto_sqlist', 'set_auto_sqlist', 'GetPushUser', 'ModifyTableComment', 'export_table_structure', 'set_restart_task', 'get_restart_task','view_database_types',
            'add_database_types','delete_database_types','update_database_types','set_database_type_by_name','find_databases_by_name_and_type',
            'is_zip_password_protected','mysql_oom_adj','GetStartErrType','ClearMysqlBinLog','SetInnodbRecovery','GetBackupSize','GetImportLog','GetImportSize',"GetValidatePasswordConfig","SetValidatePasswordConfig","GetLoginFailed","SetLoginFailed","GetTimeOut","SetTimeOut","GetAuditLogConfig","SetAuditLogConfig","GeUserHostList","GetMysqlCommands","SetAuditLogRules","GetAuditLog","GetDatabaseList","GetmvDataDirSpeed"
            )
    return publicObject(databaseObject, defs, None, pdata)


@app.route('/acme', methods=method_all)
def acme(pdata=None):
    # Let's 证书管理
    comReturn = comm.local()
    if comReturn: return comReturn
    import acme_v2
    acme_v2_object = acme_v2.acme_v2()
    defs = ('get_orders', 'remove_order', 'get_order_find', 'revoke_order',
            'create_order', 'get_account_info', 'set_account_info',
            'update_zip', 'get_cert_init_api', 'get_auths', 'auth_domain',
            'check_auth_status', 'download_cert', 'apply_cert', 'renew_cert',
            'apply_cert_api', 'apply_dns_auth', 'get_order_list', 'get_order_detail', 'validate_domain', 'delete_order', 'download_cert_to_local', 'SetCertToSite',
            'auth_domain_api'
            )
    return publicObject(acme_v2_object, defs, None, pdata)


@app.route('/message/<action>', methods=method_all)
def message(action=None):
    # 提示消息管理
    comReturn = comm.local()
    if comReturn: return comReturn
    import panelMessage
    message_object = panelMessage.panelMessage()
    defs = ('get_messages', 'get_message_find', 'create_message',
            'status_message', 'remove_message', 'get_messages_all')
    return publicObject(message_object, defs, action, None)


@app.route('/api', methods=method_all)
def api(pdata=None):
    # APP使用的API接口管理
    comReturn = comm.local()
    if comReturn: return comReturn
    import panelApi
    api_object = panelApi.panelApi()
    defs = ('get_token', 'check_bind', 'get_bind_status', 'get_apps',
            'add_bind_app', 'remove_bind_app', 'set_token', 'get_tmp_token',
            'get_app_bind_status', 'login_for_app')
    return publicObject(api_object, defs, None, pdata)


@app.route('/control', methods=method_all)
@app.route('/control/<action>/', methods=method_all)
@app.route('/control/<action>', methods=method_all)
def control(action=None,pdata=None):
    # 监控页面
    comReturn = comm.local()
    if comReturn: return comReturn
    import system
    data = system.system().GetConcifInfo()
    data['lan'] = public.GetLan('control')
    return render_template('index1.html', data=data)


@app.route('/logs', methods=method_all)
@app.route('/logs/<action>/', methods=method_all)
@app.route('/logs/<action>', methods=method_all)
def logs(action=None,pdata=None):
    comReturn = comm.local()
    if comReturn: return comReturn
    if request.method == method_get[0] and not pdata:
        data = {}
        data['lan'] = public.GetLan('soft')
        data['show_workorder'] = not os.path.exists('data/not_workorder.pl')
        return render_template('index1.html', data=data)


@app.route('/firewall', methods=method_all)
@app.route('/firewall/<action>/', methods=method_all)
@app.route('/firewall/<action>', methods=method_all)
def firewall(action=None,pdata=None):
    # 安全页面
    comReturn = comm.local()
    if comReturn: return comReturn
    if request.method == method_get[0] and not pdata:
        import system
        data = system.system().GetConcifInfo()
        data['lan'] = public.GetLan('firewall')
        data['js_random'] = get_js_random()

        return render_template('index1.html', data=data)

    import firewalls
    firewallObject = firewalls.firewalls()
    defs = ('GetList', 'AddDropAddress', 'DelDropAddress', 'FirewallReload',
            'SetFirewallStatus', 'AddAcceptPort', 'DelAcceptPort',
            'SetSshStatus', 'SetPing', 'SetSshPort', 'GetSshInfo',
            'SetFirewallStatus')
    return publicObject(firewallObject, defs, None, pdata)


@app.route('/ssh_security', methods=method_all)
def ssh_security(pdata=None):
    # SSH安全
    comReturn = comm.local()
    if comReturn: return comReturn
    if request.method == method_get[0] and not pdata and not request.args.get(
            'action', '') in ['download_key']:
        data = {}
        data['lan'] = public.GetLan('firewall')
        data['js_random'] = get_js_random()
        return render_template('firewall.html', data=data)
    import ssh_security
    firewallObject = ssh_security.ssh_security()
    is_csrf = True
    if request.args.get('action', '') in ['download_key']: is_csrf = False
    defs = ('san_ssh_security', 'set_password', 'set_sshkey', 'stop_key',
            'get_config', 'download_key', 'stop_password', 'get_key',
            'return_ip', 'add_return_ip', 'del_return_ip', 'start_jian',
            'stop_jian', 'get_jian', 'get_logs', 'set_root', 'stop_root',
            'start_auth_method', 'stop_auth_method', 'get_auth_method',
            'check_so_file', 'get_so_file', 'get_pin', 'set_login_send',
            'get_login_send', 'get_msg_push_list', 'clear_login_send', 'get_login_record', 'start_login_record',
            'stop_login_record', 'get_record_list', 'get_file_json', 'set_root_password',
            'set_anti_conf', 'get_anti_conf', 'get_sshd_anti_logs', 'del_ban_ip', "remove_video_record",
            'get_sys_user', 'add_sys_user', 'del_sys_user', 'set_user_send', 'get_user_send', "get_record_video")
    return publicObject(firewallObject, defs, None, pdata, is_csrf)


@app.route('/monitor', methods=method_all)
def panel_monitor(pdata=None):
    # 云控统计信息
    comReturn = comm.local()
    if comReturn: return comReturn
    if comm.get_sk(): return abort(404)
    import monitor
    dataObject = monitor.Monitor()
    defs = ('get_spider', 'get_exception', 'get_request_count_qps',
            'load_and_up_flow', 'get_request_count_by_hour')
    return publicObject(dataObject, defs, None, pdata)


@app.route('/san', methods=method_all)
def san_baseline(pdata=None):
    # 云控安全扫描
    comReturn = comm.local()
    if comReturn: return comReturn
    if comm.get_sk(): return abort(404)
    import san_baseline
    dataObject = san_baseline.san_baseline()
    defs = ('start', 'get_api_log', 'get_resut', 'get_ssh_errorlogin',
            'repair', 'repair_all')
    return publicObject(dataObject, defs, None, pdata)


@app.route('/password', methods=method_all)
def panel_password(pdata=None):
    # 云控密码管理
    comReturn = comm.local()
    if comReturn: return comReturn
    if comm.get_sk(): return abort(404)
    import password
    dataObject = password.password()
    defs = ('set_root_password', 'get_mysql_root', 'set_mysql_password',
            'set_panel_password', 'SetPassword', 'SetSshKey', 'StopKey',
            'GetConfig', 'StopPassword', 'GetKey', 'get_databses',
            'rem_mysql_pass', 'set_mysql_access', "get_panel_username")
    return publicObject(dataObject, defs, None, pdata)


@app.route('/warning', methods=method_all)
def panel_warning(pdata=None):
    # 首页安全警告
    comReturn = comm.local()
    if comReturn: return comReturn
    if public.get_csrf_html_token_key() in session and 'login' in session:
        if not check_csrf():
            return public.ReturnJson(False, 'INIT_CSRF_ERR'), json_header
    get = get_input()
    ikey = 'warning_list'
    import panelWarning
    dataObject = panelWarning.panelWarning()
    if get.action == 'get_list':
        result = cache.get(ikey)
        if not result or 'force' in get:
            result = json.loads('{"ignore":[],"risk":[],"security":[]}')
            try:

                defs = ("get_list",)
                result = publicObject(dataObject, defs, None, pdata)
                cache.set(ikey, result, 3600)
                return result
            except:
                pass
        return result

    defs = ('get_list', 'set_ignore', 'get_result', 'check_find', 'check_cve', 'set_vuln_ignore', 'get_scan_bar', 'get_tmp_result',
            'kill_get_list')
    if get.action in ['set_ignore', 'check_find', 'set_vuln_ignore']:
        cache.delete(ikey)
    return publicObject(dataObject, defs, None, pdata)


@app.route('/bak', methods=method_all)
def backup_bak(pdata=None):
    # 云控备份服务
    comReturn = comm.local()
    if comReturn: return comReturn
    if comm.get_sk(): return abort(404)
    import backup_bak
    dataObject = backup_bak.backup_bak()
    defs = ('get_sites', 'get_databases', 'backup_database', 'backup_site',
            'backup_path', 'get_database_progress', 'get_site_progress',
            'down', 'get_down_progress', 'download_path', 'backup_site_all',
            'get_all_site_progress', 'backup_date_all',
            'get_all_date_progress')
    return publicObject(dataObject, defs, None, pdata)


@app.route('/abnormal', methods=method_all)
def abnormal(pdata=None):
    # 云控系统统计
    comReturn = comm.local()
    if comReturn: return comReturn
    if comm.get_sk(): return abort(404)
    import abnormal
    dataObject = abnormal.abnormal()
    defs = ('mysql_server', 'mysql_cpu', 'mysql_count', 'php_server',
            'php_conn_max', 'php_cpu', 'CPU', 'Memory', 'disk',
            'not_root_user', 'start')
    return publicObject(dataObject, defs, None, pdata)


@app.route('/project/<mod_name>/<def_name>/<stype>', methods=method_all)
def project(mod_name, def_name, stype=None):
    comReturn = comm.local()
    if comReturn: return comReturn
    from panelProjectController import ProjectController
    project_obj = ProjectController()
    defs = ('model',)
    get = get_input()
    get.action = 'model'
    get.mod_name = mod_name
    get.def_name = def_name
    get.stype = stype
    if stype == "html":
        return project_obj.model(get)
    return publicObject(project_obj, defs, None, get)


@app.route('/msg/<mod_name>/<def_name>', methods=method_all)
def msgcontroller(mod_name, def_name):
    comReturn = comm.local()
    if comReturn: return comReturn
    from MsgController import MsgController
    project_obj = MsgController()
    defs = ('model',)
    get = get_input()
    get.action = 'model'
    get.mod_name = mod_name
    get.def_name = def_name
    return publicObject(project_obj, defs, None, get)


@app.route('/docker', methods=method_all)
@app.route('/docker/<action>/', methods=method_all)
@app.route('/docker/<action>', methods=method_all)
@app.route('/docker_ifame', methods=method_all)
def docker(action=None, pdata=None):
    if not public.is_bind():
        return redirect('/bind', 302)
    comReturn = comm.local()
    if comReturn: return comReturn
    if request.method == method_get[0]:
        import system
        data = system.system().GetConcifInfo()
        data['js_random'] = get_js_random()
        data['lan'] = public.GetLan('files')
        return render_template('index1.html', data=data)


@app.route('/dbmodel/<mod_name>/<def_name>', methods=method_all)
def dbmodel(mod_name, def_name):
    comReturn = comm.local()
    if comReturn: return comReturn
    from panelDatabaseController import DatabaseController
    database_obj = DatabaseController()
    defs = ('model',)
    get = get_input()
    get.action = 'model'
    get.mod_name = mod_name
    get.def_name = def_name

    return publicObject(database_obj, defs, None, get)


@app.route('/files', methods=method_all)
@app.route('/files_ifame', methods=method_all)
def files(pdata=None):
    # 文件管理
    comReturn = comm.local()
    if comReturn: return comReturn
    if request.method == method_get[0] and not request.args.get(
            'path') and not pdata:
        import system
        data = system.system().GetConcifInfo()
        data['recycle_bin'] = os.path.exists('data/recycle_bin.pl')
        data['lan'] = public.GetLan('files')
        data['js_random'] = get_js_random()
        if request.path in ['/files_ifame']:
            return render_template('files.html', data=data)
        return render_template('index1.html', data=data)

    import files
    filesObject = files.files()
    defs = ('CheckExistsFiles', 'GetExecLog', 'GetSearch', 'ExecShell',
            'GetExecShellMsg', 'exec_git', 'exec_composer',
            'create_download_url', 'get_images_resize', 'UploadFile', 'GetDir',
            'CreateFile', 'CreateDir', 'DeleteDir', 'DeleteFile',
            'get_download_url_list', 'remove_download_url',
            'modify_download_url', 'CopyFile', 'CopyDir', 'MvFile',
            'GetFileBody', 'SaveFileBody', 'Zip', 'UnZip', 'ZipAndDownload',
            'get_download_url_find', 'set_file_ps', 'CreateLink',
            'add_files_rsync', 'SearchFiles', 'upload', 'read_history',
            're_history', 'auto_save_temp', 'get_auto_save_body', 'get_videos',
            'GetFileAccess', 'SetFileAccess', 'GetDirSize', 'SetBatchData',
            'BatchPaste', 'install_rar', 'get_path_size', 'get_file_attribute',
            'get_file_hash', 'DownloadFile', 'GetTaskSpeed', 'CloseLogs',
            'InstallSoft', 'UninstallSoft', 'SaveTmpFile',
            'get_composer_version', 'exec_composer', 'update_composer',
            'GetTmpFile', 'del_files_store', 'add_files_store',
            'get_files_store', 'del_files_store_types',
            'add_files_store_types', 'exec_git', 'upload_file_exists',
            'RemoveTask', 'ActionTask', 'Re_Recycle_bin', 'Get_Recycle_bin',
            'Del_Recycle_bin', 'Close_Recycle_bin', 'Recycle_bin',
            'file_webshell_check', 'dir_webshell_check', 'files_search', 'download_file',
            'files_replace', 'get_replace_logs', 'send_baota', 'get_dir_down_total',
            'GetFileHistory', "get_bt_sync_status", "mutil_unzip", "test_path",
            'SplitFile', 'JoinConfigFile', 'JoinFile',  # 切割文件，合并文件
            'file_history', 'file_history_list', 'del_file_history', 'list_backups', 'restore_backup', 'delete_backup', 'download_backup', 'get_backup_config', 'edit_backup_config','set_backup_status',
            'SearchFilesData', 'update_cors_config', 'delete_cors_config', 'view_cors_config',
            'merge_split_file', 'get_zip_status', 'GetDirNew','upload_files_exists', 'del_history', 'Del_Recycle_bin_new', 'Close_Recycle_bin_new', 'Batch_Del_Recycle_bin'
            )
    return publicObject(filesObject, defs, None, pdata)


@app.route('/crontab', methods=method_all)
@app.route('/crontab/<action>/', methods=method_all)
@app.route('/crontab/<action>', methods=method_all)
def crontab(action=None,pdata=None):
    # 计划任务
    comReturn = comm.local()
    if comReturn: return comReturn
    if request.method == method_get[0] and not pdata and not request.args:
        import system
        data = system.system().GetConcifInfo()
        data['lan'] = public.GetLan('crontab')
        data['js_random'] = get_js_random()
        if request.path in ['/crontab_ifame']:
            return render_template('crontab.html', data=data)
        return render_template('index1.html', data=data)

    import crontab
    crontabObject = crontab.crontab()
    defs = (
        'set_cron_status_all', 'get_zone', 'get_domain', 'cancel_top', 'set_task_top', 'GetCrontab', 'AddCrontab',
        'GetDataList', 'GetLogs',
        'DelLogs', 'download_logs', 'clear_logs',
        'DelCrontab', 'StartTask', 'set_cron_status', 'get_crond_find', 'set_atuo_start_syssafe',
        'modify_crond', 'get_backup_list', 'check_url_connecte', 'cloud_backup_download',
        'GetDatabases', 'get_crontab_types', 'add_crontab_type', 'remove_crontab_type', 'modify_crontab_type_name', 'set_crontab_type', 'export_crontab_to_json', 'import_crontab_from_json',
        'set_rotate_log', 'get_rotate_log_config','set_rotate_log_status','get_restart_project_config', 'set_restart_project','set_execute_script','get_system_user_list','get_auto_config','set_auto_config','get_databases','get_log_path','get_local_backup_path','get_crontab_service','repair_crontab_service')
    return publicObject(crontabObject, defs, None, pdata)


@app.route('/soft', methods=method_all)
@app.route('/soft/<action>', methods=method_all)
@app.route('/soft/<action>/', methods=method_all)
def soft(action=None,pdata=None):
    # 软件商店页面
    comReturn = comm.local()
    if comReturn: return comReturn
    import system
    data = system.system().GetConcifInfo()
    data['lan'] = public.GetLan('soft')
    data['js_random'] = get_js_random()
    is_bind()
    return render_template('index1.html', data=data)


@app.route('/config', methods=method_all)
@app.route('/config/<action>/', methods=method_all)
@app.route('/config/<action>', methods=method_all)
def config(action=None,pdata=None):
    # 面板设置页面
    comReturn = comm.local()
    if comReturn: return comReturn

    if request.method == method_get[0] and not pdata:
        import system, wxapp, config
        c_obj = config.config()
        data = system.system().GetConcifInfo()
        data['lan'] = public.GetLan('config')
        try:
            data['wx'] = wxapp.wxapp().get_user_info(None)['msg']
        except:
            data['wx'] = 'INIT_WX_NOT_BIND'
        data['api'] = ''
        data['ipv6'] = ''
        sess_out_path = 'data/session_timeout.pl'
        if not os.path.exists(sess_out_path):
            public.writeFile(sess_out_path, '86400')
        s_time_tmp = public.readFile(sess_out_path)
        s_time = int(s_time_tmp)
        if s_time % 86400 == 0 and s_time >= 86400:
            show_time = str(s_time // 86400) + '天'
        else:
            show_time = str(s_time // 3600) + '小时'
        data['session_timeout'] = show_time
        data["left_title"] = public.readFile("data/title.pl") if os.path.exists("data/title.pl") else ""
        if c_obj.get_ipv6_listen(None): data['ipv6'] = 'checked'
        if c_obj.get_token(None)['open']: data['api'] = 'checked'
        data['basic_auth'] = c_obj.get_basic_auth_stat(None)
        data['status_code'] = c_obj.get_not_auth_status()
        data['basic_auth']['value'] = public.getMsg('CLOSED')
        if data['basic_auth']['open']:
            data['basic_auth']['value'] = public.getMsg('OPENED')
        data['debug'] = ''
        data['show_recommend'] = not os.path.exists('data/not_recommend.pl')
        data['show_workorder'] = not os.path.exists('data/not_workorder.pl')
        data['notice_risk_ignore'] = c_obj.get_notice_risk_ignore()
        data['js_random'] = get_js_random()
        if app.config['DEBUG']: data['debug'] = 'checked'
        data['is_local'] = ''
        if public.is_local(): data['is_local'] = 'checked'
        is_bind()
        
        return render_template('index1.html', data=data)

    import config
    defs = (
        'setlastPassword', 'set_file_deny', 'del_file_deny', 'get_file_deny', 'set_improvement',
        'get_ols_private_cache_status', 'get_ols_value', 'set_ols_value',
        'get_ols_private_cache', 'get_ols_static_cache', 'get_nps_new', 'write_nps_new',
        'set_ols_static_cache', 'switch_ols_private_cache',
        'set_ols_private_cache', 'set_coll_open', 'get_qrcode_data',
        'check_two_step', 'set_two_step_auth', 'create_user', 'remove_user',
        'modify_user', 'set_click_logs', 'get_node_config', 'set_node_config',
        'get_key', 'get_php_session_path', 'set_php_session_path',
        'get_cert_source', 'get_users', 'set_local', 'set_debug',
        'get_panel_error_logs', 'clean_panel_error_logs', 'get_menu_list',
        'set_hide_menu_list', 'get_basic_auth_stat', 'set_basic_auth', 'set_recommend_show',
        'get_cli_php_version', 'get_tmp_token', 'get_temp_login',
        'set_temp_login', 'remove_temp_login', 'clear_temp_login',
        'get_temp_login_logs', 'set_request_iptype', 'set_request_type',
        'set_cli_php_version', 'DelOldSession', 'GetSessionCount',
        'SetSessionConf', 'show_recommend', 'show_workorder', 'GetSessionConf',
        'get_ipv6_listen', 'set_ipv6_status', 'GetApacheValue',
        'SetApacheValue', 'GetNginxValue', 'SetNginxValue', 'get_token',
        'set_token', 'set_admin_path', 'is_pro', 'set_not_auth_status',
        'get_php_config', 'get_config', 'SavePanelSSL', 'GetPanelSSL',
        'GetPHPConf', 'SetPHPConf', 'GetPanelList', 'AddPanelInfo',
        'SetPanelInfo', 'DelPanelInfo', 'ClickPanelInfo', 'SetPanelSSL',
        'SetTemplates', 'Set502', 'setPassword', 'setUsername', 'setPanel',
        'setPathInfo', 'setPHPMaxSize', 'getFpmConfig', 'setFpmConfig',
        'setPHPMaxTime', 'syncDate', 'syncDateCrontab', 'setPHPDisable', 'SetControl',
        'ClosePanel', 'AutoUpdatePanel', 'SetPanelLock', 'return_mail_list',
        'del_mail_list', 'add_mail_address', 'user_mail_send', 'get_user_mail',
        'set_dingding', 'get_dingding', 'get_settings', 'user_stmp_mail_send',
        'user_dingding_send', 'get_login_send', 'set_login_send', 'set_empty',
        'clear_login_send', 'get_login_log', 'login_ipwhite', 'set_ssl_verify',
        'get_ssl_verify', 'get_password_config', 'set_password_expire',
        'set_password_safe', "get_msg_configs", "get_module_template",
        "install_msg_module", "uninstall_msg_module", "set_msg_config",
        "set_default_channel", "get_msg_fun", "get_msg_push_list",
        "get_msg_configs_by", "get_login_area", "set_login_area", "set_table_header",
        "get_login_area_list", "clear_login_list", "get_nps", "write_nps", "stop_nps", "Get_debug",
        "set_limit_area", "get_limit_area", "get_table_header", "Get_debug",
        "set_left_title", "set_status_info", "get_status_info", "set_popularize",
        "get_memo_body", "delete_ua", "modify_ua", "modify_ua", "get_limit_ua", "set_ua",
        "get_nps_info","balance_pay_cert","err_collection","GetPhpPeclLog","phpPeclInstall",
        "phpPeclUninstall","GetPeclInstallList","set_login_origin",
				"get_panel_theme","set_panel_theme","update_panel_theme","validate_theme_file","import_theme_config","export_theme_config","get_export_file_info",
        "SetNoticeIgnore", "get_versionnumber",
    )

    return publicObject(config.config(), defs, None, pdata)


@app.route('/ajax', methods=method_all)
def ajax(pdata=None):
    # 面板系统服务状态接口
    comReturn = comm.local()
    if comReturn: return comReturn


    import ajax
    ajaxObject = ajax.ajax()
    defs = ('get_lines', 'php_info', 'change_phpmyadmin_ssl_port',
            'set_phpmyadmin_ssl', 'get_phpmyadmin_ssl', 'get_pd',
            'get_pay_type', 'check_user_auth', 'to_not_beta', 'get_beta_logs',
            'apple_beta', 'GetApacheStatus', 'GetCloudHtml',
            'get_load_average', 'GetOpeLogs', 'GetFpmLogs', 'GetFpmSlowLogs',
            'SetMemcachedCache', 'GetMemcachedStatus', 'GetRedisStatus',
            'GetWarning', 'SetWarning', 'CheckLogin', 'GetSpeed', 'GetAd',
            'phpSort', 'ToPunycode', 'GetBetaStatus', 'SetBeta',
            'setPHPMyAdmin', 'delClose', 'KillProcess', 'GetPHPInfo',
            'GetQiniuFileList', 'get_process_tops', 'get_process_cpu_high',
            'UninstallLib', 'InstallLib', 'SetQiniuAS', 'GetQiniuAS',
            'GetLibList', 'GetProcessList', 'GetNetWorkList', 'GetNginxStatus',
            'GetPHPStatus', 'GetTaskCount', 'GetSoftList', 'GetNetWorkIo',
            'GetDiskIo', 'GetCpuIo', 'ignore_version', 'CheckInstalled',
            'UpdatePanel', 'GetInstalled', 'GetPHPConfig', 'SetPHPConfig',
            'log_analysis', 'speed_log', 'get_result', 'get_detailed',
            'check_auth_ip', 'get_panel_error_info', 'Clean_bt_host', 'GetNetWorkIoByDay',
            'Set_bt_host', 'Get_ip_info', 'reGetCloudPHPExt', 'GetMysqlAlarmInfo', 'set_cron_task', 'get_cron_task','phpmyadmin_client_check',
            'remove_analysis')

    return publicObject(ajaxObject, defs, None, pdata)


@app.route('/system', methods=method_all)
def system(pdata=None):
    # 面板系统状态接口
    comReturn = comm.local()
    if comReturn: return comReturn
    import system
    sysObject = system.system()
    defs = ('get_io_info', 'UpdatePro', 'GetAllInfo', 'GetNetWorkApi',
            'GetLoadAverage', 'ClearSystem', 'GetNetWorkOld', 'GetNetWork',
            'GetDiskInfo', 'GetCpuInfo', 'GetBootTime', 'GetSystemVersion',
            'GetMemInfo', 'GetSystemTotal', 'GetConcifInfo', 'ServiceAdmin',
            'ReWeb', 'RestartServer', 'ReMemory', 'RepPanel','set_rname','ReloadWeb','reload_task',
            'repair_panel','upgrade_panel','get_upgrade_log', 'upgrade_env', 'upgrade_env_log',
            'GetTemplateOverview', 'GetOverview', 'AddOverview', 'SetOverview', 'DelOverview'  # 首页概览
            )
    return publicObject(sysObject, defs, None, pdata)


@app.route('/deployment', methods=method_all)
def deployment(pdata=None):
    # 一键部署接口
    comReturn = comm.local()
    if comReturn: return comReturn
    import plugin_deployment
    sysObject = plugin_deployment.plugin_deployment()
    defs = ('GetList', 'GetSiteList', 'AddPackage', 'DelPackage',
            'SetupPackage', 'GetSpeed', 'GetPackageOther', 'GetJarPath', 'GetInLog', 'check_project_env'
            )
    return publicObject(sysObject, defs, None, pdata)


@app.route('/data', methods=method_all)
@app.route('/panel_data', methods=method_all)
def panel_data(pdata=None):
    # 从数据库获取数据接口
    comReturn = comm.local()
    if comReturn: return comReturn
    import data
    dataObject = data.data()
    defs = ('setPs', 'getData', 'getFind', 'getKey', 'setSort', 'removrSort', 'get_https_port', 'set_https_port', 'del_sorted', 'get_site_num')
    return publicObject(dataObject, defs, None, pdata)

@app.route('/mail', methods=method_all)
@app.route('/mail/<action>', methods=method_all)
@app.route('/mail/<action>/', methods=method_all)
def mail(action=None,pdata=None):
    # 图标
    comReturn = comm.local()
    if comReturn: return comReturn
    is_bind()
    return render_template('index1.html', data={})


@app.route('/wp', methods=method_all)
@app.route('/wp/<action>', methods=method_all)
@app.route('/wp/<action>/', methods=method_all)
def wp(action=None,pdata=None):
    # 图标
    comReturn = comm.local()
    if comReturn: return comReturn
    is_bind()
    return render_template('index1.html', data={})

@app.route('/node', methods=method_all)
@app.route('/node/<action>', methods=method_all)
@app.route('/node/<action>/', methods=method_all)
def node(action=None,pdata=None):
    # 图标
    comReturn = comm.local()
    if comReturn: return comReturn
    is_bind()
    return render_template('index1.html', data={})

@app.route('/domain', methods=method_all)
@app.route('/domain/<action>', methods=method_all)
@app.route('/domain/<action>/', methods=method_all)
def domain(action=None,pdata=None):
    # 图标
    comReturn = comm.local()
    if comReturn: return comReturn
    is_bind()
    return render_template('index1.html', data={})

@app.route('/vhost', methods=method_all)
@app.route('/vhost/<action>', methods=method_all)
@app.route('/vhost/<action>/', methods=method_all)
def vhost(action=None,pdata=None):
    # 图标
    comReturn = comm.local()
    if comReturn: return comReturn
    is_bind()
    return render_template('index1.html', data={})


@app.route('/ssl', methods=method_all)
@app.route('/ssl/<action>', methods=method_all)
def ssl(action=None,pdata=None):
    # 商业SSL证书申请接口
    comReturn = comm.local()
    if comReturn: return comReturn
    import panelSSL

    if request.method == method_get[0]:
        if request.args.get('action') not in ['download_cert']:
            data = {}
            return render_template('index1.html', data=data)

    toObject = panelSSL.panelSSL()
    defs = ('check_url_txt', 'RemoveCert', 'renew_lets_ssl', 'SetCertToSite',
            'SetBatchCertToSite', 'GetSiteDomain', 'GetCertList', 'SaveCert',
            'GetCert', 'GetCertName', 'again_verify', 'cancel_cert_order',
            'get_cert_admin', 'apply_order_ca', 'DelToken', 'GetToken',
            'GetUserInfo', 'GetOrderList', 'GetDVSSL', 'Completed',
            'SyncOrder', 'download_cert', 'set_cert', 'cancel_cert_order',
            'ApplyDVSSL', 'apply_cert_order_pay', 'get_order_list',
            'get_order_find', 'apply_order_pay', 'get_pay_status',
            'apply_order', 'get_verify_info', 'get_verify_result',
            'get_product_list', 'set_verify_info', 'renew_cert_order',
            'GetSSLInfo', 'downloadCRT', 'GetSSLProduct', 'Renew_SSL',
            'Get_Renew_SSL', 'GetAuthToken', 'GetBindCode',
            'apply_cert_install_pay', 'check_ssl_method',
            'get_product_list_v2', 'get_cert_list', 'get_cert_info',
            'upload_cert_to_cloud', 'remove_cloud_cert','get_ssl_ps','set_ssl_ps','apply_order_byca'
            , 'TencentcloudMarketAuth', 'TencentcloudMarketAuthLogin', 'GetCloudType', 'GetAuthUrl', 'AuthLogin'
            , 'soft_release', 'batch_soft_release', 'get_order_details','set_auto_renew_cert'
            , 'GetWechatAuthUrl', 'SetWechatBindUser'
            )
    get = get_input()

    if get.action == 'download_cert':
        from io import BytesIO
        import base64
        result = toObject.download_cert(get)
        fp = BytesIO(base64.b64decode(result['data']))
        return send_file(fp,
                         download_name=result['filename'],
                         as_attachment=True,
                         mimetype='application/zip')
    result = publicObject(toObject, defs, get.action, get)
    return result

@app.route('/task', methods=method_all)
def task(pdata=None):
    # 后台任务接口
    comReturn = comm.local()
    if comReturn: return comReturn
    import panelTask
    toObject = panelTask.bt_task()
    defs = ('get_task_lists', 'remove_task', 'get_task_find',
            "get_task_log_by_id")
    result = publicObject(toObject, defs, None, pdata)
    return result


@app.route('/plugin', methods=method_all)
def plugin(pdata=None):
    # 插件系统接口
    comReturn = comm.local()
    if comReturn: return comReturn
    import panelPlugin
    pluginObject = panelPlugin.panelPlugin()
    defs = ('set_score', 'get_score', 'update_zip', 'input_zip', 'export_zip',
            'add_index', 'remove_index', 'sort_index', 'install_plugin',
            'uninstall_plugin', 'get_soft_find', 'get_index_list',
            'get_soft_list', 'get_cloud_list', 'get_soft_list_thread',
            'check_deps', 'flush_cache', 'GetCloudWarning', 'install',
            'unInstall', 'getPluginList', 'getPluginInfo', 'repair_plugin',
            'upgrade_plugin', 'get_make_args', 'add_make_args',
            'input_package', 'export_zip', 'get_download_speed',
            'get_usually_plugin', 'get_plugin_upgrades', 'close_install',
            'getPluginStatus', 'setPluginStatus', 'a', 'getCloudPlugin',
            'getConfigHtml', 'savePluginSort', 'del_make_args',
            'set_make_args', 'get_cloud_list_status', 'is_verify_unbinding',
            'push_plugin', "check_plugin_settings", "save_plugin_settings",
            "load_plugin_settings", "set_plugin_ignore", "get_plugin_ignore", "RegetCloudPHPExt")
    return publicObject(pluginObject, defs, None, pdata)


@app.route('/wxapp', methods=method_all)
@app.route('/panel_wxapp', methods=method_all)
def panel_wxapp(pdata=None):
    # 微信小程序绑定接口
    comReturn = comm.local()
    if comReturn: return comReturn
    import wxapp
    toObject = wxapp.wxapp()
    defs = ('blind', 'get_safe_log', 'blind_result', 'get_user_info',
            'blind_del', 'blind_qrcode')
    result = publicObject(toObject, defs, None, pdata)
    return result


@app.route('/auth', methods=method_all)
def auth(pdata=None):
    # 面板认证接口
    comReturn = comm.local()
    if comReturn: return comReturn
    import panelAuth
    toObject = panelAuth.panelAuth()
    defs = ('get_plugin_remarks', 'get_re_order_status_plugin',
            'create_plugin_other_order', 'get_order_stat',
            'get_voucher_plugin', 'create_order_voucher_plugin',
						'get_auth_bind_num',
            'get_product_discount_by', 'get_re_order_status',
            'create_order_voucher', 'create_order', 'get_order_status',
            'get_voucher', 'flush_pay_status', 'create_serverid',
            'check_serverid', 'get_plugin_list', 'check_plugin',
            'get_buy_code', 'check_pay_status', 'get_wx_order_status',
            'get_renew_code', 'check_renew_code', 'get_business_plugin',
            'get_ad_list', 'check_plugin_end', 'get_plugin_price', 'get_apply_copon', 'get_coupon_list', 'ignore_coupon_time',
            'set_user_adviser', 'rest_unbind_count', 'unbind_authorization', 'get_all_voucher_plugin',
            'get_pay_unbind_count', 'get_coupons', 'get_credits', 'create_with_credit_by_panel', 'get_last_paid_time', 'receive_products', 'get_free_activity_info')
    result = publicObject(toObject, defs, None, pdata)
    return result


@app.route('/download', methods=method_get)
def download():
    # 文件下载接口
    comReturn = comm.local()
    if comReturn: return comReturn
    filename = request.args.get('filename')
    if filename.find('|') != -1:
        filename = filename.split('|')[1]
    if not filename:
        return public.ReturnJson(False, "INIT_ARGS_ERR"), json_header
    if filename in [
        'alioss', 'qiniu', 'upyun', 'txcos', 'ftp', 'msonedrive',
        'gcloud_storage', 'gdrive', 'aws_s3', 'obs', 'bos'
    ]:
        return panel_cloud(False)
    import html
    filename = html.unescape(filename)
    try:
        import stat
        file_stat = os.stat(filename)
        if stat.S_ISSOCK(file_stat.st_mode):
            return public.ReturnJson(False, "Unix 域套接字文件不可下载"), json_header
        elif stat.S_ISCHR(file_stat.st_mode):
            return public.ReturnJson(False, "字符设备文件不可下载"), json_header
        elif stat.S_ISBLK(file_stat.st_mode):
            return public.ReturnJson(False, "块设备文件不可下载"), json_header
        elif stat.S_ISFIFO(file_stat.st_mode):
            return public.ReturnJson(False, "FIFO 管道文件不可下载"), json_header
    except:
        pass
    if os.path.isdir(filename):
        return public.ReturnJson(False, "目录不可以下载！"), json_header
    if not os.path.exists(filename):
        return public.ReturnJson(False, "FILE_NOT_EXISTS"), json_header

    if request.args.get('play') == 'true':
        import panelVideo
        start, end = panelVideo.get_range(request)
        return panelVideo.partial_response(filename, start, end)
    else:
        mimetype = "application/octet-stream"
        extName = filename.split('.')[-1]
        if extName in ['png', 'gif', 'jpeg', 'jpg']: mimetype = None
        public.WriteLog("TYPE_FILE", 'FILE_DOWNLOAD', (filename, public.GetClientIp()))
        if not os.path.exists(filename):
            return public.ReturnJson(False, "FILE_NOT_EXISTS"), json_header
        return send_file(filename,
                         mimetype=mimetype,
                         as_attachment=True,
                         etag=True,
                         conditional=True,
                         download_name=os.path.basename(filename),
                         max_age=0)


@app.route('/down/<token>', methods=method_all)
def down(token=None, fname=None):
    # 文件分享对外接口

    try:
        if public.M('download_token').count() == 0: return abort(404)
        fname = request.args.get('fname')
        if fname:
            if (len(fname) > 256): return abort(404)
        if fname: fname = fname.strip('/')
        if not token: return abort(404)
        if len(token) > 48: return abort(404)
        char_list = [
            '\\', '/', ':', '*', '?', '"', '<', '>', '|', ';', '&', '`'
        ]
        for char in char_list:
            if char in token: return abort(404)
        if not request.args.get('play') in ['true', None, '']:
            return abort(404)
        args = get_input()
        v_list = ['fname', 'play', 'file_password', 'data', 'down']
        for n in args.__dict__.keys():
            if not n in v_list:
                return public.returnJson(False, '不能存在多余参数'), json_header
        if not re.match(r"^[\w\.]+$", token): return abort(404)
        find = public.M('download_token').where('token=?', (token,)).find()
        if not isinstance(find["ps"], str):
            find["ps"] = str(int(find["ps"]))

        if not find: return abort(404)
        if time.time() > int(find['expire']): return abort(404)

        if not os.path.exists(find['filename']): return abort(404)
        if find['password'] and not token in session:
            pdata = {
                "to_path": "",
                "src_path": find['filename'],
                "password": True,
                "filename": find['filename'].split('/')[-1],
                "ps": find['ps'],
                "total": find['total'],
                "token": find['token'],
                "expire": public.format_date(times=find['expire']),
                "err_msg": ""
            }
            if 'file_password' in args:
                if not re.match(r"^\w+$", args.file_password):
                    # return public.ReturnJson(False, '密码错误-1!'), json_header
                    pdata["err_msg"] = "提取码格式错误"
                    return render_template('down.html', data=pdata)
                if args.file_password != str(find['password']) and args.file_password + ".0" != str(find['password']):
                    # return public.ReturnJson(False, '密码错误-2!'), json_header
                    pdata["err_msg"] = "提取码错误"
                    return render_template('down.html', data=pdata)
                session[token] = 1
                session['down'] = True
            else:
                session['down'] = True
                return render_template('down.html', data=pdata)

        if not find['password']:
            session['down'] = True
            session[token] = 1

        if session[token] != 1:
            return abort(404)

        filename = find['filename']
        if fname:
            filename = os.path.join(filename, fname)
            if not public.path_safe_check(fname, False): return abort(404)
            if not os.path.exists(filename):
                filename = os.path.join(os.path.dirname(find['filename']), fname)
            if os.path.isdir(filename):
                return get_dir_down(filename, token, find)
        else:
            if os.path.isdir(filename):
                return get_dir_down(filename, token, find)

        if request.args.get('play') == 'true':
            import panelVideo
            start, end = panelVideo.get_range(request)
            return panelVideo.partial_response(filename, start, end)
        else:
            filename = find['filename']
            if os.path.isdir(filename):
                filename = os.path.join(filename, fname)
            if request.args.get('play') == 'true':
                import panelVideo
                start, end = panelVideo.get_range(request)
                return panelVideo.partial_response(filename, start, end)
            else:
                import files
                if request.args.get('play') == 'true':
                    pdata = files.files().get_videos(args)
                    return public.GetJson(pdata), json_header
                if not request.args.get('down'):
                    mimetype = "application/octet-stream"
                    extName = filename.split('.')[-1]
                    if extName in ['png', 'gif', 'jpeg', 'jpg']: mimetype = None
                    b_name = os.path.basename(filename)
                    file_download_num(filename, 1)
                    return send_file(filename,
                                     mimetype=mimetype,
                                     as_attachment=True,
                                     download_name=b_name,
                                     max_age=0)
                args = public.dict_obj()
                path = os.path.dirname(filename)
                args.path = path
                args.share = True
                b_name = os.path.basename(filename)
                to_path = filename.replace(find['filename'], '').strip('/')

                pdata = files.files().GetDir(args)
                pdata['DIR'] = []
                pdata['FILES'] = [i for i in pdata['FILES'] if b_name == i.split(';')[0]]
                pdata['token'] = token
                pdata['ps'] = find['ps']
                pdata['src_path'] = find['filename']
                pdata['to_path'] = to_path
                if find['expire'] < (time.time() + (86400 * 365 * 10)):
                    pdata['expire'] = public.format_date(times=find['expire'])
                else:
                    pdata['expire'] = '永久有效'
                pdata['filename'] = (find['filename'].split('/')[-1] + '/' +
                                     to_path).strip('/')
            return render_template('down.html', data=pdata, to_size=public.to_size, download_num=file_download_num)
    except:
        return abort(404)


@app.route('/cloud', methods=method_all)
def panel_cloud(is_csrf=True):
    # 从对像存储下载备份文件接口
    comReturn = comm.local()
    if comReturn: return comReturn
    if is_csrf:
        if not check_csrf():
            return public.ReturnJson(False, 'INIT_CSRF_ERR'), json_header
    get = get_input()
    _filename = get.filename
    plugin_name = ""
    if _filename.find('|') != -1:
        plugin_name = get.filename.split('|')[1]
        if "name" not in get: get.name = get.filename.split('|')[-1]
    else:
        plugin_name = get.filename

    if not os.path.exists('plugin/' + plugin_name + '/' + plugin_name +
                          '_main.py'):
        return public.returnJson(False, 'INIT_PLUGIN_NOT_EXISTS'), json_header
    public.package_path_append('plugin/' + plugin_name)
    plugin_main = __import__(plugin_name + '_main')
    public.mod_reload(plugin_main)
    tmp = eval("plugin_main.%s_main()" % plugin_name)
    if not hasattr(tmp, 'download_file'):
        return public.returnJson(False,
                                 'INIT_PLUGIN_NOT_DOWN_FUN'), json_header
    if not re.match(r"^[\w\.\/-]+$", get.name):
        return public.returnJson(False, 'FILE_NOT_EXISTS'), json_header
    download_url = tmp.download_file(get.name)
    if plugin_name == 'ftp':
        if download_url.find("ftp") != 0:
            download_url = "ftp://" + download_url
    else:
        if download_url.find('http') != 0:
            download_url = 'http://' + download_url

    if "toserver" in get and get.toserver == "true":
        download_dir = "/tmp/"
        if "download_dir" in get:
            download_dir = get.download_dir
        local_file = os.path.join(download_dir, get.name)

        input_from_local = False
        if "input_from_local" in get:
            input_from_local = True if get.input_from_local == "true" else False

        if input_from_local:
            if os.path.isfile(local_file):
                return {
                    "status": True,
                    "msg": "文件已存在，将优先从本地恢复。",
                    "task_id": -1,
                    "local_file": local_file
                }
        from panelTask import bt_task
        task_obj = bt_task()
        task_id = task_obj.create_task('下载文件', 1, download_url, local_file)
        return {
            "status": True,
            "msg": "下载任务创建成功。",
            "local_file": local_file,
            "task_id": task_id
        }

    return redirect(download_url)


@app.route('/software', methods=method_all)
def software(pdata=None):
    # 图标
    comReturn = comm.local()
    if comReturn: return comReturn
    return render_template('software.html', data={})


@app.route('/waf', methods=method_all)
@app.route('/waf_ifame', methods=method_all)
def waf(pdata=None):
    # 图标
    comReturn = comm.local()
    if comReturn: return comReturn
    return render_template('index1.html', data={})


@app.route('/total', methods=method_all)
def total(pdata=None):
    # 图标
    comReturn = comm.local()
    if comReturn: return comReturn
    return render_template('index1.html', data={})


@app.route('/btwaf_error', methods=method_get)
def btwaf_error():
    # 图标
    comReturn = comm.local()
    if comReturn: return comReturn
    get = get_input()
    p_path = os.path.join('/www/server/panel/plugin/', "btwaf")
    if not os.path.exists(p_path):
        if get.name == 'btwaf' and get.fun == 'index':
            return render_template('error3.html', data={})
    return render_template('error3.html', data={})


@app.route('/favicon.ico', methods=method_get)
def send_favicon():
    # 图标
    comReturn = comm.local()
    if comReturn: return abort(404)
    s_file = '/www/server/panel/BTPanel/static/favicon.ico'
    if not os.path.exists(s_file): return abort(404)
    return send_file(s_file, conditional=True, etag=True)


@app.route('/rspamd', defaults={'path': ''}, methods=method_all)
@app.route('/rspamd/<path:path>', methods=method_all)
def proxy_rspamd_requests(path):
    comReturn = comm.local()
    if comReturn: return comReturn
    # param = str(request.url).split('?')[-1]
    # if not param:
    #     param = ""
    param = "" if len(str(request.url).split('?')) < 2 else param[-1]
    import requests
    headers = {}
    for h in request.headers.keys():
        headers[h] = request.headers[h]
    if request.method == "GET":
        if re.search(r"\.(js|css)$", path):
            return send_file('/usr/share/rspamd/www/rspamd/' + path,
                             conditional=True,
                             etag=True)
        if path == "/":
            return send_file('/usr/share/rspamd/www/rspamd/',
                             conditional=True,
                             etag=True)
        url = "http://127.0.0.1:11334/rspamd/" + path + "?" + param
        for i in [
            'stat', 'auth', 'neighbours', 'list_extractors',
            'list_transforms', 'graph', 'maps', 'actions', 'symbols',
            'history', 'errors', 'check_selector', 'saveactions',
            'savesymbols', 'getmap'
        ]:
            if i in path:
                url = "http://127.0.0.1:11334/" + path + "?" + param
        req = requests.get(url, headers=headers, stream=True)
        return Resp(stream_with_context(req.iter_content()),
                    content_type=req.headers['content-type'])
    else:
        url = "http://127.0.0.1:11334/" + path
        for i in request.form.keys():
            data = '{}='.format(i)
        # public.writeFile('/tmp/2',data+"\n","a+")
        req = requests.post(url, data=data, headers=headers, stream=True)

        return Resp(stream_with_context(req.iter_content()),
                    content_type=req.headers['content-type'])


@app.route('/tips', methods=method_get)
def tips():
    # 提示页面
    # comReturn = comm.local()
    # if comReturn: return abort(404)
    if not 'admin_auth' in session:
        return abort(404)
    get = get_input()
    if len(get.__dict__.keys()) > 1: return abort(404)
    return render_template('tips.html')


# ======================普通路由区============================#

# ======================严格排查区域============================#

route_path = os.path.join(admin_path, '')
if not route_path: route_path = '/'
if route_path[-1] == '/': route_path = route_path[:-1]
if route_path[0] != '/': route_path = '/' + route_path


@app.route('/login', methods=method_all)
@app.route(route_path, methods=method_all)
@app.route(route_path + '/', methods=method_all)
def login():
    # 面板登录接口
    if os.path.exists('install.pl'): return redirect('/install')
    global admin_check_auth, admin_path, route_path
    is_auth_path = False
    if admin_path != '/bt' and os.path.exists(
            admin_path_file) and not 'admin_auth' in session:
        is_auth_path = True
    # 登录输入验证
    if request.method == method_post[0]:
        if is_auth_path:
            g.auth_error = True
            return public.error_not_login(None)
        v_list = ['username', 'password', 'code', 'vcode', 'cdn_url', 'safe_mode']
        for v in v_list:
            if v in ['username', 'password']: continue
            pv = request.form.get(v, '').strip()
            if v == 'cdn_url':
                if len(pv) > 32:
                    return public.returnMsg(False, '错误的参数长度!'), json_header
                if not re.match(r"^[\w\.-]+$", pv):
                    public.returnJson(False, '错误的参数格式'), json_header
                continue

            if not pv: continue
            p_len = 32
            if v == 'code': p_len = 4
            if v == 'vcode': p_len = 6
            if v == 'safe_mode': p_len = 1
            if len(pv) != p_len:
                if v == 'code':
                    return public.returnJson(False, '验证码长度错误'), json_header
                return public.returnJson(False, '错误的参数长度'), json_header
            if not re.match(r"^\w+$", pv):
                return public.returnJson(False, '错误的参数格式'), json_header

        for n in request.form.keys():
            if not n in v_list:
                return public.returnJson(False, '登录参数中不能有多余参数'), json_header

    get = get_input()
    import userlogin
    if hasattr(get, 'tmp_token'):
        result = userlogin.userlogin().request_tmp(get)
        return is_login(result)
    # 过滤爬虫
    if public.is_spider(): return abort(404)
    if hasattr(get, 'dologin'):
        login_path = '/login'
        if not 'login' in session: return public.error_not_login()
        if os.path.exists(admin_path_file): login_path = route_path
        if session['login'] != False:
            session['login'] = False
            client_ip = public.GetClientIp()
            remote_port = request.environ.get('REMOTE_PORT', None)
            if remote_port is None:
                remote_port = request.headers.get('X-Real-Port', None)

            if remote_port:
                log_message = '客户端：{}:{}，已手动退出面板'.format(client_ip, remote_port)
            else:
                log_message = '客户端：{}，已手动退出面板'.format(client_ip)

            public.WriteLog('用户登出', log_message)

            # public.WriteLog(
            #     '用户登出', '客户端：{}，已手动退出面板'.format(
            #         public.GetClientIp() + ":" + remote_port
            #         ))

            if 'tmp_login_expire' in session:
                s_file = 'data/session/{}'.format(session['tmp_login_id'])
                if os.path.exists(s_file):
                    os.remove(s_file)
            token_key = public.get_csrf_html_token_key()
            if token_key in session:
                del (session[token_key])
            session.clear()
            sess_file = 'data/sess_files/' + public.get_sess_key()
            if os.path.exists(sess_file):
                try:
                    os.remove(sess_file)
                except:
                    pass
            sess_tmp_file = public.get_full_session_file()
            if os.path.exists(sess_tmp_file): os.remove(sess_tmp_file)
            g.dologin = True
            return redirect(public.get_admin_path())

    if is_auth_path:
        if route_path != request.path and route_path + '/' != request.path:
            referer = request.headers.get('Referer', 'err')
            referer_tmp = referer.split('/')
            referer_path = referer_tmp[-1]
            if referer_path == '':
                referer_path = referer_tmp[-2]
            if route_path != '/' + referer_path:
                g.auth_error = True
                # return render_template('autherr.html')
                return public.error_not_login(None)

    session['admin_auth'] = True
    comReturn = common.panelSetup().init()
    if comReturn: return comReturn

    if request.method == method_post[0]:
        result = userlogin.userlogin().request_post(get)
        return is_login(result)

    if request.method == method_get[0]:
        result = userlogin.userlogin().request_get(get)
        if result:
            return result
        data = {}
        data['lan'] = public.GetLan('login')
        data['hosts'] = '[]'
        hosts_file = 'plugin/static_cdn/hosts.json'
        if os.path.exists(hosts_file):
            data['hosts'] = public.get_cdn_hosts()
            if type(data['hosts']) == dict:
                data['hosts'] = '[]'
            else:
                data['hosts'] = json.dumps(data['hosts'])
        data['app_login'] = os.path.exists('data/app_login.pl')
        public.cache_set(
            public.Md5(
                uuid.UUID(int=uuid.getnode()).hex[-12:] +
                public.GetClientIp()), 'check', 360)
        # 生成登录token
        last_key = 'last_login_token'
        last_time_key = 'last_login_token_time'
        s_time = int(time.time())
        if last_key in session and last_time_key in session:
            # 10秒内不重复生成token
            if s_time - session[last_time_key] > 10:
                session[last_key] = public.GetRandomString(32)
                session[last_time_key] = s_time
        else:
            session[last_key] = public.GetRandomString(32)
            session[last_time_key] = s_time

        data[last_key] = session[last_key]
        data['public_key'] = public.get_rsa_public_key()
        return render_template('login.html', data=data)


@app.route('/close', methods=method_get)
def close():
    # 面板已关闭页面
    if not os.path.exists('data/close.pl'): return redirect('/')
    data = {}
    data['lan'] = public.getLan('close')
    return render_template('close.html', data=data)


@app.route('/get_app_bind_status', methods=method_all)
def get_app_bind_status(pdata=None):
    # APP绑定状态查询
    if not public.check_app('app_bind'): return abort(404)
    get = get_input()
    if len(get.__dict__.keys()) > 2: return '存在无意义参数!'
    v_list = ['bind_token', 'data']
    for n in get.__dict__.keys():
        if not n in v_list:
            return public.returnJson(False, '不能存在多余参数'), json_header
    import panelApi
    api_object = panelApi.panelApi()
    return json.dumps(api_object.get_app_bind_status(get_input())), json_header


@app.route('/check_bind', methods=method_all)
def check_bind(pdata=None):
    # APP绑定查询
    if not public.check_app('app_bind'): return abort(404)
    get = get_input()
    if len(get.__dict__.keys()) > 4: return '存在无意义参数!'
    v_list = ['bind_token', 'client_brand', 'client_model', 'data']
    for n in get.__dict__.keys():
        if not n in v_list:
            return public.returnJson(False, '不能存在多余参数'), json_header
    import panelApi
    api_object = panelApi.panelApi()
    return json.dumps(api_object.check_bind(get_input())), json_header


@app.route('/code', methods=method_get)
def code():
    if not 'code' in session: return ''
    if not session['code']: return ''
    # 获取图片验证码
    try:
        import vilidate
    except:
        public.ExecShell("pip install Pillow -I")
        return "Pillow not install!"
    vie = vilidate.vieCode()
    codeImage = vie.GetCodeImage(80, 4)
    if sys.version_info[0] == 2:
        try:
            from cStringIO import StringIO
        except:
            from StringIO import StringIO
        out = StringIO()
    else:
        from io import BytesIO
        out = BytesIO()
    codeImage[0].save(out, "png")
    cache.set("codeStr", public.md5("".join(codeImage[1]).lower()), 180)
    cache.set("codeOut", 1, 0.1)
    out.seek(0)
    return send_file(out, mimetype='image/png', max_age=0)


def file_download_num(filename, num=0):
    if os.path.exists('/www/server/panel/data/download_num.json'):
        try:
            data = json.loads(public.readFile('/www/server/panel/data/download_num.json'))
        except:
            data = {}
    else:
        data = {}
    download_num = data.get(filename, 0)
    download_num += num
    data[filename] = download_num
    if num:
        public.writeFile('/www/server/panel/data/download_num.json', json.dumps(data))
    return download_num


@app.route('/database/<mod_name>/<def_name>', methods=method_all)
def databaseModel(mod_name, def_name):
    comReturn = comm.local()
    if comReturn: return comReturn
    from panelDatabaseController import DatabaseController
    project_obj = DatabaseController()
    defs = ('model',)
    get = get_input()
    get.action = 'model'
    get.mod_name = mod_name
    get.def_name = def_name

    return publicObject(project_obj, defs, None, get)


# 系统安全模型页面
@app.route('/safe/<mod_name>/<def_name>', methods=method_all)
def safeModel(mod_name, def_name):
    comReturn = comm.local()
    if comReturn: return comReturn
    from panelSafeController import SafeController
    project_obj = SafeController()
    defs = ('model',)
    get = get_input()
    get.action = 'model'
    get.mod_name = mod_name
    get.def_name = def_name

    return publicObject(project_obj, defs, None, get)


# 通用模型路由
@app.route('/<index>/<mod_name>/<def_name>', methods=method_all)
def allModule(index, mod_name, def_name):
    comReturn = comm.local()
    if comReturn: return comReturn

    # 如果不存在模型文件则检查是否为插件
    mod_file = "{}/class/{}Model/{}Model.py".format(public.get_panel_path(), index, mod_name)
    if not os.path.exists(mod_file):
        p_path = public.get_plugin_path() + '/' + index
        if os.path.exists(p_path):
            return panel_other(index, mod_name, def_name)

    from panelController import Controller
    controller_obj = Controller()
    defs = ('model',)
    get = get_input()
    get.model_index = index
    get.action = 'model'
    get.mod_name = mod_name
    get.def_name = def_name
    return publicObject(controller_obj, defs, None, get)


@app.route('/public', methods=method_all)
def panel_public():
    get = get_input()
    if len("{}".format(get.__dict__)) > 1024 * 32:
        return abort(404)

    # 获取ping测试
    if 'get_ping' in get:
        try:
            import panelPing
            p = panelPing.Test()
            get = p.check(get)
            if not get: return abort(404)
            result = getattr(p, get['act'])(get)
            result_type = type(result)
            if str(result_type).find('Response') != -1: return result
            return public.getJson(result), json_header
        except:
            return abort(404)

    if public.cache_get(
            public.Md5(
                uuid.UUID(int=uuid.getnode()).hex[-12:] +
                public.GetClientIp())) != 'check':
        return abort(404)
    global admin_check_auth, admin_path, route_path, admin_path_file
    if admin_path != '/bt' and os.path.exists(
            admin_path_file) and not 'admin_auth' in session:
        return abort(404)
    v_list = ['fun', 'name', 'filename', 'data', 'secret_key']
    for n in get.__dict__.keys():
        if not n in v_list:
            return abort(404)

    get.client_ip = public.GetClientIp()
    num_key = get.client_ip + '_wxapp'
    if not public.get_error_num(num_key, 10):
        return public.returnMsg(False, '连续10次认证失败，禁止1小时')
    if not hasattr(get, 'name'): get.name = ''
    if not hasattr(get, 'fun'): return abort(404)
    if not public.path_safe_check("%s/%s" % (get.name, get.fun)):
        return abort(404)
    if get.fun in ['login_qrcode', 'is_scan_ok', 'set_login']:
        # 检查是否验证过安全入口
        if admin_path != '/bt' and os.path.exists(
                admin_path_file) and not 'admin_auth' in session:
            return abort(404)
        # 验证是否绑定了设备
        if not public.check_app('app'):
            return public.returnMsg(False, '未绑定用户!')
        import wxapp
        pluwx = wxapp.wxapp()
        checks = pluwx._check(get)
        if type(checks) != bool or not checks:
            public.set_error_num(num_key)
            return public.getJson(checks), json_header
        data = public.getJson(eval('pluwx.' + get.fun + '(get)'))
        return data, json_header
    else:
        return abort(404)


"""
@name 面板SSL验证
@description 面板SSL验证
"""
@app.route('/.well-known/pki-validation/<name>.txt', methods=method_all)
def panel_ssl(name=None, fun=None):
    if not re.match(r"^[A-Za-z0-9]{32}$", name):
        return abort(404)

    check_file = '{}/.well-known/pki-validation/{}.txt'.format(panel_path,name)
    if not os.path.exists(check_file):
        return abort(404)

    return send_file(check_file, conditional=True, etag=True)



@app.route('/<name>/<fun>', methods=method_all)
@app.route('/<name>/<fun>/<path:stype>', methods=method_all)
def panel_other(name=None, fun=None, stype=None):

    if not public.is_bind():
        return redirect('/bind', 302)
    if public.is_error_path():
        return redirect('/error', 302)
    if not name: return abort(404)
    if not re.match(r"^[\w\-]+$", name): return abort(404)
    if fun and not re.match(r"^[\w\-\.]+$", fun): return abort(404)
    if name != "mail_sys" or fun != "send_mail_http.json":
        comReturn = comm.local()
        if comReturn: return comReturn
        if not stype:
            tmp = fun.split('.')
            fun = tmp[0]
            if len(tmp) == 1: tmp.append('')
            stype = tmp[1]
        if fun:
            if name == 'btwaf' and fun == 'index':
                pass
            elif name == 'firewall' and fun == 'get_file':
                pass
            elif fun == 'static':
                pass
            elif stype == 'html':
                pass
            else:
                if public.get_csrf_cookie_token_key(
                ) in session and 'login' in session:
                    if not check_csrf():
                        return public.ReturnJson(False,
                                                 'INIT_CSRF_ERR'), json_header
        args = None
    else:
        p_path = public.get_plugin_path() + '/' + name
        if not os.path.exists(p_path): return abort(404)
        args = get_input()
        args_list = [
            'mail_from', 'password', 'mail_to', 'subject', 'content',
            'subtype', 'data'
        ]
        for k in args.__dict__:
            if not k in args_list: return abort(404)

    if not fun: fun = 'index.html'
    if not stype:
        tmp = fun.split('.')
        fun = tmp[0]
        if len(tmp) == 1: tmp.append('')
        stype = tmp[1]

    if not name: name = 'coll'
    if not public.path_safe_check("%s/%s/%s" % (name, fun, stype)):
        return abort(404)
    if name.find('./') != -1 or not re.match(r"^[\w-]+$", name):
        return abort(404)
    if not name:
        return public.returnJson(False, 'PLUGIN_INPUT_ERR'), json_header
    p_path = public.get_plugin_path() + '/' + name
    if not os.path.exists(p_path):
        if name == 'btwaf' and fun == 'index':
            pdata = {}
            import PluginLoader
            plugin_list = PluginLoader.get_plugin_list(0)
            for p in plugin_list['list']:
                if p['name'] in ['btwaf']:
                    if p['endtime'] != 0 and p['endtime'] < time.time():
                        pdata['error_msg'] = 1
                        break
            return render_template('error3.html', data=pdata)
        return abort(404)

    # 是否响插件应静态文件
    if fun == 'static':
        if stype.find('./') != -1 or not os.path.exists(p_path + '/static'):
            return abort(404)
        s_file = p_path + '/static/' + stype
        if s_file.find('..') != -1: return abort(404)
        if not re.match(r"^[\w\./-]+$", s_file): return abort(404)
        if not public.path_safe_check(s_file): return abort(404)
        if not os.path.exists(s_file): return abort(404)
        return send_file(s_file, conditional=True, etag=True)

    # 准备参数
    if not args: args = get_input()
    args.client_ip = public.GetClientIp()
    args.fun = fun

    # 初始化插件对象
    try:
        import PluginLoader
        try:
            args.s = fun
            data = PluginLoader.plugin_run(name, fun, args)
            if isinstance(data, dict):
                if 'status' in data and data[
                    'status'] == False and 'msg' in data:
                    if isinstance(data['msg'], str):
                        if data['msg'].find('加载失败') != -1 or data['msg'].find(
                                'Traceback ') == 0:
                            raise public.PanelError(data['msg'])
        except Exception as ex:
            if name == 'btwaf' and fun == 'index' and str(ex).find(
                    '未购买') != -1:
                return render_template('error3.html', data={})
            return public.get_error_object(None, plugin_name=name)

        r_type = type(data)
        if r_type in [Response, Resp]:
            return data

        # 处理响应
        if stype == 'json':  # 响应JSON
            return public.getJson(data), json_header
        elif stype == 'html':  # 使用模板
            t_path_root = p_path + '/templates/'
            t_path = t_path_root + fun + '.html'
            if not os.path.exists(t_path):
                return public.returnJson(False,
                                         'PLUGIN_NOT_TEMPLATE'), json_header
            t_body = public.readFile(t_path)
            # 处理模板包含
            rep = r'{%\s?include\s"(.+)"\s?%}'
            includes = re.findall(rep, t_body)
            for i_file in includes:
                filename = p_path + '/templates/' + i_file
                i_body = 'ERROR: File ' + filename + ' does not exists.'
                if os.path.exists(filename):
                    i_body = public.readFile(filename)
                t_body = re.sub(rep.replace('(.+)', i_file), i_body, t_body)
            return render_template_string(t_body, data=data)
        else:  # 直接响应插件返回值,可以是任意flask支持的响应类型
            r_type = type(data)
            if r_type == dict:
                if name == 'btwaf' and 'msg' in data:
                    return render_template('error3.html',
                                           data={"error_msg": data['msg']})
                return public.returnJson(
                    False,
                    public.getMsg('PUBLIC_ERR_RETURN').format(
                        r_type)), json_header
            return data
    except:
        if not 'login' in session: return abort(404)
        return public.get_error_object(None, plugin_name=name)


@app.route('/hook', methods=method_all)
def panel_hook():
    # webhook接口
    get = get_input()
    if not os.path.exists('plugin/webhook'):
        return abort(404)
    if 'p' in get or 'limit' in get:
        return abort(404)
    public.package_path_append('plugin/webhook')
    import webhook_main
    res = webhook_main.webhook_main().RunHook(get)
    if res['code'] == 0: abort(404)
    return public.getJson(res)


@app.route('/install', methods=method_all)
def install():
    # 初始化面板接口
    if public.is_spider(): return abort(404)
    if not os.path.exists('install.pl'): return abort(404)
    if public.M('config').where("id=?", ('1',)).getField('status') == 1:
        if os.path.exists('install.pl'): os.remove('install.pl')
        session.clear()
        return abort(404)
    ret_login = os.path.join('/', admin_path)
    if admin_path == '/' or admin_path == '/bt': ret_login = '/login'
    session['admin_path'] = False
    session['login'] = False
    if request.method == method_get[0]:
        if not os.path.exists('install.pl'): return redirect(ret_login)
        data = {}
        data['status'] = os.path.exists('install.pl')
        data['username'] = public.GetRandomString(8).lower()
        return render_template('install.html', data=data)

    elif request.method == method_post[0]:
        if not os.path.exists('install.pl'): return redirect(ret_login)
        get = get_input()
        if not hasattr(get, 'bt_username'):
            return public.getMsg('INSTALL_USER_EMPTY')
        if not get.bt_username: return public.getMsg('INSTALL_USER_EMPTY')
        if not hasattr(get, 'bt_password1'):
            return public.getMsg('INSTALL_PASS_EMPTY')
        if not get.bt_password1: return public.getMsg('INSTALL_PASS_EMPTY')
        if get.bt_password1 != get.bt_password2:
            return public.getMsg('INSTALL_PASS_CHECK')
        public.M('users').where("id=?", (1,)).save(
            'username,password',
            (get.bt_username,
             public.password_salt(public.md5(get.bt_password1.strip()),
                                  uid=1)))
        os.remove('install.pl')
        public.M('config').where("id=?", ('1',)).setField('status', 1)
        data = {}
        data['status'] = os.path.exists('install.pl')
        data['username'] = get.bt_username
        return render_template('install.html', data=data)


# ==================================================#

# ======================公共方法区域START============================#


def get_dir_down(filename, token, find):
    # 获取分享目录信息
    import files
    args = public.dict_obj()
    args.path = filename
    args.share = True
    to_path = filename.replace(find['filename'], '').strip('/')

    if request.args.get('play') == 'true':
        pdata = files.files().get_videos(args)
        return public.GetJson(pdata), json_header
    else:
        pdata = files.files().GetDir(args)
        pdata['token'] = token
        pdata['ps'] = find['ps']
        pdata['src_path'] = find['filename']
        pdata['to_path'] = to_path
        if find['expire'] < (time.time() + (86400 * 365 * 10)):
            pdata['expire'] = public.format_date(times=find['expire'])
        else:
            pdata['expire'] = '永久有效'
        pdata['filename'] = (find['filename'].split('/')[-1] + '/' +
                             to_path).strip('/')
        return render_template('down.html', data=pdata, to_size=public.to_size, download_num=file_download_num)


def get_phpmyadmin_dir():
    # 获取phpmyadmin目录
    path = public.GetConfigValue('setup_path') + '/phpmyadmin'
    if not os.path.exists(path): return None
    phpport = '888'
    try:
        import re
        if session['webserver'] == 'nginx':
            filename = public.GetConfigValue(
                'setup_path') + '/nginx/conf/nginx.conf'
            conf = public.readFile(filename)
            rep = r"listen\s+([0-9]+)\s*;"
            rtmp = re.search(rep, conf)
            if rtmp:
                phpport = rtmp.groups()[0]
        if session['webserver'] == 'apache':
            filename = public.GetConfigValue(
                'setup_path') + '/apache/conf/extra/httpd-vhosts.conf'
            conf = public.readFile(filename)
            rep = r"Listen\s+([0-9]+)\s*\n"
            rtmp = re.search(rep, conf)
            if rtmp:
                phpport = rtmp.groups()[0]
        if session['webserver'] == 'openlitespeed':
            filename = public.GetConfigValue(
                'setup_path') + '/panel/vhost/openlitespeed/listen/888.conf'
            public.writeFile('/tmp/2', filename)
            conf = public.readFile(filename)
            rep = r"address\s*\*\:\s*(\d+)"
            rtmp = re.search(rep, conf)
            if rtmp:
                phpport = rtmp.groups()[0]
    except:
        pass

    for filename in os.listdir(path):
        filepath = path + '/' + filename
        if os.path.isdir(filepath):
            if filename[0:10] == 'phpmyadmin':
                return str(filename), phpport
    return None


class run_exec:
    # 模块访问对像
    def run(self, toObject, defs, get):
        result = None
        if not get['action'] in defs:
            return public.ReturnJson(False, 'ARGS_ERR'), json_header
        result = getattr(toObject, get.action)(get)
        if not hasattr(get, 'html') and not hasattr(get, 's_module'):
            r_type = type(result)
            if r_type in [Response, Resp]: return result
            result = public.GetJson(result), json_header

        if g.is_aes:
            result = public.aes_encrypt(result[0], g.aes_key), json_header
        return result


def check_csrf():
    # CSRF校验
    if app.config['DEBUG']: return True
    http_token = request.headers.get('x-http-token')
    if not http_token: return False
    if http_token != public.get_csrf_sess_html_token_value(): return False
    return True


def publicObject(toObject, defs, action=None, get=None, is_csrf=True):
    try:
        # 模块访问前置检查
        if is_csrf and public.get_csrf_sess_html_token_value() and session.get(
                'login', None):
            if not check_csrf():
                return public.ReturnJson(False, 'INIT_CSRF_ERR'), json_header

        if not get: get = get_input()
        if action: get.action = action

        if hasattr(get, 'path'):
            get.path = get.path.replace('//', '/').replace('\\', '/')
            if get.path.find('./') != -1:
                return public.ReturnJson(False,
                                         'INIT_PATH_NOT_SAFE'), json_header
            if get.path.find('->') != -1:
                get.path = get.path.split('->')[0].strip()
            get.path = public.xssdecode(get.path)
        if hasattr(get, 'filename'):
            get.filename = public.xssdecode(get.filename)

        if hasattr(get, 'sfile'):
            get.sfile = get.sfile.replace('//', '/').replace('\\', '/')
            get.sfile = public.xssdecode(get.sfile)
        if hasattr(get, 'dfile'):
            get.dfile = get.dfile.replace('//', '/').replace('\\', '/')
            get.dfile = public.xssdecode(get.dfile)

        if hasattr(toObject, 'site_path_check'):
            if not toObject.site_path_check(get):
                return public.ReturnJson(False, 'INIT_ACCEPT_NOT'), json_header
        run_obj = run_exec()
        res = run_obj.run(toObject, defs, get)
        del (run_obj)
        return res
    except:
        if os.path.exists('data/debug.pl'):
            print(public.get_error_info())
            public.print_log(public.get_error_info())
        return error_500(None)
    finally:
        del (toObject)
        del (get)


def check_login(http_token=None):
    # 检查是否登录面板
    if cache.get('dologin'): return False
    if 'login' in session:
        loginStatus = session['login']
        if loginStatus and http_token:
            if public.get_csrf_sess_html_token_value() != http_token:
                return False
        return loginStatus
    return False


def get_pd():
    # 获取授权信息
    tmp = -1
    # try:
    #     import panelPlugin
    #     get = public.dict_obj()
    #     # get.init = 1
    #     tmp1 = panelPlugin.panelPlugin().get_cloud_list(get)
    # except:
    tmp1 = None
    if tmp1:
        tmp = tmp1[public.to_string([112, 114, 111])]
        ltd = tmp1.get('ltd', -1)
    else:
        ltd = -1
        tmp4 = cache.get(public.to_string([112, 95, 116, 111, 107, 101, 110]))
        if tmp4:
            tmp_f = public.to_string([47, 116, 109, 112, 47]) + tmp4
            if not os.path.exists(tmp_f): public.writeFile(tmp_f, '-1')
            tmp = public.readFile(tmp_f)
            if tmp: tmp = int(tmp)
    if not ltd or not isinstance(ltd, int): ltd = -1
    if tmp == None or not isinstance(tmp, int): tmp = -1
    if ltd < 1:
        if ltd == -2:
            tmp3 = public.to_string([
                60, 115, 112, 97, 110, 32, 99, 108, 97, 115, 115, 61, 34, 98,
                116, 108, 116, 100, 45, 103, 114, 97, 121, 34, 62, 60, 115,
                112, 97, 110, 32, 115, 116, 121, 108, 101, 61, 34, 99, 111,
                108, 111, 114, 58, 32, 35, 102, 99, 54, 100, 50, 54, 59, 102,
                111, 110, 116, 45, 119, 101, 105, 103, 104, 116, 58, 32, 98,
                111, 108, 100, 59, 109, 97, 114, 103, 105, 110, 45, 114, 105,
                103, 104, 116, 58, 53, 112, 120, 34, 62, 24050, 36807, 26399,
                60, 47, 115, 112, 97, 110, 62, 60, 97, 32, 99, 108, 97, 115,
                115, 61, 34, 98, 116, 108, 105, 110, 107, 34, 32, 111, 110, 99,
                108, 105, 99, 107, 61, 34, 98, 116, 46, 115, 111, 102, 116, 46,
                117, 112, 100, 97, 116, 97, 95, 108, 116, 100, 40, 41, 34, 62,
                32493, 36153, 60, 47, 97, 62, 60, 47, 115, 112, 97, 110, 62
            ])
        elif tmp == -1:
            tmp3 = public.to_string([
                60, 115, 112, 97, 110, 32, 99, 108, 97, 115, 115, 61, 34, 98,
                116, 112, 114, 111, 45, 102, 114, 101, 101, 34, 32, 111, 110,
                99, 108, 105, 99, 107, 61, 34, 98, 116, 46, 115, 111, 102, 116,
                46, 117, 112, 100, 97, 116, 97, 95, 99, 111, 109, 109, 101,
                114, 99, 105, 97, 108, 95, 118, 105, 101, 119, 40, 41, 34, 32,
                116, 105, 116, 108, 101, 61, 34, 28857, 20987, 21319, 32423,
                21040, 21830, 19994, 29256, 34, 62, 20813, 36153, 29256, 60,
                47, 115, 112, 97, 110, 62
            ])
        elif tmp == -2:
            tmp3 = public.to_string([
                60, 115, 112, 97, 110, 32, 99, 108, 97, 115, 115, 61, 34, 98,
                116, 112, 114, 111, 45, 103, 114, 97, 121, 34, 62, 60, 115,
                112, 97, 110, 32, 115, 116, 121, 108, 101, 61, 34, 99, 111,
                108, 111, 114, 58, 32, 35, 102, 99, 54, 100, 50, 54, 59, 102,
                111, 110, 116, 45, 119, 101, 105, 103, 104, 116, 58, 32, 98,
                111, 108, 100, 59, 109, 97, 114, 103, 105, 110, 45, 114, 105,
                103, 104, 116, 58, 53, 112, 120, 34, 62, 24050, 36807, 26399,
                60, 47, 115, 112, 97, 110, 62, 60, 97, 32, 99, 108, 97, 115,
                115, 61, 34, 98, 116, 108, 105, 110, 107, 34, 32, 111, 110, 99,
                108, 105, 99, 107, 61, 34, 98, 116, 46, 115, 111, 102, 116, 46,
                117, 112, 100, 97, 116, 97, 95, 112, 114, 111, 40, 41, 34, 62,
                32493, 36153, 60, 47, 97, 62, 60, 47, 115, 112, 97, 110, 62
            ])
        if tmp >= 0 and ltd in [-1, -2]:
            if tmp == 0:
                tmp2 = public.to_string([27704, 20037, 25480, 26435])
                tmp3 = public.to_string([
                    60, 115, 112, 97, 110, 32, 99, 108, 97, 115, 115, 61, 34,
                    98, 116, 112, 114, 111, 34, 62, 123, 48, 125, 60, 115, 112,
                    97, 110, 32, 115, 116, 121, 108, 101, 61, 34, 99, 111, 108,
                    111, 114, 58, 32, 35, 102, 99, 54, 100, 50, 54, 59, 102,
                    111, 110, 116, 45, 119, 101, 105, 103, 104, 116, 58, 32,
                    98, 111, 108, 100, 59, 34, 62, 123, 49, 125, 60, 47, 115,
                    112, 97, 110, 62, 60, 47, 115, 112, 97, 110, 62
                ]).format(
                    public.to_string([21040, 26399, 26102, 38388, 65306]),
                    tmp2)
            else:
                tmp2 = time.strftime(
                    public.to_string([37, 89, 45, 37, 109, 45, 37, 100]),
                    time.localtime(tmp))
                tmp3 = public.to_string([
                    60, 115, 112, 97, 110, 32, 99, 108, 97, 115, 115, 61, 34,
                    98, 116, 112, 114, 111, 34, 62, 21040, 26399, 26102, 38388,
                    65306, 60, 115, 112, 97, 110, 32, 115, 116, 121, 108, 101,
                    61, 34, 99, 111, 108, 111, 114, 58, 32, 35, 102, 99, 54,
                    100, 50, 54, 59, 102, 111, 110, 116, 45, 119, 101, 105,
                    103, 104, 116, 58, 32, 98, 111, 108, 100, 59, 109, 97, 114,
                    103, 105, 110, 45, 114, 105, 103, 104, 116, 58, 53, 112,
                    120, 34, 62, 123, 48, 125, 60, 47, 115, 112, 97, 110, 62,
                    60, 97, 32, 99, 108, 97, 115, 115, 61, 34, 98, 116, 108,
                    105, 110, 107, 34, 32, 111, 110, 99, 108, 105, 99, 107, 61,
                    34, 98, 116, 46, 115, 111, 102, 116, 46, 117, 112, 100, 97,
                    116, 97, 95, 112, 114, 111, 40, 41, 34, 62, 32493, 36153,
                    60, 47, 97, 62, 60, 47, 115, 112, 97, 110, 62
                ]).format(tmp2)
        else:
            tmp3 = public.to_string([
                60, 115, 112, 97, 110, 32, 99, 108, 97, 115, 115, 61, 34, 98,
                116, 112, 114, 111, 45, 103, 114, 97, 121, 34, 32, 111, 110,
                99, 108, 105, 99, 107, 61, 34, 98, 116, 46, 115, 111, 102, 116,
                46, 117, 112, 100, 97, 116, 97, 95, 112, 114, 111, 40, 41, 34,
                32, 116, 105, 116, 108, 101, 61, 34, 28857, 20987, 21319,
                32423, 21040, 19987, 19994, 29256, 34, 62, 20813, 36153, 29256,
                60, 47, 115, 112, 97, 110, 62
            ])
    else:
        tmp3 = public.to_string([
            60, 115, 112, 97, 110, 32, 99, 108, 97, 115, 115, 61, 34, 98, 116,
            108, 116, 100, 34, 62, 21040, 26399, 26102, 38388, 65306, 60, 115,
            112, 97, 110, 32, 115, 116, 121, 108, 101, 61, 34, 99, 111, 108,
            111, 114, 58, 32, 35, 102, 99, 54, 100, 50, 54, 59, 102, 111, 110,
            116, 45, 119, 101, 105, 103, 104, 116, 58, 32, 98, 111, 108, 100,
            59, 109, 97, 114, 103, 105, 110, 45, 114, 105, 103, 104, 116, 58,
            53, 112, 120, 34, 62, 123, 125, 60, 47, 115, 112, 97, 110, 62, 60,
            97, 32, 99, 108, 97, 115, 115, 61, 34, 98, 116, 108, 105, 110, 107,
            34, 32, 111, 110, 99, 108, 105, 99, 107, 61, 34, 98, 116, 46, 115,
            111, 102, 116, 46, 117, 112, 100, 97, 116, 97, 95, 108, 116, 100,
            40, 41, 34, 62, 32493, 36153, 60, 47, 97, 62, 60, 47, 115, 112, 97,
            110, 62
        ]).format(
            time.strftime(public.to_string([37, 89, 45, 37, 109, 45, 37, 100]),
                          time.localtime(ltd)))

    return tmp3, tmp, ltd


def send_authenticated():
    # 发送http认证信息
    request_host = public.GetHost()
    result = Response(
        '', 401,
        {'WWW-Authenticate': 'Basic realm="%s"' % request_host.strip()})
    # if not 'login' in session and not 'admin_auth' in session: session.clear()
    return result


# 取端口
def FtpPort():
    # 获取FTP端口
    if session.get('port'): return
    import re
    try:
        file = public.GetConfigValue(
            'setup_path') + '/pure-ftpd/etc/pure-ftpd.conf'
        conf = public.readFile(file)
        rep = r"\n#?\s*Bind\s+[0-9]+\.[0-9]+\.[0-9]+\.+[0-9]+,([0-9]+)"
        port = re.search(rep, conf).groups()[0]
    except:
        port = '21'
    session['port'] = port


def is_login(result):
    # 判断是否登录2
    if 'login' in session:
        if session['login'] == True:
            # result = make_response(result)
            # request_token = public.GetRandomString(48)
            # request_token_key = public.get_csrf_cookie_token_key()
            # session[request_token_key] = request_token
            # samesite = app.config['SESSION_COOKIE_SAMESITE']
            # secure = app.config['SESSION_COOKIE_SECURE']
            # if app.config['SSL'] and request.full_path.find('/login?tmp_token=') == 0:
            #     samesite = 'None'
            #     secure = True
            # result.set_cookie(request_token_key, request_token,
            # max_age=86400 * 30,
            # samesite= samesite,
            # secure=secure
            # )
            pass
    return result


def is_bind():
    pass
    # if os.path.exists(bind_pl):
    #    os.remove(bind_pl)


# js随机数模板使用，用于不更新版本号时更新前端文件不需要用户强制刷新浏览器
def get_js_random():
    js_random = public.readFile('data/js_random.pl')
    if not js_random or js_random == '1':
        js_random = public.GetRandomString(16)
    public.writeFile('data/js_random.pl', js_random)
    return js_random


# 获取输入数据
def get_input():
    data = public.dict_obj()
    exludes = ['blob']
    for key in request.args.keys():
        data.set(key, str(request.args.get(key, '')))
    try:
        for key in request.form.keys():
            if key in exludes: continue
            data.set(key, str(request.form.get(key, '')))
    except:
        try:
            post = request.form.to_dict()
            for key in post.keys():
                if key in exludes: continue
                data.set(key, str(post[key]))
        except:
            pass

    if 'form_data' in g:
        for k in g.form_data.keys():
            data.set(k, str(g.form_data[k]))

    if not hasattr(data, 'data'): data.data = []
    return data


# 取数据对象
def get_input_data(data):
    pdata = public.dict_obj()
    for key in data.keys():
        pdata[key] = str(data[key])
    return pdata


# 检查Token
def check_token(data):
    # 已作废
    pluginPath = 'plugin/safelogin/token.pl'
    if not os.path.exists(pluginPath): return False
    from urllib import unquote
    from binascii import unhexlify
    from json import loads

    result = unquote(unhexlify(data))
    token = public.readFile(pluginPath).strip()

    result = loads(result)
    if not result: return False
    if result['token'] != token: return False
    return result


# ======================公共方法区域END============================#

# workorder load code


@app.route('/workorder/<action>', methods=method_all)
def workorder(action, pdata=None):
    comReturn = comm.local()
    if comReturn: return comReturn

    import panelWorkorder
    toObject = panelWorkorder.panelWorkorder()

    defs = ("get_user_info", "close", "create", "list", "get_messages",
            "allow")
    result = publicObject(toObject, defs, action, pdata)
    return result


# workorder end

# ---------------------    websocket  START  -------------------------- #


@sockets.route('/workorder_client')
def workorder_client(ws):
    comReturn = comm.local()
    if comReturn: return comReturn

    get = ws.receive()
    get = json.loads(get)
    if not check_csrf_websocket(ws, get):
        return

    import panelWorkorder
    toObject = panelWorkorder.panelWorkorder()
    get = get_input()
    toObject.client(ws, get)


@sockets.route('/ws_panel')
def ws_panel(ws):
    '''
        @name 面板接口ws入口
        @author hwliang<2021-07-24>
        @param ws<ws_parameter> websocket会话对像
        @return void
    '''
    comReturn = comm.local()
    if comReturn: return comReturn

    get = ws.receive()
    get = json.loads(get)
    if not check_csrf_websocket(ws, get): return

    while True:
        pdata = ws.receive()
        if pdata in ['{}', {}, None, '']:
            ws.send(json.dumps(public.return_status_code(1000, '请求参数不能为空')))
            break
        try:
            data = json.loads(pdata)
            get = public.to_dict_obj(data)
        except:
            request.form = {
                "error": pdata
            }
            raise Exception('json load error !')
        get._ws = ws
        p = threading.Thread(target=ws_panel_thread, args=(get,))
        p.start()



WS_OBJ = {}


@sockets.route('/ws_home')
def ws_home(ws):
    '''
        @name 首页接口ws入口
        @author hwliang<2021-07-24>
        @param ws<ws_parameter> websocket会话对像
        @return void
    '''
    comReturn = comm.local()
    if comReturn: return comReturn


    get = ws.receive()
    get = json.loads(get)
    if not check_csrf_websocket(ws, get): return
    global WS_OBJ
    from panelController import Controller
    model_obj = Controller()
    while True:
        pdata = ws.receive()
        if pdata in ['{}', {}, None, '']:
            ws.send(json.dumps(public.return_status_code(1000, '请求参数不能为空')))
            break
        try:
            get = public.to_dict_obj(json.loads(pdata))
        except:
            request.form = {
                "error": pdata
            }
            raise Exception('json load error !')
        get._ws = ws
        WS_OBJ[get.get('ws_id',public.GetRandomString(16))] = {'ws_obj': get._ws, 'menu': get.get('menu',''), 'timeout': int(time.time()) + 33}
        WS_OBJ = {i:j for i,j in WS_OBJ.items() if j['timeout'] > int(time.time())}
        if hasattr(get, 'model_index') and get.model_index != '':
            ws_model_thread(model_obj, get)
        else:
            ws_panel_thread(get)


def ws_panel_thread(get):
    '''
        @name 面板管理ws线程
        @author hwliang<2021-07-24>
        @param get<dict> 请求参数
        @return void
    '''

    if not hasattr(get, 'ws_callback'):
        get._ws.send(
            public.getJson(public.return_status_code(1001, 'ws_callback')))
        return
    if not hasattr(get, 'mod_name'):
        get._ws.send(
            public.getJson(public.return_status_code(1001, 'mod_name')))
        return
    if not hasattr(get, 'def_name'):
        get._ws.send(
            public.getJson(public.return_status_code(1001, 'def_name')))
        return
    get.mod_name = get.mod_name.strip()
    get.def_name = get.def_name.strip()
    check_str = '{}{}'.format(get.mod_name, get.def_name)
    if not re.match(r"^\w+$", check_str) or get.mod_name in [
        'public', 'common', 'db', 'db_mysql', 'downloadFile', 'jobs'
    ]:
        get._ws.send(
            public.getJson(
                public.return_status_code(1000, '不安全的mod_name,def_name参数内容')))
        return
    # if not hasattr(get,'args'):
    #     get._ws.send(public.getJson(public.return_status_code(1001,'args')))
    #     return

    mod_file = '{}/{}.py'.format(public.get_class_path(), get.mod_name)
    if not os.path.exists(mod_file):
        get._ws.send(
            public.getJson(
                public.return_status_code(1000,
                                          '指定模块{}不存在'.format(get.mod_name))))
        return
    _obj = public.get_script_object(mod_file)
    if not _obj:
        get._ws.send(
            public.getJson(
                public.return_status_code(1000,
                                          '指定模块{}不存在'.format(get.mod_name))))
        return
    _cls = getattr(_obj, get.mod_name)
    if not _cls:
        get._ws.send(
            public.getJson(
                public.return_status_code(
                    1000, '在{}模块中没有找到{}对像'.format(get.mod_name,
                                                            get.mod_name))))
        return
    _def = getattr(_cls(), get.def_name)
    if not _def:
        get._ws.send(
            public.getJson(
                public.return_status_code(
                    1000, '在{}对像中没有找到{}方法'.format(get.mod_name,
                                                            get.def_name))))
        return
    result = {'callback': get.ws_callback, 'result': _def(get)}
    get._ws.send(public.getJson(result))


@sockets.route('/ws_project')
def ws_project(ws):
    '''
        @name 项目管理ws入口
        @author hwliang<2021-07-24>
        @param ws<ws_parameter> websocket会话对像
        @return void
    '''
    comReturn = comm.local()
    if comReturn: return comReturn
    get = ws.receive()
    get = json.loads(get)
    if not check_csrf_websocket(ws, get): return

    from panelProjectController import ProjectController
    project_obj = ProjectController()
    while True:
        pdata = ws.receive()
        if pdata in ['{}', {}, None, '']:
            ws.send(json.dumps(public.return_status_code(1000, '请求参数不能为空')))
            break
        try:
            get = public.to_dict_obj(json.loads(pdata))
        except:
            request.form = {
                "error": pdata
            }
            raise Exception('json load error !')
        get._ws = ws
        p = threading.Thread(target=ws_project_thread, args=(project_obj, get))
        p.start()


def ws_project_thread(_obj, get):
    '''
        @name 项目管理ws线程
        @author hwliang<2021-07-24>
        @param _obj<ProjectController> 项目管理控制器对像
        @param get<dict> 请求参数
        @return void
    '''
    if not hasattr(get, 'ws_callback'):
        get._ws.send(
            public.getJson(public.return_status_code(1001, 'ws_callback')))
        return
    result = {'callback': get.ws_callback, 'result': _obj.model(get)}
    get._ws.send(public.getJson(result))


@sockets.route('/ws_files')
def ws_files(ws):
    '''
        @name 项目管理ws入口
        @author hezhihong<2023-02-10>
        @param ws<ws_parameter> websocket会话对像
        @return void
    '''
    comReturn = comm.local()
    if comReturn: return comReturn
    get = ws.receive()
    get = json.loads(get)
    if not check_csrf_websocket(ws, get): return

    from panelFilesController import FilesController
    project_obj = FilesController()
    while True:
        pdata = ws.receive()
        # public.writeFile('/tmp/aa.aa', str(pdata))
        if pdata in ['{}', {}, None, '']:
            ws.send(json.dumps(public.return_status_code(1000, '请求参数不能为空')))
            break
        try:
            get = public.to_dict_obj(json.loads(pdata))
        except:
            request.form = {
                "error": pdata
            }
            raise Exception('json load error !')
        get._ws = ws
        p = threading.Thread(target=ws_files_thread, args=(project_obj, get))
        p.start()


def ws_files_thread(_obj, get):
    '''
        @name 项目管理ws线程
        @author hezhihong<2023-02-10>
        @param _obj<ProjectController> 项目管理控制器对像
        @param get<dict> 请求参数
        @return void
    '''
    if not hasattr(get, 'ws_callback'):
        get._ws.send(
            public.getJson(public.return_status_code(1001, 'ws_callback')))
        return
    result = {'callback': get.ws_callback, 'result': _obj.model(get)}
    get._ws.send(public.getJson(result))


@sockets.route('/ws_model')
def ws_model(ws):
    '''
        @name 模型控制器ws入口
        @author hwliang<2021-07-24>
        @param ws<ws_parameter> websocket会话对像
        @return void
    '''
    comReturn = comm.local()
    if comReturn: return comReturn
    get = ws.receive()
    get = json.loads(get)
    if not check_csrf_websocket(ws, get): return

    from panelController import Controller
    model_obj = Controller()
    while True:
        pdata = ws.receive()
        if pdata in ['{}']:
            ws.send(json.dumps(public.return_status_code(1000, '请求参数不能为空')))
            break
        try:
            get = public.to_dict_obj(json.loads(pdata))
        except:
            request.form = {
                "error": pdata
            }
            raise Exception('json load error !')
        get._ws = ws
        get.model_index = get.model_index.strip()
        p = threading.Thread(target=ws_model_thread, args=(model_obj, get))
        p.start()


def ws_model_thread(_obj, get):
    '''
        @name 模型控制器ws线程
        @author hwliang<2021-07-24>
        @param _obj<Controller> 控制器对像
        @param get<dict> 请求参数
        @return void
    '''
    if not hasattr(get, 'ws_callback'):
        get._ws.send(
            public.getJson(public.return_status_code(1001, 'ws_callback')))
        return
    result = {'callback': get.ws_callback, 'result': _obj.model(get)}
    get._ws.send(public.getJson(result))


import subprocess

sock_pids = {}


@sockets.route('/sock_shell')
def sock_shell(ws):
    '''
        @name 执行指定命令，实时输出命令执行结果
        @author hwliang<2021-07-19>
        @return void

        示例：
            p = new WebSocket('ws://192.168.1.247:8888/sock_shell')
            p.send('ping www.bt.cn -c 100')
    '''
    comReturn = comm.local()
    if comReturn:
        ws.send(str(comReturn))
        return
    kill_closed()
    get = ws.receive()
    get = json.loads(get)
    if not check_csrf_websocket(ws, get): return

    t = None
    try:
        while True:
            cmdstring = ws.receive()
            if cmdstring in ['stop', 'error'] or not cmdstring:
                break
            t = threading.Thread(target=sock_recv, args=(cmdstring, ws))
            t.start()
        kill_closed()
    except:
        kill_closed()


def kill_closed():
    '''
        @name 关闭已关闭的连接
        @author hwliang<2021-07-24>
        @return void
    '''
    global sock_pids
    import psutil
    pids = psutil.pids()
    keys = sock_pids.copy().keys()
    for pid in keys:
        if hasattr(sock_pids[pid], 'closed'):
            is_closed = sock_pids[pid].closed
        else:
            is_closed = not sock_pids[pid].connected

        logging.debug("PID: {} , sock_stat: {}".format(pid, is_closed))
        if not is_closed: continue

        if pid in pids:
            try:
                p = psutil.Process(pid)
                for cp in p.children():
                    cp.kill()
                p.kill()
                logging.debug("killed: {}".format(pid))
                sock_pids.pop(pid)
            except:
                pass
        else:
            sock_pids.pop(pid)


def sock_recv(cmdstring, ws):
    global sock_pids
    try:
        p = subprocess.Popen(cmdstring + " 2>&1",
                             close_fds=True,
                             shell=True,
                             bufsize=4096,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        sock_pids[p.pid] = ws
        kill_closed()
        while p.poll() == None:
            send_line = p.stdout.readline().decode()
            if not send_line or send_line.find('tail: ') != -1: continue
            if ws.connected:
                ws.send(send_line)
        if ws.connected:
            ws.send(p.stdout.read().decode())
    except:
        kill_closed()


@app.route('/close_sock_shell', methods=method_all)
def close_sock_shell():
    '''
        @name 关闭指定命令
        @author hwliang<2021-07-19>
        @param cmdstring<string> 完整命令行
        @return dict
        示例：
            $.post('/close_sock_shell',{cmdstring:'ping www.bt.cn -c 100'})
    '''
    comReturn = comm.local()
    if comReturn: return comReturn
    args = get_input()
    if not check_csrf():
        return public.ReturnJson(False, 'INIT_CSRF_ERR'), json_header
    cmdstring = args.cmdstring.strip()
    skey = public.md5(cmdstring)
    pid = cache.get(skey)
    if not pid:
        return json.dumps(public.return_data(
            False, [], error_msg='指定sock已终止!')), json_header
    os.kill(pid, 9)
    cache.delete(skey)
    return json.dumps(public.return_data(True, '操作成功!')), json_header


def check_csrf_websocket(ws, args):
    '''
        @name 检查websocket是否被csrf攻击
        @author hwliang<2021-07-24>
        @param ws<WebSocket> websocket对像
        @return void
    '''
    if g.is_aes: return True
    if g.api_request: return True
    if public.is_debug(): return True
    is_success = True
    if not 'x-http-token' in args:
        is_success = False

    if is_success:
        if public.get_csrf_sess_html_token_value() != args['x-http-token']:
            is_success = False

    if not is_success:
        ws.send('token error')
        return False

    return True


@sockets.route('/webssh')
def webssh(ws):
    # 宝塔终端连接
    comReturn = comm.local()
    if comReturn:
        ws.send(str(comReturn))
        return
    if not ws: return 'False'
    get = ws.receive()
    if not get: return
    get = json.loads(get)
    if not check_csrf_websocket(ws, get):
        return

    import ssh_terminal
    sp = ssh_terminal.ssh_host_admin()
    if 'host' in get:
        ssh_info = {}
        ssh_info['host'] = get['host'].strip()
        if 'port' in get:
            ssh_info['port'] = int(get['port'])
        if 'username' in get:
            ssh_info['username'] = get['username'].strip()
        if 'password' in get:
            ssh_info['password'] = get['password'].strip()
        if 'pkey' in get:
            ssh_info['pkey'] = get['pkey'].strip()
        if 'pkey_passwd' in get:
            ssh_info['pkey_passwd'] = get['pkey_passwd'].strip()

        if get['host'] in ['127.0.0.1', 'localhost']:
            if not 'password' in ssh_info:
                ssh_info = sp.get_ssh_info('127.0.0.1')
                if not ssh_info: ssh_info = sp.get_ssh_info('localhost')
                if not ssh_info: ssh_info = {"host": "127.0.0.1"}
                if not 'port' in ssh_info:
                    ssh_info['port'] = public.get_ssh_port()
    else:
        ssh_info = sp.get_ssh_info('127.0.0.1')
        if not ssh_info: ssh_info = sp.get_ssh_info('localhost')
        if not ssh_info: ssh_info = {"host": "127.0.0.1"}
        ssh_info['port'] = public.get_ssh_port()

    if not ssh_info['host'] in ['127.0.0.1', 'localhost']:
        if not 'username' in ssh_info:
            ssh_info = sp.get_ssh_info(ssh_info['host'])
            if not ssh_info:
                ws.send('没有找到指定主机信息，请重新添加!')
                return
    # 本机使用本地快速终端
    if ssh_info['host'] in ['127.0.0.1', 'localhost'] and set(ssh_info.keys()) == {"host", "port"}:
        p = ssh_terminal.local_ssh_terminal()
    else:
        p = ssh_terminal.ssh_terminal()

    p.run(ws, ssh_info)
    del (p)
    if ws.connected:
        ws.close()
    return 'False'


# ---------------------    websocket END    -------------------------- #


@app.route("/daily", methods=method_all)
def daily():
    """面板日报数据"""

    comReturn = comm.local()
    if comReturn: return comReturn

    import panelDaily
    toObject = panelDaily.panelDaily()

    defs = ("get_app_usage", "get_daily_data", "get_daily_list","check_daily_status","set_daily_status")
    result = publicObject(toObject, defs)
    return result


@app.route('/phpmyadmin/<path:path_full>', methods=method_all)
def pma_proxy(path_full=None):
    '''
        @name phpMyAdmin代理
        @author hwliang<2022-01-19>
        @return Response
    '''
    comReturn = comm.local()
    if comReturn: return comReturn
    cache_key = 'pmd_port_path'
    pmd = cache.get(cache_key)
    if not pmd:
        pmd = get_phpmyadmin_dir()
        if not pmd: return '未安装phpMyAdmin,请到【软件商店】页面安装!'
        pmd = list(pmd)
        cache.set(cache_key, pmd, 10)
    panel_pool = 'http://'
    if request.url_root[:5] == 'https':
        panel_pool = 'https://'
        import ajax
        ssl_info = ajax.ajax().get_phpmyadmin_ssl(None)
        if ssl_info['status']:
            pmd[1] = ssl_info['port']
        else:
            panel_pool = 'http://'

    proxy_url = '{}127.0.0.1:{}/{}/'.format(
        panel_pool, pmd[1], pmd[0]) + request.full_path.replace(
        '/phpmyadmin/', '')
    from panelHttpProxy import HttpProxy
    px = HttpProxy()
    return px.proxy(proxy_url)


@app.route('/p/<int:port>', methods=method_all)
@app.route('/p/<int:port>/', methods=method_all)
@app.route('/p/<int:port>/<path:full_path>', methods=method_all)
def proxy_port(port, full_path=None):
    '''
        @name 代理指定端口
        @author hwliang<2022-01-19>
        @return Response
    '''

    comReturn = comm.local()
    if comReturn: return comReturn
    full_path = request.full_path.replace('/p/{}/'.format(port),
                                          '').replace('/p/{}'.format(port), '')
    uri = '{}/{}'.format(port, full_path)
    uri = uri.replace('//', '/')
    proxy_url = 'http://127.0.0.1:{}'.format(uri)
    from panelHttpProxy import HttpProxy
    px = HttpProxy()
    return px.proxy(proxy_url)


@app.route('/push', methods=method_all)
def push(pdata=None):
    comReturn = comm.local()
    if comReturn: return comReturn
    import panelPush
    toObject = panelPush.panelPush()
    defs = ('set_push_status', 'get_push_msg_list', 'get_modules_list',
            'install_module', 'uninstall_module', 'get_module_template',
            'set_push_config', 'get_push_config', 'del_push_config',
            'get_module_logs', 'get_module_config', 'get_push_list',
            'get_push_logs', "get_task_template")
    result = publicObject(toObject, defs, None, pdata)
    return result


@sockets.route('/pyenv_webssh')
def python_env_ssh(ws):
    # 宝塔终端连接
    comReturn = comm.local()
    if comReturn:
        ws.send(str(comReturn))
        return
    if not ws:
        return 'False'
    get = ws.receive()
    if not get:
        return
    get = json.loads(get)
    if not check_csrf_websocket(ws, get):
        return

    import ssh_terminal
    from projectModel.pythonModel import PyenvSshTerminal

    sp = ssh_terminal.ssh_host_admin()
    ssh_info = sp.get_ssh_info('127.0.0.1')
    if not ssh_info: ssh_info = sp.get_ssh_info('localhost')
    if not ssh_info: ssh_info = {"host": "127.0.0.1"}
    ssh_info['port'] = public.get_ssh_port()

    p = PyenvSshTerminal()
    p.run(ws, ssh_info)
    del p
    if ws.connected:
        ws.close()
    return 'False'


# 获取新场景模型的传参数据
def get_mod_input():
    '''
        @name # 获取新场景模型的传参数据
        @author wzz <2024/1/24 上午 11:42>
        @param "data":{"参数名":""} <数据类型> 参数描述
        @return dict{"status":True/False,"msg":"提示信息"}
    '''
    data = public.dict_obj()
    exludes = ['blob']
    for key in request.args.keys():
        data.set(key, str(request.args.get(key, '')))

    if request.is_json:
        for key in request.get_json().keys():
            data.set(key, str(request.get_json()[key]))
    else:
        try:
            for key in request.form.keys():
                if key in exludes: continue
                data.set(key, str(request.form.get(key, '')))
        except:
            try:
                post = request.form.to_dict()
                for key in post.keys():
                    if key in exludes: continue
                    data.set(key, str(post[key]))
            except:
                pass

    if 'form_data' in g:
        for k in g.form_data.keys():
            data.set(k, str(g.form_data[k]))

    if not hasattr(data, 'data'): data.data = []
    return data


# 2024/1/24 上午 11:42 新场景模型的路由
@app.route('/mod/<name>/<sub_name>/<fun>', methods=method_all)
@app.route('/mod/<name>/<sub_name>/<fun>/<path:stype>', methods=method_all)
def panel_mod(name=None, sub_name=None, fun=None, stype=None):
    '''
        @name 新场景模型的路由
        @author wzz <2024/1/24 上午 11:42>
        @param "data":{"参数名":""} <数据类型> 参数描述
        @return dict{"status":True/False,"msg":"提示信息"}
    '''
    if not public.is_bind():
        return redirect('/bind', 302)
    if public.is_error_path():
        return redirect('/error', 302)
    if not name: return abort(404)
    if not sub_name: return abort(404)
    if not re.match(r"^[\w\-]+$", name): return abort(404)
    if not re.match(r"^[\w\-]+$", sub_name): return abort(404)
    if fun and not re.match(r"^[\w\-\.]+$", fun): return abort(404)

    comReturn = comm.local()
    if comReturn: return comReturn
    if not stype:
        tmp = fun.split('.')
        fun = tmp[0]
        if len(tmp) == 1: tmp.append('')
        stype = tmp[1]
    if fun:
        if public.get_csrf_cookie_token_key() in session and 'login' in session:
            if not check_csrf():
                return public.ReturnJson(False, 'INIT_CSRF_ERR'), json_header

    args = get_mod_input()

    if not fun: fun = 'index.html'
    if not stype:
        tmp = fun.split('.')
        fun = tmp[0]
        if len(tmp) == 1: tmp.append('')
        stype = tmp[1]

    if not name: name = 'coll'
    if not public.path_safe_check("%s/%s/%s/%s" % (name, sub_name, fun, stype)):
        return abort(404)
    if name.find('./') != -1 or not re.match(r"^[\w-]+$", name):
        return abort(404)
    if sub_name.find('./') != -1 or not re.match(r"^[\w-]+$", sub_name):
        return abort(404)
    if not name:
        return public.returnJson(False, 'PLUGIN_INPUT_ERR'), json_header

    args.client_ip = public.GetClientIp()

    # 初始化新场景模型对象
    try:
        from mod.modController import Controller
        controller_obj = Controller()
        defs = ('model',)
        args.model_index = "mod"
        args.action = 'model'
        args.mod_name = name
        args.sub_mod_name = sub_name
        args.def_name = fun
        data = publicObject(controller_obj, defs, None, args)

        r_type = type(data)
        if r_type in [Response, Resp]:
            return data

        p_path = public.get_mod_path() + '/' + name

        # 处理响应
        if stype == 'json':  # 响应JSON
            return public.getJson(data), json_header
        elif stype == 'html':  # 使用模板
            t_path_root = p_path + '/templates/'
            t_path = t_path_root + fun + '.html'
            if not os.path.exists(t_path):
                return public.returnJson(False,
                                         'PLUGIN_NOT_TEMPLATE'), json_header
            t_body = public.readFile(t_path)
            # 处理模板包含
            rep = r'{%\s?include\s"(.+)"\s?%}'
            includes = re.findall(rep, t_body)
            for i_file in includes:
                filename = p_path + '/templates/' + i_file
                i_body = 'ERROR: File ' + filename + ' does not exists.'
                if os.path.exists(filename):
                    i_body = public.readFile(filename)
                t_body = re.sub(rep.replace('(.+)', i_file), i_body, t_body)
            return render_template_string(t_body, data=data)
        else:  # 直接响应插件返回值,可以是任意flask支持的响应类型
            r_type = type(data)
            if r_type == dict:
                if name == 'btwaf' and 'msg' in data:
                    return render_template('error3.html',
                                           data={"error_msg": data['msg']})
                return public.returnJson(
                    False,
                    public.getMsg('PUBLIC_ERR_RETURN').format(
                        r_type)), json_header
            return data
    except:
        if not 'login' in session: return abort(404)
        return public.get_error_object(None, plugin_name=name)


# 2024/2/19 上午 10:34 新场景模型控制器ws入口
@sockets.route('/ws_mod')
def ws_mod(ws):
    '''
        @name 新场景模型控制器ws入口
        @author wzz<2024-02-19>
        @param ws<ws_parameter> websocket会话对像
        @return void
    '''
    comReturn = comm.local()
    if comReturn: return comReturn
    get = ws.receive()
    get = json.loads(get)
    if not check_csrf_websocket(ws, get): return

    from mod.modController import Controller
    model_obj = Controller()
    while True:
        pdata = ws.receive()
        if pdata in ['{}', {}, None, '']:
            ws.send(json.dumps(public.return_status_code(1000, '请求参数不能为空')))
            break
        try:
            get = public.to_dict_obj(json.loads(pdata))
        except:
            request.form = {
                "error": pdata
            }
            raise Exception('json load error !')
        get._ws = ws
        get.model_index = "mod"
        p = threading.Thread(target=ws_model_thread, args=(model_obj, get))
        p.start()

# 2024/2/19 上午 10:34 新场景模型控制器ws入口，无默认return
@sockets.route('/ws_modsoc')
def ws_modsoc(ws):
    '''
        @name 新场景模型控制器ws入口
        @author wzz<2024-02-19>
        @param ws<ws_parameter> websocket会话对像
        @return void
    '''
    comReturn = comm.local()
    if comReturn: return comReturn
    get = ws.receive()
    get = json.loads(get)
    if not check_csrf_websocket(ws, get): return

    from mod.modController import Controller
    model_obj = Controller()
    while True:
        pdata = ws.receive()
        if pdata in ['{}', {}, None, '']:
            ws.send(json.dumps(public.return_status_code(1000, '请求参数不能为空')))
            break
        try:
            get = public.to_dict_obj(json.loads(pdata))
        except:
            request.form = {
                "error": pdata
            }
            raise Exception('json load error !')
        get._ws = ws
        get.model_index = "mod"
        p = threading.Thread(target=ws_mod_thread, args=(model_obj, get))
        p.start()

def ws_mod_thread(_obj, get):
    '''
        @name 模型控制器ws线程
        @author hwliang<2021-07-24>
        @param _obj<Controller> 控制器对像
        @param get<dict> 请求参数
        @return void
    '''
    try:
        mod_result = _obj.model(get)
        if mod_result is None:
            return
        result = {'callback': get.get("ws_callback", get.get("callback", "")), 'result': mod_result}
        get._ws.send(public.getJson(result))
    except:
        if public.is_debug():
            public.print_error()
        return

# ========================== 邮局退订链接 ====================
@app.route('/mailUnsubscribe', methods=method_all)
def mailUnsubscribe():
    comReturn = comm.local()
    if comReturn: return comReturn
    g.is_aes = False
    import mailUnsubscribe
    reg = mailUnsubscribe.mailUnsubscribe()
    defs = ('Unsubscribe', 'Subscribe')
    return publicObject(reg, defs, None, None)
