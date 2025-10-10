#coding: utf-8

#------------------------------
# 发送结束后筛选日志
#------------------------------
import os,sys
os.chdir('/www/server/panel')
sys.path.insert(0,'class/')
import public
import traceback

plugin_name = 'mail_sys'
def_name = 'check_task_finish'
import PluginLoader

try:
    args = public.dict_obj()
    from mailModel import mainModel
    data = mainModel.main().check_task_finish(args)

    # # args.plugin_get_object = 1
    # data = PluginLoader.plugin_run(plugin_name,def_name,args)
    print("|- 发送后过滤日志-{} ".format(data))
except Exception as ex:
    print("|- 发送后过滤日志 error: " + str(ex))
    print(traceback.format_exc())
