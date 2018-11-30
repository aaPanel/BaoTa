#coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板 
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: 黄文良 <287962566@qq.com>
# +-------------------------------------------------------------------
import sys,json,os,time,logging
if sys.version_info[0] != 2:
        from imp import reload
sys.path.append('class/')
import public
from flask import Flask
app = Flask(__name__,template_folder="templates/" + public.GetConfigValue('template'))
from flask import Flask,current_app,session,render_template,send_file,request,redirect,g,url_for,make_response
from flask_session import Session
from werkzeug.contrib.cache import SimpleCache
from flask_socketio import SocketIO,emit,send

cache = SimpleCache()
socketio = SocketIO()
socketio.init_app(app)

import common,db,jobs,uuid
jobs.control_init()
app.secret_key = uuid.UUID(int=uuid.getnode()).hex[-12:]
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
    app.config['SESSION_FILE_THRESHOLD'] = 1024
    app.config['SESSION_FILE_MODE'] = 384
    s_sqlite = False

app.config['SESSION_PERMANENT'] = True
app.config['SESSION_USE_SIGNER'] = True
app.config['SESSION_KEY_PREFIX'] = 'BT_:'
app.config['SESSION_COOKIE_NAME'] = "BT_PANEL_6"
app.config['PERMANENT_SESSION_LIFETIME'] = 86400
Session(app)

if s_sqlite: sdb.create_all()

from datetime import datetime
import socket
import paramiko

comm = common.panelAdmin()
method_all = ['GET','POST']
method_get = ['GET']
method_post = ['POST']
json_header = {'Content-Type':'application/json; charset=utf-8'}
cache.set('p_token','bmac_' + public.Md5(public.get_mac_address()))
admin_path_file = 'data/admin_path.pl'
admin_path = '/'
if os.path.exists(admin_path_file): admin_path = public.readFile(admin_path_file).strip()
admin_path_checks = ['/','/close','/login','/site','/sites','ftp','/public','/database','/data','/download_file','/control','/crontab','/firewall','/files','config','/soft','/ajax','/system','/panel_data','/code','/ssl','/plugin','/wxapp','/hook','/safe','/yield','/downloadApi','/pluginApi','/auth','/download','/cloud','/webssh','/connect_event','/panel']
if admin_path in admin_path_checks: admin_path = '/bt'


@app.route('/service_status',methods = method_get)
def service_status():
    return 'True'

@app.route('/',methods=method_all)
def home():
    comReturn = comm.local()
    if comReturn: return comReturn
    data = {}
    data[public.to_string([112, 100])] = get_pd()
    data['siteCount'] = public.M('sites').count()
    data['ftpCount'] = public.M('ftps').count()
    data['databaseCount'] = public.M('databases').count()
    data['lan'] = public.GetLan('index')
    return render_template( 'index.html',data = data)


@app.route('/close',methods=method_get)
def close():
    if not os.path.exists('data/close.pl'): return redirect('/')
    data = {}
    data['lan'] = public.getLan('close');
    return render_template('close.html',data=data)

@app.route('/login',methods=method_all)
@app.route(os.path.join(admin_path,''),methods=method_all)
def login():
    global admin_check_auth,admin_path
    is_auth_path = False
    if admin_path != '/bt' and os.path.exists(admin_path_file) and  not 'admin_auth' in session: is_auth_path = True
    get = get_input()
    if hasattr(get,'dologin'):
        login_path = '/login'
        if is_auth_path: login_path = admin_path
        if session['login'] != False:
            session['login'] = False;
            cache.set('dologin',True)
            return redirect(login_path)
    
    if is_auth_path:
        if not admin_path.replace('/','') in request.path.split('/') and os.path.join(admin_path,'') != request.path: 
            data = {}
            data['lan'] = public.getLan('close');
            return render_template('autherr.html',data=data)
    session['admin_auth'] = True
    comReturn = common.panelSetup().init()
    if comReturn: return comReturn
    import userlogin
    if request.method == method_post[0]:
        result = userlogin.userlogin().request_post(get)
        if 'login' in session:
            if session['login'] == True:
                result = make_response(result)
                request_token = public.md5(app.secret_key + str(time.time()))
                session['request_token'] = request_token
                result.set_cookie('request_token',request_token,httponly=True,max_age=86400*30)
        return result

    if request.method == method_get[0]:
        result = userlogin.userlogin().request_get(get)
        if result: return result
        data = {}
        data['lan'] = public.GetLan('login')
        return render_template(
            'login.html',
            data=data
            )

