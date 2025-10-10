# coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2015-2017 宝塔软件(http:#bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author: zouhw <zhw@bt.cn>
# -------------------------------------------------------------------

# ------------------------------
# 项目管理控制器
# ------------------------------
import os, public, json, re, time

class main:

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
        import panelPlugin
        a = public.to_dict_obj({})
        a.focre = 1
        plugin_list = panelPlugin.panelPlugin().get_soft_list(a)
        __ltd_bool = int(plugin_list['ltd']) > 1
        # __string_pro = public.to_string(
        #     [20307, 39564, 26102, 38388, 32467, 26463, 65292, 32487, 32493, 20351, 29992, 35831, 36141, 20080, 20225, 19994, 29256, 65281])
        # if time.time() > 1652975999:
        #     if not __ltd_bool:
        #         return public.returnMsg(False,__string_pro)
        try:  # 表单验证
            args.def_name = args.dk_def_name
            args.mod_name = args.dk_model_name
            if args['mod_name'] in ['base']: return public.return_status_code(1000, 'Wrong call!')
            public.exists_args('def_name,mod_name', args)
            if args['def_name'].find('__') != -1: return public.return_status_code(1000, 'The called method name cannot contain the "__" characterrong call!')
            if not re.match(r"^\w+$", args['mod_name']): return public.return_status_code(1000, 'The called module name cannot contain characters other than \w')
            if not re.match(r"^\w+$", args['def_name']): return public.return_status_code(1000, 'The called module name cannot contain characters other than \w')
        except:
            return public.get_error_object()
        # 参数处理
        mod_name = "dk_{}".format(args['mod_name'].strip())
        def_name = args['def_name'].strip()

        # 指定模型是否存在
        mod_file = "{}/projectModel/bt_docker/{}.py".format(public.get_class_path(), mod_name)
        if not os.path.exists(mod_file):
            return public.return_status_code(1003, mod_name)
        # 实例化
        def_object = public.get_script_object(mod_file)
        if not def_object: return public.return_status_code(1000, '{} model not found'.format(mod_name))
        run_object = getattr(def_object.main(), def_name, None)
        if not run_object: return public.return_status_code(1000, '{} method not found in {} model'.format(mod_name, def_name))
        # if not hasattr(args, 'data'): args.data = {}
        # if args.data:
        #     if isinstance(args.data, str):
        #         try:  # 解析为dict_obj
        #             pdata = public.to_dict_obj(json.loads(args.data))
        #         except:
        #             return public.get_error_object()
        #     else:
        #         pdata = args.data
        # else:
        #     pdata = public.dict_obj()

        # 前置HOOK
        hook_index = '{}_{}_LAST'.format(mod_name.upper(), def_name.upper())
        hook_result = public.exec_hook(hook_index, args)
        if isinstance(hook_result, public.dict_obj):
            pdata = hook_result  # 桥接
        elif isinstance(hook_result, dict):
            return hook_result  # 响应具体错误信息
        elif isinstance(hook_result, bool):
            if not hook_result:  # 直接中断操作
                return public.return_data(False, {}, error_msg='Pre-HOOK interrupt operation')

        # 调用处理方法
        result = run_object(args)

        # 后置HOOK
        hook_index = '{}_{}_END'.format(mod_name.upper(), def_name.upper())
        hook_data = public.to_dict_obj({
            'args': args,
            'result': result
        })
        hook_result = public.exec_hook(hook_index, hook_data)
        if isinstance(hook_result, dict):
            result = hook_result['result']
        return result
