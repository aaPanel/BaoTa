#!/usr/bin/python
# coding: utf-8
# -----------------------------
# 宝塔Linux面板 /垃圾清理
# Author: 1249648969@qq.com
# -----------------------------
# date 2018-10-25
import sys, os
if sys.version_info[0] == 2:
    reload(sys)
    sys.setdefaultencoding('utf-8')
os.chdir('/www/server/panel')
sys.path.append("class/")
import public,time,json,shutil


class clear_main:
    __setupPath = '/www/server/panel/plugin/clear'
    #字节单位转换
    def ToSize(self,size):
            ds = ['b','KB','MB','GB','TB']
            for d in ds:
                if size < 1024: return str(size)+d
                size = size / 1024
            return '0b';
    
    # 转换为字节
    def AnySize(self,size):
        size=str(size)
        d=size[-1]
        try:
            count=float(size[0:-1])
        except:
            count=0
            return size
        ds = ['b','K','M','G','T']
        if d in ds:
            if d=='b':
                return int(count)
            elif d=='K':
                count = count * 1024
                return int(count)
            elif d=='M':
                count = count * 1024 * 1024
                return int(count)
            elif d=='G':
                count = count * 1024 * 1024 * 1024
                return int(count)          
            elif d=='T':
                count = count * 1024 * 1024*1024 *1024
                return int(count) 
            else: 
                return int(count)
        else:   
            return '0b'
        
    #返回系统登录日志
    def ReturnLoginLog(self):    
        # 就audit 日志 和mess 日志
        rpath = '/var/log'
        total = count = 0
        con = ['/var/log/audit']
        ret=[]
        if os.path.exists(rpath):
            for d in os.listdir(rpath):
                filename = rpath + '/' + d
                if os.path.isdir(filename):
                    if filename in con:
                        for i in os.listdir(filename):
                            ret_size={}
                            name=filename+'/'+i
                            size=os.path.getsize(name)
                            ret_size['size']=self.ToSize(size)
                            ret_size['filename']=i
                            ret_size['name']=filename+'/'+i
                            ret_size['count_size']=size
                            ret.append(ret_size)
                        else:
                            ret_size={}
                            size=os.path.getsize(filename)
                            if size>=100:
                                ret_size['size']=self.ToSize(size)
                                ret_size['size']=self.ToSize(size)
                                ret_size['count_size']=size
                                ret_size['name']=filename+'/'+i#
                                ret.append=(ret_size)

        return ret

    #面板遗留文件
    def Returnpanel(self):
        clearPath = [
                    {'path':'/www/server/panel','find':'testDisk_'},
                    #{'path':'/www/wwwlogs','find':'log'},
                    {'path':'/tmp','find':'panelBoot.pl'},
                    {'path':'/www/server/panel/install','find':'.rpm'},
                    {'path':'/www/server/panel/install','find':'.zip'},
                    {'path':'/www/server/panel/install','find':'.gz'}
                    ]
        
        total = count = 0;
        ret=[]
        for c in clearPath:
            if os.path.exists(c['path']):
                for d in os.listdir(c['path']):
                    if d.find(c['find']) == -1: continue;
                    filename = c['path'] + '/' + d;
                    fsize = os.path.getsize(filename);
                    ret_size={}
                    ret_size['filename']=filename
                    ret_size['size']=self.ToSize(fsize)
                    ret_size['count_size']=fsize
                    ret.append(ret_size)
        

        return ret
    
    # 返回网站的log文件
    def ReturnWwwLog(self):
        clearPath = [{'path':'/www/wwwlogs','find':'log'},
                    {'path':'/www/wwwlogs/btwaf','find':'log'}
        ]  
        total = count = 0;
        ret=[]
        for c in clearPath:
            if os.path.exists(c['path']):
                for d in os.listdir(c['path']):
                    if d.find(c['find']) == -1: continue
                    filename = c['path'] + '/' + d;
                    fsize = os.path.getsize(filename)
                    if fsize<1024:continue
                    ret_size={}
                    ret_size['name']=filename
                    ret_size['filename']=os.path.basename(filename)
                    ret_size['count_size']=fsize
                    ret_size['size']=self.ToSize(fsize)
                    ret.append(ret_size)
        return ret

    # 返回数据库日志
    def ReturnMysqlLog(self):
        try:
            mysql_dir=str(public.ExecShell("cat /etc/my.cnf|grep datadir |awk -F \'=\' \'{print $2}\'")[0].strip())
        except:
            mysql_dir='/www/server/data'
        if os.path.exists(mysql_dir):
            clearPath = [{'path':mysql_dir,'find':'mysql-bin.00'}]
            total = count = 0;
            ret=[]
            for c in clearPath:
                for d in os.listdir(c['path']):
                    if d.find(c['find']) == -1:continue
                    filename = c['path'] + '/' + d;
                    fsize = os.path.getsize(filename)
                    if fsize<=102:continue
                    ret_size={}
                    ret_size['name']=filename
                    ret_size['filename']=os.path.basename(filename)
                    ret_size['count_size']=fsize
                    ret_size['size']=self.ToSize(fsize)
                    ret.append(ret_size)
            if len(ret)<=1:
                ret=[]
                return ret
            public.ExecShell('/etc/init.d/mysqld reload')
            return ret
    
    # 回收站
    def RetuenRecycle_bin(self):
        clearPath = [{'path':'/www/Recycle_bin','find':'_bt_'}]
        total = count = 0;
        ret={'Refile':[],'Redir':[]}
        ret2=[]
        ret3=[]
        for c in clearPath:
            if os.path.exists(c['path']):
                for d in os.listdir(c['path']):
                        filename= c['path'] + '/' + d
                        if os.path.isdir(filename):
                            size=public.ExecShell('du -sh  %s'%filename)[0].split()[0]
                            ret_size={}
                            ret_size['dir']='dir'
                            ret_size['size']=size
                            ret_size['count_size']=self.AnySize(size)
                            ret_size['name']= c['path'] + '/' + d
                            filename=d.split('_t_')[0].replace('_bt_','/')
                            ret_size['filename']=filename
                            ret2.append(ret_size)
                        else:    
                            if d.find(c['find']) == -1:continue
                            filename = c['path'] + '/' + d;
                            fsize = os.path.getsize(filename)
                            #if fsize<=1:continue
                            ret_size={}
                            ret_size['name']=filename
                            filename=os.path.basename(filename)
                            ret_size['time']=filename.split('_t_')[1]
                            filename=filename.split('_t_')[0].replace('_bt_','/')
                            ret_size['filename']=filename
                            ret_size['count_size']=fsize
                            ret_size['size']=self.ToSize(fsize)
                            ret3.append(ret_size)
        ret['Refile']=ret3
        ret['Redir']=ret2  
        return ret

    
    #返回php_session文件
    def ReturnSession(self):
        spath = '/tmp'
        total = count = 0
        import shutil
        ret={}
        if os.path.exists(spath):
            for d in os.listdir(spath):
                if d.find('sess_') == -1: continue
                filename = spath + '/' + d
                fsize = os.path.getsize(filename)
                total += fsize       
                count += 1;
                ret['php_session']=({'count':count,'size':self.ToSize(total),'count_size':total})

        return ret

     #清理php_session文件
    def ClearSession(self,data):
        if data:       
            spath = '/tmp'
            total = count = 0;
            import shutil
            if os.path.exists(spath):
                for d in os.listdir(spath):
                    if d.find('sess_') == -1: continue;
                    filename = spath + '/' + d;
                    fsize = os.path.getsize(filename);
                    total += fsize
                    if os.path.isdir(filename):
                        shutil.rmtree(filename)
                    else:
                        os.remove(filename)
                    count += 1;
                return True
            else:
                return False

     #返回邮件文件
    def ReturnMailSize(self):
        rpath = '/var/spool';
        total = count = 0;
        import shutil
        con = ['cron', 'anacron', 'mail'];
        ret=[]
        if os.path.exists(rpath):
            for d in os.listdir(rpath):
                if d in con: continue;
                dpath = rpath + '/' + d
                time.sleep(0.2);
                num = size = 0;
                for n in os.listdir(dpath):
                    ret_size={}
                    if n=='':continue
                    filename = dpath + '/' + n
                    fsize = os.path.getsize(filename);
                    ret_size['filename']=filename
                   # ret_size['name']=filename
                    ret_size['size']=self.ToSize(fsize)
                    ret_size['count_size']=fsize
                    ret.append(ret_size)
        return ret

    # 网站监控报表
    def Total_Log(self):
        clearPath = [{'path':'/www/server/total/logs','find':'_bt_'}]
        total = count = 0;
        ret=[]
        for c in clearPath:
            if os.path.exists(c['path']):
                for d in os.listdir(c['path']):
                        filename= c['path'] + '/' + d
                        if os.path.isdir(filename):
                            size=public.ExecShell('du -sh  %s'%filename)[0].split()[0]
                            ret_size={}
                            ret_size['dir']='dir'
                            ret_size['size']=size
                            ret_size['count_size']=self.AnySize(size)
                            ret_size['name']= c['path'] + '/' + d
                            filename=d.split('_t_')[0].replace('_bt_','/')
                            ret_size['filename']=filename
                            ret.append(ret_size)
        return ret

    # 返回日志总和
    def RetuenLog(self, get):
        ret={}
        ret['system_log']=self.ReturnLoginLog()
        ret['panel_log']=self.Returnpanel()
        ret['www_log']=self.ReturnWwwLog()
        ret['mysql_log']=self.ReturnMysqlLog()
        ret['Recycle']=self.RetuenRecycle_bin()
        ret['mail_log']=self.ReturnMailSize()
        ret['php_session']=self.ReturnSession()
        ret['total_log']=self.Total_Log()
        return ret

    # 清理功能
    def remove_file(self, get):
        ret=[]
        #data=data
        # 记录用户的选择的文件
        data=json.loads(get.data)
        self.log_write(data)
        if 'system_log' in data:
            system_log=data['system_log']
            if len(system_log)!=0:
                for i in system_log:
                    # 统计
                    count_size=int(i['count_size'])
                    ret.append(count_size)
                    # 清理系统日志
                    os.remove(i['name'])
                # 进度条
                time.sleep(0.1)
                listFile = self.__setupPath + '/relist.json'
                aTask = {}
                aTask['name'] = '系统日志文件清理完成'
                aTask['count'] =10
                aTask['done'] = 10
                public.writeFile(listFile, json.dumps(aTask))

        # 面板日志
        if 'panel_log' in data:
            if len(data["panel_log"])!=0:
                for i in data['panel_log']:
                    #统计总量
                    count_size=int(i['count_size'])
                    ret.append(count_size)
                    os.remove(i['filename'])
                # 进度
                listFile = self.__setupPath + '/relist.json'
                aTask = {}
                time.sleep(0.1)
                aTask['name'] = '面板遗留文件清理完成'
                aTask['count'] =20
                aTask['done'] = 20
                public.writeFile(listFile, json.dumps(aTask))

        # 网站日志
        if 'www_log' in data:
            if len(data["www_log"])!=0:
                for i in data['www_log']:
                    #总大小
                    count_size=int(i['count_size'])
                    ret.append(count_size)
                    os.remove(i['name'])
                    print(i['name'])
                    os.system('sleep 1 && /etc/init.d/bt reload > /dev/null &')
                # 进度
                time.sleep(0.1)
                listFile = self.__setupPath + '/relist.json'
                aTask = {}
                aTask['name'] = '网站log文件清理完毕'
                aTask['count'] =30
                aTask['done'] = 30
                public.writeFile(listFile, json.dumps(aTask))

        if 'mysql_log' in data:
            system_log=data['mysql_log']
            if len(system_log)!=0:
                for i in system_log:
                    count_size=int(i['count_size'])
                    ret.append(count_size)         
                    # 清理mysql日志
                    os.remove(i['name'])  
                    print(i['name'])   
                # 进度
                time.sleep(0.1)
                listFile = self.__setupPath + '/relist.json'
                aTask = {}
                aTask['name'] = '数据库日志文件清理完毕'
                aTask['count'] =40
                aTask['done'] = 40
                public.writeFile(listFile, json.dumps(aTask)) 

        # 回收站清理
        if 'Recycle' in data:
            Recycle=data['Recycle']
            if  len(Recycle['Refile'])!=0:
                for i in Recycle['Refile']:
                    print(i['name'])
                    count_size=int(i['count_size'])
                    ret.append(count_size)
                    try:
                        os.remove(i['name'])
                        print(i['name'])
                    except:
                        os.system('rm -rf %s'%i['name'])
            if len(Recycle['Redir'])!=0:
                for i in Recycle['Redir']:
                    print(i['name'])
                    count_size=int(i['count_size'])
                    ret.append(count_size)
                    import shutil
                    try:
                        shutil.rmtree(i['name'])
                        print(i['name'])
                    except:
                        os.system('rm -rf %s'%i['name'])

            # 进度
            time.sleep(0.1) 
            listFile = self.__setupPath + '/relist.json'
            aTask = {}
            aTask['name'] = '回收站文件清理完毕'
            aTask['count'] =50
            aTask['done'] = 50
            public.writeFile(listFile, json.dumps(aTask))   

        # mail 日志
        if 'mail_log' in data:
            if len(data["mail_log"])!=0:
                for i in data['mail_log']:
                    count_size=int(i['count_size'])
                    ret.append(count_size)
                    os.system('rm -rf %s'%i['filename'])
                    #import shutil
                    #shutil.rmtree(i['filename'])                                  
                    print(i['filename'])

            # 进度
            time.sleep(0.1)
            listFile = self.__setupPath + '/relist.json'
            aTask = {}
            aTask['name'] = 'mail文件清理完毕'
            aTask['count'] =60
            aTask['done'] = 60
            public.writeFile(listFile, json.dumps(aTask))

        if 'php_session' in data:
            php_session=data['php_session']
            if 'php_session' in php_session:
                if int(php_session['php_session']['count'])>1:
                    # 统计
                    count_size=int(php_session['php_session']['count_size'])
                    ret.append(count_size)
                    # 清理php_session
                    self.ClearSession(php_session)
            # 进度
            time.sleep(0.1)  
            listFile = self.__setupPath + '/relist.json'
            aTask = {}
            aTask['name'] = 'session文件检查完毕'
            aTask['count'] =70
            aTask['done'] = 70
            public.writeFile(listFile, json.dumps(aTask))

        # 网站统计报表 
        if 'total_log' in data:
            if len(data["total_log"])!=0:
                for i in data['total_log']:
                    count_size=int(i['count_size'])
                    ret.append(count_size)
                    if os.path.isdir(i['name']):
                        shutil.rmtree(i['name'])
                        print(i['name'])
            # 进度
            time.sleep(0.1)
            listFile = self.__setupPath + '/relist.json'
            aTask = {}
            aTask['name'] = '网站监控报表检查完毕'
            aTask['count'] =100
            aTask['done'] = 100
            public.writeFile(listFile, json.dumps(aTask))    
        return self.ToSize(sum(ret))

    # 设置当前进度
    def SetSpeed(self, name,tcount,tdone):
        aTask = {}
        aTask['name'] = name
        aTask['count'] =tcount
        aTask['done'] = tdone
        actionTask = self.__setupPath + '/relist.json'
        public.writeFile(actionTask, json.dumps(aTask))
        return True

    # 获取进度条
    def GetToStatus(self, get):
        actionTask = self.__setupPath + '/relist.json'
        if not os.path.exists(actionTask): return public.returnMsg(False, '查询失败!')
        aTask = json.loads(public.readFile(actionTask))
        if aTask['name'] == '网站监控报表检查完毕':
            return 100
        else:
            return aTask['count']

    # 清理的日志
    def log_write(self, data):
        actionTask = self.__setupPath + '/log.json'
        public.writeFile(actionTask, json.dumps(data))
        return True

    # 读取已经清理的数据
    def get_log(self, get):
        actionTask = self.__setupPath + '/log.json'
        if not os.path.exists(actionTask): return public.returnMsg(False, '查询失败!')
        aTask = json.loads(public.readFile(actionTask))
        return aTask


#aa=clear_main()
#xx=aa.RetuenLog()
#print xx
#print(aa.remove_file(data=xx))