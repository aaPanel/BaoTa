# coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2016  宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: hwliang <hwl@bt.  cn>
# +-------------------------------------------------------------------
from datetime import datetime, timezone

from flask import session, request, Response

import public, os, json, time, apache, psutil
from mod.base.json_util import SrcFieldJSONEncoder, SrcField


class ajax:
    def GetApacheStatus(self, get):
        a = apache.apache()
        return a.GetApacheStatus()
    
    def GetProcessCpuPercent(self, i, process_cpu):
        try:
            pp = psutil.Process(i)
            if pp.name() not in process_cpu.keys():
                process_cpu[pp.name()] = float(pp.cpu_percent(interval=0.01))
            process_cpu[pp.name()] += float(pp.cpu_percent(interval=0.01))
        except:
            pass
    
    def GetNginxStatus(self, get):
        try:
            if not os.path.exists('/www/server/nginx/sbin/nginx'):
                return public.returnMsg(False, '未安装nginx')
            process_cpu = {"nginx": 0}
            nginx_pid = public.readFile('/www/server/nginx/logs/nginx.pid')
            pro_list = []
            try:
                pro = psutil.Process(int(nginx_pid))
                pro_list = pro.children()
                pro_list = [i for i in pro_list if "worker" in ''.join(i.cmdline())]
            except:
                pass
            worker = len(pro_list)
            workermen = int(sum([int(i.memory_info().rss) for i in pro_list])) / 1024 / 1024
            from BTPanel import cache
            if pro_list:
                old_ngixn_cpu = cache.get('nginx_cpu')
                _cpu = 0
                for pp in pro_list:
                    c = pp.cpu_times()
                    for s in c: _cpu += s
                s = psutil.cpu_times()
                now_all_cpu = 0
                for i in s: now_all_cpu += i
                if old_ngixn_cpu:
                    process_cpu['nginx'] = 100.00 * (_cpu - old_ngixn_cpu['nginx_cpu']) / (now_all_cpu - old_ngixn_cpu['all_cpu'])
                cache.set('nginx_cpu', {'nginx_cpu': _cpu, 'all_cpu':now_all_cpu}, 600)
                
            # 取Nginx负载状态
            self.CheckStatusConf()
            result = public.httpGet('http://127.0.0.1/nginx_status')
            
            is_curl = False
            tmp = []
            if result:
                tmp = result.split()
            if len(tmp) < 15: is_curl = True
            
            if is_curl:
                result = public.ExecShell(
                    'curl http://127.0.0.1/nginx_status')[0]
                tmp = result.split()
            data = {}
            if "request_time" in tmp:
                data['accepts'] = tmp[8]
                data['handled'] = tmp[9]
                data['requests'] = tmp[10]
                data['Reading'] = tmp[13]
                data['Writing'] = tmp[15]
                data['Waiting'] = tmp[17]
            else:
                data['accepts'] = tmp[8]
                data['handled'] = tmp[7]
                data['requests'] = tmp[9]
                data['Reading'] = tmp[11]
                data['Writing'] = tmp[13]
                data['Waiting'] = tmp[15]
            data['active'] = tmp[2]
            data['worker'] = worker
            data['workercpu'] = round(float(process_cpu["nginx"]), 2)
            data['workermen'] = "%s%s" % (int(workermen), "MB")
            return data
        except Exception as ex:
            public.print_log(public.get_error_info())
            public.WriteLog('信息获取', "Nginx负载状态获取失败: %s" % ex)
            return public.returnMsg(False, '数据获取失败,检查nginx状态是否正常!')
    
    def GetPHPStatus(self, get):
        # 取指定PHP版本的负载状态
        try:
            version = get.version
            uri = "/phpfpm_" + version + "_status?json"
            result = public.request_php(version, uri, '')
            tmp = json.loads(result)
            fTime = time.localtime(int(tmp['start time']))
            tmp['start time'] = time.strftime('%Y-%m-%d %H:%M:%S', fTime)
            return tmp
        except Exception as ex:
            public.WriteLog('信息获取',
                            "PHP负载状态获取失败: {}".format(public.get_error_info()))
            return public.returnMsg(False, '负载状态获取失败!')
    
    def CheckStatusConf(self):
        if public.get_webserver() != 'nginx': return
        filename = session[
                       'setupPath'] + '/panel/vhost/nginx/phpfpm_status.conf'
        if os.path.exists(filename):
            if public.ReadFile(filename).find('nginx_status') != -1: return
        
        conf = '''server {
    listen 80;
    server_name 127.0.0.1;
    allow 127.0.0.1;
    location /nginx_status {
        stub_status on;
        access_log off;
    }
}'''
        
        public.writeFile(filename, conf)
        public.serviceReload()
    
    def GetTaskCount(self, get):
        # 取任务数量
        return public.M('tasks').where("status!=?", ('1',)).count()
    
    """
    @name 下载json文件
    """
    
    def download_json_files(self, url, path):
        try:
            res = json.loads(public.httpGet(url))
            if type(res) == dict:
                public.writeFile(path, json.dumps(res))
        except:
            pass
        return True
    
    def _get_jdk_status(self):
        
        # 获取本机系统架构
        import platform
        arce = platform.machine()
        if arce == 'x86_64':
            arce = 'x64'
        elif arce == 'aarch64' or 'arm' in arce:
            arce = 'arm'
        if arce not in ['x64', 'arm']:
            return {
                "name": "jdk",
                "check": "/usr/local/java/VERSION/bin/java",
                "msg": "Java 语言是一种通用的、面向对象的编程语言",
                "shell": "java.sh",
                "task": "1",
                "type": "语言解释器",
                "versions": []
            }
        default_versions = {
            "x64": [
                "jdk1.7.0_80",
                "jdk1.8.0_371",
                "jdk-9.0.4",
                "jdk-10.0.2",
                "jdk-11.0.19",
                "jdk-12.0.2",
                "jdk-13.0.2",
                "jdk-14.0.2",
                "jdk-15.0.2",
                "jdk-16.0.2",
                "jdk-17.0.8",
                "jdk-18.0.2.1",
                "jdk-19.0.2",
                "jdk-20.0.2"
            ],
            "arm": [
                "jdk1.8.0_371",
                "jdk-11.0.19",
                "jdk-15.0.2",
                "jdk-16.0.2",
                "jdk-17.0.8",
                "jdk-18.0.2.1",
                "jdk-19.0.2",
                "jdk-20.0.2"
            ]
        }
        skey = 'is_down_jdk'
        tmp_file = '/www/server/panel/data/jdk.json'
        download_url = '{}/src/jdk/jdk.json'.format(public.get_url())
        if not skey in session:
            public.run_thread(self.download_json_files, (download_url, tmp_file))
            session[skey] = True
        try:
            versions = json.loads(public.readFile(tmp_file))[arce]
        except:
            public.run_thread(self.download_json_files, (download_url, tmp_file))
            versions = default_versions[arce]
        
        data = {
            "name": "jdk",
            "check": "/usr/local/java/VERSION/bin/java",
            "msg": "Java 语言是一种通用的、面向对象的编程语言",
            "shell": "java.sh",
            "task": "1",
            "type": "语言解释器",
            "versions": [
                {"status": True if os.path.exists('/www/server/java/' + i) else False, "version": i}
                for i in versions]
        }
        return data
    
    def GetSoftList(self, get):
        # 取软件列表
        import json, os
        tmp = public.readFile('data/softList.conf')
        try:
            data = json.loads(tmp)
        except:
            data = []
        tasks = public.M('tasks').where("status!=?",
                                        ('1',)).field('status,name').select()
        for i in range(len(data)):
            data[i]['check'] = public.GetConfigValue(
                'root_path') + '/' + data[i]['check']
            for n in range(len(data[i]['versions'])):
                # 处理任务标记
                isTask = '1'
                for task in tasks:
                    tmp = public.getStrBetween('[', ']', task['name'])
                    if not tmp: continue
                    tmp1 = tmp.split('-')
                    if data[i]['name'] == 'PHP':
                        if tmp1[0].lower() == data[i]['name'].lower(
                        ) and tmp1[1] == data[i]['versions'][n]['version']:
                            isTask = task['status']
                    else:
                        if tmp1[0].lower() == data[i]['name'].lower():
                            isTask = task['status']
                
                # 检查安装状态
                if data[i]['name'] == 'PHP':
                    data[i]['versions'][n]['task'] = isTask
                    checkFile = data[i]['check'].replace(
                        'VERSION',
                        data[i]['versions'][n]['version'].replace('.', ''))
                else:
                    data[i]['task'] = isTask
                    version = public.readFile(
                        public.GetConfigValue('root_path') + '/server/' +
                        data[i]['name'].lower() + '/version.pl')
                    if not version: continue
                    if version.find(data[i]['versions'][n]['version']) == -1:
                        continue
                    checkFile = data[i]['check']
                data[i]['versions'][n]['status'] = os.path.exists(checkFile)
        data.append(self._get_jdk_status())
        return data
    
    def GetLibList(self, get):
        # 取插件列表
        import json, os
        tmp = public.readFile('data/libList.conf')
        data = json.loads(tmp)
        for i in range(len(data)):
            data[i]['status'] = self.CheckLibInstall(data[i]['check'])
            data[i]['optstr'] = self.GetLibOpt(data[i]['status'],
                                               data[i]['opt'])
        return data
    
    def CheckLibInstall(self, checks):
        for cFile in checks:
            if os.path.exists(cFile): return '已安装'
        return '未安装'
    
    # 取插件操作选项
    def GetLibOpt(self, status, libName):
        optStr = ''
        if status == '未安装':
            optStr = '<a class="link" href="javascript:InstallLib(\'' + libName + '\');">安装</a>'
        else:
            libConfig = '配置'
            if (libName == 'beta'): libConfig = '内测资料'
            
            optStr = '<a class="link" href="javascript:SetLibConfig(\'' + libName + '\');">' + libConfig + '</a> | <a class="link" href="javascript:UninstallLib(\'' + libName + '\');">卸载</a>'
        return optStr
    
    # 取插件AS
    def GetQiniuAS(self, get):
        filename = public.GetConfigValue(
            'setup_path') + '/panel/data/' + get.name + 'As.conf'
        if not os.path.exists(filename): public.writeFile(filename, '')
        data = {}
        data['AS'] = public.readFile(filename).split('|')
        data['info'] = self.GetLibInfo(get.name)
        if len(data['AS']) < 3:
            data['AS'] = ['', '', '', '']
        return data
    
    # 设置插件AS
    def SetQiniuAS(self, get):
        info = self.GetLibInfo(get.name)
        filename = public.GetConfigValue(
            'setup_path') + '/panel/data/' + get.name + 'As.conf'
        conf = get.access_key.strip() + '|' + get.secret_key.strip(
        ) + '|' + get.bucket_name.strip() + '|' + get.bucket_domain.strip()
        public.writeFile(filename, conf)
        public.ExecShell("chmod 600 " + filename)
        result = public.ExecShell(public.get_python_bin() + " " +
                                  public.GetConfigValue('setup_path') +
                                  "/panel/script/backup_" + get.name +
                                  ".py list")
        
        if result[0].find("ERROR:") == -1:
            public.WriteLog("插件管理", "设置插件[" + info['name'] + "]AS!")
            return public.returnMsg(True, '设置成功!')
        return public.returnMsg(
            False,
            'ERROR: 无法连接到' + info['name'] + '服务器,请检查[AK/SK/存储空间]设置是否正确!')
    
    # 设置内测
    def SetBeta(self, get):
        data = {}
        data['username'] = get.bbs_name
        data['qq'] = get.qq
        data['email'] = get.email
        result = public.httpPost(
            public.GetConfigValue('home') + '/Api/LinuxBeta', data)
        import json
        data = json.loads(result)
        if data['status']:
            public.writeFile('data/beta.pl',
                             get.bbs_name + '|' + get.qq + '|' + get.email)
        return data
    
    # 取内测资格状态
    def GetBetaStatus(self, get):
        try:
            return public.readFile('data/beta.pl').strip()
        except:
            return 'False'
    
    # 获取指定插件信息
    def GetLibInfo(self, name):
        import json
        tmp = public.readFile('data/libList.conf')
        data = json.loads(tmp)
        for lib in data:
            if name == lib['opt']: return lib
        return False
    
    # 获取文件列表
    def GetQiniuFileList(self, get):
        try:
            import json
            result = public.ExecShell(public.get_python_bin() + " " +
                                      public.GetConfigValue('setup_path') +
                                      "/panel/script/backup_" + get.name +
                                      ".py list")
            return json.loads(result[0])
        except:
            return public.returnMsg(False, '获取列表失败,请检查[AK/SK/存储空间]设是否正确!')
    
    # 取网络连接列表
    def GetNetWorkList(self, get):
        import psutil
        netstats = psutil.net_connections()
        networkList = []
        for netstat in netstats:
            tmp = {}
            if netstat.type == 1:
                tmp['type'] = 'tcp'
            else:
                tmp['type'] = 'udp'
            tmp['family'] = netstat.family
            tmp['laddr'] = netstat.laddr
            tmp['raddr'] = netstat.raddr
            tmp['status'] = netstat.status
            p = psutil.Process(netstat.pid)
            tmp['process'] = p.name()
            tmp['pid'] = netstat.pid
            networkList.append(tmp)
            del (p)
            del (tmp)
        networkList = sorted(networkList,
                             key=lambda x: x['status'],
                             reverse=True)
        return networkList
    
    # 取进程列表
    def GetProcessList(self, get):
        import psutil, pwd
        Pids = psutil.pids()
        
        processList = []
        for pid in Pids:
            try:
                tmp = {}
                p = psutil.Process(pid)
                if p.exe() == "": continue
                
                tmp['name'] = p.name()
                # 进程名称
                if self.GoToProcess(tmp['name']): continue
                
                tmp['pid'] = pid
                # 进程标识
                tmp['status'] = p.status()
                # 进程状态
                tmp['user'] = p.username()
                # 执行用户
                cputimes = p.cpu_times()
                tmp['cpu_percent'] = p.cpu_percent(0.1)
                tmp['cpu_times'] = cputimes.user  # 进程占用的CPU时间
                tmp['memory_percent'] = round(p.memory_percent(),
                                              3)  # 进程占用的内存比例
                pio = p.io_counters()
                tmp['io_write_bytes'] = pio.write_bytes  # 进程总共写入字节数
                tmp['io_read_bytes'] = pio.read_bytes  # 进程总共读取字节数
                tmp['threads'] = p.num_threads()  # 进程总线程数
                
                processList.append(tmp)
                del (p)
                del (tmp)
            except:
                continue
        import operator
        processList = sorted(processList,
                             key=lambda x: x['memory_percent'],
                             reverse=True)
        processList = sorted(processList,
                             key=lambda x: x['cpu_times'],
                             reverse=True)
        return processList
    
    # 结束指定进程
    def KillProcess(self, get):
        # return public.returnMsg(False,'演示服务器，禁止此操作!');
        import psutil
        p = psutil.Process(int(get.pid))
        name = p.name()
        if name == 'python': return public.returnMsg(False, 'KILL_PROCESS_ERR')
        
        p.kill()
        public.WriteLog('TYPE_PROCESS', 'KILL_PROCESS', (get.pid, name))
        return public.returnMsg(True, 'KILL_PROCESS', (get.pid, name))
    
    def GoToProcess(self, name):
        ps = [
            'sftp-server', 'login', 'nm-dispatcher', 'irqbalance', 'qmgr',
            'wpa_supplicant', 'lvmetad', 'auditd', 'master', 'dbus-daemon',
            'tapdisk', 'sshd', 'init', 'ksoftirqd', 'kworker', 'kmpathd',
            'kmpath_handlerd', 'python', 'kdmflush', 'bioset', 'crond',
            'kthreadd', 'migration', 'rcu_sched', 'kjournald', 'iptables',
            'systemd', 'network', 'dhclient', 'systemd-journald',
            'NetworkManager', 'systemd-logind', 'systemd-udevd', 'polkitd',
            'tuned', 'rsyslogd'
        ]
        
        for key in ps:
            if key == name: return True
        
        return False
    
    def GetNetWorkIo(self, get):
        # 取指定时间段的网络Io
        try:
            len_data = (int(get.end) - int(get.start)) / 60
            filter_str = ""
            if len_data > 15000:
                filter_str = "AND id % 15 = 0"
            elif len_data > 1500:
                filter_str = "AND id % 3 = 0"
            data = public.M('network').dbfile('system').where(
                "addtime>=? AND addtime<=? {}".format(filter_str), (get.start, get.end)
            ).field(
                'id,up,down,total_up,total_down,down_packets,up_packets,addtime'
            ).order('id desc').select()
            for value in data:
                value['addtime'] = time.strftime('%m/%d %H:%M', time.localtime(float(value['addtime'])))
                value['down_packets'] = SrcField(value['down_packets'])
                value['up_packets'] = SrcField(value['up_packets'])
            resp = Response(json.dumps(data, cls=SrcFieldJSONEncoder), content_type='application/json')
            return resp
        except Exception as e:
            if "no such table" in str(e):
                import db
                _sql = db.Sql().dbfile('system')
                csql = '''
CREATE TABLE IF NOT EXISTS `network` (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `up` INTEGER,
  `down` INTEGER,
  `total_up` INTEGER,
  `total_down` INTEGER,
  `down_packets` INTEGER,
  `up_packets` INTEGER,
  `addtime` INTEGER
);'''
                _sql.execute(csql, ())
                _sql.close()
            return []
    
    def GetDiskIo(self, get):
        # 取指定时间段的磁盘Io
        tmp_cols = public.M('diskio').dbfile('system').query('PRAGMA table_info(diskio)', ())

        fields = []
        for col in tmp_cols:
            if len(col) > 2:
                fields.append(col[1])
        fields.append("disk_top")

        filter_str = ""
        len_data = (int(get.end) - int(get.start)) / 60
        if len_data > 15000:
            filter_str = "AND diskio.id % 15 = 0"
        elif len_data > 1500:
            filter_str = "AND diskio.id % 3 = 0"
        data = public.M('diskio').dbfile('system').query(
            "SELECT diskio.*,process_top_list.disk_top from diskio inner join process_top_list on diskio.addtime=process_top_list.addtime where diskio.addtime>={} AND diskio.addtime<={} {} ORDER BY diskio.addtime desc;"
            .format(get.start, get.end, filter_str), ())
        if isinstance(data, str) and data.find('error: no such table: process_top_list') != -1:
            return public.M('diskio').dbfile('system').where(
                "addtime>=? AND addtime<=?", (get.start, get.end)
            ).order('id asc').select()

        try:
            def data_zip(x):
                x[-1] = SrcField(x[-1])
                x[7] = time.strftime('%m/%d %H:%M', time.localtime(float(x[7])))
                return dict(zip(fields, x))

            data = list(map(data_zip, data))
            resp = Response(json.dumps(data, cls=SrcFieldJSONEncoder), content_type='application/json')
            return resp
        except:
            return []
        # t3 = time.time()
        # public.print_log("iter_time:", (t3 - t2) *1000, "ms")
        # data = self.ToAddtime(data, True, 'disk')
        # t4 = time.time()
        # public.print_log("format_time:", (t4 - t3) *1000, "ms")
        # public.print_log("total_time:", (t4 - t) *1000, "ms")
        # return data
    
    def __format_field(self, field):
        import re
        fields = []
        for key in field:
            s_as = re.search(r'\s+as\s+', key, flags=re.IGNORECASE)
            if s_as:
                as_tip = s_as.group()
                key = key.split(as_tip)[1]
            fields.append(key)
        return fields
    
    def GetCpuIo(self, get):
        # 取指定时间段的CpuIo
        panel_path = public.get_panel_path()
        data_path = "{}/data/sql_index.pl".format(panel_path)
        if not os.path.exists(data_path):
            self.create_sql_index()

        db_obj = public.M('cpuio').dbfile('system')
        tmp_cols = db_obj.query('PRAGMA table_info(cpuio)', ())
        if db_obj.ERR_INFO:
            return []

        fields = []
        for col in tmp_cols:
            if len(col) > 2:
                fields.append(col[1])
        fields.append("cpu_top")
        fields.append("memory_top")

        # 抽样减少返回的数据量
        filter_str = ""
        len_data = (int(get.end) - int(get.start)) / 60
        if len_data > 15000:
            filter_str = "AND cpuio.id % 15 = 0"
        elif len_data > 1500:
            filter_str = "AND cpuio.id % 3 = 0"

        data = public.M('cpuio').dbfile('system').query(
            "SELECT cpuio.*,process_top_list.cpu_top,process_top_list.memory_top from cpuio inner join process_top_list on cpuio.addtime=process_top_list.addtime where cpuio.addtime>={} AND cpuio.addtime<={} {} ORDER BY cpuio.addtime desc;"
            .format(get.start, get.end, filter_str), ())

        if isinstance(data, str) and data.find(
            'error: no such table: process_top_list') != -1:
            return public.M('cpuio').dbfile('system').where(
                "addtime>=? AND addtime<=?",
                (get.start, get.end
                 )).field('id,pro,mem,addtime').order('id asc').select()
        try:
            m_pre = (psutil.virtual_memory().total / 1024 / 1024) / 100

            def data_zip(x):
                x[-1] = SrcField(x[-1])
                x[-2] = SrcField(x[-2])
                x[3] = time.strftime('%m/%d %H:%M', time.localtime(float(x[3])))
                if x[2] > 100:
                    x[2] = int(x[2]) / m_pre
                return dict(zip(fields, x))

            data = list(map(data_zip, data))
            resp = Response(json.dumps(data, cls=SrcFieldJSONEncoder), content_type='application/json')
            return resp

        except:
            return []
    
    def get_load_average(self, get):
        db_obj = public.M('load_average').dbfile('system')
        tmp_cols = db_obj.query('PRAGMA table_info(load_average)', ())
        
        if db_obj.ERR_INFO:
            return []

        fields = []
        for col in tmp_cols:
            if len(col) > 2:
                fields.append(col[1])
        fields.append("cpu_top")

        filter_str = ""
        len_data = (int(get.end) - int(get.start)) / 60
        if len_data > 15000:
            filter_str = "AND load_average.id % 15 = 0"
        elif len_data > 1500:
            filter_str = "AND load_average.id % 3 = 0"

        public.print_log("filter_str:", filter_str)
        data = public.M('load_average').dbfile('system').query(
            "SELECT load_average.*,process_top_list.cpu_top from load_average inner join process_top_list on load_average.addtime=process_top_list.addtime where load_average.addtime>={} AND load_average.addtime<={} {} ORDER BY load_average.addtime desc;"
            .format(get.start, get.end, filter_str), ())
        if isinstance(data, str) and data.find(
            'error: no such table: process_top_list') != -1:
            return public.M('load_average').dbfile('system').where(
                "addtime>=? AND addtime<=?", (get.start, get.end)
            ).field('id,pro,one,five,fifteen,addtime').order('id asc').select()

        try:
            def data_zip(x):
                x[-1] = SrcField(x[-1])
                x[5] = time.strftime('%m/%d %H:%M', time.localtime(float(x[5])))
                return dict(zip(fields, x))
            data = list(map(data_zip, data))
            resp =  Response(json.dumps(data, cls=SrcFieldJSONEncoder), content_type='application/json')
            return resp
        except:
            public.print_error()
            return []
    
    def get_process_tops(self, get):
        '''
            @name 获取进程开销排行
            @author hwliang<2021-09-07>
            @param get<dict_obj>{
                start: int<开始时间>
                end: int<结束时间>
            }
            @return list
        '''
        data = public.M('process_tops').dbfile('system').where(
            "addtime>=? AND addtime<=?",
            (get.start, get.end
             )).field('id,process_list,addtime').order('id asc').select()
        return self.ToAddtime(data)
    
    def get_process_cpu_high(self, get):
        '''
            @name 获取CPU占用高的进程列表
            @author hwliang<2021-09-07>
            @param get<dict_obj>{
                start: int<开始时间>
                end: int<结束时间>
            }
            @return list
        '''
        data = public.M('process_high_percent').dbfile('system').where(
            "addtime>=? AND addtime<=?", (get.start, get.end)).field(
            'id,name,pid,cmdline,cpu_percent,memory,cpu_time_total,addtime'
        ).order('id asc').select()
        return self.ToAddtime(data)
    
    def ToAddtime(self, data, tomem=False, types=None):
        import time
        # 格式化addtime列
        
        if tomem:
            import psutil
            mPre = (psutil.virtual_memory().total / 1024 / 1024) / 100
        length = len(data)
        he = 1
        if length > 100: he = 1
        if length > 1000: he = 3
        if length > 10000: he = 15
        if he == 1:
            for i in range(length):
                try:
                    if types:
                        key = '{}_top'.format(types)
                        if key in data[i]:
                            data[i][key] = json.loads(data[i][key])
                        if 'memory_top' in data[i]:
                            data[i]['memory_top'] = json.loads(
                                data[i]['memory_top'])
                    data[i]['addtime'] = time.strftime(
                        '%m/%d %H:%M',
                        time.localtime(float(data[i]['addtime'])))
                    if 'process_list' in data[i]:
                        data[i]['process_list'] = json.loads(
                            data[i]['process_list'])
                    if tomem and data[i]['mem'] > 100:
                        data[i]['mem'] = data[i]['mem'] / mPre
                    if tomem in [None]:
                        if type(data[i]['down_packets']) == str:
                            data[i]['down_packets'] = json.loads(
                                data[i]['down_packets'])
                            data[i]['up_packets'] = json.loads(
                                data[i]['up_packets'])
                except:
                    continue
            return data
        else:
            count = 0
            tmp = []
            couns = 0
            for value in data:
                if count < he:  # 0 1 2
                    count += 1
                    # cpu大于60的时候，随机取
                    if types == "cpu" and 'pro' in value and value['pro'] > 60:
                        couns += 1
                        # he等于3 的时候 百分之50的概率取  当he等于15的时候 百分之33的概率取
                        if (he == 3
                            and couns % 2 == 0) or (he == 15
                                                    and couns % 3 == 0):
                            if types:
                                key = '{}_top'.format(types)
                                if key in value:
                                    value[key] = json.loads(value[key])
                                if 'memory_top' in value:
                                    value['memory_top'] = json.loads(
                                        value['memory_top'])
                            value['addtime'] = time.strftime(
                                '%m/%d %H:%M',
                                time.localtime(float(value['addtime'])))
                            if tomem and 'mem' in value and value['mem'] > 100:
                                value['mem'] = value['mem'] / mPre
                            if tomem in [None]:
                                if type(value['down_packets']) == str:
                                    value['down_packets'] = json.loads(
                                        value['down_packets'])
                                    value['up_packets'] = json.loads(
                                        value['up_packets'])
                            tmp.append(value)
                    continue
                try:
                    if types:
                        key = '{}_top'.format(types)
                        if key in value:
                            value[key] = json.loads(value[key])
                        if 'memory_top' in value:
                            value['memory_top'] = json.loads(
                                value['memory_top'])
                    value['addtime'] = time.strftime(
                        '%m/%d %H:%M', time.localtime(float(value['addtime'])))
                    if tomem and 'mem' in value and value['mem'] > 100:
                        value['mem'] = value['mem'] / mPre
                    if tomem in [None]:
                        if type(value['down_packets']) == str:
                            value['down_packets'] = json.loads(
                                value['down_packets'])
                            value['up_packets'] = json.loads(
                                value['up_packets'])
                    tmp.append(value)
                    count = 0
                except:
                    continue
            return tmp
    
    def GetInstalleds(self, softlist):
        softs = ''
        for soft in softlist['data']:
            try:
                for v in soft['versions']:
                    if v['status']:
                        softs += soft['name'] + '-' + v['version'] + '|'
            except:
                pass
        return softs
    
    # 获取SSH爆破次数
    def get_ssh_intrusion(self):
        fp = open('/var/log/secure', 'rb')
        l = fp.readline()
        intrusion_total = 0
        while l:
            if l.find('Failed password for root') != -1: intrusion_total += 1
            l = fp.readline()
        fp.close()
        return intrusion_total
    
    # 申请内测版
    def apple_beta(self, get):
        try:
            userInfo = json.loads(public.ReadFile('data/userInfo.json'))
            p_data = {}
            p_data['uid'] = userInfo['uid']
            p_data['access_key'] = userInfo['access_key']
            p_data['username'] = userInfo['username']
            result = public.HttpPost(public.GetConfigValue('home') + '/api/panel/apple_beta', p_data, 5)
            try:
                return json.loads(result)
            except:
                return public.returnMsg(False, 'AJAX_CONN_ERR')
        except:
            return public.returnMsg(False, 'AJAX_USER_BINDING_ERR')
    
    def to_not_beta(self, get):
        try:
            userInfo = json.loads(public.ReadFile('data/userInfo.json'))
            p_data = {}
            p_data['uid'] = userInfo['uid']
            p_data['access_key'] = userInfo['access_key']
            p_data['username'] = userInfo['username']
            result = public.HttpPost(
                public.GetConfigValue('home') + '/api/panel/to_not_beta',
                p_data, 5)
            try:
                return json.loads(result)
            except:
                return public.returnMsg(False, 'AJAX_CONN_ERR')
        except:
            return public.returnMsg(False, 'AJAX_USER_BINDING_ERR')
    
    def to_beta(self):
        try:
            userInfo = json.loads(public.ReadFile('data/userInfo.json'))
            p_data = {}
            p_data['uid'] = userInfo['uid']
            p_data['access_key'] = userInfo['access_key']
            p_data['username'] = userInfo['username']
            public.HttpPost(
                public.GetConfigValue('home') + '/api/panel/to_beta', p_data,
                5)
        except:
            pass
    
    def get_uid(self):
        try:
            userInfo = json.loads(public.ReadFile('data/userInfo.json'))
            return userInfo['uid']
        except:
            return 0
    
    # 获取最新的5条测试版更新日志
    def get_beta_logs(self, get):
        try:
            data = json.loads(
                public.HttpGet(
                    public.GetConfigValue('home') +
                    '/api/panel/get_beta_logs'))
            return data
        except:
            return public.returnMsg(False, 'AJAX_CONN_ERR')
    
    def get_other_info(self):
        other = {}
        other['ds'] = []
        ds = public.M('domain').field('name').select()
        for d in ds:
            other['ds'].append(d['name'])
        return ','.join(other['ds'])
    
    def get_docker_model_info(self):
        """
        获取docker模块下所创建的容器，模板和项目数量
        :return: str
        """
        try:
            if not os.path.exists("/www/server/panel/data/docker.db"):
                return ""
            # 获取docker模块创建的容器数量
            dk_c_num = str(
                public.M('container').dbfile('docker').count()) + ' dk_c_num'
            # 获取docker模块创建模板数量
            dk_t_num = str(
                public.M('templates').dbfile('docker').count()) + ' dk_t_num'
            # 获取docker模块创建项目数量
            dk_s_num = str(
                public.M('stacks').dbfile('docker').count()) + ' dk_s_num'
            return "|{}|{}|{}".format(dk_c_num, dk_t_num, dk_s_num)
        except:
            return ""
    
    def UpdatePanel(self, get):
        try:
            import json
            if int(session['config']['status']) == 0:
                public.HttpGet(
                    public.GetConfigValue('home') +
                    '/Api/SetupCount?type=Linux')
                public.M('config').where("id=?", ('1',)).setField('status', 1)
            
            # 取回远程版本信 息
            if 'updateInfo' in session and hasattr(get, 'check') == False:
                updateInfo = session['updateInfo']
            else:
                logs = public.get_debug_log()
                import psutil, system, sys
                mem = psutil.virtual_memory()
                import panelPlugin
                mplugin = panelPlugin.panelPlugin()
                
                mplugin.ROWS = 10000
                panelsys = system.system()
                data = public.get_user_info()
                data['ds'] = ''  # self.get_other_info()
                data['sites'] = str(public.M('sites').count())
                data['ftps'] = str(public.M('ftps').count())
                data['databases'] = str(public.M('databases').count())
                data['system'] = panelsys.GetSystemVersion() + '|' + str(
                    mem.total / 1024 /
                    1024) + 'MB|' + str(public.getCpuType()) + '*' + str(
                    psutil.cpu_count()) + '|' + str(
                    public.get_webserver()) + '|' + session['version']
                data['system'] += '||' + self.GetInstalleds(
                    mplugin.getPluginList(
                        None)) + self.get_docker_model_info()
                data['logs'] = logs
                data['client'] = request.headers.get('User-Agent')
                data['oem'] = ''
                data['intrusion'] = 0
                data['uid'] = self.get_uid()
                # msg = public.getMsg('PANEL_UPDATE_MSG');
                data['o'] = public.get_oem_name()
                sUrl = public.GetConfigValue('home') + '/api/panel/updateLinux'
                try:
                    updateInfo = json.loads(public.httpPost(sUrl, data))
                except:
                    return public.returnMsg(False, "CONNECT_ERR")
                if not updateInfo:
                    return public.returnMsg(False, "CONNECT_ERR")
                # updateInfo['msg'] = msg;
                session['updateInfo'] = updateInfo
            
            # 输出忽略的版本
            updateInfo['ignore'] = []
            no_path = '{}/data/no_update.pl'.format(public.get_panel_path())
            if os.path.exists(no_path):
                try:
                    updateInfo['ignore'] = json.loads(public.readFile(no_path))
                except:
                    pass
            
            updateInfo['local_beta'] = 0
            local_beta = '/www/server/panel/data/local_beta.pl'
            try:
                # 2024/1/4 下午 3:32 g.version获取版本号，版本号格式为：8.0.48，判断最后一个数字是否大于10，如果大于10，则为测试版，小于或等于10，则为正式版
                from BTPanel import g
                if int(g.version.split('.')[-1]) > 10:
                    updateInfo['local_beta'] = 1
            except:
                if os.path.exists(local_beta): updateInfo['local_beta'] = 1
            
            # 检查是否需要升级
            if not hasattr(get, 'toUpdate'):
                if updateInfo['is_beta'] == 1:
                    if updateInfo['beta']['version'] == session['version']:
                        return public.returnMsg(False, updateInfo)
                else:
                    if updateInfo['version'] == session['version']:
                        return public.returnMsg(False, updateInfo)
            
            # 是否执行升级程序
            if (updateInfo['force'] == True or hasattr(get, 'toUpdate') == True
                or os.path.exists('data/autoUpdate.pl') == True):
                if not public.IsRestart():
                    return public.returnMsg(False, 'EXEC_ERR_TASK')
                if updateInfo['is_beta'] == 1:
                    updateInfo['version'] = updateInfo['beta']['version']
                setupPath = public.GetConfigValue('setup_path')
                uptype = 'update'
                httpUrl = public.get_url()
                if httpUrl:
                    updateInfo[
                        'downUrl'] = httpUrl + '/install/' + uptype + '/LinuxPanel-' + updateInfo[
                        'version'] + '.zip'
                public.downloadFile(updateInfo['downUrl'], 'panel.zip')
                if os.path.getsize('panel.zip') < 1048576:
                    return public.returnMsg(False, "PANEL_UPDATE_ERR_DOWN")
                public.ExecShell('unzip -o panel.zip -d ' + setupPath + '/')
                if os.path.exists('/www/server/panel/runserver.py'):
                    public.ExecShell('rm -f /www/server/panel/*.pyc')
                if os.path.exists('/www/server/panel/class/common.py'):
                    public.ExecShell('rm -f /www/server/panel/class/*.pyc')
                
                if os.path.exists('panel.zip'): os.remove("panel.zip")
                session['version'] = updateInfo['version']
                if 'getCloudPlugin' in session: del (session['getCloudPlugin'])
                
                if os.path.exists(local_beta): os.remove(local_beta)
                if updateInfo['is_beta'] == 1:
                    self.to_beta()
                    public.writeFile(local_beta, 'True')

                try:
                    # 标记数据库结构检查次数，防止更新后不检查
                    update_num_file = '{}/data/db/update'.format(public.get_panel_path())
                    if os.path.exists(update_num_file):
                        num = public.readFile(update_num_file)
                        if num and int(num) > 3: public.writeFile(update_num_file, '3')
                except:
                    pass
                
                public.ExecShell("/etc/init.d/bt start")
                public.writeFile('data/restart.pl', 'True')
                return public.returnMsg(True, 'PANEL_UPDATE',
                                        (updateInfo['version'],))
            
            public.ExecShell('rm -rf /www/server/phpinfo/*')
            return public.returnMsg(True, updateInfo)
        except Exception as ex:
            return public.get_error_info()
    
    # 检查是否安装任何
    def CheckInstalled(self, get):
        checks = ['nginx', 'apache', 'php', 'pure-ftpd', 'mysql']
        import os
        for name in checks:
            filename = public.GetConfigValue('root_path') + "/server/" + name
            if os.path.exists(filename): return True
        return False
    
    # 取已安装软件列表
    def GetInstalled(self, get):
        import system
        data = system.system().GetConcifInfo()
        return data
    
    # 取PHP配置
    def GetPHPConfig(self, get):
        if not hasattr(get, 'version'):
            return public.returnMsg(False, "缺少参数! version")
        import re, json
        filename = public.GetConfigValue(
            'setup_path') + '/php/' + get.version + '/etc/php.ini'
        if public.get_webserver() == 'openlitespeed':
            filename = '/usr/local/lsws/lsphp{}/etc/php/{}.{}/litespeed/php.ini'.format(
                get.version, get.version[0], get.version[1])
            if os.path.exists('/etc/redhat-release'):
                filename = '/usr/local/lsws/lsphp' + get.version + '/etc/php.ini'
        if not os.path.exists(filename):
            return public.returnMsg(False, 'PHP_NOT_EXISTS')
        phpini = public.readFile(filename)
        data = {}
        rep = "disable_functions\s*=\s{0,1}(.*)\n"
        
        tmp = re.search(rep, phpini)
        if tmp:
            data['disable_functions'] = tmp.groups()[0]
        
        rep = "upload_max_filesize\s*=\s*([0-9]+)(M|m|K|k)"
        
        tmp = re.search(rep, phpini)
        if tmp:
            data['max'] = tmp.groups()[0]
        
        rep = u"\n;*\s*cgi\.fix_pathinfo\s*=\s*([0-9]+)\s*\n"
        tmp = re.search(rep, phpini)
        if tmp:
            if tmp.groups()[0] == '0':
                data['pathinfo'] = False
            else:
                data['pathinfo'] = True
        
        self.getCloudPHPExt(get)
        try:
            phplib = json.loads(public.readFile('data/phplib.conf'))
        except:
            phplib = self.get_php_ext_by_cloud()
        libs = []
        tasks = public.M('tasks').where("status!=?",
                                        ('1',)).field('status,name').select()
        phpini_ols = None
        for lib in phplib:
            lib['task'] = '1'
            for task in tasks:
                tmp = public.getStrBetween('[', ']', task['name'])
                if not tmp: continue
                tmp1 = tmp.split('-')
                if tmp1[0].lower() == lib['name'].lower():
                    lib['task'] = task['status']
                    lib['phpversions'] = []
                    lib['phpversions'].append(tmp1[1])
            if public.get_webserver() == 'openlitespeed':
                lib['status'] = False
                get.php_version = "{}.{}".format(get.version[0],
                                                 get.version[1])
                if not phpini_ols:
                    phpini_ols = self.php_info(
                        get)['phpinfo']['modules'].lower()
                    phpini_ols = phpini_ols.split()
                for i in phpini_ols:
                    if lib['check'][:-3].lower() == i:
                        lib['status'] = True
                        break
                    if "ioncube" in lib['check'][:-3].lower(
                    ) and "ioncube" == i:
                        lib['status'] = True
                        break
            else:
                if phpini.find(lib['check']) == -1:
                    lib['status'] = False
                else:
                    lib['status'] = True
            
            libs.append(lib)
        
        data['libs'] = libs
        return data
    
    # 获取PHP扩展
    def getCloudPHPExt(self, get):
        import json
        try:
            if 'php_ext' in session: return True
            if not session.get('download_url'):
                session['download_url'] = public.GetConfigValue('download')
            download_url = session['download_url'] + '/install/lib/phplib.json'
            tstr = public.httpGet(download_url)
            data = json.loads(tstr)
            if not data: return False
            public.writeFile('data/phplib.conf', json.dumps(data))
            session['php_ext'] = True
            return True
        except:
            return False
    
    @staticmethod
    def get_php_ext_by_cloud():
        try:
            if not session.get('download_url'):
                session['download_url'] = public.GetConfigValue('download')
            download_url = session['download_url'] + '/install/lib/phplib.json'
            resp_str = public.httpGet(download_url)
            data = json.loads(resp_str)
            if isinstance(data, list):
                public.writeFile('{}/data/phplib.conf'.format(public.get_panel_path()), resp_str)
                return data
        except:
            pass
        return []
    
    def reGetCloudPHPExt(self, get):
        data = self.get_php_ext_by_cloud()
        if len(data) > 0:
            return public.returnMsg(True, '拉取云端数据成功')
        else:
            return public.returnMsg(False, '手动拉取云端数据失败,建议去 [面板设置] 中更换 [面板云端通讯节点] 后再手动拉取云端数据')
    
    # MySQL相关信息获取(告警信息获取)
    def GetMysqlAlarmInfo(self, get):
        from panelPush import panelPush
        p = panelPush()
        res = p.get_push_list(get)
        data = {"service": "mysql", "alarm": False, "id": "", "status": False}
        if not 'site_push' in res: return public.returnMsg(True, data)
        res = res['site_push']
        for key, value in res.items():
            if value["title"] == "mysql服务停止告警":
                data["id"] = key
                data["alarm"] = True
                data['data'] = value
                data["status"] = value["status"]
                return public.returnMsg(True, data)
        
        return public.returnMsg(True, data)
    
    # 取PHPINFO信息
    def GetPHPInfo(self, get):
        if public.get_webserver() == "openlitespeed":
            shell_str = "/usr/local/lsws/lsphp{}/bin/php -i".format(
                get.version)
            return public.ExecShell(shell_str)[0]
        sPath = '/www/server/phpinfo'
        if os.path.exists(sPath):
            public.ExecShell("rm -rf " + sPath)
        p_file = '/dev/shm/phpinfo.php'
        public.writeFile(p_file, '<?php phpinfo(); ?>')
        try:
            phpinfo = public.request_php(get.version, '/phpinfo.php', '/dev/shm')
        except:
            return public.returnMsg(False, '获取PHPINFO失败!')
        if os.path.exists(p_file): os.remove(p_file)
        return phpinfo.decode()
    
    # 清理日志
    def delClose(self, get):
        if not 'uid' in session: session['uid'] = 1
        if session['uid'] != 1: return public.returnMsg(False, '没有权限!')
        if 'tmp_login_id' in session:
            return public.returnMsg(False, '没有权限!')
        
        # 备份近100条日志
        new_bak = public.M('logs').limit('100').select()
        if len(new_bak) > 3:
            bak_file = '{}/data/logs.bak'.format(public.get_panel_path())
            public.writeFile(bak_file, json.dumps(new_bak))
        public.add_security_logs(
            "清空日志", '清空所有日志条数为:{}'.format(public.M('logs').count()))
        # 清空日志
        public.M('logs').where('id>?', (0,)).delete()
        public.WriteLog('TYPE_CONFIG', 'LOG_CLOSE')
        return public.returnMsg(True, 'LOG_CLOSE')
    
    def __get_webserver_conffile(self):
        webserver = public.get_webserver()
        if webserver == 'nginx':
            filename = public.GetConfigValue(
                'setup_path') + '/nginx/conf/nginx.conf'
        elif webserver == 'openlitespeed':
            filename = public.GetConfigValue(
                'setup_path'
            ) + "/panel/vhost/openlitespeed/detail/phpmyadmin.conf"
        else:
            filename = public.GetConfigValue(
                'setup_path') + '/apache/conf/extra/httpd-vhosts.conf'
        
        return filename
    
    def phpmyadmin_client_check(self,get):
        from BTPanel import cache
        pmd = cache.get("pmd_port_path")
        if not pmd:
            from BTPanel import get_phpmyadmin_dir
            pmd = get_phpmyadmin_dir()
            if not pmd: return public.ReturnMsg(False,'未安装phpMyAdmin,请到【软件商店】页面安装!')
        
        pmd_path=pmd[0]
        pmd_port=pmd[1]
        phpmyadmin_url="http://127.0.0.1:{}/{}/index.php".format(pmd_port,pmd_path)

        import requests
        from requests.exceptions import ConnectionError, Timeout, HTTPError
        webserver=public.get_webserver()
        try:
            response = requests.get(phpmyadmin_url,timeout=5)
            status_code = response.status_code
            if 200 <= status_code < 400:
                return public.ReturnMsg(True,"可以正常访问！")
            elif status_code == 502 or status_code == 503:
                return public.ReturnMsg(False,"phpmyadmin访问状态{},请检查phpmyadmin的php是否正常运行！".format(status_code))
            elif status_code == 404:
                return public.ReturnMsg(False,"phpmyadmin访问状态{},请尝试重装phpmyadmin看是否正常！".format(status_code))
            elif status_code == 403:
                return public.ReturnMsg(False,"phpmyadmin访问状态{},请检查/www/server/phpmyadmin目录及上级目录文件权限是否是755权限！".format(status_code))
            elif status_code == 401:
                return public.ReturnMsg(True,"可以正常访问！")
            else:
                return public.ReturnMsg(False,"phpmyadmin无法访问！状态码{},请截图此处报错联系客服人员查看！".format(status_code)) 
        except ConnectionError:
            return public.ReturnMsg(False,"phpmyadmin面板无法代理访问，请检查{}是否正常启动，或尝试使用【phpmyadmin】-【通过公共访问】进行访问".format(webserver))
        except Timeout:
            return public.ReturnMsg(False,"phpmyadmin连接超时，请检查{}是否正常启动或处于高负载状态".format(webserver))
        except HTTPError as http_err:
            return public.ReturnMsg(False,"phpmyadmin无法访问!,请联系客服人员查看")
        except Exception as err:
            return public.ReturnMsg(False,"phpmyadmin无法访问!,请联系客服人员查看")
        
        return public.ReturnMsg(True,"可以正常访问！")
    
    # 获取phpmyadmin ssl配置
    def get_phpmyadmin_conf(self):
        if public.get_webserver() == "nginx":
            conf_file = "/www/server/panel/vhost/nginx/phpmyadmin.conf"
            rep = r"listen\s*(\d+)"
        else:
            conf_file = "/www/server/panel/vhost/apache/phpmyadmin.conf"
            rep = r"Listen\s*(\d+)"
        return {"conf_file": conf_file, "rep": rep}
    
    # 设置phpmyadmin路径
    def set_phpmyadmin_session(self):
        import re
        conf_file = self.get_phpmyadmin_conf()
        conf = public.readFile(conf_file["conf_file"])
        rep = conf_file["rep"]
        if conf:
            port = re.search(rep, conf).group(1)
            if session['phpmyadminDir']:
                path = session['phpmyadminDir'].split("/")[-1]
                ip = public.GetHost()
                session['phpmyadminDir'] = "https://{}:{}/{}".format(
                    ip, port, path)
    
    # 获取phpmyadmin ssl状态
    def get_phpmyadmin_ssl(self, get):
        import re
        auth = False
        conf_file = self.get_phpmyadmin_conf()
        conf = public.readFile(conf_file["conf_file"])
        rep = conf_file["rep"]
        if conf:
            port = re.search(rep, conf).group(1)
            path = "/www/server/panel/vhost/{}/phpmyadmin.conf".format(public.get_webserver())
            if os.path.exists(path):
                conf = public.readFile(path)
                if conf.find("AUTH_START") != -1:
                    auth = True
            return {"status": True, "port": port, "auth": auth}
        if public.get_webserver() == "nginx":
            path = "/www/server/nginx/conf/nginx.conf"
            if os.path.exists(path):
                conf = public.readFile(path)
                if conf.find("AUTH_START") != -1:
                    auth = True
        else:
            path = "/www/server/apache/conf/extra/httpd-vhosts.conf"
            if os.path.exists(path):
                conf = public.readFile(path)
                if conf.find("AUTH_START") != -1:
                    auth = True
        return {"status": False, "port": "", "auth": auth}
    
    # 修改php ssl端口
    def change_phpmyadmin_ssl_port(self, get):
        if public.get_webserver() == "openlitespeed":
            return public.returnMsg(False, 'OpenLiteSpeed 目前尚不支持该操作')
        import re
        try:
            port = int(get.port)
            if 1 > port > 65535:
                return public.returnMsg(False, '端口范围不正确')
        except:
            return public.returnMsg(False, '端口格式不正确')
        for i in ["nginx", "apache"]:
            file = "/www/server/panel/vhost/{}/phpmyadmin.conf".format(i)
            conf = public.readFile(file)
            if not conf:
                return public.returnMsg(
                    False, "没有找到{}配置文件，请尝试关闭ssl端口设置后再打开".format(i))
            rulePort = [
                '80', '443', '21', '20', '8080', '8081', '8089', '11211',
                '6379'
            ]
            if get.port in rulePort:
                return public.returnMsg(False, 'AJAX_PHPMYADMIN_PORT_ERR')
            if i == "nginx":
                if not os.path.exists(
                    "/www/server/panel/vhost/apache/phpmyadmin.conf"):
                    return public.returnMsg(
                        False,
                        "没有找到 apache phpmyadmin ssl 配置文件，请尝试关闭ssl端口设置后再打开")
                rep = r"listen\s*([0-9]+)\s*.*;"
                oldPort = re.search(rep, conf)
                if not oldPort:
                    return public.returnMsg(
                        False, '没有检测到 nginx phpmyadmin监听的端口，请确认是否手动修改过文件')
                oldPort = oldPort.groups()[0]
                conf = re.sub(rep, 'listen ' + get.port + ' ssl;', conf)
            else:
                rep = r"Listen\s*([0-9]+)\s*\n"
                oldPort = re.search(rep, conf)
                if not oldPort:
                    return public.returnMsg(
                        False, '没有检测到 apache phpmyadmin监听的端口，请确认是否手动修改过文件')
                oldPort = oldPort.groups()[0]
                conf = re.sub(rep, "Listen " + get.port + "\n", conf, 1)
                rep = r"VirtualHost\s*\*:[0-9]+"
                conf = re.sub(rep, "VirtualHost *:" + get.port, conf, 1)
            if oldPort == get.port:
                return public.returnMsg(False, 'SOFT_PHPVERSION_ERR_PORT')
            public.writeFile(file, conf)
            public.serviceReload()
            if i == "apache":
                import firewalls
                get.ps = public.getMsg('SOFT_PHPVERSION_PS')
                fw = firewalls.firewalls()
                fw.AddAcceptPort(get)
                public.serviceReload()
                public.WriteLog('TYPE_SOFT', 'SOFT_PHPMYADMIN_PORT',
                                (get.port,))
                get.id = public.M('firewall').where('port=?',
                                                    (oldPort,)).getField('id')
                get.port = oldPort
                fw.DelAcceptPort(get)
        return public.returnMsg(True, 'SET_PORT_SUCCESS')
    
    def _get_phpmyadmin_auth(self):
        import re
        nginx_conf = '/www/server/nginx/conf/nginx.conf'
        reg = '#AUTH_START(.|\n)*#AUTH_END'
        if os.path.exists(nginx_conf):
            nginx_conf = public.readFile(nginx_conf)
            auth_tmp = re.search(reg, nginx_conf)
            if auth_tmp:
                return True
        apache_conf = '/www/server/apache/conf/extra/httpd-vhosts.conf'
        if os.path.exists(apache_conf):
            apache_conf = public.readFile(apache_conf)
            auth_tmp = re.search(reg, apache_conf)
            if auth_tmp:
                return True
    
    # 设置phpmyadmin ssl
    def set_phpmyadmin_ssl(self, get):
        if public.get_webserver() == "openlitespeed":
            return public.returnMsg(False, 'OpenLiteSpeed 目前尚不支持该操作')
        if not os.path.exists("/www/server/panel/ssl/certificate.pem"):
            return public.returnMsg(False, '面板证书不存在，请申请面板证书后再试')
        if get.v == "1":
            # 获取auth信息
            auth = ""
            if self._get_phpmyadmin_auth():
                auth = """
        #AUTH_START
        auth_basic "Authorization";
        auth_basic_user_file /www/server/pass/phpmyadmin.pass;
        #AUTH_END
"""
            # nginx配置文件
            ssl_conf = """server
    {
        listen 887 ssl;
        server_name phpmyadmin;
        index index.html index.htm index.php;
        root  /www/server/phpmyadmin;
        #SSL-START SSL相关配置，请勿删除或修改下一行带注释的404规则
        #error_page 404/404.html;
        ssl_certificate    /www/server/panel/ssl/certificate.pem;
        ssl_certificate_key    /www/server/panel/ssl/privateKey.pem;
        ssl_protocols TLSv1 TLSv1.1 TLSv1.2 TLSv1.3;
        ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:HIGH:!aNULL:!MD5:!RC4:!DHE;
        ssl_prefer_server_ciphers on;
        ssl_session_cache shared:SSL:10m;
        ssl_session_timeout 10m;
        error_page 497  https://$host$request_uri;
        #SSL-END
        %s
        include enable-php.conf;
        location ~ .*\.(gif|jpg|jpeg|png|bmp|swf)$
        {
            expires      30d;
        }
        location ~ .*\.(js|css)?$
        {
            expires      12h;
        }
        location ~ /\.
        {
            deny all;
        }
        access_log  /www/wwwlogs/access.log;
    }""" % auth
            public.writeFile("/www/server/panel/vhost/nginx/phpmyadmin.conf",
                             ssl_conf)
            import panelPlugin
            get.sName = "phpmyadmin"
            v = panelPlugin.panelPlugin().get_soft_find(get)
            if self._get_phpmyadmin_auth():
                auth = """
        #AUTH_START
        AuthType basic
        AuthName "Authorization "
        AuthUserFile /www/server/pass/phpmyadmin.pass
        Require user jose
        #AUTH_END
            """
            # apache配置
            ssl_conf = '''Listen 887
<VirtualHost *:887>
    ServerAdmin webmaster@example.com
    DocumentRoot "/www/server/phpmyadmin"
    ServerName 0b842aa5.phpmyadmin
    ServerAlias phpmyadmin.com
    #ErrorLog "/www/wwwlogs/BT_default_error.log"
    #CustomLog "/www/wwwlogs/BT_default_access.log" combined

    #SSL
    SSLEngine On
    SSLCertificateFile /www/server/panel/ssl/certificate.pem
    SSLCertificateKeyFile /www/server/panel/ssl/privateKey.pem
    SSLCipherSuite EECDH+AESGCM:EDH+AESGCM:AES256+EECDH:AES256+EDH
    SSLProtocol All -SSLv2 -SSLv3
    SSLHonorCipherOrder On

    #PHP
    <FilesMatch \.php$>
           SetHandler "proxy:{}"
    </FilesMatch>

    #DENY FILES
    <Files ~ (\.user.ini|\.htaccess|\.git|\.svn|\.project|LICENSE|README.md)$>
      Order allow,deny
      Deny from all
    </Files>

    #PATH
    <Directory "/www/wwwroot/bt.youbadbad.cn/">
{}
       SetOutputFilter DEFLATE
       Options FollowSymLinks
       AllowOverride All
       Require all granted
       DirectoryIndex index.php index.html index.htm default.php default.html default.htm
    </Directory>
</VirtualHost>'''.format(
                public.get_php_proxy(v["ext"]["phpversion"], 'apache'), auth)
            public.writeFile("/www/server/panel/vhost/apache/phpmyadmin.conf",
                             ssl_conf)
        else:
            if os.path.exists("/www/server/panel/vhost/nginx/phpmyadmin.conf"):
                os.remove("/www/server/panel/vhost/nginx/phpmyadmin.conf")
            if os.path.exists(
                "/www/server/panel/vhost/apache/phpmyadmin.conf"):
                os.remove("/www/server/panel/vhost/apache/phpmyadmin.conf")
            public.serviceReload()
            return public.returnMsg(True, '关闭成功')
        public.serviceReload()
        return public.returnMsg(True, '开启成功，请手动放行phpmyadmin ssl端口')
    
    # 设置PHPMyAdmin
    def setPHPMyAdmin(self, get):
        import re
        # try:
        filename = self.__get_webserver_conffile()
        if public.get_webserver() == 'openlitespeed':
            filename = "/www/server/panel/vhost/openlitespeed/detail/phpmyadmin.conf"
        conf = public.readFile(filename)
        if not conf: return public.returnMsg(False, '未安装nginx或apache,无法设置!')
        if hasattr(get, 'port'):
            mainPort = public.readFile('data/port.pl').strip()
            rulePort = [
                '80', '443', '21', '20', '8080', '8081', '8089', '11211',
                '6379'
            ]
            oldPort = "888"
            if get.port in rulePort:
                return public.returnMsg(False, 'AJAX_PHPMYADMIN_PORT_ERR')
            if public.get_webserver() == 'nginx':
                rep = r"listen\s+([0-9]+)\s*;"
                match = re.search(rep, conf)
                if match:
                    oldPort = match.groups()[0]
                conf = re.sub(rep, 'listen ' + get.port + ';\n', conf)
            elif public.get_webserver() == 'apache':
                rep = r"Listen\s+([0-9]+)\s*\n"
                oldPort = re.search(rep, conf).groups()[0]
                conf = re.sub(rep, "Listen " + get.port + "\n", conf, 1)
                rep = r"VirtualHost\s+\*:[0-9]+"
                conf = re.sub(rep, "VirtualHost *:" + get.port, conf, 1)
            else:
                filename = '/www/server/panel/vhost/openlitespeed/listen/888.conf'
                conf = public.readFile(filename)
                reg = r"address\s+\*:(\d+)"
                tmp = re.search(reg, conf)
                if tmp:
                    oldPort = tmp.groups()[0]
                conf = re.sub(reg, "address *:{}".format(get.port), conf)
            if oldPort == get.port:
                return public.returnMsg(False, 'SOFT_PHPVERSION_ERR_PORT')
            
            public.writeFile(filename, conf)
            import firewalls
            get.ps = public.getMsg('SOFT_PHPVERSION_PS')
            fw = firewalls.firewalls()
            fw.AddAcceptPort(get)
            public.serviceReload()
            public.WriteLog('TYPE_SOFT', 'SOFT_PHPMYADMIN_PORT', (get.port,))
            get.id = public.M('firewall').where('port=?',
                                                (oldPort,)).getField('id')
            get.port = oldPort
            fw.DelAcceptPort(get)
            return public.returnMsg(True, 'SET_PORT_SUCCESS')
        
        if hasattr(get, 'phpversion'):
            if public.get_webserver() == 'nginx':
                filename = public.GetConfigValue(
                    'setup_path') + '/nginx/conf/enable-php.conf'
                conf = public.readFile(filename)
                rep = r"(unix:/tmp/php-cgi.*\.sock|127.0.0.1:\d+)"
                conf = re.sub(rep,
                              public.get_php_proxy(get.phpversion,
                                                   'nginx'), conf, 1)
            elif public.get_webserver() == 'apache':
                rep = r"(unix:/tmp/php-cgi.*\.sock\|fcgi://localhost|fcgi://127.0.0.1:\d+)"
                conf = re.sub(rep,
                              public.get_php_proxy(get.phpversion, 'apache'),
                              conf, 1)
            else:
                reg = r'/usr/local/lsws/lsphp\d+/bin/lsphp'
                conf = re.sub(
                    reg,
                    '/usr/local/lsws/lsphp{}/bin/lsphp'.format(get.phpversion),
                    conf)
            public.writeFile(filename, conf)
            public.serviceReload()
            public.WriteLog('TYPE_SOFT', 'SOFT_PHPMYADMIN_PHP',
                            (get.phpversion,))
            return public.returnMsg(True, 'SOFT_PHPVERSION_SET')
        
        if hasattr(get, 'password'):
            import panelSite
            if (get.password == 'close'):
                return panelSite.panelSite().CloseHasPwd(get)
            else:
                return panelSite.panelSite().SetHasPwd(get)
        
        if hasattr(get, 'status'):
            pma_path = public.GetConfigValue('setup_path') + '/phpmyadmin'
            stop_path = public.GetConfigValue('setup_path') + '/stop'
            
            webserver = public.get_webserver()
            if conf.find(stop_path) != -1:
                conf = conf.replace(stop_path, pma_path)
                msg = public.getMsg('START')
            
            if webserver == 'nginx':
                sub_string = '''{};
        allow 127.0.0.1;
        allow ::1;
        deny all'''.format(pma_path)
                if conf.find(sub_string) != -1:
                    conf = conf.replace(sub_string, pma_path)
                    msg = public.getMsg('START')
                else:
                    conf = conf.replace(pma_path, sub_string)
                    msg = public.getMsg('STOP')
            elif webserver == 'apache':
                src_string = 'AllowOverride All'
                sub_string = '''{}
        Deny from all
        Allow from 127.0.0.1 ::1 localhost'''.format(src_string, pma_path)
                if conf.find(sub_string) != -1:
                    conf = conf.replace(sub_string, src_string)
                    msg = public.getMsg('START')
                else:
                    conf = conf.replace(src_string, sub_string)
                    msg = public.getMsg('STOP')
            else:
                if conf.find(stop_path) != -1:
                    conf = conf.replace(stop_path, pma_path)
                    msg = public.getMsg('START')
                else:
                    conf = conf.replace(pma_path, stop_path)
                    msg = public.getMsg('STOP')
            
            public.writeFile(filename, conf)
            public.serviceReload()
            public.WriteLog('TYPE_SOFT', 'SOFT_PHPMYADMIN_STATUS', (msg,))
            return public.returnMsg(True, 'SOFT_PHPMYADMIN_STATUS', (msg,))
        # except:
        # return public.returnMsg(False,'ERROR');
    
    def ToPunycode(self, get):
        import re
        get.domain = get.domain.encode('utf8')
        tmp = get.domain.split('.')
        newdomain = ''
        for dkey in tmp:
            # 匹配非ascii字符
            match = re.search(u"[\x80-\xff]+", dkey)
            if not match:
                newdomain += dkey + '.'
            else:
                newdomain += 'xn--' + dkey.decode('utf-8').encode(
                    'punycode') + '.'
        
        return newdomain[0:-1]
    
    # 保存PHP排序
    def phpSort(self, get):
        if public.writeFile('/www/server/php/sort.pl', get.ssort):
            return public.returnMsg(True, 'SUCCESS')
        return public.returnMsg(False, 'ERROR')
    
    # 获取广告代码
    def GetAd(self, get):
        try:
            return public.HttpGet(
                public.GetConfigValue('home') + '/Api/GetAD?name=' + get.name +
                '&soc=' + get.soc)
        except:
            return ''
    
    # 获取进度
    def GetSpeed(self, get):
        return public.getSpeed()
    
    # 检查登陆状态
    def CheckLogin(self, get):
        return True
    
    # 获取警告标识
    def GetWarning(self, get):
        warningFile = 'data/warning.json'
        if not os.path.exists(warningFile):
            return public.returnMsg(False, 'AJAX_WARNING_ERR')
        import json, time
        wlist = json.loads(public.readFile(warningFile))
        wlist['time'] = int(time.time())
        return wlist
    
    # 设置警告标识
    def SetWarning(self, get):
        wlist = self.GetWarning(get)
        id = int(get.id)
        import time, json
        for i in xrange(len(wlist['data'])):
            if wlist['data'][i]['id'] == id:
                wlist['data'][i]['ignore_count'] += 1
                wlist['data'][i]['ignore_time'] = int(time.time())
        
        warningFile = 'data/warning.json'
        public.writeFile(warningFile, json.dumps(wlist))
        return public.returnMsg(True, 'SET_SUCCESS')
    
    # 获取memcached状态
    def GetMemcachedStatus(self, get):
        import telnetlib, re
        conf = public.readFile('/etc/init.d/memcached')
        if not conf:
            return public.returnMsg(False, '获取负载状态失败，请重新安装memcached后再试!')
        result = {}
        result['bind'] = re.search('IP=(.+)', conf).groups()[0]
        result['port'] = int(re.search('PORT=(\d+)', conf).groups()[0])
        result['maxconn'] = int(re.search('MAXCONN=(\d+)', conf).groups()[0])
        result['cachesize'] = int(
            re.search('CACHESIZE=(\d+)', conf).groups()[0])
        try:
            tn = telnetlib.Telnet(result['bind'], result['port'])
        except:
            return public.returnMsg(False, '获取负载状态失败，请检查服务是否启动!')
        tn.write(b"stats\n")
        tn.write(b"quit\n")
        data = tn.read_all()
        if type(data) == bytes: data = data.decode('utf-8')
        data = data.replace('STAT', '').replace('END', '').split("\n")
        res = [
            'cmd_get', 'get_hits', 'get_misses', 'limit_maxbytes',
            'curr_items', 'bytes', 'evictions', 'limit_maxbytes',
            'bytes_written', 'bytes_read', 'curr_connections'
        ]
        for d in data:
            if len(d) < 3: continue
            t = d.split()
            if not t[0] in res: continue
            result[t[0]] = int(t[1])
        result['hit'] = 1
        if result['get_hits'] > 0 and result['cmd_get'] > 0:
            result['hit'] = float(result['get_hits']) / float(
                result['cmd_get']) * 100
        
        return result
    
    # 设置memcached缓存大小
    def SetMemcachedCache(self, get):
        import re
        confFile = '/etc/init.d/memcached'
        conf = public.readFile(confFile)
        conf = re.sub('IP=.+', 'IP=' + get.ip, conf)
        conf = re.sub('PORT=\d+', 'PORT=' + get.port, conf)
        conf = re.sub('MAXCONN=\d+', 'MAXCONN=' + get.maxconn, conf)
        conf = re.sub('CACHESIZE=\d+', 'CACHESIZE=' + get.cachesize, conf)
        public.writeFile(confFile, conf)
        public.ExecShell(confFile + ' reload')
        return public.returnMsg(True, 'SET_SUCCESS')
    
    # 取redis状态
    def GetRedisStatus(self, get):
        import re
        c = public.readFile('/www/server/redis/redis.conf')
        port = re.findall('\n\s*port\s+(\d+)', c)[0]
        password = re.findall('\n\s*requirepass\s+(.+)', c)
        if password:
            password = ' -a ' + password[0]
        else:
            password = ''
        data = public.ExecShell('/www/server/redis/src/redis-cli -p ' + port +
                                password + ' info')[0]
        res = [
            'tcp_port',
            'uptime_in_days',  # 已运行天数
            'connected_clients',  # 连接的客户端数量
            'used_memory',  # Redis已分配的内存总量
            'used_memory_rss',  # Redis占用的系统内存总量
            'used_memory_peak',  # Redis所用内存的高峰值
            'mem_fragmentation_ratio',  # 内存碎片比率
            'total_connections_received',  # 运行以来连接过的客户端的总数量
            'total_commands_processed',  # 运行以来执行过的命令的总数量
            'instantaneous_ops_per_sec',  # 服务器每秒钟执行的命令数量
            'keyspace_hits',  # 查找数据库键成功的次数
            'keyspace_misses',  # 查找数据库键失败的次数
            'latest_fork_usec'  # 最近一次 fork() 操作耗费的毫秒数
        ]
        data = data.split("\n")
        result = {}
        for d in data:
            if len(d) < 3: continue
            t = d.strip().split(':')
            if not t[0] in res: continue
            result[t[0]] = t[1]
        return result
    
    # 取PHP-FPM日志
    def GetFpmLogs(self, get):
        import re
        fpm_path = '/www/server/php/' + get.version + '/etc/php-fpm.conf'
        if not os.path.exists(fpm_path):
            return public.returnMsg(False, 'AJAX_LOG_FILR_NOT_EXISTS')
        fpm_conf = public.readFile(fpm_path)
        log_tmp = re.findall(r"error_log\s*=\s*(.+)", fpm_conf)
        if not log_tmp:
            return public.returnMsg(False, 'AJAX_LOG_FILR_NOT_EXISTS')
        log_file = log_tmp[0].strip()
        if log_file.find('var/log') == 0:
            log_file = '/www/server/php/' + get.version + '/' + log_file
        return public.returnMsg(True, public.GetNumLines(log_file, 1000))
    
    # 取PHP慢日志
    def GetFpmSlowLogs(self, get):
        import re
        fpm_path = '/www/server/php/' + get.version + '/etc/php-fpm.conf'
        if not os.path.exists(fpm_path):
            return public.returnMsg(False, 'AJAX_LOG_FILR_NOT_EXISTS')
        fpm_conf = public.readFile(fpm_path)
        log_tmp = re.findall(r"slowlog\s*=\s*(.+)", fpm_conf)
        if not log_tmp:
            return public.returnMsg(False, 'AJAX_LOG_FILR_NOT_EXISTS')
        log_file = log_tmp[0].strip()
        if log_file.find('var/log') == 0:
            log_file = '/www/server/php/' + get.version + '/' + log_file
        return public.returnMsg(True, public.GetNumLines(log_file, 1000))
    
    # 取指定日志
    def GetOpeLogs(self, get):
        if not os.path.exists(get.path):
            return public.returnMsg(False, 'AJAX_LOG_FILR_NOT_EXISTS')
        return public.returnMsg(
            True, public.xsssec(public.GetNumLines(get.path, 1000)))
    
    def get_pd(self, get):
        from BTPanel import cache
        tmp = -1
        try:
            import panelPlugin
            # get = public.dict_obj()
            # get.init = 1
            tmp1 = panelPlugin.panelPlugin().get_cloud_list(get)
        except:
            tmp1 = None
        if tmp1:
            tmp = tmp1[public.to_string([112, 114, 111])]
            ltd = tmp1.get('ltd', -1)
        else:
            ltd = -1
            tmp4 = cache.get(
                public.to_string([112, 95, 116, 111, 107, 101, 110]))
            if tmp4:
                tmp_f = public.to_string([47, 116, 109, 112, 47]) + tmp4
                if not os.path.exists(tmp_f): public.writeFile(tmp_f, '-1')
                tmp = public.readFile(tmp_f)
                if tmp: tmp = int(tmp)
        if not ltd: ltd = -1
        if tmp == None: tmp = -1
        if ltd < 1:
            if ltd == -2:
                tmp3 = public.to_string([
                    60, 115, 112, 97, 110, 32, 99, 108, 97, 115, 115, 61, 34,
                    98, 116, 108, 116, 100, 45, 103, 114, 97, 121, 34, 62, 60,
                    115, 112, 97, 110, 32, 115, 116, 121, 108, 101, 61, 34, 99,
                    111, 108, 111, 114, 58, 32, 35, 102, 99, 54, 100, 50, 54,
                    59, 102, 111, 110, 116, 45, 119, 101, 105, 103, 104, 116,
                    58, 32, 98, 111, 108, 100, 59, 109, 97, 114, 103, 105, 110,
                    45, 114, 105, 103, 104, 116, 58, 53, 112, 120, 34, 62,
                    24050, 36807, 26399, 60, 47, 115, 112, 97, 110, 62, 60, 97,
                    32, 99, 108, 97, 115, 115, 61, 34, 98, 116, 108, 105, 110,
                    107, 34, 32, 111, 110, 99, 108, 105, 99, 107, 61, 34, 98,
                    116, 46, 115, 111, 102, 116, 46, 117, 112, 100, 97, 116,
                    97, 95, 108, 116, 100, 40, 41, 34, 62, 32493, 36153, 60,
                    47, 97, 62, 60, 47, 115, 112, 97, 110, 62
                ])
            elif tmp == -1:
                tmp3 = public.to_string([
                    60, 115, 112, 97, 110, 32, 99, 108, 97, 115, 115, 61, 34,
                    98, 116, 112, 114, 111, 45, 102, 114, 101, 101, 34, 32,
                    111, 110, 99, 108, 105, 99, 107, 61, 34, 98, 116, 46, 115,
                    111, 102, 116, 46, 117, 112, 100, 97, 116, 97, 95, 99, 111,
                    109, 109, 101, 114, 99, 105, 97, 108, 95, 118, 105, 101,
                    119, 40, 41, 34, 32, 116, 105, 116, 108, 101, 61, 34,
                    28857, 20987, 21319, 32423, 21040, 21830, 19994, 29256, 34,
                    62, 20813, 36153, 29256, 60, 47, 115, 112, 97, 110, 62
                ])
            elif tmp == -2:
                tmp3 = public.to_string([
                    60, 115, 112, 97, 110, 32, 99, 108, 97, 115, 115, 61, 34,
                    98, 116, 112, 114, 111, 45, 103, 114, 97, 121, 34, 62, 60,
                    115, 112, 97, 110, 32, 115, 116, 121, 108, 101, 61, 34, 99,
                    111, 108, 111, 114, 58, 32, 35, 102, 99, 54, 100, 50, 54,
                    59, 102, 111, 110, 116, 45, 119, 101, 105, 103, 104, 116,
                    58, 32, 98, 111, 108, 100, 59, 109, 97, 114, 103, 105, 110,
                    45, 114, 105, 103, 104, 116, 58, 53, 112, 120, 34, 62,
                    24050, 36807, 26399, 60, 47, 115, 112, 97, 110, 62, 60, 97,
                    32, 99, 108, 97, 115, 115, 61, 34, 98, 116, 108, 105, 110,
                    107, 34, 32, 111, 110, 99, 108, 105, 99, 107, 61, 34, 98,
                    116, 46, 115, 111, 102, 116, 46, 117, 112, 100, 97, 116,
                    97, 95, 112, 114, 111, 40, 41, 34, 62, 32493, 36153, 60,
                    47, 97, 62, 60, 47, 115, 112, 97, 110, 62
                ])
            if tmp >= 0 and ltd in [-1, -2]:
                if tmp == 0:
                    tmp2 = public.to_string([27704, 20037, 25480, 26435])
                    tmp3 = public.to_string([
                        60, 115, 112, 97, 110, 32, 99, 108, 97, 115, 115, 61,
                        34, 98, 116, 112, 114, 111, 34, 62, 123, 48, 125, 60,
                        115, 112, 97, 110, 32, 115, 116, 121, 108, 101, 61, 34,
                        99, 111, 108, 111, 114, 58, 32, 35, 102, 99, 54, 100,
                        50, 54, 59, 102, 111, 110, 116, 45, 119, 101, 105, 103,
                        104, 116, 58, 32, 98, 111, 108, 100, 59, 34, 62, 123,
                        49, 125, 60, 47, 115, 112, 97, 110, 62, 60, 47, 115,
                        112, 97, 110, 62
                    ]).format(
                        public.to_string([21040, 26399, 26102, 38388, 65306]),
                        tmp2)
                else:
                    tmp2 = time.strftime(
                        public.to_string([37, 89, 45, 37, 109, 45, 37, 100]),
                        time.localtime(tmp))
                    tmp3 = public.to_string([
                        60, 115, 112, 97, 110, 32, 99, 108, 97, 115, 115, 61,
                        34, 98, 116, 112, 114, 111, 34, 62, 21040, 26399,
                        26102, 38388, 65306, 60, 115, 112, 97, 110, 32, 115,
                        116, 121, 108, 101, 61, 34, 99, 111, 108, 111, 114, 58,
                        32, 35, 102, 99, 54, 100, 50, 54, 59, 102, 111, 110,
                        116, 45, 119, 101, 105, 103, 104, 116, 58, 32, 98, 111,
                        108, 100, 59, 109, 97, 114, 103, 105, 110, 45, 114,
                        105, 103, 104, 116, 58, 53, 112, 120, 34, 62, 123, 48,
                        125, 60, 47, 115, 112, 97, 110, 62, 60, 97, 32, 99,
                        108, 97, 115, 115, 61, 34, 98, 116, 108, 105, 110, 107,
                        34, 32, 111, 110, 99, 108, 105, 99, 107, 61, 34, 98,
                        116, 46, 115, 111, 102, 116, 46, 117, 112, 100, 97,
                        116, 97, 95, 112, 114, 111, 40, 41, 34, 62, 32493,
                        36153, 60, 47, 97, 62, 60, 47, 115, 112, 97, 110, 62
                    ]).format(tmp2)
            else:
                tmp3 = public.to_string([
                    60, 115, 112, 97, 110, 32, 99, 108, 97, 115, 115, 61, 34,
                    98, 116, 108, 116, 100, 45, 103, 114, 97, 121, 34, 32, 111,
                    110, 99, 108, 105, 99, 107, 61, 34, 98, 116, 46, 115, 111,
                    102, 116, 46, 117, 112, 100, 97, 116, 97, 95, 108, 116,
                    100, 40, 41, 34, 32, 116, 105, 116, 108, 101, 61, 34,
                    28857, 20987, 21319, 32423, 21040, 20225, 19994, 29256, 34,
                    62, 20813, 36153, 29256, 60, 47, 115, 112, 97, 110, 62
                ])
        else:
            tmp3 = public.to_string([
                60, 115, 112, 97, 110, 32, 99, 108, 97, 115, 115, 61, 34, 98,
                116, 108, 116, 100, 34, 62, 21040, 26399, 26102, 38388, 65306,
                60, 115, 112, 97, 110, 32, 115, 116, 121, 108, 101, 61, 34, 99,
                111, 108, 111, 114, 58, 32, 35, 102, 99, 54, 100, 50, 54, 59,
                102, 111, 110, 116, 45, 119, 101, 105, 103, 104, 116, 58, 32,
                98, 111, 108, 100, 59, 109, 97, 114, 103, 105, 110, 45, 114,
                105, 103, 104, 116, 58, 53, 112, 120, 34, 62, 123, 125, 60, 47,
                115, 112, 97, 110, 62, 60, 97, 32, 99, 108, 97, 115, 115, 61,
                34, 98, 116, 108, 105, 110, 107, 34, 32, 111, 110, 99, 108,
                105, 99, 107, 61, 34, 98, 116, 46, 115, 111, 102, 116, 46, 117,
                112, 100, 97, 116, 97, 95, 108, 116, 100, 40, 41, 34, 62,
                32493, 36153, 60, 47, 97, 62, 60, 47, 115, 112, 97, 110, 62
            ]).format(
                time.strftime(
                    public.to_string([37, 89, 45, 37, 109, 45, 37, 100]),
                    time.localtime(ltd)))
        
        return tmp3, tmp, ltd
    
    # 检查用户绑定是否正确
    def check_user_auth(self, get):
        m_key = 'check_user_auth'
        if m_key in session: return session[m_key]
        u_path = 'data/userInfo.json'
        try:
            userInfo = json.loads(public.ReadFile(u_path))
        except:
            if os.path.exists(u_path): os.remove(u_path)
            return public.returnMsg(False, '宝塔帐户绑定已失效，请在[设置]页面重新绑定!')
        pdata = {
            'access_key': userInfo['access_key'],
            'secret_key': userInfo['secret_key']
        }
        result = public.HttpPost(
            public.GetConfigValue('home') + '/api/panel/check_auth_key', pdata,
            3)
        if result == '0':
            if os.path.exists(u_path): os.remove(u_path)
            return public.returnMsg(False, '宝塔帐户绑定已失效，请在[设置]页面重新绑定!')
        if result == '1':
            session[m_key] = public.returnMsg(True, '绑定有效!')
            return session[m_key]
        return public.returnMsg(True, result)
    
    # PHP探针
    def php_info(self, args):
        php_version = args.php_version.replace('.', '')
        php_path = '/www/server/php/'
        if public.get_webserver() == 'openlitespeed':
            php_path = '/usr/local/lsws/lsphp'
        php_bin = php_path + php_version + '/bin/php'
        php_ini = php_path + php_version + '/etc/php.ini'
        php_ini_lit = "/www/server/php/80/etc/php/80/litespeed/php.ini"
        if os.path.exists(php_ini_lit):
            php_ini = php_ini_lit
        tmp = public.ExecShell(
            php_bin +
            ' -c {} /www/server/panel/class/php_info.php'.format(php_ini))[0]
        if tmp.find('Warning: JIT is incompatible') != -1:
            tmp = tmp.strip().split('\n')[-1]
        try:
            result = json.loads(tmp)
            result['phpinfo'] = {}
            if "modules" not in result:
                result['modules'] = []
            
            if 'php_version' in result:
                result['phpinfo']['php_version'] = result['php_version']
        except Exception as e:
            result = {
                'php_version': php_version,
                'phpinfo': {},
                'modules': [],
                'ini': ''
            }
        
        result['phpinfo']['php_path'] = php_path
        result['phpinfo']['php_bin'] = php_bin
        result['phpinfo']['php_ini'] = php_ini
        result['phpinfo']['modules'] = ' '.join(result['modules'])
        result['phpinfo']['ini'] = result['ini']
        result['phpinfo']['keys'] = {
            "1cache": "缓存器",
            "2crypt": "加密解密库",
            "0db": "数据库驱动",
            "4network": "网络通信库",
            "5io_string": "文件和字符串处理库",
            "3photo": "图片处理库",
            "6other": "其它第三方库"
        }
        del (result['php_version'])
        del (result['modules'])
        del (result['ini'])
        return result
    
    # 取指定行
    def get_lines(self, args):
        if not hasattr(args, 'filename'):
            return public.returnMsg(False, "缺少参数! filename")
        if not os.path.exists(args.filename):
            return public.returnMsg(False, '指定日志文件不存在!')
        num = args.get('num/d', 10)
        s_body = public.GetNumLines(args.filename, num)
        return public.returnMsg(True, s_body)
    
    def log_analysis(self, get):
        public.set_module_logs('log_analysis', 'log_analysis', 1)
        import log_analysis
        log_analysis = log_analysis.log_analysis()
        return log_analysis.log_analysis(get)
    
    def speed_log(self, get):
        import log_analysis
        log_analysis = log_analysis.log_analysis()
        return log_analysis.speed_log(get)
    
    def get_result(self, get):
        import log_analysis
        log_analysis = log_analysis.log_analysis()
        return log_analysis.get_result(get)

    def remove_analysis(self, get):
        import log_analysis
        log_analysis = log_analysis.log_analysis()
        return log_analysis.remove_analysis(get)
    
    def set_cron_task(self, get):
        import log_analysis
        log_analysis = log_analysis.log_analysis()
        return log_analysis.set_cron_task(get)
    
    def get_cron_task(self, get):
        import log_analysis
        log_analysis = log_analysis.log_analysis()
        return log_analysis.get_cron_task(get)
    
    def get_detailed(self, get):
        import log_analysis
        log_analysis = log_analysis.log_analysis()
        return log_analysis.get_detailed(get)
    
    def download_pay_type(self, path):
        public.downloadFile(public.get_url() + '/install/lib/pay_type.json', path)
        return True
    
    def get_pay_type(self, get):
        """
            @name 获取推荐列表
        """
        spath = '{}/data/pay_type.json'.format(public.get_panel_path())
        if os.path.exists(spath) and os.path.getsize(spath) <= 0:
            os.remove(spath)
        
        if not os.path.exists(spath):
            public.run_thread(self.download_pay_type, (spath,))
        try:
            res = public.readFile("data/pay_type.json")
            if 'monitor' not in res:
                os.remove(spath)
                public.run_thread(self.download_pay_type, (spath,))
            data = json.loads(res)
        except json.decoder.JSONDecodeError:
            if os.path.exists(spath):os.remove(spath)
            public.run_thread(self.download_pay_type, (spath,))
            # data = json.loads(public.readFile("data/pay_type.json"))
            data = self.get_default_pay_type()
        except Exception:
            data = self.get_default_pay_type()
        
        import panelPlugin
        plu_panel = panelPlugin.panelPlugin()
        plugin_list = plu_panel.get_cloud_list()
        if not 'pro' in plugin_list: plugin_list['pro'] = -1
        
        for item in data:
            if 'list' in item:
                item['list'] = self.__get_home_list(item['list'], item['type'],
                                                    plugin_list, plu_panel)
                if item['type'] == 1:
                    if len(item['list']) > 4: item['list'] = item['list'][:4]
            if item['type'] == 0 and plugin_list['pro'] >= 0:
                item['show'] = False
        return data
    
    def __get_home_list(self, sList, stype, plugin_list, plu_panel):
        """
            @name 获取首页软件列表推荐
        """
        nList = []
        webserver = public.get_webserver()
        for x in sList:
            for plugin_info in plugin_list['list']:
                if x['name'] == plugin_info['name']:
                    if not 'endtime' in plugin_info or plugin_info[
                        'endtime'] >= 0:
                        x['isBuy'] = True
            is_check = False
            if 'dependent' in x:
                if x['dependent'] == webserver: is_check = True
            else:
                is_check = True
            if is_check:
                info = plu_panel.get_soft_find(x['name'])
                if info:
                    if stype == 1:
                        if plugin_list['pro'] >= 0: continue
                        if not info['setup']:
                            x['install'] = info['setup']
                            nList.append(x)
                    else:
                        x['install'] = info['setup']
                        nList.append(x)
        return nList
    
    def ignore_version(self, get):
        """
        @忽略版本更新
        :param version 忽略的版本号
        """
        version = get.version
        path = '{}/data/no_update.pl'.format(public.get_panel_path())
        try:
            data = json.loads(public.readFile(path))
        except:
            data = []
        
        if not version in data: data.append(version)
        
        public.writeFile(path, json.dumps(data))
        try:
            del (session['updateInfo'])
        except:
            pass
        
        return public.returnMsg(True, "忽略成功，此版本将不再提醒更新.")
    
    def check_auth_ip(self, get):
        """
        @name 检查授权ip
        """
        
        return public.check_auth_ip()
    
    def get_panel_error_info(self, get):
        """
        @name 处理面板常用错误
        """
        
        error = get.error
        force = 0
        if 'force' in get: force = int(get.force)
        
        path = '{}/data/panel_error_info.json'.format(public.get_panel_path())
        if not os.path.exists(path) or force:
            public.downloadFile(
                public.get_url() + '/linux/panel/panel_error_info.json', path)
        
        if not os.path.exists(path):
            return public.returnMsg(False, '获取失败!')
        
        data = []
        try:
            data = json.loads(public.readFile(path))
        except:
            pass
        
        for info in data:
            if 'key' in info:
                for val in info['key']:
                    if not val: continue
                    total, num = 0, 0
                    for tmp in val.split('&'):
                        total += 1
                        if error.lower().find(tmp.lower()) >= 0:
                            num += 1
                    
                    if total > 0 and num == total:
                        return public.returnMsg(True, info['value'])
        return public.returnMsg(
            False,
            '未识别的错误信息，请前往<a href="https://www.bt.cn/bbs" class="btlink">宝塔论坛</a> 发帖提问.'
        )
    
    def Clean_bt_host(self, get):
        '''
        清理本机bt.cn的hosts
        @author wzz <wzz@bt.cn>
        @param get:
        @return:
        '''
        return public.Clean_bt_host()
    
    def Get_ip_info(self, get):
        '''
        获取bt官网ip及用户服务器公网ip归属地列表
        @author wzz <wzz@bt.cn>
        @param get:
        @return:
        '''
        if hasattr(get, "get_speed"):
            return public.Get_ip_info(get.get_speed)
        return public.Get_ip_info()
    
    def Set_bt_host(self, get):
        '''
        设置bt官网(www && api)指定hosts节点
        @author wzz <wzz@bt.cn>
        @param get: get.ip 官网传ip地址,从Get_ip_info方法获取
        @return:
        '''
        if hasattr(get, "ip"):
            return public.Set_bt_host(get.ip)
        return public.Set_bt_host()
    
    @staticmethod
    def get_default_pay_type():
        spath = '{}/data/default_pay_type.json'.format(public.get_panel_path())
        default = [
    {
        "type": 0,
        "pay": "45",
        "describe": "首页-企业版推荐",
        "show": True,
        "route": "home",
        "name": "ltd",
        "price": "999.99",
        "preview": "https://www.bt.cn/new/product/linux_ltd.html",
        "ps": [
			"5分钟极速响应",
			"15天无理由退款",
            "30+款付费插件",
            "20+企业版专享功能",
            "2张SSL商用证书（年付）",
            "1000条免费短信（年付）",
            "专享企业服务群（年付）"
           
        ]
    },
    {
        "type": 1,
        "describe": "首页-软件管理-常用软件推荐",
        "show": True,
        "route": "home",
        "list": [
            {
                "pay": "40",
                "title": "网站防火墙",
                "name": "btwaf",
                "isBuy": False,
                "install": False,
                "pid": 100000010,
                "dependent": "nginx",
                "pluginType": "pro",
                "preview": "https://www.bt.cn/new/product_nginx_firewall.html",
                "ps": "web防火墙，有效抵御CC攻击、SQL注入、XSS跨站攻击、建站程序漏洞、一句话木马等常见渗透攻击"
            },
            {
                "pay": "40",
                "title": "网站防火墙",
                "name": "btwaf_httpd",
                "install": False,
                "isBuy": False,
                "pid": 100000012,
                "pluginType": "pro",
                "dependent": "apache",
                "preview": "https://www.bt.cn/new/product_nginx_firewall.html",
                "ps": "web防火墙，有效抵御CC攻击、SQL注入、XSS跨站攻击、建站程序漏洞、一句话木马等常见渗透攻击"
            },
            {
                "pay": "41",
                "title": "网站监控报表-重构版",
                "name": "monitor",
                "isBuy": False,
                "install": False,
                "pluginType": "pro",
                "pid": 100000014,
                "preview": "https://www.bt.cn/new/product_website_total.html",
                "ps": "网站监控报表，实时精确统计网站流量、ip、uv、pv、请求、蜘蛛等数据"
            },
            {
                "pay": "42",
                "title": "堡塔企业级防篡改-重构版",
                "name": "tamper_core",
                "isBuy": False,
                "install": False,
                "preview": "",
                "pid": 100000067,
                "pluginType": "ltd",
                "ps": "事件型防篡改程序,可有效保护网站重要文件不被木马篡改"
            },
			{
                "pay": "43",
                "title": "堡塔防入侵",
                "name": "bt_security",
                "isBuy": False,
                "install": False,
                "pid": 100000054,
                "pluginType": "ltd",
                "preview": "",
                "ps": "防御大多数的入侵提权攻击造成的挂马和被挖矿"
            }
        ]
    },
    {
        "type": 2,
        "pay": "33",
        "describe": "首页-状态-任务管理器",
        "show": True,
        "route": "home",
        "list": []
    },
    {
        "type": 3,
        "pay": "34",
        "describe": "首页-安全入口-推荐安全软件",
        "show": True,
        "route": "home",
        "list": []
    },
    {
        "type": 4,
        "pay": "35",
        "describe": "网站-网站加速",
        "show": False,
        "name": "waf_nginx",
        "title": "网站加速",
        "pluginName": "堡塔nginx站点加速",
        "ps": "基于nginx页面缓存的网站加速插件,推荐WordPress用户安装，效果显著，仅支持Nginx",
        "preview": "",
        "eventList": [
            {
                "event": "",
                "version": ""
            }
        ]
    },
    {
        "type": 5,
        "describe": "网站-设置推荐",
        "show": True,
        "list": [
            {
                "title": "防火墙",
                "name": "btwaf",
                "pay": "46",
                "pluginName": "Nginx网站防火墙",
                "ps": "有效拦截SQL 注入、XSS跨站、恶意代码、网站挂马等常见攻击，过滤恶意访问，降低数据泄露的风险，保障网站的可用性。",
                "preview": "https://www.bt.cn/new/product_nginx_firewall.html",
                "dependent": "nginx",
                "pluginType": "pro",
                "eventList": [
                    {
                        "event": "site_waf_config('$siteName')",
                        "version": "5.2.0"
                    }
                ]
            },
            {
                "title": "防火墙",
                "name": "btwaf_httpd",
                "pay": "46",
                "pluginName": "网站防火墙",
                "ps": "有效拦截SQL 注入、XSS跨站、恶意代码、网站挂马等常见攻击，过滤恶意访问，降低数据泄露的风险，保障网站的可用性。",
                "preview": "https://www.bt.cn/new/product_nginx_firewall.html",
                "dependent": "apache",
                "pluginType": "pro",
                "eventList": [
                    {
                        "event": "site_waf_config('$siteName')",
                        "version": "5.2.0"
                    }
                ]
            },
            {
                "title": "统计",
                "name": "total",
                "pay": "47",
                "pluginName": "网站监控报表",
                "ps": "快速分析网站运行状况，实时精确统计网站流量、ip、uv、pv、请求、蜘蛛等数据，网站SEO优化利器",
                "preview": "https://www.bt.cn/new/product_website_total.html",
                "dependent": "apache",
                "pluginType": "pro",
                "eventList": [
                    {
                        "event": "WebsiteReport('$siteName')",
                        "version": "5.0"
                    }
                ]
            },
            {
                "title": "统计",
                "name": "total",
                "pay": "47",
                "pluginName": "网站监控报表",
                "ps": "快速分析网站运行状况，实时精确统计网站流量、ip、uv、pv、请求、蜘蛛等数据，网站SEO优化利器",
                "preview": "https://www.bt.cn/new/product_website_total.html",
                "dependent": "nginx",
                "pluginType": "pro",
                "eventList": [
                    {
                        "event": "WebsiteReport('$siteName')",
                        "version": "5.0"
                    }
                ]
            }
        ]
    },
    {
        "type": 6,
        "show": True,
        "describe": "网站管理-推荐安全软件",
        "list": [
            {
                "title": "网站防篡改程序",
                "pay": "60",
                "name": "tamper_proof",
                "product_introduce": [
                    "保护站点内容安全",
                    "阻止黑客非法修改网页",
                    "阻止网站被挂马",
                    "阻止其他入侵行为"
                ],
                "previewImg": "https://www.bt.cn/Public/new/plugin/introduce/site/tamper_proof_preview.png",
                "menu_id": 15,
				"menu_name":"防篡改",
                "isBuy": False,
                "pid": 100000015,
                "pluginType": "pro",
                "preview": "",
                "ps": "事件型防篡改程序,可有效保护网站重要文件不被木马篡改"
            },
            {
                "title": "限制访问型证书",
                "pay": "61",
                "name": "ssl_verify",
                "pluginType": "ltd",
                "product_introduce": [
                    "限制指定人员访问",
                    "双向认证",
                    "内网自签SSL"
                ],
                "previewImg": "https://www.bt.cn/Public/new/plugin/introduce/site/ssl_verify_preview.png",
                "menu_id": 3,
				"menu_name":"访问限制",
                "isBuy": False,
                "pid": 100000062,
                "preview": "",
                "ps": "提供双向认证证书，可用于限制指定人员访问"
            }
        ]
    },
    {
        "type": 7,
        "show": True,
        "describe": "文件管理-推荐安全软件",
        "list": [
            {
                "title": "文件同步",
                "pluginName": "文件同步",
                "pay": "70",
                "name": "rsync",
                "pluginType": "pro",
                "ps": "基于rsync开发的文件同步工具，可用于异地备份、多台主机之间的文件实时或增量同步",
                "previewImg": "https://www.bt.cn/Public/new/plugin/rsync/1.png",
                "menu_id": 15,
                "isBuy": False,
                "pid": 100000005,
                "preview": ""
            }
        ]
    }
]
        if os.path.isfile(spath):
            try:
                res_data = json.loads(public.readFile(spath))
                if isinstance(res_data, list):
                    return res_data
            except json.JSONDecodeError:
                pass
            # 再次出错时，保障网站列表可以展示
            return default
        return default
    
    # 获取指定天数的网络Io
    def GetNetWorkIoByDay(self, get):
        try:
            if not hasattr(get, 'day'):
                return public.returnMsg(False, '参数错误!')
            day = int(get.day)
            # 获取今天0点时间戳
            result = []
            end_time = int(time.time())
            start_time = int(datetime.now().replace(tzinfo=timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0).timestamp())
            for i in range(day):
                time_name = datetime.utcfromtimestamp(start_time).strftime('%Y-%m-%d')
                data = public.M('network').dbfile('system').where(
                    "addtime>=? AND addtime<=?", (start_time, end_time)
                ).field(
                    'id,up,down,total_up,total_down,down_packets,up_packets,addtime'
                ).order('id desc').select()
                total_up = [i['total_up'] for i in data]
                total_down = [i['total_down'] for i in data]
                total_down.sort(reverse=True)
                total_up.sort(reverse=True)
                if total_down:
                    total_down = total_down[0] - total_down[-1]
                else:
                    total_down = 0
                if total_up:
                    total_up = total_up[0] - total_up[-1]
                else:
                    total_up = 0
                result.append({
                    'time': time_name,
                    'total_up': total_up,
                    'total_down': total_down
                })
                end_time = start_time
                start_time = start_time - 86400
            return result
        except:
            pass

    def create_sql_index(self):
        try:
            import db
            sql = db.Sql().dbfile('system')
            if not sql.query("SELECT name FROM sqlite_master WHERE type='index' AND name='cpu'"):
                sql.execute("CREATE INDEX 'cpu' ON 'cpuio'('addtime')")
            if not sql.query("SELECT name FROM sqlite_master WHERE type='index' AND name='ntwk'"):
                sql.execute("CREATE INDEX 'ntwk' ON 'network'('addtime')")
            if not sql.query("SELECT name FROM sqlite_master WHERE type='index' AND name='disk'"):
                sql.execute("CREATE INDEX 'disk' ON 'diskio'('addtime')")
            if not sql.query("SELECT name FROM sqlite_master WHERE type='index' AND name='load'"):
                sql.execute("CREATE INDEX 'load' ON 'load_average'('addtime')")
            if not sql.query("SELECT name FROM sqlite_master WHERE type='index' AND name='proc'"):
                sql.execute("CREATE INDEX 'proc' ON 'process_top_list'('addtime')")
            public.writeFile('data/sql_index.pl', 'True')
        except:
            pass