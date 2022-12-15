# coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板 
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: hwliang <hwl@bt.cn>
# +-------------------------------------------------------------------
import logging
import sys
import json
import os
import threading
import time
import re
import uuid
import psutil
panel_path = '/www/server/panel'
if not os.name in ['nt']:
    os.chdir(panel_path)
if not 'class/' in sys.path:
    sys.path.insert(0, 'class/')

from flask import Config, Flask, session, render_template, send_file, request, redirect, g, make_response, \
    render_template_string, abort,stream_with_context, Response as Resp
from cachelib import SimpleCache
from werkzeug.wrappers import Response
from flask_session import Session
from flask_compress import Compress


cache = SimpleCache()
import public

# 初始化Flask应用
app = Flask(__name__, template_folder="templates/{}".format(public.GetConfigValue('template')))
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
app.secret_key = public.md5(str(os.uname()) + str(psutil.boot_time())) # uuid.UUID(int=uuid.getnode()).hex[-12:]
local_ip = None
my_terms = {}
app.config['SESSION_MEMCACHED'] = SimpleCache(1000,86400)
app.config['SESSION_TYPE'] = 'memcached'
app.config['SESSION_PERMANENT'] = True
app.config['SESSION_USE_SIGNER'] = True
app.config['SESSION_KEY_PREFIX'] = 'BT_:'
app.config['SESSION_COOKIE_NAME'] = public.md5(app.secret_key)
app.config['PERMANENT_SESSION_LIFETIME'] = 86400 * 30
if app.config['SSL']:
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['SESSION_COOKIE_SECURE'] = True
else:
    app.config['SESSION_COOKIE_SAMESITE'] = None


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
if os.path.exists(admin_path_file): admin_path = public.readFile(admin_path_file).strip()
admin_path_checks = [
    '/',
    '/san',
    '/bak',
    '/monitor',
    '/abnormal',
    '/close',
    '/task',
    '/login',
    '/config',
    '/site',
    '/sites',
    '/ftp',
    '/public',
    '/database',
    '/data',
    '/download_file',
    '/control',
    '/crontab',
    '/firewall',
    '/files',
    '/soft',
    '/ajax',
    '/system',
    '/panel_data',
    '/code',
    '/ssl',
    '/plugin',
    '/wxapp',
    '/hook',
    '/safe',
    '/yield',
    '/downloadApi',
    '/pluginApi',
    '/auth',
    '/download',
    '/cloud',
    '/webssh',
    '/connect_event',
    '/panel',
    '/acme',
    '/down',
    '/api',
    '/tips',
    '/message',
    '/warning',
    '/bind',
    '/daily'
]
if admin_path in admin_path_checks: admin_path = '/bt'
uri_match = re.compile(r"(^/static/[\w_\./\-]+\.(js|css|png|jpg|gif|ico|svg|woff|woff2|ttf|otf|eot|map)$|^/[\w_\./\-]*$)")

# ===================================Flask HOOK========================#

# Flask请求勾子
@app.before_request
def request_check():
    if request.method not in ['GET','POST']:return abort(404)
    g.request_time = time.time()
    # 路由和URI长度过滤
    if len(request.path) > 256: return abort(403)
    if len(request.url) > 1024: return abort(403)
    # URI过滤
    if not uri_match.match(request.path): return abort(403)
    # POST参数过滤
    if request.path in ['/login', '/safe', '/hook', '/public', '/down', '/get_app_bind_status', '/check_bind']:
        pdata = request.form.to_dict()
        for k in pdata.keys():
            if len(k) > 48: return abort(403)
            if len(pdata[k]) > 256: return abort(403)
    if session.get('debug') == 1: return

    if app.config['BASIC_AUTH_OPEN']:
        if request.path in ['/public', '/download', '/mail_sys', '/hook', '/down', '/check_bind',
                            '/get_app_bind_status']: return
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

    if request.path.find('/static/') != -1 or request.path == '/code':
        if not 'login' in session and not 'admin_auth' in session and not 'down' in session:
            return abort(401)
    domain_check = public.check_domain_panel()
    if domain_check: return domain_check
    if public.is_local():
        not_networks = ['uninstall_plugin', 'install_plugin', 'UpdatePanel']
        if request.args.get('action') in not_networks:
            return public.returnJson(False, 'INIT_REQUEST_CHECK_LOCAL_ERR'), json_header

    if request.path in ['/site','/ftp','/database','/soft','/control','/firewall','/files','/xterm','/crontab','/config']:
        if not public.is_bind():
            return redirect('/bind',302)
        if public.is_error_path():
            return redirect('/error',302)
        if not request.path in ['/config']:
            if session.get('password_expire',False):
                return redirect('/modify_password',302)


# Flask 请求结束勾子
@app.teardown_request
def request_end(reques=None):
    if request.method not in ['GET','POST']:return
    not_acts = ['GetTaskSpeed', 'GetNetWork', 'check_pay_status', 'get_re_order_status', 'get_order_stat']
    key = request.args.get('action')
    if not key in not_acts and request.full_path.find('/static/') == -1:
        public.write_request_log()
        if 'api_request' in g:
            if g.api_request:
                session.clear()


# Flask 404页面勾子
@app.errorhandler(404)
def error_404(e):
    if request.method not in ['GET','POST']:return
    if not session.get('login',None): 
        g.auth_error = True
        return public.error_not_login()
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


# Flask 403页面勾子
@app.errorhandler(403)
def error_403(e):
    if request.method not in ['GET','POST']:return
    if not session.get('login',None): 
        g.auth_error = True
        return public.error_not_login()
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


# Flask 500页面勾子
@app.errorhandler(500)
def error_500(e):
    if request.method not in ['GET','POST']:return
    if not session.get('login',None): 
        g.auth_error = True
        return public.error_not_login()
    ss = '''404 Not Found: The requested URL was not found on the server. If you entered the URL manually please check your spelling and try again.

During handling of the above exception, another exception occurred:'''
    error_info = public.get_error_info().strip().split(ss)[-1].strip()
    request_info = '''REQUEST_DATE: {request_date}
 PAN_VERSION: {panel_version}
  OS_VERSION: {os_version}
 REMOTE_ADDR: {remote_addr}
 REQUEST_URI: {method} {full_path}
REQUEST_FORM: {request_form}
  USER_AGENT: {user_agent}'''.format(
    request_date = public.getDate(),
    remote_addr = public.GetClientIp(),
    method = request.method,
    full_path = request.full_path,
    request_form = request.form.to_dict(),
    user_agent = request.headers.get('User-Agent'),
    panel_version = public.version(),
    os_version = public.get_os_version()
)
    error_title = error_info.split("\n")[-1].replace('public.PanelError: ','').strip()
    if error_info.find('连接云端服务器失败') != -1:
        error_title = "连接云端服务器失败!"
    result = public.readFile(public.get_panel_path() + '/BTPanel/templates/default/panel_error.html').format(error_title=error_title,request_info = request_info,error_msg=error_info)
    return Resp(result,500)

# ===================================Flask HOOK========================#


# ===================================普通路由区========================#
@app.route('/', methods=method_all)
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
        return redirect('/bind',302)
    
    import system
    data = system.system().GetConcifInfo()
    data['bind'] = False
    if not os.path.exists('data/userInfo.json'):
        data['bind'] = os.path.exists('data/bind.pl')
    # data[public.to_string([112, 100])], data['pro_end'], data['ltd_end'] = get_pd()
    data[public.to_string([112, 100])], data['pro_end'], data['ltd_end'] = get_pd()
    data['siteCount'] = public.M('sites').count()
    data['ftpCount'] = public.M('ftps').count()
    data['databaseCount'] = public.M('databases').count()
    data['lan'] = public.GetLan('index')
    data['js_random'] = get_js_random()
    return render_template('index.html', data=data)


@app.route('/xterm', methods=method_all)
def xterm():
    # 宝塔终端管理
    comReturn = comm.local()
    if comReturn: return comReturn
    if request.method == method_get[0]:
        import system
        data = system.system().GetConcifInfo()
        return render_template('xterm.html', data=data)
    import ssh_terminal
    ssh_host_admin = ssh_terminal.ssh_host_admin()
    defs = (
    'get_host_list', 'get_host_find', 'modify_host', 'create_host', 'remove_host', 'set_sort', 'get_command_list',
    'create_command', 'get_command_find', 'modify_command', 'remove_command')
    return publicObject(ssh_host_admin, defs, None)


@app.route('/bind', methods=method_get)
def bind():
    comReturn = comm.local()
    if comReturn: return comReturn
    if public.is_bind(): return redirect('/',302)
    data = {}
    g.title = '请先绑定宝塔帐号'
    return render_template('bind.html', data=data)

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
    return render_template('modify_password.html', data=data)



