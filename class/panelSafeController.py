#coding: utf-8
#-------------------------------------------------------------------
# 宝塔Linux面板
#-------------------------------------------------------------------
# Copyright (c) 2015-2017 宝塔软件(http:#bt.cn) All rights reserved.
#-------------------------------------------------------------------
# Author: hwliang <hwl@bt.cn>
#-------------------------------------------------------------------

#------------------------------
# 系统安全管理控制器
#------------------------------
import os,sys,public,json,re

class SafeController:


    def __init__(self):
        pass

    def model(self,args):
        '''
            @name 调用指定项目模型
            @author hwliang<2021-12-31>
            @param args<dict_obj> {
                mod_name: string<模型名称>
                def_name: string<方法名称>
                data: JSON
            }
        '''
        try: # 表单验证
            if args['mod_name'] in ['base']: return public.return_status_code(1000,'错误的调用!')
            public.exists_args('def_name,mod_name',args)
            if args['def_name'].find('__') != -1: return public.return_status_code(1000,'调用的方法名称中不能包含“__”字符')
            if not re.match(r"^\w+$",args['mod_name']): return public.return_status_code(1000,'调用的模块名称中不能包含\w以外的字符')
            if not re.match(r"^\w+$",args['def_name']): return public.return_status_code(1000,'调用的方法名称中不能包含\w以外的字符')
        except:
            return public.get_error_object()
        # 参数处理
        module_name = args['mod_name'].strip()
        mod_name = "{}Model".format(args['mod_name'].strip())
        def_name = args['def_name'].strip()

        if not hasattr(args,'data'): args.data = {}
        if args.data:
            if isinstance(args.data,str):
                try: # 解析为dict_obj
                    pdata = public.to_dict_obj(json.loads(args.data))
                except:
                    return public.get_error_object()
            elif isinstance(args.data,dict):
                pdata = public.to_dict_obj(args.data)
            else:
                pdata = args.data
        else:
            pdata = public.dict_obj()

        if isinstance(pdata,dict): pdata =  public.to_dict_obj(pdata)
        pdata.model_index = 'safe'

        # 前置HOOK
        hook_index = '{}_{}_LAST'.format(mod_name.upper(),def_name.upper())
        hook_result = public.exec_hook(hook_index,pdata)
        if isinstance(hook_result,public.dict_obj):
            pdata = hook_result # 桥接
        elif isinstance(hook_result,dict):
            return hook_result # 响应具体错误信息
        elif isinstance(hook_result,bool):
            if not hook_result: # 直接中断操作
                return public.return_data(False,{},error_msg='前置HOOK中断操作')

        # 调用处理方法
        # result = run_object(pdata)
        import PluginLoader
        result = PluginLoader.module_run(module_name,def_name,pdata)
        if isinstance(result,dict):
            if 'status' in result and result['status'] == False and 'msg' in result:
                if isinstance(result['msg'],str):
                    if result['msg'].find('Traceback ') != -1:
                        raise public.PanelError(result['msg'])

        # 后置HOOK
        hook_index = '{}_{}_END'.format(mod_name.upper(),def_name.upper())
        hook_data = public.to_dict_obj({
            'args': pdata,
            'result': result
        })
        hook_result = public.exec_hook(hook_index,hook_data)
        if isinstance(hook_result,dict):
            result = hook_result['result']
        return result