@app.route('/sites/<action>',methods=method_all)
@app.route('/sites',methods=method_all)
def sites(action = None,pdata = None):
    comReturn = comm.local()
    if comReturn: return comReturn
    import sites
    siteObject = sites.sites()
    defs = ('create_site','remove_site','add_domain','remove_domain','open_ssl','close_ssl')
    return publicObject(siteObject,defs,action,pdata);

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
        
    defs = ('GetSiteLogs','GetSiteDomains','GetSecurity','SetSecurity','ProxyCache','CloseToHttps','HttpToHttps','SetEdate','SetRewriteTel','GetCheckSafe','CheckSafe','GetDefaultSite','SetDefaultSite','CloseTomcat','SetTomcat','apacheAddPort','AddSite','GetPHPVersion','SetPHPVersion','DeleteSite','AddDomain','DelDomain','GetDirBinding','AddDirBinding','GetDirRewrite','DelDirBinding'
            ,'get_site_types','add_site_type','remove_site_type','modify_site_type_name','set_site_type','UpdateRulelist','SetSiteRunPath','GetSiteRunPath','SetPath','SetIndex','GetIndex','GetDirUserINI','SetDirUserINI','GetRewriteList','SetSSL','SetSSLConf','CreateLet','CloseSSLConf','GetSSL','SiteStart','SiteStop'
            ,'Set301Status','Get301Status','CloseLimitNet','SetLimitNet','GetLimitNet','SetProxy','GetProxy','ToBackup','DelBackup','GetSitePHPVersion','logsOpen','GetLogsStatus','CloseHasPwd','SetHasPwd','GetHasPwd','GetDnsApi','SetDnsApi')
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
        return render_template( 'ftp.html',data=data)
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
    comReturn = comm.local()
    if comReturn: return comReturn
    if request.method == method_get[0] and not pdata:
        pmd = get_phpmyadmin_dir();
        session['phpmyadminDir'] = False
        if pmd: 
            session['phpmyadminDir'] = 'http://' + public.GetHost() + ':'+ pmd[1] + '/' + pmd[0];
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
        return render_template( 'firewall.html',data=data)
    import firewall_new
    firewallObject = firewall_new.firewalls()
    defs = ('GetList','AddDropAddress','DelDropAddress','FirewallReload','SetFirewallStatus','AddAcceptPort','DelAcceptPort','SetSshStatus','SetPing','SetSshPort','GetSshInfo','AddSpecifiesIp','DelSpecifiesIp')
    return publicObject(firewallObject,defs,None,pdata);


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
            'CopyFile','CopyDir','MvFile','GetFileBody','SaveFileBody','Zip','UnZip',
            'GetFileAccess','SetFileAccess','GetDirSize','SetBatchData','BatchPaste',
            'DownloadFile','GetTaskSpeed','CloseLogs','InstallSoft','UninstallSoft','SaveTmpFile','GetTmpFile',
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
        import system,wxapp
        data = system.system().GetConcifInfo()
        data['lan'] = public.GetLan('config')
        data['wx'] = wxapp.wxapp().get_user_info(None)['msg']
        return render_template( 'config.html',data=data)
    import config
    configObject = config.config()
    defs = ('set_admin_path','is_pro','get_php_config','get_config','SavePanelSSL','GetPanelSSL','GetPHPConf','SetPHPConf','GetPanelList','AddPanelInfo','SetPanelInfo','DelPanelInfo','ClickPanelInfo','SetPanelSSL','SetTemplates','Set502','setPassword','setUsername','setPanel','setPathInfo','setPHPMaxSize','getFpmConfig','setFpmConfig','setPHPMaxTime','syncDate','setPHPDisable','SetControl','ClosePanel','AutoUpdatePanel','SetPanelLock')
    return publicObject(configObject,defs,None,pdata);

