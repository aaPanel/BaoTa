#coding: utf-8
#-------------------------------------------------------------------
# 宝塔Linux面板
#-------------------------------------------------------------------
# Copyright (c) 2015-2017 宝塔软件(http:#bt.cn) All rights reserved.
#-------------------------------------------------------------------
# Author: hwliang <hwl@bt.cn>
#-------------------------------------------------------------------

#------------------------------
# 网站管理控制器
#------------------------------
import os,sys,public

class panelSiteController:


    def __init__(self):
        pass



    def get_parser_list(self,args):
        '''
            @name 获取支持的解释器列表
            @author hwliang<2021-07-13>
            @param args<dict_obj>
            @return list
        '''
        return public.return_data(True,public.read_config('parser'))


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
                if isinstance(version['check'],str):
                    version['check'] = [version['check']]
                for check in version['check']:
                    if os.path.exists(check):
                        versions.append(version)
        return public.return_data(True,versions)







    def create_site(self,args):
        '''
            @name 创建网站
            @author hwliang<2021-07-13>
            @param args<dict_obj> {
                data: {
                    siteName: string<网站名称>,
                    domains: list<域名列表>,  // 如：["www.bt.cn:80","bt.cn:80"]
                    parser_type: string<解释器类型>, // 从 get_parser_list 接口中获取
                    parser_version: string<解释器版本>, // 从 get_parser_versions 接口中获取
                    ps: string<网站备注>,
                    type_id: int<分类标识>,
                    path: string<网站根目录>,
                    stream_info: { // TCP、UDP时传入
                        is_stream: bool<是否为stream>,
                        pool: string<协议类型TCP/UDP>,
                        dst_address: string<目标地址>,
                        dst_port: int<目标端口>,
                        local_port: int<本地映射端口>
                    },
                    process_info: { //绑定进程时传入
                        is_process: bool<是否为启动指定文件>,
                        cwd: string<运行目录>,
                        run_file: string<启动文件>,
                        run_args: string<启动参数>,
                        run_cmd: string<启动命令> //与 run_file/run_args 互斥
                        env: list<环境变量>
                    },
                    ftp_info: { //需要同时创建FTP时传入
                        create: bool<是否创建>,
                        username: string<用户名>,
                        password: string<密码>,
                        path: string<根目录>
                    },
                    database_info: {  //需要同时创建数据库时传入
                        create: bool<是否创建>,
                        username: string<用户名>,
                        password: string<密码>,
                        db_name: string<数据库名>,
                        codeing: string<字符集>
                    }
                }
            }
        '''

