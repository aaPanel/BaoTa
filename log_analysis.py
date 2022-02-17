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
import os
import public


class log_analysis:
    path = '/www/server/panel/script/'
    log_analysis_path = '/www/server/panel/script/log_analysis.sh'

    def __init__(self):
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
        if not os.path.exists(get.path): return public.ReturnMsg(False, '没有该日志文件')
        if os.path.getsize(get.path) > 9433107294: return public.ReturnMsg(False, '日志文件太大！')
        if os.path.getsize(get.path) < 10: return public.ReturnMsg(False, '日志文件为空')
        log_path = public.Md5(get.path)
        if self.get_log_format(get.path):
            public.ExecShell(
                "cd %s && bash %s san_log %s %s &" % (self.path, self.log_analysis_path, get.path, log_path))
        else:
            public.ExecShell("cd %s && bash %s san %s %s &" % (self.path, self.log_analysis_path, get.path, log_path))
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
        if os.path.getsize(speed) < 1: return public.ReturnMsg(False, '日志文件为空')
        if not os.path.exists(speed): return public.ReturnMsg(False, '该目录没有扫描')
        try:
            data = public.ReadFile(speed)
            data = int(data)
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
                    data = data + i
                    if count >= 300: break
            return data
        else:
            if not os.path.exists(path): return count
            with open(path, 'rb') as f:
                for i in f:
                    count += 1

            return count

    def get_result(self, get):
        '''
        扫描结果
        @param path:扫描的日志文件
        @return 返回结果
        '''
        path = get.path.strip()
        log_path = public.Md5(path)
        speed = self.path + '/log/' + log_path
        result = {}
        result['xss'] = self.get_log_count(speed + 'xss.log')
        result['sql'] = self.get_log_count(speed + 'sql.log')
        result['san'] = self.get_log_count(speed + 'san.log')
        result['php'] = self.get_log_count(speed + 'php.log')
        result['ip'] = self.get_log_count(speed + 'ip.log')
        result['url'] = self.get_log_count(speed + 'url.log')
        return result

    def get_detailed(self, get):
        path = get.path.strip()
        log_path = public.Md5(path)
        speed = self.path + '/log/' + log_path
        type_list = ['xss', 'sql', 'san', 'php', 'ip', 'url']
        if get.type not in type_list: return public.ReturnMsg(False, '类型不匹配')
        if not os.path.exists(speed + get.type + '.log'): return public.ReturnMsg(False, '记录不存在')
        return self.get_log_count(speed + get.type + '.log', is_body=True)