@app.route('/ajax',methods=method_all)
def ajax(pdata = None):
    comReturn = comm.local()
    if comReturn: return comReturn
    import ajax
    ajaxObject = ajax.ajax()
    defs = ('GetCloudHtml','get_load_average','GetOpeLogs','GetFpmLogs','GetFpmSlowLogs','SetMemcachedCache','GetMemcachedStatus','GetRedisStatus','GetWarning','SetWarning','CheckLogin','GetSpeed','GetAd','phpSort','ToPunycode','GetBetaStatus','SetBeta','setPHPMyAdmin','delClose','KillProcess','GetPHPInfo','GetQiniuFileList','UninstallLib','InstallLib','SetQiniuAS','GetQiniuAS','GetLibList','GetProcessList','GetNetWorkList','GetNginxStatus','GetPHPStatus','GetTaskCount','GetSoftList','GetNetWorkIo','GetDiskIo','GetCpuIo','CheckInstalled','UpdatePanel','GetInstalled','GetPHPConfig','SetPHPConfig')
    return publicObject(ajaxObject,defs,None,pdata);

@app.route('/system',methods=method_all)
def system(pdata = None):
    comReturn = comm.local()
    if comReturn: return comReturn
    import system
    sysObject = system.system()
    defs = ('get_io_info','UpdatePro','GetAllInfo','GetNetWorkApi','GetLoadAverage','ClearSystem','GetNetWorkOld','GetNetWork','GetDiskInfo','GetCpuInfo','GetBootTime','GetSystemVersion','GetMemInfo','GetSystemTotal','GetConcifInfo','ServiceAdmin','ReWeb','RestartServer','ReMemory','RepPanel')
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
    if code_time: return u'请不要频繁获取验证码';
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
    cache.set("codeOut",1,0.2);
    out.seek(0)
    return send_file(out, mimetype='image/png', cache_timeout=0)


@app.route('/ssl',methods=method_all)
def ssl(pdata = None):
    comReturn = comm.local()
    if comReturn: return comReturn
    import panelSSL
    toObject = panelSSL.panelSSL()
    defs = ('RemoveCert','SetCertToSite','GetCertList','SaveCert','GetCert','GetCertName','DelToken','GetToken','GetUserInfo','GetOrderList','GetDVSSL','Completed','SyncOrder','GetSSLInfo','downloadCRT','GetSSLProduct')
    result = publicObject(toObject,defs,None,pdata);
    return result;

@app.route('/plugin',methods=method_all)
def plugin(pdata = None):
    comReturn = comm.local()
    if comReturn: return comReturn
    import panelPlugin
    pluginObject = panelPlugin.panelPlugin()
    defs = ('add_index','remove_index','sort_index','install_plugin','uninstall_plugin','get_soft_find','get_index_list','get_soft_list','get_cloud_list','check_deps','flush_cache','GetCloudWarning','install','unInstall','getPluginList','getPluginInfo','getPluginStatus','setPluginStatus','a','getCloudPlugin','getConfigHtml','savePluginSort')
    return publicObject(pluginObject,defs,None,pdata);



@app.route('/public',methods=method_all)
def panel_public():
    get = get_input();
    get.client_ip = public.GetClientIp();
    if get.fun in ['scan_login','login_qrcode','set_login','is_scan_ok','blind']:
        import wxapp
        pluwx = wxapp.wxapp()
        checks = pluwx._check(get)
        if type(checks) != bool or not checks: return public.getJson(checks),json_header
        data = public.getJson(eval('pluwx.'+get.fun+'(get)'))
        return data,json_header
        
    import panelPlugin
    plu = panelPlugin.panelPlugin();
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
    if not os.path.exists('plugin/webhook'): return public.getJson(public.returnMsg(False,'请先安装WebHook组件!'));
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
    if not get.data: return public.returnJson(False,'验证失败');
    comm.setSession()
    comm.init()
    comm.checkWebType()
    comm.GetOS()
    sys.path.append(pluginPath);
    import safelogin_main;
    reload(safelogin_main);
    s = safelogin_main.safelogin_main();
    if not hasattr(s,get.data['action']): return public.returnJson(False,'方法不存在');
    defs = ('GetServerInfo','add_ssh_limit','remove_ssh_limit','get_ssh_limit','get_login_log','get_panel_limit','add_panel_limit','remove_panel_limit','close_ssh_limit','close_panel_limit','get_system_info','get_service_info','get_ssh_errorlogin')
    if not get.data['action'] in defs: return 'False';
    return public.getJson(eval('s.' + get.data['action'] + '(get)'));


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