@app.route('/site', methods=method_all)
def site(pdata=None):
    # 网站管理
    comReturn = comm.local()
    if comReturn: return comReturn
    if request.method == method_get[0] and not pdata:
        # data = {}
        import system
        data = system.system().GetConcifInfo()
        data['isSetup'] = True
        data['lan'] = public.getLan('site')
        data['js_random'] = get_js_random()
        if os.path.exists(public.GetConfigValue('setup_path') + '/nginx') == False \
                and os.path.exists(public.GetConfigValue('setup_path') + '/apache') == False \
                and os.path.exists('/usr/local/lsws/bin/lswsctrl') == False:
            data['isSetup'] = False
        is_bind()
        return render_template('site.html', data=data)
    import panelSite
    siteObject = panelSite.panelSite()

    defs = (
    'upload_csv', 'create_website_multiple', 'del_redirect_multiple', 'del_proxy_multiple', 'delete_dir_auth_multiple',
    'delete_dir_bind_multiple', 'delete_domain_multiple', 'set_site_etime_multiple','check_del_data','set_https_mode','get_https_mode',
    'set_site_php_version_multiple', 'delete_website_multiple', 'set_site_status_multiple', 'get_site_domains',
    'GetRedirectFile', 'SaveRedirectFile', 'DeleteRedirect', 'GetRedirectList', 'CreateRedirect', 'ModifyRedirect',
    'set_dir_auth', 'delete_dir_auth', 'get_dir_auth', 'modify_dir_auth_pass', 'export_domains', 'import_domains',
    'GetSiteLogs', 'GetSiteDomains', 'GetSecurity', 'SetSecurity', 'ProxyCache', 'CloseToHttps', 'HttpToHttps',
    'SetEdate','get_site_errlog',
    'SetRewriteTel', 'GetCheckSafe', 'CheckSafe', 'GetDefaultSite', 'SetDefaultSite', 'CloseTomcat', 'SetTomcat',
    'apacheAddPort',
    'AddSite', 'GetPHPVersion', 'SetPHPVersion', 'DeleteSite', 'AddDomain', 'DelDomain', 'GetDirBinding',
    'AddDirBinding', 'GetDirRewrite',
    'DelDirBinding', 'get_site_types', 'add_site_type', 'remove_site_type', 'modify_site_type_name', 'set_site_type',
    'UpdateRulelist',
    'SetSiteRunPath', 'GetSiteRunPath', 'SetPath', 'SetIndex', 'GetIndex', 'GetDirUserINI', 'SetDirUserINI',
    'GetRewriteList', 'SetSSL',
    'SetSSLConf', 'CreateLet', 'CloseSSLConf', 'GetSSL', 'SiteStart', 'SiteStop', 'Set301Status', 'Get301Status',
    'CloseLimitNet', 'SetLimitNet',
    'GetLimitNet', 'RemoveProxy', 'GetProxyList', 'GetProxyDetals', 'CreateProxy', 'ModifyProxy', 'GetProxyFile',
    'SaveProxyFile', 'ToBackup',
    'DelBackup', 'GetSitePHPVersion', 'logsOpen', 'GetLogsStatus', 'CloseHasPwd', 'SetHasPwd', 'GetHasPwd', 'GetDnsApi',
    'SetDnsApi')
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
        if os.path.exists(public.GetConfigValue('setup_path') + '/pure-ftpd') == False: data['isSetup'] = False
        data['lan'] = public.GetLan('ftp')
        is_bind()
        return render_template('ftp.html', data=data)
    import ftp
    ftpObject = ftp.ftp()
    defs = ('AddUser', 'DeleteUser', 'SetUserPassword', 'SetStatus', 'setPort')
    return publicObject(ftpObject, defs, None, pdata)


@app.route('/database', methods=method_all)
def database(pdata=None):
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
                session['phpmyadminDir'] = 'http://' + public.GetHost() + ':' + pmd[1] + '/' + pmd[0]
        ajax.ajax().set_phpmyadmin_session()
        import system
        data = system.system().GetConcifInfo()
        data['isSetup'] = os.path.exists(public.GetConfigValue('setup_path') + '/mysql/bin')
        data['mysql_root'] = public.M('config').where('id=?', (1,)).getField('mysql_root')
        data['lan'] = public.GetLan('database')
        data['js_random'] = get_js_random()
        is_bind()
        return render_template('database.html', data=data)
    import database
    databaseObject = database.database()
    defs = ('GetdataInfo','check_del_data','get_database_size', 'GetInfo', 'ReTable', 'OpTable', 'AlTable', 'GetSlowLogs', 'GetRunStatus',
            'SetDbConf', 'GetDbStatus', 'BinLog', 'GetErrorLog', 'GetMySQLInfo', 'SetDataDir', 'SetMySQLPort','AddCloudDatabase',
            'AddDatabase', 'DeleteDatabase', 'SetupPassword', 'ResDatabasePassword', 'ToBackup', 'DelBackup','AddCloudServer','GetCloudServer','RemoveCloudServer','ModifyCloudServer',
            'InputSql', 'SyncToDatabases', 'SyncGetDatabases', 'GetDatabaseAccess', 'SetDatabaseAccess')
    return publicObject(databaseObject, defs, None, pdata)


@app.route('/acme', methods=method_all)
def acme(pdata=None):
    # Let's 证书管理
    comReturn = comm.local()
    if comReturn: return comReturn
    import acme_v2
    acme_v2_object = acme_v2.acme_v2()
    defs = ('get_orders', 'remove_order', 'get_order_find', 'revoke_order', 'create_order', 'get_account_info',
            'set_account_info', 'update_zip', 'get_cert_init_api',
            'get_auths', 'auth_domain', 'check_auth_status', 'download_cert', 'apply_cert', 'renew_cert',
            'apply_cert_api', 'apply_dns_auth')
    return publicObject(acme_v2_object, defs, None, pdata)


@app.route('/message/<action>', methods=method_all)
def message(action=None):
    # 提示消息管理
    comReturn = comm.local()
    if comReturn: return comReturn
    import panelMessage
    message_object = panelMessage.panelMessage()
    defs = (
    'get_messages', 'get_message_find', 'create_message', 'status_message', 'remove_message', 'get_messages_all')
    return publicObject(message_object, defs, action, None)




@app.route('/api', methods=method_all)
def api(pdata=None):
    # APP使用的API接口管理
    comReturn = comm.local()
    if comReturn: return comReturn
    import panelApi
    api_object = panelApi.panelApi()
    defs = ('get_token', 'check_bind', 'get_bind_status', 'get_apps', 'add_bind_app', 'remove_bind_app', 'set_token',
            'get_tmp_token', 'get_app_bind_status', 'login_for_app')
    return publicObject(api_object, defs, None, pdata)


@app.route('/control', methods=method_all)
def control(pdata=None):
    # 监控页面
    comReturn = comm.local()
    if comReturn: return comReturn
    import system
    data = system.system().GetConcifInfo()
    data['lan'] = public.GetLan('control')
    return render_template('control.html', data=data)


@app.route('/firewall', methods=method_all)
def firewall(pdata=None):
    # 安全页面
    comReturn = comm.local()
    if comReturn: return comReturn
    if request.method == method_get[0] and not pdata:
        import system
        data = system.system().GetConcifInfo()
        data['lan'] = public.GetLan('firewall')
        data['js_random'] = get_js_random()
        return render_template('firewall.html', data=data)
    import firewalls
    firewallObject = firewalls.firewalls()
    defs = ('GetList', 'AddDropAddress', 'DelDropAddress', 'FirewallReload', 'SetFirewallStatus',
            'AddAcceptPort', 'DelAcceptPort', 'SetSshStatus', 'SetPing', 'SetSshPort', 'GetSshInfo','SetFirewallStatus')
    return publicObject(firewallObject, defs, None, pdata)


@app.route('/ssh_security', methods=method_all)
def ssh_security(pdata=None):
    # SSH安全
    comReturn = comm.local()
    if comReturn: return comReturn
    if request.method == method_get[0] and not pdata:
        data = {}
        data['lan'] = public.GetLan('firewall')
        data['js_random'] = get_js_random()
        return render_template('firewall.html', data=data)
    import ssh_security
    firewallObject = ssh_security.ssh_security()
    defs = ('san_ssh_security', 'set_password', 'set_sshkey', 'stop_key', 'get_config',
            'stop_password', 'get_key', 'return_ip', 'add_return_ip', 'del_return_ip', 'start_jian', 'stop_jian',
            'get_jian', 'get_logs','set_root','stop_root','start_auth_method','stop_auth_method','get_auth_method','check_so_file','get_so_file','get_pin')
    return publicObject(firewallObject, defs, None, pdata)


@app.route('/monitor', methods=method_all)
def panel_monitor(pdata=None):
    # 云控统计信息
    comReturn = comm.local()
    if comReturn: return comReturn
    import monitor
    dataObject = monitor.Monitor()
    defs = ('get_spider', 'get_exception', 'get_request_count_qps', 'load_and_up_flow', 'get_request_count_by_hour')
    return publicObject(dataObject, defs, None, pdata)


@app.route('/san', methods=method_all)
def san_baseline(pdata=None):
    # 云控安全扫描
    comReturn = comm.local()
    if comReturn: return comReturn
    import san_baseline
    dataObject = san_baseline.san_baseline()
    defs = ('start', 'get_api_log', 'get_resut', 'get_ssh_errorlogin', 'repair', 'repair_all')
    return publicObject(dataObject, defs, None, pdata)


@app.route('/password', methods=method_all)
def panel_password(pdata=None):
    # 云控密码管理
    comReturn = comm.local()
    if comReturn: return comReturn
    import password
    dataObject = password.password()
    defs = ('set_root_password', 'get_mysql_root', 'set_mysql_password', 'set_panel_password',
            'SetPassword', 'SetSshKey', 'StopKey', 'GetConfig', 'StopPassword', 'GetKey',
            'get_databses', 'rem_mysql_pass', 'set_mysql_access', "get_panel_username"
            )
    return publicObject(dataObject, defs, None, pdata)


