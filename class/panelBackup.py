#coding: utf-8
#-------------------------------------------------------------------
# 宝塔Linux面板
#-------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
#-------------------------------------------------------------------
# Author: 黄文良 <287962566@qq.com>
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
sys.path.insert(0,'class/')
import public

class backup:
    _path = None
    _exclude = ""
    _err_log = '/tmp/backup_err.log'
    _inode_min = 10
    def __init__(self):
        self._path = public.M('config').where("id=?",(1,)).getField('backup_path')

    def echo_info(self,msg):
        print("|-{}".format(msg))

    def echo_error(self,msg):
        print("=" * 50)
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
        temp = public.ExecShell("df -T -P|grep '/'|grep -v tmpfs")[0]
        tempInodes = public.ExecShell("df -i -P|grep '/'|grep -v tmpfs")[0]
        temp1 = temp.split('\n')
        tempInodes1 = tempInodes.split('\n')
        diskInfo = []
        n = 0
        cuts = []
        for tmp in temp1:
            n += 1
            try:
                inodes = tempInodes1[n-1].split()
                disk = re.findall(r"^(.+)\s+([\w]+)\s+([\w\.]+)\s+([\w\.]+)\s+([\w\.]+)\s+([\d%]{2,4})\s+(/.{0,50})$",tmp.strip())
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
    def backup_path(self,spath,dfile = None,exclude=[]):
        if not os.path.exists(spath):
            self.echo_error('指定目录{}不存在!'.format(spath))
            return False

        dirname = os.path.basename(spath) 
        if not dfile:
            fname = 'web_{}_{}.tar.gz'.format(dirname,public.format_date("%Y%m%d_%H%M%S"))
            dfile = os.path.join(self._path,'site',fname)
        
        dpath = os.path.dirname(dfile)
        if not os.path.exists(dpath):
            os.makedirs(dpath,384)
        
        p_size = public.get_path_size(spath)

        exclude_config = self._exclude
        if not self.get_exclude(exclude):
            exclude_config = "未设置"

        self.echo_info('备份目录：{}'.format(spath))
        self.echo_info("目录大小：{}".format(public.to_size(p_size)))
        self.echo_info("排除设置：{}".format(exclude_config))
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
        if tar_size < int(p_size / 10):
            self.echo_error("数据压缩失败")
            self.echo_info(public.readFile(self._err_log))
            return False
        self.echo_info("文件压缩完成，耗时{:.2f}秒，压缩包大小：{}".format(time.time() - stime,public.to_size(tar_size)))
        self.echo_info("目录已备份到：{}".format(dfile))
        if os.path.exists(self._err_log):
            os.remove(self._err_log)
        return dfile

    #备份指定站点
    def backup_site(self,siteName):
        pass

    #备份所有站点
    def backup_site_all(self):
        pass

    #备份指定数据库
    def backup_database(self,dbName):
        pass

    #备份所有数据库
    def backup_database_all(self):
        pass



if __name__ == '__main__':
    p = backup()
    p.backup_path('/www/test/w6.hao.com')

    
