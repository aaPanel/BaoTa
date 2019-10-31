#coding: utf-8
#-------------------------------------------------------------------
# 宝塔Linux面板
#-------------------------------------------------------------------
# Copyright (c) 2015-2019 宝塔软件(http:#bt.cn) All rights reserved.
#-------------------------------------------------------------------
# Author: 黄文良 <287962566@qq.com>
#-------------------------------------------------------------------
import public,os,sys,json,time,psutil,py_compile,re
from BTPanel import session,cache
if sys.version_info[0] == 3: from importlib import reload
class mget: pass;
class panelPlugin:
    __isTable = None;
    __install_path = None;
    __tasks = None;
    __list = 'data/list.json'
    __type = 'data/type.json'
    __index = 'config/index.json'
    __link = 'config/link.json'
    __product_list = None
    __plugin_list = None
    pids = None
    ROWS = 15;
    
    def __init__(self):
        self.__install_path = 'plugin'

    #检查依赖
    def check_deps(self,get):
        cacheKey = 'plugin_lib_list'
        if not 'force' in get:
            libList = cache.get(cacheKey)
            if libList: return libList
        libList = json.loads(public.readFile('config/lib.json'))
        centos = os.path.exists('/bin/yum')
        for key in libList.keys():
            for i in range(len(libList[key])):
                checks = libList[key][i]['check'].split(',')
                libList[key][i]['status'] = False
                for check in checks:
                    if os.path.exists(check):
                        libList[key][i]['status'] = True
                        break;
                libList[key][i]['version'] = "-"
                if libList[key][i]['status']:
                    shellTmp = libList[key][i]['getv'].split(':D')
                    shellEx = shellTmp[0]
                    if len(shellTmp) > 1 and not centos: shellEx = shellTmp[1]
                    libList[key][i]['version'] = public.ExecShell(shellEx)[0].strip()
        cache.set(cacheKey,libList,86400);
        return libList

    #检测关键目录是否可以被写入文件
    def check_sys_write(self):
        test_file = '/etc/init.d/bt_10000100.pl'
        public.writeFile(test_file,'True')
        if os.path.exists(test_file): 
            if public.readFile(test_file) == 'True':
                os.remove(test_file)
                return True
            os.remove(test_file)
        return False

    #检查互斥
    def check_mutex(self,mutex):
        mutexs = mutex.split(',')
        for name in mutexs:
            pluginInfo = self.get_soft_find(name)
            if not pluginInfo: continue
            if pluginInfo['setup'] == True: return False
        return True

    #检查依赖
    def check_dependnet(self,dependnet):
        if not dependnet: return True
        dependnets = dependnet.split(',')
        status = True;
        for dep in dependnets:
            if not dep: continue
            if dep.find('|') != -1:
                names = dep.split('|')
                for name in names:
                    pluginInfo = self.get_soft_find(name)
                    if pluginInfo['setup'] == True:
                        status = True
                        break
                    else:
                        status = False
            else:
                pluginInfo = self.get_soft_find(dep)
                if pluginInfo['setup'] != True:
                    status = False
                    break
        return status

    #检查CPU限制
    def check_cpu_limit(self,cpuLimit):
        if psutil.cpu_count() < cpuLimit: return False
        return True

    #检查内存限制
    def check_mem_limit(self,memLimit):
        if psutil.virtual_memory().total/1024/1024 < memLimit: return False
        return True

    #检查操作系统限制
    def check_os_limit(self,osLimit):
        if osLimit == 0: return True
        if osLimit == 1:
            centos = os.path.exists('/usr/bin/yum')
            return centos
        elif osLimit == 2:
            debian = os.path.exists('/usr/bin/apt-get')
            return debian
        return True

                
    #安装插件
    def install_plugin(self,get):
        if not self.check_sys_write(): return public.returnMsg(False,'<a style="color:red;">错误：检测到系统关键目录不可写!</a><br>1、如果安装了[宝塔系统加固]，请先关闭<br><br>2、如果安装了云锁，请关闭[系统加固]功能<br>3、如果安装了安全狗，请关闭[系统防护]功能<br>4、如果使用了其它安全软件，请先卸载<br>')
        if not 'sName' in get: return public.returnMsg(False,'请指定软件名称!')
        pluginInfo = self.get_soft_find(get.sName);
        p_node = '/www/server/panel/install/public.sh'
        if os.path.exists(p_node):
            if len(public.readFile(p_node)) < 100: os.remove(p_node)
        if not pluginInfo: return public.returnMsg(False,'指定插件不存在!')
        if not self.check_mutex(pluginInfo['mutex']): return public.returnMsg(False,'请先卸载[%s]' % pluginInfo['mutex'] )
        if not hasattr(get,'id'):
            if not self.check_dependnet(pluginInfo['dependnet']): return public.returnMsg(False,'依赖以下软件,请先安装[%s]' % pluginInfo['dependnet'])
        if 'version' in get:
            for versionInfo in pluginInfo['versions']:
                if versionInfo['m_version'] != get.version: continue
                if not 'type' in get: get.type = '0'
                if int(get.type) > 3: get.type = '0'
                if get.type == '0':
                    if not self.check_cpu_limit(versionInfo['cpu_limit']): return public.returnMsg(False,'至少需要[%d]个CPU核心才能安装' % versionInfo['cpu_limit'])
                    if not self.check_mem_limit(versionInfo['mem_limit']): return public.returnMsg(False,'至少需要[%dMB]内存才能安装' % versionInfo['mem_limit'])
                if not self.check_os_limit(versionInfo['os_limit']): 
                    m_ps = {0:"所有的",1:"Centos",2:"Ubuntu/Debian"}
                    return public.returnMsg(False,'仅支持[%s]系统' % m_ps[int(versionInfo['os_limit'])])
                if not hasattr(get,'id'):
                    if not self.check_dependnet(versionInfo['dependnet']): return public.returnMsg(False,'依赖以下软件,请先安装[%s]' % versionInfo['dependnet'])
        
        if pluginInfo['type'] != 5:
            result = self.install_sync(pluginInfo,get)
        else:
            result = self.install_async(pluginInfo,get)
        try:
            if 'status' in result:
                if result['status']:
                    public.httpPost(public.GetConfigValue('home') + '/api/panel/plugin_total',{"pid":pluginInfo['id'],'p_name':pluginInfo['name']},3)
        except:pass
        return result
    
    #同步安装
    def install_sync(self,pluginInfo,get):
        if 'download' in pluginInfo['versions'][0]:
            tmp_path = '/www/server/panel/temp'
            if not os.path.exists(tmp_path): os.makedirs(tmp_path,mode=384);
            public.ExecShell("rm -rf " + tmp_path + '/*')
            toFile = tmp_path + '/' + pluginInfo['name'] + '.zip'
            public.downloadFile('http://www.bt.cn/api/Pluginother/get_file?fname=' + pluginInfo['versions'][0]['download'],toFile)
            if public.FileMd5(toFile) != pluginInfo['versions'][0]['md5']: return public.returnMsg(False,'文件Hash校验失败,停止安装!')
            update = False;
            if os.path.exists(pluginInfo['install_checks']): update =pluginInfo['versions'][0]['version_msg']
            return self.update_zip(None,toFile,update);
        else:
            download_url = public.get_url() + '/install/plugin/' + pluginInfo['name'] + '/install.sh';
            toFile = '/tmp/%s.sh' % pluginInfo['name']
            public.downloadFile(download_url,toFile);
            os.system('/bin/bash ' + toFile + ' install > /tmp/panelShell.pl');
            if os.path.exists(pluginInfo['install_checks']):
                public.WriteLog('TYPE_SETUP','PLUGIN_INSTALL_LIB',(pluginInfo['title'],));
                if os.path.exists(toFile): os.remove(toFile)
                return public.returnMsg(True,'PLUGIN_INSTALL_SUCCESS');
            return public.returnMsg(False,'安装失败!');

    #异步安装
    def install_async(self,pluginInfo,get):            
        mtype = 'install';
        mmsg = '安装';
        if hasattr(get, 'upgrade'):
            mtype = 'update'
            mmsg = 'upgrade'
        if not 'type' in get: get.type = '0'
        if int(get.type) > 3: get.type = '0'
        if get.sName == 'nginx': 
            if get.version == '1.8': return public.returnMsg(False,'Nginx 1.8.1版本过旧,不再提供支持，请选择其它版本!')
        if get.sName.find('php-') != -1: get.sName = get.sName.split('-')[0]
        php_path = '/www/server/php'
        if not os.path.exists(php_path): os.makedirs(php_path)
        apacheVersion='false';
        if public.get_webserver() == 'apache':
            apacheVersion = public.readFile('/www/server/apache/version.pl');
        public.writeFile('/var/bt_apacheVersion.pl',apacheVersion)
        public.writeFile('/var/bt_setupPath.conf','/www')
        if os.path.exists('/usr/bin/apt-get'): get.type = '3'
        execstr = "cd /www/server/panel/install && /bin/bash install_soft.sh " + get.type + " "+mtype+" " + get.sName + " "+ get.version;
        public.M('tasks').add('id,name,type,status,addtime,execstr',(None, mmsg + '['+get.sName+'-'+get.version+']','execshell','0',time.strftime('%Y-%m-%d %H:%M:%S'),execstr))
        cache.delete('install_task')
        public.writeFile('/tmp/panelTask.pl','True')
        public.WriteLog('TYPE_SETUP','PLUGIN_ADD',(get.sName,get.version));
        return public.returnMsg(True,'已将安装任务添加到队列!');

    #卸载插件
    def uninstall_plugin(self,get):
        pluginInfo = self.get_soft_find(get.sName);
        if not pluginInfo: return public.returnMsg(False,'指定插件不存在!')
        if pluginInfo['type'] != 5:
            pluginPath = self.__install_path + '/' + pluginInfo['name']
            if pluginInfo['type'] != 6:
                download_url = session['download_url'] + '/install/plugin/' + pluginInfo['name'] + '/install.sh'
                toFile = '/tmp/%s.sh' % pluginInfo['name']
                public.downloadFile(download_url,toFile)
                if os.path.exists(toFile):
                    if os.path.getsize(toFile) > 100:
                        os.system('/bin/bash ' + toFile + ' uninstall')
            
            if os.path.exists(pluginPath + '/install.sh'):
                os.system('/bin/bash ' + pluginPath + '/install.sh uninstall');

            if os.path.exists(pluginPath): os.system('rm -rf ' + pluginPath)
            public.WriteLog('TYPE_SETUP','PLUGIN_UNINSTALL_SOFT',(pluginInfo['title'],));
            return public.returnMsg(True,'PLUGIN_UNINSTALL');
        else:

            if pluginInfo['name'] == 'mysql':
                if public.M('databases').count() > 0: return public.returnMsg(False,"数据库列表非空，为了您的数据安全，请先备份并删除现有数据库<br>强制卸载命令：rm -rf /www/server/mysql")
            get.type = '0'
            issue = public.readFile('/etc/issue')
            if session['server_os']['x'] != 'RHEL': get.type = '3'
            get.sName = get.sName.lower()
            if get.sName.find('php-') != -1:
                get.sName = get.sName.split('-')[0]
            execstr = "cd /www/server/panel/install && /bin/bash install_soft.sh "+get.type+" uninstall " + get.sName.lower() + " "+ get.version.replace('.','');
            os.system(execstr);
            public.WriteLog('TYPE_SETUP','PLUGIN_UNINSTALL',(get.sName,get.version));
            return public.returnMsg(True,"PLUGIN_UNINSTALL");

    #从云端取列表
    def get_cloud_list(self,get=None):
        lcoalTmp = 'data/plugin.json'
        softList = None
        listTmp = public.readFile(lcoalTmp)
        try:
            if listTmp: softList = json.loads(listTmp)
        except:
            if os.path.exists(lcoalTmp): os.remove(lcoalTmp)

        focre  = 0
        if hasattr(get,'force'): focre = int(get.force)
        if 'focre_cloud' in session:
            if session['focre_cloud']:
                focre = 1
                session['focre_cloud'] = False

        if not 'init_cloud' in session:
                focre = 1
                session['init_cloud'] = True

        if not softList or focre > 0:
            self.clean_panel_log()
            cloudUrl = public.GetConfigValue('home') + '/api/panel/get_soft_list_test'
            import panelAuth
            pdata = panelAuth.panelAuth().create_serverid(None)
            listTmp = public.httpPost(cloudUrl,pdata,10)
            if not listTmp or len(listTmp) < 200:
                listTmp = public.readFile(lcoalTmp)
            try:
                softList = json.loads(listTmp)
            except: pass
            if softList: public.writeFile(lcoalTmp,json.dumps(softList))
            public.ExecShell('rm -f /tmp/bmac_*')
            self.getCloudPHPExt(get)
        try:
            public.writeFile("/tmp/" + cache.get('p_token'),str(softList['pro']))
        except:pass
        sType = 0
        try:
            if hasattr(get,'type'): sType = int(get['type'])
            if hasattr(get,'query'): 
                if get.query: sType = 0
        except:pass
        softList['list'] = self.get_local_plugin(softList['list'])
        softList['list'] = self.get_types(softList['list'],sType)
        if hasattr(get,'query'):
            if get.query:
                tmpList = []
                for softInfo in softList['list']:
                    if softInfo['name'].lower().find(get.query) != -1 or \
                        softInfo['title'].lower().find(get.query) != -1 or \
                        softInfo['ps'].lower().find(get.query) != -1: 
                        tmpList.append(softInfo)
                softList['list'] = tmpList
        return softList

    #清除多余面板日志
    def clean_panel_log(self):
        try:
            log_path = 'logs/request'
            if not os.path.exists(log_path): return False
            limit_num = 7
            p_logs = sorted(os.listdir(log_path))
            num = len(p_logs) - limit_num
            if num <= 0: return False
            for i in range(num):
                filename = log_path + '/' + p_logs[i]
                if not os.path.exists(filename): continue
                os.remove(filename)
            return True
        except:return False

    #取本地插件
    def get_local_plugin(self,sList):
        localList = []
        for name in os.listdir('plugin/'):
            isExists = False
            for softInfo in sList:
                if name == softInfo['name']: 
                    isExists = True
                    break;
            if isExists: continue
            filename = 'plugin/' + name + '/info.json'
            if not os.path.exists(filename): continue
            tmpInfo = public.ReadFile(filename).strip()
            if not tmpInfo: continue
            try:
                info = json.loads(tmpInfo)
            except: continue
            pluginInfo = self.get_local_plugin_info(info)
            if not pluginInfo: continue
            sList.append(pluginInfo)
        return sList

    #检查是否正在安装
    def check_setup_task(self,sName):
        if not self.__tasks:
            self.__tasks = public.M('tasks').where("status!=?",('1',)).field('status,name').select()
        if sName.find('php-') != -1: 
            tmp = sName.split('-')
            sName = tmp[0]
            version = tmp[1]
        isTask = '1';
        for task in self.__tasks:
            tmpt = public.getStrBetween('[',']',task['name'])
            if not tmpt:continue;
            tmp1 = tmpt.split('-');
            name1 = tmp1[0].lower();
            if sName == 'php':
                if name1 == sName and tmp1[1] == version: isTask = task['status'];
            else:
                if name1 == 'pure': name1 = 'pure-ftpd';
                if name1 == sName: isTask = task['status']; 

            if isTask == '-1' or isTask == '0':
                if task['name'].find('upgrade') != -1: isTask = '-2'
            break
        return isTask


    #构造本地插件信息
    def get_local_plugin_info(self,info):
        m_version = info['versions'].split(".")
        if len(m_version) < 2: return None
        if len(m_version) > 2:
            tmp = m_version[:]
            del(tmp[0])
            m_version[1] = '.'.join(tmp)

        try:
            if not 'author' in info: info['author'] = '未知'
            if not 'home' in info: info['home'] = '#'
            pluginInfo = {
	                        "id": 10000,
	                        "pid": 0,
	                        "type": 10,
	                        "price": 0,
                            "author":info['author'],
                            "home":info['home'],
	                        "name": info['name'],
	                        "title": info['title'],
	                        "panel_pro": 1,
	                        "panel_free": 1,
	                        "panel_test": 1,
	                        "ps": info['ps'],
	                        "version": info['versions'],
	                        "s_version": "0",
	                        "manager_version": "1",
	                        "c_manager_version": "1",
	                        "dependnet": "",
	                        "mutex": "",
	                        "install_checks": "/www/server/panel/plugin/" + info['name'],
	                        "uninsatll_checks": "/www/server/panel/plugin/" + info['name'],
	                        "compile_args": 0,
	                        "version_coexist": 0,
	                        "versions": [
		                        {
			                        "m_version": m_version[0],
			                        "version": m_version[1],
			                        "dependnet": "",
			                        "mem_limit": 32,
			                        "cpu_limit": 1,
			                        "os_limit": 0,
			                        "setup": True
		                        }
	                        ],
	                        "setup": True,
	                        "status": True
                        }
        except: pluginInfo = None
        return pluginInfo
                
    #处理分类
    def get_types(self,sList,sType):
        if sType == 0: return sList
        newList = []
        for sInfo in sList:
            if sInfo['type'] == sType: newList.append(sInfo)
        return newList

    #检查权限
    def check_accept(self,get):
        import common
        args = common.dict_obj()
        args.type = '8'
        p_list = self.get_cloud_list(args)
        for p in p_list['list']:
            if p['name'] == get.name:
                if p_list['pro'] < 0 and p['endtime'] < 0: return False
                break

        args.type = '10'
        p_list = self.get_cloud_list(args)
        for p in p_list['list']:
            if p['name'] == get.name:
                if not 'endtime' in p: continue;
                if p['endtime'] < 0: return False
                break
        return True

    #取软件列表
    def get_soft_list(self,get = None):
        softList = self.get_cloud_list(get)
        if not softList: 
            get.force = 1
            softList = self.get_cloud_list(get)
            if not softList: return public.returnMsg(False,'软件列表获取失败(401)!')
        softList['list'] = self.set_coexist(softList['list'])
        softList['list'] = self.get_page(softList['list'],get)
        softList['list']['data'] = self.check_isinstall(softList['list']['data'])
        softList['apache22'] = False
        softList['apache24'] = False
        check_version_path = '/www/server/apache/version_check.pl'
        if os.path.exists(check_version_path):
            softList['apache24'] = True
            if public.readFile(check_version_path).find('2.2') == 0: 
                softList['apache22'] = True
                softList['apache24'] = False

        return softList

    #取首页软件列表
    def get_index_list(self,get=None):
        softList = self.get_cloud_list(get)['list']
        if not softList: 
            get.force = 1
            softList = self.get_cloud_list(get)['list']
            if not softList: return public.returnMsg(False,'软件列表获取失败(401)!')
        softList = self.set_coexist(softList)
        if not os.path.exists(self.__index): public.writeFile(self.__index,'[]')
        indexList = json.loads(public.ReadFile(self.__index))
        dataList = []
        for index in indexList:
            for softInfo in softList:
                if softInfo['name'] == index: dataList.append(softInfo)
        dataList = self.check_isinstall(dataList)
        
        return dataList

    #添加到首页
    def add_index(self,get):
        sName = get.sName
        if not os.path.exists(self.__index): public.writeFile(self.__index,'[]')
        indexList = json.loads(public.ReadFile(self.__index))
        if sName in indexList: return public.returnMsg(False,'请不要重复添加!')

        if len(indexList) >= 12: 
            new_indexList = []
            softList = self.get_cloud_list(get)['list']
            for softInfo in softList:
                if softInfo['name'] in indexList:
                    new_softInfo = self.check_status(softInfo)
                    if not new_softInfo['setup']: indexList.remove(softInfo['name'])
            public.writeFile(self.__index,json.dumps(indexList))
            if len(indexList) >= 12: return public.returnMsg(False,'首页最多只能显示12个软件!')

        indexList.append(sName)
        public.writeFile(self.__index,json.dumps(indexList))
        return public.returnMsg(True,'添加成功!')

    #删除首页
    def remove_index(self,get):
        sName = get.sName
        indexList = []
        if not os.path.exists(self.__index): public.writeFile(self.__index,'[]')
        indexList = json.loads(public.ReadFile(self.__index))
        if not sName in indexList: return public.returnMsg(True,'删除成功!')
        indexList.remove(sName)
        public.writeFile(self.__index,json.dumps(indexList))
        return public.returnMsg(True,'删除成功!')

    #设置排序
    def sort_index(self,get):
        indexList = get.ssort.split('|')
        public.writeFile(self.__index,json.dumps(indexList))
        return public.returnMsg(True,'设置成功!')
    
    #取快捷软件列表
    def get_link_list(self,get=None):
        softList = self.get_cloud_list(get)['list']
        softList = self.set_coexist(softList)
        indexList = json.loads(public.ReadFile(self.__link))
        dataList = []
        for index in indexList:
            for softInfo in softList:
                if softInfo['name'] == index: dataList.append(softInfo)
        dataList = self.check_isinstall(dataList)
        return dataList

    #添加到快捷栏
    def add_link(self,get):
        sName = get.sName
        indexList = json.loads(public.ReadFile(self.__link))
        if sName in indexList: return public.returnMsg(False,'请不要重复添加!')
        if len(indexList) >= 5: return public.returnMsg(False,'快捷栏最多只能显示5个软件!')
        indexList.append(sName)
        public.writeFile(self.__link,json.dumps(indexList))
        return public.returnMsg(True,'添加成功!')

    #删除快捷栏
    def remove_link(self,get):
        sName = get.sName
        indexList = []
        indexList = json.loads(public.ReadFile(self.__link))
        if sName in indexList: return public.returnMsg(True,'删除成功!')
        indexList.remove(sName)
        public.writeFile(self.__link,json.dumps(indexList))
        return public.returnMsg(True,'删除成功!')

    #设置快捷栏排序
    def sort_link(self,get):
        indexList = get.ssort.split('|')
        public.writeFile(self.__link,json.dumps(indexList))
        return public.returnMsg(True,'设置成功!')



    #处理共存软件
    def set_coexist(self,sList):
        softList = []
        for sInfo in sList:
            if sInfo['version_coexist'] == 1:
                for versionA in sInfo['versions']:
                    sTmp = sInfo.copy()
                    v = versionA['m_version'].replace('.','')
                    sTmp['title'] = sTmp['title']+'-'+versionA['m_version']
                    sTmp['name'] = sTmp['name']+'-'+versionA['m_version']
                    sTmp['version'] = sTmp['version'].replace('{VERSION}',v)
                    sTmp['manager_version'] = sTmp['manager_version'].replace('{VERSION}',v)
                    sTmp['install_checks'] = sTmp['install_checks'].replace('{VERSION}',v)
                    sTmp['uninsatll_checks'] = sTmp['uninsatll_checks'].replace('{VERSION}',v)
                    sTmp['s_version'] = sTmp['s_version'].replace('{VERSION}',v)
                    sTmp['versions'] = []
                    sTmp['versions'].append(versionA)
                    softList.append(sTmp)
            else:
                softList.append(sInfo)
        return softList

    #检测是否安装
    def check_isinstall(self,sList):
        if not os.path.exists(self.__index): public.writeFile(self.__index,'[]')
        indexList = json.loads(public.ReadFile(self.__index))
        for i in range(len(sList)):
            sList[i]['index_display'] = sList[i]['name'] in indexList
            sList[i] = self.check_status(sList[i])
        return sList

    #检查软件状态
    def check_status(self,softInfo):
        softInfo['setup'] = os.path.exists(softInfo['install_checks'])
        softInfo['status'] = False
        softInfo['task'] = self.check_setup_task(softInfo['name'])
        if softInfo['name'].find('php-') != -1: softInfo['fpm'] = False
        if softInfo['setup']:
            softInfo['shell'] = softInfo['version']
            softInfo['version'] = self.get_version_info(softInfo)
            softInfo['status'] = True
            softInfo['versions'] = self.tips_version(softInfo['versions'],softInfo['version'])
            softInfo['admin'] = os.path.exists('/www/server/panel/plugin/' + softInfo['name'])
            if len(softInfo['s_version']) > 3:
                pNames = softInfo['s_version'].split(',')
                for pName in pNames:
                    if len(softInfo['manager_version']) > 5:
                        softInfo['status'] = self.process_exists(pName,softInfo['manager_version'])
                    else:
                        softInfo['status'] = self.process_exists(pName)
                    if softInfo['status']: break
        else:
            softInfo['version'] = ""
        if softInfo['version_coexist'] == 1:
            self.get_icon(softInfo['name'].split('-')[0])
        else:
            if 'min_image' in softInfo: 
                self.get_icon(softInfo['name'],softInfo['min_image'])
            else:
                self.get_icon(softInfo['name'])
        if softInfo['name'].find('php-') != -1: 
            v2= softInfo['versions'][0]['m_version'].replace('.','')
            softInfo['fpm'] = os.path.exists('/www/server/php/' + v2 + '/sbin/php-fpm')
            softInfo['status'] = os.path.exists('/tmp/php-cgi-'+v2+'.sock')
            if not softInfo['fpm']: softInfo['status'] = True
        if softInfo['name'] == 'mysql': softInfo['status'] = self.process_exists('mysqld')
        if softInfo['name'] == 'phpmyadmin': softInfo['status'] = self.get_phpmyadmin_stat()
        return softInfo

    #取phpmyadmin状态
    def get_phpmyadmin_stat(self):
        if public.get_webserver() == 'nginx':
            filename = public.GetConfigValue('setup_path') + '/nginx/conf/nginx.conf';
        else:
            filename = public.GetConfigValue('setup_path') + '/apache/conf/extra/httpd-vhosts.conf';
        if not os.path.exists(filename): return False
        conf = public.readFile(filename)
        if not conf: return False
        return conf.find('/www/server/stop') == -1

    #获取指定软件信息
    def get_soft_find(self,get = None):
        softList = self.get_cloud_list(get)['list']
        softList = self.set_coexist(softList)
        try:
            sName = get['sName']
        except:
            sName = get

        for softInfo in softList:

            if softInfo['name'] == sName: 
                if sName == 'phpmyadmin':
                    softInfo['ext'] = self.getPHPMyAdminStatus()
                return self.check_status(softInfo)
        return False


    #获取版本信息
    def get_version_info(self,sInfo):
        version = ''
        vFile1 = sInfo['uninsatll_checks'] + '/version_check.pl'
        vFile2 = sInfo['uninsatll_checks'] + '/info.json'
        if os.path.exists(vFile1): 
            version = public.ReadFile(vFile1).strip()
            if not version: os.remove(vFile1)
        elif  os.path.exists(vFile2): 
            v_tmp = public.ReadFile(vFile2).strip()
            if v_tmp: 
                try:
                    version = json.loads(v_tmp)['versions']
                except: public.ExecShell('rm -f ' + vFile2)
            else:
                version = "1.0"
        else:
            exec_args = {
                    'nginx':"/www/server/nginx/sbin/nginx -v 2>&1|grep version|awk '{print $3}'|cut -f2 -d'/'",
                    'apache':"/www/server/apache/bin/httpd -v|grep version|awk '{print $3}'|cut -f2 -d'/'",
                    'mysql':"/www/server/mysql/bin/mysql -V|grep Ver|awk '{print $5}'|cut -f1 -d','",
                    'php':"/www/server/php/{VERSION}/bin/php -v|grep cli|awk '{print $2}'",
                    'pureftpd':"cat /www/server/pure-ftpd/version.pl",
                    'phpmyadmin':"cat /www/server/phpmyadmin/version.pl",
                    'tomcat':"/www/server/tomcat/bin/version.sh|grep version|awk '{print $4}'|cut -f2 -d'/'",
                    'memcached':"/usr/local/memcached/bin/memcached -V|awk '{print $2}'",
                    'redis':"/www/server/redis/src/redis-server -v|awk '{print $3}'|cut -f2 -d'='",
                    'gitlab':'echo "8.8.5"'
                }
            
            exec_str = ''
            if sInfo['name'] in exec_args: exec_str = exec_args[sInfo['name']] 
            if sInfo['version_coexist'] == 1:
                v_tmp = sInfo['name'].split('-')
                exec_str = exec_args[v_tmp[0]].replace('{VERSION}',v_tmp[1].replace('.',''))
            version = public.ExecShell(exec_str)[0].strip()
            if version: public.writeFile(vFile1,version)

        if sInfo['name'] == 'mysql':
            vFile3 = sInfo['uninsatll_checks'] + '/version.pl'
            version_str = None
            if os.path.exists(vFile3): 
                version_str = public.readFile(vFile3)
                if version_str.find('AliSQL') != -1: version = 'AliSQL'
            if version == 'Linux' and version_str:
                version = version_str
                public.writeFile(vFile1,version)

        if sInfo['name'] == 'nginx':
            if version.find('2.2.') != -1: version = '-Tengine' + version
        return version.replace('p1','')


    #标记当前安装的版本
    def tips_version(self,versions,version):
        if len(versions) == 1:
            versions[0]['setup'] = True;
            return versions
        
        for i in range(len(versions)):
            if version == (versions[i]['m_version'] + '.' + versions[i]['version']):
                versions[i]['setup'] = True
                continue;
            vTmp = versions[i]['m_version'].split('_')
            if len(vTmp) > 1: 
                vTmp = vTmp[1]
            else:
                vTmp = vTmp[0]
            vLen = len(vTmp)
            versions[i]['setup'] = (version[:vLen] == vTmp)
        return versions

    #取pids
    def get_pids(self):
        pids = []
        for pid in os.listdir('/proc'):
            if re.match("^\d+$",pid): pids.append(pid)
        return pids


    #进程是否存在
    def process_exists(self,pname,exe = None):
        if not self.pids: self.pids = psutil.pids() #self.get_pids() #
        for pid in self.pids:
            try:
                l = '/proc/%s/exe' % pid
                f = '/proc/%s/comm' % pid
                p_exe = ''
                p_name = ''
                if os.path.exists(l): 
                    p_exe = os.readlink(l)
                    if not p_name: p_name = p_exe.split('/')[-1]

                if not p_name and os.path.exists(f):
                    fp = open(f,'r')
                    p_name = fp.read().strip()
                    fp.close()

                if not p_name: continue
                if p_name == pname: 
                    if not exe:
                        return True;
                    else:
                        if p_exe == exe: return True
            except: continue
        return False

     #取分页
    def get_page(self,data,get):
        #包含分页类
        import page
        #实例化分页类
        page = page.Page();
        info = {}
        info['count'] = len(data)
        info['row']   = self.ROWS;
        info['p'] = 1
        if hasattr(get,'p'):
            try:
                info['p']     = int(get['p'])
            except:
                info['p'] = 1
        info['uri']   = {}
        info['return_js'] = ''
        if hasattr(get,'tojs'):
            info['return_js']   = get.tojs
        
        #获取分页数据
        result = {}
        result['page'] = page.GetPage(info)
        n = 0;
        result['data'] = [];
        for i in range(info['count']):
            if n >= page.ROW: break;
            if i < page.SHIFT: continue;
            n += 1;
            result['data'].append(data[i]);
        return result;
        
    
    #取列表
    def GetList(self,get = None):
        try:
            if not os.path.exists(self.__list): return [];
            data = json.loads(public.readFile(self.__list));
            
            #排序
            data = sorted(data, key= lambda b:b['sort'],reverse=False);
            
            #获取非划分列表
            n = 0;
            for dirinfo in os.listdir(self.__install_path):
                isTrue = True
                for tm in data:
                    if tm['name'] == dirinfo: isTrue = False
                if not isTrue: continue;
                
                path = self.__install_path + '/' + dirinfo
                if os.path.isdir(path):
                    jsonFile = path + '/info.json'
                    if os.path.exists(jsonFile):
                        try:                            
                            tmp = json.loads(public.readFile(jsonFile))
                            if not hasattr(get,'type'): 
                                get.type = 0;
                            else:
                                get.type = int(get.type)
                            
                            if get.type > 0:
                                try:
                                    if get.type != tmp['id']: continue;
                                except:
                                    continue;
                            
                            tmp['pid'] = len(data) + 1000 + n
                            tmp['status'] = tmp['display'];
                            tmp['display'] = 0;
                            data.append(tmp)
                        except:
                            pass
            #索引列表
            if get:
                display = None
                if hasattr(get,'display'): display = True;
                if not hasattr(get,'type'): 
                    get.type = 0;
                else:
                    get.type = int(get.type)
                if not hasattr(get,'search'): 
                    search = None
                    m = 0
                else:
                    search = get.search.encode('utf-8').lower();
                    m = 1
                    
                tmp = [];
                for d in data:
                    self.get_icon(d['name']);
                    if display:
                        if d['display'] == 0: continue;
                    i=0;
                    if get.type > 0:
                        if get.type == d['id']: i+=1
                    else:
                        i+=1
                    if search:
                        if d['name'].lower().find(search) != -1: i+=1;
                        if d['name'].find(search) != -1: i+=1;
                        if d['title'].lower().find(search) != -1: i+=1;
                        if d['title'].find(search) != -1: i+=1;
                        if get.type > 0 and get.type != d['type']: i -= 1;
                    if i>m:tmp.append(d);
                data = tmp;
            return data
        except Exception as ex:
            return str(ex);
        
    
    #获取图标
    def get_icon(self,name,downFile = None):
        iconFile = 'BTPanel/static/img/soft_ico/ico-' + name + '.png'

        if not os.path.exists(iconFile):
            self.download_icon(name,iconFile,downFile)
        else:
            size = os.path.getsize(iconFile)
            if size == 0: self.download_icon(name,iconFile,downFile)
        
    #下载图标
    def download_icon(self,name,iconFile,downFile):
        srcIcon =  'plugin/' + name + '/icon.png';
        if os.path.exists(srcIcon):
            public.ExecShell("\cp  -a -r " + srcIcon + " " + iconFile)
        else:
            if downFile:
                public.ExecShell('wget -O ' + iconFile + ' ' + public.GetConfigValue('home') + downFile + '&');
            else:
                public.ExecShell('wget -O ' + iconFile + ' ' + public.get_url() + '/install/plugin/' + name + '/icon.png &');
                
    
    #取分页
    def GetPage(self,data,get):
        #包含分页类
        import page
        #实例化分页类
        page = page.Page();
        info = {}
        info['count'] = len(data)
        info['row']   = self.ROWS;
        info['p'] = 1
        if hasattr(get,'p'):
            info['p']     = int(get['p'])
        info['uri']   = {}
        info['return_js'] = ''
        if hasattr(get,'tojs'):
            info['return_js']   = get.tojs
        
        #获取分页数据
        result = {}
        result['page'] = page.GetPage(info)
        n = 0;
        result['data'] = [];
        for i in range(info['count']):
            if n > page.ROW: break;
            if i < page.SHIFT: continue;
            n += 1;
            result['data'].append(data[i]);
        return result;
    
    #取分类
    def GetType(self,get = None):
        try:
            if not os.path.exists(self.__type): return False;
            data = json.loads(public.readFile(self.__type));
            return data
        except:
            return False;
        
    #取单个
    def GetFind(self,name):
        try:
            data = self.GetList(None);
            for d in data:
                if d['name'] == name: return d;
            return None
        except:
            return None;
    
    #设置
    def SetField(self,name,key,value):
        data = self.GetList(None);
        for i in range(len(data)):
            if data[i]['name'] != name: continue;
            data[i][key] = value;
        
        public.writeFile(self.__list,json.dumps(data));
        return True;
    
    
    
    #安装插件
    def install(self,get):
        pluginInfo = self.GetFind(get.name);
        if not pluginInfo:
            import json
            pluginInfo = json.loads(public.readFile(self.__install_path + '/' + get.name + '/info.json'));
        
        if pluginInfo['tip'] == 'lib':
            if not os.path.exists(self.__install_path + '/' + pluginInfo['name']): os.system('mkdir -p ' + self.__install_path + '/' + pluginInfo['name']);
            if not 'download_url' in session: session['download_url'] = 'http://download.bt.cn';
            download_url = session['download_url'] + '/install/plugin/' + pluginInfo['name'] + '/install.sh';
            toFile = self.__install_path + '/' + pluginInfo['name'] + '/install.sh';
            public.downloadFile(download_url,toFile);
            os.system('/bin/bash ' + toFile + ' install');
            if self.checksSetup(pluginInfo['name'],pluginInfo['checks'],pluginInfo['versions'])[0]['status'] or os.path.exists(self.__install_path + '/' + get.name):
                public.WriteLog('TYPE_SETUP','PLUGIN_INSTALL_LIB',(pluginInfo['title'],));
                #os.system('rm -f ' + toFile);
                return public.returnMsg(True,'PLUGIN_INSTALL_SUCCESS');
            return public.returnMsg(False,'PLUGIN_INSTALL_ERR');
        else:
            import db,time
            path = '/www/server/php'
            if not os.path.exists(path): os.system("mkdir -p " + path);
            issue = public.readFile('/etc/issue')
            if session['server_os']['x'] != 'RHEL': get.type = '3'
            
            apacheVersion='false';
            if public.get_webserver() == 'apache':
                apacheVersion = public.readFile('/www/server/apache/version.pl');
            public.writeFile('/var/bt_apacheVersion.pl',apacheVersion)
            public.writeFile('/var/bt_setupPath.conf',public.GetConfigValue('root_path'))
            isTask = '/tmp/panelTask.pl'
            
            mtype = 'install';
            mmsg = '安装';
            if hasattr(get, 'upgrade'):
                if get.upgrade:
                    mtype = 'update';
                    mmsg = 'upgrade';
            execstr = "cd /www/server/panel/install && /bin/bash install_soft.sh " + get.type + " "+mtype+" " + get.name + " "+ get.version;
            sql = db.Sql()
            if hasattr(get,'id'):
                id = get.id;
            else:
                id = None;
            sql.table('tasks').add('id,name,type,status,addtime,execstr',(None, mmsg + '['+get.name+'-'+get.version+']','execshell','0',time.strftime('%Y-%m-%d %H:%M:%S'),execstr))
            public.writeFile(isTask,'True')
            public.WriteLog('TYPE_SETUP','PLUGIN_ADD',(get.name,get.version));
            return public.returnMsg(True,'PLUGIN_INSTALL');
        
        
    #卸载插件
    def unInstall(self,get):
        pluginInfo = self.GetFind(get.name);
        if not pluginInfo:
            import json
            pluginInfo = json.loads(public.readFile(self.__install_path + '/' + get.name + '/info.json'));
        
        if pluginInfo['tip'] == 'lib':
            if not os.path.exists(self.__install_path+ '/' + pluginInfo['name']): os.system('mkdir -p ' + self.__install_path + '/' + pluginInfo['name']);
            download_url = session['download_url'] + '/install/plugin/' + pluginInfo['name'] + '/install.sh';
            toFile = self.__install_path + '/' + pluginInfo['name'] + '/uninstall.sh';
            public.downloadFile(download_url,toFile)
            os.system('/bin/bash ' + toFile + ' uninstall')
            os.system('rm -rf ' + session['download_url'] + '/install/plugin/' + pluginInfo['name'])
            pluginPath = self.__install_path + '/' + pluginInfo['name']
            
            if os.path.exists(pluginPath + '/install.sh'):
                os.system('/bin/bash ' + pluginPath + '/install.sh uninstall');
                
            if os.path.exists(pluginPath):
                public.ExecShell('rm -rf ' + pluginPath);
                
            public.WriteLog('TYPE_SETUP','PLUGIN_UNINSTALL_SOFT',(pluginInfo['title'],));
            return public.returnMsg(True,'PLUGIN_UNINSTALL');
        else:
            get.type = '0'
            issue = public.readFile('/etc/issue')
            if session['server_os']['x'] != 'RHEL': get.type = '3'
            public.writeFile('/var/bt_setupPath.conf',public.GetConfigValue('root_path'))
            execstr = "cd /www/server/panel/install && /bin/bash install_soft.sh "+get.type+" uninstall " + get.name.lower() + " "+ get.version.replace('.','');
            os.system(execstr);
            public.WriteLog('TYPE_SETUP','PLUGIN_UNINSTALL',(get.name,get.version));
            return public.returnMsg(True,"PLUGIN_UNINSTALL");
    
    #取产品信息 
    def getProductInfo(self,productName):
        if not self.__product_list:
            import panelAuth
            Auth = panelAuth.panelAuth();
            self.__product_list = Auth.get_business_plugin(None);
        for product in self.__product_list:
            if product['name'] == productName: return product;
        return None;
    
    #取到期时间
    def getEndDate(self,pluginName):
        if not self.__plugin_list:
            import panelAuth
            Auth = panelAuth.panelAuth();
            tmp = Auth.get_plugin_list(None);
            if not tmp: return '未开通';
            if not 'data' in tmp: return '未开通';
            self.__plugin_list = tmp['data']
        for pluinfo in self.__plugin_list:
            if pluinfo['product'] == pluginName: 
                if not pluinfo['endtime'] or not pluinfo['state']: return '待支付';
                if pluinfo['endtime'] < time.time(): return '已到期';
                return time.strftime("%Y-%m-%d",time.localtime(pluinfo['endtime']));
        return '未开通';
    
    #取插件列表
    def getPluginList(self,get):
        import json
        arr = self.GetList(get);
        result = {}
        if not arr: 
            result['data'] = arr;
            result['type'] = self.GetType(None);
            return result;
        apacheVersion = ""
        try:
            apavFile = '/www/server/apache/version.pl';
            if os.path.exists(apavFile):
                apacheVersion = public.readFile(apavFile).strip();
        except:
            pass;
        
        result = self.GetPage(arr,get);
        arr = result['data'];
        for i in range(len(arr)):
            arr[i]['end'] = '--';
            #if 'price' in arr[i]:
            #    if arr[i]['price'] > 0:
            #        arr[i]['end'] = self.getEndDate(arr[i]['title']);
            #        if os.path.exists('plugin/beta/config.conf'):
            #            if os.path.exists('plugin/' + arr[i]['name'] + '/' + arr[i]['name'] + '_main.py') and arr[i]['end'] == '未开通': arr[i]['end'] = '--';
                    
                        
            if arr[i]['name'] == 'php':
                if apacheVersion == '2.2':
                    arr[i]['versions'] = '5.2,5.3,5.4';
                    arr[i]['update'] = self.GetPv(arr[i]['versions'], arr[i]['update'])
                elif apacheVersion == '2.4':
                    arr[i]['versions'] = '5.3,5.4,5.5,5.6,7.0,7.1,7.2,7.3,7.4';
                    arr[i]['update'] = self.GetPv(arr[i]['versions'], arr[i]['update'])
                arr[i]['apache'] = apacheVersion;
                    
            arr[i]['versions'] = self.checksSetup(arr[i]['name'].replace('_soft',''),arr[i]['checks'],arr[i]['versions'])
            
            try:
                arr[i]['update'] = arr[i]['update'].split(',');
            except:
                arr[i]['update'] = [];
            
            #是否强制使用插件模板 LIB_TEMPLATE
            if os.path.exists(self.__install_path+'/'+arr[i]['name']): arr[i]['tip'] = 'lib';
            
            if arr[i]['tip'] == 'lib': 
                arr[i]['path'] = self.__install_path + '/' + arr[i]['name'].replace('_soft','');
                arr[i]['config'] = os.path.exists(arr[i]['path'] + '/index.html');
            else:
                arr[i]['path'] = '/www/server/' + arr[i]['name'].replace('_soft','');
        arr.append(public.M('tasks').where("status!=?",('1',)).count());
        
        
        result['data'] = arr;
        result['type'] = self.GetType(None);
        return result;
    
    #GetPHPV
    def GetPv(self,versions,update):
        versions = versions.split(',');
        update = update.split(',');
        updates = [];
        for up in update:
            if up[:3] in versions: updates.append(up);
        return ','.join(updates);
    
    #保存插件排序
    def savePluginSort(self,get):
        ssort = get.ssort.split('|');
        data = self.GetList(None)
        l = len(data);
        for i in range(len(ssort)):
            if int(ssort[i]) > 1000: continue;
            for n in range(l):
                if data[n]['pid'] == int(ssort[i]): data[n]['sort'] = i;
        public.writeFile(self.__list,json.dumps(data));
        return public.returnMsg(True,'PLUGIN_SORT');
    
    #检查是否安装
    def checksSetup(self,name,checks,vers = ''):
        tmp = checks.split(',');
        versions = [];
        path = '/www/server/' + name + '/version.pl';
        v1 = '';            
        if os.path.exists(path): v1 = public.readFile(path).strip()
        if name == 'nginx': v1 = v1.replace('1.10', '1.12');
        if not self.__tasks:
            self.__tasks = public.M('tasks').where("status!=?",('1',)).field('status,name').select()
        isStatus = 0;
        versArr = vers.split(',');
        for v in versArr:
            version = {}
            
            v2 = v;
            if name == 'php': v2 = v2.replace('.','');
            status = False;
            for tm in tmp:
                if name == 'php':
                    path = '/www/server/php/' + v2
                    if os.path.exists(path + '/bin/php') and not os.path.exists(path + '/version.pl'): 
                        public.ExecShell("echo `"+path+"/bin/php 2>/dev/null -v|grep cli|awk '{print $2}'` > " + path + '/version.pl')
                    try:
                        v1 = public.readFile(path+'/version.pl').strip();
                        if not v1: os.system('rm -f ' + path + '/version.pl');
                    except:
                        v1 = "";
                    if os.path.exists(tm.replace('VERSION',v2)): status = True;
                else:
                    if os.path.exists(tm) and isStatus == 0:
                        if len(versArr) > 1:
                            im = v1.find(v)
                            if im != -1 and im < 3:
                                status = True
                                isStatus += 1;
                        else:
                            status = True
                            isStatus += 1;
            #处理任务标记
            if not self.__tasks:
                self.__tasks = public.M('tasks').where("status!=?",('1',)).field('status,name').select()
            isTask = '1';
            for task in self.__tasks:
                tmpt = public.getStrBetween('[',']',task['name'])
                if not tmpt:continue;
                tmp1 = tmpt.split('-');
                name1 = tmp1[0].lower();
                if name == 'php':
                    if name1 == name and tmp1[1] == v: isTask = task['status'];
                else:
                    if name1 == 'pure': name1 = 'pure-ftpd';
                    if name1 == name: isTask = task['status']; 
            
            infoFile = 'plugin/' + name + '/info.json'
            if os.path.exists(infoFile):
                try:
                    tmps = json.loads(public.readFile(infoFile));
                    if tmps: v1 = tmps['versions'];
                except:pass;
            
            if name == 'memcached':
                if os.path.exists('/etc/init.d/memcached'):
                    v1 = session.get('memcachedv')
                    if not v1:
                        v1 = public.ExecShell("memcached -V|awk '{print $2}'")[0].strip();
                        session['memcachedv'] = v1
            if name == 'apache':
                if os.path.exists('/www/server/apache/bin/httpd'): 
                    v1 = session.get('httpdv')
                    if not v1:
                        v1 = public.ExecShell("/www/server/apache/bin/httpd -v|grep Apache|awk '{print $3}'|sed 's/Apache\///'")[0].strip();
                        session['httpdv'] = v1
            #if name == 'mysql':
            #    if os.path.exists('/www/server/mysql/bin/mysql'): v1 = public.ExecShell("mysql -V|awk '{print $5}'|sed 's/,//'")[0].strip();

            version['status'] = status
            version['version'] = v;
            version['task'] = isTask;
            version['no'] = v1
            versions.append(version);
        return self.checkRun(name,versions);
        
    #检查是否启动
    def checkRun(self,name,versions):
        if name == 'php':
            path = '/www/server/php' 
            for i in range(len(versions)):
                if versions[i]['status']:
                    v4 = versions[i]['version'].replace('.','')
                    versions[i]['run'] = os.path.exists('/tmp/php-cgi-' + v4 + '.sock');
                    versions[i]['fpm'] = os.path.exists('/etc/init.d/php-fpm-'+v4);
                    phpConfig = self.GetPHPConfig(v4);
                    versions[i]['max'] = phpConfig['max']
                    versions[i]['maxTime'] = phpConfig['maxTime']
                    versions[i]['pathinfo'] = phpConfig['pathinfo']
                    versions[i]['display'] = os.path.exists(path + '/' + v4 + '/display.pl');
                    if len(versions) < 5: versions[i]['run'] = True;
                
        elif name == 'nginx':
            status = False
            if os.path.exists('/etc/init.d/nginx'):
                pidf = '/www/server/nginx/logs/nginx.pid';
                if os.path.exists(pidf):
                    try:
                        pid = public.readFile(pidf)
                        pname = self.checkProcess(pid);
                        if pname: status = True;
                    except:
                        status = False
            for i in range(len(versions)):
                versions[i]['run'] = False
                if versions[i]['status']: versions[i]['run'] = status
        elif name == 'apache':
            status = False
            if os.path.exists('/etc/init.d/httpd'):
                pidf = '/www/server/apache/logs/httpd.pid';
                if os.path.exists(pidf):
                    pid = public.readFile(pidf)
                    status = self.checkProcess(pid);
            for i in range(len(versions)):
                versions[i]['run'] = False
                if versions[i]['status']: versions[i]['run'] = status
        elif name == 'mysql':
            status = os.path.exists('/tmp/mysql.sock')
            for i in range(len(versions)):
                versions[i]['run'] = False
                if versions[i]['status']: versions[i]['run'] = status
        elif name == 'tomcat':
            status = False
            if os.path.exists('/www/server/tomcat/logs/catalina-daemon.pid'):
                if self.getPid('jsvc'): status = True
            if not status:
                if self.getPid('java'): status = True
            for i in range(len(versions)):
                versions[i]['run'] = False
                if versions[i]['status']: versions[i]['run'] = status
        elif name == 'pure-ftpd':
             for i in range(len(versions)):
                pidf = '/var/run/pure-ftpd.pid'
                if os.path.exists(pidf):
                    pid = public.readFile(pidf)
                    versions[i]['run'] = self.checkProcess(pid)
                    if not versions[i]['run']: os.system('rm -f ' + pidf)
        elif name == 'phpmyadmin':
            for i in range(len(versions)):
                if versions[i]['status']: versions[i] = self.getPHPMyAdminStatus();
        elif name == 'redis':
            for i in range(len(versions)):
                pidf = '/var/run/redis_6379.pid'
                if os.path.exists(pidf):
                    pid = public.readFile(pidf)
                    versions[i]['run'] = self.checkProcess(pid)
                    if not versions[i]['run']: os.system('rm -f ' + pidf)
        elif name == 'memcached':
            for i in range(len(versions)):
                pidf = '/var/run/memcached.pid'
                if os.path.exists(pidf):
                    pid = public.readFile(pidf)
                    versions[i]['run'] = self.checkProcess(pid)
                    if not versions[i]['run']: os.system('rm -f ' + pidf)
        else:
            for i in range(len(versions)):
                if versions[i]['status']: versions[i]['run'] = True;
        return versions
    
    #取PHPMyAdmin状态
    def getPHPMyAdminStatus(self):
        import re
        tmp = {}
        setupPath = '/www/server';
        configFile = setupPath + '/nginx/conf/nginx.conf';
        pauth = False
        pstatus = False
        phpversion = "54";
        if os.path.exists(configFile):
            conf = public.readFile(configFile);
            rep = "listen\s+([0-9]+)\s*;";
            rtmp = re.search(rep,conf);
            if rtmp:
                phpport = rtmp.groups()[0];
            
            if conf.find('AUTH_START') != -1: pauth = True;
            if conf.find(setupPath + '/stop') == -1: pstatus = True;
            configFile = setupPath + '/nginx/conf/enable-php.conf';
            if not os.path.exists(configFile): public.writeFile(configFile,public.readFile(setupPath + '/nginx/conf/enable-php-54.conf'));
            conf = public.readFile(configFile);
            rep = "php-cgi-([0-9]+)\.sock";
            rtmp = re.search(rep,conf);
            if rtmp:
                phpversion = rtmp.groups()[0];
            else:
                rep = "php-cgi.*\.sock";
                public.writeFile(configFile,conf);
                phpversion = '54';
        
        configFile = setupPath + '/apache/conf/extra/httpd-vhosts.conf';
        if os.path.exists(configFile):
            conf = public.readFile(configFile);
            rep = "php-cgi-([0-9]+)\.sock";
            rtmp = re.search(rep,conf);
            if rtmp:
                phpversion = rtmp.groups()[0];
            rep = "Listen\s+([0-9]+)\s*\n";
            rtmp = re.search(rep,conf);
            if rtmp:
                phpport = rtmp.groups()[0];
            if conf.find('AUTH_START') != -1: pauth = True;
            if conf.find('/www/server/stop') == -1: pstatus = True;
        
        try:
            vfile = setupPath + '/phpmyadmin/version.pl';
            if os.path.exists(vfile):
                tmp['version'] = public.readFile(vfile).strip();
                tmp['status'] = True;
                tmp['no'] = tmp['version'];
            else:
                tmp['version'] = "";
                tmp['status'] = False;
                tmp['no'] = "";
            
            tmp['run'] = pstatus;
            tmp['phpversion'] = phpversion;
            tmp['port'] = phpport;
            tmp['auth'] = pauth;
        except Exception as ex:
            tmp['status'] = False;
            tmp['error'] = str(ex);
        return tmp;
        
    #取PHP配置
    def GetPHPConfig(self,version):
        import re
        setupPath = '/www/server';
        file = setupPath + "/php/"+version+"/etc/php.ini"
        phpini = public.readFile(file)
        file = setupPath + "/php/"+version+"/etc/php-fpm.conf"
        phpfpm = public.readFile(file)
        data = {}
        try:
            rep = "upload_max_filesize\s*=\s*([0-9]+)M"
            tmp = re.search(rep,phpini).groups()
            data['max'] = tmp[0]
        except:
            data['max'] = '50'
        try:
            rep = "request_terminate_timeout\s*=\s*([0-9]+)\n"
            tmp = re.search(rep,phpfpm).groups()
            data['maxTime'] = tmp[0]
        except:
            data['maxTime'] = 0
        
        try:
            rep = u"\n;*\s*cgi\.fix_pathinfo\s*=\s*([0-9]+)\s*\n"
            tmp = re.search(rep,phpini).groups()
            
            if tmp[0] == '1':
                data['pathinfo'] = True
            else:
                data['pathinfo'] = False
        except:
            data['pathinfo'] = False
        
        return data
    
    #名取PID
    def getPid(self,pname):
        try:
            if not self.pids: self.pids = psutil.pids()
            for pid in self.pids:
                if psutil.Process(pid).name() == pname: return True;
            return False
        except: return True
    
    #检测指定进程是否存活
    def checkProcess(self,pid):
        try:
            if not self.pids: self.pids = psutil.pids()
            if int(pid) in self.pids: return True
            return False;
        except: return False
    
    #获取配置模板
    def getConfigHtml(self,get):
        filename = self.__install_path + '/' + get.name + '/index.html';
        if not os.path.exists(filename): return public.returnMsg(False,'PLUGIN_GET_HTML');
        srcBody = public.readFile(filename,'r')
        return srcBody
    
    #取插件信息
    def getPluginInfo(self,get):
        try:
            pluginInfo = self.GetFind(get.name)
            apacheVersion = ""
            try:
                apavFile = '/www/server/apache/version.pl';
                if os.path.exists(apavFile):
                    apacheVersion = public.readFile(apavFile).strip();
            except:
                pass;
            if pluginInfo['name'] == 'php':
                if apacheVersion == '2.2':
                    pluginInfo['versions'] = '5.2,5.3,5.4';
                elif apacheVersion == '2.4':
                    pluginInfo['versions'] = '5.3,5.4,5.5,5.6,7.0,7.1,7.2,7.3,7.4';
            
            pluginInfo['versions'] = self.checksSetup(pluginInfo['name'],pluginInfo['checks'],pluginInfo['versions'])
            if get.name == 'php':
                pluginInfo['phpSort'] = public.readFile('/www/server/php/sort.pl');
            return pluginInfo
        except:
            return False
    
    #取插件状态
    def getPluginStatus(self,get):
        find = self.GetFind(get.name);
        versions = [];
        path = '/www/server/php';
        for version in find['versions'].split(','):
            tmp = {}
            tmp['version'] = version
            if get.name == 'php':
                tmp['status'] = os.path.exists(path + '/' + version.replace(',','') + '/display.pl')
            else:
                tmp['status'] = find['status'];
            versions.append(tmp);
        return versions
    
    #设置插件状态
    def setPluginStatus(self,get):
        if get.name == 'php':
            isRemove = True
            path = '/www/server/php';
            if get.status == '0':
                versions = self.GetFind(get.name)['versions']
                os.system('rm -f ' + path + '/' + get.version.replace('.','') + '/display.pl');
                for version in versions.split(','):
                    if os.path.exists(path + '/' + version.replace('.','') + '/display.pl'):
                        isRemove = False;
                        break;
            else:
                public.writeFile(path + '/' + get.version.replace('.','') + '/display.pl','True');
            
            if isRemove:
                self.SetField(get.name, 'display', int(get.status))
        else:
            self.SetField(get.name, 'display', int(get.status))
        return public.returnMsg(True,'SET_SUCCESS');
    
    #从云端获取插件列表
    def getCloudPlugin(self,get):
        if session.get('getCloudPlugin') and get != None: return public.returnMsg(True,'您的插件列表已经是最新版本-1!');
        import json
        if not session.get('download_url'): session['download_url'] = 'http://download.bt.cn';
        
        #获取列表
        try:
            newUrl = public.get_url();
            if os.path.exists('plugin/beta/config.conf'):
                download_url = newUrl + '/install/list.json'
            else:
                download_url = newUrl + '/install/list_pro.json'
            data = json.loads(public.httpGet(download_url))
            session['download_url'] = newUrl;
        except:
            download_url = session['download_url'] + '/install/list_pro.json'
            data = json.loads(public.httpGet(download_url))
        
        n = i = j = 0;
        
        lists = self.GetList(None);
        
        for i in range(len(data)):
            for pinfo in lists:
                if data[i]['name'] != pinfo['name']: continue;
                data[i]['display'] = pinfo['display'];
            if data[i]['default']: 
                get.name = data[i]['name'];
                self.install(get);
        
        public.writeFile(self.__list,json.dumps(data));
        
        #获取分类
        try:
            download_url = session['download_url'] + '/install/type.json'
            types = json.loads(public.httpGet(download_url))
            public.writeFile(self.__type,json.dumps(types));
        except:
            pass;
        
        self.getCloudPHPExt(get);
        self.GetCloudWarning(get);
        session['getCloudPlugin'] = True;
        return public.returnMsg(True,'PLUGIN_UPDATE');
    
    #刷新缓存
    def flush_cache(self,get):
        self.getCloudPlugin(None);
        return public.returnMsg(True,'软件列表已更新!');
    
    #获取PHP扩展
    def getCloudPHPExt(self,get):
        import json
        try:
            if not session.get('download_url'): session['download_url'] = 'http://download.bt.cn';
            download_url = session['download_url'] + '/install/lib/phplib.json'
            tstr = public.httpGet(download_url)
            data = json.loads(tstr);
            if not data: return False;
            public.writeFile('data/phplib.conf',json.dumps(data));
            return True;
        except:
            return False;
        
    #获取警告列表
    def GetCloudWarning(self,get):
        import json
        if not session.get('download_url'): session['download_url'] = 'http://download.bt.cn';
        download_url = session['download_url'] + '/install/warning.json'
        tstr = public.httpGet(download_url)
        data = json.loads(tstr);
        if not data: return False;
        wfile = 'data/warning.json';
        wlist = json.loads(public.readFile(wfile));
        for i in range(len(data['data'])):
            for w in wlist['data']:
                if data['data'][i]['name'] != w['name']: continue;
                data['data'][i]['ignore_count'] = w['ignore_count'];
                data['data'][i]['ignore_time'] = w['ignore_time'];                         
        public.writeFile(wfile,json.dumps(data));
        return data;

    #名取标题
    def get_title_byname(self,get):
        get.sName = get.name
        find = self.get_soft_find(get)
        return find['title']

    
    
    #请求插件事件
    def a(self,get):
        if not hasattr(get,'name'): return public.returnMsg(False,'PLUGIN_INPUT_A');
        try:
            if not public.path_safe_check("%s/%s" % (get.name,get.s)): return public.returnMsg(False,'PLUGIN_INPUT_C');
            path = self.__install_path + '/' + get.name
            if not os.path.exists(path + '/'+get.name+'_main.py'): 
                if os.path.exists(path+'/index.php'):
                    import panelPHP
                    return panelPHP.panelPHP(get.name).exec_php_script(get)
                return public.returnMsg(False,'PLUGIN_INPUT_B');
            if not self.check_accept(get):return public.returnMsg(False,public.to_string([24744, 26410, 36141, 20080, 91, 37, 115, 93, 25110, 25480, 26435, 24050, 21040, 26399, 33]) % (self.get_title_byname(get),))
            sys.path.append(path);
            plugin_main = __import__(get.name+'_main');
            try:
                reload(plugin_main)
            except: pass
            pluginObject = eval('plugin_main.' + get.name + '_main()');
            if not hasattr(pluginObject,get.s): return public.returnMsg(False,'PLUGIN_INPUT_C',(get.s,));
            execStr = 'pluginObject.' + get.s + '(get)'
            return eval(execStr);
        except Exception as ex:
            import traceback
            errorMsg = traceback.format_exc();
            public.submit_error(errorMsg)
            return public.returnMsg(False,'抱歉，出错了：<br> %s ' % errorMsg.replace('\n','<br>'))

    
    #上传插件包
    def update_zip(self,get = None,tmp_file = None, update = False):
        tmp_path = '/www/server/panel/temp'
        if not os.path.exists(tmp_path): 
            os.makedirs(tmp_path,mode=384)

        if tmp_file: 
            if not os.path.exists(tmp_file): return public.returnMsg(False,'文件下载失败!')

        
        if get:
            public.ExecShell("rm -rf " + tmp_path + '/*')
            tmp_file = tmp_path + '/plugin_tmp.zip'
            from werkzeug.utils import secure_filename
            from flask import request
            f = request.files['plugin_zip']
            if f.filename[-4:] != '.zip': tmp_file = tmp_path + '/plugin_tmp.tar.gz'

            f.save(tmp_file)


        import panelTask
        panelTask.bt_task()._unzip(tmp_file,tmp_path,'','/dev/null')
        os.remove(tmp_file)
        p_info = tmp_path + '/info.json'
        if not os.path.exists(p_info):
            d_path = None
            for df in os.walk(tmp_path):
                if len(df[2]) < 3: continue
                if not 'info.json' in df[2]: continue
                if not 'install.sh' in df[2]: continue
                if not os.path.exists(df[0] + '/info.json'): continue
                d_path = df[0]
            if d_path: 
                tmp_path = d_path
                p_info = tmp_path + '/info.json'
        try:
            try:
                data = json.loads(public.ReadFile(p_info))
            except:
                data = json.loads(public.ReadFile(p_info).decode('utf-8-sig'))
            data['size'] = public.get_path_size(tmp_path)
            if not 'author' in data: data['author'] = '未知'
            if not 'home' in data: data['home'] = 'https://www.bt.cn/bbs/forum-40-1.html'

            plugin_path = '/www/server/panel/plugin/' + data['name'] + '/info.json'
            data['old_version'] = '0'
            data['tmp_path'] = tmp_path
            if os.path.exists(plugin_path):
                try:
                    old_info = json.loads(public.ReadFile(plugin_path))
                    data['old_version'] = old_info['versions']
                except:pass
        except:
            public.ExecShell("rm -rf " + tmp_path + '/*')
            return public.returnMsg(False,'在压缩包中没有找到插件信息,请检查插件包!');

        data['update'] = update
        return data

    #导入插件包
    def input_zip(self,get):
        if not os.path.exists(get.tmp_path): return public.returnMsg(False,'临时文件不存在,请重新上传!')
        plugin_path = '/www/server/panel/plugin/' + get.plugin_name
        if not os.path.exists(plugin_path): os.makedirs(plugin_path)
        public.ExecShell("\cp -a -r " + get.tmp_path + '/* ' + plugin_path + '/')
        public.ExecShell('chmod -R 600 ' + plugin_path)
        public.ExecShell('cd ' + plugin_path + ' && bash install.sh install')
        p_info = public.ReadFile(plugin_path + '/info.json')
        public.ExecShell("rm -rf /www/server/panel/temp/*")
        if p_info:
            public.WriteLog('软件管理','安装第三方插件[%s]' % json.loads(p_info)['title'])
            return public.returnMsg(True,'安装成功!')
        public.ExecShell("rm -rf " + plugin_path)
        return public.returnMsg(False,'安装失败!')
        

    #导出插件包
    def export_zip(self,get):
        plugin_path = '/www/server/panel/plugin/' + get.plugin_name
        if not os.path.exists(plugin_path): return public.returnMsg(False,'指定插件不存在!')
        
        get.sfile = plugin_path + '/'
        get.dfile = '/www/server/panel/temp/bt_plugin_' + get.plugin_name + '.zip'
        get.type = 'zip'
        import files
        files.files().Zip(get)
        if not os.path.exists(get.dfile): return public.returnMsg(False,'导出失败,请检查权限!')
        return public.returnMsg(True,get.dfile)