@app.route('/warning', methods=method_all)
def panel_warning(pdata=None):
    # 首页安全警告
    comReturn = comm.local()
    if comReturn: return comReturn

    get = get_input()
    ikey = 'warning_list'
    if get.action == 'get_list':
        result = cache.get(ikey)
        if not result or 'force' in get:
            result = public.ExecShell("{} {}/script/warning_list.py".format(public.get_python_bin(),public.get_panel_path()))[0]
            try:
                json.loads(result)
                cache.set(ikey, result, 3600)
            except:
                result = '{"ignore":[],"risk":[],"security":[]}'
        return result,json_header
    import panelWarning
    dataObject = panelWarning.panelWarning()
    defs = ('get_list', 'set_ignore', 'check_find')
    if get.action == 'set_ignore':
        cache.delete(ikey)
    return publicObject(dataObject, defs, None, pdata)


@app.route('/bak', methods=method_all)
def backup_bak(pdata=None):
    # 云控备份服务
    comReturn = comm.local()
    if comReturn: return comReturn
    import backup_bak
    dataObject = backup_bak.backup_bak()
    defs = ('get_sites', 'get_databases', 'backup_database', 'backup_site', 'backup_path', 'get_database_progress',
            'get_site_progress', 'down', 'get_down_progress', 'download_path', 'backup_site_all',
            'get_all_site_progress',
            'backup_date_all', 'get_all_date_progress'
            )
    return publicObject(dataObject, defs, None, pdata)


@app.route('/abnormal', methods=method_all)
def abnormal(pdata=None):
    # 云控系统统计
    comReturn = comm.local()
    if comReturn: return comReturn
    import abnormal
    dataObject = abnormal.abnormal()
    defs = ('mysql_server', 'mysql_cpu', 'mysql_count', 'php_server', 'php_conn_max',
            'php_cpu', 'CPU', 'Memory', 'disk', 'not_root_user', 'start'
            )
    return publicObject(dataObject, defs, None, pdata)

@app.route('/project/<mod_name>/<def_name>', methods=method_all)
def project(mod_name,def_name):
    comReturn = comm.local()
    if comReturn: return comReturn
    from panelProjectController import ProjectController
    project_obj = ProjectController()
    defs = ('model',)
    get = get_input()
    get.action = 'model'
    get.mod_name = mod_name
    get.def_name = def_name

    return publicObject(project_obj,defs,None,get)

@app.route('/dbmodel/<mod_name>/<def_name>', methods=method_all)
def dbmodel(mod_name,def_name):
    comReturn = comm.local()
    if comReturn: return comReturn
    from panelDatabaseController import DatabaseController
    database_obj = DatabaseController()
    defs = ('model',)
    get = get_input()
    get.action = 'model'
    get.mod_name = mod_name
    get.def_name = def_name

    return publicObject(database_obj,defs,None,get)



@app.route('/files', methods=method_all)
def files(pdata=None):
    # 文件管理
    comReturn = comm.local()
    if comReturn: return comReturn
    if request.method == method_get[0] and not request.args.get('path') and not pdata:
        import system
        data = system.system().GetConcifInfo()
        data['recycle_bin'] = os.path.exists('data/recycle_bin.pl')
        data['lan'] = public.GetLan('files')
        data['js_random'] = get_js_random()
        return render_template('files.html', data=data)
    import files
    filesObject = files.files()
    defs = ('CheckExistsFiles', 'GetExecLog', 'GetSearch', 'ExecShell', 'GetExecShellMsg', 'exec_git', 'exec_composer',
            'create_download_url','get_images_resize',
            'UploadFile', 'GetDir', 'CreateFile', 'CreateDir', 'DeleteDir', 'DeleteFile', 'get_download_url_list',
            'remove_download_url', 'modify_download_url',
            'CopyFile', 'CopyDir', 'MvFile', 'GetFileBody', 'SaveFileBody', 'Zip', 'UnZip', 'get_download_url_find',
            'set_file_ps','CreateLink','add_files_rsync',
            'SearchFiles', 'upload', 'read_history', 're_history', 'auto_save_temp', 'get_auto_save_body', 'get_videos',
            'GetFileAccess', 'SetFileAccess', 'GetDirSize', 'SetBatchData', 'BatchPaste', 'install_rar',
            'get_path_size','get_file_attribute','get_file_hash',
            'DownloadFile', 'GetTaskSpeed', 'CloseLogs', 'InstallSoft', 'UninstallSoft', 'SaveTmpFile',
            'get_composer_version', 'exec_composer', 'update_composer',
            'GetTmpFile', 'del_files_store', 'add_files_store', 'get_files_store', 'del_files_store_types',
            'add_files_store_types', 'exec_git','upload_file_exists',
            'RemoveTask', 'ActionTask', 'Re_Recycle_bin', 'Get_Recycle_bin', 'Del_Recycle_bin', 'Close_Recycle_bin',
            'Recycle_bin', 'file_webshell_check', 'dir_webshell_check','files_search','files_replace','get_replace_logs'
            )
    return publicObject(filesObject, defs, None, pdata)


@app.route('/crontab', methods=method_all)
def crontab(pdata=None):
    # 计划任务
    comReturn = comm.local()
    if comReturn: return comReturn
    if request.method == method_get[0] and not pdata:
        import system
        data = system.system().GetConcifInfo()
        data['lan'] = public.GetLan('crontab')
        data['js_random'] = get_js_random()
        return render_template('crontab.html', data=data)
    import crontab
    crontabObject = crontab.crontab()
    defs = ('GetCrontab', 'AddCrontab', 'GetDataList', 'GetLogs', 'DelLogs', 'DelCrontab',
            'StartTask', 'set_cron_status', 'get_crond_find', 'modify_crond'
            )
    return publicObject(crontabObject, defs, None, pdata)


@app.route('/soft', methods=method_all)
def soft(pdata=None):
    # 软件商店页面
    comReturn = comm.local()
    if comReturn: return comReturn
    import system
    data = system.system().GetConcifInfo()
    data['lan'] = public.GetLan('soft')
    data['js_random'] = get_js_random()
    is_bind()
    return render_template('soft.html', data=data)


@app.route('/config', methods=method_all)
def config(pdata=None):
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
        if not os.path.exists(sess_out_path): public.writeFile(sess_out_path, '86400')
        s_time_tmp = public.readFile(sess_out_path)
        if not s_time_tmp: s_time_tmp = '0'
        data['session_timeout'] = int(s_time_tmp)
        if c_obj.get_ipv6_listen(None): data['ipv6'] = 'checked'
        if c_obj.get_token(None)['open']: data['api'] = 'checked'
        data['basic_auth'] = c_obj.get_basic_auth_stat(None)
        data['status_code'] = c_obj.get_not_auth_status()
        data['basic_auth']['value'] = public.getMsg('CLOSED')
        if data['basic_auth']['open']: data['basic_auth']['value'] = public.getMsg('OPENED')
        data['debug'] = ''
        data['show_recommend'] = not os.path.exists('data/not_recommend.pl')
        data['show_workorder'] = not os.path.exists('data/not_workorder.pl')
        data['js_random'] = get_js_random()
        if app.config['DEBUG']: data['debug'] = 'checked'
        data['is_local'] = ''
        if public.is_local(): data['is_local'] = 'checked'
        is_bind()
        return render_template('config.html', data=data)

    import config
    defs = (
    'set_file_deny', 'del_file_deny', 'get_file_deny',
    'get_ols_private_cache_status', 'get_ols_value', 'set_ols_value', 'get_ols_private_cache', 'get_ols_static_cache',
    'set_ols_static_cache', 'switch_ols_private_cache', 'set_ols_private_cache',
    'set_coll_open', 'get_qrcode_data', 'check_two_step', 'set_two_step_auth', 'create_user', 'remove_user',
    'modify_user','set_click_logs','get_node_config','set_node_config',
    'get_key', 'get_php_session_path', 'set_php_session_path', 'get_cert_source', 'get_users',
    'set_local', 'set_debug', 'get_panel_error_logs', 'clean_panel_error_logs', 'get_menu_list', 'set_hide_menu_list',
    'get_basic_auth_stat', 'set_basic_auth', 'get_cli_php_version', 'get_tmp_token', 'get_temp_login', 'set_temp_login',
    'remove_temp_login', 'clear_temp_login', 'get_temp_login_logs','set_request_iptype','set_request_type',
    'set_cli_php_version', 'DelOldSession', 'GetSessionCount', 'SetSessionConf', 'show_recommend', 'show_workorder',
    'GetSessionConf', 'get_ipv6_listen', 'set_ipv6_status', 'GetApacheValue', 'SetApacheValue',
    'GetNginxValue', 'SetNginxValue', 'get_token', 'set_token', 'set_admin_path', 'is_pro','set_not_auth_status',
    'get_php_config', 'get_config', 'SavePanelSSL', 'GetPanelSSL', 'GetPHPConf', 'SetPHPConf',
    'GetPanelList', 'AddPanelInfo', 'SetPanelInfo', 'DelPanelInfo', 'ClickPanelInfo', 'SetPanelSSL',
    'SetTemplates', 'Set502', 'setPassword', 'setUsername', 'setPanel', 'setPathInfo', 'setPHPMaxSize',
    'getFpmConfig', 'setFpmConfig', 'setPHPMaxTime', 'syncDate', 'setPHPDisable', 'SetControl',
    'ClosePanel', 'AutoUpdatePanel', 'SetPanelLock', 'return_mail_list', 'del_mail_list', 'add_mail_address',
    'user_mail_send', 'get_user_mail', 'set_dingding', 'get_dingding', 'get_settings', 'user_stmp_mail_send',
    'user_dingding_send','get_login_send','set_login_send','set_empty','clear_login_send','get_login_log','login_ipwhite',
    'set_ssl_verify','get_ssl_verify','get_password_config','set_password_expire','set_password_safe'
    )
    return publicObject(config.config(), defs, None, pdata)


