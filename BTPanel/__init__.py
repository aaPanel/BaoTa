#coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板 
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: 黄文良 <287962566@qq.com>
# +-------------------------------------------------------------------
import sys,json,os,time,logging,re
if sys.version_info[0] != 2:
        from imp import reload
sys.path.insert(0,'class/')
import public
from flask import Flask
app = Flask(__name__,template_folder="templates/" + public.GetConfigValue('template'))
from flask import Flask,current_app,session,render_template,send_file,request,redirect,g,url_for,make_response,render_template_string,abort

from flask_session import Session
from werkzeug.contrib.cache import SimpleCache
from werkzeug.wrappers import Response
from flask_socketio import SocketIO,emit,send
dns_client = None
app.config['DEBUG'] = os.path.exists('data/debug.pl')

#设置BasicAuth
basic_auth_conf = 'config/basic_auth.json' 
app.config['BASIC_AUTH_OPEN'] = False
if os.path.exists(basic_auth_conf):
    try:
        ba_conf = json.loads(public.readFile(basic_auth_conf))
        app.config['BASIC_AUTH_USERNAME'] = ba_conf['basic_user']
        app.config['BASIC_AUTH_PASSWORD'] = ba_conf['basic_pwd']
        app.config['BASIC_AUTH_OPEN'] = ba_conf['open']
    except: pass

cache = SimpleCache()
socketio = SocketIO()
socketio.init_app(app)

import common,db,jobs,uuid
jobs.control_init()
app.secret_key = uuid.UUID(int=uuid.getnode()).hex[-12:]
local_ip = None


try:
    from flask_sqlalchemy import SQLAlchemy
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////dev/shm/session.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
    sdb = SQLAlchemy(app)
    app.config['SESSION_TYPE'] = 'sqlalchemy'
    app.config['SESSION_SQLALCHEMY'] = sdb
    app.config['SESSION_SQLALCHEMY_TABLE'] = 'session'
    s_sqlite = True
except:
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['SESSION_FILE_DIR'] = r'/dev/shm/session_py' + str(sys.version_info[0])
    app.config['SESSION_FILE_THRESHOLD'] = 2048
    app.config['SESSION_FILE_MODE'] = 384
    s_sqlite = False
    public.ExecShell("pip install flask_sqlalchemy &")

app.config['SESSION_PERMANENT'] = True
app.config['SESSION_USE_SIGNER'] = True
app.config['SESSION_KEY_PREFIX'] = 'BT_:'
app.config['SESSION_COOKIE_NAME'] = "BT_PANEL_6"
app.config['PERMANENT_SESSION_LIFETIME'] = 86400
Session(app)

if s_sqlite: sdb.create_all()

from datetime import datetime
import socket

comm = common.panelAdmin()
method_all = ['GET','POST']
method_get = ['GET']
method_post = ['POST']
json_header = {'Content-Type':'application/json; charset=utf-8'}
cache.set('p_token','bmac_' + public.Md5(public.get_mac_address()))
admin_path_file = 'data/admin_path.pl'
admin_path = '/'
if os.path.exists(admin_path_file): admin_path = public.readFile(admin_path_file).strip()
admin_path_checks = ['/','/san','/bak','/monitor','/abnormal','/close','/task','/login','/config','/site','/sites','ftp','/public','/database','/data','/download_file','/control','/crontab','/firewall','/files','config','/soft','/ajax','/system','/panel_data','/code','/ssl','/plugin','/wxapp','/hook','/safe','/yield','/downloadApi','/pluginApi','/auth','/download','/cloud','/webssh','/connect_event','/panel']
if admin_path in admin_path_checks: admin_path = '/bt'

@app.route('/service_status',methods = method_get)
def service_status():
    return 'True'


@app.before_request
def request_check():
    
    if not request.path in ['/safe','/hook','/public']:
        ip_check = public.check_ip_panel()
        if ip_check: return ip_check
    domain_check = public.check_domain_panel()
    if domain_check: return domain_check
    if public.is_local():
        not_networks = ['uninstall_plugin','install_plugin','UpdatePanel']
        if request.args.get('action') in not_networks: 
            return public.returnJson(False,'离线模式下无法使用此功能!'),json_header

    if app.config['BASIC_AUTH_OPEN']:
        if request.path in ['/public','/download']: return;
        auth = request.authorization
        if not comm.get_sk(): return;
        if not auth: return send_authenticated()
        tips = '_bt.cn'
        if public.md5(auth.username.strip() + tips) != app.config['BASIC_AUTH_USERNAME'] or public.md5(auth.password.strip() + tips) != app.config['BASIC_AUTH_PASSWORD']:
            return send_authenticated()
    

@app.teardown_request
def request_end(reques = None):
    not_acts = ['GetTaskSpeed','GetNetWork','check_pay_status','get_re_order_status','get_order_stat']
    key = request.args.get('action')
    if not key in not_acts and request.full_path.find('/static/') == -1: public.write_request_log()

def send_authenticated():
    global local_ip
    if not local_ip: local_ip = public.GetLocalIp()
    return Response('', 401,{'WWW-Authenticate': 'Basic realm="%s"' % local_ip.strip()})

@app.route('/',methods=method_all)
def home():
    comReturn = comm.local()
    if comReturn: return comReturn
    args = get_input()
    licenes = 'data/licenes.pl'
    if 'license' in args:
        public.writeFile(licenes,'True')

    data = {}
    data[public.to_string([112, 100])] = get_pd()
    data['siteCount'] = public.M('sites').count()
    data['ftpCount'] = public.M('ftps').count()
    data['databaseCount'] = public.M('databases').count()
    data['lan'] = public.GetLan('index')
    data['724'] = public.format_date("%m%d") == '0724'
    public.auto_backup_panel()
    if not os.path.exists(licenes): return render_template( 'license.html')
    return render_template( 'index.html',data = data)

@app.route('/close',methods=method_get)
def close():
    if not os.path.exists('data/close.pl'): return redirect('/')
    data = {}
    data['lan'] = public.getLan('close');
    return render_template('close.html',data=data)

