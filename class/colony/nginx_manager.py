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

os.chdir('/www/server/panel')
sys.path.insert(0, 'class/')
import public
from .ssh_client import ssh_client


class nginx_manager(object):
    __image_repo = 'wangzhj/nginx:latest'

    def __init__(self):
        pass

    def get_server_info(self, server_id):
        '''
        取指定服务器的资源信息
        '''
        data = public.M('colony_server').where('id=?', server_id).find()
        return data

    def get_image_list(self, get):
        '''
        获取节点的docker镜像列表
        '''
        server_info = self.get_server_info(get['id'])
        if int(server_info['c_type']) == 0:
            p = ssh_client(address=server_info['host'], port=server_info['port'], ssh_user=server_info['username'], password=server_info['password'])
        else:
            p = ssh_client(address=server_info['host'], port=server_info['port'], ssh_user=server_info['username'], pkey=server_info['pkey'])
        try:
            p.connect_ssh()
        except Exception as e:
            return public.returnMsg(False, '连接失败: ' + str(e))
        result = p.exec_shell('docker image list')
        if result[1]:
            return public.returnMsg(False, result[1])
        data = result[0].strip().split('\n')[1:]

        image_list = []
        for item in data:
            item_list = item.split()
            image_list.append(item_list)
        return image_list

    def create_nginx_container(self, get):
        '''
        在指定节点上运行nginx容器
        '''
        server_info = self.get_server_info(get['id'])
        if int(server_info['c_type']) == 0:
            p = ssh_client(address=server_info['host'], port=server_info['port'], ssh_user=server_info['username'], password=server_info['password'])
        else:
            p = ssh_client(address=server_info['host'], port=server_info['port'], ssh_user=server_info['username'], pkey=server_info['pkey'])
        try:
            p.connect_ssh()
        except Exception as e:
            return public.returnMsg(False, '连接失败: ' + str(e))
        result = p.exec_shell('docker pull {}'.format(self.__image_repo))
        if result[1]:
            return public.returnMsg(False, result[1])
        result = p.exec_shell('mkdir -p /data/nginx')
        if result[1]:
            return public.returnMsg(False, result[1])
        p.exec_shell('wget -O /data/nginx/conf.zip http://download.bt.cn/colony/nginx_conf.zip')
        result = p.exec_shell('unzip -o /data/nginx/conf.zip -d /data/nginx && rm -f /data/nginx/conf.zip')
        if result[1]:
            return public.returnMsg(False, result[1])
        result = p.exec_shell('docker run --name bt_nginx -itd -v /data/nginx/conf:/etc/nginx -v /www/wwwroot:/www/wwwroot -p 80:80 -p 443:443 {}'.format(self.__image_repo))
        if result[1]:
            return public.returnMsg(False, result[1])
        return public.returnMsg(True, result[0])