@app.route('/ajax', methods=method_all)
def ajax(pdata=None):
    # 面板系统服务状态接口
    comReturn = comm.local()
    if comReturn: return comReturn
    import ajax
    ajaxObject = ajax.ajax()
    defs = ('get_lines', 'php_info', 'change_phpmyadmin_ssl_port', 'set_phpmyadmin_ssl', 'get_phpmyadmin_ssl','get_pd','get_pay_type',
            'check_user_auth', 'to_not_beta', 'get_beta_logs', 'apple_beta', 'GetApacheStatus', 'GetCloudHtml',
            'get_load_average', 'GetOpeLogs', 'GetFpmLogs', 'GetFpmSlowLogs', 'SetMemcachedCache', 'GetMemcachedStatus',
            'GetRedisStatus', 'GetWarning', 'SetWarning', 'CheckLogin', 'GetSpeed', 'GetAd', 'phpSort', 'ToPunycode',
            'GetBetaStatus', 'SetBeta', 'setPHPMyAdmin', 'delClose', 'KillProcess', 'GetPHPInfo', 'GetQiniuFileList','get_process_tops','get_process_cpu_high',
            'UninstallLib', 'InstallLib', 'SetQiniuAS', 'GetQiniuAS', 'GetLibList', 'GetProcessList', 'GetNetWorkList',
            'GetNginxStatus', 'GetPHPStatus', 'GetTaskCount', 'GetSoftList', 'GetNetWorkIo', 'GetDiskIo', 'GetCpuIo',
            'CheckInstalled', 'UpdatePanel', 'GetInstalled', 'GetPHPConfig', 'SetPHPConfig','log_analysis','speed_log','get_result','get_detailed')

    return publicObject(ajaxObject, defs, None, pdata)


@app.route('/system', methods=method_all)
def system(pdata=None):
    # 面板系统状态接口
    comReturn = comm.local()
    if comReturn: return comReturn
    import system
    sysObject = system.system()
    defs = ('get_io_info', 'UpdatePro', 'GetAllInfo', 'GetNetWorkApi', 'GetLoadAverage', 'ClearSystem',
            'GetNetWorkOld', 'GetNetWork', 'GetDiskInfo', 'GetCpuInfo', 'GetBootTime', 'GetSystemVersion',
            'GetMemInfo', 'GetSystemTotal', 'GetConcifInfo', 'ServiceAdmin', 'ReWeb', 'RestartServer', 'ReMemory',
            'RepPanel')
    return publicObject(sysObject, defs, None, pdata)


@app.route('/deployment', methods=method_all)
def deployment(pdata=None):
    # 一键部署接口
    comReturn = comm.local()
    if comReturn: return comReturn
    import plugin_deployment
    sysObject = plugin_deployment.plugin_deployment()
    defs = ('GetList', 'AddPackage', 'DelPackage', 'SetupPackage', 'GetSpeed', 'GetPackageOther')
    return publicObject(sysObject, defs, None, pdata)


@app.route('/data', methods=method_all)
@app.route('/panel_data', methods=method_all)
def panel_data(pdata=None):
    # 从数据库获取数据接口
    comReturn = comm.local()
    if comReturn: return comReturn
    import data
    dataObject = data.data()
    defs = ('setPs', 'getData', 'getFind', 'getKey')
    return publicObject(dataObject, defs, None, pdata)


@app.route('/ssl', methods=method_all)
def ssl(pdata=None):
    # 商业SSL证书申请接口
    comReturn = comm.local()
    if comReturn: return comReturn
    import panelSSL
    toObject = panelSSL.panelSSL()
    defs = ('check_url_txt', 'RemoveCert', 'renew_lets_ssl', 'SetCertToSite', 'GetCertList', 'SaveCert', 'GetCert',
            'GetCertName', 'again_verify','cancel_cert_order','get_cert_admin','apply_order_ca',
            'DelToken', 'GetToken', 'GetUserInfo', 'GetOrderList', 'GetDVSSL', 'Completed', 'SyncOrder',
            'download_cert', 'set_cert', 'cancel_cert_order','ApplyDVSSL','apply_cert_order_pay',
            'get_order_list', 'get_order_find', 'apply_order_pay', 'get_pay_status', 'apply_order', 'get_verify_info',
            'get_verify_result', 'get_product_list', 'set_verify_info','renew_cert_order',
            'GetSSLInfo', 'downloadCRT', 'GetSSLProduct', 'Renew_SSL', 'Get_Renew_SSL','GetAuthToken','GetBindCode','apply_cert_install_pay')
    get = get_input()

    if get.action == 'download_cert':
        from io import BytesIO
        import base64
        result = toObject.download_cert(get)
        fp = BytesIO(base64.b64decode(result['data']))
        return send_file(fp, attachment_filename=result['filename'], as_attachment=True, mimetype='application/zip')
    result = publicObject(toObject, defs, get.action, get)
    return result


@app.route('/task', methods=method_all)
def task(pdata=None):
    # 后台任务接口
    comReturn = comm.local()
    if comReturn: return comReturn
    import panelTask
    toObject = panelTask.bt_task()
    defs = ('get_task_lists', 'remove_task', 'get_task_find', "get_task_log_by_id")
    result = publicObject(toObject, defs, None, pdata)
    return result


@app.route('/plugin', methods=method_all)
def plugin(pdata=None):
    # 插件系统接口
    comReturn = comm.local()
    if comReturn: return comReturn
    import panelPlugin
    pluginObject = panelPlugin.panelPlugin()
    defs = (
    'set_score', 'get_score', 'update_zip', 'input_zip', 'export_zip', 'add_index', 'remove_index', 'sort_index',
    'install_plugin', 'uninstall_plugin', 'get_soft_find', 'get_index_list', 'get_soft_list', 'get_cloud_list',
    'check_deps', 'flush_cache', 'GetCloudWarning', 'install', 'unInstall', 'getPluginList', 'getPluginInfo','repair_plugin','upgrade_plugin',
    'get_make_args', 'add_make_args','input_package','export_zip','get_download_speed','get_usually_plugin','get_plugin_upgrades','close_install',
    'getPluginStatus', 'setPluginStatus', 'a', 'getCloudPlugin', 'getConfigHtml', 'savePluginSort', 'del_make_args',
    'set_make_args','get_cloud_list_status','is_verify_unbinding')
    return publicObject(pluginObject, defs, None, pdata)


@app.route('/wxapp', methods=method_all)
@app.route('/panel_wxapp', methods=method_all)
def panel_wxapp(pdata=None):
    # 微信小程序绑定接口
    comReturn = comm.local()
    if comReturn: return comReturn
    import wxapp
    toObject = wxapp.wxapp()
    defs = ('blind', 'get_safe_log', 'blind_result', 'get_user_info', 'blind_del', 'blind_qrcode')
    result = publicObject(toObject, defs, None, pdata)
    return result


@app.route('/auth', methods=method_all)
def auth(pdata=None):
    # 面板认证接口
    comReturn = comm.local()
    if comReturn: return comReturn
    import panelAuth
    toObject = panelAuth.panelAuth()
    defs = ('get_plugin_remarks','get_re_order_status_plugin', 'create_plugin_other_order', 'get_order_stat',
            'get_voucher_plugin', 'create_order_voucher_plugin', 'get_product_discount_by',
            'get_re_order_status', 'create_order_voucher', 'create_order', 'get_order_status',
            'get_voucher', 'flush_pay_status', 'create_serverid', 'check_serverid',
            'get_plugin_list', 'check_plugin', 'get_buy_code', 'check_pay_status','get_wx_order_status',
            'get_renew_code', 'check_renew_code', 'get_business_plugin',
            'get_ad_list', 'check_plugin_end', 'get_plugin_price','set_user_adviser')
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
    if not filename: return public.ReturnJson(False, "INIT_ARGS_ERR"), json_header
    if filename in ['alioss', 'qiniu', 'upyun', 'txcos', 'ftp', 'msonedrive', 'gcloud_storage', 'gdrive',
                    'aws_s3']: return panel_cloud()
    if not os.path.exists(filename): return public.ReturnJson(False, "FILE_NOT_EXISTS"), json_header

    if request.args.get('play') == 'true':
        import panelVideo
        start, end = panelVideo.get_range(request)
        return panelVideo.partial_response(filename, start, end)
    else:
        mimetype = "application/octet-stream"
        extName = filename.split('.')[-1]
        if extName in ['png', 'gif', 'jpeg', 'jpg']: mimetype = None
        return send_file(filename, mimetype=mimetype,
                         as_attachment=True,
                         add_etags=True,
                         conditional=True,
                         attachment_filename=os.path.basename(filename),
                         cache_timeout=0)


