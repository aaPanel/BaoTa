#coding: utf-8
#-------------------------------------------------------------------
# 宝塔Linux面板
#-------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
#-------------------------------------------------------------------
# Author: hwliang <hwl@bt.cn>
#-------------------------------------------------------------------

#------------------------------
# 数据备份模块
#------------------------------
import os
import sys
import json
import re
import time

os.chdir('/www/server/panel')
if not 'class/' in sys.path:
    sys.path.insert(0,'class/')
import public
_VERSION = 1.5

class backup:
    _path = None
    _exclude = ""
    _err_log = '/tmp/backup_err.log'
    _inode_min = 10
    _db_mysql = None
    _cloud = None
    _is_save_local = os.path.exists('data/is_save_local_backup.pl')
    def __init__(self,cloud_object = None):
        '''
            @name 数据备份对象
            @param cloud_object 远程上传对象，需具备以下几个属性和方法：
                    _title = '中文名称,如：阿里云OSS'
                    _name = '英文名称,如：alioss'
                    upload_file(filename,data_type = None)
                        文件名 , 数据类型 site/database/path
                    
                    delete_file(filename,data_type = None)
                        文件名 , 数据类型 site/database/path
        '''
        self._cloud = cloud_object
        self._path = public.M('config').where("id=?",(1,)).getField('backup_path')

    def echo_start(self):
        print("="*90)
        print("★开始备份[{}]".format(public.format_date()))
        print("="*90)

    def echo_end(self):
        print("="*90)
        print("☆备份完成[{}]".format(public.format_date()))
        print("="*90)
        print("\n")

    def echo_info(self,msg):
        print("|-{}".format(msg))

    def echo_error(self,msg):
        print("=" * 90)
        print("|-错误：{}".format(msg))

    #构造排除
    def get_exclude(self,exclude = []):
        if not exclude:
            tmp_exclude = os.getenv('BT_EXCLUDE')
            if tmp_exclude:
                exclude = tmp_exclude.split(',')
        if not exclude: return ""
        for ex in exclude:
            self._exclude += " --exclude=\"" + ex + "\""
        self._exclude += " "
        return self._exclude

    def GetDiskInfo2(self):
        #取磁盘分区信息
        temp = public.ExecShell("df -T -P|grep '/'|grep -v tmpfs|grep -v 'snap/core'|grep -v udev")[0]
        tempInodes = public.ExecShell("df -i -P|grep '/'|grep -v tmpfs|grep -v 'snap/core'|grep -v udev")[0]
        temp1 = temp.split('\n')
        tempInodes1 = tempInodes.split('\n')
        diskInfo = []
        n = 0
        cuts = []
        for tmp in temp1:
            n += 1
            try:
                inodes = tempInodes1[n-1].split()
                disk = re.findall(r"^(.+)\s+([\w\.]+)\s+([\w\.]+)\s+([\w\.]+)\s+([\w\.]+)\s+([\d%]{2,4})\s+(/.{0,50})$",tmp.strip())
                if disk: disk = disk[0]
                if len(disk) < 6: continue
                if disk[2].find('M') != -1: continue
                if disk[2].find('K') != -1: continue
                if len(disk[6].split('/')) > 10: continue
                if disk[6] in cuts: continue
                if disk[6].find('docker') != -1: continue
                if disk[1].strip() in ['tmpfs']: continue
                arr = {}
                arr['filesystem'] = disk[0].strip()
                arr['type'] = disk[1].strip()
                arr['path'] = disk[6]
                tmp1 = [disk[2],disk[3],disk[4],disk[5]]
                arr['size'] = tmp1
                arr['inodes'] = [inodes[1],inodes[2],inodes[3],inodes[4]]
                diskInfo.append(arr)
            except:
                continue
        return diskInfo


    #取磁盘可用空间
    def get_disk_free(self,dfile):
        diskInfo = self.GetDiskInfo2()
        if not diskInfo: return '',0,0
        _root = None
        for d in diskInfo:
            if d['path'] == '/': 
                _root = d
                continue
            if re.match("^{}/.+".format(d['path']),dfile):
                return d['path'],float(d['size'][2]) * 1024,int(d['inodes'][2])
        if _root:
            return _root['path'],float(_root['size'][2]) * 1024,int(_root['inodes'][2])
        return '',0,0


    #备份指定目录 
    def backup_path(self,spath,dfile = None,exclude=[],save=3):
        self.echo_start()
        if not os.path.exists(spath):
            self.echo_error('指定目录{}不存在!'.format(spath))
            return False

        if spath[-1] == '/':
            spath = spath[:-1]
        
        dirname = os.path.basename(spath) 
        
        if not dfile:
            fname = 'path_{}_{}.tar.gz'.format(dirname,public.format_date("%Y%m%d_%H%M%S"))
            dfile = os.path.join(self._path,'path',fname)
        
        if not self.backup_path_to(spath,dfile,exclude):
            return False

        if self._cloud:
            self.echo_info("正在上传到{}，请稍候...".format(self._cloud._title))
            if self._cloud.upload_file(dfile,'path'):
                self.echo_info("已成功上传到{}".format(self._cloud._title))
            else:
                self.echo_error('错误：文件上传失败，跳过本次备份!')
                if os.path.exists(dfile):
                    os.remove(dfile)
                return False
            

        filename = dfile
        if self._cloud:
            filename = dfile + '|' + self._cloud._name + '|' + fname

        
        pdata = {
            'type': '2',
            'name': spath,
            'pid': 0,
            'filename': filename,
            'addtime': public.format_date(),
            'size': os.path.getsize(dfile)
        }
        public.M('backup').insert(pdata)

        if self._cloud:
            if not self._is_save_local:
                if os.path.exists(dfile):
                    os.remove(dfile)
                    self.echo_info("用户设置不保留本地备份，已删除{}".format(dfile))
        
        if not self._cloud:
            backups = public.M('backup').where("type=? and pid=? and name=? and filename NOT LIKE '%|%'",('2',0,spath)).field('id,name,filename').select()
        else:
            backups = public.M('backup').where("type=? and pid=? and name=? and filename LIKE '%{}%'".format(self._cloud._name),('2',0,spath)).field('id,name,filename').select()

                
        self.delete_old(backups,save,'path')
        self.echo_end()
        return dfile

    
    #清理过期备份文件
    def delete_old(self,backups,save,data_type = None):
        if type(backups) == str:
            self.echo_info('清理过期备份失败，错误：{} '.format(backups))
            return
        self.echo_info('保留最新的备份数：{} 份'.format(save))
        num = len(backups) - int(save)
        if  num > 0:
            self.echo_info('-' * 88)
            for backup in backups:
                #处理目录备份到远程的情况
                if backup['filename'].find('|') != -1:
                    tmp = backup['filename'].split('|')
                    backup['filename'] = tmp[0]
                    backup['name'] = tmp[-1]
                #尝试删除本地文件
                if os.path.exists(backup['filename']):
                    os.remove(backup['filename'])
                    self.echo_info(u"已从磁盘清理过期备份文件：" + backup['filename'])
                #尝试删除远程文件
                if self._cloud:
                    self._cloud.delete_file(backup['name'],data_type)
                    self.echo_info(u"已从{}清理过期备份文件：{}".format(self._cloud._title,backup['name']))

                #从数据库清理
                public.M('backup').where('id=?',(backup['id'],)).delete()
                num -= 1
                if num < 1: break

    #压缩目录
    def backup_path_to(self,spath,dfile,exclude = [],siteName = None):
        if not os.path.exists(spath):
            self.echo_error('指定目录{}不存在!'.format(spath))
            return False

        if spath[-1] == '/':
            spath = spath[:-1]

        dirname = os.path.basename(spath)
        dpath = os.path.dirname(dfile)
        if not os.path.exists(dpath):
            os.makedirs(dpath,384)
        
        p_size = public.get_path_size(spath)
        self.get_exclude(exclude)
        exclude_config = self._exclude
        if not self._exclude:
            exclude_config = "未设置"
        
        if siteName:
            self.echo_info('备份网站：{}'.format(siteName))
            self.echo_info('网站根目录：{}'.format(spath))
        else:
            self.echo_info('备份目录：{}'.format(spath))
        
        self.echo_info("目录大小：{}".format(public.to_size(p_size)))
        self.echo_info('排除设置：{}'.format(exclude_config))
        disk_path,disk_free,disk_inode = self.get_disk_free(dfile)
        self.echo_info("分区{}可用磁盘空间为：{}，可用Inode为：{}".format(disk_path,public.to_size(disk_free),disk_inode))
        if disk_path:
            if disk_free < p_size:
                self.echo_error("目标分区可用的磁盘空间小于{},无法完成备份，请增加磁盘容量，或在设置页面更改默认备份目录!".format(public.to_size(p_size)))
                return False

            if disk_inode < self._inode_min:
                self.echo_error("目标分区可用的Inode小于{},无法完成备份，请增加磁盘容量，或在设置页面更改默认备份目录!".format(self._inode_min))
                return False

        stime = time.time()
        self.echo_info("开始压缩文件：{}".format(public.format_date(times=stime)))
        if os.path.exists(dfile):
            os.remove(dfile)
        public.ExecShell("cd " + os.path.dirname(spath) + " && tar zcvf '" + dfile + "' " + self._exclude + " '" + dirname + "' 2>{err_log} 1> /dev/null".format(err_log = self._err_log))
        tar_size = os.path.getsize(dfile)
        if tar_size < 1:
            self.echo_error("数据压缩失败")
            self.echo_info(public.readFile(self._err_log))
            return False
        self.echo_info("文件压缩完成，耗时{:.2f}秒，压缩包大小：{}".format(time.time() - stime,public.to_size(tar_size)))
        if siteName:
            self.echo_info("网站已备份到：{}".format(dfile))
        else:
            self.echo_info("目录已备份到：{}".format(dfile))
        if os.path.exists(self._err_log):
            os.remove(self._err_log)
        return dfile

    #备份指定站点
    def backup_site(self,siteName,save = 3 ,exclude = []):
        self.echo_start()
        find = public.M('sites').where('name=?',(siteName,)).field('id,path').find()
        spath = find['path']
        pid = find['id']
        fname = 'web_{}_{}.tar.gz'.format(siteName,public.format_date("%Y%m%d_%H%M%S"))
        dfile = os.path.join(self._path,'site',fname)
        if not self.backup_path_to(spath,dfile,exclude,siteName=siteName):
            return False
        
        if self._cloud:
            self.echo_info("正在上传到{}，请稍候...".format(self._cloud._title))
            if self._cloud.upload_file(dfile,'site'):
                self.echo_info("已成功上传到{}".format(self._cloud._title))
            else:
                self.echo_error('错误：文件上传失败，跳过本次备份!')
                if os.path.exists(dfile):
                    os.remove(dfile)
                return False

        filename = dfile
        if self._cloud:
            filename = dfile + '|' + self._cloud._name + '|' + fname

        pdata = {
            'type': 0,
            'name': fname,
            'pid': pid,
            'filename': filename,
            'addtime': public.format_date(),
            'size': os.path.getsize(dfile)
        }
        public.M('backup').insert(pdata)
        if self._cloud:
            if not self._is_save_local:
                if os.path.exists(dfile):
                    os.remove(dfile)
                    self.echo_info("用户设置不保留本地备份，已删除{}".format(dfile))

        #清理多余备份
        if not self._cloud:
            backups = public.M('backup').where("type=? and pid=? and filename NOT LIKE '%|%'",('0',pid)).field('id,name,filename').select()
        else:
            backups = public.M('backup').where('type=? and pid=? and filename LIKE "%{}%"'.format(self._cloud._name),('0',pid)).field('id,name,filename').select()

        self.delete_old(backups,save,'site')
        self.echo_end()
        return dfile
            

    #备份所有站点
    def backup_site_all(self,save = 3):
        sites = public.M('sites').field('name').select()
        for site in sites:
            self.backup_site(site['name'],save)

    #配置
    def mypass(self,act):
        conf_file = '/etc/my.cnf'
        conf_file_bak = '/etc/my.cnf.bak'
        if os.path.getsize(conf_file) > 2:
            public.writeFile(conf_file_bak,public.readFile(conf_file))
            public.set_mode(conf_file_bak,600)
            public.set_own(conf_file_bak,'mysql')
        elif os.path.getsize(conf_file_bak) > 2:
            public.writeFile(conf_file,public.readFile(conf_file_bak))
            public.set_mode(conf_file,600)
            public.set_own(conf_file,'mysql')
        
        public.ExecShell("sed -i '/user=root/d' {}".format(conf_file))
        public.ExecShell("sed -i '/password=/d' {}".format(conf_file))
        if act:
            password = public.M('config').where('id=?',(1,)).getField('mysql_root')
            mycnf = public.readFile(conf_file)
            if not mycnf: return False
            src_dump_re = r"\[mysqldump\][^.]"
            sub_dump = "[mysqldump]\nuser=root\npassword=\"{}\"\n".format(password)
            mycnf = re.sub(src_dump_re, sub_dump, mycnf)
            if len(mycnf) > 100: public.writeFile(conf_file,mycnf)
            return True
        return True

    #map to list
    def map_to_list(self,map_obj):
        try:
            if type(map_obj) != list and type(map_obj) != str: map_obj = list(map_obj)
            return map_obj
        except: return []

    #备份指定数据库
    def backup_database(self,db_name,dfile = None,save=3):
        self.echo_start()
        if not dfile:
            fname = 'db_{}_{}.sql.gz'.format(db_name,public.format_date("%Y%m%d_%H%M%S"))
            dfile = os.path.join(self._path,'database',fname)
        else:
            fname = os.path.basename(dfile)
        
        dpath = os.path.dirname(dfile)
        if not os.path.exists(dpath):
            os.makedirs(dpath,384)

        import panelMysql
        if not self._db_mysql:self._db_mysql = panelMysql.panelMysql()
        d_tmp = self._db_mysql.query("select sum(DATA_LENGTH)+sum(INDEX_LENGTH) from information_schema.tables where table_schema='%s'" % db_name)
        p_size = self.map_to_list(d_tmp)[0][0]
        
        if p_size == None:
            self.echo_error('指定数据库 `{}` 没有任何数据!'.format(db_name))
            return

        character = public.get_database_character(db_name)

        self.echo_info('备份数据库：{}'.format(db_name))
        self.echo_info("数据库大小：{}".format(public.to_size(p_size)))
        self.echo_info("数据库字符集：{}".format(character))
        disk_path,disk_free,disk_inode = self.get_disk_free(dfile)
        self.echo_info("分区{}可用磁盘空间为：{}，可用Inode为：{}".format(disk_path,public.to_size(disk_free),disk_inode))
        if disk_path:
            if disk_free < p_size:
                self.echo_error("目标分区可用的磁盘空间小于{},无法完成备份，请增加磁盘容量，或在设置页面更改默认备份目录!".format(public.to_size(p_size)))
                return False

            if disk_inode < self._inode_min:
                self.echo_error("目标分区可用的Inode小于{},无法完成备份，请增加磁盘容量，或在设置页面更改默认备份目录!".format(self._inode_min))
                return False
        
        stime = time.time()
        self.echo_info("开始导出数据库：{}".format(public.format_date(times=stime)))
        if os.path.exists(dfile):
            os.remove(dfile)
        #self.mypass(True)
        try:
            password = public.M('config').where('id=?',(1,)).getField('mysql_root')
            os.environ["MYSQL_PWD"] = password
            backup_cmd = "/www/server/mysql/bin/mysqldump --default-character-set="+ character +" --force --hex-blob --opt " + db_name + " -u root" + " 2>"+self._err_log+"| gzip > " + dfile
            public.ExecShell(backup_cmd)
        except Exception as e:
            raise
        finally:
            os.environ["MYSQL_PWD"] = ""
        #public.ExecShell("/www/server/mysql/bin/mysqldump --default-character-set="+ character +" --force --hex-blob --opt " + db_name + " 2>"+self._err_log+"| gzip > " + dfile)
        #self.mypass(False)
        gz_size = os.path.getsize(dfile)
        if gz_size < 400:
            self.echo_error("数据库导出失败!")
            self.echo_info(public.readFile(self._err_log))
            return False
        self.echo_info("数据库备份完成，耗时{:.2f}秒，压缩包大小：{}".format(time.time() - stime,public.to_size(gz_size)))

        if self._cloud:
            self.echo_info("正在上传到{}，请稍候...".format(self._cloud._title))
            if self._cloud.upload_file(dfile,'database'):
                self.echo_info("已成功上传到{}".format(self._cloud._title))
            else:
                self.echo_error('错误：文件上传失败，跳过本次备份!')
                if os.path.exists(dfile):
                    os.remove(dfile)
                return False

        filename = dfile
        if self._cloud:
            filename = dfile + '|' + self._cloud._name + '|' + fname

        self.echo_info("数据库已备份到：{}".format(dfile))
        if os.path.exists(self._err_log):
            os.remove(self._err_log)

        pid = public.M('databases').where('name=?',(db_name)).getField('id')
        
        pdata = {
            'type': '1',
            'name': fname,
            'pid': pid,
            'filename': filename,
            'addtime': public.format_date(),
            'size': os.path.getsize(dfile)
        }
        public.M('backup').insert(pdata)


        if self._cloud:
            if not self._is_save_local:
                if os.path.exists(dfile):
                    os.remove(dfile)
                    self.echo_info("用户设置不保留本地备份，已删除{}".format(dfile))

        #清理多余备份
        if not self._cloud:
            backups = public.M('backup').where("type=? and pid=? and filename NOT LIKE '%|%'",('1',pid)).field('id,name,filename').select()
        else:
            backups = public.M('backup').where('type=? and pid=? and filename LIKE "%{}%"'.format(self._cloud._name),('1',pid)).field('id,name,filename').select()

        
        self.delete_old(backups,save,'database')
        self.echo_end()
        return dfile
        

    #备份所有数据库
    def backup_database_all(self,save = 3):
        databases = public.M('databases').field('name').select()
        for database in databases:
            self.backup_database(database['name'],save=save)

    
