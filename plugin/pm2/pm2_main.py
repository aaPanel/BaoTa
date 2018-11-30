#!/usr/bin/python
#coding: utf-8
#-----------------------------
# PM2管理插件
#-----------------------------
import sys,os
os.chdir('/www/server/panel');
sys.path.append("class/")
import public,re,json

class pm2_main:
    __SR = '''#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH
export HOME=/root
source /www/server/nvm/nvm.sh && ''';
    __path = '/www/server/panel/plugin/pm2/list/';
    
    #列表
    def List(self,get):
        #try:
        tmp = public.ExecShell(self.__SR + "pm2 list|grep -v 'pm2 show'");
        t2 = tmp[0].replace("│","").replace("└","").replace("─","").replace("┴","").replace("┘","").strip().split("┤")
        if len(t2) == 1: return []
        tmpArr = t2[1].strip();
        if t2[1].find('App name') != -1: tmpArr = t2[2].strip();
        appList = tmpArr.split('\n');
        result = []
        tmp = public.ExecShell('lsof -c node|grep LISTEN');
        plist = tmp[0].split('\n')
        for app in appList:
            if not app: continue;
            tmp2 = app.strip().split();
            appInfo = {}
            appInfo['name'] = tmp2[0];
            appInfo['id'] = tmp2[1];
            appInfo['mode'] = tmp2[3];
            appInfo['pid'] = tmp2[4];
            appInfo['status'] = tmp2[5];
            appInfo['restart'] = tmp2[6];
            appInfo['uptime'] = tmp2[7];
            appInfo['cpu'] = tmp2[8];
            appInfo['mem'] = tmp2[9] + ' ' + tmp2[10];
            appInfo['user'] = tmp2[11];
            appInfo['watching'] = tmp2[12];
            appInfo['port'] = 'OFF';
            appInfo['path'] = 'OFF';
            for p in plist:
                ptmp = p.split();
                if len(ptmp) < 8: continue;
                if ptmp[1] == appInfo['pid']: appInfo['port'] = ptmp[8].split(':')[1].split('->')[0];
                
            if os.path.exists(self.__path + appInfo['name']): appInfo['path'] = public.readFile(self.__path + appInfo['name']);
            result.append(appInfo);
        
        return result;
        #except:
            #return public.returnMsg(False,'请检查pm2是否正常!');
        
    #获取已安装库
    def GetMod(self,get):
        tmp = public.ExecShell(self.__SR + "npm list --depth=0 -global|grep -v '/www/server/nvm'")
        modList = tmp[0].replace("│","").replace("└","").replace("─","").replace("┴","").replace("┘","").strip().split()
        result = []
        for m in modList:
            mod = {}
            tmp = m.split('@');
            if len(tmp) < 2: continue;
            mod['name'] = tmp[0];
            mod['version'] = tmp[1];
            result.append(mod);
        return result;
    
    #安装库
    def InstallMod(self,get):
        os.system(self.__SR + 'npm install ' + get.mname + ' -g');
        return public.returnMsg(True,'安装成功!');
    
    #卸载库
    def UninstallMod(self,get):
        MyNot=['pm2','npm'];
        if get.mname in MyNot: return public.returnMsg(False,'不能卸载['+get.mname+']');
        os.system(self.__SR + 'npm uninstall ' + get.mname + ' -g');
        return public.returnMsg(True,'卸载成功!');
    
    #获取Node版本列表
    def Versions(self,get):
        result = {}
        rep = 'v\d+\.\d+\.\d+';
        tmp = public.ExecShell(self.__SR+'nvm ls-remote|grep -v v0|grep -v iojs');
        result['list'] = re.findall(rep,tmp[0])
        tmp = public.ExecShell(self.__SR + "nvm version");
        result['version'] = tmp[0].strip();
        return result;
    
    #切换Node版本
    def SetNodeVersion(self,get):
        version = get.version.replace('v','');
        estr = '''
export NVM_NODEJS_ORG_MIRROR=http://npm.taobao.org/mirrors/node && nvm install %s
nvm use %s
nvm alias default %s
oldreg=`npm get registry`
npm config set registry http://registry.npm.taobao.org/
npm install pm2 -g
npm config set registry $oldreg 
''' % (version,version,version)
        os.system(self.__SR + estr);
        return public.returnMsg(True,'已切换至['+get.version+']');
    
    #添加
    def Add(self,get):
        #get.pname = get.pname.encode('utf-8');
        runFile = (get.path + '/' + get.run).replace('//','/');
        if not os.path.exists(runFile): return public.returnMsg(False,'指定文件不存在!');
        Nlist = self.List(get);
        for node in Nlist:
            if get.pname == node['name']: return public.returnMsg(False,'指定项目名称已经存在!');
        if os.path.exists(get.path + '/package.json') and not os.path.exists(get.path + '/package-lock.json'): os.system(self.__SR + "cd " + get.path + ' && npm install -s');
        os.system(self.__SR + 'cd '+get.path+' && pm2 start ' + runFile +  ' --name "'+get.pname+'"|grep ' + get.pname);
        public.ExecShell(self.__SR + 'pm2 save && pm2 startup');
        if not os.path.exists(self.__path): os.system('mkdir -p ' + self.__path);
        public.writeFile(self.__path + get.pname,get.path);
        return public.returnMsg(True,'ADD_SUCCESS');
    
    #启动
    def Start(self,get):
        #get.pname = get.pname.encode('utf-8');
        result = public.ExecShell(self.__SR + 'pm2 start "' + get.pname + '"|grep ' + get.pname)[0];
        if result.find('online') != -1: return public.returnMsg(True,'项目['+get.pname+']已启动!');
        return public.returnMsg(False,'项目['+get.pname+']启动失败!');
    
    #停止
    def Stop(self,get):
        #get.pname = get.pname.encode('utf-8');
        result = public.ExecShell(self.__SR + 'pm2 stop "' + get.pname + '"|grep ' + get.pname)[0];
        if result.find('stoped') != -1: return public.returnMsg(True,'项目['+get.pname+']已停止!');
        return public.returnMsg(True,'项目['+get.pname+']停止失败!');
    
    #重启
    def Restart(self,get):
        #get.pname = get.pname.encode('utf-8');
        result = public.ExecShell(self.__SR + 'pm2 restart "' + get.pname + '"')[0];
        if result.find('✓') != -1: return public.returnMsg(True,'项目['+get.pname+']已重启!');
        return public.returnMsg(False,'项目['+get.pname+']重启失败!');
    
    #重载
    def Reload(self,get):
        #get.pname = get.pname.encode('utf-8');
        result = public.ExecShell(self.__SR + 'pm2 reload "' + get.pname + '"')[0];
        if result.find('✓') != -1: return public.returnMsg(True,'项目['+get.pname+']已重载!');
        return public.returnMsg(False,'项目['+get.pname+']重载失败!');
    
    #删除
    def Delete(self,get):
       # get.pname = get.pname.encode('utf-8');
        result = public.ExecShell(self.__SR + 'pm2 stop "'+get.pname+'" && pm2 delete "' + get.pname + '"|grep "' + get.pname+'"')[0];
        if result.find('✓') != -1: 
            public.ExecShell(self.__SR + 'pm2 save && pm2 startup');
            if os.path.exists(self.__path + get.pname): os.remove(self.__path + get.pname);
            return public.returnMsg(True,'DEL_SUCCESS');
        return public.returnMsg(False,'DEL_ERROR');
    
    #获取日志
    def GetLogs(self,get):
        path = '/root/.pm2/pm2.log';
        if not os.path.exists(path): return '当前没有日志';
        return public.readFile(path);

if __name__ == "__main__":
    p = pm2_main();
    print(p.List(None));