@app.route('/cloud', methods=method_all)
def panel_cloud():
    # 从对像存储下载备份文件接口
    comReturn = comm.local()
    if comReturn: return comReturn
    get = get_input()
    _filename = get.filename
    plugin_name = ""
    if _filename.find('|') != -1:
        plugin_name = get.filename.split('|')[1]
    else:
        plugin_name = get.filename

    if not os.path.exists('plugin/' + plugin_name + '/' + plugin_name + '_main.py'):
        return public.returnJson(False, 'INIT_PLUGIN_NOT_EXISTS'), json_header
    public.package_path_append('plugin/' + plugin_name)
    plugin_main = __import__(plugin_name + '_main')
    public.mod_reload(plugin_main)
    tmp = eval("plugin_main.%s_main()" % plugin_name)
    if not hasattr(tmp, 'download_file'): return public.returnJson(False, 'INIT_PLUGIN_NOT_DOWN_FUN'), json_header
    download_url = tmp.download_file(get.name)
    if plugin_name == 'ftp':
        if download_url.find("ftp") != 0: download_url = "ftp://" + download_url
    else:
        if download_url.find('http') != 0: download_url = 'http://' + download_url
    
    if "toserver" in get and get.toserver=="true":
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
    if admin_path != '/bt' and os.path.exists(admin_path_file) and not 'admin_auth' in session:
        is_auth_path = True
    # 登录输入验证
    if request.method == method_post[0]:
        if is_auth_path:
            g.auth_error = True
            return public.error_not_login(None)
        v_list = ['username', 'password', 'code', 'vcode', 'cdn_url']
        for v in v_list:
            pv = request.form.get(v, '').strip()
            if v == 'cdn_url':
                if len(pv) > 32: return public.returnMsg(False, '错误的参数长度!'), json_header
                if not re.match(r"^[\w\.-]+$", pv): public.returnJson(False, '错误的参数格式'), json_header
                continue

            if not pv: continue
            p_len = 32
            if v == 'code': p_len = 4
            if v == 'vcode': p_len = 6
            if len(pv) != p_len:
                if v == 'code': return public.returnJson(False, '验证码长度错误'), json_header
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

    if hasattr(get, 'dologin'):
        login_path = '/login'
        if not 'login' in session: return redirect(login_path)
        if os.path.exists(admin_path_file): login_path = route_path
        if session['login'] != False:
            session['login'] = False
            cache.set('dologin', True)
            public.WriteLog('用户登出', '客户端：{}，已手动退出面板'.format(
                public.GetClientIp() + ":" + str(request.environ.get('REMOTE_PORT'))))
            if 'tmp_login_expire' in session:
                s_file = 'data/session/{}'.format(session['tmp_login_id'])
                if os.path.exists(s_file):
                    os.remove(s_file)
            del(session['request_token_head'])
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
            return redirect(login_path)

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
        return render_template('login.html',data=data)


@app.route('/close', methods=method_get)
def close():
    # 面板已关闭页面
    if not os.path.exists('data/close.pl'): return redirect('/')
    data = {}
    data['lan'] = public.getLan('close')
    return render_template('close.html', data=data)


@app.route('/tips', methods=method_get)
def tips():
    # 提示页面
    get=get_input()
    if len(get.__dict__.keys()) > 1:return abort(404)
    return render_template('tips.html')


@app.route('/get_app_bind_status', methods=method_all)
def get_app_bind_status(pdata=None):
    # APP绑定状态查询
    if not public.check_app('app_bind'):return abort(404)
    get = get_input()
    if len(get.__dict__.keys()) > 2: return '存在无意义参数!'
    v_list = ['bind_token','data']
    for n in get.__dict__.keys():
        if not n in v_list:
            return public.returnJson(False, '不能存在多余参数'), json_header
    import panelApi
    api_object = panelApi.panelApi()
    return json.dumps(api_object.get_app_bind_status(get_input())), json_header


@app.route('/check_bind', methods=method_all)
def check_bind(pdata=None):
    # APP绑定查询
    if not public.check_app('app_bind'):return abort(404)
    get = get_input()
    if len(get.__dict__.keys()) > 4: return '存在无意义参数!'
    v_list = ['bind_token','client_brand','client_model','data']
    for n in get.__dict__.keys():
        if not n in v_list:
            return public.returnJson(False, '不能存在多余参数'), json_header
    import panelApi
    api_object = panelApi.panelApi()
    return json.dumps(api_object.check_bind(get_input())), json_header


@app.route('/code',methods=method_get)
def code():
    if not 'code' in session: return ''
    if not session['code']: return ''
    get=get_input()
    if len(get.__dict__.keys()) > 2: return '存在无意义参数!'
    # 获取图片验证码
    try:
        import vilidate, time
    except:
        public.ExecShell("pip install Pillow -I")
        return "Pillow not install!"
    code_time = cache.get('codeOut')
    if code_time: return u'Error: Don\'t request validation codes frequently'
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


@app.route('/down/<token>', methods=method_all)
def down(token=None, fname=None):
    # 文件分享对外接口
    try:
        fname = request.args.get('fname')
        if fname:
            if (len(fname) > 256): return abort(404)
        if fname: fname = fname.strip('/')
        if not token: return abort(404)
        if len(token) != 12: return abort(404)
        if not request.args.get('play') in ['true', None, '']:
            return abort(404)
        args = get_input()
        v_list = ['fname', 'play', 'file_password','data']
        for n in args.__dict__.keys():
            if not n in v_list:
                return public.returnJson(False, '不能存在多余参数'), json_header
        if not re.match(r"^\w+$", token): return abort(404)
        find = public.M('download_token').where('token=?', (token,)).find()

        if not find: return abort(404)
        if time.time() > int(find['expire']): return abort(404)

        if not os.path.exists(find['filename']): return abort(404)
        if find['password'] and not token in session:
            if 'file_password' in args:
                if not re.match(r"^\w+$", args.file_password):
                    return public.ReturnJson(False, '密码错误-1!'), json_header
                if re.match(r"^\d+$", args.file_password):
                    args.file_password = str(int(args.file_password))
                    args.file_password += ".0"
                    

                if args.file_password != str(find['password']):
                    return public.ReturnJson(False, '密码错误-2!'), json_header
                session[token] = 1
                session['down'] = True
            else:
                pdata = {
                    "to_path": "",
                    "src_path": find['filename'],
                    "password": True,
                    "filename": find['filename'].split('/')[-1],
                    "ps": find['ps'],
                    "total": find['total'],
                    "token": find['token'],
                    "expire": public.format_date(times=find['expire'])
                }
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
            mimetype = "application/octet-stream"
            extName = filename.split('.')[-1]
            if extName in ['png', 'gif', 'jpeg', 'jpg']: mimetype = None
            b_name = os.path.basename(filename)
            return send_file(filename, mimetype=mimetype,
                             as_attachment=True,
                             attachment_filename=b_name,
                             cache_timeout=0)
    except:
        return abort(404)


@app.route('/public', methods=method_all)
def panel_public():
    get = get_input()
    if len("{}".format(get.__dict__)) > 1024 * 32:
        return 'ERROR'

    #获取ping测试
    if 'get_ping' in get:
        try:
            import panelPing
            p = panelPing.Test()
            get = p.check(get)
            if not get: return 'ERROR'
            result = getattr(p,get['act'])(get)
            result_type = type(result)
            if str(result_type).find('Response') != -1: return result
            return public.getJson(result),json_header
        except:
            return abort(404)
    global admin_check_auth, admin_path, route_path, admin_path_file
    if admin_path != '/bt' and os.path.exists(admin_path_file) and not 'admin_auth' in session:
        return abort(404)
    v_list = ['fun', 'name','filename', 'data','secret_key']
    for n in get.__dict__.keys():
        if not n in v_list:
            return abort(404)

    get.client_ip = public.GetClientIp()
    num_key = get.client_ip + '_wxapp'
    if not public.get_error_num(num_key, 10):
        return public.returnMsg(False, '连续10次认证失败，禁止1小时')
    if not hasattr(get, 'name'): get.name = ''
    if not hasattr(get, 'fun'): return abort(404)
    if not public.path_safe_check("%s/%s" % (get.name, get.fun)): return abort(404)
    if get.fun in ['login_qrcode', 'is_scan_ok','set_login']:
        # 检查是否验证过安全入口
        if admin_path != '/bt' and os.path.exists(admin_path_file) and not 'admin_auth' in session:
            return abort(404)
        #验证是否绑定了设备
        if not public.check_app('app'):return public.returnMsg(False,'未绑定用户!')
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


@app.route('/favicon.ico', methods=method_get)
def send_favicon():
    # 图标
    comReturn = comm.local()
    if comReturn: return abort(404)
    s_file = '/www/server/panel/BTPanel/static/favicon.ico'
    if not os.path.exists(s_file): return abort(404)
    return send_file(s_file, conditional=True, add_etags=True)



@app.route('/btwaf_error', methods=method_get)
def btwaf_error():
    # 图标
    comReturn = comm.local()
    if comReturn: return comReturn
    get=get_input()
    p_path = os.path.join('/www/server/panel/plugin/', "btwaf")
    if not os.path.exists(p_path): 
        if get.name == 'btwaf' and get.fun == 'index':
            return  render_template('error3.html',data={})
    return  render_template('error3.html',data={})

