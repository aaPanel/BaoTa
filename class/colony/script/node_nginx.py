# coding: utf-8
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: wzj <wzj@bt.cn>
# +-------------------------------------------------------------------
# +-------------------------------------------------------------------
# | nginx操作类库
# +-------------------------------------------------------------------
import re
import sys
import os
import shutil
import json

os.chdir('/www/server/panel')
sys.path.insert(0, 'class/')
import public
from .ssh_client import ssh_client


class nginx_manager(object):
    __nfs_server = ''
    __nfs_host = ''
    __nfs_root = ''

    def __init__(self):
        nfs_conf = json.loads(public.readFile('/www/server/panel/class/colony/nfs.conf'))
        self.__nfs_host = nfs_conf['host']
        self.__nfs_root = nfs_conf['root']
        self.__nfs_server = '{}:{}'.format(self.__nfs_host, self.__nfs_root)

    def get_server_info(self, server_id):
        '''
        取指定服务器的资源信息
        '''
        data = public.M('colony_server').where('id=?', server_id).find()
        return data

    def connect_server(self, server_info):
        '''
        连接指定服务器
        '''
        if int(server_info['c_type']) == 0:
            p = ssh_client(address=server_info['host'], port=server_info['port'], ssh_user=server_info['username'], password=server_info['password'])
        else:
            p = ssh_client(address=server_info['host'], port=server_info['port'], ssh_user=server_info['username'], pkey=server_info['pkey'])
        try:
            p.connect_ssh()
        except Exception as e:
            return public.returnMsg(False, '连接失败: ' + str(e))
        return p

    def local_mount_nfs(self, get):
        '''
        本机挂载nfs
        '''
        if not os.path.exists('/usr/sbin/showmount'):
            if os.path.exists('/usr/bin/yum'):
                public.ExecShell('yum install nfs-utils -y')
            else:
                public.ExecShell('apt install nfs-common -y')
        result = public.ExecShell('showmount -e {} | grep "{}"'.format(self.__nfs_host, self.__nfs_host))
        if not result[0]:
            return public.returnMsg(False, '本机挂载nfs失败, 失败原因: {}'.format(result[1]))
        if not os.path.exists(self.__nfs_root):
            os.makedirs(self.__nfs_root)
        public.ExecShell('mount -t nfs {nfs_server} {root}'.format(nfs_server=self.__nfs_server, root=self.__nfs_root))
        result = public.ExecShell("df -h | grep '{}'".format(self.__nfs_server))[0]
        if not result:
            return public.returnMsg(False, '本机挂载nfs失败')
        return public.returnMsg(True, '挂载nfs成功')

    def mount_nfs(self, get):
        '''
        挂载nfs
        '''
        server_info = self.get_server_info(get['server_id'])
        p = self.connect_server(server_info)
        if isinstance(p, dict):
            return p

        result = p.exec_shell('showmount -e {} | grep "{}"'.format(self.__nfs_host, self.__nfs_host))
        if not result[0]:
            return public.returnMsg(False, result)
        p.exec_shell('mkdir {}'.format(self.__nfs_root))
        p.exec_shell('mount -t nfs {nfs_server} {root}'.format(root=self.__nfs_root, nfs_server=self.__nfs_server))
        result = p.exec_shell("df -h | grep '{}'".format(self.__nfs_server))[0]
        if not result:
            return public.returnMsg(False, '受控机挂载nfs失败')
        return public.returnMsg(True, '挂载nfs成功')

    def sync_conf(self, get):
        '''
        同步网站nginx配置，通过nfs
        '''
        server_info = self.get_server_info(get['server_id'])
        p = self.connect_server(server_info)
        if isinstance(p, dict):
            return p

        result = self.local_mount_nfs(get)
        if not result['status']:
            return result
        result = self.mount_nfs(get)
        if not result['status']:
            return result
        # 同步vhost文件夹
        nfs_path = '{root}/{path}/'.format(root=self.__nfs_root, path=server_info['host'])
        if not os.path.exists(nfs_path):
            os.makedirs(nfs_path)
        src_file = '/www/server/panel/vhost/'
        dst_file = '{root}/{path}/vhost/'.format(root=self.__nfs_root, path=server_info['host'])
        if not os.path.exists(nfs_path):
            os.makedirs(nfs_path)
        if os.path.exists(dst_file):
            shutil.rmtree(dst_file)
        shutil.copytree(src_file, dst_file)
        p.exec_shell('rm -rf {} && cp -a {} {}'.format(src_file, dst_file, src_file))
        return public.returnMsg(True, '同步配置到[{}]成功'.format(server_info['host']))

    def sync_conf_ftp(self, get):
        '''
        同步网站nginx配置，通过ftp
        '''
        server_info = self.get_server_info(get['server_id'])
        p = self.connect_server(server_info)
        if isinstance(p, dict):
            return p

        # 同步vhost文件夹
        p.upload_file('/www/server/panel/vhost', '/www/server/panel/vhost', is_dir=True)
        return public.returnMsg(True, '同步配置到[{}]成功'.format(server_info['host']))

    def service_admin(self, get):
        '''
        nginx服务远程重启，重载，停止，启动
        '''
        server_info = self.get_server_info(get['server_id'])
        p = self.connect_server(server_info)
        if isinstance(p, dict):
            return p

        if get.act_type not in ['reload', 'restart', 'start', 'stop']:
            return public.returnMsg(False, '非法操作!')
        cmd = '/etc/init.d/nginx {}'.format(get.act_type)
        result = p.exec_shell(cmd)
        if result[1]:
            return public.returnMsg(False, result[1])
        return public.returnMsg(True, '服务器[{}]上的nginx执行{}操作成功'.format(server_info['host'], get.act_type))

    def get_status(self, get):
        '''
        获取nginx负载状态
        '''
        server_info = self.get_server_info(get['server_id'])
        p = self.connect_server(server_info)
        if isinstance(p, dict):
            return p

        try:
            worker = int(p.exec_shell("ps aux|grep nginx|grep 'worker process'|wc -l")[0]) - 1
            workermen = int(p.exec_shell("ps aux|grep nginx|grep 'worker process'|awk '{memsum+=$6};END {print memsum}'")[0]) / 1024
            result = p.exec_shell('curl http://127.0.0.1/nginx_status')[0]
            tmp = result.split()
            data = {}
            if "request_time" in tmp:
                data['accepts'] = tmp[8]
                data['handled'] = tmp[9]
                data['requests'] = tmp[10]
                data['Reading'] = tmp[13]
                data['Writing'] = tmp[15]
                data['Waiting'] = tmp[17]
            else:
                data['accepts'] = tmp[9]
                data['handled'] = tmp[7]
                data['requests'] = tmp[8]
                data['Reading'] = tmp[11]
                data['Writing'] = tmp[13]
                data['Waiting'] = tmp[15]
            data['active'] = tmp[2]
            data['worker'] = worker
            data['workermen'] = "%s%s" % (int(workermen), "MB")
            return data
        except Exception as ex:
            public.WriteLog('信息获取', "Nginx负载状态获取失败: %s" % ex)
            return public.returnMsg(False, '数据获取失败,检查nginx状态是否正常!')

    def install(self, get):
        '''
        安装nginx
        '''
        server_info = self.get_server_info(get['server_id'])
        p = self.connect_server(server_info)
        if isinstance(p, dict):
            return p

        result = p.exec_shell('ls /www/server/nginx/sbin/nginx')[0]
        if result:
            return public.returnMsg(True, 'nginx已经安装过了')
        p.upload_file('/www/server/panel/install', '/www/server/panel/install', is_dir=True)
        result = p.exec_shell('ls /www/server/panel/install/install_soft.sh')
        if result[1]:
            return public.returnMsg(False, '同步安装脚本失败')
        result = p.exec_shell('ls /usr/bin/apt-get')
        if result[1]:
            cmd = 'cd /www/server/panel/install && /bin/bash install_soft.sh 1 install nginx {} &> /tmp/colony_nginx_install.log 2>&1'.format(get.version)
        else:
            cmd = 'cd /www/server/panel/install && /bin/bash install_soft.sh 4 install nginx {} &> /tmp/colony_nginx_install.log 2>&1'.format(get.version)
        p.exec_shell(cmd)
        return public.returnMsg(True, '安装任务执行完成')

    def get_install_log(self, get):
        '''
        获取nginx安装进度
        '''
        server_info = self.get_server_info(get['server_id'])
        p = self.connect_server(server_info)
        if isinstance(p, dict):
            return p

        result = p.exec_shell('ps -ef | grep install_soft | grep nginx | grep -v grep')[0]
        if result:
            log = p.exec_shell('tail -n 100 /tmp/colony_nginx_install.log')[0]
            return public.returnMsg(True, log)
        else:
            return public.returnMsg(False, '')

    def uninstall(self, get):
        '''
        卸载nginx
        '''
        server_info = self.get_server_info(get['server_id'])
        p = self.connect_server(server_info)
        if isinstance(p, dict):
            return p

        cmd = 'cd /www/server/panel/install && /bin/bash install_soft.sh 0 uninstall nginx {}'.format(get.version.replace('.', ''))
        p.exec_shell(cmd)
        return public.returnMsg(True, '卸载成功')
