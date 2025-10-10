#coding: utf-8

#------------------------------
# 批量发送调用脚本
#------------------------------
import os,sys
os.chdir('/www/server/panel')
# sys.path.insert(1,'BTPanel/')
sys.path.insert(0,'class/')

import public
import traceback
plugin_name = 'mail_sys'
def_name = 'check_task_status'

import PluginLoader



try:

    args = public.dict_obj()
    # args.plugin_get_object = 1
    from mailModel import mainModel
    data = mainModel.main().check_task_status(args)

    # data = PluginLoader.plugin_run(plugin_name,def_name,args)
    print("批量发送 -{} ".format(data))
except Exception as ex:
    print("批量发送 error: " + str(ex))
    print(traceback.format_exc())
