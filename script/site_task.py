#coding: utf-8
import os,sys,time
os.chdir('/www/server/panel/')
sys.path.insert(0,"class/")
import public

#设置用户状态
def SetStatus(get):
    msg = public.getMsg('OFF')
    if get.status != '0': msg = public.getMsg('ON')
    try:
        id = get['id']
        username = get['username']
        status = get['status']
        runPath = '/www/server/pure-ftpd/bin'
        if int(status)==0:
            public.ExecShell(runPath + '/pure-pw usermod ' + username + ' -r 1')
        else:
            public.ExecShell(runPath + '/pure-pw usermod ' + username + " -r ''")
        FtpReload()
        public.M('ftps').where("id=?",(id,)).setField('status',status)
        public.WriteLog('TYPE_FTP','FTP_STATUS', (msg,username))
        return public.returnMsg(True, 'SUCCESS')
    except Exception as ex:
        public.WriteLog('TYPE_FTP','FTP_STATUS_ERR', (msg,username,str(ex)))
        return public.returnMsg(False,'FTP_STATUS_ERR',(msg,))

def FtpReload():
    runPath = '/www/server/pure-ftpd/bin'
    public.ExecShell(runPath + '/pure-pw mkdb /www/server/pure-ftpd/etc/pureftpd.pdb')


oldEdate = public.readFile('data/edate.pl')
if not oldEdate: oldEdate = '0000-00-00'
mEdate = time.strftime('%Y-%m-%d',time.localtime())
edateSites = public.M('sites').where('edate>? AND edate<? AND (status=? OR status=?)',('0000-00-00',mEdate,1,u'正在运行')).field('id,name').select()
import panelSite
siteObject = panelSite.panelSite()
for site in edateSites:
    get = public.dict_obj()
    get.id = site['id']
    get.name = site['name']
    siteObject.SiteStop(get)
    
    bind_ftp = public.M('ftps').where('pid=?',get.id).find()
    if bind_ftp:
        get = public.dict_obj()
        get.id = bind_ftp['id']
        get.username = bind_ftp['name']
        get.status = '0'
        SetStatus(get)
oldEdate = mEdate
public.writeFile('/www/server/panel/data/edate.pl',mEdate)

