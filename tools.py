# coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author:  hwliang <hwl@bt.cn>
# +-------------------------------------------------------------------

# ------------------------------
# 工具箱
# ------------------------------
import sys
import os
import re
import json

panelPath = '/www/server/panel/'
os.chdir(panelPath)
sys.path.insert(0, panelPath + "class/")
import public, time, json

if sys.version_info[0] == 3: raw_input = input


def check_db():  # 检查数据库
    pass
    # data_func = {
    #     "users": check_users_tb,
    #     "config": check_config_tb,
    # }

    # for tb_name, check_func in data_func.items():
    #     sqlite_obj = public.M(tb_name)
    #     check_func(sqlite_obj)


# 用户表检查
def check_users_tb(sqlite_obj):
    pass
    # user = sqlite_obj.where("id=?", (1,)).find()
    # if not isinstance(user, (dict, list)):
    #     print("users err:{}".format(user))
    #     return
    # username = public.GetRandomString(8).lower()
    # password = public.GetRandomString(8).lower()
    # if not user:  # 表数据为空
    #     sqlite_obj.add("id,username,password", (1, username, password))
    #     print("检测到默认用户丢失,正在修复...")
    #     print("|-新用户名(username): {}".format(username))
    #     print("|-新密码(password): {}".format(password))
    #     return
    # # 表数据库缺失
    # if not user.get("username"):
    #     print("检测到[用户名]为空，正在修复...")
    #     sqlite_obj.where("id=?", (1,)).setField("username", username)
    #     print("|-新用户名(username): {}".format(username))
    # if not user.get("password"):
    #     print("检测到[用户密码]为空，正在修复...")
    #     sqlite_obj.where("id=?", (1,)).setField('password', public.password_salt(public.md5(password), uid=1))
    #     print("|-新密码(password): {}".format(password))


# 配置表检查
def check_config_tb(sqlite_obj):
    config = sqlite_obj.where("id=?", (1,)).find()
    if not isinstance(config, (dict, list)):
        print("config err:{}".format(config))
        return

    webserver = "nginx"
    backup_path = "/www/backup"
    sites_path = "/www/wwwroot"
    status = 1
    mysql_root = public.GetRandomString(8).lower()
    if not config:  # 表数据为空
        sqlite_obj.add("id,webserver,backup_path,sites_path,status,mysql_root", (1, webserver, backup_path, sites_path, status, mysql_root))
        print("检测到面板默认配置丢失，正在修复...")
        print("|-默认运行服务: {}".format(webserver))
        print("|-默认备份路径: {}".format(backup_path))
        print("|-默认网站路径: {}".format(sites_path))
        print("|-默认Mysql密码: {}".format(mysql_root))
        return
    # 表数据库缺失
    if not config.get("webserver"):
        print("检测到[默认运行服务]为空，正在修复...")
        sqlite_obj.where("id=?", (1,)).setField("webserver", webserver)
        print("|-默认运行服务: {}".format(webserver))
    if not config.get("backup_path"):
        print("检测到[默认备份路径]为空，正在修复...")
        sqlite_obj.where("id=?", (1,)).setField("backup_path", backup_path)
        print("|-默认备份路径: {}".format(backup_path))
    if not config.get("sites_path"):
        print("检测到[默认网站路径]为空，正在修复...")
        sqlite_obj.where("id=?", (1,)).setField("sites_path", sites_path)
        print("|-默认网站路径: {}".format(sites_path))
    if not config.get("mysql_root"):
        print("检测到[默认Mysql密码]为空，正在修复...")
        set_mysql_root(mysql_root)
        # sqlite_obj.where("id=?", (1,)).setField("mysql_root", mysql_root)
        # print("|-默认Mysql密码: {}".format(len(mysql_root) * "*"))


# 设置MySQL密码
def set_mysql_root(password):
    import db, os
    sql = db.Sql()

    root_mysql = '''#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH
pwd=$1
/etc/init.d/mysqld stop
mysqld_safe --skip-grant-tables&
echo '正在修改密码...';
echo 'The set password...';
sleep 6

m_version=$(cat /www/server/mysql/version.pl)
if echo "$m_version" | grep -E "(5\.1\.|5\.5\.|5\.6\.|10\.0\.|10\.1\.)" >/dev/null; then
    mysql -uroot -e "UPDATE mysql.user SET password=PASSWORD('${pwd}') WHERE user='root';"
elif echo "$m_version" | grep -E "(10\.4\.|10\.5\.|10\.6\.|10\.7\.|10\.11\.|11\.3\.|11\.4\.)" >/dev/null; then
    mysql -uroot -e "
    FLUSH PRIVILEGES;
    ALTER USER 'root'@'localhost' IDENTIFIED BY '${pwd}';
    ALTER USER 'root'@'127.0.0.1' IDENTIFIED BY '${pwd}';
    FLUSH PRIVILEGES;
    "
elif echo "$m_version" | grep -E "(5\.7\.|8\.[0-9]+\..*|9\.[0-9]+\..*)" >/dev/null; then 
    mysql -uroot -e "
    FLUSH PRIVILEGES;
    update mysql.user set authentication_string='' where user='root' and (host='127.0.0.1' or host='localhost');
    ALTER USER 'root'@'localhost' IDENTIFIED BY '${pwd}';
    ALTER USER 'root'@'127.0.0.1' IDENTIFIED BY '${pwd}';
    FLUSH PRIVILEGES;
    "
else
    mysql -uroot -e "UPDATE mysql.user SET authentication_string=PASSWORD('${pwd}') WHERE user='root';"
fi

mysql -uroot -e "FLUSH PRIVILEGES";
pkill -9 mysqld_safe
pkill -9 mysqld
sleep 2
/etc/init.d/mysqld start

echo '==========================================='
echo "root密码成功修改为: ${pwd}"
echo "The root password set ${pwd}  successuful"'''

    public.writeFile('mysql_root.sh', root_mysql)
    os.system("/bin/bash mysql_root.sh " + password)
    os.system("rm -f mysql_root.sh")

    result = public.M('config').where('id=?', (1,)).setField('mysql_root', password)
    print(result)


# 设置面板密码
def set_panel_pwd(password, ncli=False):
    password = password.strip()
    if not len(password) > 5:
        print("|-错误，密码长度必须大于5位")
        return
    import db
    sql = db.Sql()
    result = public.M('users').where('id=?', (1,)).setField('password', public.password_salt(public.md5(password), uid=1))
    username = public.M('users').where('id=?', (1,)).getField('username')
    if ncli:
        print("|-用户名: " + username)
        print("|-新密码: " + password)
    else:
        print(username)


# 设置数据库目录
def set_mysql_dir(path):
    mysql_dir = '''#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH
oldDir=`cat /etc/my.cnf |grep 'datadir'|awk '{print $3}'`
newDir=$1
mkdir $newDir
if [ ! -d "${newDir}" ];then
    echo 'The specified storage path does not exist!'
    exit
fi
echo "Stopping MySQL service..."
/etc/init.d/mysqld stop

echo "Copying files, please wait..."
\cp -r -a $oldDir/* $newDir
chown -R mysql.mysql $newDir
sed -i "s#$oldDir#$newDir#" /etc/my.cnf

echo "Starting MySQL service..."
/etc/init.d/mysqld start
echo ''
echo 'Successful'
echo '---------------------------------------------------------------------'
echo "Has changed the MySQL storage directory to: $newDir"
echo '---------------------------------------------------------------------'
'''

    public.writeFile('mysql_dir.sh', mysql_dir)
    os.system("/bin/bash mysql_dir.sh " + path)
    os.system("rm -f mysql_dir.sh")