@app.route('/coll', methods=method_all)
@app.route('/coll/', methods=method_all)
@app.route('/<name>/<fun>', methods=method_all)
@app.route('/<name>/<fun>/<path:stype>', methods=method_all)
def panel_other(name=None, fun=None, stype=None):
    if not public.is_bind():
        return redirect('/bind',302)
    # 插件接口
    if public.is_error_path():
        return redirect('/error',302)
    if not name: return abort(404)
    if name != "mail_sys" or fun != "send_mail_http.json":
        comReturn = comm.local()
        if comReturn: return comReturn
        if fun:
            if fun.find('.json') != -1:
                if 'request_token' in session and 'login' in session:
                    if not check_csrf(): return public.ReturnJson(False, 'INIT_CSRF_ERR'), json_header
        args = None
    else:
        p_path = public.get_plugin_path() + '/' + name
        if not os.path.exists(p_path): return abort(404)
        args = get_input()
        args_list = ['mail_from', 'password', 'mail_to', 'subject', 'content', 'subtype', 'data']
        for k in args.__dict__:
            if not k in args_list: return abort(404)

    if not fun: fun = 'index.html'
    if not stype:
        tmp = fun.split('.')
        fun = tmp[0]
        if len(tmp) == 1:  tmp.append('')
        stype = tmp[1]

    if not name: name = 'coll'
    if not public.path_safe_check("%s/%s/%s" % (name, fun, stype)): return abort(404)
    if name.find('./') != -1 or not re.match(r"^[\w-]+$", name): return abort(404)
    if not name: return public.returnJson(False, 'PLUGIN_INPUT_ERR'), json_header
    p_path = public.get_plugin_path() + '/' + name
    if not os.path.exists(p_path): 
        if name == 'btwaf' and fun == 'index':
            pdata = {}
            from pluginAuth import Plugin
            plugin_list = Plugin(False).get_plugin_list()
            for p in plugin_list['list']:
                if p['name'] in ['btwaf']:
                    if p['endtime'] != 0 and p['endtime'] < time.time():
                        pdata['error_msg'] = 1
                        break
            return  render_template('error3.html',data=pdata)
        return abort(404)

    # 是否响插件应静态文件
    if fun == 'static':
        if stype.find('./') != -1 or not os.path.exists(p_path + '/static'): return abort(404)
        s_file = p_path + '/static/' + stype
        if s_file.find('..') != -1: return abort(404)
        if not re.match(r"^[\w\./-]+$", s_file): return abort(404)
        if not public.path_safe_check(s_file): return abort(404)
        if not os.path.exists(s_file): return abort(404)
        return send_file(s_file, conditional=True, add_etags=True)

    # 准备参数
    if not args: args = get_input()
    args.client_ip = public.GetClientIp()
    args.fun = fun

    # 初始化插件对象
    try:
        from pluginAuth import Plugin
        try:
            args.s = fun
            args.name = name
            p = Plugin(name)
            if not p.isdef(fun): return public.returnMsg(False,'PLUGIN_INPUT_C',(fun,))
            data =  p.exec_fun(args)
        except Exception as ex:
            if name == 'btwaf' and fun == 'index' and str(ex).find('未购买') != -1:
                return  render_template('error3.html',data={}) 
            return public.get_error_object(None,plugin_name=name)

        r_type = type(data)
        if r_type in [Response,Resp]:
            return data

        # 处理响应
        if stype == 'json':  # 响应JSON
            return public.getJson(data), json_header
        elif stype == 'html':  # 使用模板
            t_path_root = p_path + '/templates/'
            t_path = t_path_root + fun + '.html'
            if not os.path.exists(t_path):
                return public.returnJson(False, 'PLUGIN_NOT_TEMPLATE'), json_header
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
                    return  render_template('error3.html',data={"error_msg":data['msg']})
                return public.returnJson(False, public.getMsg('PUBLIC_ERR_RETURN').format(r_type)), json_header
            return data
    except:
        return public.get_error_object(None, plugin_name=name)


@app.route('/hook', methods=method_all)
def panel_hook():
    # webhook接口
    get = get_input()
    if not os.path.exists('plugin/webhook'):
        return abort(404)
    public.package_path_append('plugin/webhook')
    import webhook_main
    return public.getJson(webhook_main.webhook_main().RunHook(get))


@app.route('/install', methods=method_all)
def install():
    # 初始化面板接口
    if not session.get('login',None): return public.error_not_login()
    if not os.path.exists('install.pl'): return redirect('/login')
    if public.M('config').where("id=?", ('1',)).getField('status') == 1:
        if os.path.exists('install.pl'): os.remove('install.pl')
        session.clear()
        return redirect('/login')
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
        if not hasattr(get, 'bt_username'): return public.getMsg('INSTALL_USER_EMPTY')
        if not get.bt_username: return public.getMsg('INSTALL_USER_EMPTY')
        if not hasattr(get, 'bt_password1'): return public.getMsg('INSTALL_PASS_EMPTY')
        if not get.bt_password1: return public.getMsg('INSTALL_PASS_EMPTY')
        if get.bt_password1 != get.bt_password2: return public.getMsg('INSTALL_PASS_CHECK')
        public.M('users').where("id=?", (1,)).save('username,password',
                                                   (get.bt_username,
                                                    public.password_salt(public.md5(get.bt_password1.strip()), uid=1)
                                                    )
                                                   )
        os.remove('install.pl')
        public.M('config').where("id=?", ('1',)).setField('status', 1)
        data = {}
        data['status'] = os.path.exists('install.pl')
        data['username'] = get.bt_username
        return render_template('install.html', data=data)


# @app.route('/robots.txt', methods=method_all)
# def panel_robots():
#     # 爬虫规则响应接口
#     get=get_input()
#     if len(get.__dict__.keys()) > 1:return abort(404)
#     robots = '''User-agent: *
# Disallow: /
# '''
#     return robots, {'Content-Type': 'text/plain'}

@app.route('/rspamd', defaults={'path': ''},methods=method_all)
@app.route('/rspamd/<path:path>',methods=method_all)
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
        if re.search("\.(js|css)$",path):
            return send_file('/usr/share/rspamd/www/rspamd/'+path,conditional=True,add_etags=True)
        if path == "/":
            return send_file('/usr/share/rspamd/www/rspamd/',conditional=True,add_etags=True)
        url = "http://127.0.0.1:11334/rspamd/" + path + "?" +param
        for i in ['stat','auth','neighbours','list_extractors','list_transforms','graph','maps','actions','symbols','history','errors','check_selector','saveactions','savesymbols','getmap']:
            if i in path:
                url = "http://127.0.0.1:11334/" + path + "?" +param
        req = requests.get(url, headers=headers,stream = True)
        return Resp(stream_with_context(req.iter_content()), content_type = req.headers['content-type'])
    else:
        url = "http://127.0.0.1:11334/" + path
        for i in request.form.keys():
            data = '{}='.format(i)
        # public.writeFile('/tmp/2',data+"\n","a+")
        req = requests.post(url,data=data,headers=headers,stream = True)

        return Resp(stream_with_context(req.iter_content()), content_type = req.headers['content-type'])

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
        pdata['filename'] = (find['filename'].split('/')[-1] + '/' + to_path).strip('/')
        return render_template('down.html', data=pdata, to_size=public.to_size)


def get_phpmyadmin_dir():
    # 获取phpmyadmin目录
    path = public.GetConfigValue('setup_path') + '/phpmyadmin'
    if not os.path.exists(path): return None
    phpport = '888'
    try:
        import re
        if session['webserver'] == 'nginx':
            filename = public.GetConfigValue('setup_path') + '/nginx/conf/nginx.conf'
            conf = public.readFile(filename)
            rep = r"listen\s+([0-9]+)\s*;"
            rtmp = re.search(rep, conf)
            if rtmp:
                phpport = rtmp.groups()[0]
        if session['webserver'] == 'apache':
            filename = public.GetConfigValue('setup_path') + '/apache/conf/extra/httpd-vhosts.conf'
            conf = public.readFile(filename)
            rep = r"Listen\s+([0-9]+)\s*\n"
            rtmp = re.search(rep, conf)
            if rtmp:
                phpport = rtmp.groups()[0]
        if session['webserver'] == 'openlitespeed':
            filename = public.GetConfigValue('setup_path') + '/panel/vhost/openlitespeed/listen/888.conf'
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
        if not get.action in defs:  return public.ReturnJson(False, 'ARGS_ERR'), json_header
        result = getattr(toObject,get.action)(get)
        if not hasattr(get, 'html') and  not hasattr(get, 's_module'):
            r_type = type(result)
            if r_type in [Response,Resp]: return result
            result = public.GetJson(result), json_header

        if g.is_aes:
            result = public.aes_encrypt(result[0], g.aes_key), json_header
        return result


def check_csrf():
    # CSRF校验
    if app.config['DEBUG']: return True
    request_token = request.cookies.get('request_token')
    if session['request_token'] != request_token: return False
    http_token = request.headers.get('x-http-token')
    if not http_token: return False
    if http_token != session['request_token_head']: return False
    cookie_token = request.headers.get('x-cookie-token')
    if cookie_token != session['request_token']: return False
    return True


