# coding: utf-8
# +-------------------------------------------------------------------
# | BT-Panel Linux Panel
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 BT-Panel(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author:  hwliang <hwl@bt.cn>
# +-------------------------------------------------------------------

# ------------------------------
# Toolbox
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


def check_db():  # Check database
    pass
    # data_func = {
    #     "users": check_users_tb,
    #     "config": check_config_tb,
    # }

    # for tb_name, check_func in data_func.items():
    #     sqlite_obj = public.M(tb_name)
    #     check_func(sqlite_obj)


# User table check
def check_users_tb(sqlite_obj):
    pass
    # user = sqlite_obj.where("id=?", (1,)).find()
    # if not isinstance(user, (dict, list)):
    #     print("users err:{}".format(user))
    #     return
    # username = public.GetRandomString(8).lower()
    # password = public.GetRandomString(8).lower()
    # if not user:  # Table data is empty
    #     sqlite_obj.add("id,username,password", (1, username, password))
    #     print("Default user lost detected, repairing...")
    #     print("|-New username: {}".format(username))
    #     print("|-New password: {}".format(password))
    #     return
    # # Table database missing
    # if not user.get("username"):
    #     print("Username is empty detected, repairing...")
    #     sqlite_obj.where("id=?", (1,)).setField("username", username)
    #     print("|-New username: {}".format(username))
    # if not user.get("password"):
    #     print("Password is empty detected, repairing...")
    #     sqlite_obj.where("id=?", (1,)).setField('password', public.password_salt(public.md5(password), uid=1))
    #     print("|-New password: {}".format(password))


# Config table check
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
    if not config:  # Table data is empty
        sqlite_obj.add("id,webserver,backup_path,sites_path,status,mysql_root", (1, webserver, backup_path, sites_path, status, mysql_root))
        print("Default panel configuration lost detected, repairing...")
        print("|-Default web server: {}".format(webserver))
        print("|-Default backup path: {}".format(backup_path))
        print("|-Default sites path: {}".format(sites_path))
        print("|-Default MySQL password: {}".format(mysql_root))
        return
    # Table database missing
    if not config.get("webserver"):
        print("Default web server is empty detected, repairing...")
        sqlite_obj.where("id=?", (1,)).setField("webserver", webserver)
        print("|-Default web server: {}".format(webserver))
    if not config.get("backup_path"):
        print("Default backup path is empty detected, repairing...")
        sqlite_obj.where("id=?", (1,)).setField("backup_path", backup_path)
        print("|-Default backup path: {}".format(backup_path))
    if not config.get("sites_path"):
        print("Default sites path is empty detected, repairing...")
        sqlite_obj.where("id=?", (1,)).setField("sites_path", sites_path)
        print("|-Default sites path: {}".format(sites_path))
    if not config.get("mysql_root"):
        print("Default MySQL password is empty detected, repairing...")
        set_mysql_root(mysql_root)
        # sqlite_obj.where("id=?", (1,)).setField("mysql_root", mysql_root)
        # print("|-Default MySQL password: {}".format(len(mysql_root) * "*"))


# Set MySQL password
def set_mysql_root(password):
    import db, os
    sql = db.Sql()

    root_mysql = '''#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH
pwd=$1
/etc/init.d/mysqld stop
mysqld_safe --skip-grant-tables&
echo 'Setting password...';
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
echo "Root password successfully changed to: ${pwd}"
echo "The root password set ${pwd}  successuful"'''

    public.writeFile('mysql_root.sh', root_mysql)
    os.system("/bin/bash mysql_root.sh " + password)
    os.system("rm -f mysql_root.sh")

    result = public.M('config').where('id=?', (1,)).setField('mysql_root', password)
    print(result)


# Set panel password
def set_panel_pwd(password, ncli=False):
    password = password.strip()
    if not len(password) > 5:
        print("|-Error: Password length must be greater than 5 characters")
        return
    import db
    sql = db.Sql()
    result = public.M('users').where('id=?', (1,)).setField('password', public.password_salt(public.md5(password), uid=1))
    username = public.M('users').where('id=?', (1,)).getField('username')
    if ncli:
        print("|-Username: " + username)
        print("|-New password: " + password)
    else:
        print(username)


# Set MySQL directory
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


# Package panel
def PackagePanel():
    print('========================================================')
    print('|-Cleaning log information...'),
    public.M('logs').where('id!=?', (0,)).delete()
    print('\t\t\033[1;32m[done]\033[0m')
    print('|-Cleaning task history...'),
    public.M('tasks').where('id!=?', (0,)).delete()
    print('\t\t\033[1;32m[done]\033[0m')
    print('|-Cleaning network monitoring records...'),
    public.M('network').dbfile('system').where('id!=?', (0,)).delete()
    print('\t\033[1;32m[done]\033[0m')
    print('|-Cleaning CPU monitoring records...'),
    public.M('cpuio').dbfile('system').where('id!=?', (0,)).delete()
    print('\t\033[1;32m[done]\033[0m')
    print('|-Cleaning disk monitoring records...'),
    public.M('diskio').dbfile('system').where('id!=?', (0,)).delete()
    print('\t\033[1;32m[done]\033[0m')
    print('|-Cleaning IP information...'),
    os.system('rm -f /www/server/panel/data/iplist.txt')
    os.system('rm -f /www/server/panel/data/address.pl')
    os.system('rm -f /www/server/panel/data/*.login')
    os.system('rm -f /www/server/panel/data/domain.conf')
    os.system('rm -f /www/server/panel/data/user*')
    os.system('rm -f /www/server/panel/data/admin_path.pl')
    os.system('rm -rf /www/backup/panel/*')
    os.system('rm -f /root/.ssh/*')

    print('\t\033[1;32m[done]\033[0m')
    print('|-Cleaning system usage traces...'),
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
        a_input = input('|-Automatically optimize PHP/MySQL configuration on first boot?(y/n default: y): ')
    else:
        a_input = raw_input('|-Automatically optimize PHP/MySQL configuration on first boot?(y/n default: y): ')
    if not a_input: a_input = 'y'
    print(a_input)
    if not a_input in ['Y', 'y', 'yes', 'YES']:
        public.ExecShell("rm -f /www/server/panel/php_mysql_auto.pl")
    else:
        public.writeFile('/www/server/panel/php_mysql_auto.pl', "True")

    print("|-Please select IDC brand information display settings:")
    print("=" * 50)
    print(" (1) Display default BT-Panel Linux information")
    print(" (2) Display IDC customized panel information")
    print("=" * 50)
    i_input = input("Please select panel information to display(default: 1): ")
    if i_input in [2, '2']:
        print("2 Display IDC customized panel information")
        print("=" * 50)
    else:
        print("1 Display default BT-Panel Linux information")
        print("=" * 50)
        panelPath = '/www/server/panel'
        pFile = panelPath + '/config/config.json'
        pInfo = json.loads(public.readFile(pFile))
        pInfo['title'] = u'BT-Panel Linux Panel'
        pInfo['brand'] = u'BT-Panel'
        pInfo['product'] = u'Linux Panel'
        public.writeFile(pFile, json.dumps(pInfo))
        tFile = panelPath + '/data/title.pl'
        if os.path.exists(tFile):
            os.remove(tFile)

    print("|-Please select user initialization method:")
    print("=" * 50)
    print(" (1) Display initialization page when accessing panel")
    print(" (2) Automatically generate new account and password on first startup")
    print(" (3) Automatically generate new account, password and security path on first startup")
    print("=" * 50)
    p_input = input("Please select initialization method(default: 1): ")
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
    print('\033[1;32m|-Panel packaged successfully, please do not login to the panel for any other operations!\033[0m')
    if p_input not in [2, '2', 3, '3']:
        print('\033[1;41m|-Panel initialization URL: http://{SERVERIP}:' + port + '/install\033[0m')
    else:
        print('\033[1;41m|-Command to get initial account and password: bt default \033[0m')
        print('\033[1;41m|-Note: Initial account and password can only be obtained correctly before first login \033[0m')



# Clear running tasks
def CloseTask():
    ncount = public.M('tasks').where('status!=?', (1,)).delete()
    os.system("kill `ps -ef |grep 'python panelSafe.pyc'|grep -v grep|grep -v panelExec|awk '{print $2}'`")
    os.system("kill `ps -ef |grep 'install_soft.sh'|grep -v grep|grep -v panelExec|awk '{print $2}'`")
    os.system('/etc/init.d/bt restart')
    print("Successfully cleaned " + int(ncount) + " tasks!")


def get_ipaddress():
    '''
        @name Get local IP address
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


# Self-signed certificate
def CreateSSL():
    import base64
    userInfo = public.get_user_info()
    if not userInfo:
        userInfo['uid'] = 0
        userInfo['access_key'] = 'B' * 32
    domains = get_host_all()
    pdata = {
        "action": "get_domain_cert",
        "company": "BT-Panel",
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


# Create files
def CreateFiles(path, num):
    if not os.path.exists(path): os.system('mkdir -p ' + path)
    import time;
    for i in range(num):
        filename = path + '/' + str(time.time()) + '__' + str(i)
        open(path, 'w+').close()


# Count files
def GetFilesCount(path):
    i = 0
    for name in os.listdir(path): i += 1
    return i


# Clean system garbage
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
    print('\033[1;32m|-System garbage cleaning completed, deleted [' + str(count) + '] files, freed disk space [' + ToSize(total) + ']\033[0m')


# Clean mail logs
def ClearMail():
    rpath = '/var/spool'
    total = count = 0
    import shutil
    con = ['cron', 'anacron', 'mail']
    for d in os.listdir(rpath):
        if d in con: continue
        dpath = rpath + '/' + d
        print('|-Cleaning ' + dpath + ' ...')
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
        print('|-Cleaned [' + dpath + '], deleted [' + str(num) + '] files, freed disk space [' + ToSize(size) + ']')
        total += size
        count += num
    print('=======================================================================')
    print('|-Spool cleaning completed, deleted [' + str(count) + '] files, freed disk space [' + ToSize(total) + ']')
    return total, count


# Clean PHP session files
def ClearSession():
    spath = '/tmp'
    total = count = 0
    import shutil
    print('|-Cleaning PHP_SESSION ...')
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
    print('|-PHP session cleaning completed, deleted [' + str(count) + '] files, freed disk space [' + ToSize(total) + ']')
    return total, count


# Clear recycle bin
def ClearRecycle_Bin():
    import files
    f = files.files()
    f.Close_Recycle_bin(None)


# Clean others
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
    print('|-Cleaning temporary files and website logs ...')
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
    print('|-Temporary files and website logs cleaning completed, deleted [' + str(count) + '] files, freed disk space [' + ToSize(total) + ']')
    return total, count


# Close normal logs
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


# Byte unit conversion
def ToSize(size):
    ds = ['b', 'KB', 'MB', 'GB', 'TB']
    for d in ds:
        if size < 1024: return str(size) + d
        size = size / 1024
    return '0b'


# Set panel username
def set_panel_username(username=None):
    import db
    sql = db.Sql()
    if username:
        print("|-Setting panel username...")
        re_list = re.findall(r"[^\w,.]+", username)
        if re_list:
            print("|-Error: Password cannot contain Chinese characters and special symbols: {}".format(" ".join(re_list)))
            return
        if username in ['admin', 'root']:
            print("|-Error: Cannot use too simple username")
            return

        public.M('users').where('id=?', (1,)).setField('username', username)
        print("|-New username: %s" % username)
        return

    username = public.M('users').where('id=?', (1,)).getField('username')
    if username == 'admin':
        username = public.GetRandomString(8).lower()
        public.M('users').where('id=?', (1,)).setField('username', username)
    print('username: ' + username)


# Setup IDC
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
        pInfo['product'] = u'Co-customized with BT-Panel'
        public.writeFile(pFile, json.dumps(pInfo))
        tFile = panelPath + '/data/title.pl'
        titleNew = pInfo['brand'] + u' Panel'
        if os.path.exists(tFile):
            title = public.GetConfigValue('title')
            if title == '' or title == 'BT-Panel Linux Panel':
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
            print("|-Error: No valid port entered")
            return
    if input_port in [80, 443, 21, 20, 22]:
        print("|-Error: Please do not use common ports as panel port")
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
        print("|-Error: Same as current panel port, no need to modify")
        return
    if input_port > 65535 or input_port < 1:
        print("|-Error: Available port range is 1-65535")
        return

    print("|-Starting to set panel port")
    is_exists = public.ExecShell("lsof -i:%s|grep LISTEN|grep -v grep" % input_port)
    if len(is_exists[0]) > 5:
        print("|-Error: Specified port is already occupied by other applications")
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
    print("|-Panel port has been changed to: %s" % input_port)
    print(
        "|-If your server provider is [Alibaba Cloud][Tencent Cloud][Huawei Cloud] or other servers with [Security Group] enabled, please allow port [%s] in the security group to access the panel" % input_port)
    panelPath = '/www/server/panel/data/o.pl'
    if not os.path.exists(panelPath): return False
    o = public.readFile(panelPath).strip()
    if 'tencent' == o:
        print("|-If using Tencent Cloud Lighthouse Linux exclusive version panel, no need to add to security group")

def set_panel_path(adminpath):
    admin_path = adminpath
    msg = ''
    from BTPanel import admin_path_checks
    if len(admin_path) < 6: msg = 'Security entrance address length cannot be less than 6 characters!'
    if admin_path in admin_path_checks: msg = 'This entrance has been occupied by the panel, please use another entrance!'
    if not public.path_safe_check(admin_path) or admin_path[-1] == '.': msg = 'Entrance address format is incorrect, example: /my_panel'
    if admin_path[0] != '/':
        admin_path = "/" + admin_path
    if admin_path.find("//") != -1:
        msg = 'Entrance address format is incorrect, example: /my_panel'

    valid_path_pattern = re.compile(r'^(/?([a-zA-Z0-9\-._~:/@]|%[0-9A-Fa-f]{2})*)$')
    if not valid_path_pattern.match(admin_path):
        msg ='Entrance address format is incorrect, example: /my_panel'

    admin_path_file = 'data/admin_path.pl'
    if msg != '':
        print('Setup error:{}'.format(msg))
        return
    public.writeFile(admin_path_file, admin_path)
    public.restart_panel()
    print('Security entrance setup successfully: {}'.format(admin_path))

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
    """Sync Tencent Cloud SSL certificates
    Traverse nginx certificate zip files in directory, extract and sync to panel ssl directory
    """
    import os
    import shutil
    import panelSSL
    from sslModel import certModel
    ss = panelSSL.panelSSL()

    cert_main = certModel.main()

    panel_ssl_path = "/www/server/panel/vhost/ssl"

    try:
        # Ensure source directory exists
        if not os.path.exists(tencent_ssl_path):
            print(f"Directory does not exist: {tencent_ssl_path}")
            return False
        # Get all sites and corresponding domains
        all_sites = public.M('sites').field('name,id').select()
        if not all_sites:
            print("No website information found")
            return False
        for site in all_sites:
            domians = public.M('domain').where("pid=?", (site["id"],)).field('name').select()
            if not domians:
                site["domains"] = []
            site["domains"] = [domain["name"] for domain in domians]
        BatchInfo = []

        # Traverse all files in directory
        for filename in os.listdir(tencent_ssl_path):
            if not filename.endswith('_nginx.zip'):
                continue

            # Get domain name (remove _nginx.zip suffix)
            domain = filename.replace('_nginx.zip', '')
            
            zip_path = os.path.join(tencent_ssl_path, filename)
            extract_path = os.path.join(tencent_ssl_path, domain + '_nginx')
            ssl_domain_path = os.path.join(panel_ssl_path, domain)

            try:
                # Extract file
                public.ExecShell("cd {} && unzip {}".format(tencent_ssl_path, zip_path))
                
                # Create target ssl directory
                os.makedirs(ssl_domain_path, exist_ok=True)

                # Copy certificate files
                bundle_src = os.path.join(extract_path, f"{domain}_bundle.pem")
                key_src = os.path.join(extract_path, f"{domain}.key")
                get = public.to_dict_obj({})
                get.key = public.readFile(key_src)
                get.csr = public.readFile(bundle_src)
                res=cert_main.save_cert(get)
                if res.get("status") == True:
                    print(f"Successfully synced certificate: {domain}")
                else:
                    print(f"Failed to sync certificate: {domain}")
                    continue
                # Get certificate information
                get.ssl_hash = res["ssl_hash"]
                cert_detail = public.M('ssl_info').field(
                    'dns'
                ).where("hash=?",(res["ssl_hash"])).select()
                if not cert_detail:
                    print(f"Certificate information not found: {domain}")
                    continue
                try:
                    cert_detail = json.loads(cert_detail[0]["dns"])
                except Exception as e:
                    print(f"Failed to parse certificate information: {domain}, error: {str(e)}")

                for site in all_sites:
                    if site["domains"] and all_domains_covered(site["domains"], cert_detail):
                        BatchInfo.append(
                            {"ssl_hash":res["ssl_hash"],"siteName": site["name"]}
                        )
                    
            except Exception as e:
                print(f"Error processing certificate {domain}: {str(e)}")
            finally:
                if os.path.exists(extract_path):
                    shutil.rmtree(extract_path)
        if BatchInfo:
            get = public.to_dict_obj({})
            get.BatchInfo = json.dumps(BatchInfo)
            res = ss.SetBatchCertToSite(get)
            print(res)
        else:
            print("No certificate information needs to be deployed")

        return True
    except Exception as e:
        print(f"Error syncing certificate: {str(e)}")
        return False

def all_domains_covered(domain_list, cert_domains):
    def matches(domain, pattern):
        if pattern.startswith('*.'):
            base = pattern[2:]
            base_dots = base.count('.')
            domain_dots = domain.count('.')
            # domain must end with .base and have 1 more dot than base (representing first-level subdomain)
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

        IP_ADDRES=public.ExecShell("curl -sS --connect-timeout 10 -m 20 {}".format(public.get_home_node("https://www.bt.cn/Api/getIpAddress")))[0]

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

        IP_ADDRES=public.ExecShell("curl -4 -sS --connect-timeout 10 -m 20 {}".format(public.get_home_node("https://www.bt.cn/Api/getIpAddress")))[0]

        PANEL_PORT=public.readFile("/www/server/panel/data/port.pl")

        PANEL_ADDRESS=HTTP_C+IP_ADDRES+":"+PANEL_PORT+"/login?tmp_token="+token
        print(PANEL_ADDRESS)


# Upgrade plugins to 6.0
def update_to6():
    print("====================================================")
    print("Upgrading plugins...")
    print("====================================================")
    download_address = public.get_url()
    exlodes = ['gitlab', 'pm2', 'mongodb', 'deployment_jd', 'logs', 'docker', 'beta', 'btyw']
    for pname in os.listdir('plugin/'):
        if not os.path.isdir('plugin/' + pname): continue
        if pname in exlodes: continue
        print("|-Upgrading [%s]..." % pname),
        download_url = download_address + '/install/plugin/' + pname + '/install.sh'
        to_file = '/tmp/%s.sh' % pname
        public.downloadFile(download_url, to_file)
        os.system('/bin/bash ' + to_file + ' install &> /tmp/plugin_update.log 2>&1')
        print("    \033[32m[Success]\033[0m")
    print("====================================================")
    print("\033[32mAll plugins have been successfully upgraded to the latest version!\033[0m")
    print("====================================================")


# 2024/5/29 5:58 PM Create panel reverse proxy module
def create_reverse_proxy(get):
    '''
        @param get:
        @name Create panel reverse proxy module
        @author wzz <2024/5/29 6:00 PM>
        @param "data":{"param name":""} <data type> parameter description
        @return dict{"status":True/False,"msg":"prompt message"}
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
            "remark": "BT-Panel reverse proxy [Please do not misoperate, modification may cause panel inaccessible]"
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
        return public.returnResult(True, 'Added successfully', data=return_data)
    except Exception as e:
        result = public.M('sites').where("name=?", (get.siteName,)).find()
        if not isinstance(result, dict):
            return public.returnResult(False, 'Failed to add, possibly Nginx configuration file error, please check first before setting! Error details: {}!'.format(str(e)))

        args = public.to_dict_obj({
            "id": result['id'],
            "siteName": get.siteName,
            "remove_path": 1,
        })
        pMod.delete(args)
        return public.returnResult(False, 'Failed to add, possibly Nginx configuration file error, please check first before setting! Error details: {}!'.format(str(e)))


# 2024/5/30 10:38 AM Set SSL for specified proxy
def set_reverse_proxy_ssl(get):
    '''
        @name Set SSL for specified proxy
        @author wzz <2024/5/30 10:38 AM>
        @param "data":{"param name":""} <data type> parameter description
        @return dict{"status":True/False,"msg":"prompt message"}
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

        return public.returnResult(True, 'Setup successful')
    except Exception as e:
        return public.returnMsg(False, 'Setup failed, error {}!'.format(str(e)))


# 2024/5/29 6:21 PM Close panel reverse proxy
def close_reverse_proxy():
    '''
        @name Close panel reverse proxy
        @author wzz <2024/5/29 6:21 PM>
        @param "data":{"param name":""} <data type> parameter description
        @return dict{"status":True/False,"msg":"prompt message"}
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

        return public.returnResult(True, 'Deleted successfully', data={"siteName": site_name})
    except Exception as e:
        return public.returnMsg(False, 'Delete failed, error {}!'.format(str(e)), data={"siteName": site_name})


# 2024/5/29 6:08 PM Get panel reverse proxy information
def get_reverse_proxy():
    '''
        @name Get panel reverse proxy information
        @author wzz <2024/5/29 6:08 PM>
        @param "data":{"param name":""} <data type> parameter description
        @return dict{"status":True/False,"msg":"prompt message"}
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
        return public.returnMsg(False, 'Failed to get, error {}!'.format(str(e)), data={"siteName": site_name})


# 2025/2/17 14:29 Check if disk space is less than 500M, return False if yes
def check_disk_space():
    '''
        @name Check if disk remaining space is less than 50M, return False if yes, otherwise return True
        @return bool
    '''
    disk_info = public.get_disk_usage("/")
    if disk_info.free < 50 * 1024 * 1024:
        print("==========================================================================")
        # 2025/2/17 14:34 Output formatted total disk space and remaining space
        os.system("echo -e '\\e[31mUrgent: Root directory (\"/\") disk space is less than 50M, please clean up disk space before executing command!\\e[0m'")
        print("You can execute the following command to clean manually")
        os.system("echo -e '\\e[33mCommand: btpython /www/server/panel/script/btcli.py\\e[0m'")
        print("Total disk space: {}, Remaining space: {}".format(public.to_size(disk_info.total), public.to_size(disk_info.free)))
        print("Calculated space is converted from bytes, please refer to actual size!")
        print("")
        stdout, stderr = public.ExecShell("df -Th")
        print("System df -Th output details:")
        print(stdout)
        print("==========================================================================")
        return False
    return True


# Command line menu
def bt_cli(u_input=0):
    raw_tip = "==============================================="
    raw_tip1 = "===================================================================================="
    if not u_input:
        print("=================================BT-Panel Command Line==============================")
        print("(1) Restart panel service         (8) Change panel port                            |")
        print("(2) Stop panel service            (9) Clear panel cache                            |")
        print("(3) Start panel service           (10) Clear login restrictions                    |")
        print("(4) Reload panel service          (11) Enable/Disable IP + User-Agent verification |")
        print("(5) Change panel password         (12) Remove domain binding restrictions          |")
        print("(6) Change panel username         (13) Remove IP access restrictions               |")
        print("(7) Force change MySQL password   (14) View panel default information              |")
        print("(22) Show panel error log         (15) Clean system garbage                        |")
        print("(23) Disable BasicAuth            (16) Repair panel(install latest bug fix)        |")
        print("(24) Disable dynamic OTP          (17) Set log rotation compression                |")
        print("(25) Save file history backup     (18) Set auto backup panel                       |")
        print("(26) Disable panel ssl            (19) Disable panel login region restrictions     |")
        print("(28) Change panel security path   (29) Cancel device verification                  |")
        print("(30) Cancel UA verification       (32) Enable/Disable [80,443] port access panel   |")
        print("(34) Update panel(to latest)      (35) btcli command line management tool          |")
        print("(36) Disk space cleanup tool      (99) Switch to English                           |")
        print("(0) Cancel                                                                         |")
        print(raw_tip1)
        try:
            u_input = input("Please enter command number: ")
            if sys.version_info[0] == 3: u_input = int(u_input)
        except:
            u_input = 0
    try:
        if u_input in ['log', 'logs', 'error', 'err', 'tail', 'debug', 'info']:
            os.system("tail -f {}".format(public.get_panel_log_file()))
            return
        if u_input[:6] in ['install', 'update']:
            print("Tip: Command parameter example (compile install php7.4): bt install/0/php/7.4")
            print(sys.argv)
            install_args = u_input.split('/')
            if len(install_args) < 2:
                try:
                    install_input = input("Please select installation method(0 compile, 1 rapid, default: 1): ")
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
                    print("Supported software: {}".format(soft_list))
                    print(raw_tip)
                    install_soft = input("Please enter software name to install(e.g.: nginx): ")
                    if install_soft not in soft_list_arr:
                        print("Unsupported software for command line installation")
                        install_soft = ''
            else:
                install_soft = install_args[2]

            print(raw_tip)
            if len(install_args) < 4:
                install_version = ''
                while not install_version:
                    print(raw_tip)
                    install_version = input("Please enter version number to install(e.g.: 1.18): ")
            else:
                install_version = install_args[3]

            print(raw_tip)
            os.system(
                "bash /www/server/panel/install/install_soft.sh {} {} {} {}".format(install_input, install_args[0],
                                                                                    install_soft, install_version))
            exit()

        print("Unsupported command")
        exit()
    except:
        pass

    nums = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 28, 29, 30, 31, 32, 33, 34, 35, 36, 99]
    if not u_input in nums:
        print(raw_tip)
        print("Cancelled!")
        exit()

    print(raw_tip)
    print("Executing(%s)..." % u_input)
    print(raw_tip)

    if u_input == 32:
        if public.get_webserver() != "nginx":
            print("Only supports nginx!")

        if not os.path.exists("/www/server/nginx/sbin/nginx"):
            print("Nginx not installed, cannot set port-free panel access")
            return

        print(raw_tip)
        print("After setting this function, you can access BT-Panel without port")
        print("For example, set domain as: panel.bt.cn")
        print("Then you can access panel via https://panel.bt.cn")
        print("If your domain is not resolved, you can set hosts to access")
        print("After enabling this function, http authentication and panel https will be enabled to ensure panel security, do not disable!")
        print(raw_tip)
        print()

        reverse_data = get_reverse_proxy()
        __http = 'https://' if os.path.exists("/www/server/panel/data/ssl.pl") else 'http://'
        admin_path = public.readFile('/www/server/panel/data/admin_path.pl').strip() if os.path.exists(
            "/www/server/panel/data/admin_path.pl") else "/login"

        if "siteName" in reverse_data['data'] and reverse_data['data']['siteName'] != "":
            address = __http + reverse_data['data']['siteName'] + admin_path
            print("Port-free access information set as follows:")
            print("Panel address: {}".format(address))

        if "username" in reverse_data['data']:
            print("HTTP auth username: {}".format(reverse_data['data']['username']))
            print("HTTP auth password: {}".format(reverse_data['data']['password']))

        bt_username = public.M('users').where('id=?', (1,)).getField('username')
        bt_password = public.readFile("/www/server/panel/default.pl")

        if "siteName" in reverse_data['data'] and reverse_data['data']['siteName'] != "":
            print("Panel username: {}".format(bt_username))
            print("Panel password: {}".format(bt_password))
            print()
            print("#### To disable, please enter 0 to close port-free panel access")

        site_name = input("Please enter domain or IP to access panel: ")

        if site_name == "":
            print("Domain or IP cannot be empty, please re-enter, e.g.: 192.168.100.100 or panel.bt.cn")
            return

        if site_name.startswith("0 ") or site_name == "0":
            close_reverse_proxy()
            print()
            print("Panel reverse proxy closed successfully")
            return
        else:
            if not public.check_ip(site_name) and not public.is_domain(site_name):
                print("Domain or IP format error, please re-enter, e.g.: panel.bt.cn")
                return

        get = public.to_dict_obj({
            "siteName": site_name
        })

        public.set_module_logs('Command line set port-free access', 'create', 1)
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
        print("Panel address: {}".format(address))
        # print("HTTP auth username: {}".format(result['data']['username']))
        # print("HTTP auth password: {}".format(result['data']['password']))
        print("Panel username: {}".format(bt_username))
        print("Panel password: {}".format(bt_password))
        print(raw_tip)
        public.restart_panel()
    if u_input == 33:
        close_reverse_proxy()
        print("Panel reverse proxy closed successfully")
    if u_input == 31:
        os.system('tail -50 /www/server/panel/data/login_err.log')
    if u_input == 26:
        os.system('btpython /www/server/panel/class/config.py SetPanelSSL')
        os.system("/etc/init.d/bt reload")
    if u_input == 28:
        admin_path = input('Please enter new security entrance: ')
        msg = ''
        from BTPanel import admin_path_checks
        if len(admin_path) < 6: msg = 'Security entrance address length cannot be less than 6 characters!'
        if admin_path in admin_path_checks: msg = 'This entrance has been occupied by the panel, please use another entrance!'
        if not public.path_safe_check(admin_path) or admin_path[-1] == '.': msg = 'Entrance address format is incorrect, example: /my_panel'
        if admin_path[0] != '/':
            admin_path = "/" + admin_path
        admin_path_file = 'data/admin_path.pl'
        admin_path1 = '/'
        if os.path.exists(admin_path_file): admin_path1 = public.readFile(admin_path_file).strip()
        if msg != '':
            print('Setup error: {}'.format(msg))
            return
        public.writeFile(admin_path_file, admin_path)
        public.restart_panel()
        print('Security entrance setup successfully: {}'.format(admin_path))

    if u_input == 30:
        ua_file = 'data/limitua.conf'
        if os.path.exists(ua_file):
            with open(ua_file, 'r') as f:
                data = json.load(f)
            data['status'] = '0'  # Set status value to "0"
            with open(ua_file, 'w') as f:
                json.dump(data, f)
        print("|-UA verification disabled")

    if u_input == 29:
        os.system("rm -rf /www/server/panel/data/ssl_verify_data.pl")
        os.system("/etc/init.d/bt restart")
        print("|-Device verification disabled")
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
            input_pwd = raw_input("Please enter new panel password: ")
        else:
            input_pwd = input("Please enter new panel password: ")
        set_panel_pwd(input_pwd.strip(), True)
    elif u_input == 6:
        if sys.version_info[0] == 2:
            input_user = raw_input("Please enter new panel username(≥3 chars): ")
        else:
            input_user = input("Please enter new panel username(≥3 chars): ")
        set_panel_username(input_user.strip())
    elif u_input == 7:
        if sys.version_info[0] == 2:
            input_mysql = raw_input("Please enter new MySQL password: ")
        else:
            input_mysql = input("Please enter new MySQL password: ")
        if not input_mysql:
            print("|-Error: Cannot set empty password")
            return

        if len(input_mysql) < 8:
            print("|-Error: Length cannot be less than 8 characters")
            return

        import re
        rep = r"^[\w@\._]+$"
        if not re.match(rep, input_mysql):
            print("|-Error: Password cannot contain special symbols")
            return

        print(input_mysql)
        set_mysql_root(input_mysql.strip())
    elif u_input == 8:
        input_port = input("Please enter new panel port: ")
        if sys.version_info[0] == 3: input_port = int(input_port)
        if not input_port:
            print("|-Error: No valid port entered")
            return
        if input_port in [80, 443, 21, 20, 22]:
            print("|-Error: Please do not use common ports as panel port")
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
            print("|-Error: Same as current panel port, no need to modify")
            return
        if input_port > 65535 or input_port < 1:
            print("|-Error: Available port range is 1-65535")
            return

        is_exists = public.ExecShell("lsof -i:%s|grep LISTEN|grep -v grep" % input_port)
        if len(is_exists[0]) > 5:
            print("|-Error: Specified port is already occupied by other applications")
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
        print("|-Panel port has been changed to: %s" % input_port)
        print(
            "|-If your server provider is [Alibaba Cloud][Tencent Cloud][Huawei Cloud] or other servers with [Security Group] enabled, please allow port [%s] in the security group to access the panel" % input_port)
        panelPath = '/www/server/panel/data/o.pl'
        if not os.path.exists(panelPath): return False
        o = public.readFile(panelPath).strip()
        if 'tencent' == o:
            print("|-If using Tencent Cloud Lighthouse Linux exclusive version panel, no need to add to security group")
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
            print("|-IP + User-Agent detection enabled")
            print("|-This feature can effectively prevent [replay attacks]")
        else:
            public.writeFile(not_tip, 'True')
            print("|-IP + User-Agent detection disabled")
            print("|-Note: Disabling this feature has risk of [replay attacks]")
    elif u_input == 12:
        auth_file = 'data/domain.conf'
        if os.path.exists(auth_file): os.remove(auth_file)
        os.system("/etc/init.d/bt reload")
        print("|-Domain access restrictions removed")
    elif u_input == 13:
        auth_file = 'data/limitip.conf'
        if os.path.exists(auth_file): os.remove(auth_file)
        os.system("/etc/init.d/bt reload")
        print("|-IP access restrictions removed")
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
            print("|-Repair script not found")
        os.system("bash {} repair_panel".format(sh_path))

    elif u_input == 17:
        l_path = '/www/server/panel/data/log_not_gzip.pl'
        if os.path.exists(l_path):
            print("|-Detected gzip compression disabled, enabling...")
            os.remove(l_path)
            print("|-Gzip compression enabled")
        else:
            print("|-Detected gzip compression enabled, disabling...")
            public.writeFile(l_path, 'True')
            print("|-Gzip compression disabled")
    elif u_input == 18:
        l_path = '/www/server/panel/data/not_auto_backup.pl'
        if os.path.exists(l_path):
            print("|-Detected panel auto backup disabled, enabling...")
            os.remove(l_path)
            print("|-Panel auto backup enabled")
        else:
            print("|-Detected panel auto backup enabled, disabling...")
            public.writeFile(l_path, 'True')
            print("|-Panel auto backup disabled")
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
        print("|-Panel login region restrictions disabled")
    elif u_input == 20:
        limit_info = public.get_limit_area()

        if limit_info['limit_type'] == "allow":
            rule_type = "Only allow"
        else:
            rule_type = "Deny"

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
            print("|-No panel login restriction rules configured!")
            return

        print("|-Current panel login restriction rule: [{}] following regions to login BT-Panel!\n".format(rule_type))
        if country:
            print("Country: {}".format(country))
        if province:
            print("Province: {}".format(province))
        if city:
            print("City: {}".format(city))
    elif u_input == 21:
        backup_lists = public.get_default_db_backup_dates()
        print("To restore panel database to default settings, enter: default\n")
        if len(backup_lists) > 0:
            print("|-Recoverable panel database backup list:")
            for backup_list in backup_lists:
                print("|-{}".format(backup_list))
        else:
            print("|-No recoverable panel database backup list!")

        date = input("Please enter recoverable date(format: 2020-01-01/20200101): ")

        if date == 'default':
            print("|-Warning: Restoring panel database to default settings will clear panel data!")
            confirm = input("Please enter yes to confirm: ")
            if confirm != 'yes':
                print("|-Input is not yes, exited!")
                return
            print("|-Restoring panel database to default settings...")
            public.recover_default_db(date)
            os.system("/etc/init.d/bt restart")
            return

        if not date:
            print("|-Error: No valid date entered")
            return

        if len(date) == 8 or len(date) == 10:
            if len(date) == 8:
                date = date[:4] + '-' + date[4:6] + '-' + date[6:]
            elif len(date) == 10:
                date = date[:4] + '-' + date[5:7] + '-' + date[8:]

            if date not in backup_lists:
                print("|-Error: Specified date does not exist, please enter correct date!")
                return
            print("|-Restoring panel database...")
            print("|-Warning: Restoring panel database will overwrite current panel data!")
            confirm = input("Please enter yes to confirm: ")
            if confirm != 'yes':
                print("|-Input is not yes, exited!")
                return
            result = public.recover_default_db(date)
            if result is False: return
            print("|-Panel database restored successfully!")
            print("|-Restarting panel...")
            os.system("/etc/init.d/bt restart")
            print("|-Panel restarted successfully!")
            print("|-Panel has been restored to {} settings!".format(date))
    elif u_input == 22:
        os.system('tail -100 /www/server/panel/logs/error.log')
    elif u_input == 23:
        filename = '/www/server/panel/config/basic_auth.json'
        if os.path.exists(filename): os.remove(filename)
        os.system('bt reload')
        print("|-BasicAuth disabled")
    elif u_input == 24:
        filename = '/www/server/panel/data/two_step_auth.txt'
        if os.path.exists(filename): os.remove(filename)
        print("|-Google Authenticator disabled")
    elif u_input == 25:
        l_path = '/www/server/panel/data/not_file_history.pl'
        if os.path.exists(l_path):
            print("|-Detected file history backup disabled, enabling...")
            os.remove(l_path)
            print("|-File history backup enabled")
        else:
            print("|-Detected file history backup enabled, disabling...")
            public.writeFile(l_path, 'True')
            print("|-File history backup disabled")
    elif u_input == 34:
        ver = sys.argv[3] if len(sys.argv) > 3 and sys.argv[2]=="34" else ""
        sh_path = "{}/script/upgrade_panel_optimized.py".format(public.get_panel_path())
        if not os.path.exists(sh_path):
            print("|-Upgrade script not found")
        ret_code = os.system("bash {} upgrade_panel {} --dry-run".format(sh_path, ver))
        if ret_code != 0:
            return
        continue_tip = input("Continue to update?(y/n): ")
        if continue_tip.strip().lower() in ('y', 'yes'):
            os.system("bash {} upgrade_panel {}".format(sh_path, ver))
        else:
            print("Update cancelled!")
    elif u_input == 35:
        public.ExecShell("chmod +x /www/server/panel/script/btcli.py")
        os.system("/www/server/panel/script/btcli.py")
    elif u_input == 36:
        public.ExecShell("chmod +x /www/server/panel/script/btcli.py")
        os.system("/www/server/panel/script/btcli.py")
    elif u_input == 99:
        os.system("btpython /www/server/panel/tools_en.py cli")

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
        check_db()  # Panel auto repair
    else:
        print('ERROR: Parameter error')