# 封装
def PackagePanel():
    print('========================================================')
    print('|-正在清理日志信息...'),
    public.M('logs').where('id!=?', (0,)).delete()
    print('\t\t\033[1;32m[done]\033[0m')
    print('|-正在清理任务历史...'),
    public.M('tasks').where('id!=?', (0,)).delete()
    print('\t\t\033[1;32m[done]\033[0m')
    print('|-正在清理网络监控记录...'),
    public.M('network').dbfile('system').where('id!=?', (0,)).delete()
    print('\t\033[1;32m[done]\033[0m')
    print('|-正在清理CPU监控记录...'),
    public.M('cpuio').dbfile('system').where('id!=?', (0,)).delete()
    print('\t\033[1;32m[done]\033[0m')
    print('|-正在清理磁盘监控记录...'),
    public.M('diskio').dbfile('system').where('id!=?', (0,)).delete()
    print('\t\033[1;32m[done]\033[0m')
    print('|-正在清理IP信息...'),
    os.system('rm -f /www/server/panel/data/iplist.txt')
    os.system('rm -f /www/server/panel/data/address.pl')
    os.system('rm -f /www/server/panel/data/*.login')
    os.system('rm -f /www/server/panel/data/domain.conf')
    os.system('rm -f /www/server/panel/data/user*')
    os.system('rm -f /www/server/panel/data/admin_path.pl')
    os.system('rm -rf /www/backup/panel/*')
    os.system('rm -f /root/.ssh/*')

    print('\t\033[1;32m[done]\033[0m')
    print('|-正在清理系统使用痕迹...'),
    command = '''cat /dev/null > /var/log/boot.log
cat /dev/null > /var/log/btmp
cat /dev/null > /var/log/cron
cat /dev/null > /var/log/dmesg
cat /dev/null > /var/log/firewalld
cat /dev/null > /var/log/grubby
cat /dev/null > /var/log/lastlog
cat /dev/null > /var/log/mail.info
cat /dev/null > /var/log/maillog
cat /dev/null > /var/log/messages
cat /dev/null > /var/log/secure
cat /dev/null > /var/log/spooler
cat /dev/null > /var/log/syslog
cat /dev/null > /var/log/tallylog
cat /dev/null > /var/log/wpa_supplicant.log
cat /dev/null > /var/log/wtmp
cat /dev/null > /var/log/yum.log
history -c
'''
    os.system(command)
    print('\t\033[1;32m[done]\033[0m')
    if sys.version_info[0] == 3:
        a_input = input('|-是否在首次开机自动按机器配置优化PHP/MySQL配置?(y/n default: y): ')
    else:
        a_input = raw_input('|-是否在首次开机自动按机器配置优化PHP/MySQL配置?(y/n default: y): ')
    if not a_input: a_input = 'y'
    print(a_input)
    if not a_input in ['Y', 'y', 'yes', 'YES']:
        public.ExecShell("rm -f /www/server/panel/php_mysql_auto.pl")
    else:
        public.writeFile('/www/server/panel/php_mysql_auto.pl', "True")

    print("|-请选择idc品牌信息展示设置：")
    print("=" * 50)
    print(" (1) 显示默认宝塔Linux面板信息")
    print(" (2) 显示IDC定制版面板信息")
    print("=" * 50)
    i_input = input("请选择显示的面板信息(default: 1): ")
    if i_input in [2, '2']:
        print("2 显示IDC定制版面板信息")
        print("=" * 50)
    else:
        print("1 显示默认宝塔Linux面板信息")
        print("=" * 50)
        panelPath = '/www/server/panel'
        pFile = panelPath + '/config/config.json'
        pInfo = json.loads(public.readFile(pFile))
        pInfo['title'] = u'宝塔Linux面板'
        pInfo['brand'] = u'宝塔'
        pInfo['product'] = u'Linux面板'
        public.writeFile(pFile, json.dumps(pInfo))
        tFile = panelPath + '/data/title.pl'
        if os.path.exists(tFile):
            os.remove(tFile)

    print("|-请选择用户初始化方式：")
    print("=" * 50)
    print(" (1) 访问面板页面时显示初始化页面")
    print(" (2) 首次启动时自动随机生成新帐号密码")
    print(" (3) 首次启动时自动随机生成新帐号密码和安全路径")
    print("=" * 50)
    p_input = input("请选择初始化方式(default: 1): ")
    print(p_input)
    if p_input in [2, '2']:
        public.writeFile('/www/server/panel/aliyun.pl', "True")
        s_file = '/www/server/panel/install.pl'
        if os.path.exists(s_file): os.remove(s_file)
        public.M('config').where("id=?", ('1',)).setField('status', 1)
    elif p_input in [3, '3']:
        public.writeFile('/www/server/panel/aliyun.pl', "True")
        public.writeFile('/www/server/panel/random_path.pl', "True")
        s_file = '/www/server/panel/install.pl'
        if os.path.exists(s_file): os.remove(s_file)
        public.M('config').where("id=?", ('1',)).setField('status', 1)
    else:
        public.writeFile('/www/server/panel/install.pl', "True")
        public.M('config').where("id=?", ('1',)).setField('status', 0)
    port = public.readFile('data/port.pl').strip()
    print('========================================================')
    print('\033[1;32m|-面板封装成功,请不要再登陆面板做任何其它操作!\033[0m')
    if p_input not in [2, '2', 3, '3']:
        print('\033[1;41m|-面板初始化地址: http://{SERVERIP}:' + port + '/install\033[0m')
    else:
        print('\033[1;41m|-获取初始帐号密码命令:bt default \033[0m')
        print('\033[1;41m|-注意：仅在首次登录面板前能正确获取初始帐号密码 \033[0m')



# 清空正在执行的任务
def CloseTask():
    ncount = public.M('tasks').where('status!=?', (1,)).delete()
    os.system("kill `ps -ef |grep 'python panelSafe.pyc'|grep -v grep|grep -v panelExec|awk '{print $2}'`")
    os.system("kill `ps -ef |grep 'install_soft.sh'|grep -v grep|grep -v panelExec|awk '{print $2}'`")
    os.system('/etc/init.d/bt restart')
    print("成功清理 " + int(ncount) + " 个任务!")


def get_ipaddress():
    '''
        @name 获取本机IP地址
        @author hwliang<2020-11-24>
        @return list
    '''
    ipa_tmp = public.ExecShell("ip a |grep inet|grep -v inet6|grep -v 127.0.0.1|awk '{print $2}'|sed 's#/[0-9]*##g'")[
        0].strip()
    iplist = ipa_tmp.split('\n')
    return iplist


def get_host_all():
    local_ip = ['127.0.0.1', '::1', 'localhost']
    ip_list = []
    bind_ip = get_ipaddress()

    for ip in bind_ip:
        ip = ip.strip()
        if ip in local_ip: continue
        if ip in ip_list: continue
        ip_list.append(ip)
    net_ip = public.httpGet("https://api.bt.cn/api/getipaddress")

    if net_ip:
        net_ip = net_ip.strip()
        if not net_ip in ip_list:
            ip_list.append(net_ip)
    if len(ip_list) > 1:
        ip_list = [ip_list[-1], ip_list[0]]

    print(ip_list)
    return ip_list


# 自签证书
def CreateSSL():
    import base64
    userInfo = public.get_user_info()
    if not userInfo:
        userInfo['uid'] = 0
        userInfo['access_key'] = 'B' * 32
    domains = get_host_all()
    pdata = {
        "action": "get_domain_cert",
        "company": "宝塔面板",
        "domain": ','.join(domains),
        "uid": userInfo['uid'],
        "access_key": userInfo['access_key'],
        "panel": 1
    }
    cert_api = 'https://api.bt.cn/bt_cert'
    res = public.httpPost(cert_api, {'data': json.dumps(pdata)})
    try:
        result = json.loads(res)
        if 'status' in result:
            if result['status']:
                public.writeFile('ssl/certificate.pem', result['cert'])
                public.writeFile('ssl/privateKey.pem', result['key'])
                public.writeFile('ssl/baota_root.pfx', base64.b64decode(result['pfx']), 'wb+')
                public.writeFile('ssl/root_password.pl', result['password'])
                public.writeFile('data/ssl.pl', 'True')
                public.ExecShell("/etc/init.d/bt reload")
                print('1')
                return True
    except:
        print('error:{}'.format(res))
    print('0')
    return False


