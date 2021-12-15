#coding: utf-8
#-------------------------------------------------------------------
# 宝塔Linux面板
#-------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
#-------------------------------------------------------------------
# Author: hwliang <hwl@bt.cn>
#-------------------------------------------------------------------

#------------------------------
# 通用模型
#------------------------------
import public
import os,sys,re,json
from projectModel.base import projectBase

class main(projectBase):
    '''
        @name 为其它模型服务的通用外部调用
        @auther hwliang<2021-07-22>
    '''

    def get_parser_list(self,args):
        '''
            @name 获取支持的解释器列表
            @author hwliang<2021-07-13>
            @param args<dict_obj>
            @return list
        '''
        config_data = public.read_config('parser')
        for i in range(len(config_data)):
            versions = []
            if not config_data[i]['show']: continue
            if not config_data[i]['versions']: continue
            for version in config_data[i]['versions']:
                if not isinstance(version['check'],list):
                    version['check'] = [version['check']]
                
                for check in version['check']:
                    if not check or os.path.exists(check):
                        versions.append(version['version'])
            config_data[i]['versions'] = versions
        return public.return_data(True,config_data)


    def get_parser_versions(self,args):
        '''
            @name 获取指定解释器可用版本列表
            @author hwliang<2021-07-13>
            @param args<dict_obj>{
                parser_name: string<解释器名称>
            }
            @return list
        '''
        try:
            public.exists_args('parser_name',args)
        except Exception as ex:
            return public.return_data(False,None,1001,ex)
        parser_name = args.parser_name.strip()
        config_data = public.read_config('parser')
        versions = []
        result = public.return_data(False,versions)
        for parser_data in config_data:
            if parser_data['name'] != parser_name: continue
            if not parser_data['show']: return result
            if not parser_data['versions']: return result
            for version in parser_data['versions']:
                if not isinstance(version['check'],list):
                    version['check'] = [version['check']]
                for check in version['check']:
                    if not check or os.path.exists(check):

                        versions.append(version['version'])
        return public.return_data(True,versions)