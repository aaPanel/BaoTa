# coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: lkq <lkq@bt.cn>
# |
# | 日志分析工具
# +-------------------------------------------------------------------
import json
import os
import time
import public
import datetime
import crontab
import urllib


def save_analysis(func):
    def wrapper(*args, **kwargs):
        result = {}
        result['data'] = func(*args, **kwargs)
        path = ''
        if hasattr(args[1], 'path'):
            path = args[1].path
        p = int(args[1].p) if hasattr(args[1], 'p') else 1
        row = int(args[1].row) if hasattr(args[1], 'row') else 10
        data = {path: []}
        if result['data']['start_time'] != "2022/2/22 22:22:22":
            if not os.path.exists('/www/server/panel/data/analysis.json'):
                data = {}
            else:
                data = json.loads(public.ReadFile('/www/server/panel/data/analysis.json'))
            if path not in data.keys():
                data[path] = []
            if result['data']:
                if result['data'] not in data[path]:
                    data[path].append(result['data'])
            public.WriteFile('/www/server/panel/data/analysis.json', json.dumps(data))
            data[path].reverse()
        result.update(public.get_page(len(data[path]), p, row))
        result['data'] = data[path][p * row - row:p * row]
        return result

    return wrapper


class log_analysis:
    path = '/www/server/panel/script'
    log_analysis_path = '/www/server/panel/script/log_analysis.sh'
    logs_path = '/www/server/panel/logs/analysis/'

    def __init__(self):
        if not os.path.exists(self.path + '/log/'): os.makedirs(self.path + '/log/')
        if not os.path.exists(self.log_analysis_path):
            log_analysis_data = '''help(){
	echo  "Usage: ./action.sh [options] [FILE] [OUTFILE]     "
	echo  "Options:"
	echo  "xxx.sh san_log     [FILE] 获取成功访问请求中带有xss|sql|铭感信息|php代码执行 关键字的日志列表  [OUTFILE]   11"
	echo  "xxx.sh san     [FILE] 获取成功访问请求中带有sql关键字的日志列表   [OUTFILE]   11  "
}

if [ $# == 0 ]
then
	help
	exit
fi

if [ ! -e $2 ]
then
	echo -e "$2: 日志文件不存在"
	exit
fi

if [ ! -d "log" ]
then
	mkdir log
fi

echo "[*] Starting ..."

if  [ $1 == "san_log" ]
then
    echo "1">./log/$3
	echo "开始获取xss跨站脚本攻击日志..."

	grep -E ' (200|302|301|500|444|403|304) ' $2  | grep -i -E "(javascript|data:|alert\(|onerror=|%3Cimg%20src=x%20on.+=|%3Cscript|%3Csvg/|%3Ciframe/|%3Cscript%3E).*?HTTP/1.1" >./log/$3xss.log

	echo "分析日志已经保存到./log/$3xss.log"
	echo "扫描到攻击次数: "`cat ./log/$3xss.log |wc -l`
	echo "20">./log/$3


	echo  "开始获取sql注入漏洞攻击日志..."
	echo "分析日志已经保存到./log/$3sql.log"
grep -E ' (200|302|301|500|444|403) ' $2 | grep -i -E "(from.+?information_schema.+|select.+(from|limit)|union(.*?)select|extractvalue\(|case when|extractvalue\(|updatexml\(|sleep\().*?HTTP/1.1" > ./log/$3sql.log
    echo "扫描到攻击次数: "`cat ./log/$3sql.log |wc -l`
    echo "40">./log/$3

	echo -e "开始获取文件遍历/代码执行/扫描器信息/配置文件等相关日志"
	grep -E ' (200|302|301|500|444|403) ' $2 | grep -i -E "(\.\.|WEB-INF|/etc|\w\{1,6\}\.jsp |\w\{1,6\}\.php|\w+\.xml |\w+\.log |\w+\.swp |\w*\.git |\w*\.svn |\w+\.json |\w+\.ini |\w+\.inc |\w+\.rar |\w+\.gz |\w+\.tgz|\w+\.bak |/resin-doc).*?HTTP/1.1" >./log/$3san.log
	echo "分析日志已经保存到./log/$3san.log"
	echo "扫描到攻击次数: "`cat ./log/$3san.log |wc -l`
	echo "50">./log/$3


	echo -e "开始获取php代码执行扫描日志"
	grep -E ' (200|302|301|500|444|403) ' $2 | grep -i -E "(gopher://|php://|file://|phar://|dict://data://|eval\(|file_get_contents\(|phpinfo\(|require_once\(|copy\(|\_POST\[|file_put_contents\(|system\(|base64_decode\(|passthru\(|\/invokefunction\&|=call_user_func_array).*?HTTP/1.1" >./log/$3php.log
	echo "分析日志已经保存到./log/$3php.log"
	echo "扫描到攻击次数: "`cat ./log/$3php.log |wc -l`
	echo "60">./log/$3


	echo -e "正在统计访问次数最多ip的次数和值"
# 	cat $2|awk -F" " '{print $1}'|sort|uniq -c|sort -nrk 1 -t' '|head -100
	awk '{print $1}' $2 |sort|uniq -c |sort -nr |head -100 >./log/$3ip.log
	echo "80">./log/$3


    echo -e "正在统计访问次数最多的请求接口的url的次数和值"
	awk '{print $7}' $2 |sort|uniq -c |sort -nr |head -100 >./log/$3url.log
	echo "100">./log/$3


elif [ $1 == "san" ]
then
    echo "1">./log/$3
	echo "开始获取xss跨站脚本攻击日志..."
	grep -E ' (200|302|301|500|444|403|304) ' $2  | grep -i -E "(javascript|data:|alert\(|onerror=|%3Cimg%20src=x%20on.+=|%3Cscript|%3Csvg/|%3Ciframe/|%3Cscript%3E).*?HTTP/1.1" >./log/$3xss.log
	echo "分析日志已经保存到./log/$3xss.log"
	echo "扫描到攻击次数: "`cat ./log/$3xss.log |wc -l`
	echo "20">./log/$3

	echo  "开始获取sql注入漏洞攻击日志..."
	echo "分析日志已经保存到./log/$3sql.log"
grep -E ' (200|302|301|500|444|403) ' $2 | grep -i -E "(from.+?information_schema.+|select.+(from|limit)|union(.*?)select|extractvalue\(|case when|extractvalue\(|updatexml\(|sleep\().*?HTTP/1.1" > ./log/$3sql.log
    echo "扫描到攻击次数: "`cat ./log/$3sql.log |wc -l`
    echo "40">./log/$3

	echo -e "开始获取文件遍历/代码执行/扫描器信息/配置文件等相关日志"
	grep -E ' (200|302|301|500|444|403) ' $2 | grep -i -E "(\.\.|WEB-INF|/etc|\w\{1,6\}\.jsp |\w\{1,6\}\.php|\w+\.xml |\w+\.log |\w+\.swp |\w*\.git |\w*\.svn |\w+\.json |\w+\.ini |\w+\.inc |\w+\.rar |\w+\.gz |\w+\.tgz|\w+\.bak |/resin-doc).*?HTTP/1.1" >./log/$3san.log

	echo "分析日志已经保存到./log/$3san.log"
	echo "扫描到攻击次数: "`cat ./log/$3san.log |wc -l`
	echo "60">./log/$3

	echo -e "开始获取php代码执行扫描日志"
	grep -E ' (200|302|301|500|444|403) ' $2 | grep -i -E "(gopher://|php://|file://|phar://|dict://data://|eval\(|file_get_contents\(|phpinfo\(|require_once\(|copy\(|\_POST\[|file_put_contents\(|system\(|base64_decode\(|passthru\(|\/invokefunction\&|=call_user_func_array).*?HTTP/1.1" >./log/$3php.log
	echo "分析日志已经保存到./log/$3php.log"
	echo "扫描到攻击次数: "`cat ./log/$3php.log |wc -l`
	echo "100">./log/$3

else
	help
fi

echo "[*] shut down"
'''
            public.WriteFile(self.log_analysis_path, log_analysis_data)

    def get_log_format(self, path):
        '''
        @获取日志格式
        '''
        f = open(path, 'r')
        data = None
        for i in f:
            data = i.split()
            break
        f.close()
        if not data: return False
        if not public.check_ip(data[0]): return False
        if len(data) < 6: return False
        return True

    def log_analysis(self, get):
        '''
        分析日志
        @param path:需要分析的日志
        @return 返回具体的分析结果
        @ 需要使用异步的方式进行扫描
        '''
        path = get.path
        log_path = public.Md5(path)
        serverType = public.get_webserver()
        # if serverType == "nginx":
        #     pass
        # elif serverType == 'apache':
        #     path = path.strip(".log") + '-access_log'
        # else:
        #     path = path.strip(".log") + '_ols.access_log'
        if not os.path.exists(path): return public.ReturnMsg(False, '没有该日志文件')
        if os.path.getsize(path) > 9433107294: return public.ReturnMsg(False, '日志文件太大！')
        if os.path.getsize(path) < 10: return public.ReturnMsg(False, '日志文件为空')
        if self.get_log_format(path):
            public.ExecShell(
                "cd %s && bash %s san_log %s %s &" % (self.path, self.log_analysis_path, path, log_path))
        else:
            public.ExecShell("cd %s && bash %s san %s %s &" % (self.path, self.log_analysis_path, path, log_path))
        speed = self.path + '/log/' + log_path + ".time"
        public.WriteFile(speed, str(time.time()) + "[]" + time.strftime('%Y-%m-%d %X', time.localtime()) + "[]" + "0")
        return public.ReturnMsg(True, '启动扫描成功')

    def speed_log(self, get):
        '''
        扫描进度
        @param path:扫描的日志文件
        @return 返回进度
        '''
        path = get.path.strip()
        log_path = public.Md5(path)
        speed = self.path + '/log/' + log_path
        if not os.path.exists(speed): return public.ReturnMsg(False, '该目录没有扫描')
        if os.path.getsize(speed) < 1: return public.ReturnMsg(False, '日志文件为空')
        try:
            data = public.ReadFile(speed)
            data = int(data)
            if data == 100:
                time_data, start_time, status = public.ReadFile(self.path + '/log/' + log_path + ".time").split("[]")
                public.WriteFile(speed + ".time", str(time.time() - float(time_data)) + "[]" + start_time + "[]" + "1")
            return public.ReturnMsg(True, data)
        except:
            return public.ReturnMsg(True, 0)

    def get_log_count(self, path, is_body=False):
        count = 0
        if is_body:
            if not os.path.exists(path): return ''
            data = ''
            with open(path, 'r') as f:
                for i in f:
                    count += 1
                    data = data.replace('<', '&lt;').replace('>', '&gt;') + i.replace('<', '&lt;').replace('>', '&gt;')
                    if count >= 300: break
            return data
        else:
            if not os.path.exists(path): return count
            with open(path, 'rb') as f:
                for i in f:
                    count += 1
            return count

    @save_analysis
    def get_result(self, get):
        '''
        扫描结果
        @param path:扫描的日志文件
        @return 返回结果
        '''
        try:
            path = get.path.strip()
            log_path = public.Md5(path)
            speed = self.path + '/log/' + log_path
            result = {}
            if os.path.exists(speed):
                result['is_status'] = True
            else:
                result['is_status'] = False
            if os.path.exists(speed + ".time"):
                time_data, start_time, status = public.ReadFile(self.path + '/log/' + log_path + ".time").split("[]")
                if status == '1' or start_time == 1:
                    result['time'] = time_data
                    result['start_time'] = start_time
            else:
                result['time'] = "0"
                result['start_time'] = "2022/2/22 22:22:22"
            if 'time' not in result:
                result['time'] = "0"
                result['start_time'] = "2022/2/22 22:22:22"
            result['xss'] = self.get_log_count(speed + 'xss.log')
            result['sql'] = self.get_log_count(speed + 'sql.log')
            result['san'] = self.get_log_count(speed + 'san.log')
            result['php'] = self.get_log_count(speed + 'php.log')
            result['ip'] = self.get_log_count(speed + 'ip.log')
            result['url'] = self.get_log_count(speed + 'url.log')
            self.save_result(path, result['start_time'])
            return result
        except:
            return {}

    # 保存历史执行记录

    def get_detailed(self, get):
        try:
            path = get.path.strip()
            log_path = public.Md5(path)
            speed = self.path + '/log/' + log_path
            type_list = ['xss', 'sql', 'san', 'php', 'ip', 'url']
            if get.type not in type_list: return public.ReturnMsg(False, '类型不匹配')
            if hasattr(get, 'time') and time != '':
                try:
                    name = str(int(datetime.datetime.strptime(get.time, "%Y-%m-%d %H:%M:%S").timestamp()))
                except:
                    name = '1645539742'
                if os.path.exists(os.path.join(self.logs_path, name)):
                    log = json.loads(public.readFile(os.path.join(self.logs_path, name)))
                    if get.type == 'all':
                        return public.returnMsg(True, log)
                    else:
                        return public.returnMsg(True, log[get.type])
                else:
                    return public.returnMsg(False, '历史记录读取失败！')
            if not os.path.exists(speed + get.type + '.log'): return public.ReturnMsg(False, '记录不存在')
            return self.get_log_count(speed + get.type + '.log', is_body=True)
        except:
            return ''

    def save_result(self, path, name):
        try:
            try:
                name = str(int(datetime.datetime.strptime(name, "%Y-%m-%d %H:%M:%S").timestamp()))
            except:
                name = '1645539742'
            if not os.path.exists(self.logs_path):
                os.makedirs(self.logs_path)
            if os.path.exists(os.path.join(self.logs_path, name)):
                return 0
            get = public.dict_obj()
            get.action = 'get_detailed'
            get.path = path
            types = ['xss', 'sql', 'san', 'php', 'ip', 'url']
            logs = {}
            for tp in types:
                get.type = tp
                data = self.get_detailed(get)

                # # 确保 data 是字符串
                if not isinstance(data, str):
                    continue

                data = data.strip().split('\n')
                type_logs = []
                for i in data:
                    if tp not in ['ip', 'url']:
                        try:
                            i.replace('"', '')
                            l = i.strip().split(' ')
                            ip = l[0]
                            time = l[3][1:] if len(l[3]) > 1 else l[3]
                            url = public.xsssec2(l[6])
                            ua = ' '.join(l[11:]).replace('"', '')
                            type_logs.append({'ip': ip, 'time': time, 'url': url, 'ua': ua})
                        except:
                            pass
                    else:
                        l = i.strip().split(' ')
                        num = l[0]
                        path = urllib.parse.quote(l[1])
                        type_logs.append({'num': num, 'path': path})
                logs[tp] = type_logs
            if not os.path.exists(os.path.join(self.logs_path, name)):
                public.writeFile(os.path.join(self.logs_path, name), json.dumps(logs))
        except:
            pass

    def set_cron_task(self, get):  # 已不再使用，告警在告警模块中添加
        public.set_module_logs('log_analysis', 'set_cron_task', 1)
        try:
            cron_task_path = '/www/server/panel/data/cron_task_analysis.json'
            if not (hasattr(get, 'path') and hasattr(get, 'cycle') and hasattr(get, 'status') and hasattr(get, 'channel')):
                return public.returnMsg(False, '参数有误！')
            channel = get['channel']
            path = get['path']
            cycle = get['cycle']
            status = get['status']
            if not os.path.exists(cron_task_path):
                public.writeFile(cron_task_path, json.dumps({}))
            # 检查path是否真实存在
            if not os.path.exists(path):
                return public.returnMsg(False, '日志{}不存在'.format(path))
            data = json.loads(public.readFile(cron_task_path))
            if int(status) == 1:
                self.add_crontab()
                data[path] = {'status': int(status), 'cycle': cycle, 'path': path}
                if get.channel != '':
                    data['channel'] = channel
            else:
                if path in data.keys():
                    del data[path]
                if len(data) <= 1:
                    self.del_crontab()
            public.writeFile(cron_task_path, json.dumps(data))
            return public.returnMsg(True, '定时任务设置成功！')
        except:
            return public.returnMsg(False, '定时任务设置失败')

    def add_crontab(self):
        """
        @name 构造日志切割任务
        """
        cron_name = '[勿删]web日志定期检测服务'
        if not public.M('crontab').where('name=?', (cron_name,)).count():
            cmd = 'btpython /www/server/panel/script/cron_log_analysis.py'
            args = {
                "name": cron_name,
                "type": 'day',
                "where1": '',
                "hour": '11',
                "minute": '50',
                "sName": "",
                "sType": 'toShell',
                "notice": '0',
                "notice_channel": '',
                "save": '',
                "save_local": '1',
                "backupTo": '',
                "sBody": cmd,
                "urladdress": ''
            }
            import crontab
            res = crontab.crontab().AddCrontab(args)
            if res and "id" in res.keys():
                return True
            return False
        return True

    def del_crontab(self):
        """
        @name 删除项目定时任务
        @auther hezhihong<2022-10-31>
        @return
        """
        try:
            cron_name = '[勿删]web日志定期检测服务'
            p = crontab.crontab()
            id = public.M('crontab').where("name=?", (cron_name,)).getField('id')
            args = {"id": id}
            p.DelCrontab(args)
            return True
        except:
            return False

    def get_cron_task(self, get):
        if not hasattr(get, 'path'):
            return public.returnMsg(False, '参数有误！')
        path = get.path
        cron_task_path = '/www/server/panel/data/cron_task_analysis.json'
        default = {'channel': '', 'status': 0, 'cycle': 1, 'path': ''}
        if not os.path.exists(cron_task_path):
            public.writeFile(cron_task_path, json.dumps({}))
        data = json.loads(public.readFile(cron_task_path))
        result = data.get(path, default)
        if 'channel' not in result.keys():
            result['channel'] = data.get('channel', '')
        return result

    # 清空web日志分析数据
    def remove_analysis(self, get):
        if not hasattr(get, "path"):
            return public.returnMsg(False, '缺少参数path')

        path = get.path.strip()

        if not os.path.exists(path):
            return public.returnMsg(False, '日志文件不存在')

        filedata = '/www/server/panel/data/analysis.json'
        try:
            data = json.loads(public.readFile(filedata))
        except:
            data = {}

        if not data:
            return public.returnMsg(False, "清空成功")

        if path in data:
            del data[path]
            public.writeFile(filedata, json.dumps(data))

        target_directory = self.path + '/log/'

        if os.path.exists(target_directory) and os.path.isdir(target_directory):
            file_path = os.listdir(target_directory)
            for temp in file_path:
                if not os.path.isfile(target_directory + temp):continue
                if temp.find(public.Md5(path)) != -1:
                    os.remove(target_directory + temp)
        else:
            return public.returnMsg(False, "目录不存在")

        return public.returnMsg(True, "清空成功！")