def publicObject(toObject, defs, action=None, get=None):
    try:
        # 模块访问前置检查
        if 'request_token' in session and 'login' in session:
            if not check_csrf(): return public.ReturnJson(False, 'INIT_CSRF_ERR'), json_header

        if not get: get = get_input()
        if action: get.action = action

        if hasattr(get, 'path'):
            get.path = get.path.replace('//', '/').replace('\\', '/')
            if get.path.find('./') != -1: return public.ReturnJson(False, 'INIT_PATH_NOT_SAFE'), json_header
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
            if not toObject.site_path_check(get): return public.ReturnJson(False, 'INIT_ACCEPT_NOT'), json_header
        return run_exec().run(toObject, defs, get)
    except:
        return error_500(None)


def check_login(http_token=None):
    # 检查是否登录面板
    if cache.get('dologin'): return False
    if 'login' in session:
        loginStatus = session['login']
        if loginStatus and http_token:
            if session['request_token_head'] != http_token: return False
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
    if not ltd: ltd = -1
    if tmp == None: tmp = -1
    if ltd < 1:
        if ltd == -2:
            tmp3 = public.to_string([60, 115, 112, 97, 110, 32, 99, 108, 97, 115, 115, 61, 34, 98, 116, 108, 116, 100,
                                     45, 103, 114, 97, 121, 34, 62, 60, 115, 112, 97, 110, 32, 115, 116, 121, 108, 101,
                                     61, 34, 99, 111, 108, 111, 114, 58, 32, 35, 102, 99, 54, 100, 50, 54, 59, 102, 111,
                                     110, 116, 45, 119, 101, 105, 103, 104, 116, 58, 32, 98, 111, 108, 100, 59, 109, 97,
                                     114, 103, 105, 110, 45, 114, 105, 103, 104, 116, 58, 53, 112, 120, 34, 62, 24050,
                                     36807,
                                     26399, 60, 47, 115, 112, 97, 110, 62, 60, 97, 32, 99, 108, 97, 115, 115, 61, 34,
                                     98, 116,
                                     108, 105, 110, 107, 34, 32, 111, 110, 99, 108, 105, 99, 107, 61, 34, 98, 116, 46,
                                     115, 111,
                                     102, 116, 46, 117, 112, 100, 97, 116, 97, 95, 108, 116, 100, 40, 41, 34, 62, 32493,
                                     36153, 60, 47, 97, 62, 60, 47, 115, 112, 97, 110, 62])
        elif tmp == -1:
            tmp3 = public.to_string([60, 115, 112, 97, 110, 32, 99, 108, 97, 115, 115, 61, 34, 98,
                                     116, 112, 114, 111, 45, 102, 114, 101, 101, 34, 32, 111, 110, 99, 108, 105, 99,
                                     107,
                                     61, 34, 98, 116, 46, 115, 111, 102, 116, 46, 117, 112, 100, 97, 116, 97, 95, 99,
                                     111, 109, 109, 101, 114, 99, 105, 97, 108, 95, 118, 105, 101, 119, 40, 41, 34,
                                     32, 116, 105, 116, 108, 101, 61, 34, 28857, 20987, 21319, 32423, 21040,
                                     21830, 19994, 29256, 34, 62, 20813, 36153, 29256, 60, 47, 115, 112, 97, 110, 62])
        elif tmp == -2:
            tmp3 = public.to_string([60, 115, 112, 97, 110, 32, 99, 108, 97, 115, 115, 61, 34, 98, 116,
                                     112, 114, 111, 45, 103, 114, 97, 121, 34, 62, 60, 115, 112, 97, 110, 32,
                                     115, 116, 121, 108, 101, 61, 34, 99, 111, 108, 111, 114, 58, 32, 35,
                                     102, 99, 54, 100, 50, 54, 59, 102, 111, 110, 116, 45, 119, 101, 105, 103,
                                     104, 116, 58, 32, 98, 111, 108, 100, 59, 109, 97, 114, 103, 105, 110, 45,
                                     114, 105, 103, 104, 116, 58, 53, 112, 120, 34, 62, 24050, 36807, 26399,
                                     60, 47, 115, 112, 97, 110, 62, 60, 97, 32, 99, 108, 97, 115, 115, 61, 34,
                                     98, 116, 108, 105, 110, 107, 34, 32, 111, 110, 99, 108, 105, 99, 107, 61,
                                     34, 98, 116, 46, 115, 111, 102, 116, 46, 117, 112, 100, 97, 116, 97, 95,
                                     112, 114, 111, 40, 41, 34, 62, 32493, 36153, 60, 47, 97, 62, 60,
                                     47, 115, 112, 97, 110, 62])
        if tmp >= 0 and ltd in [-1, -2]:
            if tmp == 0:
                tmp2 = public.to_string([27704, 20037, 25480, 26435])
                tmp3 = public.to_string([60, 115, 112, 97, 110, 32, 99, 108, 97, 115, 115, 61, 34, 98, 116,
                                         112, 114, 111, 34, 62, 123, 48, 125, 60, 115, 112, 97, 110, 32, 115, 116,
                                         121, 108, 101, 61, 34, 99, 111, 108, 111, 114, 58, 32, 35, 102, 99, 54, 100,
                                         50, 54, 59, 102, 111, 110, 116, 45, 119, 101, 105, 103, 104, 116,
                                         58, 32, 98, 111, 108, 100, 59, 34, 62, 123, 49, 125, 60, 47, 115,
                                         112, 97, 110, 62, 60, 47, 115, 112, 97, 110, 62]).format(
                    public.to_string([21040, 26399, 26102, 38388, 65306]), tmp2)
            else:
                tmp2 = time.strftime(public.to_string([37, 89, 45, 37, 109, 45, 37, 100]), time.localtime(tmp))
                tmp3 = public.to_string([60, 115, 112, 97, 110, 32, 99, 108, 97, 115, 115, 61, 34, 98, 116,
                                         112, 114, 111, 34, 62, 21040, 26399, 26102, 38388, 65306, 60, 115, 112,
                                         97, 110, 32, 115, 116, 121, 108, 101, 61, 34, 99, 111, 108, 111, 114,
                                         58, 32, 35, 102, 99, 54, 100, 50, 54, 59, 102, 111, 110, 116, 45, 119,
                                         101, 105, 103, 104, 116, 58, 32, 98, 111, 108, 100, 59, 109, 97, 114,
                                         103, 105, 110, 45, 114, 105, 103, 104, 116, 58, 53, 112, 120, 34, 62, 123,
                                         48, 125, 60, 47, 115, 112, 97, 110, 62, 60, 97, 32, 99, 108, 97, 115,
                                         115, 61, 34, 98, 116, 108, 105, 110, 107, 34, 32, 111, 110, 99, 108, 105, 99,
                                         107, 61, 34, 98, 116, 46, 115, 111, 102, 116, 46, 117, 112, 100, 97,
                                         116, 97, 95, 112, 114, 111, 40, 41, 34, 62, 32493, 36153, 60, 47, 97, 62, 60,
                                         47, 115, 112, 97, 110, 62]).format(tmp2)
        else:
            tmp3 = public.to_string([60, 115, 112, 97, 110, 32, 99, 108, 97, 115, 115, 61, 34, 98, 116, 112,
                                     114, 111, 45, 103, 114, 97, 121, 34, 32, 111, 110, 99, 108, 105, 99, 107,
                                     61, 34, 98, 116, 46, 115, 111, 102, 116, 46, 117, 112, 100, 97, 116, 97,
                                     95, 112, 114, 111, 40, 41, 34, 32, 116, 105, 116, 108, 101, 61, 34, 28857,
                                     20987, 21319, 32423, 21040, 19987, 19994, 29256, 34, 62, 20813, 36153,
                                     29256, 60, 47, 115, 112, 97, 110, 62])
    else:
        tmp3 = public.to_string([60, 115, 112, 97, 110, 32, 99, 108, 97, 115, 115, 61, 34, 98, 116, 108, 116,
                                 100, 34, 62, 21040, 26399, 26102, 38388, 65306, 60, 115, 112, 97, 110, 32, 115, 116,
                                 121, 108, 101, 61, 34, 99, 111, 108, 111, 114, 58, 32, 35, 102, 99, 54, 100, 50,
                                 54, 59, 102, 111, 110, 116, 45, 119, 101, 105, 103, 104, 116, 58, 32, 98, 111,
                                 108, 100, 59, 109, 97, 114, 103, 105, 110, 45, 114, 105, 103, 104, 116, 58, 53,
                                 112, 120, 34, 62, 123, 125, 60, 47, 115, 112, 97, 110, 62, 60, 97, 32, 99, 108,
                                 97, 115, 115, 61, 34, 98, 116, 108, 105, 110, 107, 34, 32, 111, 110, 99, 108, 105,
                                 99, 107, 61, 34, 98, 116, 46, 115, 111, 102, 116, 46, 117, 112, 100, 97, 116, 97,
                                 95, 108, 116, 100, 40, 41, 34, 62, 32493, 36153, 60, 47, 97, 62, 60, 47, 115,
                                 112, 97, 110, 62]).format(
            time.strftime(public.to_string([37, 89, 45, 37, 109, 45, 37, 100]), time.localtime(ltd)))

    return tmp3, tmp, ltd


