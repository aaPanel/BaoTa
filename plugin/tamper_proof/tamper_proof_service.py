#coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: 黄文良 <287962566@qq.com>
# +-------------------------------------------------------------------

#+--------------------------------------------------------------------
#|   宝塔防篡改事件
#+--------------------------------------------------------------------
import sys
reload(sys)
sys.setdefaultencoding('utf-8')
sys.path.append('/www/server/panel/class')
import os,datetime,pyinotify,logging,hashlib,public,json,hashlib,shutil,time,pwd

class MyEventHandler(pyinotify.ProcessEvent):
    _PLUGIN_PATH = "/www/server/panel/plugin/tamper_proof"
    __TIMEOUT_LOCK = '/timeout_locks.json'
    __CONFIG = '/config.json'
    _SITES = '/sites.json'
    _SITES_DATA = None
    __CONFIG_DATA = None
    _DONE_FILE = None
        
    def process_IN_CREATE(self, event):
        siteInfo = self.get_SITE_CONFIG(event.pathname)
        print(event.pathname)
        if not self.check_FILE(event,siteInfo,True): return False
        self._DONE_FILE = event.pathname
        if event.dir:
            return False
            #if os.path.exists(event.pathname): os.removedirs(event.pathname)
        else:
            if os.path.exists(event.pathname): os.remove(event.pathname)
        self.write_LOG('create',siteInfo['siteName'],event.pathname)
     
    def process_IN_DELETE(self, event):
        siteInfo = self.get_SITE_CONFIG(event.pathname)
        if not self.check_FILE(event,siteInfo): return False
        if self.renew_FILE(event.pathname,siteInfo):
            self.write_LOG('delete',siteInfo['siteName'],event.pathname)
     
    def process_IN_MODIFY(self, event):
        siteInfo = self.get_SITE_CONFIG(event.pathname)
        if not self.check_FILE(event,siteInfo): return False
        if self.renew_FILE(event.pathname,siteInfo):
            self.write_LOG('modify',siteInfo['siteName'],event.pathname)

    def process_IN_MOVED_TO(self,event):
        siteInfo = self.get_SITE_CONFIG(event.pathname)
        if not self.check_FILE(event,siteInfo): return False
        if hasattr(event,'src_pathname'):
            self.renew_FILE(event.src_pathname,siteInfo)
        else:
            event.src_pathname = "null"
        if not self.renew_FILE(event.pathname,siteInfo): 
            if os.path.exists(event.pathname): 
                self._DONE_FILE = event.pathname
                os.remove(event.pathname)
        self.write_LOG('move',siteInfo['siteName'],event.src_pathname + ' -> ' + event.pathname)
    
    def process_IN_MOVED_FROM(self,event):
        self.process_IN_MOVED_TO(event)

    def check_FILE(self,event,siteInfo,create = False):
        if not siteInfo: return False
        if self._DONE_FILE == event.pathname:
            self._DONE_FILE = None
            return False
        if self.access_FILE(event.pathname,siteInfo): return False
        if not siteInfo['open']: return False
        if not siteInfo: return False
        if self.exclude_PATH(event.pathname): return False
        if event.dir and create: return True
        if not self.protect_EXT(event.pathname): return False
        return True

    def protect_EXT(self,pathname):
        if pathname.find('.') == -1: return False
        extName = pathname.split('.')[-1].lower()
        siteData = self.get_SITE_CONFIG(pathname)
        if siteData:
            if extName in siteData['protectExt']: 
                return True
        return False

    def exclude_PATH(self,pathname):
        if pathname.find('/') == -1: return False
        siteData = self.get_SITE_CONFIG(pathname)
        pathname = pathname.lower()
        dirNames = pathname.split('/')
        if siteData:
            for ePath in siteData['excludePath']:
                if ePath in dirNames: return True
                if pathname.find(ePath) == 0: return True
        return False

    def access_FILE(self,pathname,siteInfo):
        filename = '/www/server/panel/access_file.pl'
        if not os.path.exists(filename): return False
        if pathname != public.readFile(filename): return False
        backupFile = self._PLUGIN_PATH + '/sites/' + siteInfo['siteName'] + '/' + self.get_S_MD5(pathname) + '.bak'
        if self.check_MD5(backupFile,pathname): return False
        self._DONE_FILE = pathname
        shutil.copyfile(pathname,backupFile)
        if os.path.exists(filename): os.remove(filename)
        return True

    def set_ACCRSS(self,filename,mode = 755,user = 'www',gid=None,uid=None,src_filename = None):
        if not os.path.exists(filename): return False
        if src_filename:
            m_stat = self.get_ACCESS(src_filename)
            mode = m_stat[0]
            uid = m_stat[1]
            gid = m_stat[2]

        if gid == None: 
            u_pwd = pwd.getpwnam(user)
            gid = u_pwd.pw_gid
            uid = u_pwd.pw_uid

        os.chown(filename,uid,gid)
        os.chmod(filename,mode)
        return True

    def get_ACCESS(self,filename):
        stat = os.stat(filename)
        return stat.st_mode,stat.st_uid,stat.st_gid

    def check_MD5(self,file1,file2):
        md51 = self.get_MD5(file1)
        md52 = self.get_MD5(file2)
        return (md51 == md52)

    def renew_FILE(self,pathname,siteInfo):
        backupPath = self._PLUGIN_PATH + '/sites/' + siteInfo['siteName'] + '/' + self.get_S_MD5(pathname) + '.bak'
        if not os.path.exists(backupPath): return False
        if self.check_MD5(backupPath,pathname): return False
        if not os.path.exists(os.path.dirname(pathname)): os.makedirs(os.path.dirname(pathname))
        self._DONE_FILE = pathname
        shutil.copyfile(backupPath,pathname)
        self.set_ACCRSS(filename=pathname,src_filename=backupPath)
        return True

    def get_SITE_CONFIG(self,pathname):
        if not self._SITES_DATA: self._SITES_DATA = json.loads(public.readFile(self._PLUGIN_PATH + self._SITES))
        for site in self._SITES_DATA:
            length = len(site['path'])
            if len(pathname) < length: continue
            if site['path'] != pathname[:length]: continue
            if not site['open']:continue
            return site
        return None

    def get_CONFIG(self):
        if self.__CONFIG_DATA: return self.__CONFIG_DATA
        self.__CONFIG_DATA = json.loads(public.readFile(self._PLUGIN_PATH + self.__CONFIG))

    def get_MD5(self,filename):
        if not os.path.isfile(filename): return False;
        my_hash = hashlib.md5()
        f = file(filename,'rb')
        while True:
            b = f.read(8096)
            if not b :
                break
            my_hash.update(b)
        f.close()
        return my_hash.hexdigest();

    def get_S_MD5(self,strings):
        m = hashlib.md5()
        m.update(strings)
        return m.hexdigest()

        
    def list_DIR(self,path,siteInfo):
        backupPath = os.path.join(self._PLUGIN_PATH + '/sites/',siteInfo['siteName'])
        if not os.path.exists(backupPath): os.makedirs(backupPath,600)
        for name in os.listdir(path):
            fileName = os.path.join(path,name)
            if os.path.isdir(fileName):
                if not name.lower() in siteInfo['excludePath']:
                    self.list_DIR(fileName,siteInfo)
                continue
            if not self.get_EXT_NAME(name.lower()) in siteInfo['protectExt']: continue
            if os.path.getsize(fileName) > 5242880: continue

            backupFile = os.path.join(backupPath,self.get_S_MD5(fileName)+'.bak')
            if os.path.exists(backupFile):
                if os.path.getsize(backupFile) == os.path.getsize(fileName): continue
                if self.check_MD5(backupFile,fileName): continue
            shutil.copyfile(fileName,backupFile)
            self.set_ACCRSS(filename=backupFile,src_filename=fileName)

    def get_EXT_NAME(self,fileName):
        return fileName.split('.')[-1]

    def write_LOG(self,eventType,siteName,pathname):
        dateDay = time.strftime("%Y-%m-%d",time.localtime())
        logPath = self._PLUGIN_PATH + '/sites/' + siteName + '/total/' + dateDay
        if not os.path.exists(logPath): os.makedirs(logPath)
        logFile = os.path.join(logPath,'logs.json')
        logVar = [int(time.time()),eventType,pathname]
        fp = open(logFile,'a+')
        fp.write(json.dumps(logVar) + "\n")
        fp.close()
        logFiles = [
                logPath + '/total.json',
                self._PLUGIN_PATH + '/sites/' + siteName + '/total/total.json',
                self._PLUGIN_PATH + '/sites/total.json'
            ]

        for totalLogFile in logFiles:
            if not os.path.exists(totalLogFile):
                totalData = {"total":0,"delete":0,"create":0,"modify":0,"move":0}
            else:
                totalData = json.loads(public.readFile(totalLogFile))

            totalData['total'] += 1
            totalData[eventType] += 1
            public.writeFile(totalLogFile,json.dumps(totalData))
     
def run():
    import time
    s = time.time()
    watchManager = pyinotify.WatchManager()
    event = MyEventHandler()
    mode = pyinotify.IN_CREATE | pyinotify.IN_DELETE | pyinotify.IN_MODIFY | pyinotify.IN_MOVED_TO | pyinotify.IN_MOVED_FROM
    sites = json.loads(public.readFile(event._PLUGIN_PATH + event._SITES))
    logType = u'防篡改程序'
    os.chdir("/www/server/panel")
    for siteInfo in sites:
        if not siteInfo['open']: continue
        event.list_DIR(siteInfo['path'].encode('utf-8'),siteInfo)
        watchManager.add_watch(siteInfo['path'].encode('utf-8'), mode ,auto_add=True, rec=True)
    
    e = time.time() - s
    public.WriteLog(logType,u"网站防篡改服务已成功启动,耗时[%s]秒" % e)
    notifier = pyinotify.Notifier(watchManager, event)
    notifier.loop()


 
if __name__ == '__main__':
    run()
