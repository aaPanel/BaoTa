#coding: utf-8
#-------------------------------------------------------------------
# 宝塔Linux面板
#-------------------------------------------------------------------
# Copyright (c) 2015-2017 宝塔软件(http:#bt.cn) All rights reserved.
#-------------------------------------------------------------------
# Author: hwliang <hwl@bt.cn>
#-------------------------------------------------------------------

#------------------------------
# 项目管理控制器
#------------------------------
import os,sys,public,json,re

class ProjectController:


    def __init__(self):
        pass

    

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
    
    def model(self,args):
        '''
            @name 调用指定项目模型
            @author hwliang<2021-07-15>
            @param args<dict_obj> {
                data: {
                    project_name: string<项目名称>,
                    ps: string<项目备注>,
                    parser_type: string<解释器类型>, // 从 get_parser_list 接口中获取
                    parser_version: string<解释器版本>, // 从 get_parser_versions 接口中获取
                    type_id: int<分类标识>,
                    def_name: string<方法名称>,
                    mod_name: string<模型名称>, //如php、java、python、nodejs

                    // 以下为不同模型下的附加参数示例 
                    php: {
                        domains: list<域名列表>,  // 如：["www.bt.cn:80","bt.cn:80"]
                        path: string<网站根目录>
                    },
                    stream: { // TCP、UDP时传入
                        is_stream: bool<是否为stream>,
                        pool: string<协议类型TCP/UDP>,
                        dst_address: string<目标地址>,
                        dst_port: int<目标端口>,
                        local_port: int<本地映射端口>
                    },
                    process: { //绑定进程时传入
                        is_process: bool<是否为启动指定文件>,
                        cwd: string<运行目录>,
                        run_file: string<启动文件>,
                        run_args: string<启动参数>,
                        run_cmd: string<启动命令> //与 run_file/run_args 互斥
                        env: list<环境变量>
                    }
                }
            }
        '''
        try: # 表单验证
            public.exists_args('data',args)
            try: # 解析为dict_obj
                pdata = public.to_dict_obj(json.loads(args.data))
            except Exception as ex:
                return public.return_status_code(1002,ex)
            public.exists_args('project_name,def_name,mod_name',pdata)
            if pdata['def_name'].find('__') != -1: return public.return_status_code(1000,'调用的方法名称中不能包含“__”字符')
            if not re.match(r"^\w+$",pdata['mod_name']): return public.return_status_code(1000,'调用的模块名称中不能包含\w以外的字符')
            if not re.match(r"^\w+$",pdata['def_name']): return public.return_status_code(1000,'调用的方法名称中不能包含\w以外的字符')
        except Exception as ex:
            return public.return_status_code(1000,ex)
        # 参数处理
        mod_name = "{}Model".format(pdata['mod_name'].strip())
        def_name = pdata['def_name'].strip()
        
        # 指定模型是否存在
        mod_file = "{}/projectModel/{}.py".format(public.get_class_path(),mod_name)
        if not os.path.exists(mod_file):
            return public.return_status_code(1003,mod_name)
        # 实例化
        mod_object = __import__('projectModel.{}'.format(mod_name))
        def_object = getattr(mod_object,def_name,None)

        # 方法是否存在
        if not def_object:
            return public.return_status_code(1004,def_name)
        return def_object(pdata)