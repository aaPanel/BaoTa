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

class MsgController:

    def __init__(self):
        pass

    def model(self, args):
        '''
            @name 调用指定项目模型
            @author hwliang<2021-07-15>
            @param args<dict_obj> {
                mod_name: string<模型名称>
                def_name: string<方法名称>
                data: JSON
            }
        '''
        try:  # 表单验证
            if args['mod_name'] in ['base']: return public.return_status_code(1000, '错误的调用!')
            public.exists_args('def_name,mod_name', args)
            if args['def_name'].find('__') != -1: return public.return_status_code(1000, '调用的方法名称中不能包含“__”字符')
            if not re.match(r"^\w+$", args['mod_name']): return public.return_status_code(1000, '调用的模块名称中不能包含\w以外的字符')
            if not re.match(r"^\w+$", args['def_name']): return public.return_status_code(1000, '调用的方法名称中不能包含\w以外的字符')
        except:
            return public.get_error_object()
        # 参数处理
        mod_name = "{}".format(args['mod_name'].strip())
        def_name = args['def_name'].strip()

        # 指定模型是否存在
        mod_file = "{}/msg/{}_msg.py".format(public.get_class_path(), mod_name)
        if not os.path.exists(mod_file):
            return public.return_status_code(1003, mod_name)
        # 实例化
        def_object = public.get_script_object(mod_file)
        if not def_object: return public.return_status_code(1000, '没有找到{}模型'.format(mod_name))
        #实例化对象名称
        def_object_name = '{}_msg'.format(mod_name)
        class_obj = getattr(def_object, def_object_name, None)
        #实例化main 对象
        run_object = getattr(class_obj(), def_name, None)
        if not run_object: return public.return_status_code(1000, '没有在{}模型中找到{}方法'.format(mod_name, def_name))
        if not hasattr(args, 'data'): args.data = {}
        if args.data:
            if isinstance(args.data, str):
                try:  # 解析为dict_obj
                    pdata = public.to_dict_obj(json.loads(args.data))
                except:
                    return public.get_error_object()
            else:
                pdata = args.data
        else:
            pdata = args

        # 前置HOOK
        hook_index = '{}_{}_LAST'.format(mod_name.upper(), def_name.upper())
        hook_result = public.exec_hook(hook_index, pdata)
        if isinstance(hook_result, public.dict_obj):
            pdata = hook_result  # 桥接
        elif isinstance(hook_result, dict):
            return hook_result  # 响应具体错误信息
        elif isinstance(hook_result, bool):
            if not hook_result:  # 直接中断操作
                return public.return_data(False, {}, error_msg='前置HOOK中断操作')

        # 调用处理方法
        result = run_object(pdata)

        # 后置HOOK
        hook_index = '{}_{}_END'.format(mod_name.upper(), def_name.upper())
        hook_data = public.to_dict_obj({
            'args': pdata,
            'result': result
        })
        hook_result = public.exec_hook(hook_index, hook_data)
        if isinstance(hook_result, dict):
            result = hook_result['result']
        return result



