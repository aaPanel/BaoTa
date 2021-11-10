#coding: utf-8
import os,sys,time,re,json
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


#面板日志分析统计
def logs_analysis():
    logs_path = '/www/server/panel/logs/request/'
    logs_tips = logs_path + 'tips/'
    admin_path = public.readFile('/www/server/panel/data/admin_path.pl')
    exolode_mods = ['data','warning','message','workorder','login','public','code','wxapp','webhook','webssh']
    if admin_path: 
        admin_path = admin_path.replace('/','')
        if admin_path: exolode_mods.append(admin_path)
    explode_names = ['GetNetWork','get_task_lists','get_index_list','UpdatePanel',
    'GetTaskCount','get_config','get_site_types','get_load_average','GetCpuIo',
    'GetDiskIo','GetNetWorkIo','SetControl','GetDirSize','GetSshInfo','get_host_list',
    'get_command_list','GetDataList','get_soft_list','upload','check_two_step','get_settings',
    'get_menu_list','GetSpeed','getConfigHtml','get_sync_task_find','get_buy_code','get_install_log']

    if not os.path.exists(logs_path): return
    if not os.path.exists(logs_tips): os.makedirs(logs_tips,384)
    import re
    if sys.version_info[0] == 2:
        from urlparse import parse_qs, urlparse
    else:
        from urllib.parse import parse_qs, urlparse
        
    for fname in os.listdir(logs_path):
        if fname in ['tips']:continue
        day_date = fname.split('.')[0]
        filename = logs_path + fname.replace('.gz','')
        tip_file = logs_tips + day_date + '.pl'
        if os.path.exists(tip_file): continue
        if fname[-2:] != 'gz': continue
        public.ExecShell("cd {} && gunzip {}".format(logs_path,fname))
        if not os.path.exists(filename): continue
        f = open(filename,'r')
        data_list = []
        tmp_list = {}
        while True:
            try:
                tmp_line = f.readline()
                if not tmp_line: break
                log_line = json.loads(tmp_line)
                tmp = {}
                tmp['client_type'] = 'pc' if not re.search('(iPhone|Mobile|Android|iPod|iOS)',log_line[4],re.I) else 'mobile'
                url_obj = urlparse(log_line[3])
                url_path = url_obj.path
                url_args = parse_qs(url_obj.query)
                mod_tmp = url_path.split('/')
                tmp['s_name'] = ''
                tmp['mod_name'] = ''
                if 'colony' in mod_tmp:
                    tmp['mod_name'] = mod_tmp[1] + '/' + mod_tmp[2]
                    if len(mod_tmp) > 3:
                        tmp['s_name'] = mod_tmp[3]
                else:
                    tmp['mod_name'] = mod_tmp[1]
                    if len(mod_tmp) > 2:
                        tmp['s_name'] = mod_tmp[2]

                if 'action' in url_args.keys():
                    if not url_args['action'] in [['a']]:
                        tmp['s_name'] = url_args['action'][0]
                    else:
                        tmp['s_name'] = url_args['s'][0]
                        tmp['mod_name'] = url_args['name'][0]
                if log_line[2] == 'POST':
                    if log_line[-2].find("\'") == -1:
                        try:
                            post = json.loads(log_line[-2].replace("'",'"'))
                            if 'action' in post.keys():
                                if not post['action'] in ['a']:
                                    tmp['s_name'] = post['action']
                                else:
                                    tmp['s_name'] = post['name']
                                    tmp['mod_name'] = post['s']
                        except:pass
                if not tmp['mod_name'] and not tmp['s_name']: tmp['mod_name'] = 'home'
                if tmp['mod_name'] in exolode_mods: continue
                if tmp['s_name'] in explode_names: continue
                key = public.md5(tmp['mod_name'] + '_' + tmp['s_name'])
                if key in tmp_list.keys():
                    tmp_list[key]['day_count'] += 1
                else:
                    tmp['day_count'] = 1
                    tmp_list[key] = tmp 
            except:
                print(public.get_error_info())
                break
        f.close()
        public.ExecShell("cd {} && gzip {}".format(logs_path,fname.replace('.gz','')))
        public.writeFile(tip_file,'')
        for k in tmp_list.keys():
            data_list.append(tmp_list[k])
        pdata = {
            'day_date': day_date,
            'data_list': json.dumps(data_list)
        }

        print(public.HttpPost('https://www.bt.cn/api/panel/model_total',pdata))
    
    panelPath = '/www/server/panel'
    logs_path = '{}/logs/click'.format(panelPath)
    logs_tips = logs_path + '/tips'
    if not os.path.exists(logs_tips): os.makedirs(logs_tips)        

    for fname in os.listdir(logs_path):
        if fname in ['tips']:continue
        tip_file = '{}/tips/{}.pl'.format(logs_path,day_date)
        if os.path.exists(tip_file): continue
        
        day_date = fname.split('.')[0]
        if public.format_date().find(day_date) >= 0: continue
        
        data_list = []
        try:                       
            rlist = json.loads(public.readFile(logs_path + '/' + fname))
        except :
            print(public.get_error_info())
            rlist = []

        for key in rlist:
            try:
                data_list.append({ 'client_type' :'pc','os':'linux','mod_name':key,'day_count':rlist[key] })
            except :pass            
        pdata = {'data_list': json.dumps(data_list),'day_date':day_date }
 
        ret = public.HttpPost('https://www.bt.cn/api/wpanel/model_click',pdata)
        print(ret)
        public.writeFile(tip_file,'')



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
logs_analysis()