# 创建文件
def CreateFiles(path, num):
    if not os.path.exists(path): os.system('mkdir -p ' + path)
    import time;
    for i in range(num):
        filename = path + '/' + str(time.time()) + '__' + str(i)
        open(path, 'w+').close()


# 计算文件数量
def GetFilesCount(path):
    i = 0
    for name in os.listdir(path): i += 1
    return i


# 清理系统垃圾
def ClearSystem():
    count = total = 0
    tmp_total, tmp_count = ClearMail()
    count += tmp_count
    total += tmp_total
    print('=======================================================================')
    tmp_total, tmp_count = ClearSession()
    count += tmp_count
    total += tmp_total
    print('=======================================================================')
    tmp_total, tmp_count = ClearOther()
    count += tmp_count
    total += tmp_total
    print('=======================================================================')
    print('\033[1;32m|-系统垃圾清理完成，共删除[' + str(count) + ']个文件,释放磁盘空间[' + ToSize(total) + ']\033[0m')


# 清理邮件日志
def ClearMail():
    rpath = '/var/spool'
    total = count = 0
    import shutil
    con = ['cron', 'anacron', 'mail']
    for d in os.listdir(rpath):
        if d in con: continue
        dpath = rpath + '/' + d
        print('|-正在清理' + dpath + ' ...')
        time.sleep(0.2)
        num = size = 0
        for n in os.listdir(dpath):
            filename = dpath + '/' + n
            fsize = os.path.getsize(filename)
            print('|---[' + ToSize(fsize) + '] del ' + filename),
            size += fsize
            if os.path.isdir(filename):
                shutil.rmtree(filename)
            else:
                os.remove(filename)
            print('\t\033[1;32m[OK]\033[0m')
            num += 1
        print('|-已清理[' + dpath + '],删除[' + str(num) + ']个文件,共释放磁盘空间[' + ToSize(size) + ']')
        total += size
        count += num
    print('=======================================================================')
    print('|-已完成spool的清理，删除[' + str(count) + ']个文件,共释放磁盘空间[' + ToSize(total) + ']')
    return total, count


# 清理php_session文件
def ClearSession():
    spath = '/tmp'
    total = count = 0
    import shutil
    print('|-正在清理PHP_SESSION ...')
    for d in os.listdir(spath):
        if d.find('sess_') == -1: continue
        filename = spath + '/' + d
        fsize = os.path.getsize(filename)
        print('|---[' + ToSize(fsize) + '] del ' + filename),
        total += fsize
        if os.path.isdir(filename):
            shutil.rmtree(filename)
        else:
            os.remove(filename)
        print('\t\033[1;32m[OK]\033[0m')
        count += 1
    print('|-已完成php_session的清理，删除[' + str(count) + ']个文件,共释放磁盘空间[' + ToSize(total) + ']')
    return total, count


# 清空回收站
def ClearRecycle_Bin():
    import files
    f = files.files()
    f.Close_Recycle_bin(None)


# 清理其它
def ClearOther():
    clearPath = [
        {'path': '/www/server/panel', 'find': 'testDisk_'},
        {'path': '/www/wwwlogs', 'find': 'log'},
        {'path': '/tmp', 'find': 'panelBoot.pl'},
        {'path': '/www/server/panel/install', 'find': '.rpm'},
        {'path': '/www/server/panel/install', 'find': '.zip'},
        {'path': '/www/server/panel/install', 'find': '.gz'}
    ]

    total = count = 0
    print('|-正在清理临时文件及网站日志 ...')
    for c in clearPath:
        for d in os.listdir(c['path']):
            if d.find(c['find']) == -1: continue
            filename = c['path'] + '/' + d
            if os.path.isdir(filename): continue
            fsize = os.path.getsize(filename)
            print('|---[' + ToSize(fsize) + '] del ' + filename),
            total += fsize
            os.remove(filename)
            print('\t\033[1;32m[OK]\033[0m')
            count += 1
    public.serviceReload()
    os.system('sleep 1 && /etc/init.d/bt reload > /dev/null &')
    print('|-已完成临时文件及网站日志的清理，删除[' + str(count) + ']个文件,共释放磁盘空间[' + ToSize(total) + ']')
    return total, count


# 关闭普通日志
def CloseLogs():
    try:
        paths = ['/usr/lib/python2.7/site-packages/web/httpserver.py',
                 '/usr/lib/python2.6/site-packages/web/httpserver.py']
        for path in paths:
            if not os.path.exists(path): continue
            hsc = public.readFile(path)
            if hsc.find('500 Internal Server Error') != -1: continue
            rstr = '''def log(self, status, environ):
        if status != '500 Internal Server Error': return;'''
            hsc = hsc.replace("def log(self, status, environ):", rstr)
            if hsc.find('500 Internal Server Error') == -1: return False
            public.writeFile(path, hsc)
    except:
        pass


# 字节单位转换
def ToSize(size):
    ds = ['b', 'KB', 'MB', 'GB', 'TB']
    for d in ds:
        if size < 1024: return str(size) + d
        size = size / 1024
    return '0b'


# 随机面板用户名
def set_panel_username(username=None):
    import db
    sql = db.Sql()
    if username:
        print("|-正在设置面板用户名...")
        re_list = re.findall(r"[^\w,.]+", username)
        if re_list:
            print("|-错误，密码不能包含中文和特殊字符： {}".format(" ".join(re_list)))
            return
        if username in ['admin', 'root']:
            print("|-错误，不能使用过于简单的用户名")
            return

        public.M('users').where('id=?', (1,)).setField('username', username)
        print("|-新用户名: %s" % username)
        return

    username = public.M('users').where('id=?', (1,)).getField('username')
    if username == 'admin':
        username = public.GetRandomString(8).lower()
        public.M('users').where('id=?', (1,)).setField('username', username)
    print('username: ' + username)


# 设定idc
def setup_idc():
    try:
        panelPath = '/www/server/panel'
        filename = panelPath + '/data/o.pl'
        if not os.path.exists(filename): return False
        o = public.readFile(filename).strip()
        c_url = 'http://www.bt.cn/api/idc/get_idc_info_bycode?o=%s' % o
        idcInfo = json.loads(public.httpGet(c_url))
        if not idcInfo['status']: return False
        pFile = panelPath + '/config/config.json'
        pInfo = json.loads(public.readFile(pFile))
        pInfo['brand'] = idcInfo['msg']['name']
        pInfo['product'] = u'与宝塔联合定制版'
        public.writeFile(pFile, json.dumps(pInfo))
        tFile = panelPath + '/data/title.pl'
        titleNew = pInfo['brand'] + u'面板'
        if os.path.exists(tFile):
            title = public.GetConfigValue('title')
            if title == '' or title == '宝塔Linux面板':
                public.writeFile(tFile, titleNew)
                public.SetConfigValue('title', titleNew)
        else:
            public.writeFile(tFile, titleNew)
            public.SetConfigValue('title', titleNew)
        return True
    except:
        pass