route_path = os.path.join(admin_path,'')
if route_path[-1] == '/': route_path = route_path[:-1]
if route_path[0] != '/': route_path = '/' + route_path
@app.route('/login',methods=method_all)
@app.route(route_path,methods=method_all)
@app.route(route_path + '/',methods=method_all)
def login():
    if os.path.exists('install.pl'): return redirect('/install')
    global admin_check_auth,admin_path,route_path
    is_auth_path = False
    if admin_path != '/bt' and os.path.exists(admin_path_file) and  not 'admin_auth' in session: is_auth_path = True
    get = get_input()
    import userlogin
    if hasattr(get,'tmp_token'):
        result = userlogin.userlogin().request_tmp(get)
        return is_login(result)

    if hasattr(get,'dologin'):
        login_path = '/login'
        if not 'login' in session: return redirect(login_path)
        if os.path.exists(admin_path_file): login_path = route_path
        if session['login'] != False:
            session['login'] = False;
            cache.set('dologin',True)
            session.clear()
            session_path = r'/dev/shm/session_py' + str(sys.version_info[0])
            if os.path.exists(session_path): public.ExecShell("rm -f " + session_path + '/*')
            return redirect(login_path)
    
    if is_auth_path:
        if route_path != request.path and route_path + '/' != request.path: 
            data = {}
            data['lan'] = public.getLan('close');
            return render_template('autherr.html',data=data)
    session['admin_auth'] = True
    comReturn = common.panelSetup().init()
    if comReturn: return comReturn
    
    if request.method == method_post[0]:
        result = userlogin.userlogin().request_post(get)
        return is_login(result)

    if request.method == method_get[0]:
        result = userlogin.userlogin().request_get(get)
        if result: return result
        data = {}
        data['lan'] = public.GetLan('login')
        return render_template(
            'login.html',
            data=data
            )

def is_login(result):
    if 'login' in session:
        if session['login'] == True:
            result = make_response(result)
            request_token = public.GetRandomString(48)
            session['request_token'] = request_token
            result.set_cookie('request_token',request_token,max_age=86400*30)
    return result

@app.route('/site',methods=method_all)
def site(pdata = None):
    comReturn = comm.local()
    if comReturn: return comReturn
    if request.method == method_get[0] and not pdata:
        data = {}
        data['isSetup'] = True;
        data['lan'] = public.getLan('site');
        if os.path.exists(public.GetConfigValue('setup_path')+'/nginx') == False and os.path.exists(public.GetConfigValue('setup_path')+'/apache') == False: data['isSetup'] = False;
        return render_template( 'site.html',data=data)
    import panelSite
    siteObject = panelSite.panelSite()
        
    defs = ('GetRedirectFile','SaveRedirectFile','DeleteRedirect','GetRedirectList','CreateRedirect','ModifyRedirect','set_dir_auth','delete_dir_auth','get_dir_auth','modify_dir_auth_pass',
            'GetSiteLogs','GetSiteDomains','GetSecurity','SetSecurity','ProxyCache','CloseToHttps','HttpToHttps','SetEdate',
            'SetRewriteTel','GetCheckSafe','CheckSafe','GetDefaultSite','SetDefaultSite','CloseTomcat','SetTomcat','apacheAddPort',
            'AddSite','GetPHPVersion','SetPHPVersion','DeleteSite','AddDomain','DelDomain','GetDirBinding','AddDirBinding','GetDirRewrite',
            'DelDirBinding','get_site_types','add_site_type','remove_site_type','modify_site_type_name','set_site_type','UpdateRulelist',
            'SetSiteRunPath','GetSiteRunPath','SetPath','SetIndex','GetIndex','GetDirUserINI','SetDirUserINI','GetRewriteList','SetSSL',
            'SetSSLConf','CreateLet','CloseSSLConf','GetSSL','SiteStart','SiteStop','Set301Status','Get301Status','CloseLimitNet','SetLimitNet',
            'GetLimitNet','RemoveProxy','GetProxyList','GetProxyDetals','CreateProxy','ModifyProxy','GetProxyFile','SaveProxyFile','ToBackup',
            'DelBackup','GetSitePHPVersion','logsOpen','GetLogsStatus','CloseHasPwd','SetHasPwd','GetHasPwd','GetDnsApi','SetDnsApi')
    return publicObject(siteObject,defs,None,pdata);

@app.route('/ftp',methods=method_all)
def ftp(pdata = None):
    comReturn = comm.local()
    if comReturn: return comReturn
    if request.method == method_get[0] and not pdata:
        FtpPort()
        data = {}
        data['isSetup'] = True;
        if os.path.exists(public.GetConfigValue('setup_path') + '/pure-ftpd') == False: data['isSetup'] = False;
        data['lan'] = public.GetLan('ftp')
        return render_template('ftp.html',data=data)
    import ftp
    ftpObject = ftp.ftp()
    defs = ('AddUser','DeleteUser','SetUserPassword','SetStatus','setPort')
    return publicObject(ftpObject,defs,None,pdata);

#取端口
def FtpPort():
    if session.get('port'):return
    import re
    try:
        file = public.GetConfigValue('setup_path')+'/pure-ftpd/etc/pure-ftpd.conf'
        conf = public.readFile(file)
        rep = "\n#?\s*Bind\s+[0-9]+\.[0-9]+\.[0-9]+\.+[0-9]+,([0-9]+)"
        port = re.search(rep,conf).groups()[0]
    except:
        port='21'
    session['port'] = port

@app.route('/database',methods=method_all)
def database(pdata = None):
    import ajax
    comReturn = comm.local()
    if comReturn: return comReturn
    if request.method == method_get[0] and not pdata:
        pmd = get_phpmyadmin_dir();
        session['phpmyadminDir'] = False
        if pmd: 
            session['phpmyadminDir'] = 'http://' + public.GetHost() + ':'+ pmd[1] + '/' + pmd[0];
        ajax.ajax().set_phpmyadmin_session()
        data = {}
        data['isSetup'] = os.path.exists(public.GetConfigValue('setup_path') + '/mysql/bin');
        data['mysql_root'] = public.M('config').where('id=?',(1,)).getField('mysql_root');
        data['lan'] = public.GetLan('database')
        return render_template('database.html',data=data)
    import database
    databaseObject = database.database()
    defs = ('GetdataInfo','GetInfo','ReTable','OpTable','AlTable','GetSlowLogs','GetRunStatus','SetDbConf','GetDbStatus','BinLog','GetErrorLog','GetMySQLInfo','SetDataDir','SetMySQLPort','AddDatabase','DeleteDatabase','SetupPassword','ResDatabasePassword','ToBackup','DelBackup','InputSql','SyncToDatabases','SyncGetDatabases','GetDatabaseAccess','SetDatabaseAccess')
    return publicObject(databaseObject,defs,None,pdata);

def get_phpmyadmin_dir():
        path = public.GetConfigValue('setup_path') + '/phpmyadmin'
        if not os.path.exists(path): return None
        
        phpport = '888';
        try:
            import re;
            if session['webserver'] == 'nginx':
                filename =public.GetConfigValue('setup_path') + '/nginx/conf/nginx.conf';
                conf = public.readFile(filename);
                rep = "listen\s+([0-9]+)\s*;";
                rtmp = re.search(rep,conf);
                if rtmp:
                    phpport = rtmp.groups()[0];
            else:
                filename = public.GetConfigValue('setup_path') + '/apache/conf/extra/httpd-vhosts.conf';
                conf = public.readFile(filename);
                rep = "Listen\s+([0-9]+)\s*\n";
                rtmp = re.search(rep,conf);
                if rtmp:
                    phpport = rtmp.groups()[0];
        except:
            pass
            
        for filename in os.listdir(path):
            filepath = path + '/' + filename
            if os.path.isdir(filepath):
                if filename[0:10] == 'phpmyadmin':
                    return str(filename),phpport
        return None

