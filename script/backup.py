#!/usr/bin/python
#coding: utf-8
#-----------------------------
# 宝塔Linux面板网站备份工具
#-----------------------------

import sys,os
os.chdir('/www/server/panel')
sys.path.append("class/")
if sys.version_info[0] == 2: 
    reload(sys)
    sys.setdefaultencoding('utf-8')
import public,db,time
import panelBackup

class backupTools(panelBackup.backup):
    def backupSite(self,name,count):
        self.backup_site(name,save=count)
    
    def backupDatabase(self,name,count):
        self.backup_database(name,save=count)
    
    #备份指定目录
    def backupPath(self,path,count):
        self.backup_path(path,save=count)
        
    
    def backupSiteAll(self,save):
        self.backup_site_all(save)
        

    def backupDatabaseAll(self,save):
        self.backup_database_all(save)

def get_function_args(func):
    import sys
    if sys.version_info[0] == 3:
        import inspect
        return inspect.getfullargspec(func).args
    else:
        return func.__code__.co_varnames

if __name__ == "__main__":
    cls_args = get_function_args(backupTools.__init__)
    if "cron_info" in cls_args and len(sys.argv) == 5:
        cron_name = sys.argv[4]
        cron_info = {
            "echo": cron_name
        }
        backup = backupTools(cron_info=cron_info)
    else:
        backup = backupTools()
        
    type = sys.argv[1]
    if type == 'site':
        if sys.argv[2] == 'ALL':
             backup.backupSiteAll(sys.argv[3])
        else:
            backup.backupSite(sys.argv[2], sys.argv[3])
    elif type == 'path':
        backup.backupPath(sys.argv[2],sys.argv[3])
    elif type == 'database':
        if sys.argv[2] == 'ALL':
            backup.backupDatabaseAll(sys.argv[3])
        else:
            backup.backupDatabase(sys.argv[2], sys.argv[3])
    