def set_panel_port(panelport):
    input_port=int(panelport)

    if not input_port:
            print("|-错误，未输入任何有效端口")
            return
    if input_port in [80, 443, 21, 20, 22]:
        print("|-错误，请不要使用常用端口作为面板端口")
        return

    try:
        port_str = public.readFile('data/port.pl')
        if port_str:
            old_port = int(port_str)
        else:
            old_port = 0
    except:
        old_port = 0

    if old_port == input_port:
        print("|-错误，与面板当前端口一致，无需修改")
        return
    if input_port > 65535 or input_port < 1:
        print("|-错误，可用端口范围在1-65535之间")
        return

    print("|-开始设置面板端口")
    is_exists = public.ExecShell("lsof -i:%s|grep LISTEN|grep -v grep" % input_port)
    if len(is_exists[0]) > 5:
        print("|-错误，指定端口已被其它应用占用")
        return
    public.writeFile('data/port.pl', str(input_port))
    if os.path.exists("/usr/bin/firewall-cmd"):
        os.system("firewall-cmd --permanent --zone=public --add-port=%s/tcp" % input_port)
        os.system("firewall-cmd --reload")
    elif os.path.exists("/etc/sysconfig/iptables"):
        os.system("iptables -I INPUT -p tcp -m state --state NEW -m tcp --dport %s -j ACCEPT" % input_port)
        os.system("service iptables save")
    else:
        os.system("ufw allow %s" % input_port)
        os.system("ufw reload")
    os.system("/etc/init.d/bt reload")
    print("|-已将面板端口修改为：%s" % input_port)
    print(
        "|-若您的服务器提供商是[阿里云][腾讯云][华为云]或其它开启了[安全组]的服务器,请在安全组放行[%s]端口才能访问面板" % input_port)
    panelPath = '/www/server/panel/data/o.pl'
    if not os.path.exists(panelPath): return False
    o = public.readFile(panelPath).strip()
    if 'tencent' == o:
        print("|-若使用腾讯轻量云-Linux专享版面板，则不需要添加至安全组")

def set_panel_path(adminpath):
    admin_path = adminpath
    msg = ''
    from BTPanel import admin_path_checks
    if len(admin_path) < 6: msg = '安全入口地址长度不能小于6位!'
    if admin_path in admin_path_checks: msg = '该入口已被面板占用,请使用其它入口!'
    if not public.path_safe_check(admin_path) or admin_path[-1] == '.': msg = '入口地址格式不正确,示例: /my_panel'
    if admin_path[0] != '/':
        admin_path = "/" + admin_path
    if admin_path.find("//") != -1:
        msg = '入口地址格式不正确,示例: /my_panel'

    valid_path_pattern = re.compile(r'^(/?([a-zA-Z0-9\-._~:/@]|%[0-9A-Fa-f]{2})*)$')
    if not valid_path_pattern.match(admin_path):
        msg ='入口地址格式不正确,示例: /my_panel'

    admin_path_file = 'data/admin_path.pl'
    if msg != '':
        print('设置出错:{}'.format(msg))
        return
    public.writeFile(admin_path_file, admin_path)
    public.restart_panel()
    print('安全入口设置成功：{}'.format(admin_path))

def set_panel_ssl(status):
    status=status
    if status == "enable":
        CreateSSL()
    if status == "disable":
        os.system('btpython /www/server/panel/class/config.py SetPanelSSL')
        os.system("/etc/init.d/bt reload")

def get_panel_version():
    exit(public.version())

def sync_tencent_ssl(tencent_ssl_path="/root/tencent_ssl"):
    """同步腾讯云证书
    遍历目录下的nginx证书压缩包，解压并同步到面板ssl目录
    """
    import os
    import shutil
    import panelSSL
    from sslModel import certModel
    ss = panelSSL.panelSSL()

    cert_main = certModel.main()

    panel_ssl_path = "/www/server/panel/vhost/ssl"

    try:
        # 确保源目录存在
        if not os.path.exists(tencent_ssl_path):
            print(f"目录不存在: {tencent_ssl_path}")
            return False
        # 获取所有网站和对应的域名
        all_sites = public.M('sites').field('name,id').select()
        if not all_sites:
            print("没有找到任何网站信息")
            return False
        for site in all_sites:
            domians = public.M('domain').where("pid=?", (site["id"],)).field('name').select()
            if not domians:
                site["domains"] = []
            site["domains"] = [domain["name"] for domain in domians]
        BatchInfo = []

        # 遍历目录下的所有文件
        for filename in os.listdir(tencent_ssl_path):
            if not filename.endswith('_nginx.zip'):
                continue

            # 获取域名（去除_nginx.zip后缀）
            domain = filename.replace('_nginx.zip', '')
            
            zip_path = os.path.join(tencent_ssl_path, filename)
            extract_path = os.path.join(tencent_ssl_path, domain + '_nginx')
            ssl_domain_path = os.path.join(panel_ssl_path, domain)

            try:
                # 解压文件
                public.ExecShell("cd {} && unzip {}".format(tencent_ssl_path, zip_path))
                
                # 创建目标ssl目录
                os.makedirs(ssl_domain_path, exist_ok=True)

                # 复制证书文件
                bundle_src = os.path.join(extract_path, f"{domain}_bundle.pem")
                key_src = os.path.join(extract_path, f"{domain}.key")
                get = public.to_dict_obj({})
                get.key = public.readFile(key_src)
                get.csr = public.readFile(bundle_src)
                res=cert_main.save_cert(get)
                if res.get("status") == True:
                    print(f"成功同步证书: {domain}")
                else:
                    print(f"同步证书失败: {domain}")
                    continue
                # 获取证书信息
                get.ssl_hash = res["ssl_hash"]
                cert_detail = public.M('ssl_info').field(
                    'dns'
                ).where("hash=?",(res["ssl_hash"])).select()
                if not cert_detail:
                    print(f"未找到证书信息: {domain}")
                    continue
                try:
                    cert_detail = json.loads(cert_detail[0]["dns"])
                except Exception as e:
                    print(f"解析证书信息失败: {domain}, 错误: {str(e)}")

                for site in all_sites:
                    if site["domains"] and all_domains_covered(site["domains"], cert_detail):
                        BatchInfo.append(
                            {"ssl_hash":res["ssl_hash"],"siteName": site["name"]}
                        )
                    
            except Exception as e:
                print(f"处理证书时出错 {domain}: {str(e)}")
            finally:
                if os.path.exists(extract_path):
                    shutil.rmtree(extract_path)
        if BatchInfo:
            get = public.to_dict_obj({})
            get.BatchInfo = json.dumps(BatchInfo)
            res = ss.SetBatchCertToSite(get)
            print(res)
        else:
            print("没有需要部署的证书信息")

        return True
    except Exception as e:
        print(f"同步证书时出错: {str(e)}")
        return False

def all_domains_covered(domain_list, cert_domains):
    def matches(domain, pattern):
        if pattern.startswith('*.'):
            base = pattern[2:]
            base_dots = base.count('.')
            domain_dots = domain.count('.')
            # domain必须以.base结尾，且domain的点数比base多1（表示一级子域）
            if domain.endswith('.' + base) and domain_dots == base_dots + 1:
                return True
        else:
            if domain == pattern:
                return True
        return False

    return all(any(matches(domain, pattern) for pattern in cert_domains) for domain in domain_list)

def get_temp_login():
    s_time = int(time.time())
    expire_time=int(int(time.time()) + 3600 * 3)
    public.M('temp_login').where('state=? and expire>?', (0, s_time)).delete()
    token = public.GetRandomString(48)
    salt = public.GetRandomString(12)

    pdata = {
        'token': public.md5(token + salt),
        'salt': salt,
        'state': 0,
        'login_time': 0,
        'login_addr': '',
        'expire': expire_time,
    }

    if not public.M('temp_login').count():
        pdata['id'] = 101

    if public.M('temp_login').insert(pdata):
        if os.path.exists('/www/server/panel/data/ssl.pl'):
            HTTP_C="https://"
        else:
            HTTP_C="http://"

        IP_ADDRES=public.ExecShell("curl -sS --connect-timeout 10 -m 20 https://www.bt.cn/Api/getIpAddress")[0]

        PANEL_PORT=public.readFile("/www/server/panel/data/port.pl")

        PANEL_ADDRESS=HTTP_C+IP_ADDRES+":"+PANEL_PORT+"/login?tmp_token="+token
        print(PANEL_ADDRESS)