@app.route('/control',methods=method_all)
def control(pdata = None):
    comReturn = comm.local()
    if comReturn: return comReturn
    if request.method == method_get[0]:
        data = {}
        data['lan'] = public.GetLan('control')
        return render_template( 'control.html',data=data)

@app.route('/firewall',methods=method_all)
def firewall(pdata = None):
    comReturn = comm.local()
    if comReturn: return comReturn
    if request.method == method_get[0] and not pdata:
        data = {}
        data['lan'] = public.GetLan('firewall')
        return render_template( 'firewall.html',data=data)
    import firewalls
    firewallObject = firewalls.firewalls()
    defs = ('GetList','AddDropAddress','DelDropAddress','FirewallReload','SetFirewallStatus','AddAcceptPort','DelAcceptPort','SetSshStatus','SetPing','SetSshPort','GetSshInfo')
    return publicObject(firewallObject,defs,None,pdata);

@app.route('/firewall_new',methods=method_all)
def firewall_new(pdata = None):
    comReturn = comm.local()
    if comReturn: return comReturn
    if request.method == method_get[0] and not pdata:
        data = {}
        data['lan'] = public.GetLan('firewall')
        return render_template( 'firewall_new.html',data=data)
    import firewall_new
    firewallObject = firewall_new.firewalls()
    defs = ('GetList','AddDropAddress','DelDropAddress','FirewallReload','SetFirewallStatus','AddAcceptPort','DelAcceptPort','SetSshStatus','SetPing','SetSshPort','GetSshInfo','AddSpecifiesIp','DelSpecifiesIp')
    return publicObject(firewallObject,defs,None,pdata);


@app.route('/monitor', methods=method_all)
def panel_monitor(pdata=None):
    comReturn = comm.local()
    if comReturn: return comReturn
    import monitor
    dataObject = monitor.Monitor()
    defs = ('get_spider', 'get_exception', 'get_request_count_qps', 'load_and_up_flow', 'get_request_count_by_hour')
    return publicObject(dataObject, defs, None, pdata)


@app.route('/san', methods=method_all)
def san_baseline(pdata=None):
    comReturn = comm.local()
    if comReturn: return comReturn
    import san_baseline
    dataObject = san_baseline.san_baseline()
    defs = ('start', 'get_api_log', 'get_resut', 'get_ssh_errorlogin','repair','repair_all')
    return publicObject(dataObject, defs, None, pdata)

@app.route('/password', methods=method_all)
def panel_password(pdata=None):
    comReturn = comm.local()
    if comReturn: return comReturn
    import password
    dataObject = password.password()
    defs = ('set_root_password', 'get_mysql_root', 'set_mysql_password', 'set_panel_password', 'SetPassword', 'SetSshKey','StopKey','GetConfig','StopPassword','GetKey','get_databses','rem_mysql_pass','set_mysql_access',"get_panel_username")
    return publicObject(dataObject, defs, None, pdata)


@app.route('/bak', methods=method_all)
def backup_bak(pdata=None):
    comReturn = comm.local()
    if comReturn: return comReturn
    import backup_bak
    dataObject = backup_bak.backup_bak()
    defs = ('get_sites', 'get_databases', 'backup_database', 'backup_site', 'backup_path', 'get_database_progress',
            'get_site_progress', 'down','get_down_progress','download_path','backup_site_all','get_all_site_progress','backup_date_all','get_all_date_progress')
    return publicObject(dataObject, defs, None, pdata)


@app.route('/abnormal', methods=method_all)
def abnormal(pdata=None):
    comReturn = comm.local()
    if comReturn: return comReturn
    import abnormal
    dataObject = abnormal.abnormal()
    defs = ('mysql_server', 'mysql_cpu', 'mysql_count', 'php_server', 'php_conn_max', 'php_cpu', 'CPU', 'Memory', 'disk', 'not_root_user', 'start')
    return publicObject(dataObject, defs, None, pdata)

@app.route('/files',methods=method_all)
def files(pdata = None):
    comReturn = comm.local()
    if comReturn: return comReturn
    if request.method == method_get[0] and not request.args.get('path') and not pdata:
        data = {}
        data['lan'] = public.GetLan('files')
        return render_template('files.html',data=data)
    import files
    filesObject = files.files()
    defs = ('CheckExistsFiles','GetExecLog','GetSearch','ExecShell','GetExecShellMsg','UploadFile','GetDir','CreateFile','CreateDir','DeleteDir','DeleteFile',
            'CopyFile','CopyDir','MvFile','GetFileBody','SaveFileBody','Zip','UnZip','SearchFiles','upload','read_history',
            'GetFileAccess','SetFileAccess','GetDirSize','SetBatchData','BatchPaste','install_rar','get_path_size',
            'DownloadFile','GetTaskSpeed','CloseLogs','InstallSoft','UninstallSoft','SaveTmpFile','GetTmpFile','del_files_store','add_files_store','get_files_store','del_files_store_types','add_files_store_types'
            'RemoveTask','ActionTask','Re_Recycle_bin','Get_Recycle_bin','Del_Recycle_bin','Close_Recycle_bin','Recycle_bin')
    return publicObject(filesObject,defs,None,pdata);


@app.route('/crontab',methods=method_all)
def crontab(pdata = None):
    comReturn = comm.local()
    if comReturn: return comReturn
    if request.method == method_get[0] and not pdata:
        data = {}
        data['lan'] = public.GetLan('crontab')
        return render_template( 'crontab.html',data=data)
    import crontab
    crontabObject = crontab.crontab()
    defs = ('GetCrontab','AddCrontab','GetDataList','GetLogs','DelLogs','DelCrontab','StartTask','set_cron_status','get_crond_find','modify_crond')
    return publicObject(crontabObject,defs,None,pdata);

@app.route('/soft',methods=method_all)
def soft(pdata = None):
    comReturn = comm.local()
    if comReturn: return comReturn
    if request.method == method_get[0] and not pdata:
        data={}
        data['lan'] = public.GetLan('soft')
        return render_template( 'soft.html',data=data)

