#coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: 黄文良 <287962566@qq.com>
# +-------------------------------------------------------------------
#+--------------------------------------------------------------------
#|   宝塔防篡改程序
#+--------------------------------------------------------------------
import os,sys,public,json,time

class tamper_proof_init:
    __plugin_path = '/www/server/panel/plugin/tamper_proof'
    __sites = None

    def get_index(self,get):
        self.sync_sites(get)
        day = None
        if hasattr(get,'day'): day = get.day
        data = {}
        data['open'] = self.get_service_status(None)
        data['sites'] = self.get_sites(None)
        data['total'] = self.get_total()
        for i in range(len(data['sites'])):
            data['sites'][i]['total'] = self.get_total(data['sites'][i]['siteName'],day)
        return data

    def get_sites(self,get = None):
        if self.__sites: return self.__sites
        data = json.loads(public.readFile(self.__plugin_path + '/sites.json'))
        self.__sites = data
        return data

    def get_site_find(self,get):
        return self.__get_find(get.siteName)

    def __get_find(self,siteName):
        data = self.get_sites(None)
        for siteInfo in data:
            if siteName == siteInfo['siteName']: return siteInfo
        return None

    def save_site_config(self,siteInfo):
        data = self.get_sites(None)
        for i in range(len(data)):
            if data[i]['siteName'] != siteInfo['siteName']: continue
            data[i] = siteInfo
            break
        self.write_sites(data)

    def write_sites(self,data):
        public.writeFile(self.__plugin_path + '/sites.json',json.dumps(data))
        os.system('/etc/init.d/bt_tamper_proof restart')


    def service_admin(self,get):
        m_logs = {'start':'启动','stop':'停止','restart':'重启'}
        os.system('/etc/init.d/bt_tamper_proof %s' % get.serviceStatus)
        self.write_log('%s防篡改服务' % m_logs[get.serviceStatus])
        return public.returnMsg(True,u'操作成功!')

    def get_service_status(self,get):
        result = public.ExecShell("/etc/init.d/bt_tamper_proof status|grep already")
        return (len(result[0]) > 3)

    def set_site_status(self,get):
        siteInfo = self.get_site_find(get)
        if not siteInfo: return public.returnMsg(False,u'指定站点不存在!')
        siteInfo['open'] = not siteInfo['open']
        self.save_site_config(siteInfo)
        m_logs = {True:'开启',False:'关闭'}
        self.write_log('%s站点[%s]防篡改保护' % (m_logs[siteInfo['open']],siteInfo['siteName']))
        return public.returnMsg(True,u'设置成功!')

    def add_excloud(self,get):
        if get.excludePath.find('/') != -1: return public.returnMsg(False,u'目录名称不能包含[/]')
        siteInfo = self.get_site_find(get)
        if not siteInfo: return public.returnMsg(False,u'指定站点不存在!')
        get.excludePath = get.excludePath.lower()
        if get.excludePath in siteInfo['excludePath']: return public.returnMsg(False,u'指定目录已在排除列表!')
        siteInfo['excludePath'].insert(0,get.excludePath)
        self.save_site_config(siteInfo)
        self.write_log('站点[%s]添加排除目录名[%s]到排除列表' % (siteInfo['siteName'],get.excludePath))
        return public.returnMsg(True,u'添加成功!')

    def remove_excloud(self,get):
        siteInfo = self.get_site_find(get)
        if not siteInfo: return public.returnMsg(False,u'指定站点不存在!')
        if not get.excludePath in siteInfo['excludePath']: return public.returnMsg(False,u'指定目录不在排除列表!')
        siteInfo['excludePath'].remove(get.excludePath)
        self.save_site_config(siteInfo)
        self.write_log('站点[%s]从排除列表中删除目录名[%s]' % (siteInfo['siteName'],get.excludePath))
        return public.returnMsg(True,u'删除成功!')

    def add_protect_ext(self,get):
        if get.protectExt.find('.') != -1: return public.returnMsg(False,u'扩展名称不能包含[.]')
        siteInfo = self.get_site_find(get)
        if not siteInfo: return public.returnMsg(False,u'指定站点不存在!')
        get.protectExt = get.protectExt.lower()
        if get.protectExt in siteInfo['protectExt']: return public.returnMsg(False,u'指定文件类型已在受保护列表!')
        siteInfo['protectExt'].insert(0,get.protectExt)
        self.save_site_config(siteInfo)
        self.write_log('站点[%s]添加文件类型[.%s]到受保护的文件类型列表' % (siteInfo['siteName'],get.protectExt))
        return public.returnMsg(True,u'添加成功!')

    def remove_protect_ext(self,get):
        siteInfo = self.get_site_find(get)
        if not siteInfo: return public.returnMsg(False,u'指定站点不存在!')
        if not get.protectExt in siteInfo['protectExt']: return public.returnMsg(False,u'指定文件类型不在受保护列表!')
        siteInfo['protectExt'].remove(get.protectExt)
        self.save_site_config(siteInfo)
        self.write_log('站点[%s]从受保护的文件类型列表中删除文件类型[.%s]' % (siteInfo['siteName'],get.protectExt))
        return public.returnMsg(True,u'删除成功!')

    def sync_sites(self,get):
        data = self.get_sites(None)
        sites = public.M('sites').field('name,path').select()
        config = json.loads(public.readFile(self.__plugin_path + '/config.json'))
        names = []
        n = 0
        for siteTmp in sites:
            names.append(siteTmp['name'])
            siteInfo = self.__get_find(siteTmp['name'])
            if siteInfo:
                if siteInfo['path'] != siteTmp['path']:
                    siteInfo['path'] = siteTmp['path']
                    self.save_site_config(siteInfo)
                    data = self.get_sites()
                    
                continue
            siteInfo = {}
            siteInfo['siteName'] = siteTmp['name']
            siteInfo['path'] = siteTmp['path']
            siteInfo['open'] = False
            siteInfo['excludePath'] = config['excludePath']
            siteInfo['protectExt'] = config['protectExt']
            data.append(siteInfo)
            n +=1

        newData = []
        for siteInfoTmp in data:
            if siteInfoTmp['siteName'] in names:
                newData.append(siteInfoTmp)
            else:
                os.system("rm -rf " + self.__plugin_path + '/sites/' + siteInfoTmp['siteName'])
                n+=1
        if n > 0: self.write_sites(newData)
        self.__sites = None

    def get_total(self,siteName = None,day=None):
        defaultTotal = {"total":0,"delete":0,"create":0,"modify":0,"move":0}
        if siteName:
            total = {}
            total['site'] = public.readFile(self.__plugin_path + '/sites/'+siteName+'/total/total.json')
            if total['site']: 
                total['site'] = json.loads(total['site'])
            else:
                total['site'] = defaultTotal
            if not day: day = time.strftime("%Y-%m-%d",time.localtime())
            total['day'] = public.readFile(self.__plugin_path + '/sites/'+siteName + '/total/' + day + '/total.json')
            if total['day']: 
                total['day'] = json.loads(total['day'])
            else:
                total['day'] = defaultTotal
        else:
            filename = self.__plugin_path + '/sites/total.json'
            if os.path.exists(filename):
                total = json.loads(public.readFile(filename))
            else:
                total = defaultTotal
        return total

    def get_days(self,path):
        days = []
        if not os.path.exists(path): os.makedirs(path)
        for dirname in os.listdir(path):
            if dirname == '..' or dirname == '.' or dirname == 'total.json': continue
            if not os.path.isdir(path + '/' + dirname): continue
            days.append(dirname)
        days = sorted(days,reverse=True)
        return days

    #取文件指定尾行数
    def GetNumLines(self,path,num,p=1):
        pyVersion = sys.version_info[0]
        try:
            import cgi
            if not os.path.exists(path): return "";
            start_line = (p - 1) * num;
            count = start_line + num;
            fp = open(path,'rb')
            buf = ""
            fp.seek(-1, 2)
            if fp.read(1) == "\n": fp.seek(-1, 2)
            data = []
            b = True
            n = 0;
            for i in range(count):
                while True:
                    newline_pos = str.rfind(str(buf), "\n")
                    pos = fp.tell()
                    if newline_pos != -1:
                        if n >= start_line:
                            line = buf[newline_pos + 1:]
                            try:
                                data.append(json.loads(cgi.escape(line)))
                            except: pass
                        buf = buf[:newline_pos]
                        n += 1;
                        break;
                    else:
                        if pos == 0:
                            b = False
                            break
                        to_read = min(4096, pos)
                        fp.seek(-to_read, 1)
                        t_buf = fp.read(to_read)
                        if pyVersion == 3:
                            if type(t_buf) == bytes: t_buf = t_buf.decode('utf-8')
                        buf = t_buf + buf
                        fp.seek(-to_read, 1)
                        if pos - to_read == 0:
                            buf = "\n" + buf
                if not b: break;
            fp.close()
        except: return []
        if len(data) >= 2000:
            arr = []
            for d in data:
                arr.insert(0,json.dumps(d))
            public.writeFile(path,"\n".join(arr))
        return data

    def get_safe_logs(self,get):
        data = {}
        path = self.__plugin_path + '/sites/'+get.siteName + '/total'
        data['days'] = self.get_days(path)
        if not data['days']: 
            data['logs'] = []
        else:
            if not 'p' in get: get.p = 1
            day =  data['days'][0]
            if hasattr(get,'day'): day = get.day
            data['get_day'] = day
            data['logs'] = self.GetNumLines(path + '/' + day + '/logs.json',2000,int(get.p))
        return data

    def get_logs(self,get):
        import page
        page = page.Page();
        count = public.M('logs').where('type=?',(u'防篡改程序',)).count();
        limit = 12;
        info = {}
        info['count'] = count
        info['row']   = limit
        info['p'] = 1
        if hasattr(get,'p'):
            info['p']    = int(get['p'])
        info['uri']      = {}
        info['return_js'] = ''
        if hasattr(get,'tojs'):
            info['return_js']   = get.tojs
        data = {}
        data['page'] = page.GetPage(info,'1,2,3,4,5');
        data['data'] = public.M('logs').where('type=?',(u'防篡改程序',)).order('id desc').limit(str(page.SHIFT)+','+str(page.ROW)).field('log,addtime').select();
        return data;

    def write_log(self,log):
        public.WriteLog('防篡改程序',log)