def get_temp_login_ipv4():
    s_time = int(time.time())
    expire_time=int(int(time.time()) + 3600 * 3)
    public.M('temp_login').where('state=? and expire>?', (0, s_time)).delete()
    token = public.GetRandomString(48)
    salt = public.GetRandomString(12)

    pdata = {
        'token': public.md5(token + salt),
        'salt': salt,
        'state': 0,
        'login_time': 0,
        'login_addr': '',
        'expire': expire_time,
    }

    if not public.M('temp_login').count():
        pdata['id'] = 101

    if public.M('temp_login').insert(pdata):
        if os.path.exists('/www/server/panel/data/ssl.pl'):
            HTTP_C="https://"
        else:
            HTTP_C="http://"

        IP_ADDRES=public.ExecShell("curl -4 -sS --connect-timeout 10 -m 20 https://www.bt.cn/Api/getIpAddress")[0]

        PANEL_PORT=public.readFile("/www/server/panel/data/port.pl")

        PANEL_ADDRESS=HTTP_C+IP_ADDRES+":"+PANEL_PORT+"/login?tmp_token="+token
        print(PANEL_ADDRESS)


# 将插件升级到6.0
def update_to6():
    print("====================================================")
    print("正在升级插件...")
    print("====================================================")
    download_address = public.get_url()
    exlodes = ['gitlab', 'pm2', 'mongodb', 'deployment_jd', 'logs', 'docker', 'beta', 'btyw']
    for pname in os.listdir('plugin/'):
        if not os.path.isdir('plugin/' + pname): continue
        if pname in exlodes: continue
        print("|-正在升级【%s】..." % pname),
        download_url = download_address + '/install/plugin/' + pname + '/install.sh'
        to_file = '/tmp/%s.sh' % pname
        public.downloadFile(download_url, to_file)
        os.system('/bin/bash ' + to_file + ' install &> /tmp/plugin_update.log 2>&1')
        print("    \033[32m[成功]\033[0m")
    print("====================================================")
    print("\033[32m所有插件已成功升级到最新!\033[0m")
    print("====================================================")


# 2024/5/29 下午5:58 调用面板反向代理的模块创建
def create_reverse_proxy(get):
    '''
        @param get:
        @name 调用面板反向代理的模块创建
        @author wzz <2024/5/29 下午6:00>
        @param "data":{"参数名":""} <数据类型> 参数描述
        @return dict{"status":True/False,"msg":"提示信息"}
    '''
    from mod.project.proxy.comMod import main as proxyMod
    pMod = proxyMod()

    panel_port = public.readFile('data/port.pl')

    try:
        close_reverse_proxy()
        __http = 'https' if os.path.exists("/www/server/panel/data/ssl.pl") else 'http'
        if __http != "https":
            CreateSSL()
        __http = "https"

        args = public.to_dict_obj({
            "proxy_pass": "{}://127.0.0.1:{}".format(__http, panel_port),
            "proxy_type": "http",
            "domains": get.siteName,
            "proxy_host": "$http_host",
            "remark": "宝塔面板的反代[请误操作,修改可能会导致面板无法访问]"
        })
        create_result = pMod.create(args)
        if not create_result['status']:
            return public.returnResult(False, create_result['msg'])

        # args.site_name = get.siteName
        # args.auth_path = "/"
        # args.username = public.GetRandomString(8).lower()
        # args.password = public.GetRandomString(8).lower()
        # if os.path.exists("data/http_auth.pwd"):
        #     public.ExecShell("rm -rf /www/server/panel/data/http_auth.pwd")
        #
        # public.writeFile("data/http_auth.pwd", args.password)
        # args.name = public.GetRandomString(5)
        #
        # auth_result = pMod.add_dir_auth(args)
        # if not create_result['status']:
        #     return public.returnResult(False, auth_result['msg'])

        return_data = {
            # "username": args.username,
            # "password": args.password,
            "siteName": get.siteName,
            "http": __http
        }
        return public.returnResult(True, '添加成功', data=return_data)
    except Exception as e:
        result = public.M('sites').where("name=?", (get.siteName,)).find()
        if not isinstance(result, dict):
            return public.returnResult(False, '添加失败，可能是Nginx配置文件错误，请先检查后再设置！错误详情：{}!'.format(str(e)))

        args = public.to_dict_obj({
            "id": result['id'],
            "siteName": get.siteName,
            "remove_path": 1,
        })
        pMod.delete(args)
        return public.returnResult(False, '添加失败，可能是Nginx配置文件错误，请先检查后再设置！错误详情：{}!'.format(str(e)))


# 2024/5/30 上午10:38 设置指定代理的SSL
def set_reverse_proxy_ssl(get):
    '''
        @name 设置指定代理的SSL
        @author wzz <2024/5/30 上午10:38>
        @param "data":{"参数名":""} <数据类型> 参数描述
        @return dict{"status":True/False,"msg":"提示信息"}
    '''
    from mod.project.proxy.comMod import main as proxyMod
    pMod = proxyMod()

    try:
        key = public.readFile("ssl/privateKey.pem")
        csr = public.readFile("ssl/certificate.pem")
        get.key = key
        get.csr = csr
        result = pMod.set_ssl(get)
        if not result['status']:
            return public.returnResult(False, result['msg'])

        return public.returnResult(True, '设置成功')
    except Exception as e:
        return public.returnMsg(False, '设置失败，错误{}!'.format(str(e)))


# 2024/5/29 下午6:21 关闭面板反向代理
def close_reverse_proxy():
    '''
        @name 关闭面板反向代理
        @author wzz <2024/5/29 下午6:21>
        @param "data":{"参数名":""} <数据类型> 参数描述
        @return dict{"status":True/False,"msg":"提示信息"}
    '''
    from mod.project.proxy.comMod import main as proxyMod
    pMod = proxyMod()

    site_name = ""
    sid = ""
    try:
        args = public.to_dict_obj({})
        proxy_list = pMod.get_list(args)
        if proxy_list["data"] is None:
            return public.returnResult(True, '', data={"siteName": site_name})

        panel_port = public.readFile('data/port.pl')
        for proxy in proxy_list["data"]["data"]:
            if panel_port == proxy["proxy_pass"].split(":")[-1]:
                site_name = proxy["name"]
                sid = proxy["id"]
                break

        args.id = sid
        args.site_name = site_name
        args.remove_path = 1
        delete_result = pMod.delete(args)
        if not delete_result['status']:
            return public.returnResult(False, delete_result['msg'])

        if os.path.exists("data/http_auth.pwd"):
            public.ExecShell("rm -rf /www/server/panel/data/http_auth.pwd")

        return public.returnResult(True, '删除成功', data={"siteName": site_name})
    except Exception as e:
        return public.returnMsg(False, '删除失败，错误{}!'.format(str(e)), data={"siteName": site_name})


# 2024/5/29 下午6:08 获取面板反代的信息
def get_reverse_proxy():
    '''
        @name
        @author wzz <2024/5/29 下午6:08>
        @param "data":{"参数名":""} <数据类型> 参数描述
        @return dict{"status":True/False,"msg":"提示信息"}
    '''
    from mod.project.proxy.comMod import main as proxyMod
    pMod = proxyMod()

    site_name = ""
    try:
        args = public.to_dict_obj({})
        proxy_list = pMod.get_list(args)
        if proxy_list["data"] is None:
            return public.returnResult(True, '', data={"siteName": site_name})

        panel_port = str(public.get_panel_port())
        for proxy in proxy_list["data"]["data"]:
            if panel_port == proxy["proxy_pass"].split(":")[-1].strip():
                site_name = proxy["name"]
                break

        # if site_name != "":
        #     args.site_name = site_name
        #     global_conf = pMod.get_global_conf(args)
        #
        #     password = ""
        #     if os.path.exists("data/http_auth.pwd"):
        #         password = public.readFile("data/http_auth.pwd")
        #
        #     if password == "":
        #         return public.returnResult(True, '', data={"siteName": site_name})
        #
        #     return_result = {
        #         "username": global_conf["data"]["basic_auth"][0]["username"],
        #         "password": password,
        #         "siteName": site_name
        #     }

        #     return public.returnResult(True, '', data=return_result)

        return public.returnResult(True, '', data={"siteName": site_name})
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return public.returnMsg(False, '获取失败，错误{}!'.format(str(e)), data={"siteName": site_name})