@app.route('/config',methods=method_all)
def config(pdata = None):
    comReturn = comm.local()
    if comReturn: return comReturn
    if request.method == method_get[0] and not pdata:
        import system,wxapp,config
        c_obj = config.config()
        data = system.system().GetConcifInfo()
        data['lan'] = public.GetLan('config')
        try:
            data['wx'] = wxapp.wxapp().get_user_info(None)['msg']
        except:
            data['wx'] = '当前未绑定微信号'
        data['api'] = ''
        data['ipv6'] = '';
        sess_out_path = 'data/session_timeout.pl'
        if not os.path.exists(sess_out_path): public.writeFile(sess_out_path,'86400')
        workers_p = 'data/workers.pl'
        if not os.path.exists(workers_p): public.writeFile(workers_p,'1')
        data['workers'] = int(public.readFile(workers_p))
        s_time_tmp = public.readFile(sess_out_path)
        if not s_time_tmp: s_time_tmp = '0'
        data['session_timeout'] = int(s_time_tmp)
        if c_obj.get_ipv6_listen(None): data['ipv6'] = 'checked'
        if c_obj.get_token(None)['open']: data['api'] = 'checked'
        data['basic_auth'] = c_obj.get_basic_auth_stat(None)
        data['basic_auth']['value'] = '已关闭'
        if data['basic_auth']['open']: data['basic_auth']['value'] = '已开启'
        data['debug'] = ''
        if app.config['DEBUG']: data['debug'] = 'checked'
        data['is_local'] = ''
        if public.is_local(): data['is_local'] = 'checked'
        return render_template( 'config.html',data=data)
    import config
    defs = ('get_php_session_path','set_php_session_path','get_cert_source','set_local','set_debug','get_panel_error_logs','clean_panel_error_logs','get_basic_auth_stat','set_basic_auth','get_cli_php_version','get_tmp_token','set_cli_php_version','DelOldSession', 'GetSessionCount', 'SetSessionConf', 'GetSessionConf','get_ipv6_listen','set_ipv6_status','GetApacheValue','SetApacheValue','GetNginxValue','SetNginxValue','get_token','set_token','set_admin_path','is_pro','get_php_config','get_config','SavePanelSSL','GetPanelSSL','GetPHPConf','SetPHPConf','GetPanelList','AddPanelInfo','SetPanelInfo','DelPanelInfo','ClickPanelInfo','SetPanelSSL','SetTemplates','Set502','setPassword','setUsername','setPanel','setPathInfo','setPHPMaxSize','getFpmConfig','setFpmConfig','setPHPMaxTime','syncDate','setPHPDisable','SetControl','ClosePanel','AutoUpdatePanel','SetPanelLock')
    return publicObject(config.config(),defs,None,pdata);

@app.route('/ajax',methods=method_all)
def ajax(pdata = None):
    comReturn = comm.local()
    if comReturn: return comReturn
    import ajax
    ajaxObject = ajax.ajax()
    defs = ('change_phpmyadmin_ssl_port','set_phpmyadmin_ssl','get_phpmyadmin_ssl','check_user_auth','to_not_beta','get_beta_logs','apple_beta','GetApacheStatus','GetCloudHtml','get_load_average','GetOpeLogs','GetFpmLogs','GetFpmSlowLogs','SetMemcachedCache','GetMemcachedStatus','GetRedisStatus','GetWarning','SetWarning','CheckLogin','GetSpeed','GetAd','phpSort','ToPunycode','GetBetaStatus','SetBeta','setPHPMyAdmin','delClose','KillProcess','GetPHPInfo','GetQiniuFileList','UninstallLib','InstallLib','SetQiniuAS','GetQiniuAS','GetLibList','GetProcessList','GetNetWorkList','GetNginxStatus','GetPHPStatus','GetTaskCount','GetSoftList','GetNetWorkIo','GetDiskIo','GetCpuIo','CheckInstalled','UpdatePanel','GetInstalled','GetPHPConfig','SetPHPConfig')
    return publicObject(ajaxObject,defs,None,pdata);

@app.route('/system',methods=method_all)
def system(pdata = None):
    comReturn = comm.local()
    if comReturn: return comReturn
    import system
    sysObject = system.system()
    defs = ('get_io_info','UpdatePro','GetAllInfo','GetNetWorkApi','GetLoadAverage','ClearSystem','GetNetWorkOld','GetNetWork','GetDiskInfo','GetCpuInfo','GetBootTime','GetSystemVersion','GetMemInfo','GetSystemTotal','GetConcifInfo','ServiceAdmin','ReWeb','RestartServer','ReMemory','RepPanel')
    return publicObject(sysObject,defs,None,pdata);

@app.route('/deployment',methods=method_all)
def deployment(pdata = None):
    comReturn = comm.local()
    if comReturn: return comReturn
    import plugin_deployment
    sysObject = plugin_deployment.plugin_deployment()
    defs = ('GetList','AddPackage','DelPackage','SetupPackage','GetSpeed','GetPackageOther')
    return publicObject(sysObject,defs,None,pdata);

@app.route('/data',methods=method_all)
@app.route('/panel_data',methods=method_all)
def panel_data(pdata = None):
    comReturn = comm.local()
    if comReturn: return comReturn
    import data
    dataObject = data.data()
    defs = ('setPs','getData','getFind','getKey')
    return publicObject(dataObject,defs,None,pdata);

    
@app.route('/code')
def code():
    import vilidate,time
    code_time = cache.get('codeOut')
    if code_time: return u'Error: Don\'t request validation codes frequently';
    vie = vilidate.vieCode();
    codeImage = vie.GetCodeImage(80,4);
    if sys.version_info[0] == 2:
        try:
            from cStringIO import StringIO
        except:
            from StringIO import StringIO
        out = StringIO();
    else:
        from io import BytesIO
        out = BytesIO();
    codeImage[0].save(out, "png")
    cache.set("codeStr",public.md5("".join(codeImage[1]).lower()),180)
    cache.set("codeOut",1,0.1);
    out.seek(0)
    return send_file(out, mimetype='image/png', cache_timeout=0)


@app.route('/ssl',methods=method_all)
def ssl(pdata = None):
    comReturn = comm.local()
    if comReturn: return comReturn
    import panelSSL
    toObject = panelSSL.panelSSL()
    defs = ('RemoveCert','renew_lets_ssl','SetCertToSite','GetCertList','SaveCert','GetCert','GetCertName','DelToken','GetToken','GetUserInfo','GetOrderList','GetDVSSL','Completed','SyncOrder','GetSSLInfo','downloadCRT','GetSSLProduct','Renew_SSL','Get_Renew_SSL')
    result = publicObject(toObject,defs,None,pdata);
    return result;

@app.route('/task',methods=method_all)
def task(pdata = None):
    comReturn = comm.local()
    if comReturn: return comReturn
    import panelTask
    toObject = panelTask.bt_task()
    defs = ('get_task_lists','remove_task','get_task_find')
    result = publicObject(toObject,defs,None,pdata);
    return result;

