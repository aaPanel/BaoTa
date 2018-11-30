# coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2019 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: 戴艺森 <623815825@qq.com>
# +-------------------------------------------------------------------
import sys
import os
import json
import base64
import ast
import time
sys.path.append("class/")
import public
import db
if sys.version_info[0] != 2:
    import pymysql
    pymysql.install_as_MySQLdb()
import MySQLdb
import panelMysql


class mysql_conn():
    def __init__(self, user, passwd, port, db, socket='/tmp/mysql.sock'):
        self.conn = MySQLdb.connect(
            host='localhost',
            port=port,
            user=user,
            db=db,
            passwd=passwd,
            charset="utf8",
            unix_socket=socket,
            connect_timeout=1
        )
        self.cur = self.conn.cursor()

    def query(self, sql, params):
        self.cur.execute(sql, params)
        return self

    def execute(self, sql):
        return self.cur.execute(sql)

    def findall(self):
        results = self.cur.fetchall()
        return results

    def find(self):
        results = self.cur.fetchone()
        return results

    def commit(self):
        self.conn.commit()

    def close(self):
        self.conn.close()


class master():

    def delSlaveByMaster(self, get):
        # 删除从服务器
        if 'ip' in get.keys() and get['ip'] in self.data['slave']:
            slave_info = self.data['slave'][get['ip']]
            slave_panel_addr = slave_info['slave_panel_addr']
            my_panel_addr = public.getPanelAddr()
            post_data = {
                "passwd": slave_info['passwd'],
                "panel_addr": my_panel_addr
            }
            del self.data['slave'][get['ip']]
            self._curlServer(post_data, slave_panel_addr, 'delSlaveBySlave')
        else:
            del self.data['slave'][get['client_ip']]
        self._updateFile('data.json', self.data)
        return public.returnMsg(True, '删除成功')

    def __getAllUserId(self):
        slave_id_arr = []
        for name in self.data['slave']:
            if self.data['slave'][name]['slave_id']:
                slave_id_arr.append(self.data['slave'][name]['slave_id'])
        all_user_id = slave_id_arr + [self.my_id]
        return all_user_id

    def __encodeKey(self, server_id, uesr, passwd, all_user_id, master_ip, panel_addr, db, master_id, mysql_version):
        data = json.dumps({'A': server_id, 'B': uesr, 'C': passwd, 'D': all_user_id,
                           'E': master_ip, 'F': panel_addr, 'G': db, 'H': master_id, 'I': mysql_version})
        return base64.b64encode(data)

    def downSqlFile(self, get):
        # 用于主服务器
        data = public.readFile(self.masterslave_path+"token.pl")
        if get['passwd'] == data.split(':')[-1].replace('\n', ''):
            filename = "%smaster_sql_file.sql.gz" % self.masterslave_path
            return filename

    def addSlaveByMaster(self, get):
        '''
        开启权限 允许从服务器连接
        get = {
            'db':'*',
            'master_ip':'192.168.1.242',
        }
        '''
        self._mysql.execute('unlock tables;')
        passwd = public.GetRandomString(32)
        data = "%s:%s:%s" % (get['master_ip'], get['db'], passwd)
        public.ExecShell("echo '%s' > %stoken.pl" %
                         (data, self.masterslave_path))
        '''
        秘钥包含：server_id, uesr, passwd, all_user_id, master_ip, panel_addr, db
        '''
        all_user_id = self.__getAllUserId()
        my_panel_addr = public.getPanelAddr()
        secret_key = self.__encodeKey(self.my_id, self.user_name, passwd, all_user_id, get['master_ip'],
                                      my_panel_addr, get['db'], self.my_id, self.my_version)
        print(secret_key)
        return public.returnMsg(True, secret_key)

    def createAccountByMaster(self, get):
        '''
        from:   setSlave(self, get)
        to:     createAccountBySlave(self, get)
        添加用户
        锁表
        导出数据库
        '''
        # change master
        print('主服务器：  添加账户并锁表')
        create_sql = "grant replication slave on *.* to '%s'@'%s' identified by '%s';" \
            % (self.user_name, get['slave_ip'], get['passwd'])

        # self._set_master_binlog_db(get['db'])
        self._mysql.execute(create_sql)
        flush_sql = "flush privileges;"
        self._mysql.execute(flush_sql)
        lock_sql = "flush tables with read lock;"
        self._mysql.execute(lock_sql)

        master_info = self._mysql.query("show master status;", []).find()
        log_file = master_info[0]
        log_pos = master_info[1]
        print("导出主数据库", get['db'])
        sql_name = 'master_sql_file.sql.gz'
        get['file_name'] = sql_name

        falg = self._dumpMysql(get)

        # 请求从服务器  --> createAccountBySlave
        my_panel_addr = public.getPanelAddr()
        post_data = {
            "slave_ip": get['slave_ip'],
            "passwd": get['passwd'],
            "panel_addr": my_panel_addr,
            "log_file": log_file,
            "log_pos": log_pos,
            "master_ip": get['master_ip'],
            "master_id": get['master_id'],
            'db': get['db']
        }
        self.data['slave'][get['slave_ip']] = {
            "status": True,
            "slave_panel_addr": get['panel_addr'],
            "passwd": get['passwd'],
            'db': get['db'],
            'slave_id': get['slave_id']
        }
        # if False and os.path.getsize(self.masterslave_path+sql_name) < 1024*1024*100:
        if falg:
            # 将从服务器信息 写入 data.json文件
            self._updateFile('data.json', self.data)
            data = self._curlServer(
                post_data, get['panel_addr'], 'createAccountBySlave')
            print('2---> createAccountBySlave', data[1:-1])
            return data[1:-1], ''
        else:
            '''
            # 文件过大 返回下载链接
            # 将从服务器信息 写入 data.json文件
            self.data['slave'][get['slave_ip']]['status'] = False
            self._updateFile('data.json', self.data)
            return '%s/yield?action=a&name=masterslave&fun=downSqlFile&passwd=%s&master_ip=%s'\
                % (my_panel_addr, get['passwd'], get['master_ip']), post_data
            '''
            # 解锁
            post_data['status'] = '404'
            self.unlockTables(post_data)
            return '404'

    def unlockTables(self, get):
        '''
        主服务器 解锁
        from: createAccountBySlave(self, get)
        '''
        print('主服务器 解锁')
        self._mysql.execute("unlock tables;")
        # print('rm -f %smaster_sql_file*' % self.masterslave_path
        public.ExecShell('rm -f %smaster_sql_file*' % self.masterslave_path)
        print(get['status'] == "200")
        if get['status'] == "200":
            self.data['slave'][get['slave_ip']]['status'] = True
        self._updateFile('data.json', self.data)
        return True

    # def _set_master_binlog_db(self, db):
    #     # 主从复制指定数据库
    #     is_update = False
    #     if db != '*':
    #         with open(self.mysql_conf_file, "r") as conf:
    #             for n, row in enumerate(conf):
    #                 if row.find("binlog-do-db") != -1:
    #                     if row.find(db) != -1:
    #                         return True
    #                     num = n
    #                     break
    #                 if row.find('[mysqldump]') != -1:
    #                     num = n - 1
    #                     break
    #             sed_cmd = "sed -i '%da%s' %s" % (num, 'binlog-do-db = %s' %
    #                                              db, self.mysql_conf_file)
    #             is_update = True
    #             public.ExecShell(sed_cmd)
    #     else:
    #         # 删除配置文件指定的数据库
    #         with open(self.mysql_conf_file, "r") as conf:
    #             for n, row in enumerate(conf):
    #                 if row.find("binlog-do-db") != -1:
    #                     is_update = True
    #                     sed_cmd = "sed -i '%sd' %s" % (n+1,
    #                                                    self.mysql_conf_file)
    #                     public.ExecShell(sed_cmd)
    #     if is_update:
    #         os.system('/etc/init.d/mysqld reload')
    #     return True

    def _set_salve_replicate_db(self, dbs):
        # 主从复制指定从数据库 需要复制的数据库
        is_update = False
        if dbs != '*':
            for db in dbs.split(','):
                with open(self.mysql_conf_file, "r") as conf:
                    for n, row in enumerate(conf):
                        if row.find("replicate-do-db") != -1:
                            if row.find(db) != -1:
                                return True
                            num = n
                            break
                        if row.find('[mysqldump]') != -1:
                            num = n - 1
                            break
                    sed_cmd = "sed -i '%da%s' %s" % (num, 'replicate-do-db = %s' %
                                                     db, self.mysql_conf_file)
                    is_update = True
                    public.ExecShell(sed_cmd)
        else:
            # 删除配置文件指定的数据库
            with open(self.mysql_conf_file, "r") as conf:
                for n, row in enumerate(conf):
                    if row.find("replicate-do-db") != -1:
                        is_update = True
                        sed_cmd = "sed -i '%sd' %s" % (n+1,
                                                       self.mysql_conf_file)
                        public.ExecShell(sed_cmd)
        if is_update:
            os.system('/etc/init.d/mysqld reload')
        return True