@app.route('/yield',methods=method_all)
def panel_yield():
    get = get_input()
    import panelPlugin
    plu = panelPlugin.panelPlugin();
    get.s = '_check';
    get.client_ip = public.GetClientIp()
    checks = plu.a(get)
    if type(checks) != bool or not checks: return
    get.s = get.fun
    filename = plu.a(get);
    mimetype = 'application/octet-stream'
    return send_file(filename,mimetype=mimetype, as_attachment=True,attachment_filename=os.path.basename(filename))

@app.route('/downloadApi',methods=method_all)
def panel_downloadApi():
    get = get_input()
    if not public.checkToken(get): get.filename = str(time.time());
    filename = 'plugin/psync/backup/' + get.filename.encode('utf-8');
    mimetype = 'application/octet-stream'
    return send_file(filename,mimetype=mimetype, as_attachment=True,attachment_filename=os.path.basename(filename))


@app.route('/pluginApi',methods=method_all)
def panel_pluginApi():
    get = get_input()
    if not public.checkToken(get): return public.returnJson(False,'无效的Token!');
    infoFile = 'plugin/' + get.name + '/info.json';
    if not os.path.exists(infoFile): return False;
    import json
    info = json.loads(public.readFile(infoFile));
    if not info['api']:  return public.returnJson(False,'您没有权限访问当前插件!');

    import panelPlugin
    pluginObject = panelPlugin.panelPlugin();
    defs = ('install','unInstall','getPluginList','getPluginInfo','getPluginStatus','setPluginStatus','a','getCloudPlugin','getConfigHtml','savePluginSort')
    return publicObject(pluginObject,defs);

@app.route('/auth',methods=method_all)
def auth(pdata = None):
    comReturn = comm.local()
    if comReturn: return comReturn
    import panelAuth
    toObject = panelAuth.panelAuth()
    defs = ('get_re_order_status_plugin','get_voucher_plugin','create_order_voucher_plugin','get_product_discount_by','get_re_order_status','create_order_voucher','create_order','get_order_status','get_voucher','flush_pay_status','create_serverid','check_serverid','get_plugin_list','check_plugin','get_buy_code','check_pay_status','get_renew_code','check_renew_code','get_business_plugin','get_ad_list','check_plugin_end','get_plugin_price')
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
    if not filename: return public.ReturnJson(False,"参数错误!"),json_header
    if filename in ['alioss','qiniu','upyun','txcos']: return panel_cloud()
    if not os.path.exists(filename): return public.ReturnJson(False,"指定文件不存在!"),json_header
    mimetype = "application/octet-stream"
    extName = filename.split('.')[-1]
    if extName in ['png','gif','jpeg','jpg']: mimetype = None
    return send_file(filename,mimetype=mimetype, as_attachment=True,attachment_filename=os.path.basename(filename))

@app.route('/cloud',methods=method_get)
def panel_cloud():
    comReturn = comm.local()
    if comReturn: return comReturn
    get = get_input()
    if not os.path.exists('plugin/' + get.filename + '/' + get.filename+'_main.py'): return public.returnJson(False,'指定插件不存在!'),json_header
    sys.path.append('plugin/' + get.filename)
    plugin_main = __import__(get.filename+'_main')
    reload(plugin_main)
    tmp = eval("plugin_main.%s_main()" % get.filename)
    if not hasattr(tmp,'download_file'): return public.returnJson(False,'指定插件没有文件下载方法!'),json_header
    return redirect(tmp.download_file(get.name))

ssh = paramiko.SSHClient()
shell = None

@socketio.on('webssh')
def webssh(msg):
    if not check_login(): 
        emit('server_response',{'data':'会话丢失，请重新登陆面板!\r\n'})
        return None
    global shell,ssh
    ssh_success = True
    if not shell: ssh_success = connect_ssh()
    if not shell:
        emit('server_response',{'data':'连接SSH服务失败!\r\n'})
        return;
    if shell.exit_status_ready(): ssh_success = connect_ssh()
    if not ssh_success:
        emit('server_response',{'data':'连接SSH服务失败!\r\n'})
        return;
    shell.send(msg)
    try:
        time.sleep(0.005)
        recv = shell.recv(4096)
        emit('server_response',{'data':recv.decode("utf-8")})
    except Exception as ex:
        pass