@app.route('/plugin',methods=method_all)
def plugin(pdata = None):
    comReturn = comm.local()
    if comReturn: return comReturn
    import panelPlugin
    pluginObject = panelPlugin.panelPlugin()
    defs = ('update_zip','input_zip','export_zip','add_index','remove_index','sort_index','install_plugin','uninstall_plugin','get_soft_find','get_index_list','get_soft_list','get_cloud_list','check_deps','flush_cache','GetCloudWarning','install','unInstall','getPluginList','getPluginInfo','getPluginStatus','setPluginStatus','a','getCloudPlugin','getConfigHtml','savePluginSort')
    return publicObject(pluginObject,defs,None,pdata);



@app.route('/public',methods=method_all)
def panel_public():
    get = get_input();
    get.client_ip = public.GetClientIp();
    if not hasattr(get,'name'): get.name = ''
    if not hasattr(get,'fun'): return abort(404)
    if not public.path_safe_check("%s/%s" % (get.name,get.fun)): return abort(404)
    if get.fun in ['scan_login', 'login_qrcode', 'set_login', 'is_scan_ok', 'blind','static']:
        if get.fun == 'static':
            if not public.path_safe_check("%s" % (get.filename)): return abort(404)
            s_file = '/www/server/panel/BTPanel/static/' + get.filename
            if s_file.find('..') != -1 or s_file.find('./') != -1: return abort(404)
            if not os.path.exists(s_file): return abort(404)
            return send_file(s_file, conditional=True, add_etags=True)

        #检查是否验证过安全入口
        if get.fun in ['login_qrcode','is_scan_ok']:
            global admin_check_auth,admin_path,route_path,admin_path_file
            if admin_path != '/bt' and os.path.exists(admin_path_file) and  not 'admin_auth' in session: return 'False'
        import wxapp
        pluwx = wxapp.wxapp()
        checks = pluwx._check(get)
        if type(checks) != bool or not checks: return public.getJson(checks),json_header
        data = public.getJson(eval('pluwx.'+get.fun+'(get)'))
        return data,json_header
    
    import panelPlugin
    plu = panelPlugin.panelPlugin()
    get.s = '_check';
    checks = plu.a(get)
    if type(checks) != bool or not checks: return public.getJson(checks),json_header
    get.s = get.fun
    comm.setSession()
    comm.init()
    comm.checkWebType()
    comm.GetOS()
    result = plu.a(get)
    return public.getJson(result),json_header

@app.route('/favicon.ico',methods=method_get)
def send_favicon():
    s_file = '/www/server/panel/BTPanel/static/favicon.ico'
    if not os.path.exists(s_file): return abort(404)
    return send_file(s_file,conditional=True,add_etags=True)


@app.route('/coll',methods=method_all)
@app.route('/coll/',methods=method_all)
@app.route('/<name>/<fun>',methods=method_all)
@app.route('/<name>/<fun>/<path:stype>',methods=method_all)
def panel_other(name=None,fun = None,stype=None):
    if not name: name = 'coll'
    if not public.path_safe_check("%s/%s/%s" % (name,fun,stype)): return abort(404)
    if name.find('./') != -1 or not re.match("^[\w-]+$",name): return abort(404)
    if not name: return public.returnJson(False,'请传入插件名称!'),json_header
    p_path = '/www/server/panel/plugin/' + name
    if not os.path.exists(p_path): return abort(404)


    #是否响插件应静态文件
    if fun == 'static':
        if stype.find('./') != -1 or not os.path.exists(p_path + '/static'): return abort(404)
        s_file = p_path + '/static/' + stype
        if s_file.find('..') != -1: return abort(404)
        if not re.match("^[\w\./-]+$",s_file): return abort(404)
        if not public.path_safe_check(s_file): return abort(404)
        if not os.path.exists(s_file): return abort(404)
        return send_file(s_file,conditional=True,add_etags=True)

    #准备参数
    args = get_input();
    args.client_ip = public.GetClientIp();
    if not fun: fun = 'index.html'
    if not stype:
        tmp = fun.split('.')
        fun = tmp[0]
        if len(tmp) == 1:  tmp.append('')
        stype = tmp[1]
    args.fun = fun
    
    #初始化插件对象
    try:
        is_php = os.path.exists(p_path + '/index.php')
        if not is_php:
            sys.path.append(p_path);
            plugin_main = __import__(name+'_main')
            try:
                if sys.version_info[0] == 2:
                    reload(plugin_main)
                else:
                    from imp import reload
                    reload(plugin_main)
            except:pass
            plu = eval('plugin_main.' + name + '_main()')
            if not hasattr(plu,fun): return public.returnJson(False,'指定方法不存在!'),json_header

        #检查访问权限
        comReturn = comm.local()
        if comReturn: 
            if not is_php:
                if not hasattr(plu,'_check'): return public.returnJson(False,'指定插件不支持公共访问!'),json_header
                checks = plu._check(args)
                r_type = type(checks)
                if r_type == Response: return checks
                if r_type != bool or not checks: return public.getJson(checks),json_header

            #初始化面板数据
            comm.setSession()
            comm.init()
            comm.checkWebType()
            comm.GetOS()
    
            import panelPlugin
            plugins = panelPlugin.panelPlugin()
            args.name = name
            if not plugins.check_accept(args):
                return public.returnMsg(False,public.to_string([24744, 26410, 36141, 20080, 91, 37, 115, 93, 25110, 25480, 26435, 24050, 21040, 26399, 33]) % (plugins.get_title_byname(args),))
    
        #执行插件方法
        if not is_php:
            data = eval('plu.'+fun+'(args)')
        else:
            import panelPHP
            args.s = fun
            args.name = name
            data = panelPHP.panelPHP(name).exec_php_script(args)
            
        r_type = type(data)
        if r_type == Response: return data

        #处理响应
        if stype == 'json':  #响应JSON
            return public.getJson(data),json_header
        elif stype == 'html':   #使用模板
            t_path_root = p_path + '/templates/'
            t_path = t_path_root + fun + '.html'
            if not os.path.exists(t_path): return public.returnJson(False,'指定模板不存在!'),json_header
            t_body = public.readFile(t_path)

            #处理模板包含
            rep = '{%\s?include\s"(.+)"\s?%}'
            includes = re.findall(rep,t_body)
            for i_file in includes:
                filename = p_path + '/templates/' + i_file
                i_body = 'ERROR: File '+filename+' does not exists.'
                if os.path.exists(filename):
                    i_body = public.readFile(filename)
                t_body = re.sub(rep.replace('(.+)',i_file),i_body,t_body)

            return render_template_string(t_body,data = data)
        else:  #直接响应插件返回值,可以是任意flask支持的响应类型
            r_type = type(data)
            if r_type == dict: return public.returnJson(False,'错误的返回类型[%s]' % r_type),json_header
            return data
    except:
        error_info = public.get_error_info()
        public.submit_error(error_info)
        return error_info.replace('\n','<br>\n')


