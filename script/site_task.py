# coding: utf-8
import os, sys, time, re, json
import psutil
import traceback

PANEL_PATH='/www/server/panel'
os.chdir(PANEL_PATH)
sys.path.insert(0, "class/")
sys.path.insert(0, PANEL_PATH)

# 检测是否有正在执行的任务， 有则杀死上个任务
for i in psutil.pids():
    try:
        if i == os.getpid():
            continue
        p = psutil.Process(i)
        is_python = False
        cmdline = p.cmdline()
    except:
        traceback.print_exc()
        continue

    for cmd_split in cmdline:
        if cmd_split.find('python') > 0:
            is_python = True
        if is_python and cmd_split.find('site_task.py') > 0:
            print("当前有站点任务正在执行，杀死上一个任务")
            p.kill()


import public


# 设置用户状态
def SetStatus(get):
    msg = public.getMsg('OFF')
    if get.status != '0': msg = public.getMsg('ON')
    username = 'Unknown'
    try:
        id = get['id']
        username = get['username']
        status = get['status']
        runPath = '/www/server/pure-ftpd/bin'
        if int(status) == 0:
            public.ExecShell(runPath + '/pure-pw usermod ' + username + ' -r 1')
        else:
            public.ExecShell(runPath + '/pure-pw usermod ' + username + " -r ''")
        FtpReload()
        public.M('ftps').where("id=?", (id,)).setField('status', status)
        public.WriteLog('TYPE_FTP', 'FTP_STATUS', (msg, username))
        return public.returnMsg(True, 'SUCCESS')
    except Exception as ex:
        public.WriteLog('TYPE_FTP', 'FTP_STATUS_ERR', (msg, username, str(ex)))
        return public.returnMsg(False, 'FTP_STATUS_ERR', (msg,))


def FtpReload():
    runPath = '/www/server/pure-ftpd/bin'
    public.ExecShell(runPath + '/pure-pw mkdb /www/server/pure-ftpd/etc/pureftpd.pdb')


def flush_ssh_log():
    """
    @name 更新ssh日志
    """

    try:

        c_time = 0
        c_file = '{}/data/ssh/time.day'.format(public.get_panel_path())
        try:
            c_time = int(public.readFile(c_file))
        except:
            pass

        if c_time:
            pass
        if time.time() - c_time > 86400:
            import PluginLoader
            # 登录成功日志
            args = public.dict_obj()
            args.model_index = 'safe'
            args.count = 100
            args.p = 1000000
            res = PluginLoader.module_run("syslog", "get_ssh_success", args)

            # 登录所有登录日志
            res = PluginLoader.module_run("syslog", "get_ssh_list", args)

            # 登录失败日志
            res = PluginLoader.module_run("syslog", "get_ssh_error", args)

            public.writeFile(c_file, str(int(time.time())))
        else:
            pass
    except:
        import traceback
        print(traceback.format_exc())
        pass


oldEdate = public.readFile('data/edate.pl')
if not oldEdate: oldEdate = '0000-00-00'
mEdate = time.strftime('%Y-%m-%d', time.localtime())
if oldEdate == mEdate:
    print('今日已处理')
    exit(0)
edateSites = public.M('sites').where('edate>? AND edate<? AND (status=? OR status=?)', ('0000-00-00', mEdate, 1, u'正在运行')).field('id,name,project_type', ).select()
import panelSite

siteObject = panelSite.panelSite()

from projectModel.javaModel import main as javaMod
from projectModel.pythonModel import main as pythonMod
from projectModel.nodejsModel import main as nodejsMod
from projectModel.otherModel import main as otherMod
from projectModel.goModel import main as goMod

mods = {
    "java": javaMod(),
    "python": pythonMod(),
    "node": nodejsMod(),
    "other": otherMod(),
    "go": goMod()
}

for site in edateSites:
    get = public.dict_obj()
    get.id = site['id']
    get.name = site['name']

    if site['project_type'] == "PHP":
        siteObject.SiteStop(get)

        bind_ftp = public.M('ftps').where('pid=?', get.id).find()
        if bind_ftp:
            # get = public.dict_obj()
            get.id = bind_ftp['id']
            get.username = bind_ftp['name']
            get.status = '0'
            SetStatus(get)

    try:
        if site['project_type'] == "JAVA":
            mods["java"].stop_project(get)

        if site['project_type'] == "Node":
            mods["node"].stop_project(get)

        if site['project_type'] == "Go":
            mods["go"].stop_project(get)

        if site['project_type'] == "Python":
            mods["python"].StopProject(get)

        if site['project_type'] == "Other":
            mods["other"].stop_project(get)
    except:
        public.debug_log()


oldEdate = mEdate
public.writeFile('/www/server/panel/data/edate.pl', mEdate)

# flush_ssh_log()

def deal_with_docker_expired_site():
    '''
        @name Docker网站项目-网站到期处理
    '''
    try:
        # 2024/11/19 11:13 1天只检查1次
        # pl_file = '{}/data/check_deal_with_docker_expired_site.pl'.format(PANEL_PATH)
        # if os.path.exists(pl_file):
        #     mtime = os.path.getmtime(pl_file)
        #     if time.time() - mtime < 86400: return
        # ↑
        # └-----如上的检查逻辑已在 data/edate.pl 中处理，本脚本每天实际只运行一次

        from btdockerModel import dk_public as dp
        sresult = dp.sql("docker_sites").field("id,name,edate").select()
        if not sresult: return

        from mod.project.docker.sites.sitesManage import SitesManage
        site_manage = SitesManage()

        for site in sresult:
            if not site: continue
            if site['edate'] == '0000-00-00': continue
            if site['edate'] == time.strftime('%Y-%m-%d', time.localtime()): continue
            if site['edate'] < time.strftime('%Y-%m-%d', time.localtime()):
                args = public.dict_obj()
                args.id = site['id']
                args.status = 0
                args.site_name = site['name']
                site_manage.set_site_status(args)
                public.WriteLog("Docker网站项目-网站到期处理", "网站{}已到期".format(site['name']))

        # if not os.path.exists(pl_file): public.writeFile(pl_file, 'True')
    except:
        pass


deal_with_docker_expired_site()


if public.get_improvement():
    import PluginLoader

    PluginLoader.start_total()