# 2025/2/17 14:29 检测如果磁盘剩余空间是否小于500M，是就返回False
def check_disk_space():
    '''
        @name 检测如果磁盘剩余空间是否小于500M，是就返回False，否则返回True
        @return bool
    '''
    disk_info = public.get_disk_usage("/")
    if disk_info.free < 500 * 1024 * 1024:
        print("==========================================================================")
        # 2025/2/17 14:34 输出格式化后的总磁盘空间和剩余空间
        os.system("echo -e '\\e[31m紧急：根目录(\"/\")磁盘空间不足500M，请先清理磁盘空间后再执行命令！\\e[0m'")
        print("总磁盘空间：{}，剩余空间：{}".format(public.to_size(disk_info.total), public.to_size(disk_info.free)))
        print("计算空间由字节转换，请以实际大小为准！")
        print("")
        stdout, stderr = public.ExecShell("df -Th")
        print("系统 df -Th 输出详情如下：")
        print(stdout)
        print("==========================================================================")
        return False
    return True


# 命令行菜单
def bt_cli(u_input=0):
    raw_tip = "==============================================="
    raw_tip1 = "===================================================================================="
    if not u_input:
        print("==================================宝塔面板命令行====================================")
        print("(1) 重启面板服务                  (8) 改面板端口                                   |")
        print("(2) 停止面板服务                  (9) 清除面板缓存                                 |")
        print("(3) 启动面板服务                  (10) 清除登录限制                                |")
        print("(4) 重载面板服务                  (11) 设置是否开启IP + User-Agent验证             |")
        print("(5) 修改面板密码                  (12) 取消域名绑定限制                            |")
        print("(6) 修改面板用户名                (13) 取消IP访问限制                              |")
        print("(7) 强制修改MySQL密码             (14) 查看面板默认信息                            |")
        print("(22) 显示面板错误日志             (15) 清理系统垃圾                                |")
        print("(23) 关闭BasicAuth认证            (16) 修复面板(安装当前版本的最新bug修复包)       |")
        print("(24) 关闭动态口令认证             (17) 设置日志切割是否压缩                        |")
        print("(25) 设置是否保存文件历史副本     (18) 设置是否自动备份面板                        |")
        print("(26) 关闭面板ssl                  (19) 关闭面板登录地区限制                        |")
        print("(28) 修改面板安全入口             (29) 取消访问设备验证                            |")
        print("(30) 取消访问UA验证               (32) 开启/关闭【80、443】端口访问面板            |")
        print("(34) 更新面板(更新到最新版本)                                                      |")
        print("(0) 取消                                                                           |")
        print(raw_tip1)
        try:
            u_input = input("请输入命令编号：")
            if sys.version_info[0] == 3: u_input = int(u_input)
        except:
            u_input = 0
    try:
        if u_input in ['log', 'logs', 'error', 'err', 'tail', 'debug', 'info']:
            os.system("tail -f {}".format(public.get_panel_log_file()))
            return
        if u_input[:6] in ['install', 'update']:
            print("提示：命令传参示例（编译安装php7.4）：bt install/0/php/7.4")
            print(sys.argv)
            install_args = u_input.split('/')
            if len(install_args) < 2:
                try:
                    install_input = input("请选择安装方式(0 编译安装，1 极速安装，默认: 1)：")
                    install_input = int(install_input)
                except:
                    install_input = 1
            else:
                install_input = int(install_args[1])
            print(raw_tip)
            soft_list = 'nginx apache php mysql memcached redis pure-ftpd phpmyadmin pm2 docker openlitespeed mongodb'
            soft_list_arr = soft_list.split(' ')
            if len(install_args) < 3:
                install_soft = ''
                while not install_soft:
                    print("支持的软件：{}".format(soft_list))
                    print(raw_tip)
                    install_soft = input("请输入要安装的软件名称(如：nginx)：")
                    if install_soft not in soft_list_arr:
                        print("不支命令行安装的持的软件")
                        install_soft = ''
            else:
                install_soft = install_args[2]

            print(raw_tip)
            if len(install_args) < 4:
                install_version = ''
                while not install_version:
                    print(raw_tip)
                    install_version = input("请输入要安装的版本号(如：1.18)：")
            else:
                install_version = install_args[3]

            print(raw_tip)
            os.system(
                "bash /www/server/panel/install/install_soft.sh {} {} {} {}".format(install_input, install_args[0],
                                                                                    install_soft, install_version))
            exit()

        print("不支持的指令")
        exit()
    except:
        pass

    nums = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 28, 29, 30, 31, 32, 33, 34]
    if not u_input in nums:
        print(raw_tip)
        print("已取消!")
        exit()

    print(raw_tip)
    print("正在执行(%s)..." % u_input)
    print(raw_tip)

    if u_input == 32:
        if public.get_webserver() != "nginx":
            print("仅支持nginx！")

        if not os.path.exists("/www/server/nginx/sbin/nginx"):
            print("未安装nginx，无法设置免端口访问面板")
            return

        print(raw_tip)
        print("此功能设置后可免端口访问宝塔面板")
        print("例如，设置域名为：panel.bt.cn")
        print("则可以通过 https://panel.bt.cn 访问面板")
        print("如果您输入的域名未解析，设置hosts即可访问")
        print("开启此功能后会启用http认证以及面板https，以确保面板使用安全，请勿关闭！")
        print(raw_tip)
        print()

        reverse_data = get_reverse_proxy()
        __http = 'https://' if os.path.exists("/www/server/panel/data/ssl.pl") else 'http://'
        admin_path = public.readFile('/www/server/panel/data/admin_path.pl').strip() if os.path.exists(
            "/www/server/panel/data/admin_path.pl") else "/login"

        if "siteName" in reverse_data['data'] and reverse_data['data']['siteName'] != "":
            address = __http + reverse_data['data']['siteName'] + admin_path
            print("已设置的免端口访问信息如下：")
            print("面板地址： {}".format(address))

        if "username" in reverse_data['data']:
            print("http认证用户名： {}".format(reverse_data['data']['username']))
            print("http认证密码： {}".format(reverse_data['data']['password']))

        bt_username = public.M('users').where('id=?', (1,)).getField('username')
        bt_password = public.readFile("/www/server/panel/default.pl")

        if "siteName" in reverse_data['data'] and reverse_data['data']['siteName'] != "":
            print("面板用户名： {}".format(bt_username))
            print("面板密码： {}".format(bt_password))
            print()
            print("#### 如需关闭，请输入0 关闭免端口访问面板")

        site_name = input("请输入访问面板的域名或IP：")

        if site_name == "":
            print("域名或ip不能为空，请重新输入，例如：192.168.100.100或panel.bt.cn")
            return

        if site_name.startswith("0 ") or site_name == "0":
            close_reverse_proxy()
            print()
            print("面板反向代理关闭成功")
            return
        else:
            if not public.check_ip(site_name) and not public.is_domain(site_name):
                print("域名或ip格式错误，请重新输入，例如：panel.bt.cn")
                return

        get = public.to_dict_obj({
            "siteName": site_name
        })

        public.set_module_logs('命令行设置免端口访问', 'create', 1)
        result = create_reverse_proxy(get)
        if not result["status"]:
            print(result["msg"])
            return

        if result["data"]["http"] == 'https':
            get.site_name = site_name
            set_reverse_proxy_ssl(get)
            __http = 'https://'

        print()
        print(raw_tip)
        address = __http + result['data']['siteName'] + admin_path
        print("面板地址： {}".format(address))
        # print("http认证用户名： {}".format(result['data']['username']))
        # print("http认证密码： {}".format(result['data']['password']))
        print("面板用户名： {}".format(bt_username))
        print("面板密码： {}".format(bt_password))
        print(raw_tip)
        public.restart_panel()
    if u_input == 33:
        close_reverse_proxy()
        print("面板反向代理关闭成功")
    if u_input == 31:
        os.system('tail -50 /www/server/panel/data/login_err.log')
    if u_input == 26:
        os.system('btpython /www/server/panel/class/config.py SetPanelSSL')
        os.system("/etc/init.d/bt reload")
    if u_input == 28:
        admin_path = input('请输入新的安全入口:')
        msg = ''
        from BTPanel import admin_path_checks
        if len(admin_path) < 6: msg = '安全入口地址长度不能小于6位!'
        if admin_path in admin_path_checks: msg = '该入口已被面板占用,请使用其它入口!'
        if not public.path_safe_check(admin_path) or admin_path[-1] == '.': msg = '入口地址格式不正确,示例: /my_panel'
        if admin_path[0] != '/':
            admin_path = "/" + admin_path
        admin_path_file = 'data/admin_path.pl'
        admin_path1 = '/'
        if os.path.exists(admin_path_file): admin_path1 = public.readFile(admin_path_file).strip()
        if msg != '':
            print('设置出错:{}'.format(msg))
            return
        public.writeFile(admin_path_file, admin_path)
        public.restart_panel()
        print('安全入口设置成功：{}'.format(admin_path))

    if u_input == 30:
        ua_file = 'data/limitua.conf'
        if os.path.exists(ua_file):
            with open(ua_file, 'r') as f:
                data = json.load(f)
            data['status'] = '0'  # 将status的值设置为"0"
            with open(ua_file, 'w') as f:
                json.dump(data, f)
        print("|-已关闭访问UA验证")

    if u_input == 29:
        os.system("rm -rf /www/server/panel/data/ssl_verify_data.pl")
        os.system("/etc/init.d/bt restart")
        print("|-已关闭访问设备验证")
    if u_input == 1:
        os.system("/etc/init.d/bt restart")
    elif u_input == 2:
        os.system("/etc/init.d/bt stop")
    elif u_input == 3:
        os.system("/etc/init.d/bt start")
    elif u_input == 4:
        os.system("/etc/init.d/bt reload")
    elif u_input == 5:
        if sys.version_info[0] == 2:
            input_pwd = raw_input("请输入新的面板密码：")
        else:
            input_pwd = input("请输入新的面板密码：")
        set_panel_pwd(input_pwd.strip(), True)
    elif u_input == 6:
        if sys.version_info[0] == 2:
            input_user = raw_input("请输入新的面板用户名(≥3位)：")
        else:
            input_user = input("请输入新的面板用户名(≥3位)：")
        set_panel_username(input_user.strip())
    elif u_input == 7:
        if sys.version_info[0] == 2:
            input_mysql = raw_input("请输入新的MySQL密码：")
        else:
            input_mysql = input("请输入新的MySQL密码：")
        if not input_mysql:
            print("|-错误，不能设置空密码")
            return

        if len(input_mysql) < 8:
            print("|-错误，长度不能少于8位")
            return

        import re
        rep = r"^[\w@\._]+$"
        if not re.match(rep, input_mysql):
            print("|-错误，密码中不能包含特殊符号")
            return

        print(input_mysql)
        set_mysql_root(input_mysql.strip())
    elif u_input == 8:
        input_port = input("请输入新的面板端口：")
        if sys.version_info[0] == 3: input_port = int(input_port)
        if not input_port:
            print("|-错误，未输入任何有效端口")
            return
        if input_port in [80, 443, 21, 20, 22]:
            print("|-错误，请不要使用常用端口作为面板端口")
            return
        try:
            port_str = public.readFile('data/port.pl')
            if port_str:
                old_port = int(port_str)
            else:
                old_port = 0
        except:
            old_port = 0

        if old_port == input_port:
            print("|-错误，与面板当前端口一致，无需修改")
            return
        if input_port > 65535 or input_port < 1:
            print("|-错误，可用端口范围在1-65535之间")
            return

        is_exists = public.ExecShell("lsof -i:%s|grep LISTEN|grep -v grep" % input_port)
        if len(is_exists[0]) > 5:
            print("|-错误，指定端口已被其它应用占用")
            return
        public.writeFile('data/port.pl', str(input_port))
        if os.path.exists("/usr/bin/firewall-cmd"):
            os.system("firewall-cmd --permanent --zone=public --add-port=%s/tcp" % input_port)
            os.system("firewall-cmd --reload")
        elif os.path.exists("/etc/sysconfig/iptables"):
            os.system("iptables -I INPUT -p tcp -m state --state NEW -m tcp --dport %s -j ACCEPT" % input_port)
            os.system("service iptables save")
        else:
            os.system("ufw allow %s" % input_port)
            os.system("ufw reload")
        os.system("/etc/init.d/bt reload")
        print("|-已将面板端口修改为：%s" % input_port)
        print(
            "|-若您的服务器提供商是[阿里云][腾讯云][华为云]或其它开启了[安全组]的服务器,请在安全组放行[%s]端口才能访问面板" % input_port)
        panelPath = '/www/server/panel/data/o.pl'
        if not os.path.exists(panelPath): return False
        o = public.readFile(panelPath).strip()
        if 'tencent' == o:
            print("|-若使用腾讯轻量云-Linux专享版面板，则不需要添加至安全组")
    elif u_input == 9:
        sess_file = '/www/server/panel/data/session'
        if os.path.exists(sess_file):
            os.system("rm -f {}/*".format(sess_file))
        public.clear_sql_session()
        os.system("/etc/init.d/bt reload")
    elif u_input == 10:
        os.system("/etc/init.d/bt reload")
    elif u_input == 11:
        not_tip = '{}/data/not_check_ip.pl'.format(public.get_panel_path())
        if os.path.exists(not_tip):
            os.remove(not_tip)
            print("|-已开启IP + User-Agent检测")
            print("|-此功能可以有效防止[重放攻击]")
        else:
            public.writeFile(not_tip, 'True')
            print("|-已关闭IP + User-Agent检测")
            print("|-注意：关闭此功能有被[重放攻击]的风险")
    elif u_input == 12:
        auth_file = 'data/domain.conf'
        if os.path.exists(auth_file): os.remove(auth_file)
        os.system("/etc/init.d/bt reload")
        print("|-已取消域名访问限制")
    elif u_input == 13:
        auth_file = 'data/limitip.conf'
        if os.path.exists(auth_file): os.remove(auth_file)
        os.system("/etc/init.d/bt reload")
        print("|-已取消IP访问限制")
    elif u_input == 14:
        try:
            if os.path.exists('/www/server/panel/data/panel_generation.pl'):
                conf = json.loads(public.readFile('/www/server/panel/data/panel_generation.pl'))
                __http = 'https://' if os.path.exists("/www/server/panel/data/ssl.pl") else 'http://'
                admin_path = public.readFile('/www/server/panel/data/admin_path.pl')
                if admin_path:
                    if admin_path.strip() in ("", "/"):
                        admin_path = '/login'
                    else:
                        admin_path = admin_path.strip()
                else:
                    admin_path = '/login'
                address = __http + conf['domain'] + admin_path
                public.writeFile('/www/server/panel/data/panel_site_address.pl', address)
            else:
                public.ExecShell("rm -rf /www/server/panel/data/panel_site_address.pl")
        except:
            pass
        os.system("/etc/init.d/bt default")
    elif u_input == 15:
        ClearSystem()
    elif u_input == 16:
        sh_path = "{}/script/upgrade_panel_optimized.py".format(public.get_panel_path())
        if not os.path.exists(sh_path):
            print("|-未找到修复脚本")
        os.system("bash {} repair_panel".format(sh_path))

    elif u_input == 17:
        l_path = '/www/server/panel/data/log_not_gzip.pl'
        if os.path.exists(l_path):
            print("|-检测到已关闭gzip压缩功能,正在开启...")
            os.remove(l_path)
            print("|-已开启gzip压缩")
        else:
            print("|-检测到已开启gzip压缩功能,正在关闭...")
            public.writeFile(l_path, 'True')
            print("|-已关闭gzip压缩")
    elif u_input == 18:
        l_path = '/www/server/panel/data/not_auto_backup.pl'
        if os.path.exists(l_path):
            print("|-检测到已关闭面板自动备份功能,正在开启...")
            os.remove(l_path)
            print("|-已开启面板自动备份功能")
        else:
            print("|-检测到已开启面板自动备份功能,正在关闭...")
            public.writeFile(l_path, 'True')
            print("|-已关闭面板自动备份功能")
    elif u_input == 19:
        empty_content = {
            "limit_area": {
                "city": [],
                "province": [],
                "country": []
            },
            "limit_area_status": "false",
            "limit_type": "deny"
        }

        try:
            limit_area_json = json.loads(public.readFile("/www/server/panel/data/limit_area.json"))
        except json.decoder.JSONDecodeError:
            limit_area_json = empty_content
        except TypeError:
            limit_area_json = empty_content

        limit_area_json['limit_area_status'] = "false"
        public.writeFile('data/limit_area.json', json.dumps(limit_area_json))
        print("|-已关闭面板登录地区限制")
    elif u_input == 20:
        limit_info = public.get_limit_area()

        if limit_info['limit_type'] == "allow":
            rule_type = "仅允许"
        else:
            rule_type = "禁止"

        city = []
        province = []
        country = []
        for area in limit_info['limit_area']['city']:
            city.append(area['name'])
        for area in limit_info['limit_area']['province']:
            province.append(area['name'])
        for area in limit_info['limit_area']['country']:
            country.append(area['name'])

        if not country and not province and not city:
            print("|-当前未配置面板登录限制规则!")
            return

        print("|-当前面板登录限制规则为：【{}】以下地区登录宝塔面板！\n".format(rule_type))
        if country:
            print("国家：{}".format(country))
        if province:
            print("省份：{}".format(province))
        if city:
            print("城市：{}".format(city))
    elif u_input == 21:
        backup_lists = public.get_default_db_backup_dates()
        print("如需恢复面板数据库初始设置请输入：default\n")
        if len(backup_lists) > 0:
            print("|-可以恢复的面板数据库备份列表：")
            for backup_list in backup_lists:
                print("|-{}".format(backup_list))
        else:
            print("|-没有可以恢复的面板数据库备份列表！")

        date = input("请输入可恢复的日期(格式：2020-01-01/20200101)：")

        if date == 'default':
            print("|-警告：恢复面板数据库初始设置将会清空面板数据！")
            confirm = input("请输入yes确认：")
            if confirm != 'yes':
                print("|-输入非yes，已退出！")
                return
            print("|-正在恢复面板数据库初始设置...")
            public.recover_default_db(date)
            os.system("/etc/init.d/bt restart")
            return

        if not date:
            print("|-错误，未输入任何有效日期")
            return

        if len(date) == 8 or len(date) == 10:
            if len(date) == 8:
                date = date[:4] + '-' + date[4:6] + '-' + date[6:]
            elif len(date) == 10:
                date = date[:4] + '-' + date[5:7] + '-' + date[8:]

            if date not in backup_lists:
                print("|-错误，指定的日期不存在，请输入正确日期！")
                return
            print("|-正在恢复面板数据库...")
            print("|-警告：恢复面板数据库将会覆盖当前面板数据！")
            confirm = input("请输入yes确认：")
            if confirm != 'yes':
                print("|-输入非yes，已退出！")
                return
            result = public.recover_default_db(date)
            if result is False: return
            print("|-面板数据库恢复成功！")
            print("|-正在重启面板...")
            os.system("/etc/init.d/bt restart")
            print("|-面板重启成功！")
            print("|-已将面板恢复至{}的设置！".format(date))
    elif u_input == 22:
        os.system('tail -100 /www/server/panel/logs/error.log')
    elif u_input == 23:
        filename = '/www/server/panel/config/basic_auth.json'
        if os.path.exists(filename): os.remove(filename)
        os.system('bt reload')
        print("|-已关闭BasicAuth认证")
    elif u_input == 24:
        filename = '/www/server/panel/data/two_step_auth.txt'
        if os.path.exists(filename): os.remove(filename)
        print("|-已关闭谷歌认证")
    elif u_input == 25:
        l_path = '/www/server/panel/data/not_file_history.pl'
        if os.path.exists(l_path):
            print("|-检测到已关闭文件副本功能,正在开启...")
            os.remove(l_path)
            print("|-已开启文件副本功能")
        else:
            print("|-检测到已开启文件副本功能,正在关闭...")
            public.writeFile(l_path, 'True')
            print("|-已关闭文件副本功能")
    elif u_input == 34:
        ver = sys.argv[3] if len(sys.argv) > 3 and sys.argv[2]=="34" else ""
        sh_path = "{}/script/upgrade_panel_optimized.py".format(public.get_panel_path())
        if not os.path.exists(sh_path):
            print("|-未找到升级脚本")
        ret_code = os.system("bash {} upgrade_panel {} --dry-run".format(sh_path, ver))
        if ret_code != 0:
            return
        continue_tip = input("是否继续执行更新?(y/n):")
        if continue_tip.strip().lower() in ('y', 'yes'):
            os.system("bash {} upgrade_panel {}".format(sh_path, ver))
        else:
            print("已取消更新!")