@app.route('/wxapp',methods=method_all)
@app.route('/panel_wxapp',methods=method_all)
def panel_wxapp(pdata = None):
    comReturn = comm.local()
    if comReturn: return comReturn
    import wxapp
    toObject = wxapp.wxapp()
    defs = ('blind','get_safe_log','blind_result','get_user_info','blind_del','blind_qrcode')
    result = publicObject(toObject,defs,None,pdata);
    return result;

@app.route('/hook',methods=method_all)
def panel_hook():
    get = get_input()
    if not os.path.exists('plugin/webhook'): return public.getJson(public.returnMsg(False,'INIT_WEBHOOK_ERR'));
    sys.path.append('plugin/webhook');
    import webhook_main
    return public.getJson(webhook_main.webhook_main().RunHook(get));

@app.route('/safe',methods=method_all)
def panel_safe():
    get = get_input()
    pluginPath = 'plugin/safelogin';
    if hasattr(get,'check'):
        if os.path.exists(pluginPath + '/safelogin_main.py'): return 'True';
        return 'False';
    get.data = check_token(get.data);
    if not get.data: return public.returnJson(False,'INIT_CHECK_ERR');
    comm.setSession()
    comm.init()
    comm.checkWebType()
    comm.GetOS()
    sys.path.append(pluginPath);
    import safelogin_main;
    reload(safelogin_main);
    s = safelogin_main.safelogin_main();
    if not hasattr(s,get.data['action']): return public.returnJson(False,'INIT_FUN_NOT_EXISTS');
    defs = ('GetServerInfo','add_ssh_limit','remove_ssh_limit','get_ssh_limit','get_login_log','get_panel_limit','add_panel_limit','remove_panel_limit','close_ssh_limit','close_panel_limit','get_system_info','get_service_info','get_ssh_errorlogin')
    if not get.data['action'] in defs: return 'False';
    return public.getJson(eval('s.' + get.data['action'] + '(get)'));


@app.route('/install',methods=method_all)
def install():
    if public.M('config').where("id=?",('1',)).getField('status') == 1: 
        if os.path.exists('install.pl'): os.remove('install.pl');
        return redirect('/login')
    ret_login = os.path.join('/',admin_path)
    if admin_path == '/' or admin_path == '/bt': ret_login = '/login'

    if request.method == method_get[0]:
        if not os.path.exists('install.pl'): return redirect(ret_login)
        data = {}
        data['status'] = os.path.exists('install.pl');
        data['username'] = public.GetRandomString(8).lower()
        return render_template( 'install.html',data = data)
    
    elif request.method == method_post[0]:
        if not os.path.exists('install.pl'): return redirect(ret_login)
        get = get_input()
        if not hasattr(get,'bt_username'): return '用户名不能为空!';
        if not get.bt_username: return '用户名不能为空!'
        if not hasattr(get,'bt_password1'): return '密码不能为空!';
        if not get.bt_password1: return '密码不能为空!';
        if get.bt_password1 != get.bt_password2: return '两次输入的密码不一致，请重新输入!';
        public.M('users').where("id=?",(1,)).save('username,password',(get.bt_username,public.md5(get.bt_password1.strip())))
        os.remove('install.pl');
        public.M('config').where("id=?",('1',)).setField('status',1);
        data = {}
        data['status'] = os.path.exists('install.pl');
        data['username'] = get.bt_username;
        return render_template( 'install.html',data = data)


#检查Token
def check_token(data):
    pluginPath = 'plugin/safelogin/token.pl';
    if not os.path.exists(pluginPath): return False;
    from urllib import unquote;
    from binascii import unhexlify;
    from json import loads;
        
    result = unquote(unhexlify(data));
    token = public.readFile(pluginPath).strip();
        
    result = loads(result);
    if not result: return False;
    if result['token'] != token: return False;
    return result;


@app.route('/auth',methods=method_all)
def auth(pdata = None):
    comReturn = comm.local()
    if comReturn: return comReturn
    import panelAuth
    toObject = panelAuth.panelAuth()
    defs = ('get_re_order_status_plugin','create_plugin_other_order','get_order_stat','get_voucher_plugin','create_order_voucher_plugin','get_product_discount_by','get_re_order_status','create_order_voucher','create_order','get_order_status','get_voucher','flush_pay_status','create_serverid','check_serverid','get_plugin_list','check_plugin','get_buy_code','check_pay_status','get_renew_code','check_renew_code','get_business_plugin','get_ad_list','check_plugin_end','get_plugin_price')
    result = publicObject(toObject,defs,None,pdata);
    return result;


@app.route('/robots.txt',methods=method_all)
def panel_robots():
    robots = '''User-agent: *
Disallow: /
'''
    return robots,{'Content-Type':'text/plain'}

@app.route('/download',methods=method_get)
def download():
    comReturn = comm.local()
    if comReturn: return comReturn
    filename = request.args.get('filename')
    if not filename: return public.ReturnJson(False,"INIT_ARGS_ERR"),json_header
    if filename in ['alioss','qiniu','upyun','txcos','ftp']: return panel_cloud()
    if not os.path.exists(filename): return public.ReturnJson(False,"FILE_NOT_EXISTS"),json_header
    mimetype = "application/octet-stream"
    extName = filename.split('.')[-1]
    if extName in ['png','gif','jpeg','jpg']: mimetype = None
    #if extName in ['mp4','avi']: mimetype = 'multipart/x-mixed-replace'
    return send_file(filename,mimetype=mimetype, as_attachment=True,attachment_filename=os.path.basename(filename),cache_timeout=0)

@app.route('/cloud',methods=method_get)
def panel_cloud():
    comReturn = comm.local()
    if comReturn: return comReturn
    get = get_input()
    if not os.path.exists('plugin/' + get.filename + '/' + get.filename+'_main.py'): return public.returnJson(False,'INIT_PLUGIN_NOT_EXISTS'),json_header
    sys.path.append('plugin/' + get.filename)
    plugin_main = __import__(get.filename+'_main')
    reload(plugin_main)
    tmp = eval("plugin_main.%s_main()" % get.filename)
    if not hasattr(tmp,'download_file'): return public.returnJson(False,'INIT_PLUGIN_NOT_DOWN_FUN'),json_header
    if get.filename == 'ftp':
        download_url = tmp.getFile(get.name)
    else:
        download_url = tmp.download_file(get.name)
        if download_url.find('http') != 0:download_url = 'http://' + download_url
    return redirect(download_url)

