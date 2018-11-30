#coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板 x3
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2019 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: 黄文良 <287962566@qq.com>
# +-------------------------------------------------------------------
import sys
sys.path.append('/www/server/panel/class')
import public,re,json,os
class mongodb_main:
    __mongodb_path = '/www/server/mongodb';
    
    #获取数据库列表
    def get_databases(self,get):
        config = self.get_options(get)
        tmp = public.ExecShell('mongo admin --port '+config['port']+' --eval \'printjson(db.runCommand({"listDatabases":1}))\'|grep -v MongoDB|grep -v connecting')[0]
        return json.loads(tmp)
    
    #获取服务状态
    def get_service_status(self,get):
        pidFile = self.__mongodb_path + '/log/configsvr.pid'
        pid = int(public.readFile(pidFile))
        import psutil
        if pid in psutil.pids(): return True;
        return False;
    
    #取负载状态
    def get_status(self,get):
        tmp = public.ExecShell('mongo admin --eval "db.serverStatus()"|grep -v MongoDB|grep -v connecting')[0]
        tmp = tmp.strip().replace("NumberLong(","").replace(")}","}").replace("),",",").replace("ISODate(","").replace("\n","").replace("\t","").replace(")","")
        return json.loads(tmp)
    
    #创建数据库
    def create_database(self,get):
        public.ExecShell('mongo '+get.dbname+' --eval \'db.'+get.dbname+'.insert({"name":"'+get.dbname+'"})\'');
        public.ExecShell('mongo '+get.dbname+' --eval \'db.'+get.dbname+'.remove({"name":"'+get.dbname+'"})\'');
        return public.returnMsg(True,'创建成功!');
    
    #删除数据库
    def remove_database(self,get):
        sysdb = ['admin','config','local']
        if get.dbname in sysdb: return public.returnMsg(False,'系统数据库,不可删除!');
        public.ExecShell('mongo '+get.dbname+' --eval \'db.dropDatabase()\'');
        return public.returnMsg(True,'删除成功!');
    
    #获取配置文件
    def get_config(self,get):
        filename = self.__mongodb_path + '/config.conf'
        if os.path.exists(filename):
            return public.readFile(filename);
        return ""
    
    #保存配置文件
    def save_config(self,get):
        public.writeFile(self.__mongodb_path + '/config.conf',get.config_body)
        get.status = '2';
        self.service_admin(get);
        return public.returnMsg(True,'保存成功!')
    
    #获取日志文件
    def get_logs(self,get):
        filename = self.__mongodb_path + '/log/config.log'
        if os.path.exists(filename):
            return public.GetNumLines(self.__mongodb_path + '/log/config.log',1000);
        return "当前日志为空..."
    
    #获取配置项
    def get_options(self,get):
        options = ['port','bindIp','path','dbPath','pidFilePath']
        data = {}
        conf = self.get_config(None)
        for opt in options:
            tmp = re.findall(opt + ":\s+(.+)",conf)
            if not tmp: continue;
            data[opt] = tmp[0]
        return data
    
    #保存配置项
    def save_options(self,get):
        options = ['port','bindIp','path','dbPath','pidFilePath']
        conf = self.get_config(None)
        for opt in options:
            conf = re.sub(opt + ":\s+(.+)",opt + ": " + get[opt],conf);
        filename = self.__mongodb_path + '/config.conf';
        
        public.writeFile(filename,conf);
        get.status = '2';
        self.service_admin(get);
        return public.returnMsg(True,'配置已保存!')
    
    #服务管理
    def service_admin(self,get):
        statusOption = {"0":"stop","1":"start","2":"restart"}
        statusString = statusOption[get.status]
        public.ExecShell('/etc/init.d/mongodb ' + statusString)
        return public.returnMsg(True,'操作成功!');
    
    
    