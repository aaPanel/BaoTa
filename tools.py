#coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: hwliang <hwl@bt.cn>
# +-------------------------------------------------------------------

#------------------------------
# 工具箱
#------------------------------
import sys,os
panelPath = '/www/server/panel/'
os.chdir(panelPath)
sys.path.insert(0,panelPath + "class/")
import public,time,json
if sys.version_info[0] == 3: raw_input = input

#设置MySQL密码
def set_mysql_root(password):
    import db,os
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
m_version=$(cat /www/server/mysql/version.pl|grep -E "(5.1.|5.5.|5.6.|10.0|10.1)")
m2_version=$(cat /www/server/mysql/version.pl|grep -E "(10.5.|10.4.)")
if [ "$m_version" != "" ];then
    mysql -uroot -e "UPDATE mysql.user SET password=PASSWORD('${pwd}') WHERE user='root'";
elif [ "$m2_version" != "" ];then
    mysql -uroot -e "FLUSH PRIVILEGES;alter user 'root'@'localhost' identified by '${pwd}';alter user 'root'@'127.0.0.1' identified by '${pwd}';FLUSH PRIVILEGES;";
else
    m_version=$(cat /www/server/mysql/version.pl|grep -E "(5.7.|8.0.)")
    if [ "$m_version" != "" ];then
        mysql -uroot -e "FLUSH PRIVILEGES;update mysql.user set authentication_string='' where user='root' and (host='127.0.0.1' or host='localhost');alter user 'root'@'localhost' identified by '${pwd}';alter user 'root'@'127.0.0.1' identified by '${pwd}';FLUSH PRIVILEGES;";
    else
        mysql -uroot -e "update mysql.user set authentication_string=password('${pwd}') where user='root';"
    fi
fi
mysql -uroot -e "FLUSH PRIVILEGES";
pkill -9 mysqld_safe
pkill -9 mysqld
sleep 2
/etc/init.d/mysqld start