if __name__ == "__main__":
    type = sys.argv[1]
    if type == 'root':
        set_mysql_root(sys.argv[2])
    elif type == 'panel':
        set_panel_pwd(sys.argv[2])
    elif type == 'username':
        if len(sys.argv) > 2:
            set_panel_username(sys.argv[2])
        else:
            set_panel_username()
    elif type == 'reusername':
        set_panel_username(sys.argv[2])
    elif type == 'o':
        setup_idc()
    elif type == 'mysql_dir':
        set_mysql_dir(sys.argv[2])
    elif type == 'package':
        PackagePanel()
    elif type == 'ssl':
        CreateSSL()
    elif type == 'clear':
        ClearSystem()
    elif type == 'closelog':
        CloseLogs()
    elif type == 'update_to6':
        update_to6()
    elif type == 'set_panel_port':
        set_panel_port(sys.argv[2])
    elif type == 'set_panel_path':
        set_panel_path(sys.argv[2])
    elif type == 'set_panel_ssl':
        set_panel_ssl(sys.argv[2])
    elif type == 'get_temp_login':
        get_temp_login()
    elif type == 'get_panel_version':
        get_panel_version()
    elif type == 'sync_tencent_ssl':
        sync_tencent_ssl()
    elif type == 'get_temp_login_ipv4':
        get_temp_login_ipv4()
    elif type == 'phpenv':
        import jobs
        jobs.set_php_cli_env()
    elif type == "cli":
        clinum = 0
        try:
            if len(sys.argv) > 2:
                clinum = int(sys.argv[2]) if sys.argv[2][:6] not in ['instal', 'update'] else sys.argv[2]
        except:
            clinum = sys.argv[2]
        if clinum != 14:
            if not check_disk_space(): exit(1)
        bt_cli(clinum)
    elif type == 'check_db':
        check_db()  # 面板自动修复
    else:
        print('ERROR: Parameter error')