ssh = None
shell = None
try:
    import paramiko
    ssh = paramiko.SSHClient()
except:
    public.ExecShell('pip install paramiko==2.0.2 &')

@socketio.on('connect')
def socket_connect(msg=None):
    if not check_login(): 
        emit('server_response',{'data':public.getMsg('111')})
        return False

@socketio.on('webssh')
def webssh(msg):
    if not check_login(msg['x_http_token']): 
        emit('server_response',{'data':public.getMsg('INIT_WEBSSH_LOGOUT')})
        return None

    global shell,ssh
    ssh_success = True
    if type(msg['data']) == dict:
        if 'ssh_user' in msg['data']:
            connect_ssh(msg['data']['ssh_user'].strip(),msg['data']['ssh_passwd'].strip())
    if not shell: ssh_success = connect_ssh()
    if not shell:
        emit('server_response',{'data':public.getMsg('INIT_WEBSSH_CONN_ERR')})
        return;
    if shell.exit_status_ready(): ssh_success = connect_ssh()
    if not ssh_success:
        emit('server_response',{'data':public.getMsg('INIT_WEBSSH_CONN_ERR')})
        return;
    shell.send(msg['data'])
    time.sleep(0.005)
    recv = shell.recv(4096)
    emit('server_response',{'data':recv.decode("utf-8")})

def connect_ssh(user=None,passwd=None):
    global shell,ssh
    pkey = '/root/.ssh/id_rsa_bt'
    if not os.path.exists('/root/.ssh/authorized_keys') or not os.path.exists(pkey):
        create_rsa()
    try:
        if not user:
            key=paramiko.RSAKey.from_private_key_file(pkey)
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            if not user:
                ssh.connect('127.0.0.1', public.GetSSHPort(),pkey=key)
            else:
                ssh.connect('127.0.0.1', public.GetSSHPort(),username=user,password=passwd)
        except:
            if public.GetSSHStatus():
                try:
                    if not user:
                        ssh.connect('localhost', public.GetSSHPort(),pkey=key)
                    else:
                        ssh.connect('localhost', public.GetSSHPort(),username=user,password=passwd)
                except:
                    create_rsa()
                    return False;
            import firewalls
            fw = firewalls.firewalls()
            get = common.dict_obj()
            ssh_status = fw.GetSshInfo(get)['status']
            if not ssh_status:
                get.status = '0';
                fw.SetSshStatus(get)

            if not user:
                ssh.connect('127.0.0.1', public.GetSSHPort(),pkey=key)
            else:
                ssh.connect('127.0.0.1', public.GetSSHPort(),username=user,password=passwd)

            if not ssh_status:
                get.status = '1';
                fw.SetSshStatus(get);
        shell = ssh.invoke_shell(term='xterm', width=100, height=29)
        shell.setblocking(0)
        return True
    except:
        shell = None
        return False

def create_rsa():
    id_ras = '/root/.ssh/id_rsa_bt'
    a_keys = '/root/.ssh/authorized_keys'
    if not os.path.exists(a_keys) or not os.path.exists(id_ras):
        public.ExecShell("rm -f /root/.ssh/id_rsa_bt*")
        public.ExecShell('ssh-keygen -q -t rsa -P "" -f /root/.ssh/id_rsa_bt')
        public.ExecShell('cat /root/.ssh/id_rsa_bt.pub >> /root/.ssh/authorized_keys')
    else:
        id_ras_pub = '/root/.ssh/id_rsa_bt.pub'
        if os.path.exists(id_ras_pub):
            pub_body = public.readFile(id_ras_pub)
            keys_body = public.readFile(a_keys)
            if keys_body.find(pub_body) == -1:
                public.ExecShell('cat /root/.ssh/id_rsa_bt.pub >> /root/.ssh/authorized_keys')
    public.ExecShell('chmod 600 /root/.ssh/authorized_keys')
    
@socketio.on('connect_event')
def connected_msg(msg):
    if not check_login(): 
        emit('server_response',{'data':public.getMsg('INIT_WEBSSH_LOGOUT')})
        return None 
    global shell
    if not shell: connect_ssh()
    if shell:
        try:
            recv = shell.recv(8192)
            emit('server_response',{'data':recv.decode("utf-8")})
        except:
            pass


def check_csrf():
    if app.config['DEBUG']: return True
    request_token = request.cookies.get('request_token')
    if session['request_token'] != request_token: return False
    http_token = request.headers.get('x-http-token')
    if not http_token: return False
    if http_token != session['request_token_head']: return False
    cookie_token = request.headers.get('x-cookie-token')
    if cookie_token != session['request_token']: return False
    return True

def publicObject(toObject,defs,action=None,get = None):
    if 'request_token' in session and 'login' in session:
        if not check_csrf(): return public.ReturnJson(False,'CSRF校验失败，请重新登录面板'),json_header

    if not get: get = get_input()
    if action: get.action = action

    if hasattr(get,'path'):
            get.path = get.path.replace('//','/').replace('\\','/');
            if get.path.find('..') != -1: return public.ReturnJson(False,'不安全的路径'),json_header
            if get.path.find('->') != -1:
                get.path = get.path.split('->')[0].strip();
    
    for key in defs:
        if key == get.action:
            fun = 'toObject.'+key+'(get)'
            if hasattr(get,'html') or hasattr(get,'s_module'):
                return eval(fun)
            else:
                return public.GetJson(eval(fun)),json_header
    
    return public.ReturnJson(False,'ARGS_ERR'),json_header


def check_login(http_token=None):
    if cache.get('dologin'): return False
    if 'login' in session: 
        loginStatus = session['login']
        if loginStatus and http_token:
            if session['request_token_head'] != http_token: return False
        return loginStatus
    return False

