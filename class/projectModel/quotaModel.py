#coding: utf-8
#-------------------------------------------------------------------
# 宝塔Linux面板
#-------------------------------------------------------------------
# Copyright (c) 2015-2017 宝塔软件(http:#bt.cn) All rights reserved.
#-------------------------------------------------------------------
# Author: hwliang <hwl@bt.cn>
#-------------------------------------------------------------------

#------------------------------
# 磁盘配额管理
#------------------------------
import os,public,psutil,json,time
from projectModel.base import projectBase

class main(projectBase):
    __config_path = '{}/config/quota.json'.format(public.get_panel_path())
    __mysql_config_file = '{}/config/mysql_quota.json'.format(public.get_panel_path())
    __auth_msg = public.to_string([27492, 21151, 33021, 20026, 20225, 19994, 29256, 19987, 20139, 21151, 33021, 65292, 35831, 20808, 36141, 20080, 20225, 19994, 29256])
    
    def __init__(self) -> None:
        xfs_quota_bin = '/usr/sbin/xfs_quota'
        if not os.path.exists(xfs_quota_bin):
            if os.path.exists('/usr/bin/apt-get'):
                public.ExecShell('apt-get install xfsprogs -y')
            else:
                public.ExecShell('yum install xfsprogs -y')


    def get_xfs_disk(self,args=None):
        '''
            @name 获取xfs磁盘信息列表
            @author hwliang<2022-02-14>
            @return list
        '''
        disks = []
        for disk in psutil.disk_partitions():
            if disk.fstype == 'xfs':
                disks.append((disk.mountpoint,disk.device,psutil.disk_usage(disk.mountpoint).free))
        return disks

    def get_path_free_quota_size(self,args = None):
        '''
            @name 获取可用的磁盘配额容量
            @author hwliang<2022-02-14>
            @param args.path<string> 需要检查的目录
            @return int
        '''
        return self.get_free_quota_size(args.path)

    def get_path_dev_mountpoint(self,path):
        '''
            @name 获取目录所在挂载点
            @author hwliang<2022-02-15>
            @param path<string> 目录
            @return string
        '''
        disks = self.get_xfs_disk()
        for disk in disks:
            if path.find(disk[0] + '/') == 0:
                return disk[1]
        return ''
        
        

    def get_free_quota_size(self,path):
        '''
            @name 获取可用的磁盘配额容量
            @author hwliang<2022-02-14>
            @param path<string> 需要检查的目录
            @return int
        '''
        if not os.path.exists(path): return -1
        if not os.path.isdir(path): return -2
        xfs_disks = self.get_xfs_disk()
        for disk in xfs_disks:
            if path.find(disk[0] + '/') == 0:
                return disk[2] / 1024 / 1024
        return -3


    def get_quota_path_list(self,args = None,get_path = None):
        '''
            @name 获取磁盘配额的目录列表
            @author hwliang<2022-02-14>
            @param args<dict> 参数列表
            @return list
        '''
        if not os.path.exists(self.__config_path): 
            public.writeFile(self.__config_path,'[]')
        
        quota_list = json.loads(public.readFile(self.__config_path))

        new_quota_list = []
        for quota in quota_list:
            if not os.path.exists(quota['path']) or not os.path.isdir(quota['path']) or os.path.islink(quota['path']):continue
            if get_path:
                if quota['path'] == get_path:
                    usage_info = psutil.disk_usage(quota['path'])
                    quota['used'] = usage_info.used
                    quota['free'] = usage_info.free
                    return quota
                else:
                    continue
            usage_info = psutil.disk_usage(quota['path'])
            quota['used'] = usage_info.used
            quota['free'] = usage_info.free
            new_quota_list.append(quota)

        if get_path:
            return {'size':0,'used':0,'free':0}

        if len(new_quota_list) != len(quota_list):
            public.writeFile(self.__config_path,json.dumps(new_quota_list))
        
        return quota_list


    def get_quota_mysql_list(self,args = None,get_name = None):
        '''
            @name 获取数据库配额列表
            @author hwliang<2022-02-14>
            @param args<dict> 参数列表
            @return list
        '''
        if not os.path.exists(self.__mysql_config_file): 
            public.writeFile(self.__mysql_config_file,'[]')
        
        quota_list = json.loads(public.readFile(self.__mysql_config_file))
        new_quota_list = []
        db_obj = public.M('databases')
        for quota in quota_list:
            if get_name:
                if quota['db_name'] == get_name:
                    quota['used'] = quota['used'] = int(public.get_database_size_by_name(quota['db_name']))
                    return quota
            else:
                if db_obj.where('name=?',quota['db_name']).count():
                    if args:quota['used'] = int(public.get_database_size_by_name(quota['db_name']))
                    new_quota_list.append(quota)
        db_obj.close()
        if get_name:
            return {'size':0,'used':0}
        if len(new_quota_list) != len(quota_list):
            public.writeFile(self.__mysql_config_file,json.dumps(new_quota_list))
        return new_quota_list

    def rm_mysql_insert_accept(self,mysql_obj,username,db_name,db_host):
        '''
            @name 移除数据库用户的插入权限
            @author hwliang<2022-02-14>
            @param mysql_obj<object> 数据库对象
            @param username<string> 用户名
            @param db_name<string> 数据库名称
            @param db_host<string> host
            @return bool
        '''
        res = mysql_obj.execute("REVOKE ALL PRIVILEGES ON `{}`.* FROM '{}'@'{}';".format(db_name,username,db_host))
        if res: raise public.PanelError('移除数据库用户的插入权限失败: {}'.format(res))
        res = mysql_obj.execute("GRANT SELECT, DELETE, CREATE, DROP, REFERENCES, INDEX, CREATE TEMPORARY TABLES, LOCK TABLES, CREATE VIEW, EVENT, TRIGGER, SHOW VIEW, CREATE ROUTINE, ALTER ROUTINE, EXECUTE ON `{}`.* TO '{}'@'{}';".format(db_name,username,db_host))
        if res: raise public.PanelError('移除数据库用户的插入权限失败: {}'.format(res))
        mysql_obj.execute("FLUSH PRIVILEGES;")
        return True

    def rep_mysql_insert_accept(self,mysql_obj,username,db_name,db_host):
        '''
            @name 恢复数据库用户的插入权限
            @author hwliang<2022-02-14>
            @param mysql_obj<object> 数据库对象
            @param username<string> 用户名
            @param db_name<string> 数据库名称
            @param db_host<string> host
            @return bool
        '''
        res = mysql_obj.execute("REVOKE ALL PRIVILEGES ON `{}`.* FROM '{}'@'{}';".format(db_name,username,db_host))
        if res: raise public.PanelError('恢复数据库用户的插入权限失败: {}'.format(res))
        res = mysql_obj.execute("GRANT ALL PRIVILEGES ON `{}`.* TO '{}'@'{}';".format(db_name,username,db_host))
        if res: raise public.PanelError('恢复数据库用户的插入权限失败: {}'.format(res))
        mysql_obj.execute("FLUSH PRIVILEGES;")
        return True


    def mysql_quota_service(self):
        '''
            @name 启动MySQL配额监测服务
            @author hwliang<2022-02-14>
            @return void
        '''
        while 1:
            time.sleep(600)
            self.mysql_quota_check()


    def map_to_list(self,map_obj):
        try:
            if type(map_obj) != list and type(map_obj) != str: map_obj = list(map_obj)
            return map_obj
        except: return []
        
    def mysql_quota_check(self):
        '''
            @name 检查MySQL配额
            @author hwliang<2022-02-14>
            @return void
        '''
        if not self.check_auth(): return public.returnMsg(False,self.__auth_msg)
        quota_list = self.get_quota_mysql_list()
        for quota in quota_list:
            try:
                used_size = public.get_database_size_by_name(quota['db_name']) / 1024 / 1024
                username = public.M('databases').where('name=?',(quota['db_name'],)).getField('username')
                mysql_obj = public.get_mysql_obj(quota['db_name'])
                accept = self.map_to_list(mysql_obj.query("select Host from mysql.user where User='" + username + "'"))
                if used_size < quota['size']: 
                    if not quota['insert_accept']:
                        for host in accept:
                            self.rep_mysql_insert_accept(mysql_obj,username,quota['db_name'],host[0])
                        quota['insert_accept'] = True
                        public.WriteLog('磁盘配额','数据库[{}]因低于配额[{}MB],恢复插入权限'.format(quota['db_name'],quota['size']))
                    if hasattr(mysql_obj,'close'): mysql_obj.close()
                    continue
                
                for host in accept:
                    self.rm_mysql_insert_accept(mysql_obj,username,quota['db_name'],host[0])
                quota['insert_accept'] = False
                public.WriteLog('磁盘配额','数据库[{}]因超出配额[{}MB],移除插入权限'.format(quota['db_name'],quota['size']))
                if hasattr(mysql_obj,'close'): mysql_obj.close()
            except:
                public.print_log(public.get_error_info())
        public.writeFile(self.__mysql_config_file,json.dumps(quota_list))

    def create_mysql_quota(self,args):
        '''
            @name 创建磁盘配额
            @author hwliang<2022-02-14>
            @param args<dict>{
                db_name<string> 数据库名称
                size<int> 配额大小(MB)
            }
            @return dict
        '''
        if not self.check_auth(): return public.returnMsg(False,self.__auth_msg)
        if not os.path.exists(self.__mysql_config_file): 
            public.writeFile(self.__mysql_config_file,'[]')
        size = int(args['size'])
        db_name = args.db_name.strip()
        quota_list = json.loads(public.readFile(self.__mysql_config_file))
        for quota in quota_list:
            if quota['db_name'] == db_name:
                return public.returnMsg(False,'数据库配额已存在')
        
        quota_list.append({
            'db_name':db_name,
            'size':size,
            'insert_accept':True
        })
        public.writeFile(self.__mysql_config_file,json.dumps(quota_list))
        public.WriteLog('磁盘配额','创建数据库[{db_name}]的配额限制为: {size}MB'.format(db_name=db_name,size=size))
        self.mysql_quota_check()
        return public.returnMsg(True,'添加成功')


    def check_auth(self):
        return True
        from pluginAuth import Plugin
        plugin_obj = Plugin(False)
        plugin_list = plugin_obj.get_plugin_list()
        return int(plugin_list['ltd']) > time.time()

    def modify_mysql_quota(self,args):
        '''
            @name 修改数据库配额
            @author hwliang<2022-02-14>
            @param args<dict>{
                db_name<string> 数据库名称
                size<int> 配额大小(MB)
            }
            @return dict
        '''
        if not self.check_auth(): return public.returnMsg(False,self.__auth_msg)
        if not os.path.exists(self.__mysql_config_file): 
            public.writeFile(self.__mysql_config_file,'[]')
        size = int(args['size'])
        db_name = args.db_name.strip()
        quota_list = json.loads(public.readFile(self.__mysql_config_file))
        is_exists = False
        for quota in quota_list:
            if quota['db_name'] == db_name:
                quota['size'] = size
                is_exists = True
                break

        if is_exists:
            public.writeFile(self.__mysql_config_file,json.dumps(quota_list))
            public.WriteLog('磁盘配额','修改数据库[{db_name}]的配额限制为: {size}MB'.format(db_name=db_name,size=size))
            self.mysql_quota_check()
            return public.returnMsg(True,'修改成功')
        return self.create_mysql_quota(args)



    def get_xfs_quota_id(self,mountpoint):
        '''
            @name 获取xfs文件系统中的配额ID
            @author hwliang<2022-02-15>
            @param mountpoint<string> 挂载点
            @return int
        '''
        id_list = []
        result = public.ExecShell("xfs_quota -x -c report {mountpoint}|awk '{{print $1}}'|grep '#'".format(mountpoint=mountpoint))[0]
        if not result: return id_list
        for id in result.split('\n'):
            if id: id_list.append(int(id.split('#')[-1]))
        return id_list

    def get_quota_id(self,quota_path_list,mountpoint):
        '''
            @name 获取下一个项目配额ID
            @author hwliang<2022-02-15>
            @param quota_path_list<list> 配额列表
            @return int
        '''
        quota_id = 1001
        if not quota_path_list: return quota_id
        quota_id = quota_path_list[-1]['id'] + 1
        xfs_quota_id_list = sorted(self.get_xfs_quota_id(mountpoint))
        if xfs_quota_id_list:
            if xfs_quota_id_list[-1] > quota_id:
                quota_id = xfs_quota_id_list[-1] + 1
        return quota_id
        

    def create_path_quota(self,args):
        '''
            @name 创建磁盘配额
            @author hwliang<2022-02-14>
            @param args<dict>{
                path<string> 目录
                size<int> 配额大小(MB)
            }
            @return dict
        '''
        if not self.check_auth(): return public.returnMsg(False,self.__auth_msg)
        path = args.path.strip()
        size = int(args.size)
        if not os.path.exists(path): return public.returnMsg(False,'指定目录不存在')
        if os.path.isfile(path): return public.returnMsg(False,'指定目录不是目录!')
        if os.path.islink(path): return public.returnMsg(False,'指定目录是软链接!')
        quota_path_list = self.get_quota_path_list()
        for quota in quota_path_list:
            if quota['path'] == path: return public.returnMsg(False,'指定目录已经设置过配额!')

        free_quota_size = self.get_free_quota_size(path)
        if free_quota_size == -3: return public.returnMsg(False,'指定目录所在分区不是XFS分区,不支持目录配额!')
        if free_quota_size == -2: return public.returnMsg(False,'这不是一个有效的目录!')
        if free_quota_size == -1: return public.returnMsg(False,'指定目录不存在!')

        if size > free_quota_size: return public.returnMsg(False,'指定磁盘可用的配额容量不足!')

        mountpoint = self.get_path_dev_mountpoint(path)
        if not mountpoint: return public.returnMsg(False,'指定目录不在xfs磁盘分区中!')
        quota_id = self.get_quota_id(quota_path_list,mountpoint)

        res = public.ExecShell("xfs_quota -x -c 'project -s -p {path} {quota_id}'".format(path=path,quota_id=quota_id))
        if res[1]: return public.returnMsg(False,res[1])
        res = public.ExecShell("xfs_quota -x -c 'limit -p bhard={size}m {quota_id}' {mountpoint}".format(quota_id=quota_id,size=size,mountpoint=mountpoint))
        if res[1]: return public.returnMsg(False,res[1])
        quota_path_list.append({
            'path':args.path,
            'size':size,
            'id': quota_id
        })
        public.writeFile(self.__config_path,json.dumps(quota_path_list))
        public.WriteLog('磁盘配额','创建目录[{path}]的配额限制为: {size}MB'.format(path=path,size=size))
        return public.returnMsg(True,'添加成功')


    def modify_path_quota(self,args):
        '''
            @name 修改磁盘配额
            @author hwliang<2022-02-14>
            @param args<dict>{
                path<string> 目录
                size<int> 配额大小(MB)
            }
            @return dict
        '''
        if not self.check_auth(): return public.returnMsg(False,self.__auth_msg)
        path = args.path.strip()
        size = int(args.size)
        if not os.path.exists(path): return public.returnMsg(False,'指定目录不存在')
        if os.path.isfile(path): return public.returnMsg(False,'指定目录不是目录!')
        if os.path.islink(path): return public.returnMsg(False,'指定目录是软链接!')
        quota_path_list = self.get_quota_path_list()
        quota_id = 0
        for quota in quota_path_list:
            if quota['path'] == path:
                quota_id = quota['id']
                break
        if not quota_id: return self.create_path_quota(args)

        free_quota_size = self.get_free_quota_size(path)
        if free_quota_size == -3: return public.returnMsg(False,'指定目录所在分区不是XFS分区,不支持目录配额!')
        if free_quota_size == -2: return public.returnMsg(False,'这不是一个有效的目录!')
        if free_quota_size == -1: return public.returnMsg(False,'指定目录不存在!')
        if size > free_quota_size: return public.returnMsg(False,'指定磁盘可用的配额容量不足!')

        mountpoint = self.get_path_dev_mountpoint(path)
        if not mountpoint: return public.returnMsg(False,'指定目录不在xfs磁盘分区中!')
        res = public.ExecShell("xfs_quota -x -c 'project -s -p {path} {quota_id}'".format(path=path,quota_id=quota_id))
        if res[1]: return public.returnMsg(False,res[1])
        res = public.ExecShell("xfs_quota -x -c 'limit -p bhard={size}m {quota_id}' {mountpoint}".format(quota_id=quota_id,size=size,mountpoint=mountpoint))
        if res[1]: return public.returnMsg(False,res[1])
        for quota in quota_path_list:
            if quota['path'] == path:
                quota['size'] = size
                break
        public.writeFile(self.__config_path,json.dumps(quota_path_list))
        public.WriteLog('磁盘配额','修改目录[{path}]的配额限制为: {size}MB'.format(path=path,size=size))
        return public.returnMsg(True,'修改成功')


    


    