def send_authenticated():
    # 发送http认证信息
    request_host = public.GetHost()
    result = Response('', 401, {'WWW-Authenticate': 'Basic realm="%s"' % request_host.strip()})
    # if not 'login' in session and not 'admin_auth' in session: session.clear()
    return result


# 取端口
def FtpPort():
    # 获取FTP端口
    if session.get('port'): return
    import re
    try:
        file = public.GetConfigValue('setup_path') + '/pure-ftpd/etc/pure-ftpd.conf'
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
            result = make_response(result)
            request_token = public.GetRandomString(48)
            session['request_token'] = request_token
            samesite = app.config['SESSION_COOKIE_SAMESITE']
            secure = app.config['SESSION_COOKIE_SECURE']
            if app.config['SSL'] and request.full_path.find('/login?tmp_token=') == 0:
                samesite = 'None'
                secure = True
            result.set_cookie('request_token', request_token, 
            max_age=86400 * 30,
            samesite= samesite,
            secure=secure
            )
    return result


def is_bind():
    pass
    #if os.path.exists(bind_pl):
    #    os.remove(bind_pl)
        
# js随机数模板使用，用于不更新版本号时更新前端文件不需要用户强制刷新浏览器
def get_js_random():
    js_random = public.readFile('data/js_random.pl')
    if not js_random or js_random == '1':
        js_random = public.GetRandomString(16)
    public.writeFile('data/js_random.pl',js_random)
    return js_random

# 获取输入数据
def get_input():
    data = public.dict_obj()
    exludes = ['blob']
    for key in request.args.keys():
        data[key] = str(request.args.get(key, ''))
    try:
        for key in request.form.keys():
            if key in exludes: continue
            data[key] = str(request.form.get(key, ''))
    except:
        try:
            post = request.form.to_dict()
            for key in post.keys():
                if key in exludes: continue
                data[key] = str(post[key])
        except:
            pass

    if 'form_data' in g:
        for k in g.form_data.keys():
            data[k] = str(g.form_data[k])

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

@app.route('/workorder/<action>',methods=method_all)
def workorder(action, pdata=None):

    comReturn = comm.local()
    if comReturn: return comReturn

    import panelWorkorder
    toObject = panelWorkorder.panelWorkorder()

    defs = ("get_user_info","close", "create", "list", "get_messages", "allow")
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
    if not check_csrf_websocket(ws,get):
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
    if not check_csrf_websocket(ws,get): return

    while True:
        pdata = ws.receive()
        if pdata == '{}': break
        data = json.loads(pdata)
        get = public.to_dict_obj(data)
        get._ws = ws
        p = threading.Thread(target=ws_panel_thread,args=(get,))
        p.start()

def ws_panel_thread(get):
    '''
        @name 面板管理ws线程
        @author hwliang<2021-07-24>
        @param get<dict> 请求参数
        @return void
    '''
    
    if not hasattr(get,'ws_callback'):
        get._ws.send(public.getJson(public.return_status_code(1001,'ws_callback')))
        return
    if not hasattr(get,'mod_name'):
        get._ws.send(public.getJson(public.return_status_code(1001,'mod_name')))
        return
    if not hasattr(get,'def_name'):
        get._ws.send(public.getJson(public.return_status_code(1001,'def_name')))
        return
    get.mod_name = get.mod_name.strip()
    get.def_name = get.def_name.strip()
    check_str = '{}{}'.format(get.mod_name,get.def_name)
    if not re.match("^\w+$",check_str) or get.mod_name in ['public','common','db','db_mysql','downloadFile','jobs']:
        get._ws.send(public.getJson(public.return_status_code(1000,'不安全的mod_name,def_name参数内容')))
        return
    if not hasattr(get,'args'):
        get._ws.send(public.getJson(public.return_status_code(1001,'args')))
        return
    
    mod_file = '{}/{}.py'.format(public.get_class_path(),get.mod_name)
    if not os.path.exists(mod_file):
        get._ws.send(public.getJson(public.return_status_code(1000,'指定模块{}不存在'.format(get.mod_name))))
        return
    _obj = public.get_script_object(mod_file)
    if not _obj: 
        get._ws.send(public.getJson(public.return_status_code(1000,'指定模块{}不存在'.format(get.mod_name))))
        return
    _cls = getattr(_obj, get.mod_name)
    if not _cls:
        get._ws.send(public.getJson(public.return_status_code(1000,'在{}模块中没有找到{}对像'.format(get.mod_name,get.mod_name))))
        return
    _def = getattr(_cls(), get.def_name)
    if not _def:
        get._ws.send(public.getJson(public.return_status_code(1000,'在{}对像中没有找到{}方法'.format(get.mod_name,get.def_name))))
        return
    result = {
        'callback': get.ws_callback,
        'result':_def(public.to_dict_obj(get.args))
    }
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
    if not check_csrf_websocket(ws,get): return

    from panelProjectController import ProjectController
    project_obj = ProjectController()
    while True:
        pdata = ws.receive()
        if pdata in '{}': break
        get = public.to_dict_obj(json.loads(pdata))
        get._ws = ws
        p = threading.Thread(target=ws_project_thread,args=(project_obj,get))
        p.start()
        

def ws_project_thread(_obj,get):
    '''
        @name 项目管理ws线程
        @author hwliang<2021-07-24>
        @param _obj<ProjectController> 项目管理控制器对像
        @param get<dict> 请求参数
        @return void
    '''
    if not hasattr(get,'ws_callback'):
        get._ws.send(public.getJson(public.return_status_code(1001,'ws_callback')))
        return
    result = {
        'callback': get.ws_callback,
        'result':_obj.model(get)
    }
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
    if not check_csrf_websocket(ws,get): return

    t = None
    try:
        while True:
            cmdstring = ws.receive()
            if cmdstring in ['stop','error'] or not cmdstring:
                break
            t = threading.Thread(target = sock_recv,args=(cmdstring,ws))
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
        if hasattr(sock_pids[pid],'closed'):
            is_closed = sock_pids[pid].closed
        else:
            is_closed = not sock_pids[pid].connected
        
        logging.debug("PID: {} , sock_stat: {}".format(pid,is_closed))
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


def sock_recv(cmdstring,ws):
    global sock_pids
    try:
        p = subprocess.Popen(cmdstring + " 2>&1",close_fds=True,shell=True,bufsize=4096,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        sock_pids[p.pid] = ws
        kill_closed()
        while p.poll() == None:
            send_line = p.stdout.readline().decode()
            if not send_line or send_line.find('tail: ') != -1: continue
            ws.send(send_line)
        ws.send(p.stdout.read().decode())
    except:
        kill_closed()

@app.route('/close_sock_shell',methods=method_all)
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


    cmdstring = args.cmdstring.strip()
    skey = public.md5(cmdstring)
    pid = cache.get(skey)
    if not pid: 
        return json.dumps(public.return_data(False,[],error_msg='指定sock已终止!')),json_header
    os.kill(pid,9)
    cache.delete(skey)
    return json.dumps(public.return_data(True,'操作成功!')),json_header

def check_csrf_websocket(ws,args):
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
        if session['request_token_head'] != args['x-http-token']: 
            is_success = False

    if is_success and 'request_token' in session:
        cookie_token = request.cookies.get('request_token')
        if cookie_token != session['request_token']: 
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
    if not check_csrf_websocket(ws,get):
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

        if get['host'] in ['127.0.0.1', 'localhost'] and 'port' not in ssh_info:
            ssh_info = sp.get_ssh_info('127.0.0.1')
            if not ssh_info: ssh_info = sp.get_ssh_info('localhost')
            if not ssh_info: ssh_info = {"host": "127.0.0.1"}
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

    defs = ("get_app_usage", "get_daily_data", "get_daily_list")
    result = publicObject(toObject, defs)
    return result

@app.route('/phpmyadmin/<path:path_full>',methods=method_all)
def pma_proxy(path_full = None):
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
        cache.set(cache_key,pmd,10)
    panel_pool = 'http://'
    if request.url_root[:5] == 'https':
        panel_pool = 'https://'
        import ajax
        ssl_info = ajax.ajax().get_phpmyadmin_ssl(None)
        if ssl_info['status']:
            pmd[1] = ssl_info['port']
        else:
            panel_pool = 'http://'

    proxy_url = '{}127.0.0.1:{}/{}/'.format(panel_pool,pmd[1],pmd[0]) + request.full_path.replace('/phpmyadmin/','')
    from panelHttpProxy import HttpProxy
    px = HttpProxy()
    return px.proxy(proxy_url)

@app.route('/p/<int:port>',methods=method_all)
@app.route('/p/<int:port>/',methods=method_all)
@app.route('/p/<int:port>/<path:full_path>',methods=method_all)
def proxy_port(port,full_path=None):
    '''
        @name 代理指定端口
        @author hwliang<2022-01-19>
        @return Response
    '''
    
    comReturn = comm.local()
    if comReturn: return comReturn
    full_path = request.full_path.replace('/p/{}/'.format(port),'').replace('/p/{}'.format(port),'')
    uri = '{}/{}'.format(port,full_path)
    uri = uri.replace('//','/')
    proxy_url = 'http://127.0.0.1:{}'.format(uri)
    from panelHttpProxy import HttpProxy
    px = HttpProxy()
    return px.proxy(proxy_url)

    