def get_pd():
    tmp = -1
    try:
        import panelPlugin
        tmp1 = panelPlugin.panelPlugin().get_cloud_list()
    except:
        tmp1 = None
    if tmp1:
        tmp = tmp1[public.to_string([112,114,111])]
    else:
        tmp4 = cache.get(public.to_string([112, 95, 116, 111, 107, 101, 110]))
        if tmp4:
            tmp_f = public.to_string([47, 116, 109, 112, 47]) + tmp4
            if not os.path.exists(tmp_f): public.writeFile(tmp_f,'-1')
            tmp = public.readFile(tmp_f)
            if tmp: tmp = int(tmp)
    if tmp == -1:
        tmp3 = public.to_string([60, 115, 112, 97, 110, 32, 99, 108, 97, 115, 115, 61, 34, 98, 116, 112, 114, 111, 45, 103, 114, 97, 121, 34, 32, 111, 110, 99, 108, 105, 99, 107, 61, 34, 98, 116, 46, 115, 111, 102, 116, 46, 117, 112, 100, 97, 116, 97, 95, 112, 114, 111, 40, 41, 34, 32, 116, 105, 116, 108, 101, 61, 34, 28857, 20987, 21319, 32423, 21040, 19987, 19994, 29256, 34, 62, 20813, 36153, 29256, 60, 47, 115, 112, 97, 110, 62])
    elif tmp == -2:
        tmp3 = public.to_string([60, 115, 112, 97, 110, 32, 99, 108, 97, 115, 115, 61, 34, 98, 116, 112, 114, 111, 45, 103, 114, 97, 121, 34, 62, 60, 115, 112, 97, 110, 32,
                                115, 116, 121, 108, 101, 61, 34, 99, 111, 108, 111, 114, 58, 32, 35, 102, 99, 54, 100, 50, 54, 59, 102, 111, 110, 116, 45, 119, 101, 105, 103, 
                                104, 116, 58, 32, 98, 111, 108, 100, 59, 109, 97, 114, 103, 105, 110, 45, 114, 105, 103, 104, 116, 58, 53, 112, 120, 34, 62, 24050, 36807, 26399, 
                                60, 47, 115, 112, 97, 110, 62, 60, 97, 32, 99, 108, 97, 115, 115, 61, 34, 98, 116, 108, 105, 110, 107, 34, 32, 111, 110, 99, 108, 105, 99, 107, 61, 
                                34, 98, 116, 46, 115, 111, 102, 116, 46, 117, 112, 100, 97, 116, 97, 95, 112, 114, 111, 40, 41, 34, 62, 32493, 36153, 60, 47, 97, 62, 60, 47, 115, 112, 97, 110, 62])
    elif tmp >= 0:
        if tmp == 0:
            tmp2 = public.to_string([27704,20037,25480,26435])
            tmp3 = public.to_string([60, 115, 112, 97, 110, 32, 99, 108, 97, 115, 115, 61, 34, 98, 116, 112, 114, 111, 34, 62, 123, 48, 125, 60, 115, 112, 97, 110, 32, 115, 116, 
                                 121, 108, 101, 61, 34, 99, 111, 108, 111, 114, 58, 32, 35, 102, 99, 54, 100, 50, 54, 59, 102, 111, 110, 116, 45, 119, 101, 105, 103, 104, 116,
                                58, 32, 98, 111, 108, 100, 59, 34, 62, 123, 49, 125, 60, 47, 115, 112, 97, 110, 62, 60, 47, 115, 112, 97, 110, 62]).format(public.to_string([21040,26399,26102,38388,65306]),tmp2)
        else:
            tmp2 = time.strftime(public.to_string([37, 89, 45, 37, 109, 45, 37, 100]),time.localtime(tmp))
            tmp3 = public.to_string([60, 115, 112, 97, 110, 32, 99, 108, 97, 115, 115, 61, 34, 98, 116, 112, 114, 111, 34, 62, 21040, 26399, 26102, 38388, 65306, 60, 115, 112, 
                                     97, 110, 32, 115, 116, 121, 108, 101, 61, 34, 99, 111, 108, 111, 114, 58, 32, 35, 102, 99, 54, 100, 50, 54, 59, 102, 111, 110, 116, 45, 119, 
                                     101, 105, 103, 104, 116, 58, 32, 98, 111, 108, 100, 59, 109, 97, 114, 103, 105, 110, 45, 114, 105, 103, 104, 116, 58, 53, 112, 120, 34, 62, 123, 
                                     48, 125, 60, 47, 115, 112, 97, 110, 62, 60, 97, 32, 99, 108, 97, 115, 115, 61, 34, 98, 116, 108, 105, 110, 107, 34, 32, 111, 110, 99, 108, 105, 99, 
                                     107, 61, 34, 98, 116, 46, 115, 111, 102, 116, 46, 117, 112, 100, 97, 116, 97, 95, 112, 114, 111, 40, 41, 34, 62, 32493, 36153, 60, 47, 97, 62, 60, 
                                     47, 115, 112, 97, 110, 62]).format(tmp2)
    else:
        tmp3 = public.to_string([60, 115, 112, 97, 110, 32, 99, 108, 97, 115, 115, 61, 34, 98, 116, 112, 114, 111, 45, 103, 114, 97, 121, 34, 32, 111, 110, 99, 108, 105, 99, 107, 61, 34, 98, 116, 46, 115, 111, 102, 116, 46, 117, 112, 100, 97, 116, 97, 95, 112, 114, 111, 40, 41, 34, 32, 116, 105, 116, 108, 101, 61, 34, 28857, 20987, 21319, 32423, 21040, 19987, 19994, 29256, 34, 62, 20813, 36153, 29256, 60, 47, 115, 112, 97, 110, 62])
        
    return tmp3


@app.errorhandler(404)
def notfound(e):
    errorStr = public.ReadFile('./BTPanel/templates/' + public.GetConfigValue('template') + '/error.html')
    try:
        errorStr = errorStr.format(public.getMsg('PAGE_ERR_404_TITLE'),public.getMsg('PAGE_ERR_404_H1'),public.getMsg('PAGE_ERR_404_P1'),public.getMsg('NAME'),public.getMsg('PAGE_ERR_HELP'))
    except IndexError: pass
    return errorStr,404
  
@app.errorhandler(500)
def internalerror(e):
    #if str(e).find('Permanent Redirect') != -1: return e
    public.submit_error()
    errorStr = public.ReadFile('./BTPanel/templates/' + public.GetConfigValue('template') + '/error.html')
    try:
        if not app.config['DEBUG']:
            errorStr = errorStr.format(public.getMsg('PAGE_ERR_500_TITLE'),public.getMsg('PAGE_ERR_500_H1'),public.getMsg('PAGE_ERR_500_P1'),public.getMsg('NAME'),public.getMsg('PAGE_ERR_HELP'))
        else:
            errorStr = errorStr.format(public.getMsg('PAGE_ERR_500_TITLE'),str(e),'<pre>'+public.get_error_info() + '</pre>','以上调试信息仅在开发者模式显示','版本号: ' + public.version())
    except IndexError:pass
    return errorStr,500


#获取输入数据
def get_input():
    data = common.dict_obj()
    exludes = ['blob']
    for key in request.args.keys():
        data[key] = str(request.args.get(key,''))
    try:
        for key in request.form.keys():
            if key in exludes: continue
            data[key] = str(request.form.get(key,''))
    except:
        post = request.form.to_dict()
        for key in post.keys():
            if key in exludes: continue
            data[key] = str(post[key])

    if not hasattr(data,'data'): data.data = []
    return data

#取数据对象
def get_input_data(data):
    pdata = common.dict_obj()
    for key in data.keys():
        pdata[key] = str(data[key])
    return pdata