class slave():

    def delSlaveBySlave(self, get):
        self._mysql.execute("stop slave;")
        self._mysql.execute("change master to master_host=' ';")
        self._mysql.execute("reset slave;")
        if 'ip' in get.keys():
            master_info = self.data['master'][get['ip']]
            master_panel_addr = master_info['master_panel_addr']
            my_panel_addr = public.getPanelAddr()
            post_data = {
                "passwd": master_info['passwd'],
                "panel_addr": my_panel_addr
            }
            del self.data['master'][get['ip']]
            self._curlServer(post_data, master_panel_addr, 'delSlaveByMaster')
        else:
            del self.data['master'][get['client_ip']]
        self._updateFile('data.json', self.data)
        return public.returnMsg(True, '删除成功')

    def __setServerId(self, server_id):
        with open(self.mysql_conf_file, "r") as conf:
            for n, row in enumerate(conf):
                if row.find("server-id") != -1:
                    print('正在修改 serverid')
                    self.__sedCmd(n+1, "server-id",
                                  "server-id = %s" % server_id)
                    break
        time.sleep(1)
        print('正在重启mysql服务器')
        os.system('/etc/init.d/mysqld restart')
        print('重启成功', self._mysql)
        time.sleep(1)

    def __sedCmd(self, n, old, new):
        sed_cmd = "sed -i '%ds/[ #]*%s.*/%s/' %s" % (
            n, old, new, self.mysql_conf_file)
        public.ExecShell(sed_cmd)
        if not public.ExecShell("cat /etc/my.cnf|grep 'slave-skip-errors'|awk '{print $3}'")[0]:
            sed_cmd = "sed -i '%da%s' %s" % (
                n, 'slave-skip-errors = 1062,1032,1060', self.mysql_conf_file)
            public.ExecShell(sed_cmd)

    def uploadSqlFile(self, get):
        # 用于从服务器
        # with open(self.masterslave_path+'master_sql_file.sql', 'wb') as f:
        with open(self.masterslave_path+'master_sql_file.sql', "w") as code:
            code.write(get['file'])

    def _importMysql(self, db):
        # 覆盖导入
        file_path = self.masterslave_path + 'master_sql_file.sql'
        public.ExecShell('gunzip %s.gz' % file_path)
        sql = "mysql -uroot -p%s < %s " % (self.passwd, file_path)
        print('正在导入', sql)
        public.WriteLog('主从复制', '已导入主服务器的数据库')
        return public.ExecShell(sql)

    def setSlave(self, get):
        '''
        # 将该服务器设置为 从服务器
        to:     createAccountByMaster(self, get)
        '''
        try:
            data = json.loads(base64.b64decode(get['secret_key']))
            server_id = data['A']
            user = data['B']
            passwd = data['C']
            all_user_id = data['D']
            master_ip = data['E']
            master_panel_addr = data['F']
            db = data['G']
            master_id = data['H']
            master_version = data['I']
        except:
            return public.returnMsg(403, '秘钥不正确')

        if master_version != self.my_version:
            return public.returnMsg(403, '数据库版本不一致')

        if master_ip in self.data['master'].keys():
            return public.returnMsg(403, '该主数据库已存在，请不要重复添加')

        if master_ip in self.data['master']:
            return public.returnMsg(403, '已存在主服务器, 不支持做多主复制')

        # if self.data['master'] and self.my_id in all_user_id:
        #     # 该服务器同时也为 主服务器
        #     return public.returnMsg(403, '目标服务存在主服务器，server-id冲突，请手动处理')

        if self.data['slave'] and self.my_id in all_user_id:
            # 该服务器同时也为 主服务器
            return public.returnMsg(403, '目标服务存在从服务器，server-id冲突，请手动处理')

        if not master_ip in self.data['slave'].keys():
            print('正在计算 severid', self.my_id in all_user_id, self.my_id)
            # 该服务器的server_id 存在 主服务器已分配的id中 则修改该服务器id
            if self.my_id in all_user_id:
                # 计算新的 slave_id
                user_count = len(all_user_id)
                for i in xrange(1, user_count+2):
                    if str(i) not in all_user_id:
                        slave_id = i
                        break
                print('修改 服务器id', slave_id)
                self.__setServerId(slave_id)

                # 并且该服务器 同时也是主服务器  ——————>  这里暂时不设置
            else:
                # 不需修改 服务器id, 添加slave-skip-errors
                slave_id = self.my_id
                if not public.ExecShell("cat /etc/my.cnf|grep 'slave-skip-errors'|awk '{print $3}'")[0]:
                    self.__setServerId(self.my_id)

            print('计算成功', self.my_id)

        else:
            # 不需要重新导入数据库，主主复制
            public.ExecShell('echo 1 > %sis_import' % self.masterslave_path)
            print('主主复制')
            # 不需修改 服务器id, 添加slave-skip-errors
            slave_id = self.my_id
            if not public.ExecShell("cat /etc/my.cnf|grep 'slave-skip-errors'|awk '{print $3}'")[0]:
                self.__setServerId(self.my_id)

        data = "%s:%s:%s" % (master_ip, db, passwd)
        public.ExecShell("echo '%s' > %stoken.pl" %
                         (data, self.masterslave_path))
        my_panel_addr = public.getPanelAddr()
        # 请求主服务器 --> createAccountByMaster
        post_data = {
            "slave_ip": get['slave_ip'],
            "passwd": passwd,
            "slave_id": slave_id,
            "db": db,
            "panel_addr": my_panel_addr,
            "master_ip": master_ip,
            "master_id": master_id
        }
        print('1---> createAccountByMaster')
        msg = self._curlServer(
            post_data, master_panel_addr, 'createAccountByMaster')
        print('msg-----------', msg)
        try:
            msg = ast.literal_eval(msg)
        except: return {'status': 401, 'msg': '服务器无法连接目标面板地址:' + master_panel_addr}
        print('msg-----------', msg[0])
        if msg[0] == '200':
            return public.returnMsg(200, '成功添加')
        # return public.returnMsg(False, msg)
        elif msg[0] == '401':
            return public.returnMsg(401, '添加失败')
        else:
            return {'status': 404, 'msg': '数据文件过大，请先做主从复制，再导入数据库!'}
            # return {'status': 404, 'msg': '数据文件过大，请手动下载到从服务器导入', 'url': msg[0], 'post_data': msg[1]}

    def createAccountBySlave(self, get):
        # 添加用户
        '''
        from:   createAccountByMaster(self, get)
        to:     unlockTables(self, get)
        '''
        # print(self.data
        # 导入数据库
        # 请求数据库文件

        url = "%s/yield?action=a&name=masterslave&fun=downSqlFile&passwd=%s&master_ip=%s" % (
            get['panel_addr'], get['passwd'], get['master_ip'])
        public.ExecShell("wget '%s' -O %s" %
                         (url, self.masterslave_path+'master_sql_file.sql.gz'))

        # # 备份 从服务器数据库
        # get['file_name'] = 'salve_sql_file.sql.bak.gz'
        # self._dumpMysql(get)

        if not os.path.exists(self.masterslave_path+'is_import'):
            # 导入数据库
            _, ret = self._importMysql(get['db'])
            if ret and 'Using a password on' not in ret:
                # 导入出错
                print('导入出错', ret)
                public.ExecShell('rm -f %smaster_sql_file.sql' %
                                 self.masterslave_path)
                return '401'

        return self._startSlave(get)

    def _startSlave(self, get):
        status = '200'
        print('从服务器： stop slave; 添加用户 start slave')
        self._mysql.execute("stop slave;")
        create_sql = "change master to master_host='%s',master_user='%s',master_password='%s', master_log_file='%s',master_log_pos=%s;" \
            % (get['master_ip'], self.user_name, get['passwd'], get['log_file'], get['log_pos'])
        # print('slave 4: ', create_sql)
        self._mysql.execute(create_sql)

        self._mysql.execute("start slave;")
        time.sleep(0.5)
        slave_status = self._mysql.query("show slave status;", []).find()
        print(slave_status[10], slave_status[11])
        if slave_status[10] == 'Yes' and slave_status[11] == 'Yes':
            self._set_salve_replicate_db(get['db'])

            # 将从服务器信息 写入 data.json文件
            self.data['master'][get['master_ip']] = {
                "master_panel_addr": get['panel_addr'],
                "passwd": get['passwd'],
                'db': get['db'],
                'master_id': get['master_id']
            }
            self._updateFile('data.json', self.data)
        else:
            time.sleep(0.5)
            slave_status = self._mysql.query("show slave status;", []).find()
            if slave_status[10] == 'Yes' and slave_status[11] == 'Yes':
                self._set_salve_replicate_db(get['db'])
                # 将从服务器信息 写入 data.json文件
                self.data['master'][get['master_ip']] = {
                    "master_panel_addr": get['panel_addr'],
                    "passwd": get['passwd'],
                    'db': get['db'],
                    'master_id': get['master_id']
                }
                self._updateFile('data.json', self.data)
            else:
                status = '401'

        my_panel_addr = public.getPanelAddr()
        # 请求主服务器 --> unlockTables
        post_data = {
            "passwd": get['passwd'],
            "panel_addr": my_panel_addr,
            "master_ip": get['master_ip'],
            "status": status,
            'slave_ip': get['slave_ip']
        }
        print('3---> unlockTables')
        self._curlServer(post_data, get['panel_addr'], 'unlockTables')
        public.ExecShell('rm -f %smaster_sql_file*' % self.masterslave_path)
        return status

    def uploadFile(self, get):
        import ast
        # public.ExecShell('rm -f %smaster_sql_file*' % self.masterslave_path)
        # public.writeFile(self.masterslave_path +
        #                  'master_sql_file.sql.gz', get['file'])
        # post_data = {
        #     "slave_ip": get['slave_ip'],
        #     "passwd": passwd,
        #     "slave_id": slave_id,
        #     "db": db,
        #     "panel_addr": my_panel_addr,
        #     "master_ip": master_ip,
        #     "master_id": master_id
        # }
        post_data = ast.literal_eval(get['post_data'])

        print(self._importMysql(post_data['db']))
        status = self._startSlave(post_data)
        print('_startSlave--------------------', status)
        if status == '200':
            return public.returnMsg(True, '导入成功')
        else:
            return public.returnMsg(False, '操作失败')

    def getStatus(self, get):
        # /public?action=a&name=masterslave&fun=getStatus
        slave_status = self._mysql.query("show slave status;", []).find()
        #web.header("Access-Control-Allow-Origin", "*")
        if slave_status:
            print(slave_status[10], slave_status[11])
            data = {
                'Slave_IO_Running': slave_status[10],
                'Slave_SQL_Running': slave_status[11]
            }
            return data


