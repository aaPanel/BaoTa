# coding: utf-8
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: hwliang<hwl@bt.cn>
# +-------------------------------------------------------------------
# +-------------------------------------------------------------------
# | 初始化主服务器环境
# +-------------------------------------------------------------------
import sys,os
os.chdir('/www/server/panel')
sys.path.insert(0,'class')
import public
class main_init:

    exec_log = '/tmp/bt-init.log'

    
    def install_nfs_server(self):
        '''
            @name 检测并安装nfs_server
            @ps 如果已安装，将直接返回，若安装异常，会将异常信息抛出，并记录到日志
            @author hwliang<2021-03-20>
            @return void
        '''
        if public.ExecShell("systemctl status nfs-server|grep 'active (exited)'")[0]:
            return True

        nfsd_file = '/usr/sbin/rpc.nfsd'
        if not os.path.exists(nfsd_file):
            public.ExecShell("yum install nfs-utils -y &> {}".format(self.exec_log))
        public.ExecShell("systemctl enable nfs-server &>> {}".format(self.exec_log))
        public.ExecShell('systemctl start nfs-server &>> {}'.format(self.exec_log))
        if public.ExecShell("systemctl status nfs-server|grep 'active (exited)'")[0]:
            return True
        raise Exception('nfs-server安装失败,详情请查看日志文件：{}'.format(self.exec_log))

    def install_nginx(self):
        '''
            @name 检测并安装nginx
            @ps 会直接安装最新稳定版，如果已安装最新稳定版，将直接返回，若安装异常，会将异常信息抛出，并记录到日志
            @author hwliang<2021-03-20>
            @return void
        '''

        

    def install_php(self):
        '''
            @name 检测并安装选择的PHP版本
            @ps 检测并安装用户初始化集群环境时选择的所有PHP版本，若某个PHP版本损坏无法启动，将被重新安装
            @author hwliang<2021-03-20>
            @return void
        '''

    def install_mysql(self):
        '''
            @name 检测并安装选择的MySQL版本
            @ps 如果已安装，将直接返回，若安装异常，会将异常信息抛出，并记录到日志
            @author hwliang<2021-03-20>
            @return void
        '''

    def install_memcached(self):
        '''
            @name 检测并安装最新的memcached版本
            @ps 如果已安装，将直接返回，若安装异常，会将异常信息抛出，并记录到日志
            @author hwliang<2021-03-20>
            @return void
        '''

    def install_bt_rsyslog(self):
        '''
            @name 检测并安装最新的bt-rsyslog集群日志管理器
            @ps 如果已安装，将直接返回，若安装异常，会将异常信息抛出，并记录到日志
            @author hwliang<2021-03-20>
            @return void
        '''

    def check_firewall(self):
        '''
            @name 检测并修复firewalld服务
            @ps 如果filewalld服务一切正常，则直接返回
            @author hwliang<2021-03-20>
            @return void
        '''

if __name__ == '__main__':
    p = main_init()
    p.install_nfs_server()