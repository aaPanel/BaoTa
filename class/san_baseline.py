#!/usr/bin/python
# coding: utf-8
# | Author: 1249648969@qq.com
# +--------------------------------------------------------------------
# |   宝塔安全基线扫描                                                   |
# +--------------------------------------------------------------------
import sys, os

if sys.version_info[0] == 2:
    reload(sys)
    sys.setdefaultencoding('utf-8')
os.chdir('/www/server/panel')
sys.path.append("class/")
import time, hashlib, sys, os, json, requests, re, public, random, string, requests


class san_baseline:
    setupPath = '/www/server'
    logPath = '/www/server/panel/data/san_baseline.log'
    _Speed = None
    config = '/www/server/panel/data/result.log'

    def __init__(self):

        if not os.path.exists(self.logPath):
            resutl={}
            public.WriteFile(self.logPath,json.dumps(resutl))
        if not os.path.exists(self.config):
            resutl = {}
            public.WriteFile(self.config, json.dumps(resutl))


    # SSH 安全扫描
    def ssh_security(self):
        # 确保SSH MaxAuthTries 设置为3-6之间
        result = []
        ssh_maxauth = {
            "type": "file",
            "harm": "高",
            "name": "确保SSH MaxAuthTries 设置为3-6之间",
            "file": "/etc/ssh/sshd_config",
            "Suggestions": "加固建议   在/etc/ssh/sshd_config 中取消MaxAuthTries注释符号#, 设置最大密码尝试失败次数3-6 建议为4",
            "repair": "MaxAuthTries 4",
            "rule": [
                {"re": "\nMaxAuthTries\s*(\d+)", "check": {"type": "number", "max": 7, "min": 3}}]
        }
        ret = self.check_san_baseline(ssh_maxauth)
        if not ret: result.append(ssh_maxauth)
        # SSHD强制使用V2安全协议
        sshd_v2 = {
            "type": "file",
            "harm": "高",
            "name": "SSHD 强制使用V2安全协议",
            "file": "/etc/ssh/sshd_config",
            "Suggestions": "加固建议   在/etc/ssh/sshd_config 文件按如相下设置参数",
            "repair": "Protocol 2",
            "rule": [
                {"re": "\nProtocol\s*(\d+)", "check": {"type": "number", "max": 3, "min": 1}}]
        }
        ret = self.check_san_baseline(sshd_v2)

        if not ret: result.append(sshd_v2)
        # 设置SSH空闲超时退出时间
        set_ssh_timetout = {
            "type": "file",
            "harm": "高",
            "name": "设置SSH空闲超时退出时间",
            "file": "/etc/ssh/sshd_config",
            "Suggestions": "加固建议   在/etc/ssh/sshd_config 将ClientAliveInterval设置为300到900，即5-15分钟，将ClientAliveCountMax设置为0-3",
            "repair": "ClientAliveInterval 600  ClientAliveCountMax 2",
            "rule": [
                {"re": "\nClientAliveInterval\s*(\d+)", "check": {"type": "number", "max": 900, "min": 300}}]
        }
        ret = self.check_san_baseline(set_ssh_timetout)
        if not ret: result.append(set_ssh_timetout)
        # 确保SSH LogLevel 设置为INFO
        ssh_log_evel = {
            "type": "file",
            "harm": "高",
            "name": "确保SSH LogLevel 设置为INFO",
            "file": "/etc/ssh/sshd_config",
            "Suggestions": "加固建议   在/etc/ssh/sshd_config 文件以按如下方式设置参数（取消注释）",
            "repair": "LogLevel INFO",
            "rule": [
                {"re": "\nLogLevel\s*(\w+)", "check": {"type": "string", "value": ['INFO']}}]
        }
        ret = self.check_san_baseline(ssh_log_evel)

        if not ret: result.append(ssh_log_evel)

        # 禁止SSH空密码用户登陆
        ssh_not_pass = {
            "type": "file",
            "harm": "高",
            "name": "禁止SSH空密码用户登陆",
            "file": "/etc/ssh/sshd_config",
            "Suggestions": "加固建议  在/etc/ssh/sshd_config 将PermitEmptyPasswords配置为no",
            "repair": "PermitEmptyPasswords no",
            "rule": [
                {"re": "\nPermitEmptyPasswords\s*(\w+)", "check": {"type": "string", "value": ['no']}}]
        }
        ret = self.check_san_baseline(ssh_not_pass)
        if not ret: result.append(ssh_not_pass)

        # 端口非默认
        ssh_port_default = {
            "type": "file",
            "name": "SSH使用默认端口22",
            "harm": "高",
            "file": "/etc/ssh/sshd_config",
            "Suggestions": "加固建议   在/etc/ssh/sshd_config 将Port 设置为6000到65535随意一个, 例如",
            "repair": "Port 60151",
            "rule": [
                {"re": "Port\s*(\d+)", "check": {"type": "number", "max": 65535, "min": 22}}]
        }
        ret = self.check_san_baseline(ssh_port_default)
        if not ret: result.append(ssh_port_default)
        return result

    ######面板安全监测##########################

    # 监测是否开启IP限制登陆
    def get_limitip(self):
        if os.path.exists('/www/server/panel/data/limitip.conf'):
            ret = public.ReadFile('/www/server/panel/data/limitip.conf')
            if not ret:
                return False
            return True
        else:
            return False

    # 监测默认端口
    def get_port(self):
        ret = public.ReadFile('/www/server/panel/data/port.pl')
        ret = int(public.ReadFile('/www/server/panel/data/port.pl'))
        if ret == 8888:
            return False
        else:
            return True

    # 监测是否开启安全入口
    def get_admin_path(self):
        if os.path.exists('/www/server/panel/data/admin_path.pl'):
            return True
        else:
            return False

    # 域名绑定
    def get_domain(self):
        if os.path.exists('/www/server/panel/data/domain.conf'):
            return True
        else:
            return False

    # 查看APi是否开启
    def get_api_open(self):
        if os.path.exists('/www/server/panel/config/api.json'):
            ret = json.loads(public.ReadFile('/www/server/panel/config/api.json'))
            if ret['open']:
                return False
            return True
        else:
            return True

    # 查看用户名是否是弱用户名
    def get_username(self):
        userInfo = public.M('users').where("id=?", (1,)).field('id,username,password').find()
        if userInfo['username'] == 'admin' or userInfo['username'] == 'root' or userInfo['username'] == 'password':
            return False
        else:
            return True

    # 不安全的插件
    def get_secite(self):
        if os.path.exists('/www/server/panel/plugin/ss'):
            return False
        else:
            return True

    # 面板目录权限

    # 面板安全扫描
    def panel_security(self):
        result = []
        if not self.get_limitip():
            ret1 = {
                "harm": "中",
                "type": "file",
                "name": "宝塔面板登陆未开启（授权IP）限制登陆",
                "Suggestions": "加固建议 :如果你的IP存在固定IP建议添加到面板的授权IP",
                "repair": "首页-->面板设置->授权IP->添加IP",
            }
            result.append(ret1)
            # 端口是否是8888端口
            get_port_default = self.get_port()
            if not get_port_default:
                ret1 = {
                    "harm": "中",
                    "type": "file",
                    "name": "宝塔面板登陆端口未修改",
                    "Suggestions": "加固建议 : 修改默认端口,例如8989或56641",
                    "repair": "首页-->面板设置->面板端口->修改端口-->保存",
                }
                result.append(ret1)
            get_admin_path = self.get_admin_path()
            if not get_admin_path:
                ret1 = {
                    "harm": "高",
                    "type": "file",
                    "name": "宝塔面板登陆未开启安全入口",
                    "Suggestions": "加固建议 : 修改安全入口例如 /123456789",
                    "repair": "首页-->面板设置->安全入口->修改安全入口-->保存",
                }
                result.append(ret1)
            get_api_open = self.get_api_open()
            if not get_api_open:
                ret1 = {
                    "harm": "中",
                    "type": "file",
                    "name": "面板已经开启API(请注意是否需要开启API或者API的白名单IP是否是授权IP)",
                    "Suggestions": "加固建议 : 不必要使用时刻建议关闭",
                    "repair": "首页-->面板设置->API接口->关闭|开启",
                }
                result.append(ret1)
        get_username = self.get_username()
        if not get_username:
            ret1 = {
                "harm": "高",
                "type": "file",
                "name": "面板用户名过于简单",
                "Suggestions": "加固建议 : 修改为强用户名",
                "repair": "例如:ad!@#min1750..",
            }
            result.append(ret1)

        get_secite = self.get_secite()
        if not get_secite:
            ret1 = {
                "harm": "高",
                "type": "file",
                "name": "存在国家不允许的翻墙插件",
                "Suggestions": "加固建议 : 建议删除SS插件",
                "repair": "rm -rf /www/server/panel/plugin/ss",
            }
            result.append(ret1)
        panel_chome = [
            {
                "type": "chmod",
                "file": "/www/server/panel/BTPanel",
                "chmod": [600],
                "user": ['root'],
                'group': ['root']
            }, {
                "type": "chmod",
                "file": "/www/server/panel/class",
                "chmod": [600],
                "user": ['root'],
                'group': ['root']
            }, {
                "type": "chmod",
                "file": "/www/server/panel/config",
                "chmod": [600],
                "user": ['root'],
                'group': ['root']
            }, {
                "type": "chmod",
                "file": "/www/server/panel/data",
                "chmod": [600],
                "user": ['root'],
                'group': ['root']
            }, {
                "type": "chmod",
                "file": "/www/server/panel/install",
                "chmod": [600],
                "user": ['root'],
                'group': ['root']
            }, {
                "type": "chmod",
                "file": "/www/server/panel/logs",
                "chmod": [600],
                "user": ['root'],
                'group': ['root']
            }, {
                "type": "chmod",
                "file": "/www/server/panel/package",
                "chmod": [600],
                "user": ['root'],
                'group': ['root']
            }, {
                "type": "chmod",
                "file": "/www/server/panel/plugin",
                "chmod": [600],
                "user": ['root'],
                'group': ['root']
            }, {
                "type": "chmod",
                "file": "/www/server/panel/rewrite",
                "chmod": [600],
                "user": ['root'],
                'group': ['root']
            }, {
                "type": "chmod",
                "file": "/www/server/panel/ssl",
                "chmod": [600],
                "user": ['root'],
                'group': ['root']
            }, {
                "type": "chmod",
                "file": "/www/server/panel/temp",
                "chmod": [600],
                "user": ['root'],
                'group': ['root']
            }, {
                "type": "chmod",
                "file": "/www/server/panel/vhost",
                "chmod": [600],
                "user": ['root'],
                'group': ['root']
            }
        ]
        for i in panel_chome:
            if not self.check_san_baseline(i):
                ret1 = {
                    "harm": "高",
                    "type": "file",
                    "name": "面板关键性文件权限错误%s" % i['file'],
                    "Suggestions": "加固建议 : %s 权限改为%s 所属用户为%s" % (i['file'], i['chmod'], i['user']),
                    "repair": "加固建议 : %s 权限改为%s 所属用户为%s" % (i['file'], i['chmod'], i['user']),
                }
                result.append(ret1)

        return result

    # php版本泄露
    def php_version_info(self):
        ret = []
        php_path = '/www/server/php/'
        php_list = os.listdir(php_path)
        if len(php_list) >= 1:
            for i in php_list:
                if os.path.isdir(php_path + i):
                    if os.path.exists(php_path + i + '/etc/php.ini'):
                        php_data = {
                            "type": "file",
                            "harm": "中",
                            "name": "PHP 版本泄露",
                            "file": php_path + i + '/etc/php.ini',
                            "Suggestions": "加固建议, 在%s expose_php的值修改为Off中修改" % (php_path + i + '/etc/php.ini'),
                            "repair": "expose_php = Off",
                            "rule": [
                                {"re": "\nexpose_php\s*=\s*(\w+)", "check": {"type": "string", "value": ['Off']}}]
                        }
                        if not self.check_san_baseline(php_data):
                            ret.append(php_data)
        return ret

    # PHP 危险函数
    def php_error_funcation(self):
        ret = []
        php_path = '/www/server/php/'
        php_list = os.listdir(php_path)
        if len(php_list) >= 1:
            for i in php_list:
                if os.path.isdir(php_path + i):
                    if os.path.exists(php_path + i + '/etc/php.ini'):
                        php_data = {
                            "type": "diff",
                            "harm": "严重",
                            "name": "PHP%s 中存在危险函数未禁用" % i,
                            "file": php_path + i + '/etc/php.ini',
                            "Suggestions": "加固建议, 在%s 中 disable_functions= 修改成如下:" % (php_path + i + '/etc/php.ini'),
                            "repair": "disable_functions = passthru,exec,system,chroot,chgrp,chown,shell_exec,popen,proc_open,ini_alter,ini_restore,dl,openlog,syslog,readlink,symlink,popepassthru",
                            "rule": [
                                {"re": "\ndisable_functions\s?=\s?(.+)", "check": {"type": "string", "value": [
                                    'passthru,exec,system,chroot,chgrp,chown,shell_exec,popen,proc_open,ini_alter,ini_restore,dl,openlog,syslog,readlink,symlink,popepassthru']}}]
                        }
                        if not self.check_san_baseline(php_data):
                            ret.append(php_data)
        return ret

    # 版本过旧
    def php_dir(self):
        php_version_dir = {
            "type": "dir",
            "harm": "高",
            "name": "PHP 5.2 版本过旧",
            "file": '/www/server/php/52',
            "Suggestions": "加固建议：不再使用php5.2 ",
            "repair": "PHP 5.2 已经被淘汰建议升级更高的版本",
            "rule": []
        }
        if not self.check_san_baseline(php_version_dir):
            return php_version_dir
        return {}

    # php配置安全

    def php_security(self):
        ret = []
        php_path = '/www/server/php/'
        php_list = os.listdir(php_path)
        if len(php_list) >= 1:
            for i in php_list:
                if os.path.isdir(php_path + i):
                    if os.path.exists(php_path + i + '/etc/php.ini'):
                        php_data = {
                            "type": "file",
                            "harm": "中",
                            "name": "PHP%s 版本泄露" % i,
                            "file": php_path + i + '/etc/php.ini',
                            "Suggestions": "加固建议, 在%s expose_php的值修改为Off中修改" % (php_path + i + '/etc/php.ini'),
                            "repair": "expose_php = Off",
                            "rule": [
                                {"re": "\nexpose_php\s*=\s*(\w+)", "check": {"type": "string", "value": ['Off']}}]
                        }
                        if not self.check_san_baseline(php_data):
                            ret.append(php_data)

        if len(php_list) >= 1:
            for i in php_list:
                if os.path.isdir(php_path + i):
                    if os.path.exists(php_path + i + '/etc/php.ini'):
                        php_data = {
                            "type": "diff",
                            "harm": "严重",
                            "name": "PHP%s 中存在危险函数未禁用" % i,
                            "file": php_path + i + '/etc/php.ini',
                            "Suggestions": "加固建议, 在%s 中 disable_functions= 修改成如下:" % (php_path + i + '/etc/php.ini'),
                            "repair": "disable_functions = passthru,exec,system,chroot,chgrp,chown,shell_exec,popen,proc_open,ini_alter,ini_restore,dl,openlog,syslog,readlink,symlink,popepassthru",
                            "rule": [
                                {"re": "\ndisable_functions\s?=\s?(.+)", "check": {"type": "string", "value": [
                                    'passthru,exec,system,chroot,chgrp,chown,shell_exec,popen,proc_open,ini_alter,ini_restore,dl,openlog,syslog,readlink,symlink,popepassthru']}}]
                        }
                        if not self.check_san_baseline(php_data):
                            ret.append(php_data)

        php_version_dir = {
            "type": "dir",
            "harm": "高",
            "name": "PHP 5.2 版本过旧",
            "file": '/www/server/php/52',
            "Suggestions": "加固建议：不再使用php5.2 ",
            "repair": "PHP 5.2 已经被淘汰建议升级更高的版本",
            "rule": []
        }
        if not self.check_san_baseline(php_version_dir):
            return php_version_dir
        return ret

    # Redis 配置按
    def redis_security(self):
        ret = []
        # 查看redis 是否监听的是0.0.0.0 返回True 代表高危
        redis_server_ip = {
            "type": "file",
            "harm": "高",
            "name": "Redis 监听的地址为0.0.0.0",
            "file": '/www/server/redis/redis.conf',
            "Suggestions": "加固建议, 在%s 中的监听IP设置为127.0.0.1 例如" % ('/www/server/redis/redis.conf'),
            "repair": "bind 127.0.0.1",
            "rule": [
                {"re": "\nbind\s*(.+)", "check": {"type": "string", "value": ['0.0.0.0']}}]
        }
        if self.check_san_baseline(redis_server_ip):
            ret.append(redis_server_ip)

        # 查看redis是否设置密码
        redis_server_not_pass = {
            "type": "password",
            "harm": "高",
            "name": "Redis 查看是否设置密码",
            "file": '/www/server/redis/redis.conf',
            "Suggestions": "加固建议, 在%s 中的监听IP设置为127.0.0.1 例如" % ('/www/server/redis/redis.conf'),
            "repair": "bind 127.0.0.1",
            "rule": [
                {"re": "\nrequirepass\s*(.+)", "check": {"type": "string", "value": []}}]
        }
        if not self.check_san_baseline(redis_server_not_pass):
            ret.append(redis_server_not_pass)

        # 查看redis 是否是弱密码
        redis_server_pass = {
            "type": "password",
            "harm": "高",
            "name": "Redis 存在弱密码",
            "file": '/www/server/redis/redis.conf',
            "Suggestions": "加固建议, 在%s 中requirepass 设置为强密码" % ('/www/server/redis/redis.conf'),
            "repair": "例如:Ad@#$#@A1545132..",
            "rule": [
                {"re": "\nrequirepass\s*(.+)", "check": {"type": "string", "value": ['123456', 'admin', 'damin888']}}]
        }
        if not self.check_san_baseline(redis_server_pass):
            ret.append(redis_server_pass)
        # 查看版本是否是低于最新版本
        if os.path.exists('/www/server/redis/version.pl'):
            re2t = public.ReadFile('/www/server/redis/version.pl')
            if re2t != '5.0.3':
                ret2 = {
                    "type": "password",
                    "harm": "高",
                    "name": "Redis 版本低于最新版本",
                    "file": '/www/server/redis/redis.conf',
                    "Suggestions": "加固建议,升级到最新版的redis",
                    "repair": "最新版为5.0.3"
                }
                ret.append(ret2)
        return ret

    # memcached 配置安全
    def memcache_security(self):
        ret = []
        memcache_bind = {
            "type": "file",
            "harm": "高",
            "name": "Memcache 监听IP为0.0.0.0",
            "file": '/etc/init.d/memcached',
            "Suggestions": "加固建议, 在%s 中的监听IP设置为127.0.0.1 例如" % ('/etc/init.d/memcached'),
            "repair": "IP=127.0.0.1",
            "rule": [
                {"re": "\nIP\s?=\s?(.+)", "check": {"type": "string", "value": ['0.0.0.0']}}]
        }
        if self.check_san_baseline(memcache_bind):
            ret.append(memcache_bind)
        return ret

    # 查看是否是弱密码
    def get_root_pass(self):
        # mysql 弱密码
        ret = public.M('config').field('mysql_root').select()[0]['mysql_root']
        if ret == '123456' or ret == 'admin':
            return False
        if len(ret) <= 6:
            return False
        return True

    # 查看mysql 是否有对外连接用户
    def chekc_mysql_user(self):
        ret = public.M('config').field('mysql_root').select()[0]['mysql_root']
        sql = ''' mysql -uroot -p''' + ret + ''' -e "select User,Host from mysql.user where host='%'" '''
        resutl = public.ExecShell(sql)
        if resutl[0] == '':
            return True
        else:
            return False

    # mysql 配置安全
    def mysql_security(self):
        result = []
        if not self.get_root_pass():
            ret = {
                "type": "password",
                "harm": "高",
                "name": "Mysql root密码为弱密码",
                "file": '/etc/init.d/memcached',
                "Suggestions": "加固建议： 使用强密码",
                "repair": "例如:adM1#@$544..",
            }
            result.append(ret)

        if public.M('firewall').where('port=?', ('3306',)).count():
            ret = {
                "type": "password",
                "harm": "高",
                "name": "3306 端口对外开放",
                "file": '/etc/init.d/memcached',
                "Suggestions": "加固建议： 建议3306不对外开放，如果是特殊需求可以忽略这次记录",
                "repair": "关闭3306对外访问",
            }
            result.append(ret)

        if not self.chekc_mysql_user():
            e = '''select User,Host from mysql.user where host='%' '''
            ret = {
                "type": "password",
                "harm": "高",
                "name": "Mysql 存在外部连接用户",
                "file": '/etc/init.d/memcached',
                "Suggestions": "加固建议： 进入数据库查看mysql用户表",
                "repair": e,
            }
            result.append(ret)
        return result

    # 系统用户 安全
    def user_security(self):
        result = []
        # 密码复杂度检查
        pass_fuza = {
            "type": "file",
            "harm": "中",
            "name": "SSH 密码复杂度检查",
            "file": "/etc/security/pwquality.conf",
            "Suggestions": "加固建议/etc/security/pwquality.conf, 把minlen(密码最小长度)设置为9-32,把minclass(至少包含小写字母，大写字母，数字，特殊字符等3类或者4类)",
            "repair": "minlen=10  minclass=3",
            "rule": [
                {"re": "minlen\s*=\s*(\d+)", "check": {"type": "number", "max": 32, "min": 9}}]
        }
        if not self.check_san_baseline(pass_fuza):
            result.append(pass_fuza)

        # 设置时间失效时间
        set_time_out = {
            "type": "file",
            "harm": "高",
            "name": "SSH 用户设置时间失效时间",
            "file": "/etc/login.defs",
            "Suggestions": "加固建议  使用非密码登陆方式密钥对。请忽略此项, 在/etc/login.defs 中将PASS_MAX_DAYS 参数设置为60-180之间",
            "repair": "PASS_MAX_DAYS 90   需同时执行命令设置root 密码失效时间   命令如下:  chage --maxdays 90 root",
            "rule": [
                {"re": "PASS_MAX_DAYS\s*(\d+)", "check": {"type": "number", "max": 180, "min": 60}}]
        }
        if not self.check_san_baseline(set_time_out):
            result.append(set_time_out)

        # 设置密码修改最小间隔时间
        set_pass_time_out = {
            "type": "file",
            "harm": "中",
            "name": "设置密码修改最小间隔时间",
            "file": "/etc/login.defs",
            "Suggestions": "加固建议   在/etc/login.defs PASS_MIN_DAYS 参数设置为7-14之间",
            "repair": "PASS_MIN_DAYS 7   需同时执行命令设置root 密码失效时间   命令如下:  chage --mindays 7 root",
            "rule": [
                {"re": "PASS_MIN_DAYS\s*(\d+)", "check": {"type": "number", "max": 14, "min": 7}}]
        }
        if not self.check_san_baseline(set_pass_time_out):
            result.append(set_pass_time_out)

        # 存在非root 的管理员用户(危险)
        get_root_0 = {
            "type": "shell",
            "harm": "紧急",
            "name": "存在非root 的管理员用户(危险)",
            "ps": "除root以为的其他的UID为0的用户的应该删除。或者为其分配新的UID",
            "cmd": '''cat /etc/passwd | awk -F: '($3 == 0) { print $1 }'|grep -v '^root$' ''',
            "find": {"re": "\w+"}
        }
        if not self.check_san_baseline(get_root_0):
            result.append(get_root_0)

        # 开启地址空间布局随机化
        set_kerner_space = {
            "type": "file",
            "harm": "中",
            "name": "开启地址空间布局随机化",
            "ps": "它将进程的内存空间地址随机化来增加入侵者预测目的地址难度, 从而减低进程成功入侵的风险",
            "file": "/proc/sys/kernel/randomize_va_space",
            "Suggestions": "加固建议：执行命令",
            "repair": "sysctl -w kernel.randomize_va_space=2",
            "rule": [
                {"re": "\d+", "check": {"type": "number", "max": 3, "min": 1}}]
        }
        if not self.check_san_baseline(set_kerner_space):
            result.append(set_kerner_space)

        # 确保密码到期警告天数为7或更多
        pass_warndays = {
            "type": "file",
            "harm": "中",
            "name": "SSH 用户设置时间失效时间",
            "file": "/etc/login.defs ",
            "Suggestions": "加固建议  在/etc/login.defs PASS_WARN_AGE 参数设置为7-14之间，建议为7",
            "repair": "PASS_WARN_AGE 7  同时执行命令使root用户设置生效 chage --warndays 7 root",
            "rule": [
                {"re": "PASS_WARN_AGE\s*(\d+)", "check": {"type": "number", "max": 15, "min": 6}}]
        }

        if not self.check_san_baseline(pass_warndays):
            result.append(pass_warndays)

        # 查看用户是否空密码的用户
        if len(self.user_not_password()) >= 1:
            user_len = {
                "type": "file",
                "harm": "中",
                "name": "系统存在空密码的用户",
                "file": "/etc/login.defs ",
                "Suggestions": "加固建议  为如下%s这些用户添加密码" % self.user_not_password(),
                "repair": "（如果用户不用可以删除）",
            }
            result.append(user_len)

        return result

    # 查看用户是否有空密码的用户
    def user_not_password(self):
        ret = public.ReadFile('/etc/passwd')
        ret = ret.split('\n')
        base_user = []
        not_pass_user = []
        for i in ret:
            i = i.split(':')
            if i[-1] == '/sbin/nologin':
                continue
            if i[0] == '': continue
            base_user.append(i[0])
        check_file_resutl = public.ReadFile('/etc/shadow')
        check_file_resutl = check_file_resutl.split('\n')
        for i in check_file_resutl:
            if not i: continue
            i = i.split(':')
            # print(i[0],base_user)
            if i[0] in base_user:
                if i[1] == '!!':
                    not_pass_user.append(i[0])
        return not_pass_user

    # 计划任务 安全
    def tasks_security(self):
        ret = []
        f = open('/var/spool/cron/root', 'r')
        for i in f.readlines():
            if not i: continue;
            i2 = i
            i = i.strip().split()
            if not i: continue
            if i == None: continue
            if i[5]:
                if '/www/server/' not in i[5]:
                    if '/root/.acme.sh' not in i[5]:
                        if 'wget' in i or 'curl' in i or 'bash' or 'http://' in i or 'https://' in i:
                            task = {}
                            task['name'] = '异常计划任务'
                            task["harm"] = "高",
                            task["repair"] = "请排查是否是异常下载",
                            task['Suggestions'] = '请排查是否是异常下载'
                            task['list'] = i2
                            ret.append(task)
        return ret

    # system 关键目录权限
    def system_dir_security(self):
        # 关键性文件权限
        result = []
        user_config_chmoe = [
            {
                "type": "chmod",
                "file": "/etc/passwd",
                "chmod": [644],
                "user": ['root'],
                'group': ['root']
            }, {
                "type": "chmod",
                "file": "/etc/shadow",
                "chmod": [400],
                "user": ['root'],
                'group': ['root']
            }, {
                "type": "chmod",
                "file": "/etc/group",
                "chmod": [644],
                "user": ['root'],
                'group': ['root']
            }, {
                "type": "chmod",
                "file": "/etc/gshadow",
                "chmod": [400],
                "user": ['root'],
                'group': ['root']
            }, {
                "type": "chmod",
                "file": "/etc/hosts.allow",
                "chmod": [644],
                "user": ['root'],
                'group': ['root']
            }, {
                "type": "chmod",
                "file": "/etc/hosts.deny",
                "chmod": [644],
                "user": ['root'],
                'group': ['root']
            }, {
                "type": "chmod",
                "file": "/www",
                "chmod": [755],
                "user": ['root'],
                'group': ['root']
            }, {
                "type": "chmod",
                "file": "/www/server",
                "chmod": [755],
                "user": ['root'],
                'group': ['root']
            }, {
                "type": "chmod",
                "file": "/www/wwwroot",
                "chmod": [755],
                "user": ['root'],
                'group': ['root']
            }, {
                "type": "chmod",
                "file": "/etc/rc.d",
                "chmod": [755],
                "user": ['root'],
                'group': ['root']
            }, {
                "type": "chmod",
                "file": "/etc/rc.local",
                "chmod": [644],
                "user": ['root'],
                'group': ['root']
            }, {
                "type": "chmod",
                "file": "/etc/rc.d/rc.local",
                "chmod": [644],
                "user": ['root'],
                'group': ['root']
            }, {
                "type": "chmod",
                "file": "/var/spool/cron/root",
                "chmod": [600],
                "user": ['root'],
                'group': ['root']
            }
        ]
        for i in user_config_chmoe:
            if not self.check_san_baseline(i):
                ret1 = {
                    "harm": "高",
                    "type": "file",
                    "name": "系统关键性文件权限错误%s" % i['file'],
                    "Suggestions": "加固建议 : %s 权限改为%s 所属用户为%s" % (i['file'], i['chmod'], i['user']),
                    "repair": "加固建议 : %s 权限改为%s 所属用户为%s" % (i['file'], i['chmod'], i['user']),
                }
                result.append(ret1)
        return result

    # 查看站点是否开启SSL
    # 取SSL状态
    def GetSSL(self, siteName):
        path = '/etc/letsencrypt/live/' + siteName;
        type = 0
        if os.path.exists(path + '/README'):  type = 1;
        if os.path.exists(path + '/partnerOrderId'):  type = 2;
        csrpath = path + "/fullchain.pem";  # 生成证书路径
        keypath = path + "/privkey.pem";  # 密钥文件路径
        key = public.readFile(keypath);
        csr = public.readFile(csrpath);
        file = self.setupPath + '/panel/vhost/' + public.get_webserver() + '/' + siteName + '.conf'
        conf = public.readFile(file);
        keyText = 'SSLCertificateFile'
        if public.get_webserver() == 'nginx': keyText = 'ssl_certificate';
        status = True
        if (conf.find(keyText) == -1):
            status = False
            type = -1
        return status

    # 取SSL的 SSL 协议
    def get_ssl_tls(self, siteName):
        tls = []
        if os.path.exists('/www/server/panel/vhost/nginx/%s.conf' % siteName):
            ret = public.ReadFile('/www/server/panel/vhost/nginx/%s.conf' % siteName)
            valuse = re.findall('ssl_protocols\s+(.+)', ret)
            print(valuse)
            if 'TLSv1' in valuse[0]:
                tls.append('TLSv1')
            if 'TLSv1.1' in valuse[0]:
                tls.append('LSv1.1')
        return tls

    # 是否使用宝塔防火墙
    def get_btwaf(self):
        if os.path.exists('/www/server/btwaf'):
            return True
        else:
            return False

    # 站点安全
    def site_security(self):
        # 是否开启防御跨站的
        resutl = {}
        site_secr = []
        site_lists = public.M('sites').field('name,path').select()
        for i in site_lists:
            path = i['path'] + '/.user.ini'
            ssl = self.GetSSL(i['name'])
            tls = []
            if ssl:
                tls = self.get_ssl_tls(i['name'])

            if not os.path.exists(path):
                site = {}
                site['user_ini'] = False
                site['name'] = '%s该站点未启用SSL' % i['name']

                site['ssl'] = ssl
                site['tls'] = tls
                if not ssl:
                    site['harm'] = "低",
                    site['ps'] = '%s该站点未启用SSL' % i['name']
                else:
                    if tls:
                        site['harm'] = "中",
                        site['ps'] = '%s该站点启用了不安全的SSL协议LSv1 或者LSv1.1' % i['name']
                site_secr.append(site)
            else:
                site = {}
                site['user_ini'] = True
                site['name'] = '%s该站点未启用SSL' % i['name']
                site['ssl'] = ssl
                site['tls'] = tls
                if not ssl:
                    site['harm'] = "低",
                    site['ps'] = '%s该站点未启用SSL' % i['name']
                else:
                    if tls:
                        site['harm'] = "中",
                        site['ps'] = '%s该站点启用了不安全的SSL协议LSv1 或者LSv1.1' % i['name']
                site_secr.append(site)
        resutl['site_list'] = site_secr
        resutl['btwaf'] = self.get_btwaf()
        return resutl

    # 主判断函数
    def check_san_baseline(self, base_json):
        if base_json['type'] == 'file':
            if os.path.exists(base_json['file']):
                ret = public.ReadFile(base_json['file'])
                for i in base_json['rule']:
                    valuse = re.findall(i['re'], ret)
                    print(valuse)
                    if i['check']['type'] == 'number':
                        if not valuse: return False
                        if not valuse[0]: return False
                        valuse = int(valuse[0])

                        if valuse > i['check']['min'] and valuse < i['check']['max']:
                            return True
                        else:
                            return False
                    elif i['check']['type'] == 'string':

                        if not valuse: return False
                        if not valuse[0]: return False
                        valuse = valuse[0]
                        print(valuse)
                        if valuse in i['check']['value']:
                            return True
                        else:
                            return False
            return True

        elif base_json['type'] == 'diff':
            if os.path.exists(base_json['file']):
                ret = public.ReadFile(base_json['file'])
                for i in base_json['rule']:
                    valuse = re.findall(i['re'], ret)
                    if i['check']['type'] == 'string':
                        if valuse[0] in i['check']['value']:
                            return True
                        else:
                            return False
            else:
                return True

        elif base_json['type'] == 'password':
            if os.path.exists(base_json['file']):
                ret = public.ReadFile(base_json['file'])
                for i in base_json['rule']:
                    valuse = re.findall(i['re'], ret)
                    print(valuse)
                    if not valuse: return False
                    if not valuse[0]: return False
                    if not i['check']['value']: return True
                    if i['check']['value']:
                        if valuse[0] in i['check']['value']:
                            return False
                        else:
                            return True
            else:
                return True

        elif base_json['type'] == 'dir':
            if os.path.exists(base_json['file']):
                return False
            else:
                return True


        elif base_json['type'] == 'shell':
            ret = public.ExecShell(base_json['cmd'])
            if not ret: return True
            if not ret[0]: return True
            if re.search(base_json['find']['re'], ret[0]):
                return False
            else:
                return True

        elif base_json['type'] == 'chmod':
            if os.path.exists(base_json['file']):
                ret = self.GetFileAccess(base_json['file'])
                if ret['chown'] in base_json['user'] and int(ret['chmod']) in base_json['chmod'] and ret['group'] in \
                        base_json['group']:
                    return True
                else:
                    return False
            else:
                return True

    # 获取文件/目录 权限信息
    def GetFileAccess(self, filename):
        if sys.version_info[0] == 2: filename = filename.encode('utf-8');
        data = {}
        try:
            import pwd
            stat = os.stat(filename)
            data['chmod'] = str(oct(stat.st_mode)[-3:])
            data['chown'] = pwd.getpwuid(stat.st_uid).pw_name
            data['group'] = pwd.getpwuid(stat.st_gid).pw_name
        except:
            data['chmod'] = 755
            data['chown'] = 'www'
            data['group'] = 'www'
        return data

    ####################################网站连通性##############################

    # 网站连通性
    def site_curl_security(self):
        result = []
        site_list = public.M('sites').field('name').select()
        if len(site_list) >= 1:
            for i in site_list:
                site = i['name']
                print(site)
                try:
                    ret = requests.get('http://127.0.0.1', timeout=3, headers={"host": site}, verify=False)
                    if ret.status_code != 200:
                        ret_status = {
                            "type": "site",
                            "name": "%s站点通过本机访问失败" % i['nane'],
                            "harm": "高",
                            "file": "%s站点通过本机访问失败" % i['name'],
                            "Suggestions": "加固建议, 检查是否是绑定了当前服务器的IP",
                            "repair": "检查是否是绑定了当前服务器的IP"
                        }
                        result.append(ret_status)
                except:
                    continue
        return result

    ################################## Nginx/APACHE 安全################################
    # Nginx/Apache 配置安全
    def Nginx_Apache_security(self):
        ret = []
        Nginx_Get_version = {
            "type": "file",
            "name": "Nginx 版本泄露",
            "harm": "高",
            "file": '/www/server/nginx/conf/nginx.conf',
            "Suggestions": "加固建议, 在%s expose_php的值修改为Off中修改" % ('/www/server/php/56/etc/php.ini'),
            "repair": "expose_php = Off",
            "rule": [
                {"re": "server_tokens\s*(.+)", "check": {"type": "string", "value": ['off;']}}]
        }
        if not self.check_san_baseline(Nginx_Get_version):
            ret.append(Nginx_Get_version)
        if os.path.exists('/www/server/nginx/version.pl'):
            ret2 = public.ReadFile('/www/server/nginx/version.pl')
            if ret2 == '1.8':
                Nginx_Get_version = {
                    "type": "file",
                    "name": "Nginx 版本过低",
                    "harm": "高",
                    "file": '/www/server/nginx/conf/nginx.conf',
                    "Suggestions": "加固建议, 升级至最新版的Nginx 软件",
                    "repair": "例如：Nignx1.17 或者Nginx1.16",
                }
                ret.append(Nginx_Get_version)

        return ret

    ####################################      system 关键文件版本 ######################
    # system 关键文件版本
    def system_version_security(self):
        ret = []
        return ret

    # 查询日志(查看进度)
    def get_api_log(self, get):

        if not os.path.exists(self.logPath): public.returnMsg(False, "无日志")
        ret = json.loads(public.readFile(self.logPath))
        if int(len(ret)) == 0:
            return public.returnMsg(False, "无日志")
        return public.returnMsg(True, ret)
        # 写输出日志

    def WriteLogs(self, logMsg):
        fp = open(self.logPath, 'w+')
        fp.write(logMsg)
        fp.close()

    # 查询日志(查看进度)
    def get_resut(self, get):
        time.sleep(0.5)
        if not os.path.exists(self.config): public.returnMsg(False, "无日志")
        ret = json.loads(public.readFile(self.config))
        if int(len(ret)) == 0:
            return public.returnMsg(False, "无日志")
        return public.returnMsg(True, ret)
        # 写输出日志

    def Write_result(self, logMsg):
        fp = open(self.config, 'w+')
        fp.write(logMsg)
        fp.close()

    def Write(self, name, count):
        Speed = {}
        Speed['name'] = '正在进行检测%s' % name
        Speed['total'] = 0
        Speed['Current_file'] = None  # 当前发送的文件
        Speed['progress'] = "%.2f" % (float(count) / float(13) * 100)
        Speed['ok'] = False
        self._Speed = Speed
        self.WriteLogs(json.dumps(Speed))

    #########################################################################
    # 统计入口
    def San_Entrance(self):
        if os.path.exists(self.logPath): os.remove(self.logPath)
        SSH = self.ssh_security()
        self.Write(name='ssh安全监测', count=1)

        time.sleep(1)
        PANEL = self.panel_security()
        self.Write(name='面板安全监测', count=2)
        time.sleep(1)
        PHP = self.php_security()
        self.Write(name='PHP安全监测', count=3)
        time.sleep(1)
        NINGX = self.Nginx_Apache_security()
        self.Write(name='Nginx/Apache安全监测', count=4)
        time.sleep(1)
        redis = self.redis_security()
        self.Write(name='redis安全监测', count=5)
        time.sleep(1)
        memcache = self.memcache_security()
        self.Write(name='memcache安全监测', count=6)

        mysql = self.mysql_security()
        self.Write(name='Mysql安全监测', count=7)
        time.sleep(1)
        system_user = self.user_security()
        self.Write(name='系统用户安全监测', count=8)
        time.sleep(1)
        task = self.tasks_security()
        self.Write(name='系统计划任务安全监测', count=9)
        time.sleep(1)
        site_curl = self.site_curl_security()
        self.Write(name='网站连接监测', count=10)
        time.sleep(1)
        system_dir = self.system_dir_security()
        self.Write(name='系统关键目录安全监测', count=11)
        time.sleep(1)
        site_sec = self.site_security()
        self.Write(name='网站安全监测', count=12)
        time.sleep(1)
        system_file = self.system_version_security()
        self.Write(name='系统关键性文件监控', count=13)

        if not self._Speed == None:
            self._Speed['ok'] = True
            self._Speed['name'] = '所有扫描完毕'
            self.WriteLogs(json.dumps(self._Speed))

        aa = {
            "SSH": SSH,
            "PANEL": PANEL,
            "PHP": PHP,
            "NINGX/APCHE": NINGX,
            "redis": redis,
            "memcache": memcache,
            "mysql": mysql,
            "system_user": system_user,
            "task": task,
            "site_curl": site_curl,
            "system_dir": system_dir,
            "site_sec": site_sec,
            "system_file": system_file,
        }

        self.Write_result(json.dumps(aa))
        return aa

    def start(self, get):
        os.system('python /www/server/panel/class/san_baseline.py &')
        return public.returnMsg(True, '1')

    # 取爆破
    def get_ssh_errorlogin(self, get):
        path = '/var/log/secure'
        if not os.path.exists(path): public.writeFile(path, '');
        fp = open(path, 'r');
        l = fp.readline();
        data = {};
        data['intrusion'] = [];
        data['intrusion_total'] = 0;

        data['defense'] = [];
        data['defense_total'] = 0;

        data['success'] = [];
        data['success_total'] = 0;

        limit = 100;
        while l:
            if l.find('Failed password for root') != -1:
                if len(data['intrusion']) > limit: del (data['intrusion'][0]);
                #data['intrusion'].append(l);
                data['intrusion_total'] += 1;
            elif l.find('Accepted') != -1:
                if len(data['success']) > limit: del (data['success'][0]);
                data['success'].append(l);
                data['success_total'] += 1;
            # elif l.find('refused') != -1:
            #     if len(data['defense']) > limit: del (data['defense'][0]);
            #     data['defense'].append(l);
            #     data['defense_total'] += 1;
            l = fp.readline();

        months = {'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04', 'May': '05', 'Jun': '06', 'Jul': '07', 'Aug': '08', 'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12'}

        success = [];
        for g in data['success']:
            tmp = {}
            tmp1 = g.split();
            tmp['date'] = months[tmp1[0]] + '/' + tmp1[1] + ' ' + tmp1[2];
            tmp['user'] = tmp1[8];
            tmp['address'] = tmp1[10];
            success.append(tmp);
        data['success'] = success;

        return data;


if __name__ == '__main__':
    my_api = san_baseline()
    r_data = my_api.San_Entrance()