class masterslave_init(master, slave):
    user_name = 'btrsync'
    mysql_conf_file = '/etc/my.cnf'
    masterslave_path = '/www/server/panel/plugin/masterslave/'
    args_cmd = "cat %s|grep %s|awk '{print $3}'|xargs|awk '{print $1}'"
    port = public.ExecShell(args_cmd % (mysql_conf_file, 'port'))[
        0].replace('\n', '')
    my_id = public.ExecShell(args_cmd % (
        mysql_conf_file, 'server-id'))[0].replace('\n', '')
    unix_socket = public.ExecShell(args_cmd % (mysql_conf_file, 'socket'))[
        0].replace('\n', '')

    my_version = public.ExecShell(
        "mysql -V|awk '{print $5}'|sed 's/,//'")[0].replace('\n', '')
    passwd = public.M("config").field("mysql_root").find()['mysql_root']
    init_error_msg = None

    def __init__(self):
        try:
            self._mysql = mysql_conn('root', self.passwd, int(self.port), 'mysql', self.unix_socket)
            if not os.path.exists(self.masterslave_path+"data.json"):
                public.ExecShell('echo {\\"master\\": {}, \\"slave\\": {}} > ' + self.masterslave_path+"data.json")
            fbody = public.readFile(self.masterslave_path+"data.json")
            self.data = json.loads(fbody)
        except Exception as e:
            self.init_error_msg = e

    def getInfo(self, get):
        is_update = False
        my_panel_addr = public.getPanelAddr()
        public.ExecShell('rm -f %sis_import' % self.masterslave_path)
        if self.init_error_msg:
            return public.returnMsg(False, str(self.init_error_msg))
        data_list = []
        for ip in self.data['master']:
            data_list.append({
                'master_ip': ip,
                'slave_ip': '本机',
                'db': self.data['master'][ip]['db'],
                'master_panel_addr': self.data['master'][ip]['master_panel_addr'],
                'slave_panel_addr': my_panel_addr,
                'passwd': self.data['master'][ip]['passwd'],
            })
        for ip in self.data['slave']:
            if self.data['slave'][ip]['status']:
                data_list.append({
                    'master_ip': '本机',
                    'slave_ip': ip,
                    'db': self.data['slave'][ip]['db'],
                    'slave_panel_addr': self.data['slave'][ip]['slave_panel_addr'],
                    'master_panel_addr': my_panel_addr,
                    'passwd': self.data['slave'][ip]['passwd'],
                })
        db = ['*'] + self.getDataBaseList()
        self.check_port_accept(get);
        return public.returnMsg(True, {'data_list': data_list, 'db': db})
    
    #检查是否放行3306
    def check_port_accept(self,get):
        try:
            import firewalls
            get.port = '3306';
            get.ps = 'MySQL';
            firewalls.firewalls().AddAcceptPort(get);
        except:pass

    def getDataBaseList(self):
        database_list = []
        for database in self._mysql.query("show databases;", []).findall():
            if database[0] not in ['information_schema', 'mysql', 'performance_schema', 'sys']:
                database_list.append(database[0])
        return database_list

    def _check(self, get):
        if get['fun'] in ['getStatus']:
            return True
        if get['fun'] in ['delSlaveBySlave']:
            return self.data['master'][get['client_ip']]['passwd'] == get['passwd']
        if get['fun'] == 'delSlaveByMaster':
            return self.data['slave'][get['client_ip']]['passwd'] == get['passwd']

        data = public.readFile(self.masterslave_path+"token.pl").split(':')
        if get['passwd'] == data[-1].replace('\n', '') and get['master_ip'] == data[0]:
            return True
        else:
            print('验证失败')
            return False

    def reqPost(self, url, data):
        # 发布时 不使用该函数
        try:
            import urllib
            import urllib2
            import ssl
            context = ssl._create_unverified_context()
            data = urllib.urlencode(data)
            req = urllib2.Request(url, data)
            response = urllib2.urlopen(req, context=context, timeout=7200)
            return response.read()
        except Exception as ex:
            return str(ex)

    def _curlServer(self, post_data, panel_addr, fun):
        url = '%s/public?action=a&name=masterslave&fun=%s' % (panel_addr, fun)
        return public.httpPost(url, post_data).decode('unicode_escape')
        # return self.reqPost(url, post_data).decode('unicode_escape')

    def _dumpMysql(self, get):
        # 获取数据库大小
        information_schema_mysql = mysql_conn('root', self.passwd, int(
            self.port), 'information_schema', self.unix_socket)
        data_size_sql = "select concat(round(sum(data_length/1024/1024),2)) as data from tables"
        if get['db'] != '*':
            data_size_sql += " where "
            dbs = get['db'].split(',')
            dbs_len = len(dbs)
            for n, i in enumerate(dbs):
                data_size_sql += "table_schema='%s' " % i
                if dbs_len != n+1:
                    data_size_sql += 'or '

        data = information_schema_mysql.query(data_size_sql, []).find()
        print('数据库大小', data[0])
        if float(data[0]) > 100.0:
            return False

        # 导出数据库
        # print('导出数据库', get['db'], get['file_name']

        if get['db'] == '*':
            dbs = " ".join(self.getDataBaseList())
        else:
            dbs = get['db'].replace(',', ' ')
        mysql_dump_cmd = "mysqldump -uroot -p%s  --databases %s | gzip > %s%s" % (
            self.passwd, dbs, self.masterslave_path, get['file_name'])
        print(mysql_dump_cmd)
        public.WriteLog('主从复制', '导出' + get['db'] + '数据库')
        return public.ExecShell(mysql_dump_cmd)

    def _updateFile(self, file_name, data):
        # 更新 文件
        public.writeFile(self.masterslave_path+'data.json',
                         json.dumps(data, sort_keys=True))
        pass

    def get_ip(self, get):
        IP = public.GetLocalIp()
        if IP == '0.0.0.0':
            return ''
        return IP