echo '==========================================='
echo "root密码成功修改为: ${pwd}"
echo "The root password set ${pwd}  successuful"'''
    
    public.writeFile('mysql_root.sh',root_mysql)
    os.system("/bin/bash mysql_root.sh " + password)
    os.system("rm -f mysql_root.sh")
    
    result = sql.table('config').where('id=?',(1,)).setField('mysql_root',password)
    print(result)

#设置面板密码
def set_panel_pwd(password,ncli = False):
    import db
    sql = db.Sql()
    result = sql.table('users').where('id=?',(1,)).setField('password',public.password_salt(public.md5(password),uid=1))
    username = sql.table('users').where('id=?',(1,)).getField('username')
    if ncli:
        print("|-用户名: " + username)
        print("|-新密码: " + password)
    else:
        print(username)

#设置数据库目录
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

    public.writeFile('mysql_dir.sh',mysql_dir)
    os.system("/bin/bash mysql_dir.sh " + path)
    os.system("rm -f mysql_dir.sh")


#封装
def PackagePanel():
    print('========================================================')
    print('|-正在清理日志信息...'),
    public.M('logs').where('id!=?',(0,)).delete()
    print('\t\t\033[1;32m[done]\033[0m')
    print('|-正在清理任务历史...'),
    public.M('tasks').where('id!=?',(0,)).delete()
    print('\t\t\033[1;32m[done]\033[0m')
    print('|-正在清理网络监控记录...'),
    public.M('network').dbfile('system').where('id!=?',(0,)).delete()
    print('\t\033[1;32m[done]\033[0m')
    print('|-正在清理CPU监控记录...'),
    public.M('cpuio').dbfile('system').where('id!=?',(0,)).delete()
    print('\t\033[1;32m[done]\033[0m')
    print('|-正在清理磁盘监控记录...'),
    public.M('diskio').dbfile('system').where('id!=?',(0,)).delete()
    print('\t\033[1;32m[done]\033[0m')
    print('|-正在清理IP信息...'),
    os.system('rm -f /www/server/panel/data/iplist.txt')
    os.system('rm -f /www/server/panel/data/address.pl')
    os.system('rm -f /www/server/panel/data/*.login')
    os.system('rm -f /www/server/panel/data/domain.conf')
    os.system('rm -f /www/server/panel/data/user*')
    os.system('rm -f /www/server/panel/data/admin_path.pl')
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
    
    
    print("|-请选择用户初始化方式：")
    print("="*50)
    print(" (1) 访问面板页面时显示初始化页面")
    print(" (2) 首次启动时自动随机生成新帐号密码")
    print("="*50)
    p_input = input("请选择初始化方式(default: 1): ")
    print(p_input)
    if p_input in [2,'2']:
        public.writeFile('/www/server/panel/aliyun.pl',"True")
        s_file = '/www/server/panel/install.pl'
        if os.path.exists(s_file): os.remove(s_file)
        public.M('config').where("id=?",('1',)).setField('status',1)
    else:
        public.writeFile('/www/server/panel/install.pl',"True")
        public.M('config').where("id=?",('1',)).setField('status',0)
    port = public.readFile('data/port.pl').strip()
    print('========================================================')
    print('\033[1;32m|-面板封装成功,请不要再登陆面板做任何其它操作!\033[0m')
    if not p_input in [2,'2']:
        print('\033[1;41m|-面板初始化地址: http://{SERVERIP}:'+port+'/install\033[0m')
    else:
        print('\033[1;41m|-获取初始帐号密码命令:bt default \033[0m')

#清空正在执行的任务
def CloseTask():
    ncount = public.M('tasks').where('status!=?',(1,)).delete()
    os.system("kill `ps -ef |grep 'python panelSafe.pyc'|grep -v grep|grep -v panelExec|awk '{print $2}'`")
    os.system("kill `ps -ef |grep 'install_soft.sh'|grep -v grep|grep -v panelExec|awk '{print $2}'`")
    os.system('/etc/init.d/bt restart')
    print("成功清理 " + int(ncount) + " 个任务!")
    
#自签证书
def CreateSSL():
    import OpenSSL
    key = OpenSSL.crypto.PKey()
    key.generate_key( OpenSSL.crypto.TYPE_RSA, 2048 )
    cert = OpenSSL.crypto.X509()
    cert.set_serial_number(0)
    cert.get_subject().CN = public.GetLocalIp()
    cert.set_issuer(cert.get_subject())
    cert.gmtime_adj_notBefore( 0 )
    cert.gmtime_adj_notAfter( 10*365*24*60*60 )
    cert.set_pubkey( key )
    cert.sign( key, 'md5' )
    cert_ca = OpenSSL.crypto.dump_certificate(OpenSSL.crypto.FILETYPE_PEM, cert)
    private_key = OpenSSL.crypto.dump_privatekey(OpenSSL.crypto.FILETYPE_PEM, key)
    if len(cert_ca) > 100 and len(private_key) > 100:
        public.writeFile('ssl/certificate.pem',cert_ca)
        public.writeFile('ssl/privateKey.pem',private_key)
        print('success')
        return
    print('error')

#创建文件
def CreateFiles(path,num):
    if not os.path.exists(path): os.system('mkdir -p ' + path)
    import time;
    for i in range(num):
        filename = path + '/' + str(time.time()) + '__' + str(i)
        open(path,'w+').close()

#计算文件数量
def GetFilesCount(path):
    i=0
    for name in os.listdir(path): i += 1
    return i


#清理系统垃圾
def ClearSystem():
    count = total = 0
    tmp_total,tmp_count = ClearMail()
    count += tmp_count
    total += tmp_total
    print('=======================================================================')
    tmp_total,tmp_count = ClearSession()
    count += tmp_count
    total += tmp_total
    print('=======================================================================')
    tmp_total,tmp_count = ClearOther()
    count += tmp_count
    total += tmp_total
    print('=======================================================================')
    print('\033[1;32m|-系统垃圾清理完成，共删除['+str(count)+']个文件,释放磁盘空间['+ToSize(total)+']\033[0m')

#清理邮件日志
def ClearMail():
    rpath = '/var/spool'
    total = count = 0
    import shutil
    con = ['cron','anacron','mail']
    for d in os.listdir(rpath):
        if d in con: continue
        dpath = rpath + '/' + d
        print('|-正在清理' + dpath + ' ...')
        time.sleep(0.2)
        num = size = 0
        for n in os.listdir(dpath):
            filename = dpath + '/' + n
            fsize = os.path.getsize(filename)
            print('|---['+ToSize(fsize)+'] del ' + filename),
            size += fsize
            if os.path.isdir(filename):
                shutil.rmtree(filename)
            else:
                os.remove(filename)
            print('\t\033[1;32m[OK]\033[0m')
            num += 1
        print('|-已清理['+dpath+'],删除['+str(num)+']个文件,共释放磁盘空间['+ToSize(size)+']')
        total += size
        count += num
    print('=======================================================================')
    print('|-已完成spool的清理，删除['+str(count)+']个文件,共释放磁盘空间['+ToSize(total)+']')
    return total,count

#清理php_session文件
def ClearSession():
    spath = '/tmp'
    total = count = 0
    import shutil
    print('|-正在清理PHP_SESSION ...')
    for d in os.listdir(spath):
        if d.find('sess_') == -1: continue
        filename = spath + '/' + d
        fsize = os.path.getsize(filename)
        print('|---['+ToSize(fsize)+'] del ' + filename),
        total += fsize
        if os.path.isdir(filename):
            shutil.rmtree(filename)
        else:
            os.remove(filename)
        print('\t\033[1;32m[OK]\033[0m')
        count += 1
    print('|-已完成php_session的清理，删除['+str(count)+']个文件,共释放磁盘空间['+ToSize(total)+']')
    return total,count

#清空回收站
def ClearRecycle_Bin():
    import files
    f = files.files()
    f.Close_Recycle_bin(None)
    
#清理其它
def ClearOther():
    clearPath = [
                 {'path':'/www/server/panel','find':'testDisk_'},
                 {'path':'/www/wwwlogs','find':'log'},
                 {'path':'/tmp','find':'panelBoot.pl'},
                 {'path':'/www/server/panel/install','find':'.rpm'},
                 {'path':'/www/server/panel/install','find':'.zip'},
                 {'path':'/www/server/panel/install','find':'.gz'}
                 ]
    
    total = count = 0
    print('|-正在清理临时文件及网站日志 ...')
    for c in clearPath:
        for d in os.listdir(c['path']):
            if d.find(c['find']) == -1: continue
            filename = c['path'] + '/' + d
            if os.path.isdir(filename): continue
            fsize = os.path.getsize(filename)
            print('|---['+ToSize(fsize)+'] del ' + filename),
            total += fsize
            os.remove(filename)
            print('\t\033[1;32m[OK]\033[0m')
            count += 1
    public.serviceReload()
    os.system('sleep 1 && /etc/init.d/bt reload > /dev/null &')
    print('|-已完成临时文件及网站日志的清理，删除['+str(count)+']个文件,共释放磁盘空间['+ToSize(total)+']')
    return total,count

#关闭普通日志
def CloseLogs():
    try:
        paths = ['/usr/lib/python2.7/site-packages/web/httpserver.py','/usr/lib/python2.6/site-packages/web/httpserver.py']
        for path in paths:
            if not os.path.exists(path): continue
            hsc = public.readFile(path)
            if hsc.find('500 Internal Server Error') != -1: continue
            rstr = '''def log(self, status, environ):
        if status != '500 Internal Server Error': return;'''
            hsc = hsc.replace("def log(self, status, environ):",rstr)
            if hsc.find('500 Internal Server Error') == -1: return False
            public.writeFile(path,hsc)
    except:pass

#字节单位转换
def ToSize(size):
    ds = ['b','KB','MB','GB','TB']
    for d in ds:
        if size < 1024: return str(size)+d
        size = size / 1024
    return '0b'

#随机面板用户名
def set_panel_username(username = None):
    import db
    sql = db.Sql()
    if username:
        if len(username) < 3:
            print("|-错误，用户名长度不能少于3位")
            return
        if username in ['admin','root']:
            print("|-错误，不能使用过于简单的用户名")
            return

        sql.table('users').where('id=?',(1,)).setField('username',username)
        print("|-新用户名: %s" % username)
        return
    
    username = sql.table('users').where('id=?',(1,)).getField('username')
    if username == 'admin': 
        username = public.GetRandomString(8).lower()
        sql.table('users').where('id=?',(1,)).setField('username',username)
    print('username: ' + username)
    
#设定idc
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
        public.writeFile(pFile,json.dumps(pInfo))
        tFile = panelPath + '/data/title.pl'
        titleNew = pInfo['brand'] + u'面板'
        if os.path.exists(tFile):
            title = public.GetConfigValue('title')
            if title == '' or title == '宝塔Linux面板': 
                public.writeFile(tFile,titleNew)
                public.SetConfigValue('title',titleNew)
        else:
            public.writeFile(tFile,titleNew)
            public.SetConfigValue('title',titleNew)
        return True
    except:pass

#将插件升级到6.0
def update_to6():
    print("====================================================")
    print("正在升级插件...")
    print("====================================================")
    download_address = public.get_url()
    exlodes = ['gitlab','pm2','mongodb','deployment_jd','logs','docker','beta','btyw']
    for pname in os.listdir('plugin/'):
        if not os.path.isdir('plugin/' + pname): continue
        if pname in exlodes: continue
        print("|-正在升级【%s】..." % pname),
        download_url = download_address + '/install/plugin/' + pname + '/install.sh'
        to_file = '/tmp/%s.sh' % pname
        public.downloadFile(download_url,to_file)
        os.system('/bin/bash ' + to_file + ' install &> /tmp/plugin_update.log 2>&1')
        print("    \033[32m[成功]\033[0m")
    print("====================================================")
    print("\033[32m所有插件已成功升级到最新!\033[0m")
    print("====================================================")

#命令行菜单
def bt_cli(u_input = 0):
    raw_tip = "==============================================="
    if not u_input:
        print("===============宝塔面板命令行==================")
        print("(1) 重启面板服务           (8) 改面板端口")
        print("(2) 停止面板服务           (9) 清除面板缓存")
        print("(3) 启动面板服务           (10) 清除登录限制")
        print("(4) 重载面板服务           (11) 取消入口限制")
        print("(5) 修改面板密码           (12) 取消域名绑定限制")
        print("(6) 修改面板用户名         (13) 取消IP访问限制")
        print("(7) 强制修改MySQL密码      (14) 查看面板默认信息")
        print("(22) 显示面板错误日志      (15) 清理系统垃圾")
        print("(23) 关闭BasicAuth认证     (16) 修复面板(检查错误并更新面板文件到最新版)")
        print("(24) 关闭谷歌认证          (17) 设置日志切割是否压缩")
        print("(25) 设置是否保存文件历史副本  (18) 设置是否自动备份面板")
        print("(0) 取消")
        print(raw_tip)
        try:
            u_input = input("请输入命令编号：")
            if sys.version_info[0] == 3: u_input = int(u_input)
        except: u_input = 0

    nums = [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,22,23,24,25]
    if not u_input in nums:
        print(raw_tip)
        print("已取消!")
        exit()

    print(raw_tip)
    print("正在执行(%s)..." % u_input)
    print(raw_tip)

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
        if len(input_pwd.strip()) < 5:
            print("|-错误，密码长度不能小于5位")
            return
        set_panel_pwd(input_pwd.strip(),True)
    elif u_input == 6:
        if sys.version_info[0] == 2:
            input_user = raw_input("请输入新的面板用户名(>3位)：")
        else:
            input_user = input("请输入新的面板用户名(>3位)：")
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
        if input_port in [80,443,21,20,22]:
            print("|-错误，请不要使用常用端口作为面板端口")
            return
        old_port = int(public.readFile('data/port.pl'))
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

        public.writeFile('data/port.pl',str(input_port))
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
        print("|-若您的服务器提供商是[阿里云][腾讯云][华为云]或其它开启了[安全组]的服务器,请在安全组放行[%s]端口才能访问面板" % input_port)
    elif u_input == 9:
        sess_file = '/www/server/panel/data/session'
        if os.path.exists(sess_file):
            os.system("rm -f {}/*".format(sess_file))
        os.system("/etc/init.d/bt reload")
    elif u_input == 10:
        os.system("/etc/init.d/bt reload")
    elif u_input == 11:
        auth_file = 'data/admin_path.pl'
        if os.path.exists(auth_file): os.remove(auth_file)
        os.system("/etc/init.d/bt reload")
        print("|-已取消入口限制")
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
        os.system("/etc/init.d/bt default")
    elif u_input == 15:
        ClearSystem()
    elif u_input == 16:
        os.system("curl http://download.bt.cn/install/update6.sh|bash")
    elif u_input == 17:
        l_path = '/www/server/panel/data/log_not_gzip.pl'
        if os.path.exists(l_path):
            print("|-检测到已关闭gzip压缩功能,正在开启...")
            os.remove(l_path)
            print("|-已开启gzip压缩")
        else:
            print("|-检测到已开启gzip压缩功能,正在关闭...")
            public.writeFile(l_path,'True')
            print("|-已关闭gzip压缩")
    elif u_input == 18:
        l_path = '/www/server/panel/data/not_auto_backup.pl'
        if os.path.exists(l_path):
            print("|-检测到已关闭面板自动备份功能,正在开启...")
            os.remove(l_path)
            print("|-已开启面板自动备份功能")
        else:
            print("|-检测到已开启面板自动备份功能,正在关闭...")
            public.writeFile(l_path,'True')
            print("|-已关闭面板自动备份功能")
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
            public.writeFile(l_path,'True')
            print("|-已关闭文件副本功能")



if __name__ == "__main__":
    type = sys.argv[1]
    if type == 'root':
        set_mysql_root(sys.argv[2])
    elif type == 'panel':
        set_panel_pwd(sys.argv[2])
    elif type == 'username':
        set_panel_username()
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
    elif type == "cli":
        clinum = 0
        if len(sys.argv) > 2: clinum = int(sys.argv[2])
        bt_cli(clinum)
    else:
        print('ERROR: Parameter error')
