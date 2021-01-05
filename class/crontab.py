#coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 宝塔软件(http:#bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: hwliang <hwl@bt.cn>
# +-------------------------------------------------------------------
import public,db,os,time,re
from BTPanel import session,cache
class crontab:
    field = 'id,name,type,where1,where_hour,where_minute,echo,addtime,status,save,backupTo,sName,sBody,sType,urladdress'
    #取计划任务列表
    def GetCrontab(self,get):
        self.checkBackup()
        self.__clean_log()
        cront = public.M('crontab').order("id desc").field(self.field).select()
        if type(cront) == str:
            public.M('crontab').execute("ALTER TABLE 'crontab' ADD 'status' INTEGER DEFAULT 1",())
            public.M('crontab').execute("ALTER TABLE 'crontab' ADD 'save' INTEGER DEFAULT 3",())
            public.M('crontab').execute("ALTER TABLE 'crontab' ADD 'backupTo' TEXT DEFAULT off",())
            public.M('crontab').execute("ALTER TABLE 'crontab' ADD 'sName' TEXT",())
            public.M('crontab').execute("ALTER TABLE 'crontab' ADD 'sBody' TEXT",())
            public.M('crontab').execute("ALTER TABLE 'crontab' ADD 'sType' TEXT",())
            public.M('crontab').execute("ALTER TABLE 'crontab' ADD 'urladdress' TEXT",())
            cront = public.M('crontab').order("id desc").field(self.field).select()
        
        data=[]
        for i in range(len(cront)):
            tmp=cront[i]
            if cront[i]['type']=="day":
                tmp['type']=public.getMsg('CRONTAB_TODAY')
                tmp['cycle']= public.getMsg('CRONTAB_TODAY_CYCLE',(str(cront[i]['where_hour']),str(cront[i]['where_minute'])))
            elif cront[i]['type']=="day-n":
                tmp['type']=public.getMsg('CRONTAB_N_TODAY',(str(cront[i]['where1']),))
                tmp['cycle']=public.getMsg('CRONTAB_N_TODAY_CYCLE',(str(cront[i]['where1']),str(cront[i]['where_hour']),str(cront[i]['where_minute'])))
            elif cront[i]['type']=="hour":
                tmp['type']=public.getMsg('CRONTAB_HOUR')
                tmp['cycle']=public.getMsg('CRONTAB_HOUR_CYCLE',(str(cront[i]['where_minute']),))
            elif cront[i]['type']=="hour-n":
                tmp['type']=public.getMsg('CRONTAB_N_HOUR',(str(cront[i]['where1']),))
                tmp['cycle']=public.getMsg('CRONTAB_N_HOUR_CYCLE',(str(cront[i]['where1']),str(cront[i]['where_minute'])))
            elif cront[i]['type']=="minute-n":
                tmp['type']=public.getMsg('CRONTAB_N_MINUTE',(str(cront[i]['where1']),))
                tmp['cycle']=public.getMsg('CRONTAB_N_MINUTE_CYCLE',(str(cront[i]['where1']),))
            elif cront[i]['type']=="week":
                tmp['type']=public.getMsg('CRONTAB_WEEK')
                if not cront[i]['where1']: cront[i]['where1'] = '0'
                tmp['cycle']= public.getMsg('CRONTAB_WEEK_CYCLE',(self.toWeek(int(cront[i]['where1'])),str(cront[i]['where_hour']),str(cront[i]['where_minute'])))
            elif cront[i]['type']=="month":
                tmp['type']=public.getMsg('CRONTAB_MONTH')
                tmp['cycle']=public.getMsg('CRONTAB_MONTH_CYCLE',(str(cront[i]['where1']),str(cront[i]['where_hour']),str(cront[i]['where_minute'])))
            data.append(tmp)
        return data


    #清理日志
    def __clean_log(self):
        try:
            log_file = '/www/server/cron'
            if not os.path.exists(log_file): return False
            for f in os.listdir(log_file):
                if f[-4:] != '.log': continue
                filename = log_file + '/' + f
                if os.path.getsize(filename) < 1048576 /2: continue
                tmp = public.GetNumLines(filename,100)
                public.writeFile(filename,tmp)
        except:
            pass

    
    #转换大写星期
    def toWeek(self,num):
        wheres={
                0   :   public.getMsg('CRONTAB_SUNDAY'),
                1   :   public.getMsg('CRONTAB_MONDAY'),
                2   :   public.getMsg('CRONTAB_TUESDAY'),
                3   :   public.getMsg('CRONTAB_WEDNESDAY'),
                4   :   public.getMsg('CRONTAB_THURSDAY'),
                5   :   public.getMsg('CRONTAB_FRIDAY'),
                6   :   public.getMsg('CRONTAB_SATURDAY')
                }
        try:
            return wheres[num]
        except:
            return ''
    
    #检查环境
    def checkBackup(self):
        if cache.get('check_backup'): return None
        #检查备份脚本是否存在
        filePath=public.GetConfigValue('setup_path')+'/panel/script/backup'
        if not os.path.exists(filePath):
            public.downloadFile(public.GetConfigValue('home') + '/linux/backup.sh',filePath)
        #检查日志切割脚本是否存在
        filePath=public.GetConfigValue('setup_path')+'/panel/script/logsBackup'
        if not os.path.exists(filePath):
            public.downloadFile(public.GetConfigValue('home') + '/linux/logsBackup.py',filePath)
        #检查计划任务服务状态
        
        import system
        sm = system.system()
        if os.path.exists('/etc/init.d/crond'): 
            if not public.process_exists('crond'): public.ExecShell('/etc/init.d/crond start')
        elif os.path.exists('/etc/init.d/cron'):
            if not public.process_exists('cron'): public.ExecShell('/etc/init.d/cron start')
        elif os.path.exists('/usr/lib/systemd/system/crond.service'):
            if not public.process_exists('crond'): public.ExecShell('systemctl start crond')
        cache.set('check_backup',True,3600)
    

    #设置计划任务状态
    def set_cron_status(self,get):
        id = get['id']
        cronInfo = public.M('crontab').where('id=?',(id,)).field(self.field).find()
        status = 1
        if cronInfo['status'] == status:
            status = 0
            self.remove_for_crond(cronInfo['echo'])
        else:
            cronInfo['status'] = 1
            self.sync_to_crond(cronInfo)
        
        public.M('crontab').where('id=?',(id,)).setField('status',status)
        public.WriteLog('计划任务','修改计划任务['+cronInfo['name']+']状态为['+str(status)+']')
        return public.returnMsg(True,'设置成功')

    #修改计划任务
    def modify_crond(self,get):
        if len(get['name'])<1:
             return public.returnMsg(False,'CRONTAB_TASKNAME_EMPTY')
        id = get['id']
        cuonConfig,get,name = self.GetCrondCycle(get)
        cronInfo = public.M('crontab').where('id=?',(id,)).field(self.field).find()
        if not get['where1']: get['where1'] = get['week']
        del(cronInfo['id'])
        del(cronInfo['addtime'])
        cronInfo['name'] = get['name']
        cronInfo['type'] = get['type']
        cronInfo['where1'] = get['where1']
        cronInfo['where_hour'] = get['hour']
        cronInfo['where_minute'] = get['minute']
        cronInfo['save'] = get['save']
        cronInfo['backupTo'] = get['backupTo']
        cronInfo['sBody'] = get['sBody']
        cronInfo['urladdress'] = get['urladdress']
        public.M('crontab').where('id=?',(id,)).save('name,type,where1,where_hour,where_minute,save,backupTo,sBody,urladdress',
                                                     (get['name'],get['type'],get['where1'],get['hour'],get['minute'],get['save'],get['backupTo'],get['sBody'],get['urladdress']))
        
        self.remove_for_crond(cronInfo['echo'])
        self.sync_to_crond(cronInfo)
        public.WriteLog('计划任务','修改计划任务['+cronInfo['name']+']成功')
        return public.returnMsg(True,'修改成功')


    #获取指定任务数据
    def get_crond_find(self,get):
        id = int(get.id)
        data = public.M('crontab').where('id=?',(id,)).field(self.field).find()
        return data



    #同步到crond
    def sync_to_crond(self,cronInfo):
        if 'status' in cronInfo:
            if cronInfo['status'] == 0: return False
        if 'where_hour' in cronInfo:
            cronInfo['hour'] = cronInfo['where_hour']
            cronInfo['minute'] = cronInfo['where_minute']
            cronInfo['week'] = cronInfo['where1']
        cuonConfig,cronInfo,name = self.GetCrondCycle(cronInfo)
        cronPath=public.GetConfigValue('setup_path')+'/cron'
        cronName=self.GetShell(cronInfo)
        if type(cronName) == dict: return cronName
        cuonConfig += ' ' + cronPath+'/'+cronName+' >> '+ cronPath+'/'+cronName+'.log 2>&1'
        wRes = self.WriteShell(cuonConfig)
        if type(wRes) != bool: return False
        self.CrondReload()
        
    #添加计划任务
    def AddCrontab(self,get):
        if len(get['name'])<1:
             return public.returnMsg(False,'CRONTAB_TASKNAME_EMPTY')
        cuonConfig,get,name = self.GetCrondCycle(get)
        cronPath=public.GetConfigValue('setup_path')+'/cron'
        cronName=self.GetShell(get)
        if type(cronName) == dict: return cronName
        cuonConfig += ' ' + cronPath+'/'+cronName+' >> '+ cronPath+'/'+cronName+'.log 2>&1'

        wRes = self.WriteShell(cuonConfig)
        if type(wRes) != bool: return wRes
        self.CrondReload()
        addData=public.M('crontab').add(
            'name,type,where1,where_hour,where_minute,echo,addtime,status,save,backupTo,sType,sName,sBody,urladdress',
            (get['name'],get['type'],get['where1'],get['hour'],get['minute'],cronName,time.strftime('%Y-%m-%d %X',time.localtime()),1,get['save'],get['backupTo'],get['sType'],get['sName'],get['sBody'],get['urladdress'])
            )
        if addData>0:
            result = public.returnMsg(True,'ADD_SUCCESS')
            result['id'] = addData
            return result
        return public.returnMsg(False,'ADD_ERROR')
    
    #构造周期
    def GetCrondCycle(self,params):
        cuonConfig=""
        name = ""
        if params['type']=="day":
            cuonConfig = self.GetDay(params)
            name = public.getMsg('CRONTAB_TODAY')
        elif params['type']=="day-n":
            cuonConfig = self.GetDay_N(params)
            name = public.getMsg('CRONTAB_N_TODAY',(params['where1'],))
        elif params['type']=="hour":
            cuonConfig = self.GetHour(params)
            name = public.getMsg('CRONTAB_HOUR')
        elif params['type']=="hour-n":
            cuonConfig = self.GetHour_N(params)
            name = public.getMsg('CRONTAB_HOUR')
        elif params['type']=="minute-n":
            cuonConfig = self.Minute_N(params)
        elif params['type']=="week":
            params['where1']=params['week']
            cuonConfig = self.Week(params)
        elif params['type']=="month":
            cuonConfig = self.Month(params)
        return cuonConfig,params,name

    #取任务构造Day
    def GetDay(self,param):
        cuonConfig ="{0} {1} * * * ".format(param['minute'],param['hour'])
        return cuonConfig
    #取任务构造Day_n
    def GetDay_N(self,param):
        cuonConfig ="{0} {1} */{2} * * ".format(param['minute'],param['hour'],param['where1'])
        return cuonConfig
    
    #取任务构造Hour
    def GetHour(self,param):
        cuonConfig ="{0} * * * * ".format(param['minute'])
        return cuonConfig
    
    #取任务构造Hour-N
    def GetHour_N(self,param):
        cuonConfig ="{0} */{1} * * * ".format(param['minute'],param['where1'])
        return cuonConfig
    
    #取任务构造Minute-N
    def Minute_N(self,param):
        cuonConfig ="*/{0} * * * * ".format(param['where1'])
        return cuonConfig
    
    #取任务构造week
    def Week(self,param):
        cuonConfig ="{0} {1} * * {2}".format(param['minute'],param['hour'],param['week'])
        return cuonConfig
    
    #取任务构造Month
    def Month(self,param):
        cuonConfig = "{0} {1} {2} * * ".format(param['minute'],param['hour'],param['where1'])
        return cuonConfig
    
    #取数据列表
    def GetDataList(self,get):
        data = {}
        data['data'] = public.M(get['type']).field('name,ps').select()
        data['orderOpt'] = []
        import json
        tmp = public.readFile('data/libList.conf')
        libs = json.loads(tmp)
        for lib in libs:
            if not 'opt' in lib: continue
            filename = 'plugin/{}'.format(lib['opt'])
            if not os.path.exists(filename): continue
            tmp = {}
            tmp['name'] = lib['name']
            tmp['value']= lib['opt']
            data['orderOpt'].append(tmp)
        return data
    
    #取任务日志
    def GetLogs(self,get):
        id = get['id']
        echo = public.M('crontab').where("id=?",(id,)).field('echo').find()
        logFile = public.GetConfigValue('setup_path')+'/cron/'+echo['echo']+'.log'
        if not os.path.exists(logFile):return public.returnMsg(False, 'CRONTAB_TASKLOG_EMPTY')
        log = public.GetNumLines(logFile,2000)
        return public.returnMsg(True, log)
    
    #清理任务日志
    def DelLogs(self,get):
        try:
            id = get['id']
            echo = public.M('crontab').where("id=?",(id,)).getField('echo')
            logFile = public.GetConfigValue('setup_path')+'/cron/'+echo+'.log'
            os.remove(logFile)
            return public.returnMsg(True, 'CRONTAB_TASKLOG_CLOSE')
        except:
            return public.returnMsg(False, 'CRONTAB_TASKLOG_CLOSE_ERR')
    
    #删除计划任务
    def DelCrontab(self,get):
        try:
            id = get['id']
            find = public.M('crontab').where("id=?",(id,)).field('name,echo').find()
            if not self.remove_for_crond(find['echo']): return public.returnMsg(False,'无法写入文件，请检查是否开启了系统加固功能!')
            cronPath = public.GetConfigValue('setup_path') + '/cron'
            sfile = cronPath + '/' + find['echo']
            if os.path.exists(sfile): os.remove(sfile)
            sfile = cronPath + '/' + find['echo'] + '.log'
            if os.path.exists(sfile): os.remove(sfile)
            
            public.M('crontab').where("id=?",(id,)).delete()
            public.WriteLog('TYPE_CRON', 'CRONTAB_DEL',(find['name'],))
            return public.returnMsg(True, 'DEL_SUCCESS')
        except:
            return public.returnMsg(False, 'DEL_ERROR')

    #从crond删除
    def remove_for_crond(self,echo):
        file = self.get_cron_file()
        conf=public.readFile(file)
        if conf.find(str(echo)) == -1: return True
        rep = ".+" + str(echo) + ".+\n"
        conf = re.sub(rep, "", conf)
        try:
            if not public.writeFile(file,conf): return False
        except:
            return False
        self.CrondReload()
        return True
    
    #取执行脚本
    def GetShell(self,param):
        #try:
        type=param['sType']
        if type=='toFile':
            shell=param.sFile
        else :
            head="#!/bin/bash\nPATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin\nexport PATH\n"
            log='-access_log'
            python_bin = public.get_python_bin()
            if public.get_webserver()=='nginx':
                log='.log'
            if type in ['site','path'] and param['sBody'] != 'undefined' and len(param['sBody']) > 1:
                exports = param['sBody'].replace("\r\n","\n").replace("\n",",")
                head += "BT_EXCLUDE=\"" + exports.strip() + "\"\nexport BT_EXCLUDE\n"
            wheres={
                    'path': head + python_bin +" " + public.GetConfigValue('setup_path')+"/panel/script/backup.py path "+param['sName']+" "+str(param['save']),
                    'site'  :   head +python_bin+ " " + public.GetConfigValue('setup_path')+"/panel/script/backup.py site "+param['sName']+" "+str(param['save']),
                    'database': head +python_bin+ " " + public.GetConfigValue('setup_path')+"/panel/script/backup.py database "+param['sName']+" "+str(param['save']),
                    'logs'  :   head +python_bin+ " " + public.GetConfigValue('setup_path')+"/panel/script/logsBackup "+param['sName']+" "+str(param['save']),
                    'rememory' : head + "/bin/bash " + public.GetConfigValue('setup_path') + '/panel/script/rememory.sh',
                    'webshell': head +python_bin+ " " + public.GetConfigValue('setup_path') + '/panel/class/webshell_check.py site ' + param['sName'] +' ' +param['urladdress']
                    }
            if param['backupTo'] != 'localhost':
                cfile = public.GetConfigValue('setup_path') + "/panel/plugin/" + param['backupTo'] + "/" + param['backupTo'] + "_main.py"
                if not os.path.exists(cfile): cfile = public.GetConfigValue('setup_path') + "/panel/script/backup_" + param['backupTo'] + ".py"
                wheres={
                    'path': head + python_bin+" " + cfile + " path " + param['sName'] + " " + str(param['save']),
                    'site'  :   head + python_bin+" " + cfile + " site " + param['sName'] + " " + str(param['save']),
                    'database': head + python_bin+" " + cfile + " database " + param['sName'] + " " + str(param['save']),
                    'logs'  :   head + python_bin+" " + public.GetConfigValue('setup_path')+"/panel/script/logsBackup "+param['sName']+" "+str(param['save']),
                    'rememory' : head + "/bin/bash " + public.GetConfigValue('setup_path') + '/panel/script/rememory.sh',
                     'webshell': head + python_bin+" " + public.GetConfigValue('setup_path') + '/panel/class/webshell_check.py site ' + param['sName'] +' ' +param['urladdress']
                    }
                
            try:
                shell=wheres[type]
            except:
                if type == 'toUrl':
                    shell = head + "curl -sS --connect-timeout 10 -m 3600 '" + param['urladdress']+"'"
                else:
                    shell=head+param['sBody'].replace("\r\n","\n")
                    
                shell += '''
echo "----------------------------------------------------------------------------"
endDate=`date +"%Y-%m-%d %H:%M:%S"`
echo "★[$endDate] Successful"
echo "----------------------------------------------------------------------------"
'''
        cronPath=public.GetConfigValue('setup_path')+'/cron'
        if not os.path.exists(cronPath): public.ExecShell('mkdir -p ' + cronPath)
        if not 'echo' in param:
            cronName=public.md5(public.md5(str(time.time()) + '_bt'))
        else:
            cronName = param['echo']
        file = cronPath+'/' + cronName
        public.writeFile(file,self.CheckScript(shell))
        public.ExecShell('chmod 750 ' + file)
        return cronName
        #except Exception as ex:
            #return public.returnMsg(False, 'FILE_WRITE_ERR' + str(ex))
        
    #检查脚本
    def CheckScript(self,shell):
        keys = ['shutdown','init 0','mkfs','passwd','chpasswd','--stdin','mkfs.ext','mke2fs']
        for key in keys:
            shell = shell.replace(key,'[***]')
        return shell
    
    #重载配置
    def CrondReload(self):
        if os.path.exists('/etc/init.d/crond'): 
            public.ExecShell('/etc/init.d/crond reload')
        elif os.path.exists('/etc/init.d/cron'):
            public.ExecShell('service cron restart')
        else:
            public.ExecShell("systemctl reload crond")
        
    #将Shell脚本写到文件
    def WriteShell(self,config):
        u_file = '/var/spool/cron/crontabs/root'
        file = self.get_cron_file()
        if not os.path.exists(file): public.writeFile(file,'')
        conf = public.readFile(file)
        if type(conf)==bool:return public.returnMsg(False,'读取文件失败!')
        conf += config + "\n"
        if public.writeFile(file,conf):
            if not os.path.exists(u_file):
                public.ExecShell("chmod 600 '" + file + "' && chown root.root " + file)
            else:
                public.ExecShell("chmod 600 '" + file + "' && chown root.crontab " + file)
            return True
        return public.returnMsg(False,'文件写入失败,请检查是否开启系统加固功能!')
    
    #立即执行任务
    def StartTask(self,get):
        echo = public.M('crontab').where('id=?',(get.id,)).getField('echo')
        execstr = public.GetConfigValue('setup_path') + '/cron/' + echo
        public.ExecShell('chmod +x ' + execstr)
        public.ExecShell('nohup ' + execstr + ' >> ' + execstr + '.log 2>&1 &')
        return public.returnMsg(True,'CRONTAB_TASK_EXEC')

    #获取计划任务文件位置
    def get_cron_file(self):
        u_path = '/var/spool/cron/crontabs'
        u_file = u_path + '/root'
        c_file = '/var/spool/cron/root'
        cron_path = c_file
        if not os.path.exists(u_path):
            cron_path=c_file
        
        if os.path.exists("/usr/bin/apt-get"):
            cron_path = u_file
        elif os.path.exists('/usr/bin/yum'):
            cron_path = c_file

        if cron_path == u_file:
            if not os.path.exists(u_path): 
                os.makedirs(u_path,472)
                public.ExecShell("chown root:crontab {}".format(u_path))
        return cron_path
        
        
    
        