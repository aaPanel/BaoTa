#coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: hwliang <hwl@bt.cn>
# +-------------------------------------------------------------------

#+--------------------------------------------------------------------
#|   插件认证模块
#+--------------------------------------------------------------------


import public
import PluginLoader

class Plugin:
    __plugin_name = None
    __is_php = False
    __dict__ = None
    __obj_dict = {}


    def __init__(self,init_plugin_name = None):
        '''
            @name 实例化插件对像
            @author hwliang<2021-06-15>
            @param init_plugin_name<string> 插件名称
            @return Plguin<object>
        '''
        if not init_plugin_name is False:
            if not init_plugin_name:
                raise ValueError('参数错误,plugin_name少需要一个有效参数')
        self.__plugin_name = init_plugin_name

    def get_plugin_list(self,upgrade_force = False):
        '''
            @name 获取插件列表
            @author hwliang<2021-06-15>
            @param upgrade_force<bool> 是否强制重新获取列表
            @return dict
        '''
        force = 1 if upgrade_force else 0
        return PluginLoader.get_plugin_list(force)


    def exec_fun(self,get_args,def_name = None):
        '''
            @name 执行指定方法
            @author hwliang<2021-06-16>
            @param def_name<string> 方法名称
            @param get_args<dict_obj> POST/GET参数对像
            @return mixed
        '''
        if not def_name:
            def_name = get_args.get("s","")
        else:
            if not 's' in get_args:
                get_args.s = def_name

        res = PluginLoader.plugin_run(self.__plugin_name,def_name,get_args)
        if isinstance(res,dict):
            if 'status' in res and res['status'] == False and 'msg' in res:
                if isinstance(res['msg'],str):
                    if res['msg'].find('Traceback ') != -1:
                        raise public.PanelError(res['msg'])
        return res

    def get_fun(self,def_name):
        '''
            @name 获取函对像
            @author hwliang<2021-06-28>
            @param def_name<string> 函数名称
            @return func_object
        '''
        if def_name in self.__obj_dict.keys():
            return self.__obj_dict[def_name]
        get_args = public.dict_obj()
        get_args.plugin_get_object = 1
        return PluginLoader.plugin_run(self.__plugin_name,def_name,get_args)


    def isdef(self,def_name):
        '''
            @name 指定方法是否存在
            @author hwliang<2021-06-16>
            @param def_name<string> 方法名称
            @return bool
        '''
        if self.__is_php: return True
        self.__obj_dict[def_name] = self.get_fun(def_name)
        return True if self.__obj_dict[def_name] else False

    def __dir__(self):
        return ''

