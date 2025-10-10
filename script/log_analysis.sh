help(){
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
