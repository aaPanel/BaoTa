#coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板 
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: hwliang <hwl@bt.cn>
# +-------------------------------------------------------------------

import sys,os,time,json
from BTPanel import send_file,Response,public
class index:


    def index(self,args):

        return 'ok'

    def test(self,args):

        return Response('禁止访问',403)


    def get_server_list(self,args):
        '''
            @name 获取服务器列表
        '''
        data = public.M('colony_servers').select()
        return data


    def get_server_find(self,args):
        '''
            @name 获取指定服务器信息
        '''

        sid = args.get('sid/d')
        result = public.M('colony_servers').where('sid=?',sid).find()
        if not result: return public.returnMsg(False,'指定参数不存在')
        return result


    def create_server(self,args):
        '''
            @name 添加服务器
            @param address 服务器IP
            @param ssh_info SSH连接信息
            @param status 状态 0.停用 1.启用
            @param s_type  服务器类型 0.混合 1.HTTP  2.数据库 3.应用服务器
            @param ps 备注
        '''
        ssh_info = args.get('ssh_info/j')
        pdata = {
            'address': args.get('address/s'),
            'ssh_info': json.dumps(ssh_info),
            'status': 1,
            's_type': args.get('s_type/d'),
            'ps': args.get('ps/s'),
            'addtime': int(time.time())
        }

        if public.M('colony_servers').where('address=?',pdata['address']).count():
            return public.returnMsg(False,'指定服务器已经添加过了!')
        

        public.M('colony_servers').insert(pdata)



    def modify_server(self,args):
        '''
            @name 修改指定服务器信息
        '''
        pass


    def remove_server(self,args):
        '''
            @name 删除指定服务器信息
        '''
        pass

    
    def get_total_info(self,args):
        '''
            @name 获取统计信息（节点/网站/数据库/其它应用）
        '''
        pass

    def get_load_info(self,args):
        '''
            @name 获取负载信息
        '''

    def get_warning_info(self,args):
        '''
            @name 获取警告信息
        '''

    