def connect_ssh():
    global shell,ssh
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect('127.0.0.1', public.GetSSHPort())
    except:
        if public.GetSSHStatus():
            try:
                ssh.connect('localhost', public.GetSSHPort())
            except:
                return False;
        import firewalls
        fw = firewalls.firewalls()
        get = common.dict_obj()
        get.status = '0';
        fw.SetSshStatus(get)
        ssh.connect('127.0.0.1', public.GetSSHPort())
        get.status = '1';
        fw.SetSshStatus(get);
    shell = ssh.invoke_shell(term='xterm', width=100, height=29)
    shell.setblocking(0)
    return True
    
@socketio.on('connect_event')
def connected_msg(msg):
    if not check_login(): 
        emit(pdata.s_response,{'data':'会话丢失，请重新登陆面板!\r\n'})
        return None 
    try:
        recv = shell.recv(8192)
        emit('server_response',{'data':recv.decode("utf-8")})
    except:pass

@socketio.on('panel')
def websocket_test(data):
    pdata = get_input_data(data)
    if not check_login():
        emit(pdata.s_response,{'data':public.returnMsg(-1,'会话丢失，请重新登陆面板!')})
        return None 
    mods = ['site','ftp','database','ajax','system','crontab','files','config','panel_data','plugin','ssl','auth','firewall','panel_wxapp']
    if not pdata['s_module'] in mods:
        result = public.returnMsg(False,"指定模块不存在!")
    else:
        result = eval("%s(pdata)" % pdata['s_module'])
    if not hasattr(pdata,'s_response'): pdata.s_response = 'response'
    emit(pdata.s_response,{'data':result})

def publicObject(toObject,defs,action=None,get = None):
    if 'request_token' in session and 'login' in session:
        request_token = request.cookies.get('request_token')
        if session['request_token'] != request_token:
            if session['login'] != False:
                session['login'] = False;
                cache.set('dologin',True)
                return redirect('/login')

    if not get: get = get_input()
    if action: get.action = action
    if hasattr(get,'path'):
            get.path = get.path.replace('//','/').replace('\\','/');
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


def check_login():
    if cache.get('dologin'): return False
    if 'login' in session: 
        loginStatus = session['login']
        return loginStatus
    return False

def get_pd():
    tmp = -1
    tmp1 = cache.get(public.to_string([112, 108, 117, 103, 105, 110, 95, 115, 111, 102, 116, 95, 108, 105, 115, 116]))
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
        tmp3 = public.to_string([20813,36153,29256])
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
        tmp3 = public.to_string([20813,36153,29256])
        
    return tmp3


@app.errorhandler(404)
def notfound(e):
    errorStr = '''<!doctype html>
<html lang="zh">
    <head>
        <meta charset="utf-8">
        <title>%s</title>
    </head>
    <body>
        <h1>%s</h1>
        <p>%s</p>
        <hr>
        <address>%s 6.x <a href="https://www.bt.cn/bbs" target="_blank">%s</a></address>
    </body>
</html>''' % (public.getMsg('PAGE_ERR_404_TITLE'),public.getMsg('PAGE_ERR_404_H1'),public.getMsg('PAGE_ERR_404_P1'),public.getMsg('NAME'),public.getMsg('PAGE_ERR_HELP'))
    return errorStr,404
  
@app.errorhandler(500)
def internalerror(e):
    errorStr = '''<!doctype html>
<html lang="zh">
    <head>
        <meta charset="utf-8">
        <title>%s</title>
    </head>
    <body>
        <h1>%s</h1>
        <p>%s</p>
        <hr>
        <address>%s 6.x <a href="https://www.bt.cn/bbs" target="_blank">%s</a></address>
    </body>
</html>'''  % (public.getMsg('PAGE_ERR_500_TITLE'),public.getMsg('PAGE_ERR_500_H1'),public.getMsg('PAGE_ERR_500_P1'),public.getMsg('NAME'),public.getMsg('PAGE_ERR_HELP'))
    return errorStr,500


#获取输入数据
def get_input():
    data = common.dict_obj()
    post = request.form.to_dict()
    get = request.args.to_dict()
    data.args = get
    for key in get.keys():
        data[key] = str(get[key])
    for key in post.keys():
        data[key] = str(post[key])

    if not hasattr(data,'data'): data.data = []
    return data

#取数据对象
def get_input_data(data):
    pdata = common.dict_obj()
    for key in data.keys():
        pdata[key] = str(data[key])
    return pdata
